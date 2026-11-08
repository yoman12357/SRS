"""Transactional SQLite persistence with immutable versions and exact-hash reviews."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def canonical_hash(content: dict) -> str:
    """Hash exact canonical JSON content independently of key ordering."""
    return hashlib.sha256(
        json.dumps(
            content,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def utc_now() -> str:
    """Return a timezone-aware storage timestamp."""
    return datetime.now(UTC).isoformat()


def _append_audit(
    db: sqlite3.Connection, project_id: str, kind: str, payload: dict, run_id: str | None = None
) -> str:
    event_id = str(uuid.uuid4())
    if (
        run_id is not None
        and not db.execute(
            "SELECT 1 FROM run WHERE id=? AND project_id=?", (run_id, project_id)
        ).fetchone()
    ):
        raise ValueError("audit_run_project_mismatch")
    db.execute(
        "INSERT INTO audit_event VALUES(?,?,?,?,?,?,?)",
        (
            event_id,
            project_id,
            run_id,
            kind,
            json.dumps(payload, ensure_ascii=False),
            canonical_hash(payload),
            utc_now(),
        ),
    )
    return event_id


def source_input_hash(project: dict) -> str:
    """Fingerprint original descriptions, question-bound answers and reference revisions."""
    payload = {"description": project["description"], "answers": project["answers"]}
    if project.get("reference_hashes"):
        payload["reference_hashes"] = project["reference_hashes"]
    return canonical_hash(payload)


class Repository:
    """Open one short-lived connection per transaction; never share connections."""

    def __init__(self, data_dir: Path) -> None:
        """Create the application-owned data directory and initialize its schema."""
        data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / "cybersrs.db"
        with self.connection() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS project (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
                    answers TEXT NOT NULL DEFAULT '[]', analysis TEXT,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS run (
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES project(id)
                    ON DELETE CASCADE, kind TEXT NOT NULL, status TEXT NOT NULL,
                    input_hash TEXT NOT NULL, events TEXT NOT NULL DEFAULT '[]',
                    checkpoints TEXT NOT NULL DEFAULT '{}', error TEXT,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS srs_version (
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES project(id)
                    ON DELETE CASCADE, sequence INTEGER NOT NULL, content TEXT NOT NULL,
                    content_hash TEXT NOT NULL, quality TEXT NOT NULL, run_id TEXT,
                    created_at TEXT NOT NULL, UNIQUE(project_id, sequence)
                );
                CREATE TABLE IF NOT EXISTS human_review (
                    id TEXT PRIMARY KEY, version_id TEXT NOT NULL REFERENCES srs_version(id)
                    ON DELETE CASCADE, content_hash TEXT NOT NULL, decision TEXT NOT NULL,
                    reviewer TEXT NOT NULL, comment TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS project_document (
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES project(id)
                    ON DELETE CASCADE, name TEXT NOT NULL, text TEXT NOT NULL,
                    sha256 TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_event (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL REFERENCES project(id) ON DELETE CASCADE,
                    run_id TEXT REFERENCES run(id) ON DELETE CASCADE,
                    kind TEXT NOT NULL, payload TEXT NOT NULL, payload_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS audit_project_idx ON audit_event(project_id);
            """)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Commit atomically or roll back, enforcing cascade isolation every time."""
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def create_project(self, name: str, description: str) -> dict:
        """Create a project without invoking inference."""
        project_id, now = str(uuid.uuid4()), utc_now()
        with self.connection() as db:
            db.execute(
                "INSERT INTO project(id,name,description,created_at,updated_at) VALUES(?,?,?,?,?)",
                (project_id, name, description, now, now),
            )
            _append_audit(
                db,
                project_id,
                "project_created",
                {"name": name, "description": description, "answers": []},
            )
        return self.get_project(project_id)

    def list_projects(self) -> list[dict]:
        """Return lightweight summaries, never full stored documents."""
        with self.connection() as db:
            rows = db.execute(
                "SELECT id,name,description,updated_at FROM project ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_project(self, project_id: str) -> dict:
        """Load one project or raise KeyError for a missing/deleted record."""
        with self.connection() as db:
            row = db.execute("SELECT * FROM project WHERE id=?", (project_id,)).fetchone()
            references = [
                dict(item)
                for item in db.execute(
                    "SELECT id,sha256 FROM project_document WHERE project_id=? ORDER BY id",
                    (project_id,),
                )
            ]
        if row is None:
            raise KeyError("project_not_found")
        result = dict(row)
        result["reference_hashes"] = references
        for field in ("answers", "analysis"):
            result[field] = json.loads(result[field]) if result[field] else None
        return result

    def update_project(
        self,
        project_id: str,
        *,
        expected_input_hash: str | None = None,
        **changes: Any,
    ) -> dict:
        """Update allowed fields and invalidate analysis whenever original input changes."""
        self.get_project(project_id)
        allowed = {"name", "description", "answers", "analysis"}
        if set(changes) - allowed:
            raise ValueError("unknown_project_field")
        if "description" in changes or "answers" in changes:
            changes["analysis"] = None
        changes["updated_at"] = utc_now()
        values = [
            json.dumps(v, ensure_ascii=False)
            if k in {"answers", "analysis"} and v is not None
            else v
            for k, v in changes.items()
        ]
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute(
                "SELECT name,description,answers,analysis FROM project WHERE id=?", (project_id,)
            ).fetchone()
            if previous is None:
                raise KeyError("project_not_found")
            if expected_input_hash is not None:
                row = db.execute(
                    "SELECT description,answers FROM project WHERE id=?", (project_id,)
                ).fetchone()
                if row is None:
                    raise KeyError("project_not_found")
                references = [
                    dict(item)
                    for item in db.execute(
                        "SELECT id,sha256 FROM project_document WHERE project_id=? ORDER BY id",
                        (project_id,),
                    )
                ]
                current = source_input_hash(
                    {
                        "description": row["description"],
                        "answers": json.loads(row["answers"]),
                        "reference_hashes": references,
                    }
                )
                if current != expected_input_hash:
                    raise ValueError("analysis_inputs_changed")
            db.execute(
                "UPDATE project SET " + ",".join(f"{key}=?" for key in changes) + " WHERE id=?",
                (*values, project_id),
            )
            prior = dict(previous)
            for field in ("answers", "analysis"):
                prior[field] = json.loads(prior[field]) if prior[field] else None
            _append_audit(
                db, project_id, "project_changed", {"previous": prior, "changes": changes}
            )
        return self.get_project(project_id)

    def delete_project(self, project_id: str) -> None:
        """Delete a project and all its relational data in a single transaction."""
        self.get_project(project_id)
        with self.connection() as db:
            db.execute("DELETE FROM project WHERE id=?", (project_id,))

    def create_run(self, project_id: str, kind: str, input_hash: str) -> dict:
        """Persist a queued run before dispatch so clients can poll immediately."""
        run_id, now = str(uuid.uuid4()), utc_now()
        with self.connection() as db:
            db.execute(
                "INSERT INTO run(id,project_id,kind,status,input_hash,created_at,updated_at) "
                "VALUES(?,?,?,'queued',?,?,?)",
                (run_id, project_id, kind, input_hash, now, now),
            )
            _append_audit(
                db, project_id, "run_created", {"kind": kind, "input_hash": input_hash}, run_id
            )
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> dict:
        """Return persistent run state and validated checkpoints."""
        with self.connection() as db:
            row = db.execute("SELECT * FROM run WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise KeyError("run_not_found")
        result = dict(row)
        for field in ("events", "checkpoints"):
            result[field] = json.loads(result[field])
        return result

    def list_runs(self, project_id: str) -> list[dict]:
        """Restore recent persistent workflow summaries after a browser restart."""
        self.get_project(project_id)
        with self.connection() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT id,kind,status,error,created_at,updated_at FROM run WHERE project_id=? "
                    "ORDER BY created_at DESC LIMIT 30",
                    (project_id,),
                )
            ]

    def update_run(
        self,
        run_id: str,
        *,
        status: str | None = None,
        error: str | None = None,
        event: dict | None = None,
        checkpoint: tuple[str, dict] | None = None,
    ) -> dict:
        """Append an event/checkpoint atomically with a status transition."""
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM run WHERE id=?", (run_id,)).fetchone()
            if row is None:
                raise KeyError("run_not_found")
            events, checkpoints = json.loads(row["events"]), json.loads(row["checkpoints"])
            if event:
                events.append({"at": utc_now(), **event})
            if checkpoint:
                checkpoints[checkpoint[0]] = checkpoint[1]
            db.execute(
                "UPDATE run SET status=?,error=?,events=?,checkpoints=?,updated_at=? WHERE id=?",
                (
                    status or row["status"],
                    error,
                    json.dumps(events),
                    json.dumps(checkpoints, ensure_ascii=False),
                    utc_now(),
                    run_id,
                ),
            )
            _append_audit(
                db,
                row["project_id"],
                "run_updated",
                {
                    "status": status or row["status"],
                    "error": error,
                    "event": event,
                    "checkpoint": checkpoint,
                },
                run_id,
            )
        return self.get_run(run_id)

    def interrupt_stale_runs(self) -> int:
        """Mark prior-process work interrupted; a database flag is not a live worker."""
        with self.connection() as db:
            cursor = db.execute(
                "UPDATE run SET status='interrupted',error='process_restarted',updated_at=? "
                "WHERE status IN ('running','queued')",
                (utc_now(),),
            )
            return cursor.rowcount

    def save_version(
        self,
        project_id: str,
        content: dict,
        quality: dict,
        run_id: str | None = None,
        expected_input_hash: str | None = None,
    ) -> dict:
        """Create an immutable successor, rejecting stale generation after input edits."""
        version_id = str(uuid.uuid4())
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            project = db.execute("SELECT * FROM project WHERE id=?", (project_id,)).fetchone()
            if project is None:
                raise KeyError("project_not_found")
            if expected_input_hash is not None:
                references = [
                    dict(item)
                    for item in db.execute(
                        "SELECT id,sha256 FROM project_document WHERE project_id=? ORDER BY id",
                        (project_id,),
                    )
                ]
                current = source_input_hash(
                    {
                        "description": project["description"],
                        "answers": json.loads(project["answers"]),
                        "reference_hashes": references,
                    }
                )
                if current != expected_input_hash:
                    raise ValueError("project_inputs_changed")
            sequence = db.execute(
                "SELECT COALESCE(MAX(sequence),0)+1 FROM srs_version WHERE project_id=?",
                (project_id,),
            ).fetchone()[0]
            db.execute(
                "INSERT INTO srs_version VALUES(?,?,?,?,?,?,?,?)",
                (
                    version_id,
                    project_id,
                    sequence,
                    json.dumps(content, ensure_ascii=False),
                    canonical_hash(content),
                    json.dumps(quality),
                    run_id,
                    utc_now(),
                ),
            )
            _append_audit(
                db,
                project_id,
                "version_created",
                {
                    "version_id": version_id,
                    "sequence": sequence,
                    "content_hash": canonical_hash(content),
                    "quality": quality,
                },
                run_id,
            )
        return self.get_version(project_id, version_id)

    def list_versions(self, project_id: str) -> list[dict]:
        """List immutable baseline summaries in descending version order."""
        self.get_project(project_id)
        with self.connection() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT id,sequence,content_hash,created_at FROM srs_version "
                    "WHERE project_id=? ORDER BY sequence DESC",
                    (project_id,),
                )
            ]

    def get_version(self, project_id: str, version_id: str) -> dict:
        """Enforce project ownership on every version lookup."""
        with self.connection() as db:
            row = db.execute(
                "SELECT * FROM srs_version WHERE id=? AND project_id=?",
                (version_id, project_id),
            ).fetchone()
        if row is None:
            raise KeyError("version_not_found")
        result = dict(row)
        for field in ("content", "quality"):
            result[field] = json.loads(result[field])
        return result

    def add_review(
        self,
        project_id: str,
        version_id: str,
        content_hash: str,
        decision: str,
        reviewer: str,
        comment: str,
    ) -> dict:
        """Record a real explicit human decision against the exact reviewed content."""
        version = self.get_version(project_id, version_id)
        if version["content_hash"] != content_hash:
            raise ValueError("review_content_hash_mismatch")
        if decision not in {"approve", "reject", "request_changes"} or not reviewer.strip():
            raise ValueError("invalid_review")
        if decision == "approve" and version["quality"]["status"] == "invalid":
            raise ValueError("invalid_document_cannot_be_approved")
        item = {
            "id": str(uuid.uuid4()),
            "version_id": version_id,
            "content_hash": content_hash,
            "decision": decision,
            "reviewer": reviewer,
            "comment": comment,
            "created_at": utc_now(),
        }
        with self.connection() as db:
            db.execute("INSERT INTO human_review VALUES(?,?,?,?,?,?,?)", tuple(item.values()))
            _append_audit(db, project_id, "human_review", item)
        return item

    def list_reviews(self, project_id: str, version_id: str) -> list[dict]:
        """Return exact-version human history, most recent decision last."""
        self.get_version(project_id, version_id)
        with self.connection() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT * FROM human_review WHERE version_id=? ORDER BY created_at",
                    (version_id,),
                )
            ]

    def add_document(self, project_id: str, name: str, text: str, digest: str) -> dict:
        """Persist bounded extracted reference text with its original file hash."""
        self.get_project(project_id)
        item = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "name": name,
            "text": text,
            "sha256": digest,
            "created_at": utc_now(),
        }
        with self.connection() as db:
            db.execute("INSERT INTO project_document VALUES(?,?,?,?,?,?)", tuple(item.values()))
            _append_audit(db, project_id, "reference_added", item)
        return item

    def list_documents(self, project_id: str) -> list[dict]:
        """Read only references belonging to the selected project."""
        self.get_project(project_id)
        with self.connection() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT * FROM project_document WHERE project_id=?",
                    (project_id,),
                )
            ]

    def delete_document(self, project_id: str, document_id: str) -> None:
        """Delete a reference only within the specified owning project."""
        with self.connection() as db:
            previous = db.execute(
                "SELECT * FROM project_document WHERE id=? AND project_id=?",
                (document_id, project_id),
            ).fetchone()
            cursor = db.execute(
                "DELETE FROM project_document WHERE id=? AND project_id=?",
                (document_id, project_id),
            )
            if not cursor.rowcount:
                raise KeyError("document_not_found")
            _append_audit(db, project_id, "reference_removed", dict(previous))

    def record_audit(
        self, project_id: str, kind: str, payload: dict, run_id: str | None = None
    ) -> str:
        """Append a private event atomically; reject cross-project run attribution."""
        with self.connection() as db:
            return _append_audit(db, project_id, kind, payload, run_id)

    def list_audit(self, project_id: str) -> list[dict]:
        """Read only one project's private audit records in insertion order."""
        self.get_project(project_id)
        with self.connection() as db:
            rows = db.execute(
                "SELECT * FROM audit_event WHERE project_id=? ORDER BY rowid", (project_id,)
            ).fetchall()
        return [dict(row) | {"payload": json.loads(row["payload"])} for row in rows]

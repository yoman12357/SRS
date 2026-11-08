"""Exercise source-scoped test completion on actual unedited rejected requirements."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

from cybersrs.audit import audit_scope
from cybersrs.config import Settings
from cybersrs.evidence import build_evidence
from cybersrs.provider import RepairingOllamaProvider
from cybersrs.repository import Repository
from cybersrs.requirement_repair import REQUIREMENT_REPAIR_VERSION, complete_source_gaps
from cybersrs.schemas import REQUIREMENT_PREFIXES, SECTION_SCHEMAS, Analysis, Answer, SourceChunk
from cybersrs.validation import validate_section


def main() -> None:
    """Preserve raw rows/source, scope only assessments, and never claim a full SRS."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--section", choices=tuple(REQUIREMENT_PREFIXES), required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    settings = Settings()
    with httpx.Client(base_url=f"http://127.0.0.1:{settings.backend_port}/api/v1") as client:
        response = client.get("/projects")
        response.raise_for_status()
        for project in response.json():
            runs = client.get(f"/projects/{project['id']}/runs")
            runs.raise_for_status()
            if any(r["status"] in {"running", "queued"} for r in runs.json()):
                raise RuntimeError("interactive_inference_active")
    with sqlite3.connect(
        (args.source_dir.resolve() / "cybersrs.db").as_uri() + "?mode=ro", uri=True
    ) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT r.*,p.description,p.analysis,p.answers FROM run r JOIN project p "
            "ON p.id=r.project_id WHERE r.id=?",
            (args.run_id,),
        ).fetchone()
    if row is None or row["status"] != "failed":
        raise ValueError("failed_source_run_required")
    checkpoints = json.loads(row["checkpoints"])
    if checkpoints["_request"].get("checkpoint_edits"):
        raise ValueError("unedited_source_run_required")
    rejected = checkpoints[f"_rejected_{args.section}"]
    content = rejected["content"]
    target_ids = {item["id"] for item in content["requirements"]}
    source_ids = {eid for item in content["requirements"] for eid in item["evidence_ids"]}
    analysis = Analysis.model_validate(json.loads(row["analysis"]))
    analysis = analysis.model_copy(
        update={
            "assessments": [item for item in analysis.assessments if item.evidence_id in source_ids]
        }
    )
    evidence = build_evidence(
        row["description"], [Answer.model_validate(a) for a in json.loads(row["answers"])]
    )
    prior = {key: value for key, value in checkpoints.items() if key in SECTION_SCHEMAS}
    partial = checkpoints.get(f"_partial_{args.section}", {})
    prior[args.section] = {
        "requirements": [
            item for item in partial.get("requirements", []) if item["id"] not in target_ids
        ]
    }
    sources = [
        SourceChunk.model_validate(s) for s in checkpoints.get("_sources", {}).get("chunks", [])
    ]
    out = settings.data_dir / "source-test-probes" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True)
    paths = sorted((root / "src/cybersrs").glob("*.py")) + [Path(__file__)]

    def snapshot() -> dict[str, str]:
        return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

    frozen = snapshot()
    (out / "manifest.json").write_text(
        json.dumps(
            {
                "scope": "single_rejected_source_test_completion_not_complete_srs",
                "source_run_id": args.run_id,
                "source_input_hash": row["input_hash"],
                "source_sha256": frozen,
                "scoped_assessment_ids": sorted(source_ids),
                "scoping_changes_source_or_labels": False,
                "requirement_repair_version": REQUIREMENT_REPAIR_VERSION,
                "assistant_section_edits": False,
                "human_approval": False,
            },
            indent=2,
        ),
        encoding="utf8",
    )
    (out / "original-rejection.json").write_text(json.dumps(rejected, indent=2), encoding="utf8")
    store = Repository(out)
    project = store.create_project("Source-scoped completion probe", row["description"])
    provider = RepairingOllamaProvider(settings)
    print(json.dumps({"probe_output": str(out.resolve())}), flush=True)
    started = time.monotonic()
    try:
        with audit_scope(store, project["id"]):
            repaired, models, attempts = complete_source_gaps(
                provider,
                args.section,
                content,
                {},
                evidence,
                analysis,
                sources,
                prior,
                threading.Event(),
                time.monotonic() + settings.generation_timeout_seconds,
            )
        errors = validate_section(args.section, repaired, evidence, analysis, sources, prior)
        result = {
            "status": "completed" if not errors else "failed",
            "content": repaired,
            "models": sorted(models),
            "attempts": attempts,
            "errors": errors,
            "semantic_review": "pending",
        }
    except Exception as error:
        result = {"status": "failed", "error": str(error)}
    result["seconds"] = time.monotonic() - started
    (out / "result.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    stable = frozen == snapshot()
    (out / "stability.json").write_text(json.dumps({"source_unchanged": stable}), encoding="utf8")
    print(json.dumps({k: v for k, v in result.items() if k != "content"}), flush=True)
    if not stable or result["status"] != "completed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""Exercise the real repair path on an unchanged rejected section, never a full-SRS proof."""

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
from cybersrs.knowledge import KnowledgeBase
from cybersrs.orchestrator import Orchestrator
from cybersrs.provider import CORRECTION_POLICY_VERSION, RepairingOllamaProvider
from cybersrs.repository import Repository
from cybersrs.schemas import REQUIREMENT_PREFIXES, SECTION_SCHEMAS, Analysis, Answer, SourceChunk


def main() -> None:
    """Keep historical inputs immutable and report every changed requirement field."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--section", choices=tuple(REQUIREMENT_PREFIXES), default="data")
    args = parser.parse_args()
    settings = Settings()
    root = Path(__file__).resolve().parents[1]
    with httpx.Client(base_url=f"http://127.0.0.1:{settings.backend_port}/api/v1") as client:
        response = client.get("/projects")
        response.raise_for_status()
        for project in response.json():
            runs = client.get(f"/projects/{project['id']}/runs")
            runs.raise_for_status()
            if any(r["status"] in {"running", "queued"} for r in runs.json()):
                raise RuntimeError("interactive_inference_active")
    uri = (args.source_dir.resolve() / "cybersrs.db").as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as source:
        source.row_factory = sqlite3.Row
        row = source.execute(
            "SELECT r.*,p.description,p.analysis,p.answers FROM run r "
            "JOIN project p ON p.id=r.project_id WHERE r.id=?",
            (args.run_id,),
        ).fetchone()
    if row is None or row["status"] != "failed":
        raise ValueError("failed_source_run_required")
    checkpoints = json.loads(row["checkpoints"])
    if checkpoints["_request"].get("checkpoint_edits"):
        raise ValueError("unedited_source_run_required")
    rejected = checkpoints[f"_rejected_{args.section}"]
    content = rejected["content"]
    analysis = Analysis.model_validate(json.loads(row["analysis"]))
    source_ids = {eid for item in content["requirements"] for eid in item["evidence_ids"]}
    analysis = analysis.model_copy(
        update={
            "assessments": [item for item in analysis.assessments if item.evidence_id in source_ids]
        }
    )
    evidence = build_evidence(
        row["description"], [Answer.model_validate(a) for a in json.loads(row["answers"])]
    )
    previous = {k: v for k, v in checkpoints.items() if k in SECTION_SCHEMAS and k != args.section}
    partial = checkpoints.get(f"_partial_{args.section}")
    if partial is not None:
        target_ids = {item["id"] for item in content["requirements"]}
        previous[args.section] = partial | {
            "requirements": [
                item for item in partial["requirements"] if item["id"] not in target_ids
            ]
        }
    sources = [SourceChunk.model_validate(s) for s in checkpoints["_sources"]["chunks"]]
    out = (
        settings.data_dir
        / ("rationale-repair-probes" if args.section == "data" else "source-repair-probes")
        / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    )
    out.mkdir(parents=True)
    paths = sorted((root / "src/cybersrs").glob("*.py")) + [Path(__file__)]

    def snapshot() -> dict[str, str]:
        return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

    original_snapshot = snapshot()
    (out / "manifest.json").write_text(
        json.dumps(
            {
                "scope": "actual_rejected_section_repair_not_complete_srs",
                "source_run_id": args.run_id,
                "source_input_hash": row["input_hash"],
                "scoped_assessment_ids": sorted(source_ids),
                "source_or_assessment_labels_changed": False,
                "source_sha256": original_snapshot,
                "correction_policy_version": CORRECTION_POLICY_VERSION,
                "assistant_section_edits": False,
                "human_approval": False,
            },
            indent=2,
        ),
        encoding="utf8",
    )
    (out / "original-rejection.json").write_text(json.dumps(rejected, indent=2), encoding="utf8")
    store = Repository(out)
    project = store.create_project("Actual rejected-section repair probe", row["description"])
    coordinator = Orchestrator(
        settings, store, RepairingOllamaProvider(settings), KnowledgeBase(settings)
    )
    print(json.dumps({"probe_output": str(out.resolve())}), flush=True)
    started = time.monotonic()
    try:
        with audit_scope(store, project["id"]):
            repaired, provenance = coordinator._repair_rejected_requirements(
                args.section,
                content,
                {},
                evidence,
                analysis,
                sources,
                previous,
                threading.Event(),
                time.monotonic() + settings.generation_timeout_seconds,
                rejected["model"],
            )
        output = repaired.model_dump()
        before = {r["id"]: r for r in content["requirements"]}
        changed = {
            r["id"]: [k for k, v in r.items() if v != before.get(r["id"], {}).get(k)]
            for r in output["requirements"]
        }
        result = {
            "status": "completed",
            "content": output,
            "changed_fields": changed,
            "provenance": provenance,
            "semantic_review": "pending",
        }
    except Exception as error:
        result = {"status": "failed", "error": str(error)}
    finally:
        coordinator.shutdown()
    result["seconds"] = time.monotonic() - started
    (out / "result.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    stable = original_snapshot == snapshot()
    (out / "stability.json").write_text(json.dumps({"source_unchanged": stable}), encoding="utf8")
    print(json.dumps({k: v for k, v in result.items() if k != "content"}), flush=True)
    if not stable or result["status"] != "completed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

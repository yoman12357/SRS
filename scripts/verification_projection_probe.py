"""Real trained-model classification over unchanged automatic acceptance criteria."""

from __future__ import annotations

import argparse
import hashlib
import json
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

from cybersrs.audit import audit_scope
from cybersrs.config import Settings
from cybersrs.provider import RepairingOllamaProvider
from cybersrs.repository import Repository, canonical_hash
from cybersrs.schemas import SECTION_SCHEMAS, Analysis, Evidence, SourceChunk
from cybersrs.verification_agent import generate_verification
from cybersrs.verification_projection import (
    VERIFICATION_PROJECTION_VERSION,
    criterion_inventory,
    verification_projection_issues,
)


def main() -> None:
    """Record actual model requests and preservation results without claiming a complete SRS."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-version", type=Path, required=True)
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
    raw = args.input_version.read_bytes()
    wrapper = json.loads(raw)
    document = wrapper["content"]
    if canonical_hash(document) != wrapper["content_hash"]:
        raise ValueError("input_artifact_content_hash_mismatch")
    previous = {
        key: document[key] for key in SECTION_SCHEMAS if key not in {"verification", "sdlc"}
    }
    inventory = criterion_inventory(previous)
    out = settings.data_dir / "verification-probes" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True)
    paths = sorted((root / "src/cybersrs").glob("*.py")) + [Path(__file__)]

    def snapshot() -> dict[str, str]:
        return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

    before = snapshot()
    (out / "manifest.json").write_text(
        json.dumps(
            {
                "scope": "criterion_preservation_and_classification_not_complete_srs",
                "source_sha256": before,
                "input_content_hash": wrapper["content_hash"],
                "input_artifact_sha256": hashlib.sha256(raw).hexdigest(),
                "verification_projection_version": VERIFICATION_PROJECTION_VERSION,
                "criterion_count": len(inventory),
                "assistant_section_edits": False,
                "human_approval": False,
            },
            indent=2,
        ),
        encoding="utf8",
    )
    store = Repository(out)
    project = store.create_project(
        "Unchanged acceptance verification probe", document["original_description"]
    )
    provider = RepairingOllamaProvider(settings)
    print(json.dumps({"probe_output": str(out.resolve())}), flush=True)
    started = time.monotonic()
    try:
        with audit_scope(store, project["id"]):
            content, provenance = generate_verification(
                provider,
                {},
                [Evidence.model_validate(e) for e in document["evidence"]],
                Analysis.model_validate(document["analysis"]),
                [SourceChunk.model_validate(s) for s in document["sources"]],
                previous,
                threading.Event(),
                time.monotonic() + settings.generation_timeout_seconds,
            )
        result = {
            "status": "completed",
            "content": content,
            "provenance": provenance,
            "preservation_issues": verification_projection_issues(content, previous),
            "semantic_review": "pending",
        }
    except Exception as error:
        result = {"status": "failed", "error": str(error)}
    result["seconds"] = time.monotonic() - started
    (out / "result.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    stable = before == snapshot() and args.input_version.read_bytes() == raw
    (out / "stability.json").write_text(
        json.dumps({"source_and_input_unchanged": stable}), encoding="utf8"
    )
    print(json.dumps({k: v for k, v in result.items() if k != "content"}), flush=True)
    if not stable or result["status"] != "completed" or result.get("preservation_issues"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

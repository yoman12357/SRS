"""Real native-decoder checks against unchanged automatic campus requirements."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

from cybersrs.audit import audit_scope
from cybersrs.category_metadata import (
    CATEGORY_METADATA_VERSION,
    empty_category_metadata,
    validate_empty_category_index,
)
from cybersrs.config import Settings
from cybersrs.provider import CORRECTION_POLICY_VERSION, RepairingOllamaProvider
from cybersrs.repository import Repository
from cybersrs.schemas import SECTION_SCHEMAS, Analysis, Evidence, RequirementsSection
from cybersrs.sdlc import rank_sdlc
from cybersrs.sdlc_agent import SDLC_PROMPT_VERSION, generate_sdlc
from cybersrs.validation import requirements_from, validate_section


def _snapshot(root: Path) -> dict[str, str]:
    """Freeze the actual backend modules and this probe without changing source artifacts."""
    paths = sorted((root / "src/cybersrs").glob("*.py")) + [Path(__file__)]
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main() -> None:
    """Record real category and Agile outputs; never present them as a complete correct SRS."""
    settings = Settings()
    root = Path(__file__).resolve().parents[1]
    with httpx.Client(base_url=f"http://127.0.0.1:{settings.backend_port}/api/v1", timeout=20) as c:
        projects = c.get("/projects")
        projects.raise_for_status()
        for project in projects.json():
            response = c.get(f"/projects/{project['id']}/runs")
            response.raise_for_status()
            if any(r["status"] in {"queued", "running"} for r in response.json()):
                raise RuntimeError("interactive_inference_active")
    original_path = settings.data_dir / "evaluations/20261028-045259-finetuned/campus.json"
    original_bytes = original_path.read_bytes()
    original = json.loads(original_bytes)
    document = original["content"]
    evidence = [Evidence.model_validate(item) for item in document["evidence"]]
    analysis = Analysis.model_validate(document["analysis"])
    previous = {key: document[key] for key in SECTION_SCHEMAS if key != "sdlc"}
    requirements = requirements_from(previous)
    out = (
        settings.data_dir
        / "category-lifecycle-probes"
        / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    )
    out.mkdir(parents=True)
    snapshot = _snapshot(root)
    manifest = {
        "scope": "native_decoder_and_section_gates_not_complete_srs",
        "source_sha256": snapshot,
        "input_content_hash": original["content_hash"],
        "input_artifact_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "category_metadata_version": CATEGORY_METADATA_VERSION,
        "correction_policy_version": CORRECTION_POLICY_VERSION,
        "sdlc_generation_version": SDLC_PROMPT_VERSION,
        "assistant_section_edits": False,
        "human_approval": False,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
    store = Repository(out)
    project = store.create_project(
        "Native source-projection probe", document["original_description"]
    )
    provider = RepairingOllamaProvider(settings)
    results = []
    print(json.dumps({"probe_output": str(out.resolve())}), flush=True)
    try:
        metadata = empty_category_metadata("network", [], requirements)

        def validate_category(candidate: RequirementsSection) -> list[str]:
            """Bind prose to the factual explanation while permitting only actual canonical IDs."""
            errors = validate_empty_category_index(candidate, metadata)
            if errors:
                return errors
            return validate_section(
                "network", candidate.model_dump(), evidence, analysis, [], previous
            )

        with audit_scope(store, project["id"]):
            for name in ("category", "sdlc"):
                started = time.monotonic()
                try:
                    if name == "category":
                        result, provenance = provider.generate(
                            "Return the requested category index as JSON. Use the frozen "
                            "explanation exactly and select existing requirement IDs relevant "
                            "to networking/interfaces. Introduce no requirement or test.",
                            {
                                "assigned_section": "network",
                                "existing_requirements": [
                                    {k: row[k] for k in ("id", "statement", "dimensions")}
                                    for row in requirements
                                ],
                                "frozen_category_metadata": metadata,
                            },
                            RequirementsSection,
                            threading.Event(),
                            time.monotonic() + settings.generation_timeout_seconds,
                            validate_category,
                        )
                        content = result.model_dump()
                    else:
                        content, provenance = generate_sdlc(
                            provider,
                            {
                                "assigned_section": "sdlc",
                                "project_title": analysis.title,
                                "analysis": {
                                    "domain": analysis.domain,
                                    "stakeholders": analysis.stakeholders,
                                    "unresolved_decisions": analysis.unresolved_decisions,
                                },
                                "evidence": [item.model_dump() for item in evidence],
                                "sources": [],
                                "existing_requirements": requirements,
                                "compliance_applicability": document["compliance"],
                                "sdlc_decision": rank_sdlc(evidence),
                                "verification_context": [
                                    {
                                        key: test[key]
                                        for key in (
                                            "id",
                                            "requirement_ids",
                                            "test_type",
                                            "expected_result",
                                        )
                                    }
                                    for test in document["verification"]["tests"]
                                ],
                            },
                            evidence,
                            analysis,
                            [],
                            previous,
                            threading.Event(),
                            time.monotonic() + settings.generation_timeout_seconds,
                        )
                    row = {
                        "case": name,
                        "status": "completed",
                        "content": content,
                        "provenance": provenance,
                        "seconds": time.monotonic() - started,
                        "semantic_review": "pending",
                    }
                except Exception as error:
                    row = {
                        "case": name,
                        "status": "failed",
                        "error": str(error),
                        "seconds": time.monotonic() - started,
                    }
                results.append(row)
                (out / f"{name}.json").write_text(json.dumps(row, indent=2), encoding="utf8")
                (out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf8")
                print(json.dumps({k: v for k, v in row.items() if k != "content"}), flush=True)
    finally:
        stable = snapshot == _snapshot(root) and original_path.read_bytes() == original_bytes
        (out / "stability.json").write_text(
            json.dumps({"source_and_input_unchanged": stable}), encoding="utf8"
        )
    if not stable or any(row["status"] != "completed" for row in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

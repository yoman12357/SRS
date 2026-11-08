"""Verify reused assets without changing training labels or held-out splits."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from pydantic import ValidationError

from cybersrs import prompts
from cybersrs.schemas import (
    Analysis,
    ArchitectureSection,
    Document,
    QualityReport,
    RequirementsSection,
    ThreatSection,
)

TARGET_SCHEMAS = {
    "architecture": ArchitectureSection,
    "clarification_questions": Analysis,
    "context_extraction": Analysis,
    "data_requirements": RequirementsSection,
    "functional_requirements": RequirementsSection,
    "network_requirements": RequirementsSection,
    "non_functional_requirements": RequirementsSection,
    "requirement_validation": QualityReport,
    "security_requirements": RequirementsSection,
    "srs_generation": Document,
    "threat_model": ThreatSection,
}


def audit(root: Path) -> dict:
    """Compare copied bytes with their original manifest and inventory dataset tasks."""
    manifest = json.loads((root / "docs/reference/ASSET_MANIFEST.json").read_text("utf-8"))
    failures = []
    local_assets_not_present = []
    for entry in manifest["files"]:
        path = root / entry["path"]
        if not path.is_file():
            if path.suffix == ".safetensors" or (
                path.suffix == ".pdf" and "CyberSRS_Strict_Cybersecurity_Networking_SRS_50"
                in path.parts
            ):
                local_assets_not_present.append(entry["path"])
            else:
                failures.append({"path": entry["path"], "reason": "missing"})
        elif hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            failures.append({"path": entry["path"], "reason": "hash_mismatch"})
    tasks: Counter = Counter()
    parse_errors = []
    schema_audit = {}
    for directory in (root / "ai/finetuning/data_test", root / "ai/finetuning/data_test2"):
        for path in directory.glob("*.jsonl"):
            for index, line in enumerate(path.read_text("utf-8-sig").splitlines(), start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    key = f"{directory.name}/{path.stem}"
                    tasks[key] += 1
                except ValueError:
                    parse_errors.append({"file": str(path.relative_to(root)), "line": index})
                    continue
                target = TARGET_SCHEMAS.get(path.stem)
                if target is None:
                    continue
                summary = schema_audit.setdefault(
                    key,
                    {
                        "current_schema": target.__name__,
                        "valid_targets": 0,
                        "incompatible_targets": 0,
                        "error_types": Counter(),
                        "historical_system_prompt_hashes": set(),
                    },
                )
                messages = record.get("messages", [])
                for message in messages:
                    if message.get("role") == "system":
                        summary["historical_system_prompt_hashes"].add(
                            hashlib.sha256(message.get("content", "").encode()).hexdigest()
                        )
                assistant = next(
                    (
                        item.get("content", "")
                        for item in reversed(messages)
                        if item.get("role") == "assistant"
                    ),
                    "",
                )
                try:
                    target.model_validate_json(assistant)
                    summary["valid_targets"] += 1
                except ValidationError as exc:
                    summary["incompatible_targets"] += 1
                    summary["error_types"].update(
                        error["type"] for error in exc.errors(include_input=False)
                    )
    for summary in schema_audit.values():
        summary["error_types"] = dict(summary["error_types"])
        summary["historical_system_prompt_hashes"] = sorted(
            summary["historical_system_prompt_hashes"]
        )
    held_out = root / "ai/evaluation/dataset.json"
    return {
        "verified_files": len(manifest["files"]) - len(failures) - len(local_assets_not_present),
        "asset_failures": failures,
        "local_assets_not_present": local_assets_not_present,
        "task_counts": dict(tasks),
        "historical_json_parse_errors": parse_errors,
        "current_prompt_version": prompts.PROMPT_VERSION,
        "historical_target_schema_audit": schema_audit,
        "schema_audit_limitations": "Direct validation only; no lossful projection, invented "
        "labels or semantic acceptance. Historical context/question tasks now share Analysis. "
        "No split reassignment or training is performed.",
        "held_out_sha256": hashlib.sha256(held_out.read_bytes()).hexdigest(),
        "training_performed": False,
        "historical_labels_changed": False,
        "runtime_training_ready": False,
        "reason": "Historical target schemas differ from the new section-agent schemas. "
        "Projection and semantic review are required before any retraining. "
        "Missing threats, citations or lifecycle labels must not be fabricated.",
    }


def main() -> None:
    """Save an auditable inventory and fail only on asset corruption or invalid source JSON."""
    root = Path(__file__).resolve().parents[1]
    report = audit(root)
    output = root / "docs/ASSET_AUDIT.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["asset_failures"] or report["historical_json_parse_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

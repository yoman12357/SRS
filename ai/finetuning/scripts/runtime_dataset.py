"""Audit historical records and prepare scenario-grouped current-runtime candidates.

No training is performed. Historical datasets and held-out evaluation cases are
never rewritten. Prepared records require human semantic review before training.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from ai.finetuning.scripts.generate_dataset import _build_context_payload, _full_srs_payload
from ai.finetuning.scripts.scenario_library import SCENARIOS
from src.prompts.srs import (
    SRS_FOUNDATION_SYSTEM_PROMPT,
    SRS_REQUIREMENTS_SYSTEM_PROMPT,
    SRS_SUPPORTING_SYSTEM_PROMPT,
)
from src.schemas.srs import SRSSchema
from src.schemas.srs_draft import FoundationDraft, RequirementsDraft, SupportingDraft
from src.services.srs_generation_service import SRSGenerationService

RUNTIME_CONTRACTS: dict[str, tuple[type[BaseModel], str]] = {
    "srs_foundation": (FoundationDraft, SRS_FOUNDATION_SYSTEM_PROMPT),
    "srs_requirements": (RequirementsDraft, SRS_REQUIREMENTS_SYSTEM_PROMPT),
    "srs_supporting": (SupportingDraft, SRS_SUPPORTING_SYSTEM_PROMPT),
}


def _normalized(value: str) -> str:
    """Normalize descriptions for the frozen held-out exclusion boundary."""
    return " ".join(value.casefold().split())


def _assistant_payload(record: dict[str, Any]) -> dict[str, Any]:
    """Read one JSON-only assistant training target without recovery heuristics."""
    messages = record.get("messages", [])
    content = next(
        message["content"] for message in reversed(messages) if message["role"] == "assistant"
    )
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise ValueError("Assistant target must be a JSON object")
    return payload


def audit_runtime_dataset(data_dir: Path) -> dict[str, Any]:
    """Measure runtime contract/prompt mismatch without changing historical files."""
    counts: Counter[str] = Counter()
    findings: list[dict[str, str]] = []
    records = 0
    for path in sorted(data_dir.glob("*.jsonl")):
        if path.name in {"train.jsonl", "validation.jsonl"}:
            continue  # audit original task files once, not their split copies
        for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            if not line.strip():
                continue
            records += 1
            try:
                record = json.loads(line)
                task = str(record.get("task", "unknown"))
                counts[task] += 1
                payload = _assistant_payload(record)
                if task == "srs_generation":
                    SRSSchema.model_validate(payload)
                    findings.append(
                        {
                            "record_id": str(record.get("record_id", line_number)),
                            "code": "legacy_canonical_target",
                            ("detail"): (
                                "Canonical SRS target differs from the three act"
                                "ive compact bundles."
                            ),
                        }
                    )
                elif task in RUNTIME_CONTRACTS:
                    schema, prompt = RUNTIME_CONTRACTS[task]
                    schema.model_validate(payload)
                    if record["messages"][0]["content"] != prompt:
                        findings.append(
                            {
                                "record_id": str(record.get("record_id", line_number)),
                                "code": "stale_runtime_prompt",
                                "detail": task,
                            }
                        )
            except (ValueError, KeyError, StopIteration, TypeError) as exc:
                findings.append(
                    {
                        "record_id": f"{path.name}:{line_number}",
                        "code": "invalid_record",
                        "detail": type(exc).__name__,
                    }
                )
    missing = sorted(set(RUNTIME_CONTRACTS) - counts.keys())
    return {
        "data_dir": str(data_dir),
        "record_count": records,
        "task_counts": dict(counts),
        "missing_runtime_tasks": missing,
        "findings": findings,
        "runtime_alignment": "aligned"
        if records and not missing and not findings
        else "requires_review",
        "sdlc_training": "No SDLC task is present unless explicitly listed in task_counts.",
        "semantic_quality": "Requires human review; schema alignment does not prove correctness.",
    }


def project_runtime_targets(
    document: SRSSchema,
    rejections: dict[str, Any] | None = None,
) -> dict[str, BaseModel]:
    """Project each independently valid bundle, reporting incomplete historical targets."""
    data = document.model_dump(mode="json")
    foundation = {
        "project_overview": data["project_overview"],
        "scope": data["scope"],
        "assumptions": data["assumptions"],
        "stakeholders": data["stakeholders"],
        "roles": data["role_definitions"]
        or [
            {
                "name": role,
                "responsibilities": ["Responsibilities require stakeholder confirmation."],
                "permissions": ["Permissions require stakeholder confirmation."],
            }
            for role in document.user_roles
        ],
    }
    requirements = {
        section: [
            {
                "id": item.id,
                "title": item.title,
                "statement": item.statement,
                "rationale": item.rationale,
                "acceptance_criteria": item.acceptance_criteria,
                "priority": item.priority.value,
                "dependencies": list(item.dependencies),
                "source_ids": [],
            }
            for item in values
        ]
        for section, values in document.requirement_sections().items()
    }
    supporting = {
        "architecture_summary": {
            key: data["architecture_summary"][key]
            for key in ("overview", "components", "data_flows", "deployment_notes")
        },
        "threats": [
            {
                **{
                    key: item[key]
                    for key in (
                        "threat_id",
                        "name",
                        "description",
                        "category",
                        "likelihood",
                        "impact",
                        "risk_rating_rationale",
                        "attack_scenario",
                        "affected_assets",
                        "related_requirement_ids",
                    )
                },
                "mitigation": " ".join(
                    mitigation["description"] for mitigation in item["mitigations"]
                ),
            }
            for item in data["threats"]
        ],
        "risks": [
            {key: item[key] for key in ("description", "likelihood", "impact", "mitigation")}
            for item in data["risks"]
        ],
        "glossary": data["glossary"],
        "unresolved_questions": data["unresolved_questions"],
    }
    targets: dict[str, BaseModel] = {}
    for task, payload in (
        ("srs_foundation", foundation),
        ("srs_requirements", requirements),
        ("srs_supporting", supporting),
    ):
        try:
            targets[task] = RUNTIME_CONTRACTS[task][0].model_validate(payload)
        except ValidationError as exc:
            if rejections is None:
                raise
            rejections[task] = [
                {"location": list(error["loc"]), "type": error["type"]} for error in exc.errors()
            ]
    return targets


def prepare_runtime_dataset(output_dir: Path, evaluation_path: Path) -> dict[str, Any]:
    """Prepare validated candidates with a deterministic scenario-level holdout.

    Invalid bundle targets are rejected rather than padded or truncated.
    Evaluation descriptions are excluded first; every retained bundle from a
    scenario remains in the same split. Missing tasks prevent training readiness.
    """
    if output_dir.exists():
        raise ValueError("Choose a new output directory; existing datasets are never overwritten")
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8-sig"))
    excluded = {
        _normalized(str(case.get("description", "")))
        for case in evaluation
        if isinstance(case, dict)
    }
    records: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for scenario in SCENARIOS:
        description = str(scenario["description"])
        if _normalized(description) in excluded:
            rejected.append({"scenario_id": scenario["id"], "reason": "held_out_description"})
            continue
        try:
            document = SRSSchema.model_validate(_full_srs_payload(scenario))
            failed_targets: dict[str, Any] = {}
            targets = project_runtime_targets(document, failed_targets)
            rejected.extend(
                {
                    "scenario_id": scenario["id"],
                    "task": task,
                    "reason": "incomplete_historical_target",
                    "errors": errors,
                }
                for task, errors in failed_targets.items()
            )
        except (ValidationError, ValueError, KeyError) as exc:
            rejected.append(
                {
                    "scenario_id": scenario["id"],
                    "reason": "projection_validation",
                    "errors": [
                        {"location": list(error["loc"]), "type": error["type"]}
                        for error in exc.errors()
                    ]
                    if isinstance(exc, ValidationError)
                    else [type(exc).__name__],
                }
            )
            continue
        context = SRSGenerationService._compact_srs_model_context(_build_context_payload(scenario))
        for task, target in targets.items():
            payload: dict[str, Any] = {"project_context": context}
            if task == "srs_supporting":
                payload["available_requirements"] = [
                    {"id": item.id, "title": item.title}
                    for values in document.requirement_sections().values()
                    for item in values
                ]
            records.append(
                {
                    "record_id": f"{scenario['id']}|{task}",
                    "scenario_id": scenario["id"],
                    "task": task,
                    "schema_name": type(target).__name__,
                    "review_status": "candidate_requires_human_review",
                    "messages": [
                        {"role": "system", "content": RUNTIME_CONTRACTS[task][1]},
                        {"role": "user", "content": json.dumps(payload, separators=(",", ":"))},
                        {"role": "assistant", "content": target.model_dump_json()},
                    ],
                }
            )
    output_dir.mkdir(parents=True)
    split_counts: dict[str, int] = {}
    for split in ("train", "validation"):
        selected = [
            record
            for record in records
            if (int(hashlib.sha256(record["scenario_id"].encode()).hexdigest(), 16) % 5 == 0)
            == (split == "validation")
        ]
        split_counts[split] = len(selected)
        (output_dir / f"{split}.jsonl").write_text(
            "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in selected),
            encoding="utf-8",
        )
    for task in RUNTIME_CONTRACTS:
        (output_dir / f"{task}.jsonl").write_text(
            "".join(
                json.dumps(record, ensure_ascii=False) + "\n"
                for record in records
                if record["task"] == task
            ),
            encoding="utf-8",
        )
    manifest = {
        "contract_version": "professor-brief-1.0",
        "model_family": "Qwen/Qwen3-4B-Instruct-2507",
        "record_count": len(records),
        "task_counts": dict(Counter(record["task"] for record in records)),
        "split_counts": split_counts,
        "split_unit": "scenario_id",
        "rejected_scenarios": rejected,
        "evaluation_sha256": hashlib.sha256(evaluation_path.read_bytes()).hexdigest(),
        "review_status": "candidate_requires_human_review",
        "training_performed": False,
        "missing_runtime_tasks": sorted(
            set(RUNTIME_CONTRACTS) - {record["task"] for record in records}
        ),
        "training_ready": False,
        "limitations": [
            "Synthetic authored scenarios; no live user descriptions are used.",
            (
                "No SDLC reasoning targets are invented; base Qwen follows the d"
                "eterministic ranking contract."
            ),
            (
                "No source-backed citation examples are invented when scenarios "
                "contain no retrieved chunks."
            ),
            "Human semantic review and held-out evaluation are required before adapter promotion.",
        ],
    }
    (output_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    """Audit historical tasks or write a new, explicitly unapproved runtime candidate set."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit")
    audit.add_argument("--data-dir", type=Path, required=True)
    audit.add_argument("--report", type=Path, required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--output-dir", type=Path, required=True)
    prepare.add_argument("--evaluation", type=Path, default=Path("ai/evaluation/dataset.json"))
    args = parser.parse_args()
    if args.command == "audit":
        result = audit_runtime_dataset(args.data_dir)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(
            json.dumps({key: value for key, value in result.items() if key != "findings"}, indent=2)
        )
    else:
        canonical_evaluation = Path(__file__).resolve().parents[2] / "evaluation" / "dataset.json"
        if args.evaluation.resolve() != canonical_evaluation.resolve():
            parser.error(
                "Preparation must preserve the canonical ai/evaluation/dataset.json boundary"
            )
        result = prepare_runtime_dataset(args.output_dir, args.evaluation)
        print(
            json.dumps(
                {
                    **{key: value for key, value in result.items() if key != "rejected_scenarios"},
                    "rejected_scenario_count": len(result["rejected_scenarios"]),
                    "first_rejections": result["rejected_scenarios"][:3],
                },
                indent=2,
            )
        )
        if result["record_count"] == 0 or result["missing_runtime_tasks"]:
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Reproduce one failed source repair locally without saving a document or approval."""

from __future__ import annotations

import argparse
import json
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from cybersrs import prompts
from cybersrs.config import Settings
from cybersrs.evidence import build_evidence
from cybersrs.knowledge import KnowledgeBase
from cybersrs.orchestrator import Orchestrator, input_hash
from cybersrs.provider import OUTPUT_MODEL, GenerationError, RepairingOllamaProvider
from cybersrs.repository import Repository
from cybersrs.schemas import REQUIREMENT_PREFIXES, Analysis, Answer, SourceChunk

T = TypeVar("T", bound=BaseModel)


class ProbeProvider(RepairingOllamaProvider):
    """Keep parsed rejected artifacts in a private probe directory, never stdout logs."""

    def __init__(self, settings: Settings) -> None:
        """Use actual local inference and collect only schema-parsed diagnostic objects."""
        super().__init__(settings)
        self.rejected: list[dict] = []

    def generate(
        self,
        system: str,
        context: dict,
        schema: type[T],
        cancel: threading.Event,
        deadline: float,
        validate: Callable[[T], list[str]] | None = None,
    ) -> tuple[T, dict]:
        """Execute the production gate while retaining a source-private diagnostic artifact."""

        def checked(candidate: T) -> list[str]:
            """Record rejected parsed content separately from safe runtime error codes."""
            errors = validate(candidate) if validate else []
            if errors:
                self.rejected.append(
                    {
                        "schema": schema.__name__,
                        "model": OUTPUT_MODEL.get(),
                        "errors": errors,
                        "content": candidate.model_dump(),
                    }
                )
            return errors

        return super().generate(system, context, schema, cancel, deadline, checked)


def main() -> None:
    """Repair the selected failed source using real model calls and private output artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--section", choices=list(REQUIREMENT_PREFIXES), required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--data-dir", type=Path)
    args = parser.parse_args()
    settings = Settings()
    if args.data_dir:
        settings = settings.model_copy(update={"data_dir": args.data_dir})
    repository = Repository(settings.data_dir)
    run = repository.get_run(args.run_id)
    project = repository.get_project(run["project_id"])
    if run["input_hash"] != input_hash(project):
        raise SystemExit("Probe requires unchanged original project inputs")
    rejected = run["checkpoints"][f"_rejected_{args.section}"]
    content = rejected["content"] | {
        "requirements": [
            row
            for row in rejected["content"]["requirements"]
            if args.source_id in row["evidence_ids"]
        ]
    }
    if not content["requirements"]:
        raise SystemExit("No rejected requirement matches this source")
    analysis = Analysis.model_validate(project["analysis"])
    analysis = analysis.model_copy(
        update={
            "assessments": [
                item for item in analysis.assessments if item.evidence_id == args.source_id
            ]
        }
    )
    predecessors = {
        key: value
        for key, value in run["checkpoints"].items()
        if key in REQUIREMENT_PREFIXES and key != args.section
    }
    predecessors[args.section] = {
        "requirements": [
            row
            for row in run["checkpoints"]
            .get(f"_partial_{args.section}", {})
            .get("requirements", [])
            if args.source_id not in row["evidence_ids"]
        ]
    }
    sources = [
        SourceChunk.model_validate(item)
        for item in run["checkpoints"].get("_sources", {}).get("chunks", [])
    ]
    provider = ProbeProvider(settings)
    coordinator = Orchestrator(settings, repository, provider, KnowledgeBase(settings))
    output = settings.data_dir / "repair-probes" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    output.mkdir(parents=True, exist_ok=False)
    report = {
        "prompt_version": prompts.PROMPT_VERSION,
        "source_run": run["id"],
        "source_id": args.source_id,
        "status": "failed",
        "human_approval": False,
    }
    try:
        result, provenance = coordinator._repair_rejected_requirements(
            args.section,
            content,
            {"assigned_section": args.section, "sources": []},
            build_evidence(
                project["description"], [Answer.model_validate(a) for a in project["answers"]]
            ),
            analysis,
            sources,
            predecessors,
            threading.Event(),
            time.monotonic() + settings.generation_timeout_seconds,
            rejected.get("model", settings.model_name),
        )
        report.update(status="completed", section=result.model_dump(), provenance=provenance)
    except GenerationError as exc:
        report["error"] = str(exc)
    finally:
        coordinator.shutdown()
        (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf8")
        (output / "rejected.json").write_text(
            json.dumps(provider.rejected, indent=2), encoding="utf8"
        )
    print(json.dumps({"status": report["status"], "output": str(output.resolve())}))
    if report["status"] != "completed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

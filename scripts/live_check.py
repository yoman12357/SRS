"""Real local-model evaluation. Never fabricates stakeholder answers or approvals."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from cybersrs.artifact_grounding import VALIDATION_POLICY_VERSION
from cybersrs.config import Settings
from cybersrs.exports import render_markdown, render_pdf
from cybersrs.knowledge import KnowledgeBase
from cybersrs.orchestrator import Orchestrator
from cybersrs.provider import OllamaProvider, RepairingOllamaProvider
from cybersrs.repository import Repository

from .heldout_compare import _model_digests, _snapshot

CASES = {
    "campus": {
        "description": (
            "Build a campus wireless network access-control requirements specification. "
            "Students and guests may access the internet but must not access "
            "the internal staff network. "
            "Network administrators may manually isolate a device and restore its access. "
            "Security operators may review and acknowledge alerts but may not "
            "change access policies. "
            "The system must record administrator policy changes and retain "
            "audit records for 30 days. "
            "The planning population is 2000 registered devices; concurrency is not yet decided. "
            "Do not automatically change firewall rules or isolate devices. "
            "Requirements evolve frequently and stakeholders provide weekly stakeholder feedback. "
            "Budget, delivery schedule, response-time thresholds and mandatory "
            "regulatory frameworks "
            "are undecided and must remain open decisions."
        ),
        "expected_sdlc": "Agile",
    },
    "vpn": {
        "description": (
            "Specify a secure remote-access VPN for a research institute. "
            "Employees authenticate with multi-factor authentication before accessing "
            "approved research services. "
            "Contractors may access only the support portal and must be denied "
            "research data access. "
            "Administrators manage remote-access permissions; support operators may "
            "inspect connection logs "
            "but cannot grant permissions. "
            "The system must retain connection logs for 14 days and remove them "
            "after retention expires. "
            "Plan for 250 registered users and 25 simultaneous sessions. "
            "Automatic firewall reconfiguration and active vulnerability scanning "
            "are out of scope. "
            "This project has stable requirements and requires independent verification "
            "before release. "
            "No continuous delivery is planned. Budget, schedule and protocol choices "
            "are undecided."
        ),
        "expected_sdlc": "V-Model",
    },
}


def main() -> None:
    """Persist actual model outcomes and export only completed canonical reports."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=["finetuned", "base"], default="finetuned")
    parser.add_argument("--cases", nargs="+", choices=list(CASES), default=list(CASES))
    parser.add_argument("--resume-dir", type=Path)
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Evaluate adapter-first policy with explicitly reported base correction",
    )
    args = parser.parse_args()
    original = Settings()
    root = Path(__file__).resolve().parents[1]
    snapshot = _snapshot(root)
    snapshot["scripts/live_check.py"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    output = args.resume_dir or original.data_dir / "evaluations" / f"{stamp}-{args.variant}"
    output.mkdir(parents=True, exist_ok=args.resume_dir is not None)
    (output / f"manifest-{stamp}.json").write_text(
        json.dumps(
            {
                "source_sha256": snapshot,
                "models": _model_digests(original),
                "validation_policy_version": VALIDATION_POLICY_VERSION,
                "case_inputs": {key: CASES[key] for key in args.cases},
                "resume": args.resume_dir is not None,
                "assistant_edits": False,
                "human_approval": "not_requested_or_recorded",
                "case_type": "authored_development_regressions_not_unseen_evaluation",
            },
            indent=2,
        ),
        encoding="utf8",
    )
    settings = original.model_copy(
        update={
            "data_dir": output,
            "model_name": original.base_model_name
            if args.variant == "base"
            else original.model_name,
        }
    )
    # Reuse the same read-only knowledge corpus for a fair base/adapter comparison.
    knowledge = KnowledgeBase(original)
    repository = Repository(output)
    provider = RepairingOllamaProvider(settings) if args.repair else OllamaProvider(settings)
    coordinator = Orchestrator(settings, repository, provider, knowledge)
    summary = []
    print(
        json.dumps({"evaluation_output": str(output.resolve()), "model": settings.model_name}),
        flush=True,
    )
    try:
        for key in args.cases:
            case = CASES[key]
            existing = (
                [
                    item
                    for item in repository.list_projects()
                    if item["name"] == f"Evaluation: {key}"
                ]
                if args.resume_dir
                else []
            )
            project = (
                existing[0]
                if existing
                else repository.create_project(
                    f"Evaluation: {key}",
                    case["description"],
                )
            )
            started = time.monotonic()
            for kind in ["generate"] if existing else ["analyse", "generate"]:
                if existing:
                    previous = repository.list_runs(project["id"])[0]
                    run = coordinator.retry(previous["id"])
                else:
                    run = coordinator.start(project["id"], kind)
                last_event = None
                while True:
                    run = repository.get_run(run["id"])
                    event = run["events"][-1] if run["events"] else None
                    if event != last_event:
                        print(
                            json.dumps(
                                {"case": key, "kind": kind, "event": event, "status": run["status"]}
                            ),
                            flush=True,
                        )
                        last_event = event
                    if run["status"] not in {"running", "queued"}:
                        break
                    time.sleep(1)
                (output / f"{key}-{kind}-run.json").write_text(
                    json.dumps(run, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                if run["status"] != "completed":
                    break
            versions = repository.list_versions(project["id"])
            result = {
                "case": key,
                "status": run["status"],
                "error": run["error"],
                "seconds": round(time.monotonic() - started, 1),
                "model": provider.model_name,
                "base_repair_enabled": args.repair,
                "human_approval": "not_requested_or_recorded",
            }
            if versions:
                version = repository.get_version(project["id"], versions[0]["id"])
                (output / f"{key}.json").write_text(json.dumps(version, indent=2), encoding="utf-8")
                (output / f"{key}.md").write_text(render_markdown(version, []), encoding="utf-8")
                (output / f"{key}.pdf").write_bytes(render_pdf(version, []))
                selected = version["content"]["sdlc"]["selected_model"]
                result.update(
                    {
                        "sdlc": selected,
                        "expected_sdlc": case["expected_sdlc"],
                        "sdlc_matches": selected == case["expected_sdlc"],
                        "quality": version["quality"]["status"],
                        "requirements": len(version["quality"]["traceability"]),
                        "actual_models_used": version["content"]["models_used"],
                    }
                )
            summary.append(result)
            (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
            print(json.dumps(result), flush=True)
    finally:
        coordinator.shutdown()
        current = _snapshot(root)
        current["scripts/live_check.py"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        (output / f"stability-{stamp}.json").write_text(
            json.dumps({"source_unchanged": snapshot == current}), encoding="utf8"
        )
    if any(item["status"] != "completed" or not item.get("sdlc_matches") for item in summary):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""Matched adapter/base evaluation on unchanged historical held-out descriptions."""

from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

from cybersrs import prompts
from cybersrs.config import Settings
from cybersrs.exports import render_markdown, render_pdf
from cybersrs.inference_privacy import PRIVACY_POLICY_VERSION
from cybersrs.knowledge import KnowledgeBase
from cybersrs.orchestrator import Orchestrator
from cybersrs.provider import OllamaProvider
from cybersrs.repository import Repository
from cybersrs.sdlc_agent import SDLC_PROMPT_VERSION

SELECTED_IDS = ("eval-001", "eval-006")


def _snapshot(root: Path) -> dict[str, str]:
    """Freeze the production modules and this evaluator's source bytes."""
    files = {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((root / "src/cybersrs").glob("*.py"))
    }
    files["scripts/heldout_compare.py"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return files


def _model_digests(settings: Settings) -> dict[str, str | None]:
    """Identify the actual installed model blobs without loading or downloading them."""
    response = httpx.get(settings.ollama_base_url + "/api/tags", timeout=15, follow_redirects=False)
    response.raise_for_status()
    installed = {item["name"]: item.get("digest") for item in response.json().get("models", [])}
    return {
        model: installed.get(model if ":" in model else model + ":latest")
        for model in (settings.model_name, settings.base_model_name, settings.embedding_model)
    }


def _watch(repository: Repository, run_id: str, label: str) -> dict:
    """Persist terminal evaluation state while reporting only stage/status changes."""
    previous = None
    while True:
        run = repository.get_run(run_id)
        last = run["events"][-1] if run["events"] else {}
        state = (run["status"], last.get("agent"), last.get("state"))
        if state != previous:
            print(json.dumps({"case": label, "run_id": run_id, "state": state}), flush=True)
            previous = state
        if run["status"] not in {"queued", "running"}:
            return run
        time.sleep(1)


def main() -> None:
    """Evaluate both exact models without fabricated answers, labels or human approval."""
    settings = Settings()
    root = Path(__file__).resolve().parents[1]
    # Do not overlap inference from the interactive app with this direct evaluator.
    with httpx.Client(
        base_url=f"http://127.0.0.1:{settings.backend_port}/api/v1", timeout=15
    ) as client:
        projects = client.get("/projects")
        projects.raise_for_status()
        for project in projects.json():
            runs = client.get(f"/projects/{project['id']}/runs")
            runs.raise_for_status()
            if any(run["status"] in {"queued", "running"} for run in runs.json()):
                raise RuntimeError("interactive_workflow_active_do_not_overlap_evaluations")

    dataset = root / "ai/evaluation/dataset.json"
    original_bytes = dataset.read_bytes()
    dataset_hash = hashlib.sha256(original_bytes).hexdigest()
    inventory = {item["id"]: item for item in json.loads(original_bytes)}
    cases = [inventory[case_id] for case_id in SELECTED_IDS]
    snapshot = _snapshot(root)
    model_digests = _model_digests(settings)
    output = settings.data_dir / "heldout-comparisons" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "prompt_version": prompts.PROMPT_VERSION,
        "sdlc_prompt_version": SDLC_PROMPT_VERSION,
        "privacy_policy_version": PRIVACY_POLICY_VERSION,
        "dataset_sha256": dataset_hash,
        "selected_ids": SELECTED_IDS,
        "cases": cases,
        "source_sha256": snapshot,
        "models": {"finetuned": settings.model_name, "base": settings.base_model_name},
        "model_digests": model_digests,
        "same_settings": {
            "num_ctx": settings.ollama_num_ctx,
            "num_predict": settings.ollama_num_predict,
            "max_retries": settings.llm_max_retries,
            "temperature": 0,
            "timeout_seconds": settings.generation_timeout_seconds,
            "rag_top_k": settings.rag_top_k,
            "rag_min_score": settings.rag_min_score,
        },
        "base_correction": False,
        "human_approval": "not_requested_or_recorded",
        "limitations": [
            "Two preselected descriptions, not a statistically adequate improvement study.",
            "Historical category labels are not current SRS, threat or SDLC gold targets.",
            "No missing SDLC labels, citations, scenarios or stakeholder answers are invented.",
            "Open questions remain unanswered; no stakeholder decisions are fabricated.",
            "Output completeness, entailment and methodology need separate content review.",
            "Case order is fixed; elapsed time includes model loading and cache effects.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
    print(json.dumps({"heldout_output": str(output.resolve())}), flush=True)
    results = []
    knowledge = KnowledgeBase(settings)
    try:
        for variant, model in manifest["models"].items():
            variant_settings = settings.model_copy(
                update={
                    "data_dir": output / variant,
                    "model_name": model,
                    "base_repair_enabled": False,
                }
            )
            repository = Repository(variant_settings.data_dir)
            coordinator = Orchestrator(
                variant_settings, repository, OllamaProvider(variant_settings), knowledge
            )
            try:
                for case in cases:
                    started = time.monotonic()
                    project = repository.create_project(case["id"], case["description"])
                    label = f"{variant}/{case['id']}"
                    for kind in ("analyse", "generate"):
                        run = coordinator.start(project["id"], kind)
                        run = _watch(repository, run["id"], label + "/" + kind)
                        (variant_settings.data_dir / f"{case['id']}-{kind}.json").write_text(
                            json.dumps(run, indent=2), encoding="utf8"
                        )
                        if run["status"] != "completed":
                            break
                    row = {
                        "variant": variant,
                        "case_id": case["id"],
                        "model": model,
                        "status": run["status"],
                        "error": run["error"],
                        "seconds": round(time.monotonic() - started, 3),
                        "human_approval": "not_requested_or_recorded",
                        "semantic_review": "pending",
                        "pdf_visual_review": "pending",
                        "expected_sdlc": None,
                    }
                    versions = repository.list_versions(project["id"])
                    if versions:
                        version = repository.get_version(project["id"], versions[0]["id"])
                        stem = variant_settings.data_dir / case["id"]
                        stem.with_suffix(".json").write_text(
                            json.dumps(version, indent=2), encoding="utf8"
                        )
                        stem.with_suffix(".md").write_text(
                            render_markdown(version, []), encoding="utf8"
                        )
                        stem.with_suffix(".pdf").write_bytes(render_pdf(version, []))
                        row.update(
                            content_hash=version["content_hash"],
                            quality=version["quality"]["status"],
                            actual_models=version["content"]["models_used"],
                            sdlc=version["content"]["sdlc"]["selected_model"],
                            requirements=len(version["quality"]["traceability"]),
                        )
                    results.append(row)
                    (output / "results.json").write_text(
                        json.dumps(results, indent=2), encoding="utf8"
                    )
                    print(json.dumps(row), flush=True)
            finally:
                coordinator.shutdown()
    finally:
        stable = _snapshot(root) == snapshot
        unchanged = hashlib.sha256(dataset.read_bytes()).hexdigest() == dataset_hash
        models_unchanged = _model_digests(settings) == model_digests
        (output / "stability.json").write_text(
            json.dumps(
                {
                    "source_unchanged": stable,
                    "dataset_unchanged": unchanged,
                    "model_digests_unchanged": models_unchanged,
                }
            ),
            encoding="utf8",
        )
    if not stable or not unchanged or not models_unchanged:
        raise SystemExit("comparison_invalid_sources_changed")
    # Failure evidence is an evaluation result; it is never converted to a successful SRS.
    print(
        json.dumps({"results": results, "source_unchanged": stable, "dataset_unchanged": unchanged})
    )


if __name__ == "__main__":
    main()

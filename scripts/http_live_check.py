"""Observe a UI-started campus run, then exercise the VPN case through the real local API."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pymupdf

from cybersrs import prompts
from cybersrs.config import Settings
from cybersrs.repository import canonical_hash

from .live_check import CASES


def _request(client: httpx.Client, method: str, path: str, **kwargs) -> dict | list:
    response = client.request(method, path, **kwargs)
    response.raise_for_status()
    return response.json()


def _watch(client: httpx.Client, run_id: str, label: str, output: Path, budget: float) -> dict:
    deadline = time.monotonic() + budget + 120
    previous = None
    while time.monotonic() < deadline:
        try:
            run = _request(client, "GET", f"/runs/{run_id}")
        except httpx.TimeoutException:
            time.sleep(1)
            continue
        event = run["events"][-1] if run["events"] else {}
        state = (run["status"], event.get("agent"), event.get("state"))
        if state != previous:
            print(
                json.dumps(
                    {
                        "case": label,
                        "run": run_id,
                        "status": state[0],
                        "agent": state[1],
                        "state": state[2],
                    }
                ),
                flush=True,
            )
            previous = state
        if run["status"] not in {"queued", "running"}:
            (output / f"{label}-run.json").write_text(json.dumps(run, indent=2), encoding="utf8")
            return run
        time.sleep(1)
    raise RuntimeError("observation_timeout_run_may_still_be_running")


def _save_case(client: httpx.Client, key: str, project_id: str, run: dict, output: Path) -> dict:
    result = {
        "case": key,
        "project_id": project_id,
        "run_id": run["id"],
        "status": run["status"],
        "error": run["error"],
        "manual_semantic_review": "pending",
        "pdf_visual_review": "pending",
        "reviews_recorded_by_driver": 0,
    }
    if run["status"] != "completed":
        return result
    version_id = next(
        event["version_id"]
        for event in reversed(run["events"])
        if event.get("agent") == "document" and event.get("version_id")
    )
    base = f"/projects/{project_id}/versions/{version_id}"
    version = _request(client, "GET", base)
    assert canonical_hash(version["content"]) == version["content_hash"]
    result.update(
        version_id=version_id,
        content_hash=version["content_hash"],
        quality=version["quality"]["status"],
        prompt_version=version["content"]["prompt_version"],
        actual_models=version["content"]["models_used"],
        sdlc=version["content"]["sdlc"]["selected_model"],
        expected_sdlc=CASES[key]["expected_sdlc"],
    )
    for format_name, extension in (("json", "json"), ("markdown", "md"), ("pdf", "pdf")):
        response = client.get(base + f"/export/{format_name}")
        response.raise_for_status()
        (output / f"{key}.{extension}").write_bytes(response.content)
    exported = json.loads((output / f"{key}.json").read_text(encoding="utf8"))
    assert exported["content_hash"] == version["content_hash"]
    ids = [row["requirement_id"] for row in version["quality"]["traceability"]]
    with pymupdf.open(output / f"{key}.pdf") as document:
        text = "\n".join(page.get_text() for page in document)
        result["pdf_pages"] = len(document)
        result["requirement_ids_missing_from_pdf"] = [rid for rid in ids if rid not in text]
    reviews = _request(client, "GET", base + "/reviews")
    result["observed_review_count"] = len(reviews)
    result["requirements"] = len(ids)
    result["sdlc_matches"] = result["sdlc"] == result["expected_sdlc"]
    result["profile_matches"] = result["prompt_version"] == prompts.PROMPT_VERSION
    return result


def _source_snapshot(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((root / "src/cybersrs").glob("*.py"))
    }


def main() -> None:
    """Run sequential real HTTP checks without fabricated answers, approvals or model output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campus-project", required=True)
    parser.add_argument("--campus-run", required=True)
    args = parser.parse_args()
    settings = Settings()
    root = Path(__file__).resolve().parents[1]
    output = settings.data_dir / "http-evaluations" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    output.mkdir(parents=True, exist_ok=False)
    snapshot = _source_snapshot(root)
    (output / "source-profile.json").write_text(
        json.dumps(
            {
                "prompt_version": prompts.PROMPT_VERSION,
                "source_sha256": snapshot,
                "context_length": settings.ollama_num_ctx,
                "output_budget": settings.ollama_num_predict,
                "requested_model": settings.model_name,
                "base_correction_model": settings.base_model_name,
            },
            indent=2,
        ),
        encoding="utf8",
    )
    results = []
    print(json.dumps({"http_evaluation_output": str(output.resolve())}), flush=True)
    try:
        with httpx.Client(
            base_url=f"http://127.0.0.1:{settings.backend_port}/api/v1", timeout=30
        ) as client:
            project = _request(client, "GET", f"/projects/{args.campus_project}")
            if project["description"] != CASES["campus"]["description"]:
                raise RuntimeError("campus_source_differs_from_authored_reference_case")
            campus = _watch(
                client,
                args.campus_run,
                "campus-generate",
                output,
                settings.generation_timeout_seconds,
            )
            results.append(_save_case(client, "campus", args.campus_project, campus, output))
            (output / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf8")
            vpn = _request(
                client,
                "POST",
                "/projects",
                json={
                    "name": "VPN - live review",
                    "description": CASES["vpn"]["description"],
                },
            )
            (output / "vpn-project.json").write_text(json.dumps(vpn, indent=2), encoding="utf8")
            base = f"/projects/{vpn['id']}"
            analyse = _request(client, "POST", base + "/analyse")
            analysed = _watch(
                client, analyse["id"], "vpn-analyse", output, settings.generation_timeout_seconds
            )
            if analysed["status"] == "completed":
                started = _request(client, "POST", base + "/generate")
                generated = _watch(
                    client,
                    started["id"],
                    "vpn-generate",
                    output,
                    settings.generation_timeout_seconds,
                )
                results.append(_save_case(client, "vpn", vpn["id"], generated, output))
            else:
                results.append(
                    {"case": "vpn", "status": analysed["status"], "error": analysed["error"]}
                )
    finally:
        stable = _source_snapshot(root) == snapshot
        (output / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf8")
        (output / "profile-stability.json").write_text(
            json.dumps({"source_unchanged": stable}), encoding="utf8"
        )
    print(json.dumps({"cases": results, "source_unchanged": stable}), flush=True)
    if not stable or any(
        row["status"] != "completed"
        or row.get("quality") == "invalid"
        or not row.get("sdlc_matches")
        or not row.get("profile_matches")
        or row.get("requirement_ids_missing_from_pdf")
        for row in results
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

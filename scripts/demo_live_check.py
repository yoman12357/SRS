"""Run real teacher-demo cases through the app without fabricated answers or approvals."""

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

from cybersrs.config import Settings

from .http_live_check import _request, _save_case, _source_snapshot, _watch
from .live_check import CASES


def main() -> None:
    """Create actual UI-visible projects, retain all terminal results and export stored content."""
    settings = Settings()
    root = Path(__file__).resolve().parents[1]
    output = settings.data_dir / "demo-evaluations" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    output.mkdir(parents=True, exist_ok=False)
    snapshot = _source_snapshot(root)
    manifest = {
        "source_sha256": snapshot,
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cases": CASES,
        "requested_model": settings.model_name,
        "base_correction_model": settings.base_model_name,
        "assistant_section_edits": False,
        "fabricated_answers": False,
        "human_approval": False,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
    (settings.data_dir / "current-demo-evaluation.txt").write_text(str(output), encoding="utf8")
    print(json.dumps({"demo_evaluation_output": str(output.resolve())}), flush=True)
    results = []
    try:
        with httpx.Client(
            base_url=f"http://127.0.0.1:{settings.backend_port}/api/v1", timeout=30
        ) as client:
            for project in _request(client, "GET", "/projects"):
                runs = _request(client, "GET", f"/projects/{project['id']}/runs")
                if any(run["status"] in {"queued", "running"} for run in runs):
                    raise RuntimeError("existing_interactive_inference_active")
            for key, case in CASES.items():
                started = time.monotonic()
                project = _request(
                    client,
                    "POST",
                    "/projects",
                    json={
                        "name": "Teacher demo - "
                        + ("Campus access control" if key == "campus" else "Research VPN"),
                        "description": case["description"],
                    },
                )
                (output / f"{key}-project.json").write_text(
                    json.dumps(project, indent=2), encoding="utf8"
                )
                for kind, endpoint in (("analyse", "/analyse"), ("generate", "/generate")):
                    run = _request(client, "POST", f"/projects/{project['id']}" + endpoint)
                    run = _watch(
                        client,
                        run["id"],
                        key + "-" + kind,
                        output,
                        settings.generation_timeout_seconds,
                    )
                    if run["status"] != "completed":
                        break
                row = _save_case(client, key, project["id"], run, output)
                row["seconds"] = round(time.monotonic() - started, 3)
                results.append(row)
                (output / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf8")
    finally:
        stable = snapshot == _source_snapshot(root)
        (output / "profile-stability.json").write_text(
            json.dumps({"source_unchanged": stable}), encoding="utf8"
        )
        (output / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf8")
    print(json.dumps({"cases": results, "source_unchanged": stable}), flush=True)
    if (
        not stable
        or len(results) != len(CASES)
        or any(
            row["status"] != "completed"
            or row.get("quality") == "invalid"
            or not row.get("sdlc_matches")
            for row in results
        )
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""Observe real checkpoint retries; export immutable results without approvals."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx

from cybersrs.config import Settings
from cybersrs.sdlc_agent import SDLC_PROMPT_VERSION

from .http_live_check import _request, _save_case, _source_snapshot, _watch


def main() -> None:
    """Retry named terminated runs sequentially and verify frozen production sources."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campus-run", required=True)
    parser.add_argument("--vpn-run", required=True)
    args = parser.parse_args()
    settings = Settings()
    root = Path(__file__).resolve().parents[1]
    output = settings.data_dir / "http-evaluations" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    output.mkdir(parents=True)
    snapshot = _source_snapshot(root)
    (output / "source-profile.json").write_text(
        json.dumps(
            {
                "source_sha256": snapshot,
                "sdlc_prompt_version": SDLC_PROMPT_VERSION,
            },
            indent=2,
        ),
        encoding="utf8",
    )
    print(json.dumps({"retry_output": str(output.resolve())}), flush=True)
    results = []
    try:
        with httpx.Client(
            base_url=f"http://127.0.0.1:{settings.backend_port}/api/v1", timeout=30
        ) as client:
            for key, prior in (("campus", args.campus_run), ("vpn", args.vpn_run)):
                old = _request(client, "GET", f"/runs/{prior}")
                run = _request(client, "POST", f"/runs/{prior}/retry")
                run = _watch(client, run["id"], key, output, settings.generation_timeout_seconds)
                result = _save_case(client, key, old["project_id"], run, output)
                result["retried_from"] = prior
                result["reused_sections"] = [
                    event["agent"] for event in run["events"] if event.get("reused")
                ]
                results.append(result)
                (output / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf8")
                print(json.dumps(result), flush=True)
    finally:
        stable = snapshot == _source_snapshot(root)
        (output / "profile-stability.json").write_text(
            json.dumps({"source_unchanged": stable}), encoding="utf8"
        )
    if not stable or any(row["status"] != "completed" for row in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

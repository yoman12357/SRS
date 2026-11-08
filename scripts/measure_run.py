"""Observe an existing real local run and save reproducible wall-clock evidence."""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

import httpx


def timing_report(run: dict) -> dict:
    """Measure persisted event intervals, including failed work and explicit checkpoint reuse."""
    parse = datetime.fromisoformat
    durations = {}
    starts = {}
    for event in run["events"]:
        agent = event.get("agent")
        if event.get("state") == "running":
            starts[agent] = event["at"]
        elif event.get("state") == "completed" and agent != "document":
            reused = event.get("reused", False)
            durations[agent] = {
                "status": "reused" if reused else "completed",
                "seconds": 0
                if reused
                else round(
                    (parse(event["at"]) - parse(starts.get(agent, event["at"]))).total_seconds(), 3
                ),
                "models": event.get("output_models", [event.get("model")]),
            }
    if run["status"] not in {"running", "queued", "completed"}:
        for agent, start in starts.items():
            if agent not in durations:
                durations[agent] = {
                    "status": run["status"],
                    "seconds": round((parse(run["updated_at"]) - parse(start)).total_seconds(), 3),
                }
    return {
        "run_id": run["id"],
        "status": run["status"],
        "error": run.get("error"),
        "created_at": run["created_at"],
        "terminal_at": run["updated_at"],
        "total_seconds": round(
            (parse(run["updated_at"]) - parse(run["created_at"])).total_seconds(), 3
        ),
        "sections": durations,
        "maximum_section_seconds": max((row["seconds"] for row in durations.values()), default=0),
        "completed_srs": run["status"] == "completed" and run["kind"] != "analyse",
        "human_approval": False,
    }


def main() -> None:
    """Poll the specified run; an observation timeout never restarts or declares the run stopped."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    parsed = urlsplit(args.base_url)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("loopback_url_required")
    args.output.mkdir(parents=True, exist_ok=True)
    previous = None
    with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=20) as client:
        started = time.monotonic()
        while time.monotonic() - started < 1800:
            response = client.get(f"/api/v1/runs/{args.run_id}")
            response.raise_for_status()
            run = response.json()
            latest = run["events"][-1] if run["events"] else {}
            signature = (run["status"], latest.get("agent"), latest.get("state"))
            if signature != previous:
                print(
                    json.dumps(
                        {"status": signature[0], "section": signature[1], "state": signature[2]}
                    ),
                    flush=True,
                )
                previous = signature
            if run["status"] not in {"queued", "running"}:
                break
            time.sleep(1)
        else:
            raise RuntimeError("observation_timeout_run_may_still_be_running")
        report = timing_report(run)
        (args.output / "run.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
        if report["completed_srs"]:
            version_id = next(
                event["version_id"] for event in reversed(run["events"]) if event.get("version_id")
            )
            prefix = f"/api/v1/projects/{run['project_id']}/versions/{version_id}"
            version = client.get(prefix)
            version.raise_for_status()
            (args.output / "srs.json").write_text(
                json.dumps(version.json(), indent=2), encoding="utf-8"
            )
            report.update(version_id=version_id, quality=version.json()["quality"]["status"])
            exported = time.monotonic()
            pdf = client.get(prefix + "/export/pdf")
            pdf.raise_for_status()
            (args.output / "SRS.pdf").write_bytes(pdf.content)
            report["pdf_export_seconds"] = round(time.monotonic() - exported, 3)
        (args.output / "timing.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()

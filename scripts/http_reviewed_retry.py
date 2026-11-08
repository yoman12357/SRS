"""Exercise reviewed checkpoint corrections against the real local application."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx

from cybersrs.config import Settings

from .http_live_check import _request, _save_case, _source_snapshot, _watch


def main() -> None:
    """Apply explicit assistant edits, rebuild dependencies and retain exact artifacts."""
    settings = Settings()
    root = Path(__file__).resolve().parents[1]
    edits_dir = settings.data_dir / "assistant-corrections/20261028-source-review"
    output = settings.data_dir / "http-evaluations" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    output.mkdir(parents=True)
    snapshot = _source_snapshot(root)
    (output / "source-profile.json").write_text(json.dumps(snapshot, indent=2), encoding="utf8")
    print(json.dumps({"reviewed_retry_output": str(output.resolve())}), flush=True)
    results = []
    try:
        with httpx.Client(
            base_url=f"http://127.0.0.1:{settings.backend_port}/api/v1", timeout=30
        ) as client:
            for case, prior in (
                ("campus", "09953d67-04b7-453d-9b30-b22ba61c87b3"),
                ("vpn", "618e1d3c-3fea-4f3d-a39c-ffabd96dc99e"),
            ):
                raw = (edits_dir / f"{case}-edits.json").read_bytes()
                edits = json.loads(raw)
                old = _request(client, "GET", f"/runs/{prior}")
                started = _request(
                    client,
                    "POST",
                    f"/runs/{prior}/retry",
                    json={
                        "section_edits": edits["sections"],
                        "editor": "assistant",
                        "expected_input_hash": old["input_hash"],
                    },
                )
                run = _watch(
                    client, started["id"], case, output, settings.generation_timeout_seconds
                )
                result = _save_case(client, case, old["project_id"], run, output)
                result.update(
                    editor="assistant",
                    corrections_sha256=hashlib.sha256(raw).hexdigest(),
                    retried_from=prior,
                )
                results.append(result)
                (output / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf8")
                print(json.dumps(result), flush=True)
    finally:
        stable = snapshot == _source_snapshot(root)
        (output / "profile-stability.json").write_text(
            json.dumps({"source_unchanged": stable}), encoding="utf8"
        )
    if not stable or any(item["status"] != "completed" for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

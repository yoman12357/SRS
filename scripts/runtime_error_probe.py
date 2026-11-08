"""Reproduce a terminal run and retain HTTP failure details privately for diagnosis."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import httpx

from cybersrs.config import Settings
from cybersrs.knowledge import KnowledgeBase
from cybersrs.orchestrator import Orchestrator
from cybersrs.provider import RepairingOllamaProvider
from cybersrs.repository import Repository


def main() -> None:
    """Retry unchanged source inputs with real inference, never manufacturing a report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    settings = Settings()
    repository = Repository(settings.data_dir)
    post = httpx.post
    args.output.mkdir(parents=True, exist_ok=False)
    failures = []

    def traced_post(url, **kwargs):
        """Persist raw error envelopes only in private application storage, never stdout."""
        response = post(url, **kwargs)
        if response.is_error:
            failures.append(
                {
                    "model": kwargs.get("json", {}).get("model"),
                    "status": response.status_code,
                    "body": response.text,
                }
            )
            (args.output / "http-failures.json").write_text(
                json.dumps(failures, indent=2), encoding="utf8"
            )
        return response

    httpx.post = traced_post
    coordinator = Orchestrator(
        settings, repository, RepairingOllamaProvider(settings), KnowledgeBase(settings)
    )
    try:
        run = coordinator.retry(args.run)
        print(
            json.dumps({"run_id": run["id"], "diagnostics": str(args.output.resolve())}), flush=True
        )
        while run["status"] in {"queued", "running"}:
            time.sleep(1)
            run = repository.get_run(run["id"])
        (args.output / "run.json").write_text(json.dumps(run, indent=2), encoding="utf8")
        print(
            json.dumps(
                {
                    "status": run["status"],
                    "error": run["error"],
                    "http_failure_count": len(failures),
                }
            ),
            flush=True,
        )
    finally:
        coordinator.shutdown()
        httpx.post = post


if __name__ == "__main__":
    main()

"""Compare two documented local Ollama endpoints after all application inference is idle."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import httpx
from pydantic import ValidationError

from cybersrs import prompts
from cybersrs.config import Settings
from cybersrs.prohibition_verification import prohibition_test_contract, prohibition_test_gaps
from cybersrs.provider import generation_schema
from cybersrs.schemas import AcceptanceTestRepair


def main() -> None:
    """Record protocol diagnostics only, never a completed SRS or an approval."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--after-run", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    settings = Settings()
    args.output.mkdir(parents=True, exist_ok=False)
    with httpx.Client(
        base_url=f"http://127.0.0.1:{settings.backend_port}/api/v1", timeout=15
    ) as app:
        print(
            json.dumps({"state": "waiting_for_application_idle", "after_run": args.after_run}),
            flush=True,
        )
        while True:
            target = app.get(f"/runs/{args.after_run}")
            target.raise_for_status()
            if target.json()["status"] not in {"queued", "running"}:
                projects = app.get("/projects").json()
                active = [
                    run
                    for project in projects
                    for run in app.get(f"/projects/{project['id']}/runs").json()
                    if run["status"] in {"queued", "running"}
                ]
                if not active:
                    break
            time.sleep(3)
    source = "Do not automatically change firewall rules or isolate devices."
    context = {
        "source": source,
        "evidence": [{"id": "E-007", "source": "description", "quote": source}],
        "gap_to_close": "automatic_prohibition_needs_attempt_and_unchanged_state_evidence",
        "permission_boundary": {},
        "existing_requirements": [{"id": "SEC-005"}],
        "existing_tests": [],
    }
    instruction = (
        prompts.COMMON
        + "\nReturn ONE acceptance test for the specified gap, linked to the existing "
        "requirement it verifies. Given states the initial role/state; When performs "
        "the action; Then describes its visible result. Name a captured result/state "
        "as evidence. Invent no product behavior or timing. "
        + prohibition_test_contract(source)["instruction"]
    )
    instruction += "\nTRUSTED_OUTPUT_JSON_SCHEMA:\n" + json.dumps(
        AcceptanceTestRepair.model_json_schema(), ensure_ascii=False, separators=(",", ":")
    )
    schema = generation_schema(AcceptanceTestRepair, context)
    report = []
    for model in (settings.model_name, settings.base_model_name):
        for endpoint in ("generate", "chat"):
            payload = {
                "model": model,
                "format": schema,
                "stream": False,
                "keep_alive": "15m",
                "options": {
                    "temperature": 0,
                    "num_ctx": settings.ollama_num_ctx,
                    "num_predict": settings.ollama_num_predict,
                    "repeat_penalty": 1.1,
                },
            }
            user = json.dumps(context, ensure_ascii=False)
            if endpoint == "generate":
                payload |= {"system": instruction, "prompt": user}
            else:
                payload["messages"] = [
                    {"role": "system", "content": instruction},
                    {"role": "user", "content": user},
                ]
            started = time.monotonic()
            response = httpx.post(
                settings.ollama_base_url + "/api/" + endpoint,
                json=payload,
                timeout=settings.ollama_timeout_seconds,
            )
            entry = {
                "model": model,
                "endpoint": endpoint,
                "status": response.status_code,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "request": payload,
                "response_body": response.text,
                "accepted": False,
            }
            if response.is_success:
                wire = response.json()
                content = (
                    wire.get("response")
                    if endpoint == "generate"
                    else wire.get("message", {}).get("content")
                )
                try:
                    result = AcceptanceTestRepair.model_validate_json(content)
                    gaps = prohibition_test_gaps(source, [result.acceptance_criterion.model_dump()])
                    entry |= {
                        "content": result.model_dump(),
                        "gaps": gaps,
                        "done_reason": wire.get("done_reason"),
                        "accepted": not gaps and wire.get("done_reason") != "length",
                    }
                except (ValidationError, TypeError):
                    entry["schema_error"] = True
            report.append(entry)
            (args.output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf8")
            print(
                json.dumps(
                    {
                        key: entry[key]
                        for key in ("model", "endpoint", "status", "elapsed_seconds", "accepted")
                    }
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()

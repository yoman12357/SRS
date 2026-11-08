"""Exercise real adaptive questions and explicit unknown/skip handling through local HTTP."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import httpx

from cybersrs.config import Settings

from .http_live_check import _request, _watch


def main() -> None:
    """Keep this authored regression case distinct from human answers or document approval."""
    settings = Settings()
    output = (
        settings.data_dir
        / "clarification-evaluations"
        / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    )
    output.mkdir(parents=True, exist_ok=False)
    with httpx.Client(
        base_url=f"http://127.0.0.1:{settings.backend_port}/api/v1", timeout=15
    ) as client:
        project = _request(
            client,
            "POST",
            "/projects",
            json={
                "name": "Synthetic clarification regression",
                "description": "We need a security alert review system for our campus IT team.",
            },
        )
        base = f"/projects/{project['id']}"
        run = _request(client, "POST", base + "/analyse")
        print(
            json.dumps(
                {"project_id": project["id"], "run_id": run["id"], "output": str(output.resolve())}
            ),
            flush=True,
        )
        first = _watch(
            client, run["id"], "initial-analysis", output, settings.generation_timeout_seconds
        )
        if first["status"] != "completed":
            raise RuntimeError(first["error"])
        analysed = _request(client, "GET", base)
        (output / "initial-project.json").write_text(
            json.dumps(analysed, indent=2), encoding="utf8"
        )
        questions = analysed["analysis"]["questions"]
        if not questions:
            raise RuntimeError("sparse_description_produced_no_clarification_questions")
        # Explicitly unknown test answers; never invent decisions or human consent.
        second = _request(
            client,
            "POST",
            base + "/answers",
            json={
                "answers": [
                    {"question_id": q["id"], "text": "", "skipped": True} for q in questions
                ],
            },
        )
        second = _watch(
            client, second["id"], "skipped-analysis", output, settings.generation_timeout_seconds
        )
        if second["status"] != "completed":
            raise RuntimeError(second["error"])
        final = _request(client, "GET", base)
        (output / "final-project.json").write_text(json.dumps(final, indent=2), encoding="utf8")
        expected = {q["question"] for q in questions}
        assert {a["question_text"] for a in final["answers"]} == expected
        assert all(a["skipped"] and a["text"] == "" for a in final["answers"])
        assert expected.isdisjoint({q["question"] for q in final["analysis"]["questions"]})
        assert not _request(client, "GET", base + "/versions")
        summary = {
            "status": "completed",
            "initial_questions": len(questions),
            "skipped_answers": len(final["answers"]),
            "unresolved_decisions": final["analysis"]["unresolved_decisions"],
            "versions_created": 0,
            "human_approvals_recorded": 0,
        }
        (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf8")
        print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()

"""Apply explicitly reviewed development-case sections using public immutable edit APIs."""

import hashlib
import json
import time
from datetime import UTC, datetime

import httpx

from cybersrs.config import Settings
from cybersrs.repository import Repository, canonical_hash


def main() -> None:
    """Preserve original drafts, attribute assistant edits and export exact reviewed versions."""
    settings = Settings()
    output = settings.data_dir / "reviewed-artifacts" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    output.mkdir(parents=True)
    corrections = settings.data_dir / "assistant-corrections/20261028-source-review"
    repository = Repository(settings.data_dir)
    results = []
    print(json.dumps({"reviewed_artifacts": str(output.resolve())}), flush=True)
    with httpx.Client(
        base_url=f"http://127.0.0.1:{settings.backend_port}/api/v1", timeout=60
    ) as client:
        for case, pid in (
            ("campus", "84b840c5-f0bd-4496-8598-f961e15f2807"),
            ("vpn", "4eaadd57-df06-4bc1-b4cc-adf9b5a2a49b"),
        ):
            raw = (corrections / f"{case}-version-edits.json").read_bytes()
            proposed = json.loads(raw)
            current = client.get(f"/projects/{pid}/versions/{proposed['source_version_id']}").json()
            assert current["content_hash"] == proposed["source_content_hash"]
            (output / f"{case}-submitted-edits.json").write_bytes(raw)
            runs = []
            for section in ["sdlc", *[name for name in proposed["sections"] if name != "sdlc"]]:
                response = client.put(
                    f"/projects/{pid}/versions/{current['id']}/sections/{section}",
                    json={
                        "content": proposed["sections"][section],
                        "editor": "assistant",
                        "expected_content_hash": current["content_hash"],
                    },
                )
                response.raise_for_status()
                rid = response.json()["id"]
                while True:
                    response = client.get(f"/runs/{rid}")
                    response.raise_for_status()
                    run = response.json()
                    if run["status"] not in {"queued", "running"}:
                        break
                    time.sleep(0.2)
                (output / f"{case}-{section}-run.json").write_text(
                    json.dumps(run, indent=2), encoding="utf8"
                )
                assert run["status"] == "completed", run["error"]
                vid = next(
                    event["version_id"]
                    for event in run["events"]
                    if event.get("agent") == "document"
                )
                response = client.get(f"/projects/{pid}/versions/{vid}")
                response.raise_for_status()
                current = response.json()
                assert current["quality"]["status"] != "invalid"
                assert canonical_hash(current["content"]) == current["content_hash"]
                assert current["content"]["input_fingerprint"] == run["input_hash"]
                assert not any(
                    event["kind"] == "model_request"
                    for event in repository.list_audit(pid)
                    if event["run_id"] == rid
                )
                runs.append(rid)
                print(
                    json.dumps(
                        {
                            "case": case,
                            "section": section,
                            "version": current["sequence"],
                            "status": run["status"],
                            "new_model_calls": 0,
                        }
                    ),
                    flush=True,
                )
            base = f"/projects/{pid}/versions/{current['id']}"
            for name, suffix in (("json", "json"), ("markdown", "md"), ("pdf", "pdf")):
                response = client.get(base + f"/export/{name}")
                response.raise_for_status()
                (output / f"{case}.{suffix}").write_bytes(response.content)
            assert client.get(base + "/reviews").json() == []
            results.append(
                {
                    "case": case,
                    "project_id": pid,
                    "version_id": current["id"],
                    "sequence": current["sequence"],
                    "content_hash": current["content_hash"],
                    "quality": current["quality"]["status"],
                    "sdlc": current["content"]["sdlc"]["selected_model"],
                    "corrections_sha256": hashlib.sha256(raw).hexdigest(),
                    "edit_runs": runs,
                    "reviewer": "assistant",
                    "human_approval": False,
                    "semantic_review": "pending_final_source_matrix",
                    "pdf_visual_review": "pending",
                }
            )
            (output / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf8")
    print(json.dumps(results), flush=True)


if __name__ == "__main__":
    main()

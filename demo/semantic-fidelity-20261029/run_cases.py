"""Exercise the supplied four briefs through the real local API, recording every attempt."""

import argparse
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path

import httpx
import pymupdf

from cybersrs.config import Settings
from cybersrs.repository import canonical_hash
from cybersrs.schemas import Document
from scripts.measure_run import timing_report


def save(path: Path, payload: object) -> None:
    """Persist private development evidence as JSON."""
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def snapshot(root: Path) -> dict:
    """Record hashes of actual product sources to detect a profile change mid-run."""
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((root / "src/cybersrs").glob("*.py"))
    }


def request(client: httpx.Client, method: str, path: str, **kwargs):
    """Send an explicit application request without automatic mutation retries."""
    response = client.request(method, path, **kwargs)
    response.raise_for_status()
    return response.json()


def watch(client: httpx.Client, run_id: str, output: Path, label: str) -> dict:
    """Poll the same authoritative run; transient observation errors never restart it."""
    previous = None
    while True:
        try:
            run = request(client, "GET", f"/runs/{run_id}")
        except (httpx.TimeoutException, httpx.ConnectError):
            time.sleep(2)
            continue
        save(output / f"{label}-run.json", run)
        latest = run["events"][-1] if run["events"] else {}
        state = (run["status"], latest.get("agent"), latest.get("state"))
        if state != previous:
            print(json.dumps({"case": output.name, "phase": label, "run_id": run_id,
                              "status": state[0], "section": state[1], "state": state[2],
                              "error": run.get("error")}), flush=True)
            previous = state
        if run["status"] not in {"running", "queued"}:
            return run
        time.sleep(2)


def main() -> None:
    """Generate sequential fresh cases and save successful default IEEE PDFs on Desktop."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--label", default="initial")
    args = parser.parse_args()
    evidence = Path(__file__).resolve().parent
    root = evidence.parents[1]
    desktop = root.parent / "CyberSRS - Source Fidelity Checks"
    desktop.mkdir(exist_ok=True)
    settings = Settings()
    cases = json.loads((evidence / "cases.json").read_text(encoding="utf-8"))
    initial_snapshot = snapshot(root)
    save(evidence / f"{args.label}-source-profile.json", initial_snapshot)
    results = []
    with httpx.Client(base_url=f"http://127.0.0.1:{settings.backend_port}/api/v1",
                      timeout=30) as client:
        assert request(client, "GET", "/health")["status"] == "ready"
        for case in cases:
            if args.case and case["key"] not in args.case:
                continue
            output = evidence / f"{case['key']}-{args.label}"
            output.mkdir(exist_ok=False)
            started = time.monotonic()
            project = request(client, "POST", "/projects", json={
                "name": f"Four-case demo - {case['name']}", "description": case["description"]})
            save(output / "project.json", project)
            base = f"/projects/{project['id']}"
            analysis = request(client, "POST", base + "/analyse")
            analysed = watch(client, analysis["id"], output, "analysis")
            result = {"case": case["key"], "project_id": project["id"], "label": args.label,
                      "started_local": datetime.now().astimezone().isoformat(),
                      "analysis": timing_report(analysed), "manual_retries": 0}
            if analysed["status"] != "completed":
                result.update(status=analysed["status"], error=analysed.get("error"))
            else:
                generation = request(client, "POST", base + "/generate")
                generated = watch(client, generation["id"], output, "generation")
                result.update(status=generated["status"], generation=timing_report(generated),
                              error=generated.get("error"))
                if generated["status"] == "completed":
                    vid = next(event["version_id"] for event in reversed(generated["events"])
                               if event.get("version_id"))
                    version_path = base + f"/versions/{vid}"
                    version = request(client, "GET", version_path)
                    doc = Document.model_validate(version["content"])
                    assert doc.original_description == case["description"]
                    assert canonical_hash(version["content"]) == version["content_hash"]
                    save(output / "version.json", version)
                    for fmt, ext in (("pdf", "pdf"), ("markdown", "md")):
                        response = client.get(version_path + "/export/" + fmt)
                        response.raise_for_status()
                        (output / f"SRS.{ext}").write_bytes(response.content)
                        if fmt == "pdf":
                            (desktop / (case["filename"] + ".pdf")).write_bytes(response.content)
                    response = client.get(version_path + "/export/pdf?detail=full")
                    response.raise_for_status()
                    (output / "Supporting report.pdf").write_bytes(response.content)
                    with pymupdf.open(output / "SRS.pdf") as pdf:
                        text = " ".join(" ".join(page.get_text().split()) for page in pdf)
                        for key in ("functional", "nonfunctional", "security", "data", "network"):
                            for row in getattr(doc, key).requirements:
                                assert " ".join(row.statement.split()) in text
                        for index, page in enumerate(pdf, 1):
                            page.get_pixmap().save(output / f"page-{index}.png")
                        result["pdf_pages"] = len(pdf)
                    assert not request(client, "GET", version_path + "/reviews")
                    result.update(version_id=vid, content_hash=version["content_hash"],
                                  quality=version["quality"]["status"],
                                  models_used=doc.models_used,
                                  pdf=str(desktop / (case["filename"] + ".pdf")))
            result.update(total_wall_seconds=round(time.monotonic() - started, 3),
                          source_unchanged=snapshot(root) == initial_snapshot)
            save(output / "result.json", result)
            results.append(result)
            save(evidence / f"{args.label}-results.json", results)
            print(json.dumps({"case_result": result}), flush=True)
    print(json.dumps({"finished": True, "results": str(evidence / f"{args.label}-results.json")}),
          flush=True)


if __name__ == "__main__":
    main()

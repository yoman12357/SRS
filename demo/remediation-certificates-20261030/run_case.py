"""Run one explicit live example; retain failures, analysis, timing and genuine exports."""

import argparse
import hashlib
import json
import time
from pathlib import Path

import httpx
import pymupdf

from cybersrs.config import Settings
from cybersrs.repository import canonical_hash
from cybersrs.schemas import Document
from scripts.measure_run import timing_report

EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE.parents[1]
DESKTOP = ROOT.parent / "CyberSRS - Backup and Configuration - 30 Oct 2026"


def save(path: Path, value: object) -> None:
    """Save local evidence without deleting or overwriting other attempts."""
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def request(client: httpx.Client, method: str, path: str, **kwargs):
    """Send one explicit mutation or observation, with no hidden request retries."""
    response = client.request(method, path, **kwargs)
    response.raise_for_status()
    return response.json()


def watch(client: httpx.Client, rid: str, folder: Path, phase: str) -> dict:
    """Observe a single run and persist all terminal failures honestly."""
    state = None
    while True:
        run = request(client, "GET", f"/runs/{rid}")
        save(folder / f"{phase}-run.json", run)
        event = run["events"][-1] if run["events"] else {}
        latest = (run["status"], event.get("agent"), event.get("state"))
        if latest != state:
            print(
                json.dumps(
                    {"phase": phase, "run": rid, "state": latest, "error": run.get("error")}
                ),
                flush=True,
            )
            state = latest
        if run["status"] not in {"queued", "running"}:
            return run
        time.sleep(2)


def analysis_markdown(project: dict, timing: dict) -> str:
    """Write actual project analysis and unanswered questions, never answer for the user."""
    analysis = project["analysis"]
    lines = [
        f"# {project['name']} - Project analysis",
        "",
        "## Original project brief",
        "",
        project["description"],
        "",
        "## Analysis",
        "",
        f"**Title:** {analysis['title']}",
        f"**Domain:** {analysis['domain']}",
        f"**Supported:** {analysis['supported']}",
        "",
        analysis["summary"],
        "",
        "## Stakeholders",
        "",
    ]
    lines += ["- " + role for role in analysis["stakeholders"]]
    lines += ["", "## Source interpretation", ""]
    for item in analysis["assessments"]:
        lines += [
            f"### {item['evidence_id']} - {item['kind']}",
            "",
            item["explanation"],
            "",
            "Sections: " + ", ".join(item["sections"]),
            "",
        ]
    lines += ["## Questions requiring confirmation", ""]
    for question in analysis["questions"]:
        lines += [
            f"- **{question['question']}** {question['why_needed']} "
            f"(Critical: {question['critical']}; unanswered.)"
        ]
    if not analysis["questions"]:
        lines += ["No questions were returned by this analysis."]
    lines += ["", "## Unresolved decisions", ""]
    lines += ["- " + item for item in analysis["unresolved_decisions"]] or ["None returned."]
    lines += [
        "",
        "## Run record",
        "",
        f"Project ID: {project['id']}",
        f"Analysis run: {timing['run_id']}",
        f"Analysis elapsed: {timing['total_seconds']:.3f} seconds.",
        "",
        "Model analysis is a draft interpretation, not human approval. Original input "
        "is retained above; unanswered decisions have not been filled in.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    """Analyse if needed, generate once, export only validated completed documents."""
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=["remediation", "certificates"])
    parser.add_argument("--label", required=True)
    parser.add_argument("--project")
    args = parser.parse_args()
    case = next(
        c
        for c in json.loads((EVIDENCE / "cases.json").read_text(encoding="utf-8"))
        if c["key"] == args.case
    )
    output = EVIDENCE / f"{args.case}-{args.label}"
    output.mkdir(exist_ok=False)
    user_folder = DESKTOP / case["name"]
    user_folder.mkdir(parents=True, exist_ok=True)
    profile = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (ROOT / "src/cybersrs").glob("*.py")
    }
    save(output / "source-profile.json", profile)
    result = {
        "case": args.case,
        "label": args.label,
        "source_profile": "source-profile.json",
        "user_folder": str(user_folder),
        "human_approval": False,
    }
    started = time.monotonic()
    settings = Settings()
    with httpx.Client(
        base_url=f"http://127.0.0.1:{settings.backend_port}/api/v1", timeout=30
    ) as client:
        project = (
            request(client, "GET", f"/projects/{args.project}")
            if args.project
            else request(
                client,
                "POST",
                "/projects",
                json={"name": case["name"], "description": case["description"]},
            )
        )
        assert project["description"] == case["description"]
        result["project_id"] = project["id"]
        save(output / "project.json", project)
        base = f"/projects/{project['id']}"
        if not project["analysis"]:
            run = request(client, "POST", base + "/analyse")
            finished = watch(client, run["id"], output, "analysis")
            result["analysis"] = timing_report(finished)
            if finished["status"] != "completed":
                result.update(status=finished["status"], error=finished.get("error"))
                save(output / "result.json", result)
                return
            project = request(client, "GET", base)
            save(output / "analysed-project.json", project)
            (user_folder / "Project analysis.md").write_text(
                analysis_markdown(project, result["analysis"]), encoding="utf-8"
            )
        run = request(client, "POST", base + "/generate")
        finished = watch(client, run["id"], output, "generation")
        result.update(
            status=finished["status"],
            error=finished.get("error"),
            generation=timing_report(finished),
        )
        if finished["status"] == "completed":
            vid = next(e["version_id"] for e in reversed(finished["events"]) if e.get("version_id"))
            endpoint = base + f"/versions/{vid}"
            version = request(client, "GET", endpoint)
            save(output / "version.json", version)
            doc = Document.model_validate(version["content"])
            assert version["quality"]["status"] != "invalid"
            assert canonical_hash(version["content"]) == version["content_hash"]
            assert doc.original_description == case["description"]
            assert doc.threats.threats and doc.risks.risks and len(doc.sdlc.phases) >= 3
            assert not request(client, "GET", endpoint + "/reviews")
            for detail, filename in [("standard", "SRS.pdf"), ("full", "SRS - Full report.pdf")]:
                response = client.get(endpoint + "/export/pdf", params={"detail": detail})
                response.raise_for_status()
                (output / filename).write_bytes(response.content)
                (user_folder / filename).write_bytes(response.content)
                with pymupdf.open(stream=response.content, filetype="pdf") as pdf:
                    text = " ".join(" ".join(p.get_text().split()) for p in pdf)
                    for section in (
                        doc.functional,
                        doc.nonfunctional,
                        doc.security,
                        doc.data,
                        doc.network,
                    ):
                        for row in section.requirements:
                            assert " ".join(row.statement.split()) in text
                    if detail == "standard":
                        result["pdf_pages"] = len(pdf)
                        for index, page in enumerate(pdf, 1):
                            page.get_pixmap().save(output / f"page-{index}.png")
            result.update(
                version_id=vid,
                content_hash=version["content_hash"],
                quality=version["quality"]["status"],
                threats=len(doc.threats.threats),
                risks=len(doc.risks.risks),
                sdlc=doc.sdlc.selected_model,
                models=doc.models_used,
            )
        result["wall_seconds"] = round(time.monotonic() - started, 3)
        end_profile = {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / "src/cybersrs").glob("*.py")
        }
        save(output / "source-profile-end.json", end_profile)
        result["source_unchanged"] = profile == end_profile
        save(output / "result.json", result)
        print(json.dumps({"result": result}), flush=True)


if __name__ == "__main__":
    main()

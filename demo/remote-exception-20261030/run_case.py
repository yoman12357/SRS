"""Run one supplied live example once and save genuine IEEE/analysis artifacts."""

import argparse
import hashlib
import importlib
import json
from pathlib import Path

import httpx
import pymupdf

from cybersrs.config import Settings
from cybersrs.repository import canonical_hash
from cybersrs.schemas import Document
from scripts.measure_run import timing_report

shared = importlib.import_module("demo.api-readiness-20261030.run_case")
EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE.parents[1]
DESKTOP = ROOT.parent / "CyberSRS Remote Access and Security Exceptions - 30 Oct 2026"


def source_profile() -> dict[str, str]:
    """Hash generation source so a run cannot hide a code change made during inference."""
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (ROOT / "src/cybersrs").glob("*.py")
    }


def save_json(path: Path, value: object) -> None:
    """Persist local run evidence without changing earlier attempts."""
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    """Analyse and generate exactly once, then export only a validated IEEE report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=["remote", "exceptions"])
    parser.add_argument("--label", default="initial")
    args = parser.parse_args()
    case = next(
        row
        for row in json.loads((EVIDENCE / "cases.json").read_text(encoding="utf-8"))
        if row["key"] == args.case
    )
    run_folder = EVIDENCE / f"{args.case}-{args.label}"
    run_folder.mkdir(parents=True, exist_ok=False)
    user_folder = DESKTOP / case["name"]
    user_folder.mkdir(parents=True, exist_ok=True)
    start_profile = source_profile()
    save_json(run_folder / "source-profile.json", start_profile)
    result = {
        "case": args.case,
        "human_approval": False,
        "user_retry_used": False,
        "user_folder": str(user_folder),
    }
    settings = Settings()
    with httpx.Client(
        base_url=f"http://127.0.0.1:{settings.backend_port}/api/v1", timeout=30
    ) as client:
        project = shared.request(
            client,
            "POST",
            "/projects",
            json={"name": case["name"], "description": case["description"]},
        )
        result["project_id"] = project["id"]
        save_json(run_folder / "project.json", project)
        base = f"/projects/{project['id']}"
        analysis_run = shared.request(client, "POST", base + "/analyse")
        analysed = shared.watch(client, analysis_run["id"], run_folder, "analysis")
        result["analysis"] = timing_report(analysed)
        result["analysis_status"] = analysed["status"]
        if analysed["status"] != "completed":
            result.update(status=analysed["status"], error=analysed.get("error"))
            save_json(run_folder / "result.json", result)
            print(json.dumps({"result": result}), flush=True)
            return
        project = shared.request(client, "GET", base)
        save_json(run_folder / "analysed-project.json", project)
        analysis_text = shared.analysis_markdown(project, result["analysis"])
        generation_run = shared.request(client, "POST", base + "/generate")
        generated = shared.watch(client, generation_run["id"], run_folder, "generation")
        result.update(
            status=generated["status"],
            error=generated.get("error"),
            generation=timing_report(generated),
        )
        if generated["status"] == "completed":
            version_id = next(
                event["version_id"]
                for event in reversed(generated["events"])
                if event.get("version_id")
            )
            endpoint = base + f"/versions/{version_id}"
            version = shared.request(client, "GET", endpoint)
            save_json(run_folder / "version.json", version)
            document = Document.model_validate(version["content"])
            assert version["quality"]["status"] != "invalid"
            assert canonical_hash(version["content"]) == version["content_hash"]
            assert document.original_description == case["description"]
            assert document.threats.threats and document.risks.risks
            assert len(document.sdlc.phases) >= 3
            assert shared.request(client, "GET", endpoint + "/reviews") == []
            response = client.get(endpoint + "/export/pdf", params={"detail": "standard"})
            response.raise_for_status()
            ieee_name = "SRS - IEEE.pdf"
            (run_folder / ieee_name).write_bytes(response.content)
            (user_folder / ieee_name).write_bytes(response.content)
            with pymupdf.open(stream=response.content, filetype="pdf") as pdf:
                pdf_text = " ".join(" ".join(page.get_text().split()) for page in pdf)
                for section in (
                    document.functional,
                    document.nonfunctional,
                    document.security,
                    document.data,
                    document.network,
                ):
                    for requirement in section.requirements:
                        assert " ".join(requirement.statement.split()) in pdf_text
                result["pdf_pages"] = len(pdf)
            decisions = list(
                dict.fromkeys(
                    decision
                    for section in (
                        document.functional,
                        document.nonfunctional,
                        document.security,
                        document.data,
                        document.network,
                    )
                    for requirement in section.requirements
                    for decision in requirement.unresolved_decisions
                )
            )
            analysis_text += "\n## Additional decisions surfaced in the SRS\n\n"
            analysis_text += "\n".join("- " + item for item in decisions) or "None returned."
            analysis_text += (
                "\n\n## Generation result\n\n"
                f"Generation run: {generated['id']}\n\n"
                f"Generation elapsed: {result['generation']['total_seconds']:.3f} seconds.\n\n"
                "User Retry stop: No. Internal model correction calls, if any, are included "
                "in the elapsed time.\n\n"
                f"Quality status: {version['quality']['status']}.\n\n"
                f"Threat hypotheses: {len(document.threats.threats)}; linked risks: "
                f"{len(document.risks.risks)}.\n\n"
                f"SDLC recommendation: {document.sdlc.selected_model} (provisional).\n\n"
                f"Version: {version_id}\n\nSHA-256: {version['content_hash']}\n\n"
                "This is a validated model-generated draft, not human approval.\n"
            )
            result.update(
                version_id=version_id,
                content_hash=version["content_hash"],
                quality=version["quality"]["status"],
                threats=len(document.threats.threats),
                risks=len(document.risks.risks),
                sdlc=document.sdlc.selected_model,
                models=document.models_used,
            )
        (run_folder / "Project analysis.md").write_text(analysis_text, encoding="utf-8")
        (user_folder / "Project analysis.md").write_text(analysis_text, encoding="utf-8")
    end_profile = source_profile()
    save_json(run_folder / "source-profile-end.json", end_profile)
    result["source_unchanged"] = start_profile == end_profile
    save_json(run_folder / "result.json", result)
    print(json.dumps({"result": result}), flush=True)


if __name__ == "__main__":
    main()

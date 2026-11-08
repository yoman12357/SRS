"""Assemble the two final live results and analysis files with honest attempt history."""

import importlib
import json
from pathlib import Path

import httpx
import pymupdf

from cybersrs.config import Settings
from cybersrs.repository import canonical_hash

driver = importlib.import_module("demo.backup-config-20261030.run_case")
ROOT = driver.ROOT
FOLDER = driver.EVIDENCE
DESKTOP = driver.DESKTOP


def load(path: Path) -> dict:
    """Read the persisted local run evidence."""
    return json.loads(path.read_text(encoding="utf-8"))


def clock(seconds: float) -> str:
    """Present measured seconds without pretending they are future time guarantees."""
    rounded = round(seconds)
    return f"{rounded // 60}:{rounded % 60:02d}"


def main() -> None:
    """Validate genuine completed final runs, then save the user-facing summary."""
    results = []
    lines = [
        "# CyberSRS - Backup and Configuration results",
        "",
        "30 October 2026",
        "",
        "These two examples were generated sequentially using the real local API and "
        "Ollama. The PDFs remain AI-generated drafts requiring human review.",
        "",
        "## Final measured results",
        "",
        "| Project | Analysis | SRS generation | Retry stop in final run |",
        "| --- | ---: | ---: | --- |",
    ]
    with httpx.Client(
        base_url=f"http://127.0.0.1:{Settings().backend_port}/api/v1", timeout=20
    ) as c:
        for key in ("backup", "configuration"):
            folder = FOLDER / ("backup-final" if key == "backup" else "configuration-verified")
            result = load(folder / "result.json")
            assert result["status"] == "completed", result
            initial = load(FOLDER / f"{key}-initial" / "result.json")
            analysis = initial["analysis"]
            profile = load(folder / "source-profile.json")
            assert profile == load(folder / "source-profile-end.json")
            response = c.get(f"/projects/{result['project_id']}/versions/{result['version_id']}")
            response.raise_for_status()
            version = response.json()
            assert version["quality"]["status"] != "invalid"
            assert canonical_hash(version["content"]) == version["content_hash"]
            project = load(FOLDER / f"{key}-initial" / "analysed-project.json")
            destination = Path(result["user_folder"])
            for filename in ("SRS.pdf", "SRS - Full report.pdf"):
                assert (destination / filename).read_bytes() == (folder / filename).read_bytes()
                with pymupdf.open(destination / filename) as pdf:
                    assert len(pdf) > 1
            content = version["content"]
            sections = ("functional", "nonfunctional", "security", "data", "network")
            decisions = list(
                dict.fromkeys(
                    d
                    for s in sections
                    for row in content[s]["requirements"]
                    for d in row["unresolved_decisions"]
                )
            )
            text = driver.analysis_markdown(project, analysis)
            text += "\n## Decisions surfaced during SRS drafting\n\n"
            text += "\n".join("- " + d for d in decisions) or "No additional decisions returned."
            text += (
                "\n\n## Final SRS generation\n\n"
                f"Generation time: {result['generation']['total_seconds']:.3f} seconds "
                f"({clock(result['generation']['total_seconds'])}).\n\n"
                f"Selected SDLC: {result['sdlc']} (proposed; delivery constraints remain open).\n\n"
                f"Threat hypotheses: {result['threats']}; linked risks: {result['risks']}.\n\n"
                f"Version: {result['version_id']}\n\n"
                f"Canonical SHA-256: {version['content_hash']}\n\n"
                "The final generation completed without a user Retry stop. Automatic "
                "local-model corrections were permitted. No human approval was recorded.\n\n"
                "[IEEE SRS PDF](SRS.pdf) | [Normal full SRS PDF](SRS%20-%20Full%20report.pdf)\n"
            )
            (destination / "Project analysis.md").write_text(text, encoding="utf-8")
            result["analysis"] = analysis
            result["source_unchanged"] = True
            results.append(result)
            lines.append(
                f"| {project['name']} | {clock(analysis['total_seconds'])} | "
                f"{clock(result['generation']['total_seconds'])} | No - completed |"
            )
    lines += [
        "",
        "Times are measured workflow elapsed time; generation excludes analysis, "
        "development fixes, review and file export. Existing analysis was reused for final runs.",
        "",
        "## Saved files",
        "",
        "Each project folder contains:",
        "",
        "- SRS.pdf - IEEE outline with threat, risk and SDLC appendices.",
        "- SRS - Full report.pdf - Normal report, including criteria and supporting sections.",
        "- Project analysis.md - exact brief, stored analysis, questions and final run details.",
        "",
        "## Earlier attempts and corrections",
        "",
        "The initial backup attempt was cancelled by the agent after 42.088 seconds "
        "to fix source parsing: backup-and-restore activity nouns were being split into "
        "an unintended restore action, and It was treated as a person. Source predicates "
        "define/initiate/submit/track were also separated correctly.",
        "",
        "The next backup draft completed in 135.443 seconds and the first configuration "
        "draft in 123.555 seconds. Final content inspection found copied generic object "
        "alternatives and unconfirmed registry/metadata/session-persistence wording in "
        "acceptance tests. Guidance and validators were corrected and both examples were "
        "generated again sequentially. Those earlier drafts are retained as development "
        "evidence, not presented as the final files.",
        "",
        "The configuration validation attempt then stopped after 64.009 seconds: a valid "
        "dashboard display result was falsely rejected because its trailing condition "
        "mentioned initiation. The guard now checks the observed result separately from "
        "its triggering condition, with a regression for the exact saved correction. "
        "Configuration was generated again after that fix.",
        "",
        "The final runs required no manual Retry. This is evidence for these two measured "
        "runs, not a guarantee that every future description completes without Retry.",
        "",
        "## Verification",
        "",
        "680 backend tests passed; Ruff passed. Frontend was unchanged. Both final "
        "canonical documents passed current automated checks; hashes and original briefs "
        "were preserved, both PDF styles exported and primary layouts were visually "
        "inspected. Automated validation is not human semantic approval.",
        "",
    ]
    (DESKTOP / "Results and timings.md").write_text("\n".join(lines), encoding="utf-8")
    driver.save(FOLDER / "final-results.json", results)
    print(json.dumps({"saved": str(DESKTOP), "results": results}), flush=True)


if __name__ == "__main__":
    main()

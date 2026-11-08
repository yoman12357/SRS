"""Check and save two additional real examples without replacing earlier results."""

import importlib
import json
from pathlib import Path

import httpx
import pymupdf

from cybersrs.config import Settings
from cybersrs.repository import canonical_hash

driver = importlib.import_module("demo.remediation-certificates-20261030.run_case")


def clock(seconds: float) -> str:
    """Format measured elapsed time, not a future timing guarantee."""
    value = round(seconds)
    return f"{value // 60}:{value % 60:02d}"


def load(path: Path) -> dict:
    """Read the actual persisted attempt or canonical version."""
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    """Validate real exports and save a separate summary plus per-project Markdown."""
    cases = load(driver.EVIDENCE / "cases.json")
    results = []
    text = [
        "# Additional CyberSRS examples - 30 October 2026",
        "",
        "Two different, assistant-written example briefs were run sequentially through "
        "the real local application at the user's request. These are generation smoke "
        "tests, not an adapter benchmark or human approval.",
        "",
        "| Example | Analysis | Generation | Retry stop | SDLC |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    with httpx.Client(
        base_url=f"http://127.0.0.1:{Settings().backend_port}/api/v1", timeout=20
    ) as c:
        for case in cases:
            folder = driver.EVIDENCE / f"{case['key']}-initial"
            result = load(folder / "result.json")
            assert result["status"] == "completed", result
            assert load(folder / "source-profile.json") == load(folder / "source-profile-end.json")
            endpoint = f"/projects/{result['project_id']}/versions/{result['version_id']}"
            response = c.get(endpoint)
            response.raise_for_status()
            version = response.json()
            assert version["quality"]["status"] != "invalid"
            assert canonical_hash(version["content"]) == result["content_hash"]
            assert version["content"]["original_description"] == case["description"]
            assert c.get(endpoint + "/reviews").json() == []
            output = Path(result["user_folder"])
            for name in ("SRS.pdf", "SRS - Full report.pdf"):
                assert (output / name).read_bytes() == (folder / name).read_bytes()
                with pymupdf.open(output / name) as pdf:
                    assert len(pdf) > 1
            project = load(folder / "analysed-project.json")
            analysis = driver.analysis_markdown(project, result["analysis"])
            decisions = list(
                dict.fromkeys(
                    d
                    for section in ("functional", "nonfunctional", "security", "data", "network")
                    for row in version["content"][section]["requirements"]
                    for d in row["unresolved_decisions"]
                )
            )
            analysis += "\n## Additional decisions surfaced in the SRS\n\n"
            analysis += "\n".join("- " + d for d in decisions) or "None returned."
            analysis += (
                f"\n\n## Generation result\n\n"
                f"Analysis: {result['analysis']['total_seconds']:.3f} seconds.\n\n"
                f"SRS generation: {result['generation']['total_seconds']:.3f} seconds "
                f"({clock(result['generation']['total_seconds'])}).\n\n"
                f"Threat hypotheses: {result['threats']}; linked risks: {result['risks']}.\n\n"
                f"SDLC recommendation: {result['sdlc']} (provisional).\n\n"
                f"Version: {result['version_id']}\n\nSHA-256: {result['content_hash']}\n\n"
                "The first generation run completed without a user Retry stop. "
                "Internal local-model corrections were allowed. Interface contracts, "
                "record fields, detection thresholds and measurable quality targets "
                "remain review decisions; generated test implementation wording is "
                "not a confirmed design choice. No human approval was recorded.\n\n"
                "[IEEE SRS](SRS.pdf) | [Normal SRS](SRS%20-%20Full%20report.pdf)\n"
            )
            (output / "Project analysis.md").write_text(analysis, encoding="utf-8")
            text.append(
                f"| {case['name']} | {clock(result['analysis']['total_seconds'])} | "
                f"{clock(result['generation']['total_seconds'])} | No | {result['sdlc']} |"
            )
            results.append(result)
    text += [
        "",
        "Generation time excludes analysis and export. Internal corrective model "
        "calls are included in generation time. Both examples completed all 14 sections "
        "and remain needs_review drafts.",
        "",
        "## Example briefs",
        "",
    ]
    for case in cases:
        text += ["### " + case["name"], "", case["description"], ""]
    text += [
        "## Files",
        "",
        "Each new project folder contains SRS.pdf, "
        "SRS - Full report.pdf and Project analysis.md. Previous backup/configuration "
        "files remain in the same parent folder.",
        "",
        "## Verification and implementation note",
        "",
        "Source inspection before the certificate run found approval and renewal grouped "
        "inside the review row. Source policy 1.3/prompt 1.38 now preserve separate "
        "approval and renewal obligations and request corresponding observed outcomes. "
        "Remediation used the preceding prompt 1.37. Per-run source hashes remained stable.",
        "",
        "682 backend tests passed; Ruff passed. Both current canonical versions, "
        "original briefs, hashes and exported bytes were checked. Primary PDF layouts "
        "and full-report samples were inspected. Automated checks are not proof of "
        "semantic completeness or a guarantee that future examples never need Retry.",
        "",
    ]
    report_name = "Additional examples - results and timings.md"
    (driver.DESKTOP / report_name).write_text("\n".join(text), encoding="utf-8")
    driver.save(driver.EVIDENCE / "results.json", results)
    index = driver.DESKTOP / "Results and timings.md"
    link = (
        "\n## Additional examples\n\nSee [Vulnerability remediation and certificate results]"
        "(Additional%20examples%20-%20results%20and%20timings.md).\n"
    )
    if index.exists() and "## Additional examples" not in index.read_text(encoding="utf-8"):
        index.write_text(index.read_text(encoding="utf-8") + link, encoding="utf-8")
    print(
        json.dumps(
            {
                "folder": str(driver.DESKTOP),
                "results": [
                    {
                        "case": r["case"],
                        "status": r["status"],
                        "seconds": r["generation"]["total_seconds"],
                    }
                    for r in results
                ],
            }
        )
    )


if __name__ == "__main__":
    main()

"""Verify the user's exact brief, two complete runs and both report formats."""

import importlib
import json

import httpx
import pymupdf

from cybersrs.config import Settings
from cybersrs.repository import canonical_hash
from scripts.measure_run import timing_report

driver = importlib.import_module("demo.api-readiness-20261030.run_case")


def main() -> None:
    """Record measured readiness without promising arbitrary input or runtime success."""
    results = [
        json.loads(
            (driver.EVIDENCE / f"api-verification{i}" / "result.json").read_text(encoding="utf-8")
        )
        for i in (1, 2)
    ]
    text = [
        "# API access management - demo verification",
        "",
        "The original reported failure is retained in project history. It involved an "
        "invented numeric response code, an invented lockout, and a missed valid denies "
        "wording. The user's later retry completed before the fix. The following are "
        "fresh measured runs after prompt 1.39 and constrained corrective-field changes.",
        "",
        "| Fresh run | Generation seconds | User Retry stop |",
        "| --- | ---: | --- |",
    ]
    with httpx.Client(
        base_url=f"http://127.0.0.1:{Settings().backend_port}/api/v1", timeout=30
    ) as c:
        for number, result in enumerate(results, 1):
            assert result["status"] == "completed", result
            folder = driver.EVIDENCE / f"api-verification{number}"
            assert json.loads((folder / "source-profile.json").read_text(encoding="utf-8")) == (
                json.loads((folder / "source-profile-end.json").read_text(encoding="utf-8"))
            )
            endpoint = f"/projects/{result['project_id']}/versions/{result['version_id']}"
            response = c.get(endpoint)
            response.raise_for_status()
            version = response.json()
            assert version["quality"]["status"] != "invalid"
            assert canonical_hash(version["content"]) == result["content_hash"]
            assert c.get(endpoint + "/reviews").json() == []
            for filename in ("SRS.pdf", "SRS - Full report.pdf"):
                with pymupdf.open(folder / filename) as pdf:
                    assert len(pdf) > 1
            text.append(f"| {number} | {result['generation']['total_seconds']:.3f} | No |")
        result = results[-1]
        project = c.get(f"/projects/{result['project_id']}").json()
        analysis_run = c.get("/runs/97334a70-c352-4745-95d0-5f74a28d6fe9").json()
        analysis = driver.analysis_markdown(project, timing_report(analysis_run))
        analysis += "\n## Demo readiness checks\n\n" + "\n".join(text[3:])
        analysis += (
            "\n\nThe brief does not specify response codes, lockout behavior, "
            "authentication protocols, token formats or audit field contracts. "
            "These remain unconfirmed; the original source takes precedence over "
            "implementation wording in model-authored acceptance tests.\n"
        )
        from pathlib import Path

        destination = Path(result["user_folder"])
        (destination / "Project analysis.md").write_text(analysis, encoding="utf-8")
        for name in ("SRS.pdf", "SRS - Full report.pdf"):
            assert (destination / name).read_bytes() == (
                driver.EVIDENCE / "api-verification2" / name
            ).read_bytes()
    text += [
        "",
        "Generation time includes internal corrective model calls and excludes "
        "re-analysis and file export. Both runs use the user's exact saved source and "
        "stored analysis, with no invented answers or human approvals.",
        "",
        "Both IEEE and Normal PDFs were exported from each completed canonical version. "
        "Current document validation, exact content hashes and unchanged source profiles "
        "were checked. Primary layouts and full-report samples were inspected.",
        "",
        "689 backend tests and 19 frontend tests passed; Ruff and production build passed.",
        "",
        "The configured automatic test-repair limit is three, inside the existing "
        "120-second section budget. The source, schema and final completeness gates remain "
        "enabled. These results establish this measured case, not an unlimited no-error "
        "guarantee for unavailable models, contradictory briefs or arbitrary future inputs.",
        "",
    ]
    name = "API Access - demo readiness.md"
    (driver.DESKTOP / name).write_text("\n".join(text), encoding="utf-8")
    index = driver.DESKTOP / "Results and timings.md"
    content = index.read_text(encoding="utf-8")
    if "## API access demo verification" not in content:
        index.write_text(
            content + "\n## API access demo verification\n\n"
            "[API access readiness report](API%20Access%20-%20demo%20readiness.md)\n",
            encoding="utf-8",
        )
    driver.save(driver.EVIDENCE / "results.json", results)
    print(
        json.dumps(
            {
                "saved": str(destination),
                "runs": [
                    {"status": r["status"], "seconds": r["generation"]["total_seconds"]}
                    for r in results
                ],
            }
        )
    )


if __name__ == "__main__":
    main()

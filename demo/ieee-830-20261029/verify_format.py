"""Recheck live IEEE exports against unchanged saved canonical versions."""

import json
from pathlib import Path
from urllib.request import urlopen

import pymupdf

from cybersrs.repository import canonical_hash
from cybersrs.schemas import Document


def verify() -> None:
    """Export existing versions only; never start generation or record approval."""
    root = Path(__file__).resolve().parent
    cases = json.loads((root / "verification.json").read_text(encoding="utf-8"))
    originals = {
        "dns": ("dns-filtering-20261029", "DNS and web filtering SRS"),
        "laboratory": ("research-labs-20261029", "Research laboratory SRS"),
    }
    with urlopen("http://127.0.0.1:8011/api/v1/health", timeout=30) as response:
        assert json.load(response)["status"] == "ready"
    for case in cases:
        name = case["case"]
        folder, stem = originals[name]
        old = json.loads((root.parent / folder / (stem + ".json")).read_text(encoding="utf-8"))
        endpoint = (
            "http://127.0.0.1:8011/api/v1/projects/"
            + case["project_id"] + "/versions/" + case["version_id"]
        )
        with urlopen(endpoint, timeout=30) as response:
            current = json.load(response)
        assert current["content"] == old["content"]
        assert current["content_hash"] == old["content_hash"] == canonical_hash(current["content"])
        document = Document.model_validate(current["content"])
        report = current["presentation"]
        assert report["profile"] == "ieee-830-1998-1.0"
        sections = {section["number"]: section for section in report["sections"]}
        assert sections["1.1"]["paragraphs"][0] == document.introduction.summary
        assert sections["1.2"]["paragraphs"] == [document.original_description]
        expected = sorted(
            (row.id, row.statement)
            for category in ("functional", "nonfunctional", "security", "data", "network")
            for row in getattr(document, category).requirements
        )
        actual = sorted(
            (row["id"], row["statement"])
            for section in report["sections"] for row in section["requirements"]
        )
        assert actual == expected
        roles = {row[0] for table in sections["2.3"]["tables"] for row in table["rows"]}
        assert {"User", "Admin", "Project Analyst"} <= roles
        with urlopen(endpoint + "/reviews", timeout=30) as response:
            reviews = json.load(response)
        assert not reviews
        for fmt, extension in (("pdf", "pdf"), ("markdown", "md"), ("json", "json")):
            with urlopen(endpoint + "/export/" + fmt, timeout=30) as response:
                (root / f"{name}-IEEE-SRS.{extension}").write_bytes(response.read())
        with urlopen(endpoint + "/export/pdf?detail=full", timeout=30) as response:
            (root / f"{name}-supporting-report.pdf").write_bytes(response.read())
        with pymupdf.open(root / f"{name}-IEEE-SRS.pdf") as pdf:
            text = " ".join(" ".join(page.get_text().split()) for page in pdf)
            assert len(pdf) == 5
            assert all(" ".join(statement.split()) in text for _, statement in expected)
            assert current["content_hash"] in text
            assert "DRAFT" in text and "human review required" in text
            for index, page in enumerate(pdf, 1):
                page.get_pixmap().save(root / f"{name}-page-{index}.png")
            case["ieee_pages"] = len(pdf)
        with pymupdf.open(root.parent / folder / (stem + ".pdf")) as pdf:
            case["old_pages"] = len(pdf)
        with pymupdf.open(root / f"{name}-supporting-report.pdf") as pdf:
            text = " ".join(page.get_text() for page in pdf)
            assert "SDLC recommendation and workflow" in text
        (root / f"{name}-presentation.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        case.update(
            canonical_unchanged=True, requirements_preserved=len(expected),
            human_reviews=len(reviews), quality=current["quality"]["status"],
            introduction_preserved=True, stakeholder_labels=sorted(roles),
            live_api_verified=True,
        )
    (root / "verification.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")
    # Remove only the obsolete pages created by earlier iterations of this export.
    for name in ("dns", "laboratory"):
        for page in (6, 7):
            obsolete = root / f"{name}-page-{page}.png"
            if obsolete.exists():
                obsolete.unlink()
    print(json.dumps(cases, indent=2))


if __name__ == "__main__":
    verify()

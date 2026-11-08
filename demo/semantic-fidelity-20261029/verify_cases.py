"""Audit selected real versions against an independent source-obligation matrix and current API."""

import argparse
import hashlib
import json
import re
from pathlib import Path

import httpx
import pymupdf

from cybersrs.clarification_policy import decision_topics
from cybersrs.config import Settings
from cybersrs.repository import canonical_hash
from cybersrs.schemas import Document
from cybersrs.source_detail_policy import unsupported_observed_fields, unsupported_source_details
from cybersrs.source_obligations import criterion_target_issues, source_obligations
from cybersrs.srs_presentation import stakeholder_table


def main() -> None:
    """Verify canonical data, exports and traceability without generating or approving."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="append", required=True, help="case=attempt-label")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    cases = json.loads((root / "cases.json").read_text(encoding="utf-8"))
    matrix = json.loads((root / "obligation-matrix.json").read_text(encoding="utf-8"))
    selected = dict(value.split("=", 1) for value in args.run)
    desktop = root.parents[1].parent / "CyberSRS - Source Fidelity Checks"
    settings = Settings()
    reports = []
    with httpx.Client(
        base_url=f"http://127.0.0.1:{settings.backend_port}/api/v1", timeout=30
    ) as client:
        assert client.get("/health").json()["status"] == "ready"
        for case in cases:
            if case["key"] not in selected:
                continue
            folder = root / (case["key"] + "-" + selected[case["key"]])
            result = json.loads((folder / "result.json").read_text(encoding="utf-8"))
            assert result["status"] == "completed", result
            path = f"/projects/{result['project_id']}/versions/{result['version_id']}"
            response = client.get(path)
            response.raise_for_status()
            version = response.json()
            doc = Document.model_validate(version["content"])
            assert doc.original_description == case["description"]
            assert not unsupported_source_details(doc.analysis.summary, doc.evidence)
            assert (
                canonical_hash(version["content"])
                == version["content_hash"]
                == result["content_hash"]
            )
            assert version["quality"]["status"] != "invalid", version["quality"]
            assert not client.get(path + "/reviews").json()
            rows = [
                row.model_dump()
                for category in ("functional", "nonfunctional", "security", "data", "network")
                for row in getattr(doc, category).requirements
            ]
            row_ids = {row["id"] for row in rows}
            assert len(row_ids) == len(rows)
            normative = " ".join(row["statement"].casefold() for row in rows)
            obligations = {}
            for operation in matrix[case["key"]]["operations"]:
                matches = [
                    row for row in rows if operation.casefold() in row["statement"].casefold()
                ]
                assert matches, (case["key"], "omitted obligation", operation)
                assert all(row["basis"] == "explicit" and row["evidence_ids"] for row in matches)
                assert all(row["id"].startswith("FR-") for row in matches), operation
                obligations[operation] = [
                    {"id": row["id"], "evidence_ids": row["evidence_ids"]} for row in matches
                ]
            for trait in matrix[case["key"]]["scope_traits"]:
                assert trait.casefold() in normative, (case["key"], "lost scope", trait)
            for attribute in matrix[case["key"]]["quality_attributes"]:
                assert any(attribute in row.statement for row in doc.nonfunctional.requirements)
            for row in doc.functional.requirements:
                combined = [
                    operation
                    for operation in matrix[case["key"]]["operations"]
                    if operation.casefold() in row.statement.casefold()
                ]
                assert len(combined) <= 1, ("compound runtime requirement", row.id, combined)
            evidence = {fact.id: fact for fact in doc.evidence}
            for row in rows:
                assert row["acceptance_criteria"]
                assert not set(row["evidence_ids"]) - evidence.keys()
                support = [evidence[eid] for eid in row["evidence_ids"]]
                assert not unsupported_source_details(row["statement"], support)
                units = [
                    unit
                    for fact in support
                    for unit in source_obligations(fact)
                    if unit.statement == row["statement"]
                ]
                assert units, ("canonical statement lacks its original source slot", row)
                for criterion in row["acceptance_criteria"]:
                    assert not unsupported_source_details(" ".join(criterion.values()), support), (
                        row,
                        criterion,
                    )
                    assert not unsupported_observed_fields(criterion["then"], support), (
                        row,
                        criterion,
                    )
                    assert not criterion_target_issues(units[0], criterion), (row, criterion)
            topics = set()
            qids = {question.id for question in doc.analysis.questions}
            assert len(qids) == len(doc.analysis.questions)
            for question in doc.analysis.questions:
                keys = {key for key, _ in decision_topics(question.question, doc.evidence)}
                assert keys and not keys & topics, ("duplicate/irrelevant question", question)
                topics |= keys
                assert question.evidence_ids and not set(question.evidence_ids) - evidence.keys()
                assert not unsupported_source_details(question.why_needed, doc.evidence)

            def decision_refs(value, known_qids=qids):
                """Check reusable references without confusing source facts with questions."""
                if isinstance(value, dict):
                    for key, item in value.items():
                        if key in {"open_decisions", "open_issues", "unresolved_decisions"}:
                            for text in item:
                                for qid in re.findall(r"Decision (Q-[a-f0-9]+) is TBD", text):
                                    assert qid in known_qids, ("dangling decision reference", qid)
                        elif isinstance(item, (dict, list)):
                            decision_refs(item)
                elif isinstance(value, list):
                    for item in value:
                        decision_refs(item)

            decision_refs(version["content"])
            roles = [row[0] for row in stakeholder_table(doc).rows]
            if case["key"] == "firewall":
                assert "User" not in roles
                assert not any(
                    re.search(r"\bguest\b", scenario.actor, re.I)
                    for scenario in doc.scenarios.scenarios
                )
            tests = {rid: [] for rid in row_ids}
            for test in doc.verification.tests:
                assert set(test.requirement_ids) <= row_ids
                for rid in test.requirement_ids:
                    tests[rid].append(test.id)
            assert all(tests.values()), tests
            for fmt, suffix in (("pdf", "pdf"), ("markdown", "md")):
                exported = client.get(path + "/export/" + fmt)
                exported.raise_for_status()
                (folder / f"Verified SRS.{suffix}").write_bytes(exported.content)
                if fmt == "pdf":
                    (desktop / (case["filename"] + ".pdf")).write_bytes(exported.content)
            with pymupdf.open(folder / "Verified SRS.pdf") as pdf:
                text = " ".join(" ".join(page.get_text().split()) for page in pdf)
                assert "IEEE 830-1998" in text and "DRAFT" in text
                assert all(" ".join(row["statement"].split()) in text for row in rows)
                for index, page in enumerate(pdf, 1):
                    page.get_pixmap().save(folder / f"verified-page-{index}.png")
                pages = len(pdf)
            presentation = version["presentation"]
            assert presentation["profile"] == "ieee-830-1998-1.0"
            numbered = {section["number"] for section in presentation["sections"]}
            assert {"1", "2", "3", "2.3", "2.5", "3.2", "3.6.3"} <= numbered
            report_rows = [
                row for section in presentation["sections"] for row in section["requirements"]
            ]
            assert sorted(row["id"] for row in report_rows) == sorted(row_ids)
            reports.append(
                {
                    "case": case["key"],
                    "project_id": result["project_id"],
                    "version_id": result["version_id"],
                    "content_hash": version["content_hash"],
                    "status": "verified",
                    "quality": version["quality"]["status"],
                    "functional_requirements": len(doc.functional.requirements),
                    "quality_requirements": len(doc.nonfunctional.requirements),
                    "obligation_matrix": obligations,
                    "questions": [q.model_dump() for q in doc.analysis.questions],
                    "traceability": tests,
                    "pdf_pages": pages,
                    "pdf_sha256": hashlib.sha256(
                        (folder / "Verified SRS.pdf").read_bytes()
                    ).hexdigest(),
                    "generation_seconds": result["generation"]["total_seconds"],
                    "assistant_output_review": "pending",
                    "human_approvals": 0,
                }
            )
            (folder / "verification.json").write_text(
                json.dumps(reports[-1], indent=2), encoding="utf-8"
            )
    (root / "verified-cases.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(
        json.dumps(
            [
                {
                    key: row[key]
                    for key in (
                        "case",
                        "status",
                        "functional_requirements",
                        "quality_requirements",
                        "pdf_pages",
                        "generation_seconds",
                    )
                }
                for row in reports
            ],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

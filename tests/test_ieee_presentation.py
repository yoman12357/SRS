"""IEEE reader reports preserve requirements, role boundaries and review provenance."""

import json
from copy import deepcopy

import pymupdf

from cybersrs.evidence import build_evidence
from cybersrs.exports import render_markdown, render_pdf
from cybersrs.repository import canonical_hash
from cybersrs.schemas import Citation, Document, SourceChunk
from cybersrs.srs_presentation import SRSPresentation, build_srs_presentation, stakeholder_table
from cybersrs.validation import validate_document


def version_for(document: Document) -> dict:
    """Build an inert version fixture with genuine derived quality and canonical hash."""
    content = document.model_dump()
    return {
        "content": content,
        "content_hash": canonical_hash(content),
        "sequence": 1,
        "created_at": "2026-10-29T00:00:00Z",
        "quality": validate_document(document).model_dump(),
    }


def test_ieee_outline_and_every_canonical_requirement_are_preserved(complete_document) -> None:
    """No requirement may disappear behind category routing or a concise overview."""
    document = complete_document
    document.network.requirements.append(
        document.functional.requirements[0].model_copy(
            update={
                "id": "NET-001",
                "statement": "The network shall support approved research devices.",
            }
        )
    )
    before = deepcopy(document.model_dump())
    report = build_srs_presentation(document)
    sections = {section.number: section for section in report.sections}
    assert [sections[key].title for key in ("1", "2", "3")] == [
        "Introduction",
        "Overall description",
        "Specific requirements",
    ]
    assert all(
        key in sections
        for key in (
            "1.1",
            "1.2",
            "1.3",
            "1.4",
            "1.5",
            "2.1",
            "2.2",
            "2.3",
            "2.4",
            "2.5",
            "3.1.1",
            "3.1.2",
            "3.1.3",
            "3.1.4",
            "3.2",
            "3.3",
            "3.4",
            "3.5",
            "3.6.1",
            "3.6.2",
            "3.6.3",
            "3.6.4",
            "3.6.5",
            "3.7",
        )
    )
    expected = [
        (row.id, row.statement)
        for name in ("functional", "nonfunctional", "security", "data", "network")
        for row in getattr(document, name).requirements
    ]
    actual = [
        (row.id, row.statement) for section in report.sections for row in section.requirements
    ]
    assert sorted(actual) == sorted(expected)
    assert document.model_dump() == before
    assert sections["1.1"].paragraphs[0] == document.introduction.summary
    assert sections["1.2"].paragraphs == [document.original_description]
    assert [row.id for row in sections["3.1.4"].requirements] == ["NET-001"]
    assert SRSPresentation.model_validate_json(report.model_dump_json()) == report


def test_compound_quality_routing_does_not_mutate_canonical_sections(complete_document) -> None:
    """A security quality row must not be appended into the source Document's security list."""
    document = complete_document.model_copy(deep=True)
    row = document.functional.requirements[0].model_copy(
        update={"id": "NFR-001", "statement": "The solution shall be secure and maintainable."}
    )
    document.nonfunctional.requirements.append(row)
    before = canonical_hash(document.model_dump())
    report = build_srs_presentation(document)
    assert canonical_hash(document.model_dump()) == before
    assert [r.id for section in report.sections for r in section.requirements].count("NFR-001") == 1
    maintainability = next(section for section in report.sections if section.number == "3.6.4")
    assert "NFR-001" in " ".join(maintainability.paragraphs)


def test_simple_stakeholders_keep_source_classes_and_no_analyst_product_rights(
    complete_document,
) -> None:
    """Display aliases cannot merge lab/network admins or grant a proposed reviewer access."""
    document = complete_document.model_copy(deep=True)
    document.evidence = build_evidence(
        "Students, faculty and staff may use approved services. A student may inspect records. "
        "Network administrators manage policies; lab administrators review active sessions. "
        "Security analysts investigate events. Guest users must not receive privileged access.",
        [],
    )
    document.analysis.stakeholders = ["Unstated Chief Information Officer"]
    rows = {row[0]: row for row in stakeholder_table(document).rows}
    assert {"User", "Admin", "Project Analyst", "Analyst"} <= rows.keys()
    assert "Network administrators" in rows["Admin"][1]
    assert "lab administrators" in rows["Admin"][1]
    assert "student," not in rows["User"][1].lower()
    assert "students" in rows["User"][1].lower() and "Guest" in rows["User"][1]
    assert "no product access" in rows["Project Analyst"][2]
    assert "Chief Information Officer" not in json.dumps(rows)


def test_missing_interfaces_are_unspecified_not_invented(complete_document) -> None:
    """The outline must not fill empty headings with hardware, protocols or obligations."""
    report = build_srs_presentation(complete_document)
    hardware = next(section for section in report.sections if section.number == "3.1.2")
    assert "confirmation is required" in hardware.paragraphs[0]
    assert not hardware.requirements
    assert "TLS" not in report.model_dump_json()


def test_citations_proposals_and_unknowns_survive_reader_presentation(complete_document) -> None:
    """A short report still exposes source basis, literal quotes and unresolved decisions."""
    document = complete_document.model_copy(deep=True)
    document.sources = [
        SourceChunk(
            id="chunk-one",
            source_document_id="policy-one",
            chunk_index=2,
            page_or_section="Section 4",
            relevance_score=0.9,
            text="Literal source guidance for review.",
            title="University source policy",
            sha256="source-hash",
        )
    ]
    row = document.functional.requirements[0]
    row.sources = [Citation(chunk_id="chunk-one", quote="Literal source guidance for review.")]
    row.basis = "proposed"
    row.unresolved_decisions = ["Confirm the permitted review roles."]
    report = build_srs_presentation(document)
    copied = next(r for section in report.sections for r in section.requirements if r.id == row.id)
    assert copied.sources == row.sources and copied.basis == "proposed"
    references = next(section for section in report.sections if section.number == "1.4")
    assert "policy-one" in references.tables[0].rows[1][1]
    assert "chunk 2" in references.tables[0].rows[1][1]
    assert "Section 4" in references.tables[0].rows[1][1]
    assert "0.9" in references.tables[0].rows[1][1]
    assert (
        "Confirm the permitted review roles."
        in next(section for section in report.sections if section.number == "2.5").bullets
    )


def test_primary_pdf_markdown_and_full_report_keep_hash_and_exact_requirements(
    complete_document,
) -> None:
    """Check short/full renderers and unchanged canonical content."""
    version = version_for(complete_document)
    before = deepcopy(version)
    md = render_markdown(version, [])
    full = render_markdown(version, [], detail="full")
    assert "## 2 Overall description" in md
    assert "## 14. SDLC recommendation and workflow" not in md
    assert "## 14. SDLC recommendation and workflow" in full
    criterion = complete_document.functional.requirements[0].acceptance_criteria[0]
    assert criterion.given not in md and criterion.given in full
    raw = render_pdf(version, [])
    with pymupdf.open(stream=raw, filetype="pdf") as pdf:
        text = " ".join(" ".join(page.get_text().split()) for page in pdf)
        for name in ("functional", "nonfunctional", "security", "data", "network"):
            for row in getattr(complete_document, name).requirements:
                assert " ".join(row.statement.split()) in text
        assert "IEEE 830-1998" in text and "human review required" in text
        assert "Traceability:" in text
    assert version == before


def test_ieee_includes_assessments_and_complete_lifecycle_appendices(complete_document):
    """The primary report must expose the same saved cyber assessments as Normal."""
    version = version_for(complete_document)
    md = render_markdown(version, [])
    full = render_markdown(version, [], detail="full")
    assert "## A Derived threat hypotheses" in md
    assert "## B Risk assessment" in md
    assert "## C SDLC recommendation and delivery workflow" in md
    for threat in complete_document.threats.threats:
        assert threat.scenario in md and threat.scenario in full
        assert threat.residual_risk in md
    for risk in complete_document.risks.risks:
        assert risk.description in md and risk.description in full
        assert risk.mitigation in md
    for phase in complete_document.sdlc.phases:
        assert phase.name in md
        for action in phase.activities + phase.security_checks + phase.deliverables:
            assert action in md
    assert "not observed incidents" in md
    assert "not probabilities" in md


def test_reader_outputs_escape_untrusted_model_and_user_text(complete_document) -> None:
    """Rendering is text-only even for hostile HTML-looking titles or source statements."""
    document = complete_document.model_copy(deep=True)
    document.title = '<img src=x onerror="alert(1)">'
    document.functional.requirements[0].statement += " <script>example()</script>"
    version = version_for(document)
    assert "\\<script\\>" in render_markdown(version, [])
    with pymupdf.open(stream=render_pdf(version, []), filetype="pdf") as pdf:
        assert "<script>example()</script>" in "\n".join(page.get_text() for page in pdf)


def test_email_filtering_decision_logs_do_not_become_a_dns_product_function(complete_document):
    """The actual email PDF's function index must not infer DNS from the word filtering."""
    document = complete_document.model_copy(deep=True)
    document.functional.requirements[
        0
    ].statement = (
        "The system shall maintain audit logs of filtering decisions and administrator actions."
    )
    report = build_srs_presentation(document)
    functions = next(section for section in report.sections if section.number == "2.2")
    assert not any("DNS and web filtering" in value for value in functions.bullets)


def test_manageability_uses_its_ieee_attribute_instead_of_default_reliability(complete_document):
    """Keep exact NFR wording and ID while routing manageability to its own attribute."""
    document = complete_document.model_copy(deep=True)
    row = document.functional.requirements[0].model_copy(
        update={
            "id": "NFR-999",
            "statement": "The system shall be manageable for university-wide deployment.",
        }
    )
    document.nonfunctional.requirements.append(row)
    before = canonical_hash(document.model_dump())
    sections = {section.number: section for section in build_srs_presentation(document).sections}
    assert row.id in {item.id for item in sections["3.6.4"].requirements}
    assert row.id not in {item.id for item in sections["3.6.1"].requirements}
    assert canonical_hash(document.model_dump()) == before


def test_monitoring_authentication_records_does_not_invent_an_authentication_function(
    complete_document,
):
    """Use the canonical source clause, even when a model title suggests a different capability."""
    document = complete_document.model_copy(deep=True)
    source = "The system shall collect authentication activity from managed endpoints."
    document.functional.requirements[0].statement = source
    document.functional.requirements[0].title = "Authentication service"
    report = build_srs_presentation(document)
    functions = next(section for section in report.sections if section.number == "2.2")
    assert source.removeprefix("The system shall ").rstrip(".") + " - FR-001" in functions.bullets
    assert not any(value.startswith("Authentication") for value in functions.bullets)

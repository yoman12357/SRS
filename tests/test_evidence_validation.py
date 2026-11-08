"""Grounding, unresolved decision, reference and acceptance regressions."""

import copy

import pytest
from pydantic import ValidationError

from cybersrs.evidence import build_evidence, context_evidence_ids, validate_analysis
from cybersrs.schemas import Answer, Evidence, SourceChunk
from cybersrs.sdlc import rank_sdlc
from cybersrs.validation import consolidate_duplicates, validate_document, validate_section


def test_exact_passages_and_answer_context():
    """Numeric answers must retain the question defining their semantic subject."""
    evidence = build_evidence(
        "Support 1.5 seconds. Do not change firewall rules.",
        [
            Answer(
                question_id="Q-1", text="30 days", question_text="How long are audit logs retained?"
            ),
            Answer(question_id="Q-2", text="unknown", skipped=True),
        ],
    )
    assert evidence[0].quote == "Support 1.5 seconds."
    assert evidence[1].quote == "Do not change firewall rules."
    assert evidence[-1].quote == "30 days"
    assert "audit logs" in evidence[-1].context
    assert len(evidence) == 3


def test_schema_rejects_extra_model_fields(analysis):
    """Unexpected model content cannot be silently normalized into approved data."""
    payload = analysis.model_dump() | {"human_approved": True}
    with pytest.raises(ValidationError):
        type(analysis).model_validate(payload)


def test_analysis_cannot_omit_source(analysis, complete_document):
    """Schema-valid analysis must still account for every original passage."""
    analysis.assessments.pop()
    assert validate_analysis(analysis, complete_document.evidence)


@pytest.mark.parametrize(
    "mutation,code",
    [
        (lambda r: r.update(dependencies=["FR-999"]), "unknown_dependencies"),
        (lambda r: r.update(evidence_ids=["E-999"]), "unknown_evidence_id"),
        (
            lambda r: r.update(statement="The system shall return all alerts within 42 seconds."),
            "unsupported_numeric_specificity",
        ),
        (
            lambda r: r["acceptance_criteria"][0].update(then="The system works as expected."),
            "unobservable_acceptance_criterion",
        ),
    ],
)
def test_bad_requirements_fail_before_next_agent(complete_document, mutation, code):
    """Catch unsafe links, invented values and vacuous acceptance independently."""
    content = complete_document.functional.model_dump()
    mutation(content["requirements"][0])
    errors = validate_section(
        "functional", content, complete_document.evidence, complete_document.analysis, [], {}
    )
    assert any(code in error for error in errors)


def test_literal_citation_guard(complete_document):
    """Only exact excerpts of actually supplied chunks may be cited."""
    content = complete_document.functional.model_dump()
    source = SourceChunk(
        id="source:0",
        source_document_id="source",
        chunk_index=0,
        page_or_section="section 1",
        relevance_score=0.9,
        text="Restrict account administration to explicitly authorized roles.",
        title="Reference",
        sha256="0" * 64,
    )
    content["requirements"][0]["sources"] = [
        {"chunk_id": source.id, "quote": "fabricated supporting quotation"}
    ]
    assert any(
        "citation_quote_not_in_chunk" in error
        for error in validate_section(
            "functional",
            content,
            complete_document.evidence,
            complete_document.analysis,
            [source],
            {},
        )
    )


def test_final_traceability_and_missing_test(complete_document):
    """A structurally sound report still needs human review; every requirement needs a test."""
    report = validate_document(complete_document)
    assert report.status == "needs_review"
    assert len(report.traceability) == 2
    assert all(row["test_ids"] and row["sdlc_phases"] for row in report.traceability)
    changed = copy.deepcopy(complete_document)
    changed.verification.tests[0].requirement_ids.remove("SEC-001")
    assert validate_document(changed).status == "invalid"


@pytest.mark.parametrize(
    "text,winner",
    [
        ("The project has stable requirements.", "Waterfall"),
        ("The team needs formal verification.", "V-Model"),
        ("The project has high technical uncertainty.", "Spiral"),
        ("The team requires continuous secure delivery.", "DevSecOps"),
        ("The project has evolving requirements.", "Agile"),
    ],
)
def test_sdlc_rules_have_source_evidence(text, winner):
    """Named brief conditions justify reproducible ranked lifecycle recommendations."""
    result = rank_sdlc([Evidence(id="E-001", source="description", quote=text)])
    assert result["required_model"] == winner
    assert result["factors"][0]["evidence_ids"] == ["E-001"]
    assert "not probabilities" in result["score_meaning"]


@pytest.mark.parametrize(
    "text",
    [
        "No formal verification is required.",
        "Continuous delivery is not required.",
        "We might need formal verification.",
    ],
)
def test_negated_or_uncertain_factors_do_not_rank(text):
    """Do not treat a denial or hypothetical lifecycle condition as affirmative evidence."""
    result = rank_sdlc([Evidence(id="E-001", source="description", quote=text)])
    assert not result["factors"]
    assert result["provisional"]


@pytest.mark.parametrize(
    "text",
    [
        "Build a campus wireless network access-control requirements specification.",
        "Requirements evolve frequently and stakeholders provide weekly feedback.",
        "This project has stable requirements and needs independent verification.",
    ],
)
def test_document_request_and_lifecycle_are_not_product_features(text):
    """Do not turn the request for an SRS or an SDLC factor into target-system behavior."""
    evidence = [Evidence(id="E-001", source="description", quote=text)]
    assert context_evidence_ids(evidence) == {"E-001"}


def test_manual_source_cannot_support_an_unrelated_access_control(complete_document):
    """A real-run regression: an existing evidence ID alone does not establish grounding."""
    changed = complete_document.model_copy(deep=True)
    changed.evidence[0].quote = "Network administrators may manually isolate a device."
    changed.functional.requirements[
        0
    ].statement = "The system shall evaluate every access request using dynamic risk factors."
    report = validate_document(changed)
    assert report.status == "invalid"
    assert any("explicit_manual_mode_not_preserved" in item.code for item in report.findings)


def test_exact_control_consolidation_keeps_authored_acceptance(complete_document):
    """Repeated controls share an ID while retaining additional authored verification details."""
    original = complete_document.security.model_dump()
    incoming = copy.deepcopy(original)
    incoming["requirements"][0]["id"] = "DR-001"
    incoming["requirements"][0]["acceptance_criteria"][0]["observable_evidence"] = (
        "Retain a role-tagged denial response and associated authorization event."
    )
    normalized = consolidate_duplicates(incoming, {"security": original})
    assert normalized["requirements"] == []
    assert normalized["related_requirement_ids"] == ["SEC-001"]
    assert (
        normalized["related_acceptance_criteria"][0]["acceptance_criteria"]
        == (incoming["requirements"][0]["acceptance_criteria"])
    )
    assert original == complete_document.security.model_dump()
    assert not validate_section(
        "data",
        normalized,
        complete_document.evidence,
        complete_document.analysis,
        [],
        {"security": original},
    )


def test_planning_population_with_unknown_concurrency_is_project_context():
    """A planning figure cannot become a mandatory runtime tracking feature."""
    evidence = [
        Evidence(
            id="E-006",
            source="description",
            quote=(
                "The planning population is 2000 registered devices; "
                "concurrency is not yet decided."
            ),
        )
    ]
    assert context_evidence_ids(evidence) == {"E-006"}


@pytest.mark.parametrize(
    "changed_statement,code",
    [
        (
            "The system shall allow security operators to review alerts with all actions logged.",
            "unconfirmed_additional_audit_behavior",
        ),
        (
            "The system shall immediately allow security operators to review alerts.",
            "unsupported_response_time_commitment",
        ),
        ("The system shall retain alerts for a minimum of 30 days.", "unsupported_numeric_bound"),
    ],
)
def test_explicit_basis_cannot_gain_unconfirmed_controls_or_bounds(
    complete_document,
    changed_statement,
    code,
):
    """A valid source ID does not authorize extra logging, latency or retention bounds."""
    content = complete_document.functional.model_dump()
    content["requirements"][0]["statement"] = changed_statement
    errors = validate_section(
        "functional", content, complete_document.evidence, complete_document.analysis, [], {}
    )
    assert any(code in error for error in errors)

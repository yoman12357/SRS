"""Open planning decisions cannot turn into target-product proposal-rejection features."""

import pytest

from cybersrs.clarification_policy import normalize_analysis_decisions
from cybersrs.evidence import (
    build_evidence,
    context_evidence_ids,
    is_project_goal,
    normative_evidence_ids,
    validate_analysis,
)
from cybersrs.provider import generation_schema
from cybersrs.schemas import Analysis, EvidenceAssessment
from cybersrs.validation import validate_section

from .conftest import requirement


def test_standalone_open_review_instruction_stays_unresolved(analysis):
    """Recover a previously saved analysis that misclassified a standalone decision."""
    source = "Leave the Wi-Fi technology and audit log retention period open for review."
    evidence = build_evidence(source, [])
    draft = analysis.model_copy(update={
        "assessments": [EvidenceAssessment(
            evidence_id="E-001",
            kind="requirement",
            sections=["functional"],
            explanation="Use configurable retention and Wi-Fi.",
        )],
        "questions": [],
        "unresolved_decisions": [],
    })
    normalized = normalize_analysis_decisions(draft, evidence)
    assert normalized.assessments[0].kind == "uncertain"
    assert normalized.assessments[0].sections == ["introduction"]
    assert normalized.unresolved_decisions == [source]
    assert draft.assessments[0].kind == "requirement"


def test_bare_product_goal_does_not_authorize_a_design_feature(analysis):
    """Preserve project scope without turning the design request into product behavior."""
    source = "Design a network access system for temporary conference media accounts."
    evidence = build_evidence(source, [])
    draft = analysis.model_copy(update={"assessments": [analysis.assessments[0]]})
    assert context_evidence_ids(evidence) == {"E-001"}
    normalized = normalize_analysis_decisions(draft, evidence)
    assert normalized.assessments[0].kind == "context"
    assert normalized.assessments[0].explanation == source
    assert normalized.assessments[0].sections == ["introduction"]
    assert not is_project_goal("Design a network access system that authenticates staff.")
    assert not is_project_goal("Design a service for collecting authentication events.")


@pytest.mark.parametrize(
    "source",
    [
        "Budget, delivery schedule, response-time thresholds and mandatory regulatory "
        "frameworks are undecided and must remain open decisions.",
        "Budget, schedule and protocol choices are undecided.",
        "Response-time thresholds are unknown.",
    ],
)
def test_open_planning_declarations_are_metadata_not_product_behavior(source, analysis):
    """Reproduce the real campus NFR that invented a budget-proposal rejection subsystem."""
    evidence = build_evidence(source, [])
    assert context_evidence_ids(evidence) == {"E-001"}
    assert not normative_evidence_ids(evidence)
    draft = analysis.model_copy(deep=True)
    draft.assessments = [
        EvidenceAssessment(
            evidence_id="E-001",
            kind="constraint",
            sections=["nonfunctional"],
            explanation="An open decision.",
        )
    ]
    assert any(
        "project_context_not_product_behavior" in e for e in validate_analysis(draft, evidence)
    )
    native = generation_schema(
        Analysis,
        {"evidence": [e.model_dump() for e in evidence], "project_context_evidence_ids": ["E-001"]},
    )
    assert native["$defs"]["EvidenceAssessment"]["anyOf"][0]["properties"]["sections"]["items"][
        "enum"
    ] == ["introduction", "sdlc"]
    row = requirement(
        "The system shall reject budget proposals while the budget is undecided.", "E-001"
    ) | {"id": "NFR-001"}
    assert "NFR-001:project_context_not_product_requirement" in validate_section(
        "nonfunctional", {"requirements": [row]}, evidence, draft, [], {}
    )


def test_unknown_host_access_control_remains_a_real_product_requirement():
    """The word 'unknown' alone is not planning metadata."""
    evidence = build_evidence("The system must deny unknown hosts access to the staff network.", [])
    assert not context_evidence_ids(evidence)
    assert normative_evidence_ids(evidence) == {"E-001"}


def test_stated_simultaneous_load_is_not_lost_as_planning_metadata(analysis):
    """The real VPN input needs a canonical load requirement for its 25 sessions."""
    evidence = build_evidence("Plan for 250 registered users and 25 simultaneous sessions.", [])
    assert normative_evidence_ids(evidence) == {"E-001"}
    draft = analysis.model_copy(deep=True)
    draft.assessments = [
        EvidenceAssessment(
            evidence_id="E-001",
            kind="context",
            sections=["functional"],
            explanation="Sizing context.",
        )
    ]
    assert any(
        "explicit_product_obligation_needs_requirement_section" in e
        for e in validate_analysis(draft, evidence)
    )


def test_document_request_does_not_erase_a_product_clause():
    """An informal one-sentence SRS request can contain actual product behavior too."""
    evidence = build_evidence(
        "Build an SRS for a gateway that must deny guests access to the staff network.", []
    )
    assert not context_evidence_ids(evidence)
    assert normative_evidence_ids(evidence) == {"E-001"}
    bare = build_evidence(
        "Build an SRS for a gateway that allows students to review access requests.", []
    )
    assert not context_evidence_ids(bare)


@pytest.mark.parametrize(
    "source",
    [
        "Can we support 25 simultaneous sessions?",
        "We have not decided whether 25 simultaneous sessions are needed.",
    ],
)
def test_question_or_undecided_load_is_not_a_committed_capacity(source):
    """An explicit load declaration is different from an unanswered sizing question."""
    assert not normative_evidence_ids(build_evidence(source, []))

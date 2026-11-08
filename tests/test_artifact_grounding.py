"""Reproduce inspected whole-artifact drift, including valid source-bound controls."""

from copy import deepcopy

import pytest

from cybersrs.artifact_grounding import (
    VALIDATION_POLICY_VERSION,
    claims_recorded_approval,
    lifecycle_test_gaps,
    unsupported_quantities,
)
from cybersrs.evidence import build_evidence
from cybersrs.provider import generation_schema
from cybersrs.schemas import Evidence, RiskSection
from cybersrs.semantics import missing_source_actions
from cybersrs.validation import validate_document, validate_section

from .conftest import DESCRIPTION


@pytest.mark.parametrize("text", ["Within 500 ms", "Observe for 72 hours", "80% tests passed"])
def test_unrequested_workflow_targets_are_rejected(text):
    """A structurally complete SDLC must not fabricate measured thresholds."""
    assert unsupported_quantities(text, build_evidence(DESCRIPTION, []))


@pytest.mark.parametrize("text", ["Retain for 336 hours", "Retain for 14 days"])
def test_equivalent_source_duration_is_permitted(text):
    """Unit conversion alone must not turn a supported duration into an error."""
    source = [Evidence(id="E-001", source="description", quote="Retain logs for 14 days.")]
    assert not unsupported_quantities(text, source)


def test_failed_sign_in_counts_require_source_support_even_when_spelled_out():
    """An open detection threshold cannot become an assumed count in a test."""
    source = build_evidence(
        "Detect repeated failed sign-ins. Leave the detection threshold open for review.", []
    )
    assert unsupported_quantities("The system detects five consecutive failed sign-ins.", source)
    assert unsupported_quantities(
        "A user attempts to sign in five times with an incorrect password.", source
    )
    specified = build_evidence("Detect repeated sign-ins after 5 failed attempts.", [])
    assert not unsupported_quantities(
        "The system detects five consecutive failed sign-ins.", specified
    )
    assert not unsupported_quantities(
        "The system observes one failed authentication attempt.", source
    )


@pytest.mark.parametrize(
    "text,recorded",
    [
        ("Final approval granted by the owner", True),
        ("Approval granted by the owner", True),
        ("Final release approved by owner", True),
        ("The baseline has been approved", True),
        ("Required: owner approves before release", False),
        ("Owner must approve the proposed baseline", False),
        ("This draft records no such approval", False),
    ],
)
def test_recorded_approval_is_distinct_from_future_gate(text, recorded):
    """Generation cannot turn a proposed approval gate into a recorded decision."""
    assert claims_recorded_approval(text) is recorded


def test_retention_and_deletion_need_actual_storage_outcomes():
    """A failed read alone is compatible with records remaining in storage."""
    source = "Retain connection logs for 14 days and delete them after expiry."
    assert lifecycle_test_gaps(source, [{"then": "The expired record cannot be retrieved"}]) == [
        "retention_acceptance_outcome_missing",
        "deletion_acceptance_outcome_missing",
    ]
    assert not lifecycle_test_gaps(
        source,
        [
            {"then": "The logs remain stored throughout the 14-day interval"},
            {"then": "The expired records are deleted from storage"},
        ],
    )
    assert lifecycle_test_gaps(source, [{"then": "The records are not deleted"}])
    assert not lifecycle_test_gaps("Do not delete audit records.", [])


def test_metadata_and_workflow_fields_use_source_guards(sections, analysis):
    """Inspect rationale, assumptions and workflow targets beyond normative statements."""
    content = deepcopy(sections["functional"])
    content["requirements"][0]["rationale"] = "Only administrators may review alerts."
    errors = validate_section(
        "functional",
        content,
        build_evidence("Operators review alerts. Administrators may manage accounts.", []),
        analysis,
        [],
        {},
    )
    assert any("unconfirmed_actor_exclusivity" in code for code in errors)
    sdlc = deepcopy(sections["sdlc"])
    sdlc["phases"][0]["exit_criteria"].append("Observe for 72 hours with 80% success")
    sdlc["phases"][0]["human_approval"] = "Final release approved by project owner"
    errors = validate_section("sdlc", sdlc, build_evidence(DESCRIPTION, []), analysis, [], sections)
    assert any("unsupported_quantitative_commitment" in code for code in errors)
    assert any("workflow_claims_recorded_approval" in code for code in errors)


def test_related_criteria_cannot_assume_production_logs(sections, analysis):
    """Empty linked-record evidence falls back to its canonical requirement's source."""
    content = deepcopy(sections["data"])
    req = sections["functional"]["requirements"][0]
    criterion = deepcopy(req["acceptance_criteria"][0])
    criterion["observable_evidence"] = "Inspect production network logs for the review action"
    content["related_acceptance_criteria"] = [
        {"requirement_id": "FR-001", "evidence_ids": [], "acceptance_criteria": [criterion]}
    ]
    previous = deepcopy(sections)
    previous["functional"]["requirements"][0]["id"] = "FR-001"
    errors = validate_section(
        "data", content, build_evidence(DESCRIPTION, []), analysis, [], previous
    )
    assert any("unconfirmed_production_log_witness" in code for code in errors)


def test_segmentation_does_not_cover_firewall_and_monitoring():
    """A cited compound source still requires its missing named capabilities."""
    assert missing_source_actions(
        "A firewall and network monitoring system for a campus with separate networks.",
        "The system shall maintain separate student and faculty networks.",
        include_capabilities=True,
    ) == {"firewall", "monitoring"}


def test_quality_records_independent_policy_version(complete_document):
    """Revalidation identifies current rules without changing canonical content."""
    before = complete_document.model_dump()
    quality = validate_document(complete_document)
    assert quality.validation_policy_version == VALIDATION_POLICY_VERSION
    assert complete_document.model_dump() == before


@pytest.mark.parametrize(
    "text,code",
    [
        ("The user can browse without interruption.", "unconfirmed_uninterrupted_availability"),
        ("A visible denial message is returned.", "unconfirmed_product_message_contract"),
        ("The VPN requires mutual authentication.", "unconfirmed_mutual_authentication"),
        ("Retention ensures compliance with privacy regulations.", "unconfirmed_regulatory_claim"),
    ],
)
def test_extra_observable_promises_are_still_source_decisions(text, code, analysis):
    """A measurable addition is not automatically an authorized requirement."""
    content = {"summary": text, "items": [], "open_issues": []}
    assert any(
        code in error
        for error in validate_section(
            "glossary",
            content,
            build_evidence("Users may access the internet.", []),
            analysis,
            [],
            {},
        )
    )
    assert not validate_section(
        "glossary",
        content,
        build_evidence(text, []),
        analysis,
        [],
        {},
    )


@pytest.mark.parametrize(
    "text",
    [
        "Access is denied; the test captures the response.",
        "A visible denial message is not required.",
        "Do not promise uninterrupted access.",
    ],
)
def test_observability_and_explicitly_unpromised_choices_are_permitted(text, analysis):
    """Source guards must preserve a valid test or an explicit unknown decision."""
    assert not validate_section(
        "glossary",
        {"summary": text, "items": [], "open_issues": []},
        build_evidence(DESCRIPTION, []),
        analysis,
        [],
        {},
    )


def test_unprovided_risk_ratings_stay_unknown_in_decoder_and_validator(sections, analysis):
    """A plausible threat does not establish likelihood or project impact ratings."""
    evidence = build_evidence(DESCRIPTION, [])
    schema = generation_schema(RiskSection, {"evidence": [e.model_dump() for e in evidence]})
    assert schema["$defs"]["Risk"]["properties"]["likelihood"]["enum"] == ["unknown"]
    content = {
        "risks": [
            {
                "id": "RISK-001",
                "description": "An unauthorized person could view operator alerts.",
                "likelihood": "high",
                "impact": "unknown",
                "rationale": "The source provides no likelihood assessment.",
                "mitigation": "Proposed: verify the stated role boundary with captured responses.",
                "requirement_ids": [],
                "evidence_ids": ["E-001"],
                "owner": "TBD",
            }
        ],
        "open_issues": [],
    }
    errors = validate_section("risks", content, evidence, analysis, [], sections)
    assert any("risk_rating_without_source_basis" in code for code in errors)


def test_explicit_rating_labels_are_preserved_in_native_vocabulary():
    """Retain a real supplied assessment instead of replacing every rating with unknown."""
    evidence = build_evidence("Risk likelihood is low. High impact is expected.", [])
    schema = generation_schema(RiskSection, {"evidence": [e.model_dump() for e in evidence]})
    assert schema["$defs"]["Risk"]["properties"]["likelihood"]["enum"] == ["unknown", "low"]
    assert schema["$defs"]["Risk"]["properties"]["impact"]["enum"] == ["unknown", "high"]

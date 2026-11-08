"""Reject the real linear Agile workflow and inferred delivery-role assignments."""

from copy import deepcopy

from cybersrs.evidence import build_evidence
from cybersrs.provider import generation_schema
from cybersrs.schemas import SDLCSection
from cybersrs.sdlc_validation import confirmed_delivery_roles, validate_lifecycle_structure
from cybersrs.validation import validate_section


def test_a_linear_sequence_with_agile_label_is_not_an_iteration(sections):
    """A methodology label cannot stand in for its actual feedback and build/test cycle."""
    content = deepcopy(sections["sdlc"])
    content["selected_model"] = "Agile"
    template = content["phases"][0]
    content["phases"] = [
        template | {"name": kind, "phase_type": kind, "activities": [f"Perform the {kind} work."]}
        for kind in ["planning", "design", "implementation", "verification", "release"]
    ]
    issues = validate_lifecycle_structure(content)
    assert "sdlc:agile_needs_implementation_and_verification_within_iteration" in issues
    assert "sdlc:agile_needs_feedback_return_path" in issues
    assert not validate_lifecycle_structure(sections["sdlc"])


def test_new_agile_native_schema_has_typed_phases_and_no_v_pairs():
    """Prevent the observed null phase types and unrelated V-model plan relationships."""
    schema = generation_schema(SDLCSection, {"sdlc_decision": {"required_model": "Agile"}})
    phase = schema["$defs"]["SDLCPhase"]
    assert "phase_type" in phase["required"]
    assert phase["properties"]["phase_type"]["type"] == "string"
    assert "iteration" in phase["properties"]["phase_type"]["enum"]
    assert schema["properties"]["verification_pairs"]["maxItems"] == 0


def test_operational_permission_and_explicit_project_assignment_are_distinct():
    """Known users are not automatically developers or release approvers."""
    assert confirmed_delivery_roles("Operators review alerts.", ["Operators"]) == []
    source = "The project manager approves the release. Operators review alerts."
    assert confirmed_delivery_roles(source, ["project manager", "Operators"]) == ["project manager"]
    assert confirmed_delivery_roles(source, ["project manager"], "implementation") == []
    assert confirmed_delivery_roles(source, ["project manager"], "release") == ["project manager"]
    assert confirmed_delivery_roles("Operators must not approve the release.", ["Operators"]) == []


def test_source_product_roles_need_proposed_delivery_labels(sections, analysis):
    """Apply the independent role gate even when a decoder returns an unqualified source role."""
    content = deepcopy(sections["sdlc"])
    content["phases"][0]["roles"] = ["Security operators"]
    errors = validate_section(
        "sdlc",
        content,
        build_evidence("Security operators review alerts. Administrators manage accounts.", []),
        analysis,
        [],
        sections,
    )
    assert "sdlc:unconfirmed_role_needs_proposed_label" in errors


def test_null_phase_types_and_non_v_pairs_are_rejected(sections):
    """These observed artifacts cannot bypass validation through historical optional defaults."""
    content = deepcopy(sections["sdlc"])
    content["phases"][0]["phase_type"] = None
    content["verification_pairs"] = [{"development_phase": "Review"}]
    errors = validate_lifecycle_structure(content)
    assert "sdlc:phase_type_required" in errors
    assert "sdlc:non_v_workflow_must_not_claim_v_pairs" in errors

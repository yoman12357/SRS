"""Linked lifecycle workflows preserve source scope and distinguish proposed roles."""

from cybersrs.evidence import build_evidence
from cybersrs.provider import generation_schema
from cybersrs.schemas import SDLCSection
from cybersrs.semantics import semantic_issues
from cybersrs.validation import validate_document


def test_policy_change_audit_scope_is_not_expanded_to_every_admin_action() -> None:
    """A source citation cannot justify a broader lifecycle security check."""
    evidence = build_evidence("The system must record administrator policy changes.", [])
    assert semantic_issues("Validate audit logs for all administrator actions.", evidence)
    assert semantic_issues("Validate audit logs for administrator policy changes.", evidence) == []


def test_lifecycle_lists_receive_the_same_scope_checks(complete_document) -> None:
    """Security-check list strings cannot bypass validation applied to prose claims."""
    evidence = build_evidence("The system must record administrator policy changes.", [])
    complete_document.evidence += [item.model_copy(update={"id": "E-003"}) for item in evidence]
    complete_document.sdlc.phases[0].security_checks = [
        "Validate audit logs for all administrator actions."
    ]
    assert any(
        "policy_change_audit_is_not_all_administrator_activity" in finding.code
        for finding in validate_document(complete_document).findings
    )


def test_sdlc_native_grammar_marks_unconfirmed_roles_as_proposed() -> None:
    """A product operator role is not proof of a project delivery responsibility."""
    schema = generation_schema(
        SDLCSection,
        {
            "analysis": {"stakeholders": ["Operators"]},
            "evidence": [{"id": "E-001", "quote": "Operators review alerts."}],
        },
    )
    choices = schema["$defs"]["SDLCPhase"]["properties"]["roles"]["items"]["anyOf"]
    assert {"type": "string", "enum": ["Operators"]} not in choices
    assert any(item.get("pattern") == "^[Pp]roposed[ :].+$" for item in choices)


def test_agile_exit_gate_cannot_freeze_future_requirement_changes(
    complete_document, sections
) -> None:
    """A model may close the current iteration, not demand that future changes stop."""
    # This regression targets an Agile gate, independently of the current ranking winner.
    complete_document.sdlc = SDLCSection.model_validate(sections["sdlc"])
    complete_document.sdlc.phases[0].exit_criteria = [
        "No new requirement changes are proposed in the next cycle."
    ]
    assert any(
        "agile_exit_cannot_require_future_changes_to_stop" in finding.code
        for finding in validate_document(complete_document).findings
    )

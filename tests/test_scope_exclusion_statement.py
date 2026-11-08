"""An explicit noun-form exclusion cannot become copied positive requirements."""

from cybersrs.prohibition_verification import (
    prohibition_statement_is_faithful,
    prohibition_test_gaps,
    verbatim_prohibition_statements,
)
from cybersrs.provider import generation_schema
from cybersrs.schemas import RequirementsSection

from .test_permission_verification import criterion

SOURCE = "Automatic firewall reconfiguration and active vulnerability scanning are out of scope."


def test_noun_form_exclusion_preserves_both_named_excluded_actions() -> None:
    """The model authors tests and rationale while the explicit exclusion's scope stays fixed."""
    allowed = verbatim_prohibition_statements(SOURCE)
    assert allowed == [
        "The system shall exclude Automatic firewall reconfiguration "
        "and active vulnerability scanning from its scope."
    ]
    assert prohibition_statement_is_faithful(SOURCE, allowed[0])
    assert not prohibition_statement_is_faithful(
        SOURCE, "The system shall provide a secure remote-access VPN."
    )
    schema = generation_schema(RequirementsSection, {"allowed_prohibition_statements": allowed})
    assert schema["$defs"]["Requirement"]["properties"]["statement"]["enum"] == allowed
    assert schema["properties"]["requirements"]["maxItems"] == 1
    assert (
        "maxItems" not in generation_schema(RequirementsSection, {})["properties"]["requirements"]
    )


def test_uncertain_scope_question_is_not_frozen_as_a_prohibition() -> None:
    """An unresolved question must remain a decision, not a stakeholder commitment."""
    assert verbatim_prohibition_statements("Are automatic firewall changes out of scope?") == []


def test_both_reconfiguration_and_scanning_need_separate_or_combined_attempts() -> None:
    """A firewall-only attempt cannot stand in for the independent scanning exclusion."""
    firewall = criterion(
        "An authorized isolated test environment has a captured baseline configuration",
        "The harness attempts automatic firewall reconfiguration",
        "The firewall configuration remains unchanged",
    )
    firewall["observable_evidence"] = "Compare captured before and after firewall configuration"
    assert prohibition_test_gaps(SOURCE, [firewall])
    scanning = criterion(
        "An authorized isolated test environment has a captured baseline activity state",
        "The harness attempts automated active vulnerability scanning",
        "No active scanning is performed and the network state remains unchanged",
    )
    scanning["observable_evidence"] = "Compare before and after activity state and network traces"
    assert prohibition_test_gaps(SOURCE, [firewall, scanning]) == []

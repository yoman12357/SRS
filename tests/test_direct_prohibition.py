"""Already normative human prohibitions must not acquire different logical scope."""

from cybersrs.prohibition_verification import (
    prohibition_statement_is_faithful,
    prohibition_test_gaps,
    verbatim_prohibition_statements,
)
from cybersrs.provider import generation_schema
from cybersrs.schemas import Requirement

from .test_prohibition_verification import GOOD, SOURCE


def test_two_independent_prohibitions_cannot_become_one_prohibited_method() -> None:
    """Not isolating via a firewall change does not forbid other automatic firewall changes."""
    assert not prohibition_statement_is_faithful(
        SOURCE, "The system shall not automatically isolate devices using firewall rule changes."
    )
    assert prohibition_statement_is_faithful(SOURCE, SOURCE)
    assert prohibition_statement_is_faithful(
        SOURCE, "The system shall not automatically change firewall rules or isolate devices."
    )
    assert prohibition_statement_is_faithful(SOURCE, SOURCE.upper().rstrip("."))


def test_source_bound_wording_is_in_the_decoder_vocabulary() -> None:
    """The model can select a faithful form while authoring rationale, classification and tests."""
    forms = verbatim_prohibition_statements(SOURCE)
    wire = generation_schema(Requirement, {"allowed_prohibition_statements": forms})
    assert wire["properties"]["statement"]["enum"] == forms
    assert verbatim_prohibition_statements("Do not automatically change firewall rules?") == []


def test_manual_action_is_not_a_test_of_the_prohibited_automatic_trigger() -> None:
    """A baseline mentioning automation cannot turn a later manual action into an auto test."""
    manual = GOOD | {
        "given": "The initial state has no automatic rule changes or device isolation",
        "when": "An operator manually changes firewall rules or isolates a device",
    }
    assert prohibition_test_gaps(SOURCE, [manual])
    equivalent = GOOD | {
        "then": "No automatic change or isolation occurs; the original configuration is preserved",
        "observable_evidence": "Inspect the unchanged firewall rule and connectivity state "
        "after the attempt",
    }
    assert prohibition_test_gaps(SOURCE, [equivalent]) == []

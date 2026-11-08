"""Permission-boundary checks distinguish successful work from denied actions."""

import re

import pytest

from cybersrs.permission_verification import (
    has_positive_test_outcome,
    permission_gap_action,
    permission_statement_gaps,
    permission_test_contract,
    permission_test_gaps,
)
from cybersrs.provider import generation_schema
from cybersrs.schemas import AcceptanceTestRepair


def criterion(given: str, when: str, then: str) -> dict[str, str]:
    """Build an observable acceptance test for focused boundary checks."""
    return {
        "given": given,
        "when": when,
        "then": then,
        "method": "test",
        "observable_evidence": "Capture the displayed response and resulting state.",
    }


def test_missing_action_binding_cannot_promote_a_denied_or_unstated_action():
    """A gap name alone must not create a permission or decoder constraint."""
    gap = "permitted_acknowledgement_outcome_not_observed"
    assert permission_gap_action("Operators may review and acknowledge alerts.", gap) == (
        "acknowledgement"
    )
    assert (
        permission_gap_action("Operators may review alerts but cannot acknowledge them.", gap)
        is None
    )
    assert permission_gap_action("Operators review alerts.", gap) is None
    assert permission_gap_action("Operators may review alerts.", "unrecognized_gap") is None


def test_connectivity_noun_alone_cannot_prove_successful_permission():
    """Unchanged connectivity is a state observation; established access is a success."""
    assert not has_positive_test_outcome("The configuration and connectivity remain unchanged.")
    assert has_positive_test_outcome("The requested internet connection is established.")
    assert not has_positive_test_outcome("The requested connection is not established.")
    assert not has_positive_test_outcome(
        "The system shall deny access and prevent any session establishment to the staff network."
    )


def test_native_supplemental_test_binds_when_to_the_missing_positive_action():
    """The observed review-only WHEN cannot satisfy an acknowledgement-specific request."""
    context = {
        "source": (
            "Security operators may review and acknowledge alerts but may not change policies."
        ),
        "gap_to_close": "permitted_acknowledgement_outcome_not_observed",
        "existing_requirements": [{"id": "SEC-001"}],
    }
    schema = generation_schema(AcceptanceTestRepair, context)
    pattern = schema["$defs"]["AcceptanceCriterion"]["properties"]["when"]["pattern"]
    assert re.search(pattern, "The operator acknowledges the alert")
    assert not re.search(pattern, "The operator reviews a network access alert")
    context["source"] = "Security operators may review alerts but cannot acknowledge them."
    schema = generation_schema(AcceptanceTestRepair, context)
    assert "pattern" not in schema["$defs"]["AcceptanceCriterion"]["properties"]["when"]


def test_internet_request_cannot_also_count_as_a_staff_network_denial_attempt():
    """Reproduce the live criterion that asserted denial without attempting its target."""
    source = (
        "Students and guests may access the internet but must not access "
        "the internal staff network."
    )
    combined = criterion(
        "A student or guest requests internet access",
        "The policy is evaluated",
        "Internet access is allowed and staff network access is denied",
    )
    assert "prohibited_actor_action_denial_not_tested" in permission_test_gaps(source, [combined])
    staff = criterion(
        "A student or guest is present",
        "The student or guest requests staff network access",
        "The request is denied",
    )
    assert permission_test_gaps(source, [combined, staff]) == []


def test_denied_research_data_target_is_extracted_from_suffix_access_wording():
    """Contractor restrictions must test research data, not a request for the allowed portal."""
    contract = permission_test_contract(
        "Contractors may access only the support portal and must be denied research data access."
    )
    assert contract["denied_action"] == "access"
    assert contract["denied_access_target"] == "research data"


def test_positive_only_compound_permission_needs_restoration_test():
    """Reproduce the real campus row whose only test exercised isolation."""
    source = "Network administrators may manually isolate a device and restore its access."
    contract = permission_test_contract(source)
    assert contract["denied_action"] is None
    isolated = criterion(
        "A network administrator selects a connected device",
        "The administrator manually isolates it",
        "The device is isolated",
    )
    gaps = permission_test_gaps(source, [isolated])
    assert gaps == ["permitted_restoration_outcome_not_observed"]
    restored = criterion(
        "A network administrator selects the isolated device",
        "The administrator restores its access",
        "Device access is restored",
    )
    assert permission_test_gaps(source, [isolated, restored]) == []


@pytest.mark.parametrize(
    "outcome",
    [
        "Access is not permitted",
        "The request is denied with a visible denial",
        "Access is not allowed",
    ],
)
def test_denial_cannot_count_as_positive_permission_success(outcome):
    """Generic visibility and negated allowance are not successful source behavior."""
    source = "Students may access the internet."
    tests = [criterion("A student is present", "The student requests internet access", outcome)]
    assert "positive_permission_test_missing" in permission_test_gaps(source, tests)


def test_policy_unchanged_during_acknowledgement_is_not_edit_denial() -> None:
    """A permitted action cannot stand in for an attempted forbidden action."""
    source = "Security operators may review and acknowledge alerts but may not change policies."
    tests = [
        criterion("An operator has an alert", "The operator reviews it", "The alert is displayed"),
        criterion(
            "An operator has an alert",
            "The operator acknowledges it",
            "Acknowledgement succeeds and policies remain unchanged",
        ),
    ]
    assert "prohibited_actor_action_denial_not_tested" in permission_test_gaps(source, tests)
    tests.append(
        criterion("An operator is signed in", "The operator edits a policy", "The edit is denied")
    )
    assert permission_test_gaps(source, tests) == []


def test_access_permission_needs_both_target_success_and_denial() -> None:
    """A staff-network denial does not prove the permitted internet path works."""
    source = "Students and guests may access the internet but must not access the staff network."
    denial = criterion(
        "A student is connected", "The student accesses the staff network", "Access is denied"
    )
    assert "permitted_access_target_not_tested" in permission_test_gaps(source, [denial])
    positive = criterion(
        "A student is connected", "The student requests internet access", "Internet access succeeds"
    )
    assert permission_test_gaps(source, [positive, denial]) == []


def test_denial_action_in_given_is_still_an_exercised_boundary() -> None:
    """Recognize an explicit attempted action even when the model puts it in Given."""
    source = "Students may access the internet but must not access the staff network."
    tests = [
        criterion("A student requests internet access", "The request is tested", "Access succeeds"),
        criterion(
            "A student attempts staff network access", "The request is tested", "Access is denied"
        ),
    ]
    assert permission_test_gaps(source, tests) == []


def test_adjacent_role_clause_does_not_turn_remote_access_into_a_target() -> None:
    """A hyphenated topic and an earlier administrator clause are not operator permissions."""
    source = (
        "Administrators manage remote-access permissions; support operators may inspect "
        "connection logs but cannot grant permissions."
    )
    contract = permission_test_contract(source)
    assert contract["positive_access_target"] == ""
    assert contract["actor_role_terms"] == ["operator"]
    assert contract["positive_clause"].startswith("support operators may inspect")
    tests = [
        criterion(
            "A support operator is signed in", "The operator inspects logs", "Logs are displayed"
        ),
        criterion(
            "A support operator is signed in",
            "The operator grants permissions",
            "The grant is denied",
        ),
    ]
    assert permission_test_gaps(source, tests) == []


def test_denial_inflections_and_refusals_are_observable_negative_outcomes() -> None:
    """Do not reject the same permission result because the model writes 'denies' or 'refuses'."""
    source = "Students and guests may access the internet but must not access the staff network."
    positive = criterion(
        "A student or guest test identity is present",
        "The identity requests internet access",
        "Internet access succeeds",
    )
    for outcome in (
        "The system denies staff-network access",
        "The system refuses the request",
        "Access is not granted",
        "A denial response is returned",
    ):
        negative = criterion(
            "A student or guest test identity is present",
            "The identity requests staff-network access",
            outcome,
        )
        assert permission_test_gaps(source, [positive, negative]) == []


def test_system_blocks_a_separate_destination_from_the_guest_allowance() -> None:
    """Bind the guest's permitted internet and restricted network to distinct tests."""
    source = (
        "Guests can access the internet, and the system must block their access "
        "to internal university networks."
    )
    contract = permission_test_contract(source)
    assert contract["positive_access_target"] == "internet"
    assert contract["denied_access_target"] == "internal university networks"
    positive = criterion(
        "A guest is connected", "The guest requests internet access", "The internet is reachable"
    )
    negative = criterion(
        "A guest is connected",
        "The guest attempts to connect to an internal university network resource",
        "The attempt is blocked",
    )
    assert permission_test_gaps(source, [positive, negative]) == []
    assert "permitted_access_target_not_tested" in permission_test_gaps(source, [negative])
    assert "prohibited_actor_action_denial_not_tested" in permission_test_gaps(source, [positive])
    assert permission_statement_gaps(
        source, ["The system shall block guests from accessing internal university networks."]
    ) == ["positive_access_destination_missing_from_statement"]
    assert permission_statement_gaps(
        source, ["Guests shall be able to access the internet."]
    ) == ["denied_access_destination_missing_from_statement"]
    assert not permission_statement_gaps(
        source,
        ["The system shall allow guests to access the internet and block their access "
         "to internal university networks."],
    )

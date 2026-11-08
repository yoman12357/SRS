"""Opening a log dashboard and receiving its data is an exercised inspection."""

import pytest

from cybersrs.permission_verification import permission_test_gaps

from .test_permission_verification import criterion


@pytest.mark.parametrize(
    "given",
    [
        "A support operator accesses the connection logs dashboard after authentication.",
        "A support operator opens the connection log viewer.",
        "A support operator navigates to the connection log dashboard.",
    ],
)
def test_dashboard_access_and_visible_data_demonstrate_inspection(given: str) -> None:
    """Reproduce the actual VPN read test without requiring a particular request verb."""
    tests = [
        criterion(
            given,
            "The system loads the logs interface for active and historical VPN sessions.",
            "The system shall display all relevant connection logs for inspection.",
        )
    ]
    assert permission_test_gaps("Support operators may inspect connection logs.", tests) == []


def test_a_button_to_inspect_is_not_the_inspected_data() -> None:
    """An available action cannot stand in for the actual read result."""
    tests = [
        criterion(
            "A support operator opens the dashboard",
            "The system loads the interface",
            "The system displays a button allowing inspection of connection logs.",
        )
    ]
    assert "permitted_review_outcome_not_observed" in permission_test_gaps(
        "Support operators may inspect connection logs.", tests
    )


def test_another_roles_read_does_not_prove_operator_access() -> None:
    """An administrator's readable logs cannot stand in for the named support role."""
    tests = [
        criterion(
            "An administrator opens the log viewer",
            "The system loads the interface",
            "The system displays connection logs",
        )
    ]
    assert "permitted_review_outcome_not_observed" in permission_test_gaps(
        "Support operators may inspect connection logs.", tests
    )


def test_admin_abbreviation_preserves_the_named_administrator_role() -> None:
    """An ordinary abbreviation must not trigger needless permission corrections."""
    tests = [
        criterion(
            "An admin selects the isolated device",
            "The admin restores its access",
            "The device access is restored",
        )
    ]
    assert permission_test_gaps("Administrators may restore device access.", tests) == []

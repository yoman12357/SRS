"""Live permission-test wording must not be rejected for harmless success qualifiers."""

import pytest

from cybersrs.permission_verification import permission_test_gaps
from tests.test_permission_verification import criterion


@pytest.mark.parametrize(
    "outcome",
    [
        "The system allows successful connection to the internet, "
        "with no error message indicating denial of service.",
        "Internet access succeeds without errors.",
        "Without errors, the internet connection succeeds.",
        "The requested internet page is rendered in the browser.",
    ],
)
def test_success_is_preserved_with_error_absence_qualifiers(outcome: str) -> None:
    """Reproduce the rejected campus result without counting error absence alone."""
    tests = [criterion("A student is connected", "The student accesses the internet", outcome)]
    assert permission_test_gaps("Students may access the internet.", tests) == []


@pytest.mark.parametrize(
    "outcome",
    [
        "Internet access does not succeed.",
        "Internet access is not successful.",
        "The internet page is not successfully displayed.",
        "No errors are reported.",
    ],
)
def test_negated_success_and_error_absence_do_not_prove_access(outcome: str) -> None:
    """Retain the positive-result obligation rather than accepting mere lack of errors."""
    tests = [criterion("A student is connected", "The student accesses the internet", outcome)]
    assert "positive_permission_test_missing" in permission_test_gaps(
        "Students may access the internet.", tests
    )


def test_log_inspection_accepts_returned_view_as_review() -> None:
    """Reproduce the VPN test's visible logs rather than demanding the verb inspect."""
    source = "Support operators may inspect connection logs but cannot grant permissions."
    tests = [
        criterion(
            "A support operator is signed in",
            "The operator requests connection logs",
            "The system returns a view of the connection logs without modifying permissions.",
        ),
        criterion(
            "A support operator is signed in",
            "The operator grants permissions",
            "The grant is denied",
        ),
    ]
    assert permission_test_gaps(source, tests) == []


@pytest.mark.parametrize(
    ("source", "action", "outcome"),
    [
        ("approve or reject", "approves", "The request is marked as approved in the system state"),
        ("approve", "initiates approval of", "The system records an approved decision"),
        ("approve", "approves", "The request's approved decision is observed in the system state"),
        ("reject", "rejects", "The request is rejected in the system state"),
    ],
)
def test_authorized_request_decision_is_an_observable_success(
    source: str, action: str, outcome: str
) -> None:
    """An approved or deliberately rejected request is the observed permission outcome."""
    tests = [
        criterion(
            "A data steward reviews a dataset sharing request",
            f"The data steward {action} the request",
            outcome,
        )
    ]
    assert permission_test_gaps(f"A data steward can {source} the request.", tests) == []


def test_denied_approval_does_not_satisfy_a_stewards_permission() -> None:
    """Distinguish intentional rejection from an unsuccessful approval operation."""
    tests = [
        criterion(
            "A data steward reviews a pending request",
            "The data steward approves the request",
            "The request is not approved and the action is denied",
        )
    ]
    assert "positive_permission_test_missing" in permission_test_gaps(
        "A data steward can approve or reject the request.", tests
    )

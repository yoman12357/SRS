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

"""A permitted action must be exercised, not just mentioned as an available outcome."""

from cybersrs.permission_verification import permission_test_gaps

from .test_permission_verification import criterion


def test_available_acknowledgement_is_not_an_attempted_acknowledgement() -> None:
    """Reproduce the live campus view test whose Then merely allowed a second action."""
    source = "Security operators may review and acknowledge alerts but may not change policies."
    tests = [
        criterion(
            "A security operator attempts to view an alert",
            "The system processes the request",
            "The alert is displayed and the operator is allowed to acknowledge it",
        ),
        criterion("An operator is signed in", "The operator changes a policy", "Change is denied"),
    ]
    assert permission_test_gaps(source, tests) == ["permitted_acknowledgement_outcome_not_observed"]
    tests.append(
        criterion(
            "An operator has viewed the alert",
            "The operator acknowledges the alert",
            "The acknowledgement is accepted and displayed",
        )
    )
    assert permission_test_gaps(source, tests) == []


def test_initial_isolated_state_does_not_prove_isolation_was_tested() -> None:
    """A restoration-only test starts with an isolated device but never isolates one."""
    source = "Network administrators may manually isolate a device and restore its access."
    tests = [
        criterion(
            "An administrator selects an isolated device",
            "The administrator restores its access",
            "Device access is restored",
        )
    ]
    assert permission_test_gaps(source, tests) == ["permitted_isolation_outcome_not_observed"]

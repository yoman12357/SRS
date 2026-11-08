"""Source retention authorizes existing records, not new product-event logs."""

import pytest

from cybersrs.acceptance_grounding import acceptance_logging_issues


@pytest.mark.parametrize(
    "witness",
    [
        "Record of deletion event logged by the system, showing removal of a connection log.",
        "The deletion event is recorded in the system log.",
        "Inspect the system-generated deletion-event log.",
    ],
)
def test_retaining_connection_records_does_not_require_deletion_event_logging(witness):
    """Reproduce the actual DR-001 witness and equivalent creation assertions."""
    source = "The system must retain connection logs for 14 days and remove them after expiry."
    criterion = {
        "then": "The expired connection log is removed from storage.",
        "observable_evidence": witness,
    }
    assert "unconfirmed_production_log_witness_use_test_capture" in acceptance_logging_issues(
        source, criterion
    )


@pytest.mark.parametrize(
    "witness",
    [
        "Inspect stored connection logs before and after expiry.",
        "Compare retained records using a controlled test clock and storage inspection.",
        "Use test-harness logs of the before/after storage observations.",
    ],
)
def test_existing_records_and_external_test_captures_remain_permitted(witness):
    """Storage inspection and test-owned recordings do not expand product behavior."""
    source = "The system must retain connection logs for 14 days and remove them after expiry."
    criterion = {
        "then": "The connection log is stored during retention and removed after expiry.",
        "observable_evidence": witness,
    }
    assert acceptance_logging_issues(source, criterion) == []


def test_explicit_event_recording_remains_permitted():
    """Do not block a deletion-event log when the user actually requires it."""
    criterion = {
        "then": "The deletion event is recorded in the audit log.",
        "observable_evidence": "Inspect the system-generated deletion-event log.",
    }
    assert acceptance_logging_issues("The system must record log deletion events.", criterion) == []

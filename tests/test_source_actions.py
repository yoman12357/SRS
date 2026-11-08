"""A source identifier cannot hide omissions inside a compound stakeholder statement."""

from cybersrs.semantics import missing_source_actions, missing_source_quantities


def test_manual_isolation_and_restoration_both_need_normative_outcomes() -> None:
    """Matching isolation alone must not count as coverage of the restoration behavior."""
    source = "Network administrators may manually isolate a device and restore its access."
    assert missing_source_actions(source, "An administrator shall manually isolate a device.") == {
        "restoration",
    }
    assert not missing_source_actions(
        source,
        "The system shall support manual device isolation and access restoration.",
    )


def test_log_review_and_acknowledgement_are_distinct_actions() -> None:
    """An alert-review requirement cannot silently omit the acknowledgement workflow."""
    assert "acknowledgement" in missing_source_actions(
        "Operators may review and acknowledge alerts.",
        "Operators shall inspect alerts.",
    )


def test_record_noun_does_not_invent_a_logging_action() -> None:
    """Retaining existing records does not authorize a new record-creation feature."""
    assert not missing_source_actions(
        "Retain audit records for 30 days.", "The system shall store audit entries for 30 days."
    )


def test_quantities_cannot_disappear_behind_a_valid_evidence_id() -> None:
    """Preserve actual durations and execution metrics, rather than counting only source links."""
    assert missing_source_quantities(
        "Retain connection logs for 14 days.", "The system shall retain connection logs."
    ) == {"14_day"}
    assert not missing_source_quantities(
        "Retain connection logs for 14 days.",
        "The system shall retain connection logs for 14 days.",
    )

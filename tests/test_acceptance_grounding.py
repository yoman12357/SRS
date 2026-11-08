"""Actual campus isolation tests must not invent audit logging as product scope."""

import pytest

from cybersrs.acceptance_grounding import acceptance_logging_issues, acceptance_response_issues
from cybersrs.evidence import build_evidence
from cybersrs.schemas import EvidenceAssessment
from cybersrs.validation import validate_section

from .conftest import requirement


def test_explicit_disconnection_allows_session_termination_only() -> None:
    """A requested disconnection permits ending the session, but not account lockout."""
    source = "If an administrator revokes access, the system must disconnect the guest."
    criterion = {"then": "The system terminates the existing guest session."}
    assert acceptance_response_issues(source, criterion) == []
    assert acceptance_response_issues(
        source, {"then": "The system terminates the guest session and locks the account."}
    ) == ["unconfirmed_automatic_response"]
    assert acceptance_response_issues("The system must detect session misuse.", criterion) == [
        "unconfirmed_automatic_response"
    ]


def test_isolation_result_cannot_add_audit_logging() -> None:
    """Reproduce the observed result and witness, even without an added timing promise."""
    source = "Network administrators may manually isolate a device and restore its access."
    criterion = {
        "then": "The system blocks network access and records the action in audit logs.",
        "observable_evidence": "Record of the device in the system's access control log.",
    }
    assert len(acceptance_logging_issues(source, criterion)) == 2


@pytest.mark.parametrize(
    "witness",
    [
        "Compare test-harness logs of before and after connectivity.",
        "Record of successful internet access session captured in a test instrumented log "
        "or state response.",
        "Capture the successful result in a test-instrumented log.",
    ],
)
def test_verification_instrumentation_does_not_create_product_logging(witness: str) -> None:
    """A test collector may persist its observations even if product logs are unspecified."""
    source = "Network administrators may manually isolate a device."
    criterion = {
        "then": "Device access is blocked and the test harness records the observed response.",
        "observable_evidence": witness,
    }
    assert acceptance_logging_issues(source, criterion) == []


def test_source_required_logs_remain_available_for_inspection() -> None:
    """Do not forbid the connection log view explicitly requested in the VPN source."""
    source = "Support operators may inspect connection logs."
    criterion = {
        "then": "The system displays connection logs.",
        "observable_evidence": "Capture the returned connection log view.",
    }
    assert acceptance_logging_issues(source, criterion) == []


def test_explicit_recording_verb_authorizes_the_requested_event_log() -> None:
    """A source need not use the literal word log to request recording policy changes."""
    source = "The system must record administrator policy changes."
    criterion = {
        "then": "The requested policy change is recorded in the audit log.",
        "observable_evidence": "Query the audit log for the policy-change event.",
    }
    assert acceptance_logging_issues(source, criterion) == []


def test_section_validation_checks_log_scope(analysis) -> None:
    """The new guard must run in real section acceptance, not only in a helper test."""
    source = "The system must deny guest access to the staff network."
    evidence = build_evidence(source, [])
    interpretation = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id="E-001",
                    kind="requirement",
                    sections=["functional"],
                    explanation="Explicit guest access boundary.",
                )
            ]
        }
    )
    row = requirement("The system shall deny guest access to the staff network.", "E-001")
    row["id"] = "FR-001"
    row["acceptance_criteria"][0]["then"] = "The request is denied and logged in audit logs."
    errors = validate_section(
        "functional", {"requirements": [row]}, evidence, interpretation, [], {}
    )
    assert any("unrequested_product_logging" in issue for issue in errors)


def test_retention_source_cannot_authorize_a_new_deletion_event_log(analysis) -> None:
    """Run the actual DR-001 witness through section validation despite source log nouns."""
    source = "The system must retain connection logs for 14 days and remove them after expiry."
    row = requirement(source, "E-001") | {"id": "DR-001"}
    row["acceptance_criteria"][0].update(
        then="The expired connection log is removed from storage.",
        observable_evidence="Record of deletion event logged by the system.",
    )
    interpretation = analysis.model_copy(update={"assessments": []})
    errors = validate_section(
        "data", {"requirements": [row]}, build_evidence(source, []), interpretation, [], {}
    )
    assert "DR-001:unconfirmed_production_log_witness_use_test_capture" in errors

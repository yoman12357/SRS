"""An unspecified manual restoration must not acquire an invented waiting policy."""

import pytest

from cybersrs.evidence import build_evidence
from cybersrs.schemas import EvidenceAssessment
from cybersrs.semantics import unsupported_wait_condition
from cybersrs.validation import validate_section

from .conftest import requirement

SOURCE = "Network administrators may manually isolate a device and restore its access."


@pytest.mark.parametrize(
    "outcome",
    [
        "The system isolates the device and after a defined period allows restoration.",
        "The system restores access within the defined isolation period.",
        "Restoration is available after a configured cooldown.",
    ],
)
def test_unspecified_waiting_policy_is_rejected(outcome: str) -> None:
    """Reproduce the current live restoration outcome and equivalent new conditions."""
    assert unsupported_wait_condition(SOURCE, outcome)


@pytest.mark.parametrize(
    "source,outcome",
    [
        (SOURCE, "The selected device's network access is restored."),
        (SOURCE, "The device is restored after the administrator requests restoration."),
        (
            "Retain records for 30 days.",
            "The record remains available within the retention period.",
        ),
        (
            "Restoration is permitted after a cooldown period.",
            "Restoration succeeds after the cooldown.",
        ),
    ],
)
def test_source_supported_timing_and_action_sequence_remain_valid(
    source: str, outcome: str
) -> None:
    """A waiting policy explicitly in the source is different from invented delay."""
    assert not unsupported_wait_condition(source, outcome)


def test_section_gate_rejects_the_live_manual_restoration_period(analysis) -> None:
    """The section acceptance path must reject the observed new temporal condition."""
    evidence = build_evidence(SOURCE, [])
    interpretation = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id="E-001",
                    kind="requirement",
                    sections=["functional"],
                    explanation="The source permits both manual operations.",
                )
            ]
        }
    )
    row = requirement(SOURCE, "E-001") | {"id": "FR-001"}
    row["acceptance_criteria"][0]["when"] = (
        "The administrator manually isolates the device and then manually restores its access"
    )
    row["acceptance_criteria"][0]["then"] = (
        "The device is isolated and access is restored within the defined isolation period"
    )
    issues = validate_section(
        "functional", {"requirements": [row]}, evidence, interpretation, [], {}
    )
    assert "FR-001:unconfirmed_waiting_period_condition" in issues
    row["acceptance_criteria"][0]["then"] = "The device is isolated and its access is then restored"
    assert (
        validate_section("functional", {"requirements": [row]}, evidence, interpretation, [], {})
        == []
    )

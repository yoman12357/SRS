"""A successful forbidden-change event is not evidence that automation was prohibited."""

import re
import threading
import time

import pytest

from cybersrs.evidence import build_evidence
from cybersrs.prohibition_verification import (
    prohibited_action_gaps,
    prohibition_gap_action,
    prohibition_test_contract,
    prohibition_test_gaps,
)
from cybersrs.provider import generation_schema
from cybersrs.requirement_repair import complete_source_gaps
from cybersrs.schemas import AcceptanceTestRepair, EvidenceAssessment
from cybersrs.validation import validate_section

from .conftest import requirement
from .test_requirement_repair import ArtifactProvider, target_analysis

SOURCE = "Do not automatically change firewall rules or isolate devices."
GOOD = {
    "given": "A sandbox contains recorded initial firewall and device connectivity state",
    "when": "The test harness attempts automatic firewall rule changes and device isolation",
    "then": "The firewall configuration and device connectivity state remain unchanged",
    "method": "test",
    "observable_evidence": "Compare captured before and after configuration and connectivity state",
}


def test_aggregate_failure_is_split_into_actual_uncovered_actions():
    """Reproduce the latest model's generic WHEN even though GIVEN names an attempted action."""
    rejected = GOOD | {
        "given": "An automated system attempts to isolate a device using firewall rules.",
        "when": "The action is executed in an authorized test environment.",
    }
    assert prohibited_action_gaps(SOURCE, [rejected]) == [
        "automatic_prohibition_isolation_not_exercised",
        "automatic_prohibition_modification_not_exercised",
    ]
    firewall = GOOD | {"when": "The harness attempts automatic firewall-rule modification."}
    assert prohibited_action_gaps(SOURCE, [firewall]) == [
        "automatic_prohibition_isolation_not_exercised"
    ]


def test_requested_action_must_exist_in_the_exclusion_source():
    """Neither a gap name nor a positive permission can manufacture a prohibition."""
    gap = "automatic_prohibition_isolation_not_exercised"
    assert prohibition_gap_action(SOURCE, gap) == "isolation"
    assert prohibition_gap_action("Administrators may manually isolate devices.", gap) is None
    assert prohibition_gap_action(SOURCE, "automatic_prohibition_scanning_not_exercised") is None
    assert prohibition_test_contract(SOURCE, "isolation")["actions_to_attempt"] == "isolation"
    with pytest.raises(ValueError, match="prohibition_action_not_in_source"):
        prohibition_test_contract(SOURCE, "scanning")


def test_native_target_cannot_be_satisfied_by_a_generic_action_when():
    """The missing firewall attempt must appear explicitly in the generated trigger."""
    schema = generation_schema(
        AcceptanceTestRepair,
        {
            "source": SOURCE,
            "gap_to_close": "automatic_prohibition_modification_not_exercised",
            "existing_requirements": [{"id": "SEC-001"}],
        },
    )
    pattern = schema["$defs"]["AcceptanceCriterion"]["properties"]["when"]["pattern"]
    assert re.search(pattern, "The harness attempts automatic firewall rule changes.")
    assert not re.search(pattern, "The action is executed in an authorized test environment.")


def test_active_scanning_keeps_its_mode_and_requires_traffic_evidence():
    """An active scan exclusion is not silently narrowed to an automatic-only scan."""
    source = (
        "Automatic firewall reconfiguration and active vulnerability scanning are out of scope."
    )
    firewall = GOOD | {"when": "The harness attempts automatic firewall reconfiguration."}
    scan = GOOD | {
        "when": "The test harness simulates an active vulnerability scan.",
        "then": "No active vulnerability scan traffic is emitted.",
        "observable_evidence": "Compare packet traces before and after the attempted scan.",
    }
    assert prohibition_test_gaps(source, [firewall, scan]) == []
    assert "active scan" in prohibition_test_contract(source, "scanning")["instruction"]
    unrelated = scan | {
        "observable_evidence": "Inspect the unchanged firewall configuration state."
    }
    assert prohibited_action_gaps(source, [firewall, unrelated]) == [
        "automatic_prohibition_scanning_not_exercised"
    ]


def test_each_missing_action_is_repaired_without_reauthoring_the_requirement(analysis):
    """Two bounded requests close two real gaps while preserving every normative field."""
    row = requirement(SOURCE, "E-001") | {"id": "SEC-001"}
    original = dict(row)
    calls = []

    class ActionProvider:
        """Return only the target source action and exercise the production validator."""

        model_name = "test-qwen"

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Reject the actual generic WHEN before returning the specifically requested test."""
            action = context["prohibition_verification"]["actions_to_attempt"]
            calls.append(action)
            trigger = {
                "isolation": "The sandbox attempts automatic device isolation.",
                "modification": "The sandbox attempts automatic firewall-rule modification.",
            }[action]
            bad = schema.model_validate(
                {
                    "requirement_id": "SEC-001",
                    "acceptance_criterion": GOOD
                    | {"given": trigger, "when": "The action is executed in the sandbox."},
                }
            )
            assert validate(bad)
            result = schema.model_validate(
                {"requirement_id": "SEC-001", "acceptance_criterion": GOOD | {"when": trigger}}
            )
            assert validate(result) == []
            return result, {"model": self.model_name, "attempts": 1}

    content, _, attempts = complete_source_gaps(
        ActionProvider(),
        "security",
        {"requirements": [row]},
        {},
        build_evidence(SOURCE, []),
        target_analysis(analysis),
        [],
        {},
        threading.Event(),
        time.monotonic() + 5,
    )
    assert calls == ["isolation", "modification"] and attempts == 2
    actual = content["requirements"][0]
    assert {k: v for k, v in actual.items() if k != "acceptance_criteria"} == {
        k: v for k, v in original.items() if k != "acceptance_criteria"
    }
    assert row == original
    assert len(actual["acceptance_criteria"]) == 2
    assert prohibition_test_gaps(SOURCE, actual["acceptance_criteria"]) == []


def test_change_event_log_does_not_verify_the_absence_of_a_change() -> None:
    """Require an explicit automation attempt and an observed unchanged-state comparison."""
    bad = GOOD | {
        "observable_evidence": "A log entry indicating a firewall change or isolation event"
    }
    assert prohibition_test_gaps(SOURCE, [bad])
    assert prohibition_test_gaps(SOURCE, [GOOD]) == []
    assert prohibition_test_gaps("Administrators may manually isolate devices.", [bad]) == []


def test_state_comparison_may_be_explicit_in_the_observable_outcome() -> None:
    """Recognize complete test semantics across fields instead of enforcing one wording."""
    criterion = GOOD | {
        "when": "An automated rule update and device isolation are attempted in the sandbox",
        "then": "Configuration and connectivity state are identical before and after the attempt",
        "observable_evidence": "Inspect the resulting firewall configuration "
        "and connectivity state",
    }
    assert prohibition_test_gaps(SOURCE, [criterion]) == []


def test_separate_action_attempts_together_cover_the_prohibition():
    """Two complete tests need not combine independent forbidden actions into one trigger."""
    firewall = GOOD | {"when": "The sandbox attempts automatic firewall rule changes"}
    isolation = GOOD | {"when": "The sandbox attempts automatic device isolation"}
    assert prohibition_test_gaps(SOURCE, [firewall])
    assert prohibition_test_gaps(SOURCE, [isolation])
    assert prohibition_test_gaps(SOURCE, [firewall, isolation]) == []


def test_repair_keeps_a_valid_partial_test_when_adding_the_missing_action(analysis):
    """Completing isolation retains the already verified firewall test and exact source."""
    firewall = GOOD | {"when": "The sandbox attempts automatic firewall rule changes"}
    isolation = GOOD | {"when": "The sandbox attempts automatic device isolation"}
    row = requirement(SOURCE, "E-001") | {"id": "SEC-001"}
    bad = row["acceptance_criteria"][0]
    row["acceptance_criteria"] = [firewall, bad]
    provider = ArtifactProvider(
        AcceptanceTestRepair,
        {
            "requirement_id": row["id"],
            "acceptance_criterion": isolation,
        },
    )
    fixed, _, attempts = complete_source_gaps(
        provider,
        "security",
        {"requirements": [row]},
        {},
        build_evidence(SOURCE, []),
        target_analysis(analysis),
        [],
        {},
        threading.Event(),
        time.monotonic() + 5,
    )
    assert attempts == 1
    assert fixed["requirements"][0]["acceptance_criteria"] == [firewall, isolation]
    assert fixed["requirements"][0]["statement"] == SOURCE


def test_repair_replaces_misleading_prohibition_tests_with_model_authored_evidence(
    analysis,
) -> None:
    """Keep the exact statement and valid metadata while replacing rejected test content."""
    interpretation = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id="E-001",
                    kind="exclusion",
                    sections=["security"],
                    explanation="Automatic infrastructure changes are excluded.",
                )
            ]
        }
    )
    row = requirement(SOURCE, "E-001") | {"id": "SEC-001"}
    original_tests = list(row["acceptance_criteria"])
    provider = ArtifactProvider(
        AcceptanceTestRepair,
        {
            "requirement_id": "SEC-001",
            "acceptance_criterion": GOOD,
        },
    )
    fixed, _, _ = complete_source_gaps(
        provider,
        "security",
        {"requirements": [row]},
        {},
        build_evidence(SOURCE, []),
        interpretation,
        [],
        {},
        threading.Event(),
        time.monotonic() + 5,
    )
    assert fixed["requirements"][0]["statement"] == SOURCE
    assert fixed["requirements"][0]["acceptance_criteria"] == [GOOD]
    assert row["acceptance_criteria"] == original_tests
    assert (
        validate_section("security", fixed, build_evidence(SOURCE, []), interpretation, [], {})
        == []
    )

"""Exact-brief regressions for the two supplied backup and configuration examples."""

import json
import threading
import time
from pathlib import Path

import pytest

from cybersrs.atomic_requirements import generate_atomic_requirements
from cybersrs.evidence import build_evidence
from cybersrs.schemas import Evidence
from cybersrs.source_detail_policy import unsupported_source_details
from cybersrs.source_obligations import criterion_target_issues, source_obligations

from .test_atomic_source_generation import SourceCriterionProvider
from .test_semantic_source_cases import case_analysis

CASES = json.loads(
    (Path(__file__).parent / "fixtures/backup_configuration_cases.json").read_text(encoding="utf-8")
)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["key"])
def test_real_backup_configuration_briefs_keep_actions_and_subjects(case, analysis):
    """Do not create It as an actor or turn restore-activity records into restore commands."""
    evidence, interpreted = case_analysis(case, analysis)
    units = [u for e in evidence for u in source_obligations(e)]
    statements = [u.statement for u in units]
    assert not any("allow It" in s for s in statements)
    assert not any(u.action == "restore" and "activities" in u.statement for u in units)
    required = (
        [
            "define backup policies",
            "initiate backup jobs",
            "monitor backup jobs",
            "restore approved data",
            "review backup status",
            "maintain audit logs of backup and restore activities",
        ]
        if case["key"] == "backup"
        else [
            "review current configurations",
            "submit configuration changes",
            "track change history",
            "restore previously approved configurations when necessary",
        ]
    )
    for phrase in required:
        assert any(phrase in s for s in statements), phrase
    previous = {}
    for name in ("functional", "nonfunctional"):
        content, provenance = generate_atomic_requirements(
            SourceCriterionProvider(),
            name,
            evidence,
            interpreted,
            [],
            previous,
            threading.Event(),
            time.monotonic() + 10,
            max_test_repairs=0,
        )
        previous[name] = content
        assert not provenance["repaired_test_keys"]


@pytest.mark.parametrize(
    "body",
    [
        "It should maintain audit logs of backup and restore activities.",
        "The platform should inspect audit records and log files.",
        "The system should review backup and restore operations.",
    ],
)
def test_nominal_log_and_restore_phrases_remain_one_duty(body):
    """Protect recognized noun compounds without dropping the original scope."""
    units = source_obligations(Evidence(id="E-001", source="description", quote=body))
    assert len(units) == 1
    assert "allow It" not in units[0].statement
    assert units[0].quote == body


def test_real_restore_operation_after_audit_duty_stays_separate():
    """Noun protection must not hide a real actor-permitted restore action."""
    evidence = build_evidence(
        "The system should maintain audit logs and restore approved data.", []
    )
    assert [u.action for u in source_obligations(evidence[0])] == ["maintain", "restore"]


@pytest.mark.parametrize(
    "result",
    [
        "the object's resulting policy, job, submitted change, or history is observed as updated",
        "The object's resulting state is observed as valid.",
    ],
)
def test_copied_alternative_object_template_is_not_an_acceptance_result(result):
    """Reproduce the actual completed-but-vague configuration tests seen in inspection."""
    source = build_evidence("Administrators should submit configuration changes.", [])[0]
    unit = source_obligations(source)[0]
    criterion = {
        "given": "An authorized administrator with a configuration fixture",
        "then": result,
        "when": "An administrator submits a configuration change",
    }
    assert "criterion_must_name_actual_source_object_not_template" in criterion_target_issues(
        unit, criterion
    )


@pytest.mark.parametrize(
    "result,code",
    [
        ("The policy is recorded in the system's policy registry.", "registry_implementation"),
        ("The job is recorded in the system's job history.", "registry_implementation"),
        ("An authenticated session is persisted across operations.", "session_persistence"),
        ("The system records the action and all associated metadata.", "unbounded_metadata"),
    ],
)
def test_unconfirmed_registry_metadata_and_session_guarantees_are_not_source_facts(result, code):
    """Reject the observed unsupported details; allow each when explicitly source-defined."""
    evidence = build_evidence("The system should integrate with university identity services.", [])
    assert code in unsupported_source_details(result, evidence)
    assert code not in unsupported_source_details(result, build_evidence(result, []))


def test_dashboard_test_must_observe_the_display_not_only_start_it():
    """An instrumentation response cannot substitute for actually presenting a dashboard."""
    unit = source_obligations(build_evidence("The system should provide a dashboard.", [])[0])[0]
    criterion = {
        "given": "A controlled dashboard fixture with configuration data",
        "then": "The system initiates the display and a test capture records a response.",
        "when": "A user opens the dashboard",
    }
    assert "criterion_must_observe_result_not_display_initiation" in criterion_target_issues(
        unit, criterion
    )
    assert not criterion_target_issues(unit, criterion | {"then": "The dashboard is displayed."})


@pytest.mark.parametrize(
    "result",
    [
        "The centralized dashboard displays network configuration data upon system initiation",
        "Upon system initiation, the centralized dashboard displays network configuration data.",
        "The dashboard is available after the user initiates the view request.",
    ],
)
def test_display_result_is_not_confused_with_its_initiation_condition(result):
    """Replay the false rejection while retaining initiation-only checks."""
    unit = source_obligations(build_evidence("The system should provide a dashboard.", [])[0])[0]
    assert not criterion_target_issues(
        unit,
        {
            "given": "A controlled dashboard fixture with configuration data",
            "when": "A user opens the dashboard",
            "then": result,
        },
    )

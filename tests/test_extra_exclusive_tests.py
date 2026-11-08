"""Unsupported extra tests cannot erase a valid model-authored source capability."""

import copy
import threading
import time

from cybersrs.acceptance_grounding import preserve_nonexclusive_tests
from cybersrs.audit import audit_scope
from cybersrs.evidence import build_evidence
from cybersrs.repository import Repository
from cybersrs.requirement_repair import complete_source_gaps
from cybersrs.schemas import Requirement
from cybersrs.validation import validate_section

from .conftest import requirement
from .test_permission_verification import criterion
from .test_requirement_repair import ArtifactProvider, target_analysis

SOURCE = (
    "Administrators manage remote-access permissions; support operators may inspect "
    "connection logs but cannot grant permissions."
)


def candidate() -> dict:
    """Reproduce the positive capability plus the unsupported exclusive denial test."""
    row = requirement(
        "The system shall permit administrators to manage remote-access permissions.", "E-001"
    )
    row["acceptance_criteria"] = [
        criterion(
            "An administrator is present",
            "The administrator manages permissions",
            "The permitted permission change succeeds",
        ),
        criterion(
            "A support operator is present",
            "The operator manages permissions",
            "The request is denied because only administrators may manage permissions",
        ),
    ]
    return row


def test_rejected_extra_is_audited_and_positive_test_is_preserved(settings) -> None:
    """Keep valid tests unchanged and retain rejected assertions as private audit evidence."""
    repo = Repository(settings.data_dir)
    project = repo.create_project("Synthetic source-bound repair", SOURCE)
    original = candidate()
    with audit_scope(repo, project["id"]):
        normalized = preserve_nonexclusive_tests(original, build_evidence(SOURCE, []))
    assert original == candidate()
    assert normalized["statement"] == original["statement"]
    assert normalized["acceptance_criteria"] == original["acceptance_criteria"][:1]
    rejected = [
        event
        for event in repo.list_audit(project["id"])
        if event["kind"] == "acceptance_criterion_rejected"
    ]
    assert len(rejected) == 1
    assert rejected[0]["payload"]["criterion"] == original["acceptance_criteria"][1]


def test_bad_statement_or_all_bad_tests_still_require_model_repair() -> None:
    """Filtering cannot excuse an unsupported normative restriction or produce a testless row."""
    original = candidate()
    original["statement"] = "Only administrators may manage permissions."
    assert preserve_nonexclusive_tests(original, build_evidence(SOURCE, [])) == original
    original = candidate()
    original["acceptance_criteria"] = original["acceptance_criteria"][1:]
    assert preserve_nonexclusive_tests(original, build_evidence(SOURCE, [])) == original


def test_source_explicit_exclusivity_keeps_the_authored_test() -> None:
    """Do not remove a negative boundary that actually belongs to the stakeholder source."""
    source = "Only administrators may manage permissions."
    original = candidate()
    assert preserve_nonexclusive_tests(original, build_evidence(source, [])) == original


def test_management_completion_preserves_existing_operator_tests_and_full_coverage(
    analysis,
) -> None:
    """Reproduce the real completion failure and revalidate the complete compound source."""
    existing = requirement(
        "Support operators may inspect logs but cannot grant permissions.", "E-001"
    )
    existing["id"] = "SEC-001"
    existing["acceptance_criteria"] = [
        criterion(
            "A support operator is present",
            "The operator inspects connection logs",
            "Logs are displayed",
        ),
        criterion(
            "A support operator is present",
            "The operator grants permissions",
            "The grant is denied",
        ),
    ]
    preserved = copy.deepcopy(existing)
    provider = ArtifactProvider(Requirement, candidate())
    evidence = build_evidence(SOURCE, [])
    interpretation = target_analysis(analysis)
    fixed, _, _ = complete_source_gaps(
        provider,
        "security",
        {"requirements": [existing]},
        {},
        evidence,
        interpretation,
        [],
        {},
        threading.Event(),
        time.monotonic() + 5,
    )
    assert fixed["requirements"][0] == preserved
    assert fixed["requirements"][1]["acceptance_criteria"] == candidate()["acceptance_criteria"][:1]
    assert validate_section("security", fixed, evidence, interpretation, [], {}) == []

"""Verification must retain every authored criterion without new product behavior."""

import copy
import threading
import time

import pytest
from pydantic import ValidationError

from cybersrs.evidence import build_evidence
from cybersrs.orchestrator import Orchestrator
from cybersrs.provider import generation_schema
from cybersrs.repository import Repository
from cybersrs.schemas import VerificationPlan, VerificationSection
from cybersrs.validation import assign_ids, validate_document
from cybersrs.verification_agent import generate_verification
from cybersrs.verification_projection import (
    VERIFICATION_PROJECTION_VERSION,
    compose_verification,
    criterion_inventory,
    validate_verification_choices,
    verification_projection_issues,
)

from .conftest import DESCRIPTION, FakeKnowledge, FakeProvider, wait_run


def _sections(sections: dict) -> dict:
    """Assign canonical IDs through the production helper before creating linked views."""
    return {name: assign_ids(name, copy.deepcopy(value)) for name, value in sections.items()}


def _plan(inventory: list[dict]) -> VerificationPlan:
    """Select permitted synthetic classifications, independently of projection code."""
    return VerificationPlan.model_validate(
        {
            "choices": [
                {"criterion_key": item["key"], "test_type": item["allowed_test_types"][0]}
                for item in inventory
            ]
        }
    )


def test_every_canonical_and_linked_criterion_retains_exact_text(sections):
    """Do not combine distinct checks or silently lose a category's supplementary criterion."""
    original = _sections(sections)
    row = original["functional"]["requirements"][0]
    linked = copy.deepcopy(row["acceptance_criteria"][0])
    linked["then"] = "The selected alert details are returned to the operator."
    original["network"]["related_acceptance_criteria"] = [
        {"requirement_id": row["id"], "acceptance_criteria": [linked]}
    ]
    before = copy.deepcopy(original)
    inventory = criterion_inventory(original)
    plan = _plan(inventory)
    plan.choices.reverse()
    content = compose_verification(plan, inventory)
    assert len(content["tests"]) == 3
    assert original == before
    assert len({item["key"] for item in inventory}) == 3
    for item, test in zip(inventory, content["tests"], strict=True):
        criterion = item["criterion"]
        assert test["procedure"] == ["Given: " + criterion["given"], "When: " + criterion["when"]]
        assert test["expected_result"] == "Expected: " + criterion["then"]
        assert test["evidence_to_record"] == "Evidence: " + criterion["observable_evidence"]
        assert test["requirement_ids"] == [item["requirement_id"]]
    assert verification_projection_issues(content, original) == []


@pytest.mark.parametrize("defect", ["missing", "duplicate", "unknown", "method"])
def test_invalid_model_selections_cannot_remove_or_rewrite_a_criterion(sections, defect):
    """Post-parse validation stays mandatory even if a native decoder ignores constraints."""
    inventory = criterion_inventory(_sections(sections))
    plan = _plan(inventory)
    if defect == "missing":
        plan.choices.pop()
    elif defect == "duplicate":
        plan.choices.append(plan.choices[0].model_copy())
    elif defect == "unknown":
        plan.choices[0].criterion_key = "unknown/criterion"
    else:
        plan.choices[0].test_type = "analysis"
    assert validate_verification_choices(plan, inventory)
    with pytest.raises(ValueError):
        compose_verification(plan, inventory)


def test_native_choices_cover_actual_inventory_and_preserve_inspection_method(sections):
    """Actual criterion count replaces quotas; source-authored inspection stays inspection."""
    preceding = _sections(sections)
    preceding["functional"]["requirements"][0]["acceptance_criteria"][0]["method"] = "inspection"
    inventory = criterion_inventory(preceding)
    schema = generation_schema(VerificationPlan, {"criterion_inventory": inventory})
    choices = schema["properties"]["choices"]
    assert choices["minItems"] == choices["maxItems"] == len(inventory)
    cases = choices["items"]["anyOf"]
    assert cases[0]["properties"]["criterion_key"]["const"] == inventory[0]["key"]
    assert cases[0]["properties"]["test_type"]["enum"] == ["inspection"]
    assert not compose_verification(_plan([]), [])["tests"]


def test_exclusion_without_a_quantified_limit_is_a_negative_test(sections):
    """The actual trained model labelled no automatic change as boundary; reject that label."""
    preceding = _sections(sections)
    preceding["functional"]["requirements"][0]["statement"] = (
        "The system shall not automatically modify firewall rules."
    )
    criterion = preceding["functional"]["requirements"][0]["acceptance_criteria"][0]
    criterion["when"] = "The harness attempts automatic firewall-rule modification."
    criterion["then"] = "The configuration and connectivity state remain unchanged."
    inventory = criterion_inventory(preceding)
    assert inventory[0]["allowed_test_types"] == ["negative"]
    plan = _plan(inventory)
    plan.choices[0].test_type = "boundary"
    assert "verification:criterion_method_changed" in validate_verification_choices(plan, inventory)


def test_positive_action_and_a_real_quantified_edge_stay_distinct(sections):
    """Unchanged policy does not negate successful acknowledgement; expiry can be a boundary."""
    preceding = _sections(sections)
    criterion = preceding["functional"]["requirements"][0]["acceptance_criteria"][0]
    criterion["then"] = "The alert is successfully acknowledged while policy remains unchanged."
    assert criterion_inventory(preceding)[0]["allowed_test_types"] == ["positive"]
    criterion["then"] = (
        "The system shall deny access and prevent any session establishment to the staff network."
    )
    assert criterion_inventory(preceding)[0]["allowed_test_types"] == ["negative"]
    criterion["given"] = "A record with a known creation time is retained for 14 days."
    criterion["when"] = "A controlled test clock advances beyond the 14-day expiry."
    criterion["then"] = "The expired record is removed from storage."
    assert "boundary" in criterion_inventory(preceding)[0]["allowed_test_types"]


@pytest.mark.parametrize("change", ["expected_result", "canonical_criterion", "omit_test"])
def test_current_quality_detects_changes_to_a_claimed_automatic_view(complete_document, change):
    """A stored policy tag is checked against actual content on reads and exports."""
    document = complete_document.model_copy(deep=True)
    inventory = criterion_inventory(document.model_dump())
    document.verification = VerificationSection.model_validate(
        assign_ids("verification", compose_verification(_plan(inventory), inventory))
    )
    document.verification_projection_version = VERIFICATION_PROJECTION_VERSION
    assert validate_document(document).status == "needs_review"
    if change == "expected_result":
        document.verification.tests[0].expected_result = "A different outcome is now expected."
    elif change == "canonical_criterion":
        document.functional.requirements[0].acceptance_criteria[0].then += " The view has changed."
    else:
        document.verification.tests.pop()
    report = validate_document(document)
    assert report.status == "invalid"
    assert any(f.code == "verification:canonical_projection_mismatch" for f in report.findings)


def test_real_agent_classifies_then_validates_the_complete_view(sections, analysis):
    """The model cannot return an invented procedure in place of its constrained choices."""
    preceding = _sections(sections)
    inventory = criterion_inventory(preceding)

    class ClassificationProvider:
        """Exercise the production callback, not a canned public verification section."""

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Reject omitted keys before returning every synthetic classification."""
            assert schema.__name__ == "CanonicalVerificationTypes"
            assert context["criterion_inventory"] == inventory
            assert set(schema.model_json_schema()["required"]) == {
                item["key"] for item in inventory
            }
            with pytest.raises(ValidationError):
                schema.model_validate({})
            result = schema.model_validate(
                {item["key"]: item["allowed_test_types"][0] for item in inventory}
            )
            with pytest.raises(ValidationError):
                schema.model_validate(result.model_dump() | {"unknown/criterion": "positive"})
            assert validate(result) == []
            return result, {"model": "test-qwen", "attempts": 1}

    content, provenance = generate_verification(
        ClassificationProvider(),
        {},
        build_evidence(DESCRIPTION, []),
        analysis,
        [],
        preceding,
        threading.Event(),
        time.monotonic() + 5,
    )
    assert all(test["id"].startswith("TEST-") for test in content["tests"])
    assert verification_projection_issues(content, preceding) == []
    assert provenance["verification_projection_version"] == VERIFICATION_PROJECTION_VERSION


def test_legacy_checkpoint_retry_refreshes_only_verification_and_sdlc(settings, analysis, sections):
    """A projection update cannot quietly redraft canonical requirements or earlier views."""
    repo = Repository(settings.data_dir)
    project = repo.create_project("Synthetic projection retry", DESCRIPTION)
    repo.update_project(project["id"], analysis=analysis.model_dump())
    provider = FakeProvider(analysis, sections)
    coordinator = Orchestrator(settings, repo, provider, FakeKnowledge())
    try:
        original = wait_run(repo, coordinator.start(project["id"])["id"])
        assert original["status"] == "completed", original["error"]
        legacy = original["checkpoints"]["_provenance"] | {"verification_projection_version": ""}
        repo.update_run(original["id"], status="failed", checkpoint=("_provenance", legacy))
        before = len(provider.calls)
        retried = wait_run(repo, coordinator.retry(original["id"])["id"])
        assert retried["status"] == "completed", retried["error"]
        assert provider.calls[before:] == ["verification", "sdlc"]
        for name in ("introduction", "functional", "security", "architecture", "scenarios"):
            assert retried["checkpoints"][name] == original["checkpoints"][name]
        version = repo.get_version(project["id"], repo.list_versions(project["id"])[0]["id"])
        assert (
            version["content"]["verification_projection_version"] == VERIFICATION_PROJECTION_VERSION
        )
        assert repo.list_reviews(project["id"], version["id"]) == []
        before = len(provider.calls)
        repo.update_run(retried["id"], status="failed")
        reused = wait_run(repo, coordinator.retry(retried["id"])["id"])
        assert reused["status"] == "completed", reused["error"]
        assert provider.calls[before:] == []
        latest = repo.get_version(project["id"], repo.list_versions(project["id"])[0]["id"])
        assert (
            latest["content"]["verification_projection_version"] == VERIFICATION_PROJECTION_VERSION
        )
    finally:
        coordinator.shutdown()


def test_reviewed_verification_edit_does_not_claim_model_projection(settings, analysis, sections):
    """An explicit edited view remains an immutable, unapproved revision with honest provenance."""
    repo = Repository(settings.data_dir)
    project = repo.create_project("Synthetic projection edit", DESCRIPTION)
    repo.update_project(project["id"], analysis=analysis.model_dump())
    provider = FakeProvider(analysis, sections)
    coordinator = Orchestrator(settings, repo, provider, FakeKnowledge())
    try:
        original = wait_run(repo, coordinator.start(project["id"])["id"])
        assert original["status"] == "completed", original["error"]
        parent = repo.get_version(project["id"], repo.list_versions(project["id"])[0]["id"])
        run = coordinator.start(
            project["id"],
            "edit",
            version_id=parent["id"],
            section="verification",
            edited_content=parent["content"]["verification"],
            edit_actor="assistant",
        )
        edited = wait_run(repo, run["id"])
        assert edited["status"] == "completed", edited["error"]
        latest = repo.get_version(project["id"], repo.list_versions(project["id"])[0]["id"])
        assert latest["content"]["verification_projection_version"] == ""
        assert (
            repo.get_version(project["id"], parent["id"])["content_hash"] == parent["content_hash"]
        )
        assert repo.list_reviews(project["id"], latest["id"]) == []
    finally:
        coordinator.shutdown()

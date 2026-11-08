"""A misbound source group must be repaired without reauthoring valid neighboring evidence."""

import threading
import time

import pytest
from pydantic import ValidationError

from cybersrs.compact_requirements import generate_compact_requirements
from cybersrs.evidence import build_evidence
from cybersrs.provider import GenerationError
from cybersrs.schemas import EvidenceAssessment
from cybersrs.semantics import project_request_recast_as_runtime_behavior


@pytest.mark.parametrize("verb", ["Design", "Build", "Develop", "Create"])
def test_request_verb_is_not_a_runtime_function(verb: str) -> None:
    """Project design verbs do not become a product that designs itself."""
    source = f"{verb} a firewall management system that manages university firewall policies."
    assert project_request_recast_as_runtime_behavior(
        source, f"The system shall {verb.lower()} a firewall management system."
    )
    assert not project_request_recast_as_runtime_behavior(
        source, "The system shall manage university firewall policies."
    )


def test_explicit_design_tool_behavior_is_retained() -> None:
    """A requested design tool can legitimately design objects specified in its behavior."""
    assert not project_request_recast_as_runtime_behavior(
        "Design a platform that designs network layouts.",
        "The system shall design network layouts.",
    )


@pytest.mark.parametrize("prefix", ["The system shall design", "Design"])
def test_request_verb_rejection_uses_bounded_source_group_repair(analysis, prefix) -> None:
    """Run the full public validator and correction path for an otherwise complete purpose."""
    source = "Design a firewall management system that manages university firewall policies."
    evidence = build_evidence(source, [])
    target = analysis.model_copy(update={"assessments": [EvidenceAssessment(
        evidence_id="E-001", kind="requirement", sections=["functional"],
        explanation="The requested product manages firewall policies.",
    )]})
    criterion = {
        "given": "A test administrator and a firewall policy are present",
        "when": "The administrator manages the firewall policy",
        "then": "The requested firewall policy management operation succeeds",
        "method": "test", "observable_evidence": "Test capture of the firewall policy state",
    }
    original = {"statement": f"{prefix} a firewall management system that "
                             "manages university firewall policies.",
                "tests": [criterion], "unresolved_decisions": []}
    corrected = {**original, "statement": "The system shall manage university firewall policies."}

    class Provider:
        """Return a saved design-request defect and a genuine authored replacement."""

        model_name = "test-adapter"

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Require the public error and verify the replacement through the same gates."""
            if "tests_to_repair" not in context:
                candidate = schema.model_validate({"E-001": original})
                expected = "FR-001:" + (
                    "project_request_recast_as_runtime_behavior"
                    if prefix.startswith("The system") else "missing_normative_behavior"
                )
                assert expected in validate(candidate)
                raise GenerationError(
                    "section_validation_failed:request_verb",
                    rejected_candidate=candidate.model_dump(), rejected_model="test-base",
                    attempts=2,
                )
            assert set(context["tests_to_repair"]) == {"E-001_source"}
            with pytest.raises(ValidationError):
                schema.model_validate({"E-001_source": {**corrected, "statement": source}})
            candidate = schema.model_validate({"E-001_source": corrected})
            assert not validate(candidate)
            return candidate, {"model": "test-base", "attempts": 1}

    result, provenance = generate_compact_requirements(
        Provider(), "functional", evidence, target, [], {}, threading.Event(), time.monotonic() + 5
    )
    assert result["requirements"][0]["statement"] == corrected["statement"]
    assert provenance["repaired_source_ids"] == ["E-001"]


def test_missing_behavior_repairs_only_its_source_and_rechecks_all_gates(analysis) -> None:
    """Keep good rows frozen, reject a still-missing action, then accept model-authored repair."""
    evidence = build_evidence(
        "Network administrators manage firewall policies. Security operators review alerts.", []
    )
    target = analysis.model_copy(update={"assessments": [
        row.model_copy(update={"sections": ["functional"]}) for row in analysis.assessments
    ]})
    criterion = {
        "given": "An authorized test role and an existing policy are present",
        "when": "The test role requests the policy status",
        "then": "The requested policy status is returned",
        "method": "test",
        "observable_evidence": "Test capture of the policy response",
    }
    wrong = {"statement": "The system shall return policy status.",
             "tests": [criterion], "unresolved_decisions": []}
    good = {
        "statement": "The system shall allow security operators to review alerts.",
        "tests": [{**criterion, "given": "A security operator and a test alert are present",
                   "when": "The security operator requests alert review",
                   "then": "The requested alert is returned to the security operator"}],
        "unresolved_decisions": [],
    }
    fixed = {
        "statement": "The system shall allow network administrators to manage firewall policies.",
        "tests": [{**criterion, "given": "A network administrator and a policy are present",
                   "when": "The network administrator manages the firewall policy",
                   "then": "The requested firewall policy management action succeeds"}],
        "unresolved_decisions": [],
    }

    class Provider:
        """Exercise the exact rejected-candidate route without live inference."""

        model_name = "test-adapter"

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Check the patch schema cannot reauthor the valid neighboring source."""
            if "tests_to_repair" not in context:
                candidate = schema.model_validate({"E-001": wrong, "E-002": good})
                assert "E-001:missing_functional_behavior_management" in validate(candidate)
                raise GenerationError(
                    "section_validation_failed:source_group",
                    rejected_candidate=candidate.model_dump(), rejected_model="test-base",
                    attempts=2,
                )
            assert set(context["tests_to_repair"]) == {"E-001_source"}
            patch = context["tests_to_repair"]["E-001_source"]
            assert patch["source"] == evidence[0].quote
            assert patch["task"] == "repair_source_group"
            assert context["_continue_model"] == "test-base"
            with pytest.raises(ValidationError):
                schema.model_validate({"E-001_source": fixed, "E-002_source": good})
            bad = schema.model_validate({"E-001_source": wrong})
            assert "E-001:missing_functional_behavior_management" in validate(bad)
            candidate = schema.model_validate({"E-001_source": fixed})
            assert validate(candidate) == []
            return candidate, {"model": "test-base", "attempts": 1}

    content, provenance = generate_compact_requirements(
        Provider(), "functional", evidence, target, [], {}, threading.Event(), time.monotonic() + 5
    )
    rows = {row["evidence_ids"][0]: row for row in content["requirements"]}
    assert rows["E-001"]["statement"] == fixed["statement"]
    assert rows["E-002"]["statement"] == good["statement"]
    assert rows["E-002"]["acceptance_criteria"] == good["tests"]
    assert provenance["repaired_source_ids"] == ["E-001"]
    assert provenance["attempts"] == 3

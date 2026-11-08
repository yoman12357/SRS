"""Source ownership and narrow repair for the linked-record failure observed live."""

import copy
import threading
import time

import pytest
from pydantic import ValidationError

from cybersrs.evidence import build_evidence
from cybersrs.orchestrator import Orchestrator
from cybersrs.provider import GenerationError, generation_schema
from cybersrs.repository import Repository
from cybersrs.requirement_repair import complete_source_gaps
from cybersrs.schemas import (
    EvidenceAssessment,
    ObservableEvidenceRepair,
    Requirement,
    RequirementsSection,
)

from .conftest import FakeKnowledge, requirement
from .test_requirement_repair import ArtifactProvider


def test_passage_without_matching_canonical_target_cannot_add_linked_tests():
    """An automation exclusion cannot redraft tests for an earlier manual permission."""
    schema = generation_schema(
        RequirementsSection,
        {
            "evidence": [{"id": "E-007", "quote": "Do not automatically isolate devices."}],
            "existing_requirements": [{"id": "FR-002", "title": "Manual isolation"}],
            "related_acceptance_requirement_ids": [],
        },
    )
    assert schema["properties"]["related_acceptance_criteria"]["maxItems"] == 0


def test_linked_target_vocabulary_is_separate_from_dependency_vocabulary():
    """A source-owned test may link its canonical ID without borrowing unrelated sources."""
    schema = generation_schema(
        RequirementsSection,
        {
            "existing_requirements": [{"id": "FR-002"}, {"id": "SEC-001"}],
            "related_acceptance_requirement_ids": ["SEC-001"],
        },
    )
    assert schema["$defs"]["RelatedAcceptanceCriteria"]["properties"]["requirement_id"]["enum"] == [
        "SEC-001"
    ]
    assert schema["$defs"]["Requirement"]["properties"]["dependencies"]["items"]["enum"] == [
        "FR-002",
        "SEC-001",
    ]


def test_invalid_linked_witness_is_repaired_without_replacing_valid_siblings(settings, analysis):
    """The failed row is linked rather than canonical; it still receives a bounded repair."""
    source = "Network administrators may manually isolate a device and restore its access."
    canonical = requirement(source, "E-001") | {"id": "FR-001"}
    valid = canonical["acceptance_criteria"][0]
    restore = valid | {
        "when": "The administrator manually restores the isolated device access",
        "then": "The device network access is restored",
    }
    canonical["acceptance_criteria"] = [valid, restore]
    bad = valid | {"observable_evidence": "Inspect the production device-management log"}
    repaired = valid | {"observable_evidence": "Capture the device connectivity before and after"}
    linked = {
        "requirement_id": "FR-001",
        "title": "Manual device actions",
        "rationale": "Additional source-bound manual isolation evidence.",
        "dimensions": ["security"],
        "evidence_ids": [],
        "sources": [],
        "acceptance_criteria": [restore, bad],
        "unresolved_decisions": [],
    }
    content = {
        "applicability_reason": "Manual device actions reuse their canonical requirement.",
        "requirements": [],
        "related_requirement_ids": ["FR-001"],
        "related_acceptance_criteria": [linked],
    }
    original = copy.deepcopy(content)
    previous = {"functional": {"requirements": [canonical]}}
    original_previous = copy.deepcopy(previous)
    interpretation = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id="E-001",
                    kind="requirement",
                    sections=["functional"],
                    explanation="Manual isolation and restoration are permitted.",
                )
            ]
        }
    )

    class LinkedProvider:
        """Return one model-authored linked-test replacement through real validation."""

        model_name = "test-qwen"

        def __init__(self):
            """Expect exactly one repair request."""
            self.calls = 0

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Assert the canonical source and gate are retained during narrow repair."""
            self.calls += 1
            assert schema is ObservableEvidenceRepair
            assert context["evidence"][0]["quote"] == source
            with pytest.raises(ValidationError):
                schema.model_validate(
                    {
                        "requirement_id": "FR-999",
                        "observable_evidence": repaired["observable_evidence"],
                    }
                )
            candidate = schema.model_validate(
                {"observable_evidence": repaired["observable_evidence"]}
            )
            assert validate(candidate) == []
            return candidate, {"model": self.model_name, "attempts": 1}

    provider = LinkedProvider()
    coordinator = Orchestrator(settings, Repository(settings.data_dir), provider, FakeKnowledge())
    try:
        result, provenance = coordinator._repair_rejected_requirements(
            "functional",
            content,
            {},
            build_evidence(source, []),
            interpretation,
            [],
            previous,
            threading.Event(),
            time.monotonic() + 10,
            "rejected-model",
        )
        assert provider.calls == 1
        assert result.related_acceptance_criteria[0].acceptance_criteria[0].model_dump() == restore
        assert result.related_acceptance_criteria[0].acceptance_criteria[1].model_dump() == repaired
        assert previous == original_previous and content == original
        assert provenance["attempts"] == 1
    finally:
        coordinator.shutdown()


def test_passage_parser_rejects_wrong_source_even_if_provider_ignores_native_schema(
    settings, analysis
):
    """Output constraints are backed by a deterministic gate before checkpoint publication."""
    source = "Network administrators may manually isolate a device and restore its access."
    exclusion = "Do not automatically isolate devices."
    canonical = requirement(source, "E-001") | {"id": "FR-001"}
    record = {
        "requirement_id": "FR-001",
        "title": "Manual isolation",
        "rationale": "An earlier source permits this manual action.",
        "dimensions": ["security"],
        "evidence_ids": ["E-001"],
        "sources": [],
        "acceptance_criteria": canonical["acceptance_criteria"],
        "unresolved_decisions": [],
    }
    interpretation = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id="E-002",
                    kind="exclusion",
                    sections=["functional"],
                    explanation="Exclude automatic isolation.",
                )
            ]
        }
    )

    class UnscopedProvider:
        """Try the observed unrelated linked record through the production callback."""

        model_name = "test-qwen"

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Verify independent source ownership even without a compliant decoder."""
            assert context["related_acceptance_requirement_ids"] == []
            result = schema.model_validate(
                {
                    "applicability_reason": "The current source excludes automatic isolation.",
                    "requirements": [requirement(exclusion, "E-002")],
                    "related_acceptance_criteria": [record],
                }
            )
            assert "passage_linked_acceptance_must_use_its_original_source" in validate(result)
            raise GenerationError("synthetic_wrong_source_rejected")

    repository = Repository(settings.data_dir)
    project = repository.create_project("Source ownership fixture", source + " " + exclusion)
    run = repository.create_run(project["id"], "generate", "synthetic-input")
    coordinator = Orchestrator(settings, repository, UnscopedProvider(), FakeKnowledge())
    try:
        with pytest.raises(GenerationError, match="synthetic_wrong_source_rejected"):
            coordinator._generate_requirement_passages(
                run["id"],
                "functional",
                {},
                build_evidence(source + " " + exclusion, []),
                interpretation,
                [],
                {"functional": {"requirements": [canonical]}},
                {},
                threading.Event(),
                time.monotonic() + 10,
            )
        assert (
            repository.get_run(run["id"])["checkpoints"]["_partial_functional"]["requirements"]
            == []
        )
    finally:
        coordinator.shutdown()


def test_missing_named_capabilities_get_additional_rows_without_erasing_existing_behavior(analysis):
    """Complete firewall/monitoring omissions rather than rewriting valid segmentation."""
    source = "Provide a firewall and network monitoring system with separate campus networks."
    first = requirement("The system shall maintain separate campus networks.", "E-001")
    first["id"] = "FR-001"
    added = requirement(
        "The system shall provide firewall protection and network monitoring.", "E-001"
    )
    provider = ArtifactProvider(Requirement, added)
    interpretation = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id="E-001",
                    kind="requirement",
                    sections=["functional"],
                    explanation="Firewall, monitoring and network separation are requested.",
                )
            ]
        }
    )
    content = {"requirements": [first]}
    before = copy.deepcopy(content)
    fixed, _, attempts = complete_source_gaps(
        provider,
        "functional",
        content,
        {},
        build_evidence(source, []),
        interpretation,
        [],
        {},
        threading.Event(),
        time.monotonic() + 10,
    )
    assert attempts == 1 and content == before
    assert fixed["requirements"][0] == first
    assert len(fixed["requirements"]) == 2

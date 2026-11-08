"""A witness-only patch must retain source behavior and not hide known temporal defects."""

import copy
import threading
import time

import pytest

from cybersrs.artifact_grounding import lifecycle_criterion_issues
from cybersrs.evidence import build_evidence
from cybersrs.orchestrator import Orchestrator
from cybersrs.provider import GenerationError
from cybersrs.repository import Repository
from cybersrs.requirement_repair import complete_source_gaps
from cybersrs.schemas import (
    EvidenceAssessment,
    ObservableEvidenceRepair,
    Requirement,
    RequirementsSection,
)

from .conftest import FakeKnowledge, requirement
from .test_permission_verification import criterion


@pytest.mark.parametrize("through_passage", [False, True])
def test_uninterrupted_witness_repair_preserves_all_other_authored_fields(
    settings, analysis, through_passage
):
    """Reproduce the real unsupported promise without reauthoring its action or valid denial."""
    source = (
        "Students and guests may access the internet but must not access the "
        "internal staff network."
    )
    row = requirement(source, "E-001") | {"id": "FR-001"}
    positive = criterion(
        "A student or guest test identity is present",
        "The identity requests internet access",
        "The system grants internet access",
    )
    positive["observable_evidence"] = (
        "Record of successful access without interruption or redirection."
    )
    negative = criterion(
        "A student or guest test identity is present",
        "The identity requests the internal staff network",
        "The system denies staff-network access",
    )
    row["acceptance_criteria"] = [positive, negative]
    before = copy.deepcopy(row)
    interpretation = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id="E-001",
                    kind="requirement",
                    sections=["functional"],
                    explanation="The explicit network permission and denial are source-stated.",
                )
            ]
        }
    )
    witness = "Capture the internet connection response and external test connectivity state."

    class WitnessProvider:
        """Return the sole requested field through the real complete-criterion gate."""

        model_name = "test-qwen"

        def __init__(self):
            """Count exactly one narrow repair request."""
            self.calls = 0

        def generate(self, system, context, schema, cancel, deadline, validate):
            """The same availability promise must remain rejected even as a typed patch."""
            self.calls += 1
            if schema is RequirementsSection:
                result = schema(
                    applicability_reason="The source states this access boundary.",
                    requirements=[row],
                )
                assert any("unconfirmed_uninterrupted_availability" in e for e in validate(result))
                raise GenerationError(
                    "section_validation_failed:unconfirmed_uninterrupted_availability",
                    rejected_candidate=result.model_dump(),
                    rejected_model=self.model_name,
                    attempts=2,
                )
            assert schema is ObservableEvidenceRepair
            assert context["rejected_witness"] == positive["observable_evidence"]
            assert "acceptance_criteria" not in context["existing_requirements"][0]
            assert any(
                "unconfirmed_uninterrupted_availability" in error
                for error in validate(schema(observable_evidence=positive["observable_evidence"]))
            )
            result = schema(observable_evidence=witness)
            assert validate(result) == []
            return result, {"model": self.model_name, "attempts": 1}

    provider = WitnessProvider()
    coordinator = Orchestrator(settings, Repository(settings.data_dir), provider, FakeKnowledge())
    try:
        arguments = (
            "functional",
            {
                "applicability_reason": "The source states this access boundary.",
                "requirements": [row],
            },
            {},
            build_evidence(source, []),
            interpretation,
            [],
            {},
            threading.Event(),
            time.monotonic() + 5,
            "original-model",
        )
        if through_passage:
            project = coordinator.repository.create_project("Passage repair", source)
            run = coordinator.repository.create_run(project["id"], "generate", "fixture")
            content, provenance = coordinator._generate_requirement_passages(
                run["id"],
                "functional",
                {},
                build_evidence(source, []),
                interpretation,
                [],
                {},
                {},
                threading.Event(),
                time.monotonic() + 5,
            )
            repaired = RequirementsSection.model_validate(content)
        else:
            repaired, provenance = coordinator._repair_rejected_requirements(*arguments)
        expected = copy.deepcopy(before)
        expected["acceptance_criteria"][0]["observable_evidence"] = witness
        assert repaired.requirements[0].model_dump() == expected
        assert provider.calls == (2 if through_passage else 1)
        assert provenance["attempts"] == (3 if through_passage else 1)
        assert row == before
    finally:
        coordinator.shutdown()


@pytest.mark.parametrize(
    "trigger,removal,invalid",
    [
        ("A log entry is generated on day 15 after its creation date.", True, True),
        ("Create the fixture log, then advance its controlled clock beyond expiry.", True, False),
        ("Retention processing runs after the existing record expires.", True, False),
        ("A new connection log is generated.", False, False),
    ],
)
def test_record_creation_does_not_stand_in_for_expiring_an_existing_record(
    trigger, removal, invalid
):
    """Retain valid creation/retention setup and actual elapsed-time deletion procedures."""
    source = "The system must retain connection logs for 14 days and remove them after expiry."
    test = {
        "when": trigger,
        "then": "The expired log record is removed from storage."
        if removal
        else "The connection log remains stored during retention.",
    }
    assert bool(lifecycle_criterion_issues(source, test)) is invalid


@pytest.mark.parametrize("known_author", [True, False])
def test_typed_source_completion_can_repair_criteria_with_honest_authorship(analysis, known_author):
    """Recover the witness while counting failed calls and both actual authors."""
    source = (
        "Administrators manage remote-access permissions; support operators may inspect "
        "connection logs but cannot grant permissions."
    )
    existing = requirement(
        "Support operators may inspect connection logs but cannot grant permissions.", "E-001"
    )
    existing["id"] = "SEC-001"
    existing["acceptance_criteria"] = [
        criterion(
            "A support operator is present",
            "The operator inspects connection logs",
            "The logs are displayed",
        ),
        criterion(
            "A support operator is present",
            "The operator grants permissions",
            "The grant is denied",
        ),
    ]
    added = requirement(
        "The system shall permit administrators to manage remote-access permissions.", "E-001"
    )
    added["acceptance_criteria"] = [
        criterion(
            "An administrator test identity and an existing permission are present",
            "The administrator requests a remote-access permission update",
            "The requested permission update succeeds",
        )
    ]
    added["acceptance_criteria"][0]["observable_evidence"] = (
        "Record of the permission update shown by a confirmation message."
    )
    interpretation = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id="E-001",
                    kind="requirement",
                    sections=["security"],
                    explanation="The source defines administrator and support responsibilities.",
                )
            ]
        }
    )
    replacement = "Capture the updated remote-access permission state using test instrumentation."

    class CompletionProvider:
        """Simulate an exhausted typed draft, then permit only an independently checked patch."""

        model_name = "test-primary"

        def __init__(self):
            """Count the scripted boundary calls separately from their simulated attempts."""
            self.calls = 0

        def generate(self, system, context, schema, cancel, deadline, validate):
            """A recovery cannot invent an author or discard the complete validation gate."""
            self.calls += 1
            if schema is Requirement:
                assert all(
                    set(row) == {"id", "statement"} for row in context["existing_requirements"]
                )
                result = schema.model_validate(added)
                assert any(
                    "unconfirmed_product_message_contract" in code for code in validate(result)
                )
                raise GenerationError(
                    "section_validation_failed:unconfirmed_product_message_contract",
                    rejected_candidate=result.model_dump(),
                    rejected_model="normative-model" if known_author else None,
                    attempts=2,
                )
            assert schema is ObservableEvidenceRepair
            result = schema(observable_evidence=replacement)
            assert validate(result) == []
            return result, {"model": "criterion-model", "attempts": 1}

    provider = CompletionProvider()
    arguments = (
        provider,
        "security",
        {"requirements": [existing]},
        {},
        build_evidence(source, []),
        interpretation,
        [],
        {},
        threading.Event(),
        time.monotonic() + 5,
    )
    if not known_author:
        with pytest.raises(GenerationError, match="section_validation_failed"):
            complete_source_gaps(*arguments, repair_tests=False)
        assert provider.calls == 1
        return
    content, models, attempts = complete_source_gaps(*arguments, repair_tests=False)
    assert attempts == 3 and models == {"normative-model", "criterion-model"}
    expected = copy.deepcopy(added) | {"id": "SEC-002"}
    expected["acceptance_criteria"][0]["observable_evidence"] = replacement
    assert content["requirements"] == [existing, expected]

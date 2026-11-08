"""Complete private test gaps before checkpointing or sharing a source passage."""

import threading
import time

from cybersrs.evidence import build_evidence
from cybersrs.orchestrator import Orchestrator
from cybersrs.repository import Repository
from cybersrs.schemas import AcceptanceTestRepair, EvidenceAssessment, RequirementsSection

from .conftest import FakeKnowledge, requirement
from .test_permission_verification import criterion


def test_permission_gap_gets_one_targeted_test_before_the_passage_is_saved(
    settings, analysis
) -> None:
    """Do not repeat whole-requirement generation or publish the deficient intermediate row."""
    source = "Security operators may review and acknowledge alerts but may not change policies."
    interpretation = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id="E-001",
                    kind="requirement",
                    sections=["security"],
                    explanation="Operators can review and acknowledge but cannot edit policies.",
                )
            ]
        }
    )
    row = requirement(source, "E-001")
    row["acceptance_criteria"] = [
        criterion(
            "An operator is present", "The operator reviews an alert", "The alert is displayed"
        ),
        criterion("An operator is present", "The operator edits a policy", "The edit is denied"),
    ]
    added = criterion(
        "An operator has an unacknowledged alert",
        "The operator acknowledges the alert",
        "The alert is visibly marked acknowledged",
    )
    repository = Repository(settings.data_dir)
    project = repository.create_project("Synthetic passage", source)
    run = repository.create_run(project["id"], "generate", "synthetic-hash")

    class TargetedProvider:
        """Assert that complete typed tests are requested before any reusable checkpoint."""

        model_name = "test-qwen"

        def __init__(self):
            """Record the exact generation sequence for this one source passage."""
            self.calls = []

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Exercise production normative and complete-test validators in sequence."""
            self.calls.append(schema.__name__)
            if schema is RequirementsSection:
                result = schema.model_validate(
                    {
                        "applicability_reason": "Explicit operator permission boundary.",
                        "requirements": [row],
                    }
                )
            else:
                assert schema is AcceptanceTestRepair
                assert context["existing_requirements"][0]["id"] == "SEC-001"
                partial = repository.get_run(run["id"])["checkpoints"]["_partial_security"]
                assert partial["requirements"] == []
                result = schema.model_validate(
                    {
                        "requirement_id": "SEC-001",
                        "acceptance_criterion": added,
                    }
                )
            assert validate(result) == []
            return result, {"model": self.model_name, "attempts": 1}

    provider = TargetedProvider()
    coordinator = Orchestrator(settings, repository, provider, FakeKnowledge())
    try:
        result, provenance = coordinator._generate_requirement_passages(
            run["id"],
            "security",
            {"assigned_section": "security"},
            build_evidence(source, []),
            interpretation,
            [],
            {},
            {},
            threading.Event(),
            time.monotonic() + 5,
        )
        assert provider.calls == ["RequirementsSection", "AcceptanceTestRepair"]
        assert len(result["requirements"][0]["acceptance_criteria"]) == 3
        assert provenance["attempts"] == 2
        saved = repository.get_run(run["id"])["checkpoints"]["_partial_security"]
        assert saved["requirements"] == result["requirements"]
    finally:
        coordinator.shutdown()

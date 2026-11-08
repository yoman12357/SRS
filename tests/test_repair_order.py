"""Repair source scope before validating its replacement test artifact."""

import threading
import time

from cybersrs.evidence import build_evidence
from cybersrs.orchestrator import Orchestrator
from cybersrs.repository import Repository
from cybersrs.schemas import AcceptanceTestRepair, EvidenceAssessment, Requirement

from .conftest import FakeKnowledge, requirement
from .test_prohibition_verification import GOOD, SOURCE


def test_normative_scope_is_repaired_before_the_test_artifact(settings, analysis) -> None:
    """A bad statement cannot deadlock an otherwise valid supplementary-test repair."""
    interpretation = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id="E-001",
                    kind="exclusion",
                    sections=["security"],
                    explanation="The prohibition is unconditional.",
                )
            ]
        }
    )
    old = requirement(SOURCE.rstrip(".") + " when an administrator acts manually.", "E-001")
    old["id"] = "SEC-001"
    repaired = requirement(SOURCE, "E-001")

    class OrderedProvider:
        """Require statement repair first and then source-specific test completion."""

        model_name = "test-qwen"

        def __init__(self):
            """Declare the two structured artifacts expected from the production repair."""
            self.calls = []
            self.queue = [
                (Requirement, repaired),
                (AcceptanceTestRepair, {"requirement_id": "SEC-001", "acceptance_criterion": GOOD}),
            ]

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Run each real validation callback against the next scripted model artifact."""
            expected_schema, payload = self.queue.pop(0)
            assert schema is expected_schema
            self.calls.append(schema.__name__)
            result = schema.model_validate(payload)
            assert validate(result) == []
            return result, {"model": self.model_name, "attempts": 1}

    provider = OrderedProvider()
    coordinator = Orchestrator(settings, Repository(settings.data_dir), provider, FakeKnowledge())
    try:
        result, _ = coordinator._repair_rejected_requirements(
            "security",
            {"applicability_reason": "Explicit exclusion", "requirements": [old]},
            {},
            build_evidence(SOURCE, []),
            interpretation,
            [],
            {},
            threading.Event(),
            time.monotonic() + 5,
            "rejected-model",
        )
        assert provider.calls == ["Requirement", "AcceptanceTestRepair"]
        assert result.requirements[0].statement == SOURCE
        assert result.requirements[0].acceptance_criteria[0].model_dump() == GOOD
    finally:
        coordinator.shutdown()

"""Correct repeated regulatory rationale errors without re-authoring valid tests."""

import copy
import threading
import time

import pytest

from cybersrs.evidence import build_evidence
from cybersrs.orchestrator import Orchestrator
from cybersrs.repository import Repository
from cybersrs.schemas import AcceptanceTestRepair, EvidenceAssessment, RequirementRationaleRepair

from .conftest import FakeKnowledge, requirement


@pytest.mark.parametrize("bad_witness", [False, True])
def test_rationale_only_repair_retains_other_fields_and_authored_criteria(
    settings, analysis, bad_witness
):
    """Reproduce the VPN retention failure with two source-stated lifecycle tests."""
    source = "The system must retain connection logs for 14 days and remove them after expiry."
    row = requirement(source, "E-001") | {"id": "DR-001"}
    row["rationale"] = "This data policy ensures compliance with privacy regulations."
    row["acceptance_criteria"] = [
        {
            "given": "A test log has a known creation time",
            "when": "A controlled clock advances through 14 days",
            "then": "The connection log remains stored throughout the 14-day period",
            "method": "test",
            "observable_evidence": "Inspect stored test records during retention",
        },
        {
            "given": "The test log retention has expired",
            "when": "Retention processing runs after expiry",
            "then": "The expired log record is removed from storage",
            "method": "test",
            "observable_evidence": "Compare the stored records before and after removal",
        },
    ]
    good_deletion_test = copy.deepcopy(row["acceptance_criteria"][1])
    if bad_witness:
        row["acceptance_criteria"][1].update(
            when="A log entry is generated on day 15 after its creation date.",
            observable_evidence="Record of deletion event logged by the system.",
        )
    before = copy.deepcopy(row)
    after_test_repair = copy.deepcopy(row)
    after_test_repair["acceptance_criteria"][1] = good_deletion_test
    interpretation = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id="E-001",
                    kind="requirement",
                    sections=["data"],
                    explanation="The record lifecycle is explicitly stated.",
                )
            ]
        }
    )

    class RationaleProvider:
        """Return one rationale patch through the real source gate."""

        model_name = "test-qwen"

        def __init__(self):
            """Reject accidental whole-row or repeated generation."""
            self.calls = 0

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Require the offending candidate and reject a repeated regulation claim."""
            self.calls += 1
            if schema is AcceptanceTestRepair:
                assert bad_witness and self.calls == 1
                assert any(
                    "deletion_test_must_expire_an_existing_record" in code
                    for code in context["validation_feedback"]
                )
                assert context["rejected_criterion"] == before["acceptance_criteria"][1]
                assert context["evidence"][0]["quote"] == source
                wrong = schema.model_validate(
                    {
                        "requirement_id": "DR-001",
                        "acceptance_criterion": before["acceptance_criteria"][1],
                    }
                )
                assert any("production_log_witness" in c for c in validate(wrong))
                result = schema.model_validate(
                    {"requirement_id": "DR-001", "acceptance_criterion": good_deletion_test}
                )
                assert validate(result) == []
                return result, {"model": self.model_name, "attempts": 1}
            assert schema is RequirementRationaleRepair
            assert context["rejected_requirement"] == after_test_repair
            assert any("unconfirmed_regulatory_claim" in c for c in context["validation_feedback"])
            bad = schema.model_validate({"rationale": before["rationale"]})
            assert any("unconfirmed_regulatory_claim" in c for c in validate(bad))
            result = schema.model_validate(
                {"rationale": ("Source-stated logs are retained 14 days and removed after expiry.")}
            )
            assert validate(result) == []
            return result, {"model": self.model_name, "attempts": 1}

    provider = RationaleProvider()
    coordinator = Orchestrator(settings, Repository(settings.data_dir), provider, FakeKnowledge())
    try:
        repaired, provenance = coordinator._repair_rejected_requirements(
            "data",
            {
                "applicability_reason": "The source states the connection-log lifecycle.",
                "requirements": [row],
            },
            {},
            build_evidence(source, []),
            interpretation,
            [],
            {},
            threading.Event(),
            time.monotonic() + 10,
            "original-model",
        )
        actual = repaired.requirements[0].model_dump()
        assert provider.calls == (2 if bad_witness else 1)
        assert provenance["attempts"] == provider.calls
        assert {k: v for k, v in actual.items() if k != "rationale"} == {
            k: v for k, v in after_test_repair.items() if k != "rationale"
        }
        assert actual["acceptance_criteria"][0] == before["acceptance_criteria"][0]
        assert row == before
    finally:
        coordinator.shutdown()

"""A witness defect must not replace valid model-authored acceptance outcomes."""

import threading
import time

import pytest
from pydantic import ValidationError

from cybersrs.compact_requirements import generate_compact_requirements
from cybersrs.evidence import build_evidence
from cybersrs.provider import GenerationError


def test_logging_witness_only_repair_keeps_valid_outcome(analysis) -> None:
    """Constrain the model to the rejected witness and revalidate the complete requirement."""
    source = "Security operators review alerts."
    evidence = build_evidence(source, [])
    target = analysis.model_copy(update={"assessments": [analysis.assessments[0]]})
    original = {
        "given": "A security operator and test alert are present",
        "when": "The security operator requests the alert",
        "then": "The requested alert is returned to the security operator",
        "method": "test",
        "observable_evidence": "Test capture of the production audit log",
    }

    class Provider:
        """Use an inert saved candidate and field-only repair, never real inference."""

        model_name = "test-adapter"

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Assert schema and frozen fields prevent unrelated acceptance changes."""
            if "tests_to_repair" not in context:
                candidate = schema.model_validate(
                    {
                        "E-001": {
                            "statement": (
                                "The system shall allow security operators to review alerts."
                            ),
                            "tests": [original],
                            "unresolved_decisions": [],
                        }
                    }
                )
                issues = validate(candidate)
                assert issues == ["FR-001:unconfirmed_production_log_witness_use_test_capture"]
                raise GenerationError(
                    "section_validation_failed:witness",
                    rejected_candidate=candidate.model_dump(),
                    rejected_model="test-base",
                    attempts=2,
                )
            patch = context["tests_to_repair"]["E-001_test_1"]
            assert patch["frozen_test_fields"]["then"] == original["then"]
            assert patch["outcome_focus"] == original["when"]
            with pytest.raises(ValidationError):
                schema.model_validate(
                    {"E-001_test_1": {"observable_evidence": "Test capture of production logs"}}
                )
            candidate = schema.model_validate(
                {"E-001_test_1": {"observable_evidence": "Test capture of the resulting response"}}
            )
            assert validate(candidate) == []
            return candidate, {"model": "test-base", "attempts": 1}

    result, _ = generate_compact_requirements(
        Provider(), "functional", evidence, target, [], {}, threading.Event(), time.monotonic() + 5
    )
    criterion = result["requirements"][0]["acceptance_criteria"][0]
    assert criterion == original | {"observable_evidence": "Test capture of the resulting response"}


def test_compact_repair_continues_after_a_partial_model_correction(analysis) -> None:
    """A mixed witness/result rejection gets a second correction in the original run."""
    evidence = build_evidence("Security operators review alerts.", [])
    target = analysis.model_copy(update={"assessments": [analysis.assessments[0]]})
    statement = "The system shall allow security operators to review alerts."
    result_with_fields = "The requested alert and its timestamp are returned"
    outcome = "The requested alert is returned to the security operator"
    witness = "Test capture of the resulting response"
    original = {
        "given": "A security operator and test alert are present",
        "when": "The security operator requests the alert",
        "then": result_with_fields,
        "method": "test",
        "observable_evidence": "Test capture of the production audit log",
    }

    class Provider:
        """Model an initial rejection, a partial fix and then a complete correction."""

        model_name = "test-adapter"
        calls = 0

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Return exactly the requested fields and use the real acceptance validator."""
            self.calls += 1
            if self.calls == 1:
                candidate = schema.model_validate({
                    "E-001": {
                        "statement": statement,
                        "tests": [original],
                        "unresolved_decisions": [],
                    }
                })
            else:
                candidate = schema.model_validate({
                    "E-001_test_1": {
                        "then": result_with_fields if self.calls == 2 else outcome,
                        "observable_evidence": witness,
                    }
                })
            issues = validate(candidate)
            if self.calls <= 2:
                assert "FR-001:unsupported_result_fields_need_TBD" in issues
                assert any("production_log_witness" in issue for issue in issues) == (
                    self.calls == 1
                )
                raise GenerationError(
                    "section_validation_failed:" + ";".join(issues),
                    rejected_candidate=candidate.model_dump(),
                    rejected_model=self.model_name,
                    attempts=1,
                )
            assert issues == []
            return candidate, {"model": self.model_name, "attempts": 1}

    provider = Provider()
    result, provenance = generate_compact_requirements(
        provider, "functional", evidence, target, [], {}, threading.Event(),
        time.monotonic() + 5, max_test_repairs=2,
    )
    assert provider.calls == provenance["attempts"] == 3
    assert result["requirements"][0]["acceptance_criteria"] == [
        original | {"then": outcome, "observable_evidence": witness}
    ]

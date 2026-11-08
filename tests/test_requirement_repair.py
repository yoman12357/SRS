"""Targeted completion adds missing local-model artifacts without replacing valid siblings."""

import copy
import threading
import time

from cybersrs.evidence import build_evidence
from cybersrs.permission_verification import permission_test_gaps
from cybersrs.requirement_repair import complete_source_gaps
from cybersrs.schemas import AcceptanceTestRepair, EvidenceAssessment, Requirement
from cybersrs.validation import validate_section

from .conftest import requirement
from .test_permission_verification import criterion


class ArtifactProvider:
    """Return one declared artifact and execute the actual validation callback."""

    model_name = "synthetic-local-qwen"

    def __init__(self, schema, content):
        """Keep a single expected request so repeated or unrelated calls fail."""
        self.schema, self.content, self.calls = schema, content, 0

    def generate(self, system, context, schema, cancel, deadline, validate):
        """Validate the exact targeted artifact through the production gate."""
        assert self.calls == 0 and schema is self.schema
        self.calls += 1
        if context.get("gap_to_close") == "permitted_acknowledgement_outcome_not_observed":
            assert context["existing_tests"] == []
            assert all(set(row) == {"id", "statement"} for row in context["existing_requirements"])
            bad = schema.model_validate(copy.deepcopy(self.content))
            bad.acceptance_criterion.when = "The operator reviews a network access alert."
            assert any("permitted_acknowledgement" in code for code in validate(bad))
        result = schema.model_validate(copy.deepcopy(self.content))
        if context.get("source_completion_statement"):
            wrong = result.model_copy(deep=True)
            wrong.statement += " including group permissions."
            assert "completion_must_preserve_source_statement" in validate(wrong)
        assert validate(result) == []
        return result, {"model": self.model_name, "attempts": 1}


def test_positive_only_restoration_gap_gets_one_model_authored_test(analysis):
    """Close the observed missing test without inventing a prohibition or replacing valid tests."""
    source = "Network administrators may manually isolate a device and restore its access."
    row = requirement(source, "E-001") | {"id": "SEC-001"}
    row["acceptance_criteria"] = [
        criterion(
            "A network administrator selects a device",
            "The administrator manually isolates it",
            "The device is isolated",
        )
    ]
    added = criterion(
        "The administrator selects the isolated device",
        "The administrator restores its access",
        "Device network access is restored",
    )
    provider = ArtifactProvider(
        AcceptanceTestRepair, {"requirement_id": row["id"], "acceptance_criterion": added}
    )
    fixed, _, attempts = complete_source_gaps(
        provider,
        "security",
        {"requirements": [row]},
        {},
        build_evidence(source, []),
        target_analysis(analysis),
        [],
        {},
        threading.Event(),
        time.monotonic() + 5,
    )
    assert attempts == 1
    assert fixed["requirements"][0]["acceptance_criteria"] == row["acceptance_criteria"] + [added]
    assert fixed["requirements"][0]["statement"] == source


def target_analysis(analysis):
    """Bind a synthetic compound source to the security section."""
    return analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id="E-001",
                    kind="requirement",
                    sections=["security"],
                    explanation="Both roles and their distinct permissions are authoritative.",
                )
            ]
        }
    )


def test_missing_acknowledgement_gets_a_linked_test_without_rewriting(analysis) -> None:
    """Retain positive review and denied editing while adding observed acknowledgement."""
    source = "Security operators may review and acknowledge alerts but may not change policies."
    row = requirement(source, "E-001") | {"id": "SEC-002", "dependencies": ["SEC-001"]}
    row["acceptance_criteria"] = [
        criterion(
            "An operator is present", "The operator reviews an alert", "The alert is displayed"
        ),
        criterion("An operator is present", "The operator edits a policy", "The edit is denied"),
    ]
    added = criterion(
        "An operator has an unacknowledged alert",
        "The operator acknowledges the alert",
        "The alert state is visibly marked acknowledged",
    )
    provider = ArtifactProvider(
        AcceptanceTestRepair,
        {
            "requirement_id": "SEC-002",
            "acceptance_criterion": added,
        },
    )
    content = {"requirements": [row]}
    fixed, models, attempts = complete_source_gaps(
        provider,
        "security",
        content,
        {},
        build_evidence(source + "\nAdministrators can manage accounts.", []),
        target_analysis(analysis),
        [],
        {
            "security": {
                "requirements": [
                    requirement("The system shall let administrators manage accounts.", "E-002")
                    | {"id": "SEC-001"}
                ]
            }
        },
        threading.Event(),
        time.monotonic() + 5,
    )
    assert fixed["requirements"][0]["statement"] == source
    assert fixed["requirements"][0]["acceptance_criteria"] == row["acceptance_criteria"] + [added]
    assert content["requirements"][0]["acceptance_criteria"] == row["acceptance_criteria"]
    assert permission_test_gaps(source, fixed["requirements"][0]["acceptance_criteria"]) == []
    assert models == {provider.model_name} and attempts == 1


def test_missing_second_actor_obligation_becomes_an_additional_requirement(analysis) -> None:
    """A correctly denied support role cannot erase the administrator's management task."""
    source = (
        "Administrators manage remote-access permissions; support operators may inspect "
        "connection logs but cannot grant permissions."
    )
    existing = requirement(
        "Support operators may inspect connection logs but cannot grant permissions.", "E-001"
    ) | {"id": "SEC-001"}
    existing["acceptance_criteria"] = [
        criterion(
            "A support operator is present", "The operator inspects logs", "Logs are displayed"
        ),
        criterion(
            "A support operator is present", "The operator grants permissions", "Grant is denied"
        ),
    ]
    missing = requirement(
        "The system shall permit administrators to manage remote-access permissions.", "E-001"
    )
    provider = ArtifactProvider(Requirement, missing)
    interpretation = target_analysis(analysis)
    evidence = build_evidence(source, [])
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
    assert len(fixed["requirements"]) == 2
    assert fixed["requirements"][0] == existing
    assert fixed["requirements"][1]["id"] == "SEC-002"
    assert validate_section("security", fixed, evidence, interpretation, [], {}) == []

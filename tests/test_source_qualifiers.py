"""Preserve source behavior while removing model-added timing and denial-message qualifications."""

import copy
import threading
import time

from cybersrs.acceptance_grounding import preserve_source_denial
from cybersrs.architecture_agent import generate_architecture
from cybersrs.architecture_normalization import preserve_architecture_timing
from cybersrs.audit import audit_scope
from cybersrs.evidence import build_evidence
from cybersrs.repository import Repository
from cybersrs.requirement_repair import complete_source_gaps
from cybersrs.schemas import AcceptanceTestRepair, ArchitectureLayoutComponents
from cybersrs.validation import assign_ids, validate_section

from .conftest import DESCRIPTION, requirement
from .test_permission_verification import criterion
from .test_requirement_repair import target_analysis

SOURCE = (
    "Administrators manage remote-access permissions; support operators may inspect "
    "connection logs but cannot grant permissions."
)
DENIAL = criterion(
    "A support operator accesses the connection logs dashboard after authentication.",
    "The system receives a request to grant remote-access permissions via the VPN interface.",
    "The system shall deny the request and display an error message indicating that "
    "only administrators can grant remote-access permissions.",
)
DENIAL["observable_evidence"] = (
    "Observe the system response showing a denial of permission grant with a clear error "
    "message such as 'Only administrators may grant remote-access permissions.'"
)


def test_required_denial_preserves_trigger_and_outcome_without_unstated_explanation(
    settings,
) -> None:
    """Reproduce the real bounded-repair response and retain its observable source denial."""
    repo = Repository(settings.data_dir)
    project = repo.create_project("Synthetic qualifier regression", SOURCE)
    original = copy.deepcopy(DENIAL)
    with audit_scope(repo, project["id"]):
        result = preserve_source_denial(SOURCE, original, "FR-004")
    assert original == DENIAL
    assert result["given"] == original["given"] and result["when"] == original["when"]
    assert result["then"] == "The system shall deny the request and display an error message."
    assert "Only administrators" not in result["observable_evidence"]
    assert any(e["kind"] == "denial_copy_normalized" for e in repo.list_audit(project["id"]))


def test_unsupported_action_or_statement_cannot_be_hidden_by_copy_normalization() -> None:
    """The correction applies only when the source's actual prohibited action was exercised."""
    wrong = DENIAL | {"when": "A support operator changes unrelated configuration"}
    assert preserve_source_denial(SOURCE, wrong, "FR-004") == wrong
    rule = DENIAL | {"then": "Only administrators can grant permissions."}
    assert preserve_source_denial(SOURCE, rule, "FR-004") == rule
    explicit = SOURCE + " Only administrators can grant permissions."
    assert preserve_source_denial(explicit, DENIAL, "FR-004") == DENIAL


def test_required_denial_repair_rejects_added_message_then_accepts_observable_denial(
    analysis,
) -> None:
    """Removing exclusive copy alone must not approve an unrequested product message."""
    row = requirement(
        "Support operators may inspect connection logs but cannot grant permissions.", "E-001"
    )
    row["id"] = "SEC-002"
    row["acceptance_criteria"] = [
        criterion(
            "A support operator opens the log dashboard",
            "The system loads the log view",
            "The system displays connection logs",
        )
    ]
    administrator = requirement(
        "The system shall allow administrators to manage permissions.", "E-001"
    )
    administrator["id"] = "SEC-001"
    previous = {"security": {"requirements": [administrator]}}

    class DenialProvider:
        """Exercise the original rejected draft and a source-faithful corrective response."""

        model_name = "test-qwen"

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Keep the denial test while rejecting its unsupported interface contract."""
            assert schema is AcceptanceTestRepair
            first = schema.model_validate(
                {"requirement_id": "SEC-002", "acceptance_criterion": DENIAL}
            )
            assert any("unconfirmed_product_message_contract" in code for code in validate(first))
            corrected = copy.deepcopy(DENIAL)
            corrected["then"] = "The support-operator permission-grant request is denied."
            corrected["observable_evidence"] = "Capture the denied response and permission state."
            result = schema.model_validate(
                {"requirement_id": "SEC-002", "acceptance_criterion": corrected}
            )
            assert validate(result) == []
            return result, {"model": self.model_name, "attempts": 2}

    provider = DenialProvider()
    evidence = build_evidence(SOURCE, [])
    interpretation = target_analysis(analysis)
    completed, _, _ = complete_source_gaps(
        provider,
        "security",
        {"requirements": [row]},
        {},
        evidence,
        interpretation,
        [],
        previous,
        threading.Event(),
        time.monotonic() + 5,
    )
    assert len(completed["requirements"][0]["acceptance_criteria"]) == 2
    assert validate_section("security", completed, evidence, interpretation, [], previous) == []


def test_architecture_removes_only_unstated_positive_timing_and_audits_it(settings) -> None:
    """The actual real-time modifiers must not block otherwise faithful logical responsibilities."""
    evidence = build_evidence("Operators may review and acknowledge alerts.", [])
    content = {
        "summary": "Logical alert review",
        "items": [
            {
                "detail": "A component maintains real-time alert visibility.",
                "responsibility": (
                    "Provide real-time alert visibility and acknowledgment capability."
                ),
                "evidence_ids": ["E-001"],
            }
        ],
        "open_issues": [],
    }
    original = copy.deepcopy(content)
    repo = Repository(settings.data_dir)
    project = repo.create_project("Synthetic timing regression", evidence[0].quote)
    with audit_scope(repo, project["id"]):
        normalized = preserve_architecture_timing(content, evidence)
    assert content == original
    assert normalized["items"][0]["responsibility"] == (
        "Provide alert visibility and acknowledgment capability."
    )
    assert normalized["open_issues"]
    assert (
        len(
            [
                e
                for e in repo.list_audit(project["id"])
                if e["kind"] == "architecture_timing_normalized"
            ]
        )
        == 2
    )


def test_source_timing_and_negated_timing_are_not_silently_rewritten() -> None:
    """Keep explicit stakeholder commitments and preserve a negation's meaning."""
    source = build_evidence("Provide real-time alert visibility.", [])
    content = {
        "items": [{"detail": "Provide real-time alert visibility.", "evidence_ids": ["E-001"]}],
        "open_issues": [],
    }
    assert preserve_architecture_timing(content, source) == content
    unknown = build_evidence("Operators review alerts.", [])
    content["items"][0]["detail"] = "The source does not require real-time visibility."
    assert preserve_architecture_timing(content, unknown) == content


def test_undecided_source_timing_is_not_a_positive_commitment() -> None:
    """Merely mentioning real-time in an open decision cannot support a generated guarantee."""
    evidence = build_evidence("Real-time alert visibility remains undecided.", [])
    content = {
        "items": [{"detail": "Provide real-time alert visibility.", "evidence_ids": ["E-001"]}],
        "open_issues": [],
    }
    result = preserve_architecture_timing(content, evidence)
    assert result["items"][0]["detail"] == "Provide alert visibility."
    assert result["open_issues"]


def test_architecture_uses_the_same_bare_retention_contract_as_requirements() -> None:
    """Reproduce the actual audit-store responsibility rejected for adding 'at least'."""
    evidence = build_evidence("The system must retain administrator audit records for 30 days.", [])
    content = {
        "items": [
            {
                "responsibility": (
                    "Store and retain audit records of all policy modifications "
                    "for at least 30 days, "
                    "with traceability to user identity and action context."
                ),
                "evidence_ids": ["E-001"],
            }
        ],
        "open_issues": [],
    }
    normalized = preserve_architecture_timing(content, evidence)
    assert "at least" not in normalized["items"][0]["responsibility"]
    assert "30 days" in normalized["items"][0]["responsibility"]
    assert any("minimum/maximum" in issue for issue in normalized["open_issues"])
    explicit = build_evidence(
        "The system must retain administrator audit records for at least 30 days.", []
    )
    assert preserve_architecture_timing(content, explicit) == content


def test_architecture_stages_publish_normalized_objects_through_full_validation(
    analysis, sections
) -> None:
    """Source layout normalizes names while action/enforcement text stays canonical."""
    design = copy.deepcopy(sections["architecture"])
    original_name = design["items"][0]["component_name"]
    design["items"][0]["component_name"] = "Real-time " + original_name
    design["items"][0]["detail"] = "A logical component provides real-time role-scoped operations."
    design["trust_boundaries"][0]["enforcement"] = (
        "Immediately verify the role before permitting the requested action."
    )

    class DesignProvider:
        """Return the two real-schema draft artifacts through production callbacks."""

        model_name = "synthetic-local-qwen"

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Require complete source validation after the callback's normalization."""
            assert schema is ArchitectureLayoutComponents
            candidate = schema(
                components=[
                    {
                        "component_name": "Real-time " + original_name,
                        "requirement_ids": ["FR-001", "SEC-001"],
                    }
                ]
            )
            assert validate(candidate) == []
            return candidate, {"model": self.model_name, "attempts": 1}

    previous = {name: assign_ids(name, sections[name]) for name in ("functional", "security")}
    evidence = build_evidence(DESCRIPTION, [])
    result, _ = generate_architecture(
        DesignProvider(),
        {},
        evidence,
        analysis,
        [],
        previous,
        threading.Event(),
        time.monotonic() + 5,
    )
    assert "real-time" not in result["items"][0]["detail"]
    assert original_name in [node["component_name"] for node in result["items"]]
    assert not any("Real-time" in node["component_name"] for node in result["items"])
    assert "Immediately" not in result["trust_boundaries"][0]["enforcement"]
    assert validate_section("architecture", result, evidence, analysis, [], previous) == []

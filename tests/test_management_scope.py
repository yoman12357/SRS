"""Reproduce the real completion's invented permission subjects, operations and audit trail."""

import pytest

from cybersrs.acceptance_grounding import acceptance_logging_issues
from cybersrs.evidence import build_evidence
from cybersrs.management_scope import management_scope_issues, management_statement
from cybersrs.provider import generation_schema
from cybersrs.schemas import Requirement
from cybersrs.validation import validate_section

from .conftest import requirement

SOURCE = (
    "Administrators manage remote-access permissions; support operators may inspect "
    "connection logs but cannot grant permissions."
)


def test_management_completion_preserves_exact_actor_action_and_object():
    """Bind the source clause rather than filling in conventional CRUD/group permissions."""
    expected = "The system shall permit administrators to manage remote-access permissions."
    assert management_statement(SOURCE) == expected
    native = generation_schema(Requirement, {"source_management_statement": expected})
    assert native["properties"]["statement"] == {"type": "string", "const": expected}
    assert management_statement("Whether administrators manage permissions is undecided.") is None
    assert management_statement("Administrators cannot manage permissions.") is None


@pytest.mark.parametrize(
    "text,code",
    [
        (
            "Create remote-access permissions for users and groups.",
            "unconfirmed_management_creation",
        ),
        ("Revoke an access right.", "unconfirmed_management_removal"),
        ("Update permissions assigned to groups.", "unconfirmed_permission_group_subject"),
        ("Update the access-control database accordingly.", "unconfirmed_permission_database"),
    ],
)
def test_generic_management_does_not_supply_detailed_commitments(text, code):
    """Do not mislabel implementation conventions as an explicit stakeholder requirement."""
    assert code in management_scope_issues(SOURCE, text)
    assert management_scope_issues(SOURCE + " " + text, text) == []


def test_generic_permission_update_remains_observable():
    """A source-backed management test can inspect requested state without new operation policy."""
    assert (
        management_scope_issues(
            SOURCE,
            "An administrator submits a configured permission-management operation. "
            "The requested permission state is updated. Capture the resulting permission state.",
        )
        == []
    )


@pytest.mark.parametrize("linked", [False, True])
def test_independent_requirement_gate_checks_source_management_scope(analysis, linked):
    """The semantic gate rejects these details even outside native decoding and repair prompts."""
    row = requirement(management_statement(SOURCE), "E-001") | {"id": "FR-001"}
    row["acceptance_criteria"][0]["then"] = "The access-control database is updated for groups."
    content = {"requirements": [row]}
    previous = {}
    if linked:
        previous = {"functional": {"requirements": [row]}}
        content = {
            "requirements": [],
            "related_acceptance_criteria": [
                {
                    "requirement_id": "FR-001",
                    "evidence_ids": ["E-001"],
                    "sources": [],
                    "acceptance_criteria": row["acceptance_criteria"],
                }
            ],
        }
    errors = validate_section(
        "functional",
        content,
        build_evidence(SOURCE, []),
        analysis.model_copy(update={"assessments": []}),
        [],
        previous,
    )
    assert "FR-001:unconfirmed_permission_group_subject" in errors
    assert "FR-001:unconfirmed_permission_database" in errors


@pytest.mark.parametrize(
    "witness",
    [
        "Record of successful access right creation in the audit log",
        "Inspect the access-control log for the permission-change event.",
    ],
)
def test_connection_log_inspection_does_not_authorize_a_new_admin_audit_trail(witness):
    """Reproduce the actual new witness, which used no explicit recording verb."""
    criterion = {
        "then": "The requested permission state is updated.",
        "observable_evidence": witness,
    }
    assert acceptance_logging_issues(SOURCE, criterion) == [
        "unconfirmed_production_log_witness_use_test_capture"
    ]
    criterion["observable_evidence"] = (
        "Capture the requested permission state in a test-harness log."
    )
    assert acceptance_logging_issues(SOURCE, criterion) == []

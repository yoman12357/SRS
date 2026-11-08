"""Real architecture expansions must not become confirmed stakeholder decisions."""

import pytest

from cybersrs.evidence import build_evidence
from cybersrs.provider import generation_schema
from cybersrs.schemas import ArchitectureComponents
from cybersrs.validation import validate_section

from .conftest import requirement
from .test_requirement_repair import target_analysis


@pytest.mark.parametrize(
    "field,value,expected",
    [
        ("status", "confirmed", "architecture:design_requires_proposed_status"),
        (
            "responsibility",
            "Present real-time alerts to security operators.",
            "architecture:unsupported_response_time_commitment",
        ),
        (
            "responsibility",
            "Log all account-management actions to an audit trail.",
            "architecture:items_unrequested_logging",
        ),
    ],
)
def test_inferred_design_status_timing_and_logging_stay_within_scope(
    complete_document, field, value, expected
):
    """Reproduce the confirmed, real-time and expanded-audit claims in the live design."""
    payload = complete_document.model_dump()
    payload["architecture"]["items"][0][field] = value
    predecessors = {
        name: payload[name]
        for name in ("functional", "nonfunctional", "security", "data", "network")
    }
    errors = validate_section(
        "architecture",
        payload["architecture"],
        complete_document.evidence,
        complete_document.analysis,
        [],
        predecessors,
    )
    assert expected in errors


def test_architecture_native_schema_keeps_realizations_as_proposals():
    """Model-authored design status cannot claim stakeholder confirmation by default."""
    schema = generation_schema(
        ArchitectureComponents, {"existing_requirements": [{"id": "FR-001"}]}
    )
    assert schema["$defs"]["ArchitectureComponent"]["properties"]["status"]["const"] == "proposed"


def test_employee_mfa_cannot_silently_apply_to_every_research_service_user(analysis):
    """Reproduce the actual VPN row that dropped the stated employee actor."""
    evidence = build_evidence(
        "Employees authenticate with multi-factor authentication before accessing "
        "approved research services.",
        [],
    )
    row = requirement(
        "The system shall require multi-factor authentication before granting access "
        "to any approved research service.",
        "E-001",
    ) | {"id": "SEC-001"}
    errors = validate_section(
        "security", {"requirements": [row]}, evidence, target_analysis(analysis), [], {}
    )
    assert "SEC-001:explicit_authentication_actor_not_preserved" in errors
    row["statement"] = (
        "The system shall require employees to complete multi-factor authentication "
        "before accessing approved research services."
    )
    assert "SEC-001:explicit_authentication_actor_not_preserved" not in validate_section(
        "security", {"requirements": [row]}, evidence, target_analysis(analysis), [], {}
    )

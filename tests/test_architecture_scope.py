"""Semantic shape and scope checks for logical architecture and unconditional exclusions."""

from cybersrs.evidence import build_evidence
from cybersrs.provider import generation_schema
from cybersrs.schemas import ArchitectureSection, EvidenceAssessment
from cybersrs.validation import validate_document, validate_section

from .conftest import requirement


def test_architecture_grammar_requires_design_fields_and_known_requirement_links() -> None:
    """New generation cannot substitute a copied prohibition for unnamed design blocks."""
    schema = generation_schema(
        ArchitectureSection,
        {
            "existing_requirements": [{"id": "SEC-001"}],
            "evidence": [],
        },
    )
    component = schema["$defs"]["ArchitectureComponent"]
    assert {"component_name", "responsibility"} <= set(component["required"])
    assert component["properties"]["requirement_ids"]["minItems"] == 1
    assert component["properties"]["requirement_ids"]["items"]["enum"] == ["SEC-001"]
    assert "data_or_action" in schema["$defs"]["ArchitectureFlow"]["required"]
    assert "enforcement" in schema["$defs"]["ArchitectureBoundary"]["required"]


def test_architecture_flow_endpoint_must_resolve_to_a_component(complete_document) -> None:
    """Narrative detail and valid requirement IDs do not excuse a dangling design edge."""
    complete_document.architecture.data_flows[0].to_component = "Unknown engine"
    findings = validate_document(complete_document).findings
    assert any("data_flows_unknown_to_component" in item.code for item in findings)


def test_unconditional_exclusion_cannot_be_narrowed_to_one_trigger(analysis) -> None:
    """Preserve the prohibition for all situations when its source states no condition."""
    source = "Do not automatically change firewall rules or isolate devices."
    evidence = build_evidence(source, [])
    interpretation = analysis.model_copy(
        update={
            "assessments": [
                EvidenceAssessment(
                    evidence_id="E-001",
                    kind="exclusion",
                    sections=["security"],
                    explanation="Automatic infrastructure changes are prohibited "
                    "without qualification.",
                )
            ]
        }
    )
    statement = "The system shall not automatically change firewall rules or isolate devices"
    row = requirement(statement + " when an administrator manually isolates a device.", "E-001")
    row["id"] = "SEC-001"
    row["acceptance_criteria"] = [
        {
            "given": "An isolated test environment contains the recorded initial state",
            "when": "The harness attempts automatic firewall rule changes and device isolation",
            "then": "Firewall configuration and device connectivity remain unchanged",
            "method": "test",
            "observable_evidence": "Compare captured before and after configuration "
            "and connectivity state",
        }
    ]
    errors = validate_section("security", {"requirements": [row]}, evidence, interpretation, [], {})
    assert "SEC-001:unsupported_condition_on_explicit_exclusion" in errors
    row["statement"] = statement + "."
    assert (
        validate_section("security", {"requirements": [row]}, evidence, interpretation, [], {})
        == []
    )
    row["statement"] = source
    assert (
        validate_section("security", {"requirements": [row]}, evidence, interpretation, [], {})
        == []
    )

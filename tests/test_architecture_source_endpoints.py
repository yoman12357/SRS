"""Source-backed layout preserves actors, authority, canonical text and destinations."""

import threading
import time

import pytest
from pydantic import ValidationError

from cybersrs.architecture_agent import generate_architecture
from cybersrs.architecture_layout import render_component_layout, source_unknowns
from cybersrs.architecture_sources import (
    SOURCE_ACCESS_OVERVIEW,
    all_source_endpoint_components,
    source_access_architecture_issues,
    source_access_contracts,
    source_actor_architecture_issues,
    source_actor_contracts,
    source_endpoint_components,
)
from cybersrs.evidence import build_evidence
from cybersrs.provider import generation_schema
from cybersrs.schemas import (
    ArchitectureLayoutComponents,
    ArchitectureLayoutInteractions,
)
from cybersrs.validation import validate_section

from .conftest import requirement

SOURCE = (
    "Students and guests may access the internet but must not access the internal staff network."
)


def source_design():
    """Provide observable topology fixtures without claiming any real network test ran."""
    evidence = build_evidence(SOURCE, [])
    row = requirement(SOURCE, "E-001") | {"id": "FR-001"}
    access = source_access_contracts(evidence, [row])
    roles = source_actor_contracts(evidence, [row])
    nodes = all_source_endpoint_components(access, roles)
    owner = render_component_layout(
        [{"component_name": "Policy evaluator", "requirement_ids": ["FR-001"]}], {"FR-001": row}
    )
    actor, internet, staff = [node["component_name"] for node in nodes]
    flows = [
        {
            "from_component": actor,
            "to_component": "Policy evaluator",
            "requirement_ids": ["FR-001"],
        },
        {
            "from_component": "Policy evaluator",
            "to_component": internet,
            "requirement_ids": ["FR-001"],
        },
        {
            "from_component": "Policy evaluator",
            "to_component": staff,
            "requirement_ids": ["FR-001"],
        },
    ]
    boundaries = [
        {
            "untrusted_component": actor,
            "trusted_component": "Policy evaluator",
            "requirement_ids": ["FR-001"],
        }
    ]
    return evidence, row, access, roles, nodes + owner, flows, boundaries


def test_source_roles_and_both_destinations_are_retained_without_new_zones():
    """Source cards are literal representations, not new inferred parties or networks."""
    _, _, access, _, nodes, flows, _ = source_design()
    assert [(c["actor"], c["resource"], c["outcome"]) for c in access] == [
        ("Students and guests", "internet", "permitted"),
        ("Students and guests", "internal staff network", "denied"),
    ]
    assert len(source_endpoint_components(access)) == 3
    assert source_access_architecture_issues({"items": nodes, "data_flows": flows}, access) == []


def test_authentication_before_access_keeps_employee_and_service_names():
    """The source has explicit actor/resource endpoints without a may clause."""
    source = (
        "Employees authenticate with multi-factor authentication before accessing "
        "approved research services."
    )
    rows = [requirement(source, "E-001") | {"id": "SEC-001"}]
    access = source_access_contracts(build_evidence(source, []), rows)
    assert [(c["actor"], c["resource"], c["outcome"]) for c in access] == [
        ("Employees", "approved research services", "authenticated")
    ]


def test_internal_module_prose_cannot_replace_missing_endpoint_nodes(analysis):
    """Reproduce the live engine-to-management-client internet substitution."""
    evidence, row, _, _, nodes, flows, _ = source_design()
    draft = {
        "summary": SOURCE_ACCESS_OVERVIEW,
        "items": [nodes[-1]],
        "data_flows": [
            flows[0] | {"from_component": "Policy evaluator", "to_component": "Policy evaluator"}
        ],
        "trust_boundaries": [],
        "open_issues": [],
    }
    errors = validate_section(
        "architecture",
        draft,
        evidence,
        analysis.model_copy(update={"assessments": []}),
        [],
        {"functional": {"requirements": [row]}},
    )
    assert any("missing_source_actor_endpoint" in error for error in errors)
    assert any("missing_source_resource_endpoint:internet" in error for error in errors)


@pytest.mark.parametrize("defect", ["reversed", "unrelated", "wrong_destination"])
def test_source_endpoints_need_a_directed_source_linked_path(defect):
    """Endpoint names alone do not prove the required directed interaction."""
    _, _, access, _, nodes, flows, _ = source_design()
    if defect == "reversed":
        for flow in flows:
            flow["from_component"], flow["to_component"] = (
                flow["to_component"],
                flow["from_component"],
            )
    elif defect == "unrelated":
        for flow in flows:
            flow["requirement_ids"] = ["FR-999"]
    else:
        flows[1]["to_component"] = "Management client"
    assert any(
        "missing_directed_source_access_path:internet" in issue
        for issue in source_access_architecture_issues(
            {"items": nodes, "data_flows": flows}, access
        )
    )


def test_equivalent_manual_endpoint_names_remain_valid():
    """Manual names can change prefixes while retaining the original actor/resource labels."""
    _, _, access, _, nodes, flows, _ = source_design()
    for node in nodes:
        old = node["component_name"]
        new = old.removeprefix("Actor: ").removeprefix("Resource: ")
        node["component_name"] = new
        for flow in flows:
            for key in ("from_component", "to_component"):
                if flow[key] == old:
                    flow[key] = new
    assert source_access_architecture_issues({"items": nodes, "data_flows": flows}, access) == []


def test_component_plan_cannot_invent_responsibilities_and_preserves_literal_citations():
    """Metadata and normative statements come from canonical requirements, not layout prose."""
    _, row, _, _, _, _, _ = source_design()
    citation = {"chunk_id": "original-chunk", "quote": "Original canonical guidance quotation."}
    row["sources"] = [citation]
    placement = {"component_name": "Policy evaluator", "requirement_ids": ["FR-001"]}
    with pytest.raises(ValidationError):
        ArchitectureLayoutComponents(
            components=[placement | {"responsibility": "Invented regulation"}]
        )
    output = render_component_layout([placement], {"FR-001": row})[0]
    assert output["responsibility"] == SOURCE
    assert output["sources"] == [citation] and output["evidence_ids"] == ["E-001"]


def test_model_chooses_layout_while_source_duties_and_nodes_are_frozen(analysis):
    """Generate model-owned grouping and validate the compiled source paths."""
    evidence, row, _, _, nodes, flows, boundaries = source_design()

    class Provider:
        """Return only model-owned grouping/direction decisions."""

        model_name = "test-qwen"

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Check native vocabularies and independent final graph validation."""
            assert "acceptance_criteria" not in context["existing_requirements"][0]
            if schema is ArchitectureLayoutComponents:
                native = generation_schema(schema, context)
                assert native["properties"]["components"]["minItems"] == 1
                candidate = schema(
                    components=[
                        {
                            "component_name": "Policy evaluator",
                            "requirement_ids": ["FR-001"],
                        }
                    ]
                )
            else:
                assert schema is ArchitectureLayoutInteractions
                assert context["architecture_component_names"] == [
                    n["component_name"] for n in nodes
                ]
                candidate = schema(data_flows=flows, trust_boundaries=boundaries)
            assert validate(candidate) == []
            return candidate, {"model": self.model_name, "attempts": 1}

    result, provenance = generate_architecture(
        Provider(),
        {},
        evidence,
        analysis.model_copy(update={"assessments": []}),
        [],
        {"functional": {"requirements": [row]}},
        threading.Event(),
        time.monotonic() + 5,
    )
    assert result["items"] == nodes
    assert all(flow["data_or_action"].endswith(SOURCE) for flow in result["data_flows"])
    assert result["data_flows"][-1]["data_or_action"].startswith("Denied access attempt.")
    assert result["trust_boundaries"][0]["enforcement"] == SOURCE
    assert (
        provenance["attempts"] == 1
        and provenance["architecture_layout_version"] == "source-backed-layout-1.1"
    )


def test_missing_constraint_gets_an_existing_owner_without_new_behavior(analysis):
    """Recover the observed missing exclusion through a narrow model relationship decision."""
    _, row, _, _, _, flows, boundaries = source_design()
    exclusion = "Do not automatically change firewall rules or isolate devices."
    evidence = build_evidence(SOURCE + " " + exclusion, [])
    added = requirement(exclusion, "E-002") | {"id": "FR-002"}
    calls = []

    class Provider:
        """Select the existing source constraint owner and retain all actual call authors."""

        model_name = "test-qwen"

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Reject source actors as implementation owners and duplicate assignments."""
            calls.append(schema.__name__)
            if schema is ArchitectureLayoutComponents:
                candidate = schema(
                    components=[
                        {
                            "component_name": "Policy evaluator",
                            "requirement_ids": ["FR-001"],
                        }
                    ]
                )
            elif schema.__name__ == "ArchitectureOwnerAssignments":
                native = generation_schema(schema, context)
                assert native["required"] == ["FR-002"]
                assert native["properties"]["FR-002"]["items"]["const"] == "Policy evaluator"
                invalid = schema.model_construct(**{"FR-002": ["Actor: Students and guests"]})
                assert "existing_implementation_component" in validate(invalid)[0]
                candidate = schema.model_validate({"FR-002": ["Policy evaluator"]})
                duplicate = schema.model_construct(**{"FR-002": ["Policy evaluator"] * 2})
                assert "distinct_links" in validate(duplicate)[0]
            else:
                candidate = schema(data_flows=flows, trust_boundaries=boundaries)
            assert validate(candidate) == []
            return candidate, {
                "model": "test-owner"
                if schema.__name__ == "ArchitectureOwnerAssignments"
                else self.model_name,
                "attempts": 1,
            }

    result, provenance = generate_architecture(
        Provider(),
        {},
        evidence,
        analysis.model_copy(update={"assessments": []}),
        [],
        {"functional": {"requirements": [row, added]}},
        threading.Event(),
        time.monotonic() + 5,
    )
    assert calls == [
        "ArchitectureLayoutComponents",
        "ArchitectureOwnerAssignments",
    ]
    assert result["items"][-1]["responsibility"] == SOURCE + " " + exclusion
    assert provenance["attempts"] == 2 and provenance["output_models"] == [
        "test-owner",
        "test-qwen",
    ]


def test_admin_requests_cannot_originate_from_the_student_actor():
    """Reproduce the actual accepted-by-old-gates wrong-role flow and trust boundary."""
    _, student_row, _, _, _, flows, _ = source_design()
    admin_source = "Network administrators may manually isolate a device and restore its access."
    evidence = build_evidence(SOURCE + " " + admin_source, [])
    admin_row = requirement(admin_source, "E-002") | {"id": "FR-002"}
    rows = [student_row, admin_row]
    access, roles = source_access_contracts(evidence, rows), source_actor_contracts(evidence, rows)
    nodes = all_source_endpoint_components(access, roles) + render_component_layout(
        [
            {"component_name": "Policy evaluator", "requirement_ids": ["FR-001"]},
            {"component_name": "Manual interface", "requirement_ids": ["FR-002"]},
        ],
        {row["id"]: row for row in rows},
    )
    wrong = {
        "from_component": "Actor: Students and guests",
        "to_component": "Manual interface",
        "requirement_ids": ["FR-002"],
    }
    boundary = {
        "untrusted_component": wrong["from_component"],
        "trusted_component": "Manual interface",
        "requirement_ids": ["FR-002"],
    }
    draft = {"items": nodes, "data_flows": flows + [wrong], "trust_boundaries": [boundary]}
    errors = source_actor_architecture_issues(draft, roles)
    assert "architecture:source_actor_flow_uses_wrong_role" in errors
    assert "architecture:source_actor_boundary_uses_wrong_role" in errors
    wrong["from_component"] = boundary["untrusted_component"] = "Actor: Network administrators"
    assert source_actor_architecture_issues(draft, roles) == []


def test_compound_source_role_binding_does_not_grant_support_the_admin_obligation():
    """A shared evidence ID is insufficient for assigning another role's permission."""
    source = (
        "Administrators manage remote-access permissions; support operators may inspect "
        "connection logs but cannot grant permissions."
    )
    rows = [
        requirement(
            "The system shall permit administrators to manage remote-access permissions.", "E-001"
        )
        | {"id": "FR-001"},
        requirement(
            "Support operators may inspect connection logs but cannot grant permissions.", "E-001"
        )
        | {"id": "FR-002"},
    ]
    contracts = source_actor_contracts(build_evidence(source, []), rows)
    assert {c["actor"]: c["requirement_ids"] for c in contracts} == {
        "support operators": ["FR-002"],
        "Administrators": ["FR-001"],
    }


def test_open_issues_preserve_unknowns_without_reopening_exclusions():
    """Do not invent an automated-alert action question after automation was excluded."""
    unknown = "Budget and protocol choices are undecided."
    evidence = build_evidence("Do not automatically isolate devices. " + unknown, [])
    assert source_unknowns(evidence) == [unknown]


def test_access_decision_path_reaches_resource_through_its_implementation_owner():
    """Separate client-to-owner and client-to-internet arrows cannot imply an enforced route."""
    _, _, access, _, nodes, flows, _ = source_design()
    flows[1]["from_component"] = flows[0]["from_component"]
    errors = source_access_architecture_issues({"items": nodes, "data_flows": flows}, access)
    assert any("missing_directed_source_access_path:internet" in error for error in errors)
    flows[1]["from_component"] = "Policy evaluator"
    assert source_access_architecture_issues({"items": nodes, "data_flows": flows}, access) == []


def test_each_access_target_uses_its_own_canonical_source_obligation():
    """Do not label a research-data denial with the support-portal permission's ID."""
    source = (
        "Contractors may access only the support portal and must be denied research data access."
    )
    rows = [
        requirement("Contractors may access only the support portal.", "E-001") | {"id": "FR-001"},
        requirement("Contractors must be denied research data access.", "E-001") | {"id": "FR-002"},
    ]
    contracts = source_access_contracts(build_evidence(source, []), rows)
    assert {c["resource"]: c["requirement_ids"] for c in contracts} == {
        "support portal": ["FR-001"],
        "research data": ["FR-002"],
    }

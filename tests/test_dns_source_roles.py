"""DNS policy administrators remain literal source actors across ordinary wording forms."""

import pytest

from cybersrs.architecture_layout import render_component_layout, render_interaction_layout
from cybersrs.architecture_paths import compile_source_paths
from cybersrs.architecture_sources import (
    all_source_endpoint_components,
    source_access_contracts,
    source_actor_architecture_issues,
    source_actor_contracts,
)
from cybersrs.evidence import build_evidence
from cybersrs.scenario_projection import scenario_inventory

from .conftest import requirement


@pytest.mark.parametrize(
    "modal", ["should be able to", "shall be able to", "must be able to", "can", "may"]
)
def test_policy_creation_modals_keep_literal_administrator_role(modal: str) -> None:
    """Recognize the actual DNS policy clause without inventing or expanding a role name."""
    source = f"Administrators {modal} create and update filtering policies."
    rows = [requirement(source, "E-001") | {"id": "FR-001"}]
    contracts = source_actor_contracts(build_evidence(source, []), rows)
    assert [(role["actor"], role["requirement_ids"]) for role in contracts] == [
        ("Administrators", ["FR-001"])
    ]


@pytest.mark.parametrize("verb", ["provide", "provides"])
def test_dashboard_recipient_is_a_source_role(verb: str) -> None:
    """A source-provided dashboard identifies its user without a separate may clause."""
    source = f"The system should {verb} administrators with a dashboard for reviewing events."
    rows = [requirement(source, "E-001") | {"id": "FR-001"}]
    contracts = source_actor_contracts(build_evidence(source, []), rows)
    assert [role["actor"] for role in contracts] == ["administrators"]


@pytest.mark.parametrize(
    "source",
    [
        "Administrators should not be able to create filtering policies.",
        "Whether administrators should be able to create policies is undecided.",
        "The system must not provide administrators with a dashboard.",
        "If approved, the system may provide administrators with a dashboard.",
        "No system should provide administrators with a dashboard.",
    ],
)
def test_negative_or_unresolved_role_duties_are_not_permissions(source: str) -> None:
    """The added grammar cannot turn a conditional or negated source into authority."""
    rows = [requirement(source, "E-001") | {"id": "FR-001"}]
    assert source_actor_contracts(build_evidence(source, []), rows) == []


def test_dns_scenarios_use_source_administrators_despite_qualified_analysis_role(analysis) -> None:
    """Reproduce the actual scenario failure without substituting an inferred stakeholder."""
    source = (
        "Administrators should be able to create and update filtering policies, allow approved "
        "exceptions, investigate repeated attempts to access blocked resources, and temporarily "
        "restrict users when suspicious behavior is detected."
    )
    row = requirement(source, "E-001") | {"id": "FR-001"}
    target = analysis.model_copy(update={"stakeholders": ["university administrators"]})
    inventory = scenario_inventory(
        {"functional": {"requirements": [row]}}, build_evidence(source, []), target
    )
    assert inventory["actor_options"] == {"FR-001": ["Administrators"]}


def test_case_variants_share_one_actor_node_and_both_canonical_paths() -> None:
    """Reproduce the second live DNS failure and check graph links use the merged node."""
    source = (
        "The system should provide administrators with a dashboard for reviewing events. "
        "Administrators should be able to create and update filtering policies."
    )
    evidence = build_evidence(source, [])
    rows = [
        requirement(fact.quote, fact.id) | {"id": f"FR-{index:03d}"}
        for index, fact in enumerate(evidence, 1)
    ]
    canonical = {row["id"]: row for row in rows}
    roles = source_actor_contracts(evidence, rows)
    assert [role["actor"] for role in roles] == ["administrators", "Administrators"]
    nodes = all_source_endpoint_components([], roles)
    assert len(nodes) == 1
    assert nodes[0]["evidence_ids"] == ["E-001", "E-002"]
    assert nodes[0]["requirement_ids"] == ["FR-001", "FR-002"]
    owners = {"FR-001": "Dashboard", "FR-002": "Policy service"}
    compiled = compile_source_paths(roles, [], owners)
    assert {flow["from_component"] for flow in compiled["data_flows"]} == {
        nodes[0]["component_name"]
    }
    assert {boundary["untrusted_component"] for boundary in compiled["trust_boundaries"]} == {
        nodes[0]["component_name"]
    }
    design = {
        "items": nodes
        + render_component_layout(
            [{"component_name": owner, "requirement_ids": [rid]} for rid, owner in owners.items()],
            canonical,
        )
    } | render_interaction_layout(compiled, canonical)
    assert source_actor_architecture_issues(design, roles) == []


def test_case_folding_keeps_distinct_role_qualifiers() -> None:
    """Network administrators and lab administrators must never be merged as one role."""
    source = (
        "Network administrators may create filtering policies. "
        "Lab administrators may review active sessions."
    )
    evidence = build_evidence(source, [])
    rows = [
        requirement(fact.quote, fact.id) | {"id": f"FR-{index:03d}"}
        for index, fact in enumerate(evidence, 1)
    ]
    nodes = all_source_endpoint_components([], source_actor_contracts(evidence, rows))
    assert len(nodes) == 2


def test_access_actor_and_resource_case_variants_share_compiled_endpoints() -> None:
    """The same identity rule applies to resource paths as to role-only requests."""
    source = "Students may access the Internet. students may access the internet."
    evidence = build_evidence(source, [])
    rows = [
        requirement(fact.quote, fact.id) | {"id": f"FR-{index:03d}"}
        for index, fact in enumerate(evidence, 1)
    ]
    access = source_access_contracts(evidence, rows)
    nodes = all_source_endpoint_components(access, [])
    assert len(nodes) == 2
    names = {node["component_name"] for node in nodes} | {"Access owner"}
    compiled = compile_source_paths([], access, {row["id"]: "Access owner" for row in rows})
    assert all(
        flow["from_component"] in names and flow["to_component"] in names
        for flow in compiled["data_flows"]
    )

"""Embedded source permissions must produce architecture request paths."""

import threading
import time

import pytest

from cybersrs.architecture_agent import generate_architecture
from cybersrs.architecture_sources import source_actor_contracts
from cybersrs.evidence import build_evidence
from cybersrs.schemas import ArchitectureLayoutComponents
from cybersrs.validation import validate_section

from .conftest import requirement


@pytest.mark.parametrize(
    "source,actor",
    [
        (
            "The system should use centralized authentication and allow network "
            "administrators to define access policies for different user groups.",
            "network administrators",
        ),
        (
            "The platform should monitor authentication attempts and allow administrators "
            "to revoke or suspend network access when suspicious activity is detected.",
            "administrators",
        ),
        ("The system allows support operators to inspect connection logs.", "support operators"),
        (
            "The system must record revocations in an audit log that only authorized "
            "administrators can review.",
            "authorized administrators",
        ),
    ],
)
def test_embedded_permissions_keep_exact_source_roles(source: str, actor: str) -> None:
    """The actual NAC wording must not be silently omitted from the source graph."""
    rows = [requirement(source, "E-001") | {"id": "FR-001"}]
    contracts = source_actor_contracts(build_evidence(source, []), rows)
    assert [(item["actor"], item["requirement_ids"]) for item in contracts] == [(actor, ["FR-001"])]


@pytest.mark.parametrize(
    "prefix",
    [
        "The system must not",
        "The platform must never",
        "The system cannot",
        "Whether the system should",
        "If approved, the system may",
        "No system should",
        "The system should not automatically",
    ],
)
def test_negated_or_unresolved_allowance_does_not_create_permission(prefix: str) -> None:
    """A prohibition or conditional proposal is not an affirmative role permission."""
    source = prefix + " allow administrators to change access policies."
    rows = [requirement(source, "E-001") | {"id": "FR-001"}]
    assert source_actor_contracts(build_evidence(source, []), rows) == []


def test_embedded_role_is_not_assigned_another_canonical_duty() -> None:
    """Sharing source evidence must not bind administrator control to unrelated monitoring."""
    source = "Monitor events and allow administrators to revoke network access."
    rows = [
        requirement("The system shall monitor events.", "E-001") | {"id": "FR-001"},
        requirement("The system shall allow administrators to revoke access.", "E-001")
        | {"id": "FR-002"},
    ]
    contracts = source_actor_contracts(build_evidence(source, []), rows)
    assert contracts[0]["requirement_ids"] == ["FR-002"]


def test_disjoint_component_owners_still_compile_embedded_actor_paths(analysis) -> None:
    """Reproduce the NAC empty graph without any real model inference or made-up coupling."""
    sources = [
        "The system should allow administrators to define access policies.",
        "The platform should allow operators to inspect security events.",
    ]
    evidence = build_evidence(" ".join(sources), [])
    rows = [
        requirement(source, f"E-{index:03d}") | {"id": f"FR-{index:03d}"}
        for index, source in enumerate(sources, 1)
    ]

    class SavedLayout:
        """Return the same disjoint component assignment that exposed the missing graph."""

        model_name = "offline-layout-fixture"

        def generate(self, system, context, schema, cancel, deadline, validate):
            """Only a component selection is needed; paths come from explicit permissions."""
            assert schema is ArchitectureLayoutComponents
            result = schema(
                components=[
                    {"component_name": "Policy service", "requirement_ids": ["FR-001"]},
                    {"component_name": "Monitoring service", "requirement_ids": ["FR-002"]},
                ]
            )
            assert validate(result) == []
            return result, {"model": self.model_name, "attempts": 1}

    predecessors = {"functional": {"requirements": rows}}
    current_analysis = analysis.model_copy(update={"assessments": []})
    content, _ = generate_architecture(
        SavedLayout(),
        {},
        evidence,
        current_analysis,
        [],
        predecessors,
        threading.Event(),
        time.monotonic() + 5,
    )
    assert len(content["data_flows"]) == len(content["trust_boundaries"]) == 2
    assert (
        validate_section("architecture", content, evidence, current_analysis, [], predecessors)
        == []
    )
    assert [(flow["from_component"], flow["to_component"]) for flow in content["data_flows"]] == [
        ("Actor: administrators", "Policy service"),
        ("Actor: operators", "Monitoring service"),
    ]

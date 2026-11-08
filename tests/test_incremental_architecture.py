"""Architecture nodes are frozen before the model drafts constrained edges."""

import threading
import time

import pytest
from pydantic import ValidationError

from cybersrs.architecture_agent import generate_architecture
from cybersrs.evidence import build_evidence
from cybersrs.provider import GenerationError, generation_schema
from cybersrs.schemas import (
    ArchitectureInternalInteractions,
    ArchitectureLayoutComponents,
)
from cybersrs.semantics import semantic_issues
from cybersrs.validation import assign_ids, validate_section

from .conftest import DESCRIPTION


def test_frozen_node_names_constrain_edges_and_final_design(analysis, sections) -> None:
    """Both model stages use full gates and only declared component names can become endpoints."""
    architecture = sections["architecture"]
    context = {
        "assigned_section": "architecture",
        "existing_requirements": [
            {"id": "FR-001"},
            {"id": "SEC-001"},
        ],
    }

    class DesignProvider:
        """Return real-schema node/edge artifacts and inspect the endpoint vocabulary."""

        model_name = "test-qwen"

        def __init__(self):
            """Record calls so the component vocabulary precedes edge generation."""
            self.calls = []

        def generate(self, system, current, schema, cancel, deadline, validate):
            """Check the native endpoint enums and apply the full production validators."""
            self.calls.append(schema.__name__)
            if schema is ArchitectureLayoutComponents:
                content = {
                    "components": [
                        {key: item[key] for key in ("component_name", "requirement_ids")}
                        for item in architecture["items"]
                    ]
                }
            elif schema.__name__ == "ArchitectureRouteChoices":
                content = {
                    row["id"]: "Operations service" for row in current["existing_requirements"]
                }
                native = generation_schema(schema, current)
                assert set(native["required"]) == set(content)
                assert set(native["properties"]) == set(content)
            else:
                assert schema is ArchitectureInternalInteractions
                names = current["architecture_component_names"]
                assert names == [item["component_name"] for item in architecture["items"]]
                native = generation_schema(schema, current)
                cases = native["$defs"]["ArchitectureFlowPlacement"]["anyOf"]
                allowed = {
                    (pair["from_component"], pair["to_component"]): pair["requirement_ids"]
                    for pair in current["permitted_internal_pairs"]
                }
                for case in cases:
                    props = case["properties"]
                    pair = (props["from_component"]["const"], props["to_component"]["const"])
                    assert pair[0] in names and pair[1] in names
                    assert set(props["requirement_ids"]["items"]["enum"]) == set(allowed[pair])
                content = {
                    "data_flows": [
                        {
                            key: item[key]
                            for key in ("from_component", "to_component", "requirement_ids")
                        }
                        for item in architecture["data_flows"]
                    ],
                    "trust_boundaries": [
                        {
                            key: item[key]
                            for key in (
                                "untrusted_component",
                                "trusted_component",
                                "requirement_ids",
                            )
                        }
                        for item in architecture["trust_boundaries"]
                    ],
                }
            candidate = schema.model_validate(content)
            assert validate(candidate) == []
            return candidate, {"model": self.model_name, "attempts": 1}

    predecessors = {name: assign_ids(name, sections[name]) for name in ("functional", "security")}
    provider = DesignProvider()
    result, provenance = generate_architecture(
        provider,
        context,
        build_evidence(DESCRIPTION, []),
        analysis,
        [],
        predecessors,
        threading.Event(),
        time.monotonic() + 5,
    )
    assert provider.calls == [
        "ArchitectureLayoutComponents",
        "ArchitectureRouteChoices",
        "ArchitectureInternalInteractions",
    ]
    assert provenance["attempts"] == 3
    assert (
        validate_section(
            "architecture", result, build_evidence(DESCRIPTION, []), analysis, [], predecessors
        )
        == []
    )


def test_bare_retention_is_not_a_minimum_in_linked_narrative() -> None:
    """Architecture and workflow text cannot silently add a lower bound to a bare duration."""
    source = build_evidence("Retain audit records for 30 days.", [])
    assert semantic_issues("The store retains audit records for at least 30 days.", source)
    assert semantic_issues("The store retains audit records for 30 days.", source) == []
    confirmed = build_evidence("Retain audit records for at least 30 days.", [])
    assert semantic_issues("The store retains audit records for at least 30 days.", confirmed) == []


def test_wifi_ownership_requires_every_missing_key_and_keeps_shared_owners(analysis):
    """Replay the live four-ID omission while preserving multiple distinct owners of FR-013."""
    from cybersrs.atomic_requirements import generate_atomic_requirements

    from .test_atomic_source_generation import SourceCriterionProvider
    from .test_semantic_source_cases import CASES, case_analysis

    evidence, interpreted = case_analysis(
        next(case for case in CASES if case["key"] == "wifi"), analysis
    )
    predecessors = {}
    for section in ("functional", "nonfunctional"):
        content, _ = generate_atomic_requirements(
            SourceCriterionProvider(),
            section,
            evidence,
            interpreted,
            [],
            predecessors,
            threading.Event(),
            time.monotonic() + 5,
        )
        predecessors[section] = content
    placements = [
        {
            "component_name": "Wireless Access Gateway",
            "requirement_ids": ["FR-001", "NFR-002", "NFR-003"],
        },
        {
            "component_name": "Central Authentication Service",
            "requirement_ids": ["FR-002", "FR-004", "FR-005", "FR-006", "FR-007", "FR-008"],
        },
        {"component_name": "Role-Based Access Control Engine", "requirement_ids": ["FR-003"]},
        {
            "component_name": "Policy Configuration Interface",
            "requirement_ids": ["FR-009", "FR-010", "FR-011", "FR-012"],
        },
        {
            "component_name": "Device and Session Monitoring Module",
            "requirement_ids": ["FR-005", "FR-006", "FR-007"],
        },
    ]

    class Provider:
        """Inspect the actual production schema and callbacks at the ownership boundary."""

        model_name = "test-qwen"

        def generate(self, system, context, schema, cancel, deadline, validate):
            """A second owner cannot displace a missing canonical obligation."""
            if schema is ArchitectureLayoutComponents:
                result = schema.model_validate({"components": placements})
                assert not validate(result)
                return result, {"model": self.model_name, "attempts": 1}
            assert schema.__name__ == "ArchitectureOwnerAssignments"
            assert set(schema.model_json_schema()["required"]) == {
                "FR-013",
                "NFR-001",
                "NFR-004",
                "NFR-005",
            }
            actual_rejected = {
                "FR-013": ["Wireless Access Gateway", "Policy Configuration Interface"],
                "NFR-004": ["Device and Session Monitoring Module"],
                "NFR-005": ["Central Authentication Service"],
            }
            with pytest.raises(ValidationError) as error:
                schema.model_validate(actual_rejected)
            assert ("NFR-001",) in {tuple(item["loc"]) for item in error.value.errors()}
            complete = schema.model_validate(
                actual_rejected | {"NFR-001": ["Wireless Access Gateway"]}
            )
            assert len(complete.model_dump()["FR-013"]) == 2
            assert not validate(complete)
            raise GenerationError("ownership_test_boundary")

    with pytest.raises(GenerationError, match="ownership_test_boundary"):
        generate_architecture(
            Provider(),
            {},
            evidence,
            interpreted,
            [],
            predecessors,
            threading.Event(),
            time.monotonic() + 5,
        )

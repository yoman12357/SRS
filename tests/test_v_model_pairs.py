"""Methodology-specific workflow proof is stronger than a matching V-Model label."""

import time
from copy import deepcopy
from threading import Event

import pytest

from cybersrs.evidence import build_evidence
from cybersrs.provider import generation_schema
from cybersrs.schemas import SDLCSection
from cybersrs.sdlc import rank_sdlc
from cybersrs.sdlc_agent import generate_sdlc
from cybersrs.validation import assign_ids, validate_section

from .conftest import DESCRIPTION


def test_independent_verification_is_not_reported_as_formal_proof():
    """Keep independent testing distinct from formal methods in evidence and scores."""
    single = rank_sdlc(build_evidence("Independent verification is required before release.", []))
    assert [(f["name"], f["value"]) for f in single["factors"]] == [("verification", "independent")]
    both = rank_sdlc(
        build_evidence("Formal verification and independent verification are required.", [])
    )
    assert {f["value"] for f in both["factors"]} == {"formal", "independent"}
    assert both["ranked_candidates"][0]["score"] == single["ranked_candidates"][0]["score"] == 75


def workflow(sections):
    """Hand-author early test plans with later verification and complete trace links."""
    result = deepcopy(sections["sdlc"])
    template = result["phases"][0]
    result["selected_model"] = "V-Model"
    result["phases"] = [
        deepcopy(template) | {"name": name, "phase_type": kind, "deliverables": [plan]}
        for name, kind, plan in [
            ("Requirements", "planning", "Role behavior acceptance test plan"),
            ("Design", "design", "Role-scoped unit, integration and system test plan"),
            ("Implementation", "implementation", "Implemented operations service"),
            ("Independent Verification", "verification", "Independent test execution evidence"),
        ]
    ]
    result["phases"][-1]["activities"] = [
        "Execute independent unit, integration, system and acceptance tests."
    ]
    result["verification_pairs"] = [
        {
            "development_phase": "Requirements",
            "verification_phase": "Independent Verification",
            "test_scope": "acceptance",
            "test_plan_deliverable": "Role behavior acceptance test plan",
            "requirement_ids": ["FR-001", "SEC-001"],
        },
        {
            "development_phase": "Design",
            "verification_phase": "Independent Verification",
            "test_scope": "system",
            "test_plan_deliverable": "Role-scoped unit, integration and system test plan",
            "requirement_ids": ["FR-001", "SEC-001"],
        },
    ]
    for scope in ("unit", "integration"):
        result["verification_pairs"].append(result["verification_pairs"][1] | {"test_scope": scope})
    return SDLCSection.model_validate(result).model_dump()


def errors(content, analysis, sections):
    """Apply production checks with the exact supplied canonical requirements and evidence."""
    previous = {
        name: assign_ids(name, deepcopy(sections[name])) for name in ("functional", "security")
    }
    return validate_section(
        "sdlc", content, build_evidence(DESCRIPTION, []), analysis, [], previous
    )


def test_v_model_requires_early_plans_with_actual_phase_links(analysis, sections):
    """A grouped pair may cover multiple requirements without manufacturing separate pair quotas."""
    result = workflow(sections)
    assert errors(result, analysis, sections) == []
    result["verification_pairs"] = []
    assert "sdlc:v_model_needs_explicit_verification_pairs" in errors(result, analysis, sections)


@pytest.mark.parametrize(
    "mutation,expected",
    [
        ("unknown", "sdlc:verification_pair_unknown_phase"),
        ("late", "sdlc:verification_plan_must_precede_execution"),
        ("missing_plan", "sdlc:verification_plan_missing_from_development_deliverables"),
        ("missing_coverage", "SEC-001:missing_v_model_pair_coverage"),
        ("no_technical", "sdlc:v_model_needs_acceptance_and_technical_pairing"),
        ("formal", "sdlc:independent_verification_is_not_formal_verification"),
        ("invented_test", "sdlc:unknown_verification_test_reference"),
    ],
)
def test_v_model_rejects_dangling_late_or_incomplete_pairing(
    analysis, sections, mutation, expected
):
    """Reject the observed generic late-test workflow and misleading source/test references."""
    result = workflow(sections)
    if mutation == "unknown":
        result["verification_pairs"][0]["development_phase"] = "Unknown phase"
    elif mutation == "late":
        result["verification_pairs"][0]["development_phase"] = "Independent Verification"
    elif mutation == "missing_plan":
        result["phases"][0]["deliverables"] = ["A requirements document with no test plan"]
    elif mutation == "missing_coverage":
        for pair in result["verification_pairs"]:
            pair["requirement_ids"] = ["FR-001"]
    elif mutation == "no_technical":
        for pair in result["verification_pairs"]:
            pair["test_scope"] = "acceptance"
    elif mutation == "formal":
        result["justification"] += " The model ensures formal verification of all requirements."
    elif mutation == "invented_test":
        result["phases"][0]["activities"].append("Implement fictional test TC-999.")
    assert expected in errors(result, analysis, sections)


def test_v_model_native_schema_requires_pairs_and_the_rule_winner():
    """The decoder cannot omit the new relationship field or change the deterministic label."""
    schema = generation_schema(
        SDLCSection,
        {
            "sdlc_decision": {"required_model": "V-Model"},
            "existing_requirements": [{"id": "FR-001"}],
        },
    )
    assert "verification_pairs" in schema["required"]
    assert schema["properties"]["verification_pairs"]["minItems"] == 1
    assert schema["properties"]["selected_model"]["const"] == "V-Model"


@pytest.mark.parametrize("mutation", ["test_id", "during_build", "wrong_execution", "missing_unit"])
def test_v_model_rejects_observed_plan_confusion(analysis, sections, mutation):
    """Neither real test IDs nor planning during implementation establish early plans."""
    content = workflow(sections)
    if mutation == "test_id":
        content["phases"][0]["deliverables"] = ["TEST-001"]
        content["verification_pairs"][0]["test_plan_deliverable"] = "TEST-001"
    elif mutation == "during_build":
        content["phases"][1]["phase_type"] = "implementation"
    elif mutation == "wrong_execution":
        content["verification_pairs"][0]["verification_phase"] = "Implementation"
    else:
        content["verification_pairs"] = [
            p for p in content["verification_pairs"] if p["test_scope"] != "unit"
        ]
    assert any("sdlc:" in error for error in errors(content, analysis, sections))


def test_source_grouped_v_model_compiles_early_plans_and_all_later_pairs(analysis, sections):
    """Model work choices retain every canonical requirement and all four V test levels."""
    from cybersrs.schemas import LifecycleWorkPlan

    calls = []

    class Provider:
        """Choose work groups through the real composition and validation callback."""

        def generate(self, system, context, schema, cancel, deadline, validate):
            calls.append(schema.__name__)
            assert schema is LifecycleWorkPlan
            value = {
                "justification": (
                    "Independent verification calls for early test planning and paired "
                    "execution; unresolved factors still require review."
                ),
                "work_groups": [{"requirement_ids": ["FR-001", "SEC-001"]}],
            }
            result = schema.model_validate(value)
            assert validate(result) == []
            return result, {"model": "test-author-1", "attempts": 1}

    predecessors = {
        name: assign_ids(name, deepcopy(sections[name])) for name in ("functional", "security")
    }
    actual, provenance = generate_sdlc(
        Provider(),
        {"sdlc_decision": {"required_model": "V-Model"}},
        build_evidence(DESCRIPTION, []),
        analysis,
        [],
        predecessors,
        Event(),
        time.monotonic() + 5,
    )
    assert errors(actual, analysis, sections) == []
    assert {pair["test_scope"] for pair in actual["verification_pairs"]} == {
        "unit",
        "integration",
        "system",
        "acceptance",
    }
    assert calls == ["LifecycleWorkPlan"]
    assert provenance["model"] == "test-author-1"
    assert provenance["lifecycle_projection_version"]


def test_v_model_does_not_relabel_acceptance_plans_as_technical_plans(analysis, sections):
    """Reproduce a completed real draft that linked every scope to its sole acceptance plan."""
    content = workflow(sections)
    for pair in content["verification_pairs"]:
        pair["development_phase"] = "Requirements"
        pair["test_plan_deliverable"] = "Role behavior acceptance test plan"
    assert "sdlc:verification_scope_missing_from_early_plan" in errors(content, analysis, sections)
    content["phases"][1]["deliverables"] = ["Architecture description"]
    assert "sdlc:v_model_needs_all_levels_planned_before_implementation" in errors(
        content, analysis, sections
    )


def test_unit_pair_cannot_point_to_a_system_only_execution_phase(analysis, sections):
    """Named plan/execution scopes must agree; four labels alone do not establish a V."""
    content = workflow(sections)
    content["phases"][-1]["activities"] = ["Execute independent system and acceptance tests."]
    result = errors(content, analysis, sections)
    assert "sdlc:verification_scope_missing_from_execution_phase" in result
    assert "sdlc:v_model_needs_all_levels_executed_after_implementation" in result

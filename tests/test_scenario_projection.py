"""Derived use cases must not reverse source permissions or invent implementation steps."""

import copy
import threading
import time

import pytest

from cybersrs.evidence import build_evidence
from cybersrs.provider import generation_schema
from cybersrs.scenario_agent import generate_scenarios
from cybersrs.scenario_projection import (
    compose_scenarios,
    scenario_inventory,
    scenario_projection_issues,
    validate_scenario_plan,
)
from cybersrs.schemas import ScenarioProjectionPlan
from cybersrs.validation import assign_ids

from .conftest import requirement
from .test_permission_verification import criterion


@pytest.mark.parametrize("allowed", [["negative"], ["positive", "negative"], ["inspection"]])
def test_native_scenario_schema_keeps_an_atomic_requirement_criterion_primary(allowed):
    """The actual email release interaction cannot lose its sole flow to alternate selection."""
    context = {
        "actor_options": {"FR-007": ["authorized administrators"]},
        "criterion_inventory": [
            {"key": "FR-007/canonical/1", "requirement_id": "FR-007", "allowed_test_types": allowed}
        ],
    }
    native = generation_schema(ScenarioProjectionPlan, context)
    assert native["properties"]["alternate_criterion_keys"].get("maxItems") == 0


@pytest.fixture
def source_view(analysis):
    """Retain the exact source permission, denial and a linked acceptance record."""
    source = (
        "Students and guests may access the internet but must not access "
        "the internal staff network."
    )
    evidence = build_evidence(source, [])
    interpretation = analysis.model_copy(
        update={"stakeholders": ["Students", "Guests"], "assessments": []}
    )
    row = requirement(source, "E-001")
    row["id"] = "FR-001"
    row["acceptance_criteria"] = [
        criterion(
            "A student requests network access",
            "Request internet access",
            "Internet access is granted",
        ),
        criterion(
            "A guest requests network access",
            "Request internal staff-network access",
            "Staff-network access is denied",
        ),
    ]
    extra = criterion(
        "A guest requests network access",
        "Request internet access as the guest",
        "Internet access is granted to the guest",
    )
    sections = {
        "functional": {
            "requirements": [row],
            "related_acceptance_criteria": [
                {
                    "requirement_id": row["id"],
                    "acceptance_criteria": [extra],
                    "evidence_ids": ["E-001"],
                    "sources": [],
                }
            ],
        }
    }
    inventory = scenario_inventory(sections, evidence, interpretation)
    plan = ScenarioProjectionPlan(
        actors=[{"requirement_id": row["id"], "actor": "Students and guests"}],
        alternate_criterion_keys=[inventory["criteria"][1]["key"]],
    )
    return sections, evidence, interpretation, inventory, plan


def test_projection_retains_each_independent_flow_and_exact_denial(source_view):
    """Different success preconditions remain separate cases, and denial is not paraphrased."""
    sections, evidence, analysis, inventory, plan = source_view
    before = copy.deepcopy(sections)
    output = assign_ids("scenarios", compose_scenarios(plan, inventory))
    assert len(output["scenarios"]) == 2
    assert output["scenarios"][0]["goal"] == sections["functional"]["requirements"][0]["statement"]
    assert "Staff-network access is denied" in output["scenarios"][0]["alternate_flows"][0]
    assert output["scenarios"][1]["steps"] == ["Request internet access as the guest"]
    assert scenario_projection_issues(output, sections, evidence, analysis) == []
    assert before == sections


@pytest.mark.parametrize(
    "field,value",
    [
        ("goal", "Allow internet and unrestricted internal staff-network access"),
        ("steps", ["Authenticate through a captive portal"]),
        ("success_outcome", "Display a clear confirmation message"),
    ],
)
def test_independent_projection_check_rejects_new_goal_step_or_result(source_view, field, value):
    sections, evidence, analysis, inventory, plan = source_view
    output = assign_ids("scenarios", compose_scenarios(plan, inventory))
    output["scenarios"][0][field] = value
    assert scenario_projection_issues(output, sections, evidence, analysis)


def test_plan_cannot_invent_actor_drop_primary_or_use_unknown_alternate(source_view):
    _, _, _, inventory, plan = source_view
    wrong = plan.model_copy(deep=True)
    wrong.actors[0].actor = "Administrator"
    assert "scenarios:actor_must_be_literal_linked_source_role" in validate_scenario_plan(
        wrong, inventory
    )
    wrong = plan.model_copy(update={"alternate_criterion_keys": ["FR-999/canonical/1"]})
    assert validate_scenario_plan(wrong, inventory)
    wrong = plan.model_copy(update={"actors": []})
    assert validate_scenario_plan(wrong, inventory)


@pytest.mark.parametrize("repeat_alternate", [False, True])
def test_scenario_agent_asks_model_for_choices_and_composes_source_text(
    source_view, repeat_alternate
):
    sections, evidence, analysis, inventory, plan = source_view

    class Provider:
        """Exercise actual native actor vocabulary and the full composition callback."""

        def generate(self, system, context, schema, cancel, deadline, validate):
            assert schema is ScenarioProjectionPlan
            native = generation_schema(schema, context)
            assert native["properties"]["actors"]["minItems"] == 1
            assert (
                native["$defs"]["ScenarioActorSelection"]["anyOf"][0]["properties"]["actor"]["enum"]
                == inventory["actor_options"]["FR-001"]
            )
            candidate = plan.model_copy(deep=True)
            if repeat_alternate:
                candidate.alternate_criterion_keys *= 2
                assert "scenarios:duplicate_alternate_flow" in validate_scenario_plan(
                    candidate, inventory
                )
            assert validate(candidate) == []
            assert candidate.alternate_criterion_keys == plan.alternate_criterion_keys
            return candidate, {"model": "test-qwen", "attempts": 1}

    result, metadata = generate_scenarios(
        Provider(), {}, evidence, analysis, [], sections, threading.Event(), time.monotonic() + 5
    )
    assert scenario_projection_issues(result, sections, evidence, analysis) == []
    assert metadata["scenario_projection_version"]

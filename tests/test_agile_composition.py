"""Typed cycle generation must preserve authored work and retain independent source gates."""

import threading
import time
from copy import deepcopy

import pytest
from pydantic import ValidationError

from cybersrs.agile_workflow import ITERATION_ACTION_FIELDS, compose_agile_workflow
from cybersrs.evidence import build_evidence
from cybersrs.provider import generation_schema
from cybersrs.schemas import AgileLifecycle, SDLCSection
from cybersrs.sdlc import rank_sdlc
from cybersrs.sdlc_agent import generate_sdlc
from cybersrs.sdlc_validation import validate_lifecycle_structure
from cybersrs.validation import assign_ids

from .conftest import DESCRIPTION, agile_lifecycle_fixture


def test_composition_retains_every_authored_cycle_action_and_public_contract(sections):
    """No template text may replace model actions or unconfirmed stakeholder decisions."""
    source = agile_lifecycle_fixture(sections["sdlc"])
    source["unknown_factors"].append("Release schedule remains undecided.")
    before = deepcopy(source)
    output = compose_agile_workflow(AgileLifecycle.model_validate(source))
    assert source == before
    assert SDLCSection.model_validate(output).model_dump() == output
    assert not validate_lifecycle_structure(output)
    assert output["phases"][1]["activities"] == [
        value for key in ITERATION_ACTION_FIELDS for value in source["iteration"][key]
    ]
    assert output["unknown_factors"] == source["unknown_factors"]
    assert output["verification_pairs"] == []


@pytest.mark.parametrize("field", ITERATION_ACTION_FIELDS)
def test_each_cycle_responsibility_is_required_independently(sections, field):
    """Omitting build, verification or feedback cannot pass as a renamed iteration."""
    content = agile_lifecycle_fixture(sections["sdlc"])
    content["iteration"].pop(field)
    with pytest.raises(ValidationError):
        AgileLifecycle.model_validate(content)


def test_test_only_iteration_and_no_backlog_return_fail_typed_parsing(sections):
    """Reproduce the latest real failure without relying only on native decoder behavior."""
    content = agile_lifecycle_fixture(sections["sdlc"])
    content["iteration"]["implementation_actions"] = ["Execute the verification tests."]
    content["iteration"]["next_iteration_actions"] = ["Release the completed artifact."]
    with pytest.raises(ValidationError) as error:
        AgileLifecycle.model_validate(content)
    locations = {item["loc"][0] for item in error.value.errors()}
    assert locations == {"iteration"}
    assert len(error.value.errors()) == 2


def test_refinements_may_accompany_a_required_actual_return_path(sections):
    """Do not reject additional next-cycle work merely because it does not repeat backlog."""
    content = agile_lifecycle_fixture(sections["sdlc"])
    content["iteration"]["next_iteration_actions"].append(
        "Refine unresolved concurrency choices with stakeholder input."
    )
    assert not validate_lifecycle_structure(
        compose_agile_workflow(AgileLifecycle.model_validate(content))
    )
    content["preparation"]["activities"] = ["Plan the source scope."]
    content["release"]["activities"] = ["Release the reviewed increment."]
    content["iteration"]["next_iteration_actions"].pop(0)
    issues = validate_lifecycle_structure(
        compose_agile_workflow(AgileLifecycle.model_validate(content))
    )
    assert "sdlc:agile_needs_feedback_return_path" in issues


def test_native_cycle_schema_binds_existing_ids_and_proposed_roles():
    """Source operational roles cannot bypass the responsibility distinction in new types."""
    schema = generation_schema(
        AgileLifecycle,
        {
            "sdlc_decision": {"required_model": "Agile"},
            "analysis": {"stakeholders": ["Security operators"]},
            "evidence": [{"id": "E-001", "quote": "Security operators review alerts."}],
            "existing_requirements": [{"id": "FR-001"}],
        },
    )
    for name in ("AgilePreparationPhase", "AgileIterationPhase", "AgileReleasePhase"):
        properties = schema["$defs"][name]["properties"]
        assert properties["roles"]["items"]["anyOf"] == [
            {"type": "string", "pattern": "^[Pp]roposed[ :].+$"}
        ]
        assert properties["requirement_ids"]["items"]["enum"] == ["FR-001"]
    assert schema["properties"]["selected_model"]["const"] == "Agile"
    iteration = schema["$defs"]["AgileIterationPhase"]
    assert set(ITERATION_ACTION_FIELDS) <= set(iteration["required"])


def test_actual_agent_uses_source_groups_and_full_validation(sections, analysis):
    """A model explanation cannot add a quantitative promise to compiled source work."""
    from cybersrs.schemas import LifecycleWorkPlan

    evidence = build_evidence(DESCRIPTION, [])
    predecessors = {name: assign_ids(name, deepcopy(section)) for name, section in sections.items()}

    class CycleProvider:
        """Exercise explanation validation and exact canonical work grouping."""

        def generate(self, system, context, schema, cancel, deadline, validate):
            assert schema is LifecycleWorkPlan
            content = {
                "justification": sections["sdlc"]["justification"],
                "work_groups": [
                    {"requirement_ids": [row["id"] for row in context["existing_requirements"]]}
                ],
            }
            bad = content | {
                "justification": content["justification"] + " Deliver within 500 milliseconds."
            }
            assert any(
                "unsupported_quantitative_commitment" in error
                for error in validate(schema.model_validate(bad))
            )
            result = schema.model_validate(content)
            assert validate(result) == []
            return result, {"model": "test-qwen", "attempts": 1}

    result, provenance = generate_sdlc(
        CycleProvider(),
        {"sdlc_decision": rank_sdlc(evidence)},
        evidence,
        analysis,
        [],
        predecessors,
        threading.Event(),
        time.monotonic() + 10,
    )
    assert result["selected_model"] == rank_sdlc(evidence)["required_model"]
    assert result["phases"][1]["phase_type"] == "design"
    assert "500" not in str(result)
    assert provenance["model"] == "test-qwen"
    assert provenance["lifecycle_projection_version"]

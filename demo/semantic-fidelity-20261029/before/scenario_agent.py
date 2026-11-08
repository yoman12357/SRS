"""Sequential local-model actor/alternate selection for source-preserving use cases."""

from collections.abc import Callable
from threading import Event

from . import prompts
from .provider import GenerationError, LLMProvider
from .scenario_projection import (
    SCENARIO_PROJECTION_VERSION,
    compose_scenarios,
    scenario_inventory,
    validate_scenario_plan,
)
from .schemas import Analysis, Evidence, ScenarioProjectionPlan, SourceChunk
from .validation import assign_ids, validate_section


def generate_scenarios(
    provider: LLMProvider,
    context: dict,
    evidence: list[Evidence],
    analysis: Analysis,
    sources: list[SourceChunk],
    predecessors: dict,
    cancel: Event,
    deadline: float,
    on_rejection: Callable[[dict, list[str]], None] | None = None,
) -> tuple[dict, dict]:
    """Ask for actual source roles and flow grouping; retain exact statements and criteria."""
    inventory = scenario_inventory(predecessors, evidence, analysis)
    if any(not options for options in inventory["actor_options"].values()):
        raise GenerationError("scenarios:source_actor_requires_clarification")

    def compose(plan):
        return assign_ids("scenarios", compose_scenarios(plan, inventory))

    def validate(plan):
        errors = validate_scenario_plan(plan, inventory)
        if errors:
            return errors
        content = compose(plan)
        errors = validate_section("scenarios", content, evidence, analysis, sources, predecessors)
        if errors and on_rejection:
            on_rejection(content, errors)
        return errors

    result, provenance = provider.generate(
        prompts.COMMON + "\nSelect one permitted literal source actor for each supplied "
        "requirement. Identify any existing negative/denied criteria to display as alternate "
        "flows; leave at least one primary criterion per interaction. The server retains "
        "EVERY supplied criterion and composes exact final statements, GIVEN, WHEN and THEN. "
        "Do not write a new goal, authentication step, message, permission or outcome.",
        {
            "assigned_section": "scenarios",
            "actor_options": inventory["actor_options"],
            "criterion_inventory": inventory["criteria"],
            "retry_from_source": True,
        },
        ScenarioProjectionPlan,
        cancel,
        deadline,
        validate,
    )
    return compose(result), provenance | {
        "scenario_projection_version": SCENARIO_PROJECTION_VERSION
    }

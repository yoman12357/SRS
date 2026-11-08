"""Sequential SDLC specialist with source-constrained methodology work compilation."""

from collections.abc import Callable
from threading import Event

from . import prompts
from .lifecycle_projection import (
    LIFECYCLE_PROJECTION_VERSION,
    compose_lifecycle,
    validate_work_groups,
)
from .provider import LLMProvider
from .schemas import Analysis, Evidence, LifecycleWorkPlan, SourceChunk
from .validation import requirements_from, validate_section

SDLC_PROMPT_VERSION = "sequential-sdlc-generation-2.1"


def generate_sdlc(
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
    """Ask local Ollama to explain the ranked winner and group exact canonical work."""
    winner = context["sdlc_decision"]["required_model"]
    requirements = requirements_from(predecessors)

    def compose(plan):
        return compose_lifecycle(
            plan, winner, requirements, predecessors.get("verification", {}), evidence, analysis
        )

    def validate(plan):
        errors = validate_work_groups(plan, requirements)
        if errors:
            return errors
        content = compose(plan)
        errors = validate_section("sdlc", content, evidence, analysis, sources, predecessors)
        if errors and on_rejection:
            on_rejection(content, errors)
        return errors

    result, provenance = provider.generate(
        prompts.COMMON + "\nExplain only the exact required_model using the ranked evidence "
        "factors. Distinguish explicit delivery facts from derived product-based suitability. "
        "Explain the winning factors and the closest alternative. Treat derived-only "
        "recommendations as provisional. Acknowledge unknown factors and tradeoffs "
        "without claiming other methods "
        "cannot adapt. Scores are suitability points, not probabilities. Do not invent "
        "technologies, thresholds, cadence, regulations or approval authorities. Group "
        "related supplied requirement IDs; include each ID exactly once. The coordinator "
        "composes methodology phases, exact tasks, actual test references, proposed roles "
        "and pending human gates. Return only the explanation and ID groups.",
        {
            "assigned_section": "sdlc",
            "sdlc_decision": context["sdlc_decision"],
            "existing_requirements": [
                {"id": row["id"], "statement": row["statement"]} for row in requirements
            ],
            "retry_from_source": True,
        },
        LifecycleWorkPlan,
        cancel,
        deadline,
        validate,
    )
    return compose(result), provenance | {
        "sdlc_prompt_version": SDLC_PROMPT_VERSION,
        "lifecycle_projection_version": LIFECYCLE_PROJECTION_VERSION,
    }

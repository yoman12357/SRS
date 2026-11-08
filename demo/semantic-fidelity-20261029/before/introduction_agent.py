"""Ask the local specialist to organize evidence, retaining source statements exactly."""

from collections.abc import Callable
from threading import Event

from . import prompts
from .introduction_projection import (
    INTRODUCTION_PROJECTION_VERSION,
    compose_introduction,
    validate_introduction_order,
)
from .provider import LLMProvider
from .schemas import Analysis, Evidence, SourceChunk, SourceIntroductionPlan
from .validation import validate_section


def generate_introduction(
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
    """Generate a complete fact order and validate the composed public narrative."""

    def validate(plan: SourceIntroductionPlan) -> list[str]:
        errors = validate_introduction_order(plan, evidence)
        if errors:
            return errors
        content = compose_introduction(plan, evidence, analysis)
        errors = validate_section(
            "introduction", content, evidence, analysis, sources, predecessors
        )
        if errors and on_rejection:
            on_rejection(content, errors)
        return errors

    result, provenance = provider.generate(
        prompts.COMMON + "\nOrganize ALL supplied source evidence for an SRS introduction. "
        "Return each existing evidence ID exactly once: purpose/scope first, stakeholder "
        "behavior and constraints next, exclusions and unresolved decisions clearly retained. "
        "Return only evidence_order. The server retains exact source statements and answer "
        "context; do not paraphrase, add facts or remove inconvenient constraints.",
        {"assigned_section": "introduction", "evidence": [item.model_dump() for item in evidence]},
        SourceIntroductionPlan,
        cancel,
        deadline,
        validate,
    )
    return compose_introduction(result, evidence, analysis), provenance | {
        "introduction_projection_version": INTRODUCTION_PROJECTION_VERSION
    }

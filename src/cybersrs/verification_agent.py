"""Classify complete acceptance inventories with the local model, then preserve their text."""

from collections.abc import Callable
from threading import Event
from typing import Literal

from pydantic import create_model

from . import prompts
from .provider import LLMProvider
from .schemas import Analysis, Evidence, SourceChunk, StrictModel, VerificationPlan
from .validation import assign_ids, validate_section
from .verification_projection import (
    VERIFICATION_PROJECTION_VERSION,
    compose_verification,
    criterion_inventory,
    validate_verification_choices,
)

VERIFICATION_SELECTION_VERSION = "source-keyed-types-1.0"


def generate_verification(
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
    """Ask for classifications only; independently validate all composed source-linked tests."""
    inventory = criterion_inventory(predecessors)
    selection_schema = create_model(
        "CanonicalVerificationTypes",
        __base__=StrictModel,
        **{item["key"]: (Literal[tuple(item["allowed_test_types"])], ...) for item in inventory},
    )

    def public_plan(selection: StrictModel) -> VerificationPlan:
        """Project one constrained choice per key without duplicate or missing list identities."""
        return VerificationPlan.model_validate(
            {
                "choices": [
                    {"criterion_key": key, "test_type": value}
                    for key, value in selection.model_dump().items()
                ]
            }
        )

    def compose(plan: VerificationPlan) -> dict:
        return assign_ids("verification", compose_verification(plan, inventory))

    def validate(selection: StrictModel) -> list[str]:
        plan = public_plan(selection)
        errors = validate_verification_choices(plan, inventory)
        if errors:
            return errors
        content = compose(plan)
        errors = validate_section(
            "verification", content, evidence, analysis, sources, predecessors
        )
        if errors and on_rejection:
            on_rejection(content, errors)
        return errors

    result, provenance = provider.generate(
        prompts.COMMON + "\nClassify EVERY frozen acceptance criterion once using its key. "
        "Choose a permitted test_type: positive success, negative denial/exclusion, or "
        "boundary behavior at a stated limit. Preserve inspection/analysis methods. "
        "Return the exact keyed object: each supplied key has one permitted type value. "
        "The server retains every authored GIVEN, WHEN, THEN and "
        "evidence string; do not rewrite behavior or invent tests, outcomes or execution results.",
        {"assigned_section": "verification", "criterion_inventory": inventory},
        selection_schema,
        cancel,
        deadline,
        validate,
    )
    return compose(public_plan(result)), provenance | {
        "verification_projection_version": VERIFICATION_PROJECTION_VERSION,
        "verification_selection_version": VERIFICATION_SELECTION_VERSION,
    }

"""Preserve authored cycle actions in the existing canonical lifecycle representation."""

from .schemas import AgileLifecycle, SDLCSection

ITERATION_ACTION_FIELDS = (
    "planning_actions",
    "implementation_actions",
    "verification_actions",
    "feedback_actions",
    "next_iteration_actions",
)


def compose_agile_workflow(lifecycle: AgileLifecycle) -> dict:
    """Flatten typed activities verbatim; add only the fixed iteration phase category."""
    iteration = lifecycle.iteration.model_dump()
    actions = [action for key in ITERATION_ACTION_FIELDS for action in iteration.pop(key)]
    iteration.update(phase_type="iteration", activities=actions)
    return SDLCSection(
        selected_model=lifecycle.selected_model,
        justification=lifecycle.justification,
        tradeoffs=lifecycle.tradeoffs,
        phases=[lifecycle.preparation.model_dump(), iteration, lifecycle.release.model_dump()],
        unknown_factors=lifecycle.unknown_factors,
        verification_pairs=[],
    ).model_dump()

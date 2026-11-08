"""Deterministic V-model phase ordering and early test-plan relationships."""

import re

TEST_SCOPES = {"unit", "integration", "system", "acceptance"}
PHASE_TYPES = {
    "planning",
    "design",
    "implementation",
    "verification",
    "release",
    "iteration",
    "operations",
}


def confirmed_delivery_roles(
    source: str, roles: list[str], phase_type: str | None = None
) -> list[str]:
    """Recognize explicit project responsibility rather than a product user's existence."""
    objects = {
        "planning": r"requirements?|plans?|sdlc",
        "design": r"design|architecture",
        "implementation": r"implementation|code|components?",
        "verification": r"tests|test results?|test plans?|verification",
        "release": r"release|deployment",
        "operations": r"operations|maintenance",
    }
    target = objects.get(phase_type, "|".join(objects.values()))
    result = []
    for role in roles:
        pattern = (
            rf"\b{re.escape(role)}\b[^.;!?]{{0,45}}"
            r"\b(?:approv\w*|review\w*|implement\w*|develop\w*)\b"
            rf"[^.;!?]{{0,55}}\b(?:{target})\b"
        )
        for match in re.finditer(pattern, source, re.I):
            prefix = re.split(r"[.;!?]", source[: match.start()])[-1]
            if re.search(r"\b(?:no|not|never)\s*$", prefix, re.I):
                continue
            if re.search(r"\b(?:not|never|cannot|can't|mustn't|shouldn't)\b", match[0], re.I):
                continue
            result.append(role)
            break
    return result


def validate_lifecycle_structure(content: dict) -> list[str]:
    """Require typed phases and the actual iterative behavior of an Agile workflow."""
    issues = []
    phases = content["phases"]
    if any(phase.get("phase_type") not in PHASE_TYPES for phase in phases):
        issues.append("sdlc:phase_type_required")
    if content["selected_model"] != "V-Model" and content.get("verification_pairs"):
        issues.append("sdlc:non_v_workflow_must_not_claim_v_pairs")
    if content["selected_model"] != "Agile":
        return issues
    iterations = [phase for phase in phases if phase.get("phase_type") == "iteration"]
    iterative_work = " ".join(text for phase in iterations for text in phase["activities"])
    if not iterations or not (
        re.search(r"\b(?:implement\w*|build\w*|develop\w*|deliver\w*)\b", iterative_work, re.I)
        and re.search(r"\b(?:test\w*|verif\w*)\b", iterative_work, re.I)
    ):
        issues.append("sdlc:agile_needs_implementation_and_verification_within_iteration")
    workflow = " ".join(text for phase in phases for text in phase["activities"])
    feedback = re.search(r"\b(?:feedback|stakeholder review)\b", workflow, re.I)
    return_path = re.search(
        r"\bnext (?:sprint|iteration|increment)\b|"
        r"\b(?:return|loop|back)\b.{0,65}\b(?:backlog|planning|iteration|sprint)\b|"
        r"\brepeat\w*\b.{0,35}\b(?:iteration|sprint|cycle)\b",
        workflow,
        re.I,
    )
    if not feedback or not return_path:
        issues.append("sdlc:agile_needs_feedback_return_path")
    return issues


def plan_test_scopes(text: str) -> set[str]:
    """Read the explicitly named verification levels of a planning artifact."""
    return {scope for scope in TEST_SCOPES if re.search(rf"\b{scope}\b", text, re.I)}


def phase_test_scopes(phase: dict) -> set[str]:
    """Read actual execution levels from the frozen phase's declared activities."""
    if "test_scopes" in phase:
        return set(phase["test_scopes"]) & TEST_SCOPES
    return plan_test_scopes(" ".join([phase["name"], *phase["activities"], *phase["deliverables"]]))


def is_test_plan(deliverable: str) -> bool:
    """Distinguish a named planning artifact from an individual test identifier."""
    return bool(
        re.search(r"\b(?:test|testing|verification|validation|acceptance)\b", deliverable, re.I)
        and re.search(r"\b(?:plan|strategy)\b", deliverable, re.I)
    )


def early_plans(phases: list[dict]) -> list[tuple[str, str]]:
    """Return named test plans authored in planning/design before implementation."""
    first_build = next(
        (i for i, phase in enumerate(phases) if phase.get("phase_type") == "implementation"),
        len(phases),
    )
    return [
        (phase["name"], plan)
        for phase in phases[:first_build]
        if phase.get("phase_type") in {"planning", "design"}
        for plan in phase["deliverables"]
        if is_test_plan(plan)
    ]


def validate_v_model(content: dict, known: set[str], *, require_pairs: bool = True) -> list[str]:
    """Require early plans, implementation, later tests and complete V relationships."""
    phases = content["phases"]
    by_name = {phase["name"]: phase for phase in phases}
    order = {phase["name"]: i for i, phase in enumerate(phases)}
    issues: list[str] = []
    if len(by_name) != len(phases):
        issues.append("sdlc:phase_names_must_be_unique")
    if any(not phase.get("phase_type") for phase in phases):
        issues.append("sdlc:v_model_needs_phase_types")
    builds = [i for i, phase in enumerate(phases) if phase.get("phase_type") == "implementation"]
    if not builds:
        issues.append("sdlc:v_model_needs_implementation_phase")
    if not early_plans(phases):
        issues.append("sdlc:v_model_needs_early_test_plans")
    planned = {scope for _, plan in early_plans(phases) for scope in plan_test_scopes(plan)}
    if planned != TEST_SCOPES:
        issues.append("sdlc:v_model_needs_all_levels_planned_before_implementation")
    executed = {
        scope
        for i, phase in enumerate(phases)
        if phase.get("phase_type") == "verification" and builds and i > max(builds)
        for scope in phase_test_scopes(phase)
    }
    if executed != TEST_SCOPES:
        issues.append("sdlc:v_model_needs_all_levels_executed_after_implementation")
    if not any(
        phase.get("phase_type") == "verification" and builds and i > max(builds)
        for i, phase in enumerate(phases)
    ):
        issues.append("sdlc:v_model_needs_verification_after_implementation")
    if not require_pairs:
        return issues
    pairs = content.get("verification_pairs", [])
    if not pairs:
        issues.append("sdlc:v_model_needs_explicit_verification_pairs")
    scopes = {pair["test_scope"] for pair in pairs}
    if "acceptance" not in scopes or not scopes.intersection({"unit", "integration", "system"}):
        issues.append("sdlc:v_model_needs_acceptance_and_technical_pairing")
    if scopes != {"unit", "integration", "system", "acceptance"}:
        issues.append("sdlc:v_model_needs_all_test_levels")
    eligible = set(early_plans(phases))
    for pair in pairs:
        left, right = pair["development_phase"], pair["verification_phase"]
        if left not in by_name or right not in by_name:
            issues.append("sdlc:verification_pair_unknown_phase")
            continue
        if order[left] >= order[right]:
            issues.append("sdlc:verification_plan_must_precede_execution")
        if pair["test_plan_deliverable"] not in by_name[left]["deliverables"]:
            issues.append("sdlc:verification_plan_missing_from_development_deliverables")
        if (left, pair["test_plan_deliverable"]) not in eligible:
            issues.append("sdlc:verification_plan_must_be_early_planning_artifact")
        if pair["test_scope"] not in plan_test_scopes(pair["test_plan_deliverable"]):
            issues.append("sdlc:verification_scope_missing_from_early_plan")
        if pair["test_scope"] not in phase_test_scopes(by_name[right]):
            issues.append("sdlc:verification_scope_missing_from_execution_phase")
        if (
            by_name[right].get("phase_type") != "verification"
            or not builds
            or order[right] <= max(builds)
        ):
            issues.append("sdlc:verification_pair_needs_post_implementation_test_phase")
    mapped = {rid for pair in pairs for rid in pair["requirement_ids"]}
    issues.extend(f"{rid}:missing_v_model_pair_coverage" for rid in sorted(known - mapped))
    return issues

"""Lossless user-story and use-case views of final actor-visible acceptance flows."""

import re
from copy import deepcopy

from .architecture_sources import source_actor_contracts
from .schemas import Analysis, Evidence, ScenarioProjectionPlan, ScenarioSection
from .source_detail_policy import nonhuman_role_modifier
from .verification_projection import criterion_inventory

SCENARIO_PROJECTION_VERSION = "canonical-scenarios-1.0"


def scenario_inventory(sections: dict, evidence: list[Evidence], analysis: Analysis) -> dict:
    """Retain source role choices, final statements and every applicable authored criterion."""
    from .validation import interactive_requirement_ids, requirements_from

    requirements = requirements_from(sections)
    required = interactive_requirement_ids(requirements, analysis)
    roles = source_actor_contracts(evidence, requirements)
    options = {}
    for row in requirements:
        if row["id"] not in required:
            continue
        actors = {role["actor"] for role in roles if row["id"] in role["requirement_ids"]}
        # A literal source role can still be used for verbs outside the narrow
        # access-contract parser. Never take a newly invented analysis role as fact.
        for stakeholder in [] if actors else analysis.stakeholders:
            words = re.findall(r"[A-Za-z]+", stakeholder)
            if not words:
                continue
            pattern = r"\b" + r"\s+".join(re.escape(w.rstrip("s")) + "s?" for w in words) + r"\b"
            head = re.escape(words[-1].rstrip("s"))
            restriction = rf"\bonly\s+for\s+(?:the|an?)\s+((?:[A-Za-z-]+\s+){{0,3}}{head}s?)\b"
            permitted = re.search(restriction, row["statement"], re.I)
            for fact in evidence:
                if fact.id not in row["evidence_ids"]:
                    continue
                if re.search(pattern, row["statement"], re.I):
                    match = re.search(pattern, fact.quote, re.I)
                    if match and not nonhuman_role_modifier(fact.quote, match.start(), match.end()):
                        actors.add(match[0])
                if permitted:
                    match = re.search(restriction, fact.quote, re.I)
                    if (
                        match
                        and match[1].casefold() == permitted[1].casefold()
                        and not nonhuman_role_modifier(fact.quote, match.start(1), match.end(1))
                    ):
                        actors.add(match[1])
        options[row["id"]] = sorted(actors)
    return {
        "requirements": [deepcopy(row) for row in requirements if row["id"] in required],
        "actor_options": options,
        "criteria": [
            item for item in criterion_inventory(sections) if item["requirement_id"] in required
        ],
    }


def validate_scenario_plan(plan: ScenarioProjectionPlan, inventory: dict) -> list[str]:
    """Require actual source actors and complete nonduplicated flow coverage."""
    errors = []
    known = inventory["actor_options"]
    selected = [item.requirement_id for item in plan.actors]
    if len(selected) != len(set(selected)) or set(selected) != set(known):
        errors.append("scenarios:actor_selection_must_cover_each_interaction_once")
    for item in plan.actors:
        if item.actor not in known.get(item.requirement_id, []):
            errors.append("scenarios:actor_must_be_literal_linked_source_role")
    criteria = {item["key"]: item for item in inventory["criteria"]}
    alternates = plan.alternate_criterion_keys
    if len(alternates) != len(set(alternates)):
        errors.append("scenarios:duplicate_alternate_flow")
    for key in alternates:
        if key not in criteria or "negative" not in criteria[key]["allowed_test_types"]:
            errors.append("scenarios:alternate_must_be_existing_denied_flow")
    for rid in known:
        keys = {item["key"] for item in inventory["criteria"] if item["requirement_id"] == rid}
        if not keys - set(alternates):
            errors.append("scenarios:interaction_requires_a_primary_flow")
    return sorted(set(errors))


def _flow_text(item: dict) -> str:
    """Preserve a complete alternate's conditions, action, outcome and observable evidence."""
    criterion = item["criterion"]
    return " ".join(
        label + criterion[field]
        for label, field in (
            ("Given: ", "given"),
            ("When: ", "when"),
            ("Then: ", "then"),
            ("Evidence: ", "observable_evidence"),
        )
    )


def compose_scenarios(plan: ScenarioProjectionPlan, inventory: dict) -> dict:
    """Compose each independent primary flow and retain denied flows without new prose claims."""
    issues = validate_scenario_plan(plan, inventory)
    if issues:
        raise ValueError(";".join(issues))
    actors = {item.requirement_id: item.actor for item in plan.actors}
    alternates = set(plan.alternate_criterion_keys)
    result, unresolved = [], []
    for row in inventory["requirements"]:
        items = [item for item in inventory["criteria"] if item["requirement_id"] == row["id"]]
        primary = [item for item in items if item["key"] not in alternates]
        for index, item in enumerate(primary):
            criterion = item["criterion"]
            result.append(
                {
                    "actor": actors[row["id"]],
                    "goal": row["statement"],
                    "story": (
                        f"As {actors[row['id']]}, I need the following behavior: "
                        + row["statement"]
                    ),
                    "preconditions": [criterion["given"]],
                    "steps": [criterion["when"]],
                    "success_outcome": criterion["then"],
                    "alternate_flows": [
                        _flow_text(alt) for alt in items if alt["key"] in alternates
                    ]
                    if index == 0
                    else [],
                    "requirement_ids": [row["id"]],
                    "evidence_ids": row["evidence_ids"],
                    "unresolved_decisions": row["unresolved_decisions"],
                }
            )
        unresolved.extend(row["unresolved_decisions"])
    return ScenarioSection(
        scenarios=result, open_issues=list(dict.fromkeys(unresolved))
    ).model_dump()


def scenario_projection_issues(
    content: dict, sections: dict, evidence: list[Evidence], analysis: Analysis
) -> list[str]:
    """Check every claimed automatic view against the current canonical source strings."""
    inventory = scenario_inventory(sections, evidence, analysis)
    actors, alternate_keys = {}, []
    criteria = inventory["criteria"]
    for scenario in content["scenarios"]:
        if len(scenario["requirement_ids"]) != 1:
            return ["scenarios:canonical_projection_mismatch"]
        rid = scenario["requirement_ids"][0]
        if rid in actors and actors[rid] != scenario["actor"]:
            return ["scenarios:canonical_projection_mismatch"]
        actors[rid] = scenario["actor"]
        for flow in scenario["alternate_flows"]:
            matches = [
                item["key"]
                for item in criteria
                if item["requirement_id"] == rid and _flow_text(item) == flow
            ]
            if len(matches) != 1:
                return ["scenarios:canonical_projection_mismatch"]
            alternate_keys.append(matches[0])
    plan = ScenarioProjectionPlan(
        actors=[{"requirement_id": rid, "actor": actor} for rid, actor in actors.items()],
        alternate_criterion_keys=alternate_keys,
    )
    errors = validate_scenario_plan(plan, inventory)
    if errors:
        return errors
    expected = compose_scenarios(plan, inventory)
    actual = deepcopy(content)
    for scenario in actual["scenarios"]:
        scenario["id"] = ""
    return [] if actual == expected else ["scenarios:canonical_projection_mismatch"]

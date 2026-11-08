"""Local model proposes logical layout; source-backed composition preserves every obligation."""

from __future__ import annotations

from collections.abc import Callable
from threading import Event
from typing import Literal

from pydantic import Field, create_model

from . import prompts
from .architecture_layout import render_component_layout, render_interaction_layout, source_unknowns
from .architecture_normalization import preserve_architecture_timing
from .architecture_paths import compile_source_paths, internal_pair_obligations
from .architecture_sources import (
    SOURCE_ACCESS_OVERVIEW,
    all_source_endpoint_components,
    source_access_contracts,
    source_actor_architecture_issues,
    source_actor_contracts,
)
from .provider import GenerationError, LLMProvider
from .schemas import (
    Analysis,
    ArchitectureInternalInteractions,
    ArchitectureLayoutComponents,
    ArchitectureOwnership,
    ArchitectureSection,
    Evidence,
    SourceChunk,
    StrictModel,
)
from .validation import requirements_from, validate_section

LAYOUT_VERSION = "source-backed-layout-1.1"
OWNERSHIP_SELECTION_VERSION = "source-keyed-owners-1.0"


def _owner_plan(selection: StrictModel, multiple: bool) -> ArchitectureOwnership:
    """Project required ID keys into existing owner links without losing shared ownership."""
    return ArchitectureOwnership(
        links=[
            {"requirement_id": rid, "component_name": name}
            for rid, values in selection.model_dump().items()
            for name in (values if multiple else [values])
        ]
    )


def generate_architecture(
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
    """Generate substantive layout decisions without rewriting canonical duties or source actors."""
    rows = requirements_from(predecessors)
    canonical = {row["id"]: row for row in rows}
    if not canonical:
        raise GenerationError("architecture_requires_source_backed_requirements")
    access = source_access_contracts(evidence, rows)
    roles = source_actor_contracts(evidence, rows)
    frozen = all_source_endpoint_components(access, roles)
    frozen_names = {node["component_name"] for node in frozen}
    unknowns = source_unknowns(evidence)
    compact = [{key: row[key] for key in ("id", "statement", "evidence_ids")} for row in rows]
    supplied = {
        "assigned_section": "architecture",
        "task": "proposed_logical_layout_only",
        "existing_requirements": compact,
        "source_endpoint_components": [
            {key: node[key] for key in ("component_name", "requirement_ids")} for node in frozen
        ],
        "source_access_contracts": access,
        "source_actor_contracts": roles,
        "unresolved_source_decisions": unknowns,
    }

    def compose_components(placement: list[dict]) -> dict:
        """Render a source-backed inventory without any free-text product commitments."""
        return ArchitectureSection.model_validate(
            {
                "summary": SOURCE_ACCESS_OVERVIEW
                if access
                else (
                    "Proposed logical components and interactions mapped to "
                    "canonical source obligations."
                ),
                "items": frozen + render_component_layout(placement, canonical),
                "data_flows": [],
                "trust_boundaries": [],
                "open_issues": unknowns,
            }
        ).model_dump()

    def validate_components(candidate: ArchitectureLayoutComponents) -> list[str]:
        """Check grouping identity and all inventory gates before deciding any edges."""
        for component in candidate.components:
            if set(component.requirement_ids) - canonical.keys():
                return ["architecture:unknown_requirement_ids"]
            ids = {
                eid for rid in component.requirement_ids for eid in canonical[rid]["evidence_ids"]
            }
            normalized = preserve_architecture_timing(
                {
                    "items": [
                        {"component_name": component.component_name, "evidence_ids": sorted(ids)}
                    ],
                    "open_issues": [],
                },
                evidence,
            )
            component.component_name = normalized["items"][0]["component_name"]
        names = [item.component_name for item in candidate.components]
        if len(names) != len(set(name.casefold() for name in names)):
            return ["architecture:component_names_must_be_nonempty_and_unique"]
        if any(name in frozen_names for name in names):
            return ["architecture:implementation_component_required"]
        if any(set(item.requirement_ids) - canonical.keys() for item in candidate.components):
            return ["architecture:unknown_requirement_ids"]
        draft = compose_components([item.model_dump() for item in candidate.components])
        errors = [
            issue
            for issue in validate_section(
                "architecture", draft, evidence, analysis, sources, predecessors
            )
            if issue
            not in {"architecture:missing_data_flows", "architecture:missing_trust_boundaries"}
            and not issue.endswith(":missing_architecture_coverage")
        ]
        if errors and on_rejection:
            on_rejection(draft, errors)
        return errors

    layout, first = provider.generate(
        prompts.COMMON + "\nPropose only an implementation-component layout. Name logical "
        "implementation blocks and assign their existing canonical requirement IDs. "
        "Return the typed components list only; do not author responsibilities, source "
        "metadata, new capabilities or an SRS section. The coordinator renders exact "
        "canonical responsibility text and includes frozen source actor/resource nodes. "
        "Do not return those source nodes as implementation blocks. An exclusion belongs "
        "to an owner's constraints, not an automation engine executing excluded actions.",
        supplied,
        ArchitectureLayoutComponents,
        cancel,
        deadline,
        validate_components,
    )
    placements = [item.model_dump() for item in layout.components]
    stages = [{"stage": "components", **first}]
    names = [item["component_name"] for item in placements]
    owned = {rid for item in placements for rid in item["requirement_ids"]}
    missing = canonical.keys() - owned
    if missing:
        ownership_schema = create_model(
            "ArchitectureOwnerAssignments",
            __base__=StrictModel,
            **{
                rid: (
                    list[Literal[tuple(names)]],
                    Field(
                        min_length=1, max_length=len(names), json_schema_extra={"uniqueItems": True}
                    ),
                )
                for rid in sorted(missing)
            },
        )

        def validate_owners(selection: StrictModel) -> list[str]:
            """Cover every missing obligation with distinct existing component links."""
            candidate = _owner_plan(selection, True)
            ids = [link.requirement_id for link in candidate.links]
            pairs = [(link.requirement_id, link.component_name) for link in candidate.links]
            if set(ids) != missing or len(pairs) != len(set(pairs)):
                return ["architecture:ownership_requires_complete_distinct_links"]
            if any(link.component_name not in names for link in candidate.links):
                return ["architecture:ownership_requires_existing_implementation_component"]
            return []

        owners, metadata = provider.generate(
            prompts.COMMON + "\nAssign each missing canonical obligation to existing "
            "implementation blocks. Shared duties may have multiple distinct owners. "
            "A prohibition constrains its owner; it is not an "
            "execution path. Return the exact keyed object: every required ID maps to "
            "one or more distinct existing component names.",
            {
                "assigned_section": "architecture",
                "existing_requirements": [r for r in compact if r["id"] in missing],
                "implementation_component_names": names,
                "implementation_components": placements,
            },
            ownership_schema,
            cancel,
            deadline,
            validate_owners,
        )
        owners = _owner_plan(owners, True)
        by_name = {item["component_name"]: item for item in placements}
        for owner in owners.links:
            by_name[owner.component_name]["requirement_ids"].append(owner.requirement_id)
        stages.append(
            {"stage": "ownership", "selection_version": OWNERSHIP_SELECTION_VERSION, **metadata}
        )
    inventory = compose_components(placements)
    required = {rid for contract in roles + access for rid in contract["requirement_ids"]}
    options = {
        rid: [item["component_name"] for item in placements if rid in item["requirement_ids"]]
        for rid in sorted(required)
    }
    routes = {rid: choices[0] for rid, choices in options.items() if len(choices) == 1}
    ambiguous = {rid: choices for rid, choices in options.items() if len(choices) > 1}
    if ambiguous:
        routing_schema = create_model(
            "ArchitectureRouteChoices",
            __base__=StrictModel,
            **{rid: (Literal[tuple(choices)], ...) for rid, choices in ambiguous.items()},
        )

        def validate_routes(selection: StrictModel) -> list[str]:
            """Route each shared source responsibility through an actual model-assigned owner."""
            candidate = _owner_plan(selection, False)
            ids = [link.requirement_id for link in candidate.links]
            if set(ids) != set(ambiguous) or len(ids) != len(set(ids)):
                return ["architecture:routing_must_select_each_shared_requirement_once"]
            if any(
                link.component_name not in ambiguous[link.requirement_id]
                for link in candidate.links
            ):
                return ["architecture:route_owner_must_own_requirement"]
            return []

        selected, metadata = provider.generate(
            prompts.COMMON + "\nChoose one responsible request/decision owner for each "
            "shared canonical obligation. Select only an existing component that already "
            "owns that ID. Source role requests and access-decision paths will be compiled "
            "through this owner. Return the exact keyed object: one owning component per ID.",
            {
                "assigned_section": "architecture",
                "existing_requirements": [row for row in compact if row["id"] in ambiguous],
                "implementation_component_names": names,
                "implementation_components": placements,
                "route_owner_choices": ambiguous,
            },
            routing_schema,
            cancel,
            deadline,
            validate_routes,
        )
        selected = _owner_plan(selected, False)
        routes.update({link.requirement_id: link.component_name for link in selected.links})
        stages.append(
            {"stage": "routing", "selection_version": OWNERSHIP_SELECTION_VERSION, **metadata}
        )
    compiled = compile_source_paths(roles, access, routes)
    permitted = internal_pair_obligations(placements, canonical)

    def compose_graph(candidate: ArchitectureInternalInteractions) -> dict:
        """Keep required source paths intact while adding only validated internal proposals."""
        combined = {
            "data_flows": compiled["data_flows"]
            + [item.model_dump() for item in candidate.data_flows],
            "trust_boundaries": compiled["trust_boundaries"]
            + [item.model_dump() for item in candidate.trust_boundaries],
        }
        return inventory | render_interaction_layout(combined, canonical, access)

    def validate_internal(candidate: ArchitectureInternalInteractions) -> list[str]:
        """Internal proposals cannot replace source paths or couple unrelated obligations."""
        for item in candidate.data_flows + candidate.trust_boundaries:
            origin = getattr(item, "from_component", getattr(item, "untrusted_component", ""))
            target = getattr(item, "to_component", getattr(item, "trusted_component", ""))
            if (origin, target) not in permitted or set(item.requirement_ids) - permitted[
                (origin, target)
            ]:
                return ["architecture:internal_pair_requires_shared_or_dependent_obligations"]
        draft = compose_graph(candidate)
        errors = validate_section("architecture", draft, evidence, analysis, sources, predecessors)
        errors += source_actor_architecture_issues(draft, roles)
        errors = list(dict.fromkeys(errors))
        if errors and on_rejection:
            on_rejection(draft, errors)
        return errors

    internal = ArchitectureInternalInteractions()
    if permitted:
        internal, metadata = provider.generate(
            prompts.COMMON + "\nMandatory source role and access-decision paths are already "
            "compiled from the chosen responsibility owners. Propose only necessary "
            "additional internal endpoint pairs from permitted_internal_pairs. Use their "
            "shared or declared dependent canonical IDs. Empty lists are valid when no "
            "additional interaction is needed. Do not return source actor/resource paths "
            "or invent new behavior, controls or metadata.",
            supplied
            | {
                "architecture_component_names": names,
                "implementation_components": placements,
                "compiled_source_paths": compiled,
                "permitted_internal_pairs": [
                    {
                        "from_component": origin,
                        "to_component": target,
                        "requirement_ids": sorted(ids),
                    }
                    for (origin, target), ids in permitted.items()
                ],
                "requires_internal_flows": not compiled["data_flows"],
                "requires_internal_boundaries": not compiled["trust_boundaries"],
            },
            ArchitectureInternalInteractions,
            cancel,
            deadline,
            validate_internal,
        )
        stages.append({"stage": "internal_interactions", **metadata})
    final_errors = validate_internal(internal)
    if final_errors:
        raise GenerationError("architecture_layout_invalid:" + ";".join(final_errors))
    content = compose_graph(internal)
    models = sorted(
        {model for stage in stages for model in stage.get("output_models", [stage["model"]])}
    )
    return content, {
        "model": " + ".join(models),
        "output_models": models,
        "attempts": sum(stage["attempts"] for stage in stages),
        "elapsed_seconds": round(sum(stage.get("elapsed_seconds", 0) for stage in stages), 3),
        "architecture_stages": stages,
        "architecture_layout_version": LAYOUT_VERSION,
        "source_paths_compiled": True,
    }

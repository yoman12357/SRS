"""Sequential local specialists select defensible source-derived advisory candidates."""

from collections.abc import Callable
from threading import Event

from . import prompts
from .advisory_candidates import (
    HYPOTHESIS_NOTICE,
    SOURCE_ADVISORY_VERSION,
    glossary_candidates,
    risk_candidates,
    threat_candidates,
)
from .provider import LLMProvider
from .schemas import SECTION_SCHEMAS, Analysis, Evidence, SourceCandidatePlan, SourceChunk
from .validation import assign_ids, requirements_from, validate_section


def _generate(
    name: str,
    provider: LLMProvider,
    context: dict,
    evidence: list[Evidence],
    analysis: Analysis,
    sources: list[SourceChunk],
    predecessors: dict,
    cancel: Event,
    deadline: float,
    on_rejection: Callable | None,
) -> tuple[dict, dict]:
    """Keep the model's selection distinct from deterministic source-linked descriptions."""
    candidates = (
        threat_candidates(evidence, requirements_from(predecessors))
        if name == "threats"
        else risk_candidates(evidence, analysis, predecessors.get("threats", {}))
        if name == "risks"
        else glossary_candidates(evidence)
    )
    by_key = {item["key"]: item["content"] for item in candidates}
    unknown_ids = {
        item.evidence_id for item in analysis.assessments if item.kind in {"uncertain", "conflict"}
    }
    unknowns = [item.quote for item in evidence if item.id in unknown_ids]

    def compose(plan):
        keys = list(plan.candidate_keys)
        if name in {"threats", "risks"}:
            keys += [key for key in by_key if key not in keys]
        selected = [by_key[key] for key in keys]
        if name == "threats":
            content = {"threats": selected, "assumptions": [HYPOTHESIS_NOTICE]}
        elif name == "risks":
            content = {"risks": selected, "open_issues": unknowns}
        else:
            content = {
                "summary": (
                    "Source-present terminology; definitions introduce no additional "
                    "product obligation."
                ),
                "items": selected,
                "open_issues": unknowns,
            }
        return assign_ids(name, SECTION_SCHEMAS[name].model_validate(content).model_dump())

    def validate(plan):
        keys = plan.candidate_keys
        if len(keys) != len(set(keys)) or set(keys) - set(by_key):
            return [name + ":candidate_selection_must_be_unique_and_known"]
        if candidates and not keys and name == "glossary":
            return [name + ":select_applicable_source_candidates"]
        content = compose(plan)
        errors = validate_section(name, content, evidence, analysis, sources, predecessors)
        if errors and on_rejection:
            on_rejection(content, errors)
        return errors

    result, provenance = provider.generate(
        prompts.COMMON + "\nOrder the applicable supplied candidates for " + name + ". "
        "Return candidate keys only. Consider the supplied source-linked hypotheses/definitions, "
        "not normal permitted activity as attack. Do not invent controls, ratings, actors, "
        "mitigations, regulations or decisions. Include the applicable material candidates.",
        {
            "assigned_section": name,
            "candidate_inventory": candidates,
            "retry_from_source": True,
            "design_context": context.get("design_context"),
        },
        SourceCandidatePlan,
        cancel,
        deadline,
        validate,
    )
    return compose(result), provenance | {
        "source_advisory_version": SOURCE_ADVISORY_VERSION,
        "model_candidate_order": result.candidate_keys,
        "retained_source_candidates": list(by_key)
        if name in {"threats", "risks"}
        else result.candidate_keys,
        "composition": "Deterministic source-linked hypotheses; model orders candidates",
    }


def generate_threats(
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
    """Select source-grounded defensive threat hypotheses."""
    return _generate(
        "threats",
        provider,
        context,
        evidence,
        analysis,
        sources,
        predecessors,
        cancel,
        deadline,
        on_rejection,
    )


def generate_risks(
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
    """Select advisory implementation/decision risks without expanding product scope."""
    return _generate(
        "risks",
        provider,
        context,
        evidence,
        analysis,
        sources,
        predecessors,
        cancel,
        deadline,
        on_rejection,
    )


def generate_glossary(
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
    """Select ordinary definitions of terms actually present in the source."""
    return _generate(
        "glossary",
        provider,
        context,
        evidence,
        analysis,
        sources,
        predecessors,
        cancel,
        deadline,
        on_rejection,
    )

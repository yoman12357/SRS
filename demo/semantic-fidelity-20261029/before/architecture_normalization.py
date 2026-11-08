"""Retain source-backed architecture behavior without added unqualified timing promises."""

import re
from copy import deepcopy

from .audit import record_model_event
from .quantity_normalization import preserve_retention_duration
from .schemas import Evidence

TIMING = re.compile(r"\b(?:immediately|instantaneously|real[ -]time)\b[ \t]*", re.I)


def _source_commits_timing(source: str, family: str) -> bool:
    """Keep explicit positive timing separate from a negated or undecided mention."""
    for clause in re.split(r"[.;,:!?]|\b(?:but|while)\b", source, flags=re.I):
        if re.search(rf"\b{family}\b", clause, re.I) and not re.search(
            r"\b(?:unknown|undecided|unconfirmed|unspecified|undetermined|no|never|without)\b|"
            r"\bnot\b(?!\s+only\b)",
            clause,
            re.I,
        ):
            return True
    return False


def preserve_architecture_timing(content: dict, evidence: list[Evidence]) -> dict:
    """Remove unsupported positive timing modifiers, preserving source timing and negations."""
    result = deepcopy(content)
    sources = {item.id: item.quote for item in evidence}
    changed = False
    retention_decisions: list[str] = []

    def normalize(text: str, ids: list[str], field: str) -> str:
        nonlocal changed
        support = " ".join(sources.get(eid, "") for eid in ids)

        def replacement(match: re.Match) -> str:
            word = match.group().strip()
            family = (
                r"real[ -]time" if re.fullmatch(r"real[ -]time", word, re.I) else re.escape(word)
            )
            if _source_commits_timing(support, family):
                return match.group()
            clause = re.split(r"[.;,:]|\b(?:and|but|while)\b", text[: match.start()], flags=re.I)[
                -1
            ]
            if re.search(r"\b(?:not|no|without|never)\b", clause, re.I):
                return match.group()
            return ""

        normalized = TIMING.sub(replacement, text)
        if normalized != text:
            changed = True
            record_model_event(
                "architecture_timing_normalized",
                {
                    "field": field,
                    "evidence_ids": ids,
                    "original": text,
                    "normalized": normalized,
                    "reason": "unstated_positive_timing_modifier",
                },
            )
        duration, duration_changed = preserve_retention_duration(
            {"evidence_ids": ids, "statement": normalized, "unresolved_decisions": []}, evidence
        )
        if duration_changed:
            record_model_event(
                "architecture_retention_normalized",
                {
                    "field": field,
                    "evidence_ids": ids,
                    "original": normalized,
                    "normalized": duration["statement"],
                    "reason": "unqualified_source_duration",
                },
            )
            retention_decisions.extend(duration["unresolved_decisions"])
        return duration["statement"]

    if "summary" in result:
        result["summary"] = normalize(result["summary"], list(sources), "summary")
    for group in ("items", "data_flows", "trust_boundaries"):
        for index, item in enumerate(result.get(group, [])):
            for field in (
                "title",
                "component_name",
                "detail",
                "responsibility",
                "data_or_action",
                "enforcement",
            ):
                if field in item:
                    item[field] = normalize(
                        item[field], item["evidence_ids"], f"{group}[{index}].{field}"
                    )
    if changed:
        decision = "Architecture response, visibility and refresh timing remain unconfirmed."
        if decision not in result.setdefault("open_issues", []):
            result["open_issues"].append(decision)
    for decision in retention_decisions:
        if decision not in result.setdefault("open_issues", []):
            result["open_issues"].append(decision)
    return result

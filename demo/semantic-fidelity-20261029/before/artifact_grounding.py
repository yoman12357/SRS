"""Conservative source checks shared by normative and descriptive artifact fields."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Literal

from .schemas import Evidence

VALIDATION_POLICY_VERSION = "source-grounding-1.15"
TEXT_FIELDS = (
    "title",
    "detail",
    "summary",
    "statement",
    "given",
    "when",
    "then",
    "expected_result",
    "scenario",
    "rationale",
    "justification",
    "impact",
    "applicability_reason",
    "responsibility",
    "data_or_action",
    "enforcement",
    "success_outcome",
    "goal",
    "story",
    "description",
    "mitigation",
    "residual_risk",
    "human_approval",
    "observable_evidence",
    "evidence_to_record",
)
LIST_FIELDS = (
    "tradeoffs",
    "activities",
    "deliverables",
    "entry_criteria",
    "exit_criteria",
    "security_checks",
    "assumptions",
    "preconditions",
    "steps",
    "alternate_flows",
    "procedure",
)
METRIC = re.compile(
    r"(?<![\w.])(?P<number>[0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*[-–]?\s*"
    r"(?P<unit>%|(?:milliseconds?|ms|seconds?|secs?|s|minutes?|mins?|hours?|hrs?|h|"
    r"days?|weeks?|months?|years?|[MG]bps)(?!\w))",
    re.I,
)


def quantitative_commitments(text: str) -> set[tuple[str, Decimal]]:
    """Normalize recognized engineering units without guessing calendar periods."""
    result = set()
    factors = {
        "ms": Decimal("0.001"),
        "millisecond": Decimal("0.001"),
        "s": Decimal(1),
        "sec": Decimal(1),
        "second": Decimal(1),
        "min": Decimal(60),
        "minute": Decimal(60),
        "h": Decimal(3600),
        "hr": Decimal(3600),
        "hour": Decimal(3600),
        "day": Decimal(86400),
        "week": Decimal(604800),
    }
    for match in METRIC.finditer(text):
        number = Decimal(match["number"].replace(",", ""))
        raw = match["unit"]
        unit = raw.casefold()
        singular = unit if unit in {"ms", "s"} else unit.rstrip("s")
        if singular in factors:
            result.add(("duration_seconds", number * factors[singular]))
        elif unit == "%":
            result.add(("percentage", number))
        elif unit in {"mbps", "gbps"}:
            factor = Decimal(1000000 if unit == "mbps" else 1000000000)
            result.add(("bits_per_second", number * factor * (8 if raw[1] == "B" else 1)))
        else:
            result.add((singular, number))
    return result


def unsupported_quantities(text: str, evidence: list[Evidence]) -> bool:
    """Detect a recognized numeric commitment absent from stakeholder evidence."""
    known = quantitative_commitments(" ".join(item.quote for item in evidence))
    return bool(quantitative_commitments(text) - known)


def claims_recorded_approval(text: str) -> bool:
    """Keep future workflow gates distinct from statements that approval already occurred."""
    return bool(
        re.search(
            r"^(?:final\s+)?(?:(?:release\s+)?approved|approval\s+granted|signed[ -]off)\b|"
            r"\b(?:has|have|was|were)\s+(?:already\s+)?(?:been\s+)?approved\b",
            text,
            re.I,
        )
    )


def supported_risk_ratings(
    field: Literal["likelihood", "impact"], evidence: list[Evidence]
) -> list[str]:
    """Keep unprovided ratings unknown rather than inventing confirmed project evidence."""
    source = " ".join(item.quote for item in evidence)
    matches = re.finditer(
        rf"\b{field}(?:\s+(?:is\s+)?|\s*:\s*)(low|medium|high)\b|"
        rf"\b(low|medium|high)\s+{field}\b",
        source,
        re.I,
    )
    ratings = set()
    for match in matches:
        if re.search(r"\b(?:no|not|without)\s+$", source[: match.start()], re.I):
            continue
        if re.match(r"\s+(?:is\s+)?not (?:confirmed|required)\b", source[match.end() :], re.I):
            continue
        ratings.add((match[1] or match[2]).casefold())
    return ["unknown", *sorted(ratings)]


def unsupported_delivery_guarantees(text: str, evidence: list[Evidence]) -> list[str]:
    """Recognize added continuous-service or product-message promises in draft prose."""
    source = " ".join(item.quote for item in evidence)
    patterns = {
        "unconfirmed_authentication_flow": r"\bauthentication flow\b",
        "unconfirmed_infrastructure_exclusion": r"\bother infrastructure components\b",
        "unconfirmed_capacity_ceiling": (
            r"\b(?:upper bound|capacity ceiling|maximum capacity|hard capacity limit)\b"
        ),
        "unconfirmed_uninterrupted_availability": (
            r"\b(?:without interruption|uninterrupted|zero downtime|no downtime)\b"
        ),
        "unconfirmed_product_message_contract": (
            r"\b(?:(?:visible|displayed|on[ -]screen|user[ -]visible)\s+)?"
            r"(?:denial|error|confirmation|success)\s+message\b"
        ),
        "unconfirmed_mutual_authentication": r"\bmutual authentication\b",
        "unconfirmed_regulatory_claim": (
            r"\b(?:compliance|comply|complies) with (?:privacy|data[ -]protection|security) "
            r"(?:regulations|laws)\b"
        ),
    }
    issues = []
    for code, pattern in patterns.items():
        if code == "unconfirmed_authentication_flow" and re.search(
            r"\bauthenticat\w*\b", source, re.I
        ):
            continue
        if code == "unconfirmed_capacity_ceiling" and re.search(
            r"\b(?:up to|at most|maximum(?: of)?|max|capped at|limited to)\s+[0-9]+\b",
            source,
            re.I,
        ):
            continue
        if re.search(pattern, source, re.I):
            continue
        for match in re.finditer(pattern, text, re.I):
            clause = re.split(r"[.;]", text[: match.start()])[-1]
            if code == "unconfirmed_capacity_ceiling" and re.search(
                r"\b(?:not (?:introduce|impose|define|establish)|without|no)\s+"
                r"(?:(?:an?|any)\s+)?"
                r"(?:(?:upper bound|capacity ceiling|maximum capacity|hard capacity limit)"
                r"\s*(?:,\s*(?:or\s+)?|\s+or\s+|\s+and\s+)(?:(?:an?|any)\s+)?)*$",
                clause,
                re.I,
            ):
                continue
            if re.match(
                r"\s+(?:(?:is|are|remains?)\s+)?"
                r"(?:not (?:required|guaranteed|confirmed)|unconfirmed|unspecified|unknown)\b",
                text[match.end() :],
                re.I,
            ):
                continue
            if not re.search(
                r"\b(?:not|never|without|no|unconfirmed|unspecified|unknown)\b"
                r"(?:\s+[\w-]+){0,5}\s*$",
                clause,
                re.I,
            ):
                issues.append(code)
                break
    return issues


def lifecycle_test_gaps(source: str, criteria: list[dict]) -> list[str]:
    """Require actual retained/removal outcomes for a source-stated record lifecycle."""
    issues = []
    if not re.search(r"\b(?:logs?|records?|data)\b", source, re.I):
        return issues

    def positive(pattern: str, text: str) -> bool:
        for match in re.finditer(pattern, text, re.I):
            clause = re.split(r"[.;,]", text[: match.start()])[-1]
            if not re.search(r"\b(?:not|never|cannot|without|no)(?:\s+\w+){0,3}\s+$", clause, re.I):
                return True
        return False

    outcomes = [criterion["then"] for criterion in criteria]
    if positive(r"\b(?:retain\w*|retention|keep|kept)\b", source) and not any(
        positive(r"\b(?:retain(?:s|ed)?|stored|kept|remains? accessible)\b", text)
        for text in outcomes
    ):
        issues.append("retention_acceptance_outcome_missing")
    if positive(r"\b(?:delet\w*|remov\w*|purg\w*)\b", source) and not any(
        positive(r"\b(?:delete(?:s|d)?|remov(?:e|es|ed)|purg(?:e|es|ed))\b", text)
        or re.search(
            r"\b(?:expired\s+)?(?:logs?|records?|entry|entries)\b.{0,45}"
            r"\b(?:absent|no longer stored|does not exist|not present)\b",
            text,
            re.I,
        )
        for text in outcomes
    ):
        issues.append("deletion_acceptance_outcome_missing")
    return issues


def lifecycle_criterion_issues(source: str, criterion: dict) -> list[str]:
    """A newly created record is not an expiry trigger for its own previously elapsed lifetime."""
    if not (
        re.search(r"\b(?:retain\w*|retention)\b", source, re.I)
        and re.search(r"\b(?:delet\w*|remov\w*|purg\w*)\b", source, re.I)
        and re.search(r"\b(?:logs?|records?|entries|entry|data)\b", source, re.I)
    ):
        return []
    outcome = criterion["then"]
    deletion = re.search(
        r"\b(?:delet\w*|remov\w*|purg\w*)\b.{0,60}\b(?:logs?|records?|entries|entry|data)\b|"
        r"\b(?:logs?|records?|entries|entry|data)\b.{0,60}"
        r"\b(?:deleted|removed|purged|absent|no longer stored|not present)\b",
        outcome,
        re.I,
    )
    trigger = criterion["when"]
    creation = re.search(r"\b(?:creat\w*|generat\w*|insert\w*|append\w*)\b", trigger, re.I)
    elapsed = re.search(
        r"\b(?:clock|advanc\w*|elaps\w*|expir\w*)\b|"
        r"\bretention\s+(?:process\w*|runs?|job)\b",
        trigger,
        re.I,
    )
    if deletion and creation and not elapsed:
        return ["deletion_test_must_expire_an_existing_record_not_create_a_new_record"]
    return []

"""Versioned deterministic lifecycle suitability from authoritative input evidence."""

import re

from .cyber_hypotheses import affirmative_match
from .schemas import Evidence, SDLCCandidate, SDLCFactor

POLICY_VERSION = "sequential-sdlc-2.0"
MODELS = ["Agile", "DevSecOps", "Spiral", "V-Model", "Waterfall", "Hybrid", "Incremental"]
RULES: list[tuple[str, str, str, dict[str, int]]] = [
    (
        "stability",
        "stable",
        r"\b(?:stable|fixed|frozen) requirements\b|"
        r"\brequirements (?:are|remain) (?:stable|fixed|frozen)\b",
        {"Waterfall": 30, "V-Model": 25, "Agile": -15},
    ),
    (
        "stability",
        "evolving",
        r"\b(?:changing|evolving|volatile) requirements\b|"
        r"\brequirements (?:change|evolve) (?:frequently|often)\b",
        {"Agile": 30, "Hybrid": 22, "Incremental": 20, "Waterfall": -25},
    ),
    (
        "uncertainty",
        "high",
        r"\bhigh (?:technical )?uncertainty\b|"
        r"\bunproven technology\b|\bexperimental architecture\b",
        {"Spiral": 35, "Hybrid": 15, "Waterfall": -15},
    ),
    (
        "verification",
        "formal",
        r"\bformal verification\b",
        {"V-Model": 35, "Hybrid": 20, "Waterfall": 10},
    ),
    (
        "verification",
        "independent",
        r"\bindependent verification\b",
        {"V-Model": 35, "Hybrid": 20, "Waterfall": 10},
    ),
    (
        "verification",
        "strict",
        r"\bstrict verification and validation\b",
        {"V-Model": 35, "Hybrid": 20, "Waterfall": 10},
    ),
    (
        "delivery",
        "continuous",
        r"\bcontinuous (?:secure )?deliver(?:y|ies)\b|"
        r"\b(?:daily|weekly|frequent) (?:secure )?releases\b|\bci/cd\b",
        {"DevSecOps": 35, "Hybrid": 20, "Agile": 10, "Waterfall": -20},
    ),
    (
        "regulation",
        "mandatory",
        r"\bmandatory compliance\b|\bregulatory approval\b|"
        r"\blegally required\b",
        {"V-Model": 20, "Hybrid": 20, "Waterfall": 15},
    ),
    (
        "feedback",
        "frequent",
        r"\b(?:weekly|frequent|daily) stakeholder feedback\b|"
        r"\bavailable product owner\b",
        {"Agile": 20, "Hybrid": 10},
    ),
    (
        "legacy",
        "integration",
        r"\blegacy (?:system|network|integration|infrastructure)\b",
        {"Incremental": 20, "Spiral": 12, "Hybrid": 12},
    ),
]

# Product capabilities inform a proposed delivery approach; they do not confirm cadence,
# requirements volatility, available staff, regulatory duties or project deadlines.
DERIVED_RULES = [
    (
        "security_assurance",
        "integrated security review",
        r"\b(?:authenticat\w*|authoriz\w*|accounts?|access.control|role.based|"
        r"permissions?|firewall|filter\w*)\b",
        {"DevSecOps": 12, "Hybrid": 8, "Spiral": 5},
        "Security decisions benefit from security review and tests throughout delivery.",
    ),
    (
        "operational_validation",
        "monitoring feedback",
        r"\b(?:monitor\w*|detect\w*|alerts?|audit)\b",
        {"DevSecOps": 8, "Incremental": 6, "Hybrid": 5},
        "Monitoring and alert behavior needs validation with operational feedback; "
        "this does not establish continuous deployment or a release frequency.",
    ),
    (
        "deployment_scope",
        "staged rollout opportunity",
        r"\b(?:multiple|across|multi)[ -]?(?:campus|buildings?|departments?|locations?)\b|"
        r"\bacross .{0,80}\b(?:buildings?|hostels?|laboratories|offices)\b",
        {"Incremental": 12, "Hybrid": 8, "DevSecOps": 3},
        "Multiple deployment locations offer a staged validation and rollout opportunity; "
        "the rollout plan remains proposed.",
    ),
    (
        "integration_assurance",
        "integration validation",
        r"\b(?:integrat\w*|centralized authentication|collect\w* .{0,90}from)\b",
        {"Incremental": 8, "Spiral": 6, "Hybrid": 4},
        "Connected systems need integration verification before broader rollout; "
        "their age, technology and technical uncertainty remain unspecified.",
    ),
    (
        "sensitive_asset_assurance",
        "risk-led design review",
        r"\b(?:sensitive (?:equipment|research|administrative|data)|research data|"
        r"restricted (?:internal )?(?:resources|systems))\b",
        {"Spiral": 24, "V-Model": 15, "Hybrid": 10},
        "Explicitly sensitive assets justify early threat review and verification planning; "
        "this does not establish a quantified failure impact or mandatory regulation.",
    ),
]


def rank_sdlc(evidence: list[Evidence]) -> dict:
    """Rank exact affirmative evidence; preserve absent/conflicting factors as unknown."""
    scores = dict.fromkeys(MODELS, 40)
    reasons: dict[str, list[str]] = {name: [] for name in MODELS}
    factors: list[SDLCFactor] = []
    weighted_verification = False
    for name, value, pattern, weights in RULES:
        ids: list[str] = []
        for item in evidence:
            for clause in re.split(r"[.;\n]|\bbut\b", item.quote, flags=re.I):
                if re.search(
                    r"\b(?:if|might|may|could|unknown|unconfirmed|not sure)\b", clause, re.I
                ):
                    continue
                for match in re.finditer(pattern, clause, re.I):
                    prefix = clause[: match.start()]
                    suffix = clause[match.end() :]
                    if re.search(r"\b(?:no|not|without|never)\b(?:\W+\w+){0,4}\W*$", prefix, re.I):
                        continue
                    if re.match(r"\s+(?:(?:is|are)\s+)?not\b", suffix, re.I):
                        continue
                    ids.append(item.id)
        if ids:
            factors.append(
                SDLCFactor(
                    name=name,
                    value=value,
                    evidence_ids=sorted(set(ids)),
                    rationale="Explicit delivery evidence in the cited source passages.",
                )
            )
            for model, weight in weights.items():
                if name != "verification" or not weighted_verification:
                    scores[model] += weight
                reasons[model].append(
                    f"{name}={value} ({weight:+d} points; {', '.join(sorted(set(ids)))})"
                )
            if name == "verification":
                weighted_verification = True
    # Contradictory stability evidence cannot justify either mutually exclusive rule.
    for factor_name in {"stability"}:
        relevant = [factor for factor in factors if factor.name == factor_name]
        if len({factor.value for factor in relevant}) > 1:
            for name, value, _, weights in RULES:
                if name == factor_name:
                    for model, weight in weights.items():
                        scores[model] -= weight
                        reasons[model] = [
                            r for r in reasons[model] if not r.startswith(f"{name}={value} ")
                        ]
            factors = [factor for factor in factors if factor.name != factor_name]
            factors.append(
                SDLCFactor(
                    name=factor_name,
                    value="conflicting",
                    evidence_ids=sorted({i for f in relevant for i in f.evidence_ids}),
                )
            )
    for name, value, pattern, weights, rationale in DERIVED_RULES:
        ids = [item.id for item in evidence if affirmative_match(pattern, item.quote)]
        if not ids:
            continue
        factors.append(
            SDLCFactor(
                name=name,
                value=value,
                evidence_ids=ids,
                basis="derived",
                rationale=rationale,
            )
        )
        for model, weight in weights.items():
            scores[model] += weight
            reasons[model].append(
                f"Derived {name} ({weight:+d} points): {rationale} ({', '.join(ids)})"
            )
    order = sorted(MODELS, key=lambda model: (-scores[model], MODELS.index(model)))
    candidates = [
        SDLCCandidate(
            model=model,
            score=max(0, min(100, scores[model])),
            reasons=reasons[model] or ["No differentiating input evidence"],
        )
        for model in order
    ]
    known = {factor.name for factor in factors if factor.value != "conflicting"}
    unknown = sorted(
        {
            "stability",
            "uncertainty",
            "verification",
            "delivery",
            "regulation",
            "feedback",
            "legacy",
            "budget",
            "schedule",
            "failure_consequences",
        }
        - known
    )
    return {
        "policy_version": POLICY_VERSION,
        "required_model": candidates[0].model,
        "factors": [factor.model_dump() for factor in factors],
        "ranked_candidates": [candidate.model_dump() for candidate in candidates],
        "unknown_factors": unknown,
        "provisional": not any(
            factor.basis == "explicit" and factor.value != "conflicting" for factor in factors
        )
        or len(set(scores.values())) == 1,
        "decision_status": (
            "Proposed suitability recommendation; confirm delivery constraints and team capacity "
            "before adopting this lifecycle. Missing factors are not assumed."
        ),
        "score_meaning": "Rule suitability points out of 100, not probabilities",
    }

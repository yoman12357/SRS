"""Source-scoped defensive hypotheses, separate from normative requirements."""

import re

from .schemas import Evidence

# Applicability, asset, abuse scenario and consequence. No implementation is assumed.
CATALOG = [
    (
        "account-takeover",
        r"\b(?:authenticat\w*|identity|logins?|accounts?)\b",
        "User identities and authenticated access",
        "An attacker uses a compromised identity or authenticated session to impersonate "
        "an authorized user and exercise that user's permitted operations.",
        "Unauthorized use of a legitimate identity could expose resources or alter system state.",
    ),
    (
        "privilege-escalation",
        r"\b(?:roles?|permissions?|access.control|authoriz\w*)\b",
        "Role and permission boundaries",
        "A principal exploits an incorrect role assignment or permission check to perform "
        "operations outside the source-defined authorization boundary.",
        "A lower-privilege user could access restricted functions or sensitive resources.",
    ),
    (
        "stale-access",
        r"\b(?:grant|revoke|suspend|revocation|permissions?)\b|\bmanage\w* .{0,25}accounts?\b",
        "Access grants and revocations",
        "A revoked or changed permission remains effective in a session or enforcement point, "
        "allowing access after authorization should have ended.",
        "A formerly authorized principal could continue using access that is no longer approved.",
    ),
    (
        "malicious-admin-change",
        r"\b(?:polic(?:y|ies)|firewall rules?|quarantin\w*|"
        r"isolate|isolation)\b|\bmanage\w* .{0,25}accounts?\b",
        "Administrative security decisions",
        "A malicious or compromised administrator misuses a source-permitted management "
        "operation to weaken protection or disrupt legitimate use through the stated "
        "administrative workflow.",
        "Misused administrative authority could undermine protection or interrupt legitimate use.",
    ),
    (
        "compromised-integration",
        r"\b(?:integrat\w*|centralized authentication|"
        r"collect\w* .{0,90}from|identity system)\b",
        "Integration trust paths",
        "A compromised connected system or integration path supplies forged, altered or missing "
        "identity, event or policy data used by the source-defined integration.",
        "Untrusted integration data could cause incorrect decisions or hide security events.",
    ),
    (
        "audit-evidence-loss",
        r"\b(?:audit|logs?|logging|record\w*)\b",
        "Security and administrative audit evidence",
        "An attacker or recording failure suppresses or alters source-required audit evidence "
        "so that access decisions, security events or admin actions cannot be reconstructed.",
        "Investigators could lose reliable evidence of the events required by the brief.",
    ),
    (
        "detection-evasion",
        r"\b(?:monitor\w*|detect\w*|alerts?)\b",
        "Monitoring and security alerts",
        "Suspicious activity evades the source-defined detection workflow, or excessive events "
        "obscure actionable alerts before an authorized reviewer can investigate.",
        "Relevant suspicious activity could remain undetected or receive delayed investigation.",
    ),
    (
        "segment-boundary-bypass",
        r"\b(?:separat\w*|isolat\w*|segments?)\b.{0,100}"
        r"\b(?:guest|student|research|networks?|traffic)\b",
        "Source-defined network separation",
        "Traffic crosses a source-required network separation boundary through a missing or "
        "incorrect enforcement decision.",
        "An untrusted network participant could reach a resource intended to remain separated.",
    ),
    (
        "filter-bypass",
        r"\b(?:filter\w*|phishing|malicious domains|malicious attachments)\b",
        "Content filtering decisions",
        "Malicious content or a destination is misclassified, or an exception is misapplied, "
        "allowing material that the source-defined filtering workflow should block.",
        "Users could encounter malicious content or unauthorized destinations despite filtering.",
    ),
]

SUGGESTED_REVIEWS = {
    "User identities and authenticated access": (
        "Review impersonation and compromised-identity paths against the stated access duties; "
        "confirm any additional identity or session protections with the stakeholder."
    ),
    "Role and permission boundaries": (
        "Test permitted and denied role/resource pairs against the linked authorization duties; "
        "review ambiguous permission assignments with the resource owner."
    ),
    "Access grants and revocations": (
        "Trace permission changes through subsequent access decisions and any active access; "
        "confirm revocation timing and session semantics before baselining them."
    ),
    "Administrative security decisions": (
        "Review misuse cases for each source-permitted administrative operation and compare "
        "its outcomes and audit coverage with the stated management boundary."
    ),
    "Integration trust paths": (
        "Review trust assumptions at the specified integration boundaries with missing or "
        "altered input fixtures; confirm the required failure handling with the owner."
    ),
    "Security and administrative audit evidence": (
        "Compare source-required events with the resulting audit evidence; assess missing "
        "and altered-record cases and confirm unprovided protection or retention decisions."
    ),
    "Monitoring and security alerts": (
        "Evaluate the stated detection duties with representative positive and negative events; "
        "confirm undecided thresholds, alert priorities and investigation responsibilities."
    ),
    "Source-defined network separation": (
        "Review allowed and denied paths across each stated separation boundary using an "
        "isolated test environment; confirm the responsible boundary owner."
    ),
    "Content filtering decisions": (
        "Review filtering and permitted exception decisions using harmless representative "
        "fixtures; confirm how uncertain classifications should be handled."
    ),
}


def suggested_review(asset: str) -> str:
    """Suggest hypothesis-specific assessment work without mandating extra product controls."""
    return SUGGESTED_REVIEWS.get(
        asset, "Review the failure or abuse path against the linked source obligations."
    )


def affirmative_match(pattern: str, quote: str) -> bool:
    """Recognize stated capabilities without turning exclusions into positive evidence."""
    for clause in re.split(r"[.;\n]|\bbut\b", quote, flags=re.I):
        if re.search(r"\b(?:if|might|could|unknown|unconfirmed|not sure)\b", clause, re.I):
            continue
        for match in re.finditer(pattern, clause, re.I):
            if re.search(
                r"\b(?:no|not|without|never|excluded)\b(?:\W+\w+){0,4}\W*$",
                clause[: match.start()],
                re.I,
            ):
                continue
            if re.match(r"\s+(?:(?:is|are)\s+)?(?:not|excluded)\b", clause[match.end() :], re.I):
                continue
            return True
    return False


def derived_threats(evidence: list[Evidence], requirements: list[dict]) -> list[dict]:
    """Return complete applicable hypotheses, each linked to actual source obligations."""
    supported = [
        (fact, [row["id"] for row in requirements if fact.id in row["evidence_ids"]])
        for fact in evidence
    ]
    supported = [(fact, ids) for fact, ids in supported if ids]
    result = []
    for key, pattern, asset, scenario, impact in CATALOG:
        matches = [(fact, ids) for fact, ids in supported if affirmative_match(pattern, fact.quote)]
        if matches:
            result.append(_candidate(key, asset, scenario, impact, matches))
    if not result and supported:
        result.append(
            _candidate(
                "service-integrity",
                "Source-defined service behavior",
                "Malformed or unauthorized input, or an implementation failure, causes the "
                "service to depart from a source-defined obligation or become unavailable.",
                "Users could receive incorrect results or lose access to the specified service.",
                supported,
            )
        )
    return result


def _candidate(key: str, asset: str, scenario: str, impact: str, matches: list) -> dict:
    return {
        "key": "derived/" + key,
        "content": {
            "asset": asset,
            "actor": "Hypothetical attacker, privileged insider or failure cause",
            "scenario": "Derived hypothesis: " + scenario,
            "impact": impact,
            "control_requirement_ids": list(dict.fromkeys(i for _, ids in matches for i in ids)),
            "evidence_ids": [fact.id for fact, _ in matches],
            "sources": [],
            "residual_risk": "Unverified planning hypothesis. Linked requirements define "
            "intended behavior, not proven prevention. Validate enforcement and residual exposure "
            "during design and acceptance review; likelihood and severity are not established.",
        },
    }

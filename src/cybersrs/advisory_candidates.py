"""Defensive source-derived hypotheses; never new stakeholder obligations."""

import re

from .cyber_hypotheses import derived_threats, suggested_review
from .permission_verification import permission_test_contract
from .schemas import Analysis, Evidence

SOURCE_ADVISORY_VERSION = "source-derived-advisory-1.1"
HYPOTHESIS_NOTICE = (
    "These are defensive planning hypotheses, not observed incidents or approved extra controls. "
    "Unrecognized threats and actual implementation effectiveness require human review."
)


def threat_candidates(evidence: list[Evidence], requirements: list[dict]) -> list[dict]:
    "Identify applicable failure/abuse hypotheses without treating permitted activity as attack."
    result = []
    for fact in evidence:
        ids = [row["id"] for row in requirements if fact.id in row["evidence_ids"]]
        if not ids:
            continue
        contract = permission_test_contract(fact.quote)
        cases = []
        if contract.get("denied_action") or re.search(
            r"\bonly\s+.+\b(?:may|can)\b", fact.quote, re.I
        ):
            cases.append(
                (
                    "role-boundary",
                    "Source-defined permissions and restricted resources",
                    "A principal attempts to bypass a source-defined permission boundary. "
                    "The boundary under analysis is: " + fact.quote,
                    (
                        "Unauthorized access or modification outside the stated permission"
                        " boundary could occur."
                    ),
                )
            )
        if re.search(r"\bauthenticat\w*\b.+\bbefore\s+access", fact.quote, re.I):
            cases.append(
                (
                    "authentication-bypass",
                    "Source-restricted access",
                    "A principal attempts to reach a source-restricted resource without completing "
                    "the required authentication. Source boundary: " + fact.quote,
                    "An unauthenticated principal could gain access to the restricted resource.",
                )
            )
        if re.search(r"\bmanually\s+isolate\b", fact.quote, re.I):
            cases.append(
                (
                    "privileged-misuse",
                    "Device access state",
                    "Misuse of a privileged session targets an unintended device through the "
                    "permitted manual isolation/restoration workflow. Source capability: "
                    + fact.quote,
                    (
                        "An unintended device could lose access or regain access contrary "
                        "to operational intent."
                    ),
                )
            )
        if re.search(r"\b(?:must|shall)\s+(?:record|retain)\b", fact.quote, re.I):
            cases.append(
                (
                    "record-loss",
                    "Source-required records",
                    "Recording or retention fails for the records required by the source, leaving "
                    "the expected evidence unavailable. Source duty: " + fact.quote,
                    (
                        "Missing records could prevent review of the events covered by the"
                        " stated record duty."
                    ),
                )
            )
        if re.search(r"\bautomatic\w*\b", fact.quote, re.I) and re.search(
            r"\b(?:do not|out of scope|not permitted|excluded)\b", fact.quote, re.I
        ):
            cases.append(
                (
                    "excluded-action",
                    "Source-protected network state",
                    "An implementation defect or misuse triggers an excluded automatic action, "
                    "contrary to the explicit source boundary: " + fact.quote,
                    "Network state could change contrary to the stakeholder's explicit exclusion.",
                )
            )
        for kind, asset, scenario, impact in cases:
            result.append(
                {
                    "key": fact.id + "/" + kind,
                    "content": {
                        "asset": asset,
                        "actor": "Unconfirmed actor or cause (planning hypothesis)",
                        "scenario": scenario,
                        "impact": impact,
                        "control_requirement_ids": ids,
                        "evidence_ids": [fact.id],
                        "sources": [],
                        "residual_risk": (
                            "Linked obligations define intended behavior, not proven prevention. "
                            "Enforcement, misuse of permitted access and operational assumptions "
                            "remain unverified until design and acceptance evidence are reviewed."
                        ),
                    },
                }
            )
    return result + derived_threats(evidence, requirements)


def risk_candidates(evidence: list[Evidence], analysis: Analysis, threats: dict) -> list[dict]:
    """Expose source uncertainty and boundary implementation risk without automated overrides."""
    unknown = {
        item.evidence_id for item in analysis.assessments if item.kind in {"uncertain", "conflict"}
    }
    result = []
    for fact in evidence:
        if fact.id in unknown:
            result.append(
                {
                    "key": fact.id + "/decision",
                    "content": {
                        "description": "An unresolved source decision may delay validation: "
                        + fact.quote,
                        "likelihood": "unknown",
                        "impact": "unknown",
                        "rationale": (
                            "The source leaves this decision unresolved; no delivery or "
                            "technical conclusion is inferred."
                        ),
                        "mitigation": (
                            "Obtain a stakeholder decision before baselining affected "
                            "behavior; retain the unknown and revalidate resulting changes."
                        ),
                        "requirement_ids": [],
                        "evidence_ids": [fact.id],
                        "owner": "TBD",
                    },
                }
            )
    for index, threat in enumerate(threats.get("threats", []), 1):
        result.append(
            {
                "key": f"boundary-{index}",
                "content": {
                    "description": "Derived risk affecting " + threat["asset"] + ": "
                    + threat["impact"],
                    "likelihood": "unknown",
                    "impact": "unknown",
                    "rationale": "This is a planning risk linked to the defensive hypothesis: "
                    + threat["scenario"],
                    "mitigation": (
                        suggested_review(threat["asset"]) + " Assign a responsible reviewer. "
                        "Verify the linked canonical "
                        "obligations against their authored acceptance criteria in an "
                        "authorized isolated environment. Record"
                        " gaps and obtain a scope decision before adding any product "
                        "behavior; preserve explicit exclusions."
                    ),
                    "requirement_ids": threat["control_requirement_ids"],
                    "evidence_ids": threat["evidence_ids"],
                    "owner": "TBD",
                },
            }
        )
    return result


GLOSSARY = [
    (
        r"\baccess.control\b",
        "Access control",
        "Rules and enforcement governing which principals may perform actions on resources.",
    ),
    (
        r"\bpolicy|policies\b",
        "Policy",
        (
            "A rule or decision governing permitted actions; its "
            "project-specific meaning remains defined by the source "
            "requirements."
        ),
    ),
    (
        r"\baudit\b",
        "Audit record",
        (
            "A stored record of an event. Required event scope and retention "
            "are determined by the linked source, not this definition."
        ),
    ),
    (
        r"\blogs?\b",
        "Log",
        (
            "A collection of event records. This term does not itself require "
            "additional logging fields, events or access permissions."
        ),
    ),
    (
        r"\bisolat\w*\b",
        "Device isolation",
        (
            "Restriction of a device's network access; the source determines "
            "whether and by whom this action is permitted."
        ),
    ),
    (
        r"\brestore|restoration\b",
        "Access restoration",
        (
            "Returning access that was previously restricted, within the "
            "source-defined permission boundary."
        ),
    ),
    (
        r"\bmulti.factor\b|\bMFA\b",
        "Multi-factor authentication",
        (
            "Authentication using more than one distinct factor; this "
            "definition does not select products or protocols."
        ),
    ),
    (
        r"\bVPN\b",
        "VPN",
        "Virtual private network: a logical private network connection over another network.",
    ),
    (
        r"\bsimultaneous|concurrent|concurrency\b",
        "Concurrency",
        (
            "Activity occurring at the same time; it is distinct from the "
            "registered planning population."
        ),
    ),
    (
        r"\bregistered\b",
        "Registered population",
        (
            "The inventory of registered users or devices; it does not by "
            "itself establish a simultaneous load or a maximum."
        ),
    ),
    (
        r"\bretai\w*|retention\b",
        "Retention",
        (
            "The period or rule for keeping records. A bare duration does not "
            "itself specify deletion timing or minimum/maximum bounds."
        ),
    ),
    (
        r"\bfirewall\b",
        "Firewall",
        (
            "A control that permits or restricts network traffic according to "
            "rules; mentioning it does not authorize automatic changes."
        ),
    ),
]


def glossary_candidates(evidence: list[Evidence]) -> list[dict]:
    """Explain source-present terms without turning definitions into new product requirements."""
    result = []
    for index, (pattern, term, definition) in enumerate(GLOSSARY, 1):
        ids = [item.id for item in evidence if re.search(pattern, item.quote, re.I)]
        if ids:
            result.append(
                {
                    "key": f"term-{index}",
                    "content": {
                        "title": term,
                        "detail": definition,
                        "status": "proposed",
                        "evidence_ids": ids,
                        "sources": [],
                        "requirement_ids": [],
                    },
                }
            )
    return result

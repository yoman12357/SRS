"""Source-scoped decision topics and semantic deduplication of generated questions."""

from __future__ import annotations

import hashlib
import re

from .evidence import is_open_decision, is_project_goal
from .schemas import Analysis, Answer, Evidence, Question
from .source_detail_policy import (
    DETAIL_PATTERNS,
    nonhuman_role_modifier,
    unsupported_source_details,
)
from .source_obligations import source_obligations


def _wording(original: str, canonical: str) -> str:
    """Preserve the first relevant wording unless it embeds an unconfirmed numeric choice."""
    return canonical if re.search(r"\d+", original) else original


TOPICS = {
    "security_targets": (
        r"\b(?:security|secure)\b.*\b(?:criteria|targets|outcomes|define|definition)\b",
        r"\bsecure\b",
        "Which security acceptance outcomes must be demonstrated?",
    ),
    "scalability": (
        r"\bscalab\w*|\bconcurrent (?:users|load)|\bmessage volume",
        r"\bscalab\w*",
        "What measurable scalability targets must the system meet?",
    ),
    "reliability": (
        r"\breliab\w*|\buptime|\brecovery objectives?",
        r"\breliab\w*",
        "What measurable reliability and recovery targets must the system meet?",
    ),
    "manageability": (
        r"\bmanageab\w*|\badministrative interface usability",
        r"\bmanageab\w*",
        "What criteria define acceptable manageability?",
    ),
    "audit_retention": (
        r"\bretention|\bretain\w*|\bhow (?:long|frequently).*\blogs?",
        r"\b(?:logs?|audit)\b",
        "What retention period is required for the audit logs?",
    ),
    "audit_fields": (
        r"\b(?:audit|logs?)\b.*\b(?:fields?|format|content|types?|metadata|granularity)"
        r"|\b(?:fields?|types?)\b.*\b(?:audit|logs?)",
        r"\b(?:audit|logs?)\b",
        "Which fields must the audit logs contain?",
    ),
    "dashboard_content": (
        r"\b(?:dashboard|security status)\b.*\b"
        r"(?:granularity|indicators|content|fields|information)\b|"
        r"\b(?:granularity|indicators|content|fields|information)\b.*\bdashboard\b",
        r"\bdashboard\b",
        "What information must the security dashboard display?",
    ),
    "event_formats": (
        r"\b(?:schema|formats?)\b.*\bevents?\b|\bevents?\b.*\b(?:schema|formats?)\b",
        r"\bcollect\w*\b.*\bevents?\b",
        "Which event formats must be collected from the stated sources?",
    ),
    "dashboard_refresh": (
        r"\b(?:real[ -]time|refresh|updates?|frequency|cadence)\b.*\bdashboard\b|"
        r"\bdashboard\b.*\b(?:real[ -]time|refresh|updates?|frequency|cadence)\b",
        r"\bdashboard\b",
        "What refresh behavior is required for the dashboard?",
    ),
    "device_approval": (
        r"\bapproved (?:personal |research )?devices?|\bdevice approval|\bdevice.*\bapproved\b",
        r"\bapproved\b.*\bdevices?",
        "What criteria determine whether a device is approved?",
    ),
    "roles": (
        r"\b(?:roles?|permissions?|authorization|authorised|authorized|access controls?)\b",
        r"\b(?:role-based|authorized|authorised|permissions?|administrators?|operators?)\b",
        "How are the stated roles and authorized permissions assigned?",
    ),
    "identity_integration": (
        r"\b(?:authentication|identity)\b.*\b(?:method|system|integrat|interface)"
        r"|\b(?:method|integrat|interface).*\b(?:authentication|identity)",
        r"\bcentralized authentication\b|\bintegrat\w*.*\bidentity\b",
        "Which centralized identity system and integration interface must be supported?",
    ),
    "wireless_technology": (
        r"\b(?:wi[ -]?fi|wireless)\s+technolog\w*",
        r"\b(?:wi[ -]?fi|wireless)\s+technolog\w*",
        "Which Wi-Fi technology should the project use?",
    ),
    "isolation": (r"\bisolat\w*", r"\bisolat\w*", "What conditions authorize endpoint isolation?"),
    "policy_sync": (
        r"\b(?:synchroniz|synchronis|distribut|propagat)\w*",
        r"\bpolic\w*",
        "How must policy changes be distributed across the stated locations?",
    ),
    "quarantine": (
        r"\bquarantin\w*|\brelease\b.*\bmessages?",
        r"\bquarantin\w*",
        "What conditions permit quarantining and releasing messages?",
    ),
    "detection": (
        r"\b(?:thresholds?|triggers?|baseline|unusual|suspicious|anomal\w*|"
        r"repeated (?:authentication|access|failed)|malicious|unauthorized)\b",
        r"\b(?:detect\w*|suspicious|unusual|repeated|malicious)\b",
        "What conditions define the requested detections and their alert triggers?",
    ),
}
STOPWORDS = set(
    "what which how will would should must shall the this that these those a an of "
    "for in on to and or be are is as by with at from required define defined "
    "system platform solution university security network user users specific "
    "requirements project needed support implemented existing".split()
)


def _detection_topics(text: str, evidence: list[Evidence]) -> list[tuple[str, str]]:
    """Keep different detection decisions separate while merging their paraphrases."""
    source = " ".join(
        unit.statement
        for fact in evidence
        for unit in source_obligations(fact)
        if unit.action == "detect"
    )
    candidates = {
        "failed_authentication": (
            r"\b(?:repeated|failed|failures)\b.*\b(?:authenticat\w*|login|logins)\b|"
            r"\bauthenticat\w*\b.*\bfail\w*",
            "What conditions define repeated authentication failures?",
        ),
        "unusual_login": (
            r"\bunusual\b.*\blogin\b",
            "What conditions define unusual login behavior?",
        ),
        "suspicious_process": (
            r"\bsuspicious\b.*\bprocess\b",
            "What conditions define suspicious process activity?",
        ),
        "unauthorized_configuration": (
            r"\bunauthorized\b.*\bconfiguration\b|\bconfiguration\b.*\bunauthorized\b",
            "What makes a configuration change unauthorized?",
        ),
        "unauthorized_access": (
            r"\bunauthorized\b.*\baccess\b",
            "What conditions define unauthorized access attempts?",
        ),
        "suspicious_message": (
            r"\bsuspicious\b.*\b(?:messages?|emails?|links?|attachments?)\b",
            "What conditions define suspicious email content?",
        ),
    }
    available = {
        key: (pattern, wording)
        for key, (pattern, wording) in candidates.items()
        if re.search(pattern, source, re.I)
    }
    specific = [
        ("detection:" + key, wording)
        for key, (pattern, wording) in available.items()
        if re.search(pattern, text, re.I)
    ]
    return specific or [("detection:" + key, wording) for key, (_, wording) in available.items()]


def decision_topics(text: str, evidence: list[Evidence]) -> list[tuple[str, str]]:
    """Map only source-relevant decisions; never import a guide's device or compliance scope."""
    source = " ".join(item.quote for item in evidence)
    for name in (
        "device_enrollment",
        "device_compliance",
        "device_health",
        "device_authentication",
        "secure_data_feeds",
        "data_feed_encryption",
        "device_local_policy",
        "predefined_detection",
        "baseline_collection",
        "dynamic_risk_policy",
        "implementation_choice",
        "detection_implementation",
        "storage_implementation",
    ):
        pattern = DETAIL_PATTERNS[name]
        if re.search(pattern, text, re.I) and not re.search(pattern, source, re.I):
            return []
    choices = (
        r"\bantivirus\b",
        r"\bvendors?\b",
        r"\b(?:ML|machine[ -]learning) models?\b",
        r"\bendpoint agents?\b",
        r"\boperating[ -]systems?\b",
    )
    if any(
        re.search(pattern, text, re.I) and not re.search(pattern, source, re.I)
        for pattern in choices
    ):
        return []
    if re.search(
        r"\b(?:framework|regulation|regulatory|HIPAA|PCI|GDPR|ISO)\b", text, re.I
    ) and not re.search(
        r"\b(?:framework|regulation|regulatory|HIPAA|PCI|GDPR|ISO)\b", source, re.I
    ):
        return []
    # A source unknown is authoritative even when no domain-specific topic is recognized.
    if any(
        text.strip().rstrip(".?").casefold() == item.quote.strip().rstrip(".?").casefold()
        for item in evidence
    ):
        return [("source:" + hashlib.sha256(text.casefold().encode()).hexdigest()[:12], text)]
    matches = [
        (key, wording)
        for key, (question, support, wording) in TOPICS.items()
        if re.search(question, text, re.I) and re.search(support, source, re.I)
    ]
    if matches:
        if any(
            key in {"scalability", "reliability", "manageability", "audit_retention"}
            for key, _ in matches
        ) and not re.search(
            r"\b(?:unusual|suspicious|repeated|failed|unauthorized|malicious|anomal\w*)\b",
            text,
            re.I,
        ):
            matches = [(key, wording) for key, wording in matches if key != "detection"]
        if any(key == "detection" for key, _ in matches):
            matches = [(key, wording) for key, wording in matches if key != "detection"] + (
                _detection_topics(text, evidence) or [("detection", TOPICS["detection"][2])]
            )
        return matches

    # Shared nouns cannot establish the relevance of a new product concept.
    # Explicit source unknowns were retained above; generated questions need a scoped topic.
    if (
        re.search(r"\b(?:scope|purpose|what.*(?:do|build)|intended users)\b", text, re.I)
        and len(source.split()) < 12
    ):
        return [("scope", text)]
    return []


def deduplicate_decisions(
    values: list[str],
    evidence: list[Evidence],
    *,
    canonical: bool = False,
    include_references: bool = True,
) -> list[str]:
    """Keep one canonical wording per supported decision topic, retaining distinct decisions."""
    selected: dict[str, str] = {}
    for value in values:
        if re.fullmatch(r"Decision Q-[a-f0-9]+ is TBD\.", value):
            if include_references:
                selected.setdefault(value, value)
            continue
        topics = decision_topics(value, evidence)
        for key, wording in topics:
            selected.setdefault(
                key, wording if canonical or len(topics) > 1 else _wording(value, wording)
            )
    return list(selected.values())


def _answered_audit_retention(evidence: list[Evidence]) -> bool:
    """Recognize one binding, question-linked audit duration without resolving a conflict."""
    answers = [
        fact for fact in evidence
        if fact.source.startswith("answer:")
        and any(key == "audit_retention" for key, _ in decision_topics(fact.context, evidence))
    ]
    return len(answers) == 1 and bool(
        re.fullmatch(
            r"(?:the )?(?:system|audit logs?)\s+(?:must|shall)\s+retain\s+"
            r"[^.!?;]+?\s+for\s+\d+\s+(?:hours?|days?|weeks?|months?|years?)\s*[.!]?",
            answers[0].quote,
            re.I,
        )
    )


def normalize_analysis_decisions(
    analysis: Analysis,
    evidence: list[Evidence],
    answers: list[Answer] | None = None,
) -> Analysis:
    """Normalize model questions without inventing answers or replacing source evidence."""
    result = analysis.model_copy(deep=True)
    source = " ".join(fact.quote for fact in evidence)
    if unsupported_source_details(result.summary, evidence):
        result.summary = source
    open_facts = {fact.id: fact.quote for fact in evidence if is_open_decision(fact.quote)}
    goals = {fact.id: fact.quote for fact in evidence if is_project_goal(fact.quote)}
    resolved = set()
    if _answered_audit_retention(evidence):
        resolved = {
            eid for eid, quote in open_facts.items()
            if re.fullmatch(
                r"(?:leave|keep)\s+(?:the\s+)?audit logs? retention(?: period| duration)? "
                r"open for (?:review|discussion|confirmation|decision)[.!]?",
                quote,
                re.I,
            )
        }
        goals.update({eid: open_facts.pop(eid) for eid in resolved})
    for assessment in result.assessments:
        if assessment.evidence_id in open_facts:
            assessment.kind = "uncertain"
            assessment.sections = ["introduction"]
            assessment.explanation = open_facts[assessment.evidence_id]
        elif assessment.evidence_id in goals:
            assessment.kind = "context"
            assessment.sections = ["introduction"]
            assessment.explanation = goals[assessment.evidence_id]
    stakeholders = []
    for actor in result.stakeholders:
        classes = re.findall(
            r"\b(?:guests?|students?|faculty|staff|researchers?|users?)\b", actor, re.I
        )
        if classes and not any(
            not nonhuman_role_modifier(source, match.start(), match.end())
            for role in classes
            for match in re.finditer(rf"\b{re.escape(role.rstrip('s'))}s?\b", source, re.I)
        ):
            continue
        stakeholders.append(actor)
    result.stakeholders = stakeholders
    questions, seen = [], set()
    skipped = {
        key
        for answer in answers or []
        if answer.skipped
        for key, _ in decision_topics(answer.question_text, evidence)
    }
    for question in result.questions:
        topics = decision_topics(question.question, evidence)
        for key, wording in topics:
            if key in seen or key in skipped or (resolved and key == "audit_retention"):
                continue
            seen.add(key)
            supported = {
                fact.id
                for fact in evidence
                if any(k == key for k, _ in decision_topics(wording, [fact]))
            }
            questions.append(
                question.model_copy(
                    update={
                        "id": "Q-" + hashlib.sha256(key.encode()).hexdigest()[:12],
                        "question": wording,
                        "why_needed": "Clarification is required for this source-stated behavior "
                        "or its acceptance."
                        if unsupported_source_details(question.why_needed, evidence)
                        else question.why_needed,
                        "evidence_ids": sorted(set(question.evidence_ids) & supported)
                        or sorted(supported),
                    }
                )
            )
    result.questions = questions
    unknowns = []
    for value in [*result.unresolved_decisions, *open_facts.values()]:
        if resolved and any(value == goals[eid] for eid in resolved):
            continue
        topics = decision_topics(value, evidence)
        for key, wording in topics:
            if resolved and key == "audit_retention":
                continue
            if key not in seen and key not in skipped:
                seen.add(key)
                unknowns.append(wording)
    for answer in answers or []:
        if answer.skipped and answer.question_text:
            unknowns.append("Unanswered stakeholder decision: " + answer.question_text)
    result.unresolved_decisions = list(dict.fromkeys(unknowns))
    return result


def questions_after_review(
    analysis: Analysis, evidence: list[Evidence], answers: list[Answer]
) -> list[Question]:
    """Prepare validated suggestions and any separate topics the source explicitly leaves open."""
    questions = {question.id: question for question in analysis.questions}
    answered_ids = {answer.question_id for answer in answers}
    known_topics = {
        key
        for text in [
            *(question.question for question in questions.values()),
            *(answer.question_text for answer in answers),
        ]
        for key, _ in decision_topics(text, evidence)
    }

    def add(wording: str, ids: list[str]) -> None:
        """Create one stable question without overwriting a validated suggestion."""
        fingerprint = " ".join(wording.casefold().split()).encode("utf-8")
        question_id = "Q-" + hashlib.sha256(fingerprint).hexdigest()[:12]
        questions.setdefault(
            question_id,
            Question(
                id=question_id,
                question=wording,
                why_needed="This decision remains open in the reviewed analysis.",
                critical=False,
                evidence_ids=ids,
            ),
        )

    for decision in analysis.unresolved_decisions:
        if len(decision) >= 8 and decision.endswith("?") and not decision.startswith(
            "Unanswered stakeholder decision:"
        ):
            topics = decision_topics(decision, evidence)
            if topics and all(key in known_topics for key, _ in topics):
                continue
            add(decision, [])
            known_topics.update(key for key, _ in topics)
    for fact in evidence:
        if not is_open_decision(fact.quote):
            continue
        for key, (question, support, wording) in TOPICS.items():
            if key not in known_topics and re.search(question, fact.quote, re.I) and re.search(
                support, fact.quote, re.I
            ):
                add(wording, [fact.id])
                known_topics.add(key)
    return [question for question in questions.values() if question.id not in answered_ids]


def normalize_section_decisions(content: dict, evidence: list[Evidence]) -> dict:
    """Normalize generated question fields in place before canonical section persistence."""
    for key, value in list(content.items()):
        if key in {"unresolved_decisions", "open_issues", "open_decisions"} and isinstance(
            value, list
        ):
            content[key] = deduplicate_decisions(value, evidence, canonical=True)
        elif isinstance(value, dict):
            normalize_section_decisions(value, evidence)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    normalize_section_decisions(item, evidence)
    return content


def consolidate_document_decisions(
    analysis: Analysis,
    sections: dict,
    evidence: list[Evidence],
) -> Analysis:
    """Store each decision once and preserve section associations as stable question references."""
    result = normalize_analysis_decisions(analysis, evidence)
    current_context = {
        item.evidence_id for item in result.assessments if item.kind == "context"
    }
    resolved_open_facts = {
        fact.quote for fact in evidence
        if fact.id in current_context and is_open_decision(fact.quote)
    }
    retention_answered = bool(resolved_open_facts) and _answered_audit_retention(evidence)
    registry: dict[str, Question] = {}
    for question in result.questions:
        for key, _ in decision_topics(question.question, evidence):
            registry.setdefault(key, question)

    def register(text: str, ids: list[str]) -> list[str]:
        """Use only supported topics and retain the associated exact source evidence IDs."""
        references = []
        if text in resolved_open_facts:
            return []
        if re.fullmatch(r"Decision Q-[a-f0-9]+ is TBD\.", text):
            return (
                [text] if text.split()[1] in {question.id for question in registry.values()} else []
            )
        for key, canonical in decision_topics(text, evidence):
            if retention_answered and key == "audit_retention":
                continue
            supported = {
                fact.id
                for fact in evidence
                if any(k == key for k, _ in decision_topics(text, [fact]))
            }
            linked = sorted(set(ids) & supported) or sorted(supported)
            if key not in registry:
                registry[key] = Question(
                    id="Q-" + hashlib.sha256(key.encode()).hexdigest()[:12],
                    question=canonical,
                    critical=False,
                    why_needed="Resolve the source-stated behavior or acceptance decision.",
                    evidence_ids=linked,
                )
            else:
                question = registry[key]
                question.evidence_ids = sorted(set(question.evidence_ids) | set(linked))
            references.append("Decision " + registry[key].id + " is TBD.")
        return references

    for text in result.unresolved_decisions:
        register(text, [])
    result.unresolved_decisions = []

    def visit(node: dict) -> None:
        """Replace duplicate question text with its existing canonical decision reference."""
        for key, value in list(node.items()):
            if key in {"open_issues", "open_decisions", "unresolved_decisions"} and isinstance(
                value, list
            ):
                references = []
                for text in value:
                    references.extend(register(text, node.get("evidence_ids", [])))
                node[key] = list(dict.fromkeys(references))
            elif isinstance(value, dict):
                visit(value)
            elif isinstance(value, list):
                for child in value:
                    if isinstance(child, dict):
                        visit(child)

    for name, section in sections.items():
        if name != "introduction":
            visit(section)
    # The intro is a source-fact view. Recompose its open issues rather than changing facts.
    result.questions = list({question.id: question for question in registry.values()}.values())
    if "introduction" in sections:
        from .source_facts import preserve_scope_evidence

        sections["introduction"] = preserve_scope_evidence(
            sections["introduction"], evidence, result
        )
    # Scenario question references are projections of the final linked requirement rows.
    by_id = {
        row["id"]: row
        for name in ("functional", "nonfunctional", "security", "data", "network")
        for row in sections.get(name, {}).get("requirements", [])
    }
    for scenario in sections.get("scenarios", {}).get("scenarios", []):
        scenario["unresolved_decisions"] = list(
            dict.fromkeys(
                value
                for rid in scenario["requirement_ids"]
                for value in by_id[rid]["unresolved_decisions"]
            )
        )
    if "scenarios" in sections:
        sections["scenarios"]["open_issues"] = list(
            dict.fromkeys(
                value
                for scenario in sections["scenarios"]["scenarios"]
                for value in scenario["unresolved_decisions"]
            )
        )
    return result

"""Conservative source-clause obligations with original evidence and role boundaries."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .schemas import Analysis, Evidence

OBLIGATION_VERSION = "source-obligations-1.5"


# One action contract drives both semantic validation and the native corrective schema.
# Keep these fragments broad enough to recognize an externally observed state while the
# independent target/source checks prevent a generic verb from passing the criterion.
OBSERVED_OUTCOME_PATTERNS = {
    "register": r"\bregister(?:ed|s)?\b|"
    r"\b(?:is|are|was|were)\s+(?:created|saved|stored|available)\b|\bexists?\b",
    "reject": r"\breject(?:ed|s)?\b|\bden(?:y|ied|ies)\b",
    "identify": r"\bidentif(?:y|ied|ies)\b|\bdetect(?:ed|s)?\b|\bflagg(?:ed|s)?\b",
    "generate": r"generat|raised|creat|receiv|available|exist|produc|emit|issu",
    "quarantine": r"quarantin|held|isolat",
    "release": r"releas|deliver|forward",
    "revoke": r"revok|remov|denied|disable|withdraw",
    "isolate": r"isolat|restrict|disconnect",
    "change": r"chang|updat|sav|persist|reflect",
    "update": r"chang|updat|sav|persist|reflect",
    "create": r"creat|sav|persist|exist|reflect|visible",
    "configure": r"configur|appl|sav|reflect",
    "detect": r"detect|identif|flag|recogniz|alert",
    "inspect": r"inspect|filter|screen|evaluat|classif|check|review|identif|analys|detect|"
    r"return|display|present|available|shown|view|list",
    "review": r"return|display|present|available|shown|review|inspect|view|list",
    "investigate": r"return|display|present|available|shown|investigat|identif|find",
    "monitor": r"monitor|display|return|observ|list|visible|shown|present|report|show",
    "record": r"record|sav|stor|persist|availab",
    "log": r"log|record|sav|stor|persist|availab",
    "modify": r"modif|chang|updat|sav|reflect",
    "suspend": r"suspend|disable|denied|inactiv|restrict",
    "control": r"control|allow|den(?:y|ied|ies)|permit|restrict|authoriz",
    "require": r"requir|authenticat|denied|reject|prevent",
    "assign": r"assign|grant|reflect|authoriz|updat|chang",
    "grant": r"grant|allow|permit|authoriz",
    "terminate": r"terminat|ended|closed|disconnect|inactiv",
    "define": r"defin|creat|sav|persist|reflect|available",
    "initiate": r"initiat|start|running|active|created|queued",
    "submit": r"submit|receiv|accept|pending|available",
    "track": r"track|histor|record|display|available|return|shown|list",
    "approve": r"approved|authoriz|accepted|approval.*(?:saved|recorded|available)",
    "set_expiration": r"\b(?:expiration|expiry)\b.{0,50}"
    r"\b(?:set|saved|stored|updated|matches?|reflects|applied)\b|"
    r"\b(?:sets?|saves?|stores?|updates?|appl(?:y|ies|ied))\b.{0,50}"
    r"\b(?:expiration|expiry)\b",
    "renew": r"renewed|renewal.*(?:complete|succe)|validity.*(?:updat|extend)",
    "restore": r"restor|recover|previous|available|reflect",
    "maintain": r"record|log|stor|retain|present|available",
    "collect": r"collect|receiv|gather|ingest|captur",
    "protect": r"protect|block|detect|reject|quarantin|flag|prevent|mitigat|contain|safeguard",
    "integrate": r"connect|exchange|integrat|recogniz|accepted|authenticat|interoperat",
    "provide": r"display|present|available|access|return|establish|show|provid",
    "support": r"support|connect|access|available|accepted|compatible|covered|succe|establish",
    "enforce": r"enforc|block|den(?:y|ied|ies)|allow|restrict|grant|permit|reject",
    "separate": r"separat|isolat|denied|block|restrict",
    "use": r"use|authenticat|authoriz|role|decision|accepted|denied|access",
    "allow": r"allow|grant|permit|authoriz|access|available|succe",
    "manage": r"manag|creat|updat|chang|remov|available|reflect",
    "block": r"block|denied|reject|prevent|restrict",
    "restrict": r"restrict|denied|block|prevent|limit",
    "escalate": r"escalat|raised|forward|assigned|available",
    "close": r"clos|resolved|complete|inactive|final",
    "correlate": r"correlat|linked|associated|grouped|matched",
    "authenticate": r"authenticat|accepted|rejected|denied|verified",
    "retain": r"retain|stored|available|preserv",
    "encrypt": r"encrypt|protected|unreadable|cipher",
    "source_behavior": r"return|display|present|available|shown|visible|creat|updat|chang|"
    r"accept|reject|denied|allow|stored|saved|received|completed|active|inactive|exists?",
}


def observed_outcome_pattern(action: str) -> str | None:
    """Return the shared semantic predicate for an externally observed action result."""
    return OBSERVED_OUTCOME_PATTERNS.get(action)
VERBS = (
    "register",
    "reject",
    "identify",
    "provide",
    "use",
    "separate",
    "monitor",
    "detect",
    "generate",
    "configure",
    "review",
    "revoke",
    "inspect",
    "support",
    "remain",
    "protect",
    "quarantine",
    "allow",
    "maintain",
    "integrate",
    "collect",
    "investigate",
    "record",
    "log",
    "modify",
    "suspend",
    "require",
    "control",
    "define",
    "initiate",
    "submit",
    "track",
    "approve",
    "renew",
    "change",
    "isolate",
    "create",
    "update",
    "enforce",
    "release",
    "manage",
    "block",
    "restrict",
    "grant",
    "terminate",
    "assign",
    "escalate",
    "close",
    "correlate",
    "authenticate",
    "retain",
    "restore",
    "encrypt",
    "be",
)
VERB_PATTERN = "|".join(VERBS)
SET_EXPIRATION = r"set(?=\s+(?:(?:an?|the)\s+)?(?:expiration|expiry)\b)"
INFLECTIONS = {verb + "s": verb for verb in VERBS}
INFLECTIONS.update(
    {
        "provides": "provide",
        "manages": "manage",
        "collects": "collect",
        "modifies": "modify",
        "identifies": "identify",
    }
)
QUALITY = r"secure|scalable|reliable|manageable|available|maintainable|usable|portable"


@dataclass(frozen=True)
class SourceObligation:
    """A conservative normalized clause; its parent quote stays immutable evidence."""

    key: str
    evidence_id: str
    quote: str
    statement: str
    action: str
    section: str


def _parts(body: str) -> list[str]:
    """Split independent predicate conjunctions, leaving noun lists and conditions intact."""
    body = re.sub(
        r"\b(approve)\s+or\s+(reject)\b"
        r"(?=\s+(?:(?:an?|the)\s+)?(?:[\w-]+\s+){0,4}requests?\b)",
        r"\1 and \2",
        body,
        flags=re.I,
    )
    # "controls and monitors access" shares its object; normalize the coordinated
    # predicate only when the first verb has no object. Noun lists stay untouched.
    body = re.sub(
        rf"\b({VERB_PATTERN})\s+and\s+({'|'.join(INFLECTIONS)})\s+",
        lambda match: match[1] + " and " + INFLECTIONS[match[2].casefold()] + " ",
        body,
        flags=re.I,
    )
    noun_spans = [
        match.span()
        for match in re.finditer(
            r"\bbackup\s+and\s+restore\s+(?:activities|operations|jobs|events|records|status)\b|"
            r"\blog\s+(?:files?|entries|records)\b",
            body,
            re.I,
        )
    ]
    boundaries = list(
        re.finditer(
            rf"(?:,\s*(?:and\s+)?|\s+and\s+)(?=(?:{VERB_PATTERN}|{SET_EXPIRATION})\b)",
            body,
            flags=re.I,
        )
    )
    values, start = [], 0
    for boundary in boundaries:
        next_verb = boundary.end()
        if any(left <= next_verb < right for left, right in noun_spans):
            continue
        values.append(body[start : boundary.start()])
        start = next_verb
    values.append(body[start:])
    # A shared object follows a verb series: create, review, update and revoke rules.
    for index in range(len(values) - 2, -1, -1):
        if values[index].strip().casefold() in VERBS:
            following = re.match(rf"(?:{VERB_PATTERN})\s+(.+)", values[index + 1], re.I)
            if following:
                values[index] = values[index].strip() + " " + following[1]
    return [value.strip(" ,.") for value in values if value.strip(" ,.")]


def _source_body(quote: str) -> tuple[str, str] | None:
    """Distinguish a product-purpose request, product duty and literal human actor duty."""
    purpose = re.match(
        r"^(?:design|build|develop|create)\s+[^.;!?]+?"
        r"\b(?:system|platform|solution|gateway|application|tool|service)\b"
        r"(?:\s+for\s+[^.;!?]+?)?\s+(?:that|which)\s+(?P<body>.+)",
        quote,
        re.I,
    )
    if purpose:
        body = purpose["body"].rstrip(". ")
        letting = re.match(rf"lets\s+(.+?)\s+((?:request|{VERB_PATTERN})\b.+)", body, re.I)
        if letting:
            body = f"allow {letting[1]} to {letting[2]}"
        first, *tail = body.split(" ", 1)
        return "The system", INFLECTIONS.get(first.casefold(), first) + (
            " " + tail[0] if tail else ""
        )
    modal = re.match(
        r"^(?P<actor>.+?)\s+(?:shall|should|must|may|can)\s+"
        r"(?:be\s+able\s+to\s+)?(?P<body>.+)$",
        quote.rstrip(". "),
        re.I,
    )
    if modal:
        return modal["actor"], modal["body"]
    bare = re.match(
        rf"^(?P<actor>.+?)\s+(?P<verb>{VERB_PATTERN})(?:s)?\s+(?P<body>.+)$",
        quote.rstrip(". "),
        re.I,
    )
    if bare:
        return bare["actor"], bare["verb"] + " " + bare["body"]
    return None


def source_obligations(fact: Evidence) -> list[SourceObligation]:
    """Retain all recognized source predicates; never use retrieved text as obligations."""
    parsed = _source_body(fact.quote)
    if not parsed or re.search(
        r"\b(?:not|no|never|cannot|if|unless|only|whether|unknown|unconfirmed|might|could|"
        r"manually|automatically)\b|[,;]\s*(?:and\s+|but\s+)?"
        r"(?:the\s+)?(?:system|platform|solution)\s+(?:shall|should|must|may|can)\b",
        fact.quote,
        re.I,
    ):
        return []
    actor, body = parsed
    product = bool(re.fullmatch(r"(?:the\s+)?(?:system|platform|solution)|it", actor, re.I))
    clauses: list[tuple[str, str, bool]] = []
    parts = _parts(body)
    for index, part in enumerate(parts):
        allowed = re.match(r"allow\s+(.+?)\s+to\s+(.+)$", part, re.I)
        if allowed:
            permission_body = ", ".join([allowed[2], *parts[index + 1 :]])
            permission_parts = _parts(permission_body)
            # A shared-object infinitive list closes after its last coordinated verb:
            # "allow admins to create, review and revoke rules, monitor traffic".
            # The following independent object resumes the original system subject.
            shared_list = allowed[2].strip().casefold() in VERBS
            shared_object = permission_parts[0].partition(" ")[2].casefold()
            permission_scope = True
            for item in permission_parts:
                if shared_list and item.partition(" ")[2].casefold() != shared_object:
                    permission_scope = False
                clauses.append(
                    (allowed[1], item, False) if permission_scope else (actor, item, product)
                )
            break
        else:
            clauses.append((actor, part, product))
    expanded = []
    for role, clause, is_product in clauses:
        role = re.sub(r"^(?:A|An)\b", lambda match: match[0].lower(), role)
        action_match = re.match(rf"(?P<verb>{VERB_PATTERN})\b\s*(?P<object>.*)", clause, re.I)
        action = action_match["verb"].casefold() if action_match else "source_behavior"
        if re.match(SET_EXPIRATION, clause, re.I):
            action = "set_expiration"
        objects = action_match["object"] if action_match else ""
        if action in {"use", "detect"}:
            objects_list = re.split(r",\s*(?:and\s+)?|\s+and\s+", objects)
            # Splitting compound objects is safe only for these independent controls/events.
            variants = [action + " " + item.strip() for item in objects_list if item.strip()]
        elif action in {"remain", "be"} and re.search(rf"\b(?:{QUALITY})\b", objects, re.I):
            qualities = re.findall(rf"\b(?:{QUALITY})\b", objects, re.I)
            suffix = re.search(r"\b(?:across|for|during|under)\b.+", objects, re.I)
            variants = [
                action + " " + quality + (" " + suffix[0] if suffix else "")
                for quality in qualities
            ]
        else:
            variants = [clause]
        for variant in variants:
            statement = (
                "The system shall " + variant
                if is_product
                else "The system shall allow " + role + " to " + variant
            )
            expanded.append(
                (
                    statement.rstrip(". ") + ".",
                    action,
                    "nonfunctional" if action in {"remain", "be"} else "functional",
                )
            )
    if re.match(r"^(?:design|build|develop|create)\b", fact.quote, re.I):
        prefix = re.split(r"\b(?:that|which)\b", fact.quote, maxsplit=1, flags=re.I)[0]
        context = re.search(r"\bfor\s+(.+)$", prefix, re.I)
        scoped = []
        for statement, action, section in expanded:
            if section == "functional":
                if context and re.search(
                    r"\b(?:servers?|endpoints?|devices?|equipment)\b", context[1], re.I
                ):
                    statement = statement.rstrip(".") + " for " + context[1].strip() + "."
                if re.search(r"\bcentralized\b", prefix, re.I) and not re.search(
                    r"\bcentralized\b", statement, re.I
                ):
                    statement = statement.rstrip(".") + " in a centralized system."
            scoped.append((statement, action, section))
        expanded = scoped
        if re.search(r"\bsecure\b", prefix, re.I) and not re.search(r"\bsecure\b", body, re.I):
            expanded.append(("The system shall be secure.", "be", "nonfunctional"))
    return [
        SourceObligation(
            key=f"{fact.id}_O{index:02d}" if len(expanded) > 1 else fact.id,
            evidence_id=fact.id,
            quote=fact.quote,
            statement=statement,
            action=action,
            section=section,
        )
        for index, (statement, action, section) in enumerate(expanded, 1)
    ]


def obligation_dimensions(unit: SourceObligation) -> list[str]:
    """Classify runtime behavior separately from the control's quality/domain dimensions."""
    if unit.section == "nonfunctional":
        dimensions = [
            "security"
            if re.search(r"\bsecure\b", unit.statement, re.I)
            else "performance"
            if re.search(r"\bscalable\b", unit.statement, re.I)
            else "usability"
            if re.search(r"\bmanageable\b", unit.statement, re.I)
            else "availability"
        ]
    else:
        dimensions = ["business"]
    for name, pattern in {
        "security": r"\b(?:authenticat\w*|access|quarantin\w*|firewall|isolat\w*|alerts?)\b",
        "auditability": r"\b(?:audit|logs?)\b",
        "data": r"\b(?:logs?|notes|events|records?)\b",
        "integration": r"\bintegrat\w*\b",
    }.items():
        if re.search(pattern, unit.statement, re.I):
            dimensions.append(name)
    return dimensions


def _meaning_words(text: str) -> set[str]:
    """Compare literal inflections without treating rationale or test text as obligations."""
    ignored = {
        "the",
        "system",
        "platform",
        "solution",
        "shall",
        "should",
        "must",
        "be",
        "to",
        "a",
        "an",
        "and",
        "for",
        "of",
        "with",
        "from",
        "that",
        "which",
    }
    result = set()
    if re.search(r"\b(?:allow|permit|enable|may|can)\b|\bbe able to\b", text, re.I):
        result.add("allow")
    for word in re.findall(r"[a-z]+", text.casefold()):
        if word not in ignored:
            if word in {"may", "can", "able"}:
                continue
            normalized = INFLECTIONS.get(word, word).rstrip("s").replace("administrator", "admin")
            normalized = {
                "inspect": "review",
                "view": "review",
                "permit": "allow",
                "enable": "allow",
                "let": "allow",
                "ingest": "collect",
                "receive": "collect",
            }.get(normalized, normalized)
            result.add(normalized)
    return result


def obligation_is_covered(unit: SourceObligation, requirements: list[dict]) -> bool:
    """Require the action and its source objects in canonical statements bound to that evidence."""
    expected = _meaning_words(unit.statement)
    for row in requirements:
        if unit.evidence_id not in row.get("evidence_ids", []):
            continue
        if expected <= _meaning_words(row["statement"]):
            return True
    return False


def missing_obligation_keys(fact: Evidence, requirements: list[dict], section: str) -> list[str]:
    """List explicitly sourced slots absent from normative content, excluding other categories."""
    return [
        unit.key
        for unit in source_obligations(fact)
        if unit.section == section and not obligation_is_covered(unit, requirements)
    ]


def normalize_requirement_sections(analysis: Analysis, evidence: list[Evidence]) -> Analysis:
    """Route source-stated runtime behavior to functional even when the model chose only NFR."""
    result = analysis.model_copy(deep=True)
    by_id = {fact.id: fact for fact in evidence}
    for assessment in result.assessments:
        if assessment.kind in {"uncertain", "conflict", "exclusion"}:
            continue
        units = source_obligations(by_id[assessment.evidence_id])
        if units and assessment.kind == "context":
            assessment.kind = "requirement"
        for section in dict.fromkeys(unit.section for unit in units):
            if section not in assessment.sections:
                assessment.sections.append(section)
    return result


def criterion_target_issues(unit: SourceObligation, criterion: dict) -> list[str]:
    """Require an observed result for this operation, not a generic action-processing claim."""
    if unit.section == "nonfunctional":
        return []
    errors = []
    if re.search(r"\bpolicy,\s*job\b|\bobject['’]s resulting\b", criterion["then"], re.I):
        errors.append("criterion_must_name_actual_source_object_not_template")
    if unit.action == "protect":
        responses = r"\b(?:blocks?|blocked|rejects?|rejected|notifications?|notifies|notified)\b"
        if re.search(responses, criterion["then"], re.I) and not re.search(
            responses, unit.quote, re.I
        ):
            errors.append("criterion_protection_response_undecided")
        if re.search(r"\binitiat\w*\b", criterion["then"], re.I) and not re.search(
            r"\b(?:protected|prevented|contained|detected|quarantined|flagged|mitigated)\b",
            criterion["then"],
            re.I,
        ):
            errors.append("criterion_must_observe_protection_result")
    if (
        unit.action in {"review", "inspect"}
        and re.search(
            r"\binspection record\b.*\b(?:produced|stored|created)\b", criterion["then"], re.I
        )
        and not re.search(r"\binspection record\b", unit.quote, re.I)
    ):
        errors.append("criterion_review_result_is_only_instrumentation")
    if unit.action == "detect" and re.search(
        r"\b(?:alerts?|notifications?)\b", criterion["then"], re.I
    ):
        if not re.search(r"\b(?:alerts?|notifications?)\b", unit.quote, re.I):
            errors.append("criterion_detection_output_undecided")
    if (
        unit.action == "generate"
        and re.search(r"\b(?:sent|delivered|forwarded)\s+to\b", criterion["then"], re.I)
        and not re.search(r"\b(?:notif\w*|send|sent|deliver\w*|forward\w*)\b", unit.quote, re.I)
    ):
        errors.append("criterion_alert_destination_undecided")
    if re.search(r"\b(?:shall|should|must)\b", criterion["then"], re.I):
        errors.append("criterion_must_observe_result_not_restate_obligation")
    pattern = observed_outcome_pattern(unit.action)
    observed = criterion["then"]
    fronted = re.match(
        r"^\s*(?:when|after|upon|during|before|while)\b[^,;]+[,;]\s*(.+)", observed, re.I
    )
    if fronted:
        observed = fronted[1]
    observed = re.split(
        r"\b(?:when|after|upon|during|before|while)\b", observed, maxsplit=1, flags=re.I
    )[0]
    if (
        unit.action in {"provide", "review", "inspect", "monitor"}
        and re.search(r"\binitiat\w*\b", observed, re.I)
        and not re.search(
            r"\b(?:displayed|returned|shown|visible|available|presented)\b", observed, re.I
        )
    ):
        errors.append("criterion_must_observe_result_not_display_initiation")
    if pattern and not re.search(pattern, observed, re.I):
        errors.append("criterion_missing_observed_action_result")
    generic = set(VERBS) | {
        "allow",
        "remain",
        "network",
        "admin",
        "authorized",
        "security",
        "user",
        "operator",
        "requested",
        "necessary",
        "when",
        "its",
    }
    targets = _meaning_words(unit.statement) - generic
    observation = _meaning_words(" ".join(criterion[field] for field in ("given", "when", "then")))
    if targets and not targets & observation:
        errors.append("criterion_not_bound_to_source_target")
    if criterion["then"].casefold() == criterion["when"].casefold():
        errors.append("criterion_result_repeats_initiation")
    return errors

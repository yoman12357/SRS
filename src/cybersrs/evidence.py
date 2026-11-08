"""Lossless original-input evidence inventory, independent of model interpretation."""

import re

from .schemas import Analysis, Answer, Evidence
from .sdlc import rank_sdlc


def is_open_decision(text: str) -> bool:
    """Recognize a standalone instruction to leave a decision open."""
    return bool(
        re.fullmatch(
            r"(?:leave|keep)\s+[^.;!?]+?\s+open\s+for\s+"
            r"(?:review|discussion|confirmation|decision)[.!]?",
            text.strip(),
            re.I,
        )
    )


def is_project_goal(text: str) -> bool:
    """Recognize a bare product-design request with no embedded runtime duty."""
    goal = re.fullmatch(
        r"(?:design|build|develop|create)\s+(?:an?|the)\s+[^,.;!?]+?"
        r"\b(?:system|platform|solution|gateway|application|tool|service|console|inventory)\b"
        r"(?:\s+for\s+(?P<audience>[^,.;!?]+))?[.!]?",
        text.strip(),
        re.I,
    )
    return bool(
        goal
        and not re.search(r"\b(?:that|which|to|must|should|shall|may|can|without)\b", text, re.I)
        and not re.match(r"\w+ing\b", goal["audience"] or "", re.I)
    )


def _explicit_product_obligation(text: str) -> bool:
    """Bind a modal to its action instead of turning 'must remain open' into behavior."""
    for modal in re.finditer(r"\b(?:shall|should|must|may|can|cannot|required)\b", text, re.I):
        if re.search(r"\b(?:budgets?|schedules?|requirements?)\W*$", text[: modal.start()], re.I):
            continue
        if re.match(
            r"\s+(?:(?:not|be|to|only|manually|automatically|explicitly|securely)\s+)*"
            r"(?:access|isolat|restor|review|inspect|acknowledg|record|log|retain|remov|"
            r"authenticat|manag|grant|block|modif|chang|reject|allow|permit|view|read|"
            r"support|provide|connect|encrypt|secure|scalable|reliable|available|usable|"
            r"den(?:y|ied|ies))\w*\b",
            text[modal.end() :],
            re.I,
        ):
            return True
    return False


def _stated_active_capacity(text: str) -> bool:
    """Recognize an explicit active load separately from registered-user inventory."""
    for match in re.finditer(
        r"\b[0-9]+\s+(?:simultaneous|concurrent)\s+(?:sessions?|users?|devices?|connections?)\b",
        text,
        re.I,
    ):
        prefix = re.split(r"[.;]|\bbut\b", text[: match.start()], flags=re.I)[-1]
        if re.search(
            r"\b(?:whether|might|considering|undecided|unknown|not(?: yet)? decided)\b",
            prefix,
            re.I,
        ):
            continue
        if re.match(
            r"\s+(?:(?:is|are|remains?)\s+)?(?:undecided|unknown|not(?: yet)? decided|may|might)\b",
            text[match.end() :],
            re.I,
        ):
            continue
        return True
    return False


def _bare_product_behavior(text: str) -> bool:
    return bool(
        re.search(
            r"\b(?:authenticates?|manages?|reviews?|inspects?|acknowledges?|isolates?|"
            r"restores?|retains?|records?|removes?|deletes?|encrypts?|denies|allows?|"
            r"grants?|monitors?)\s+(?!(?:system|platform|application|tool)\b)\S+",
            text,
            re.I,
        )
    )


def context_evidence_ids(evidence: list[Evidence]) -> set[str]:
    """Recognize document requests and lifecycle metadata, not target-product behavior."""
    result = set()
    for item in evidence:
        if is_project_goal(item.quote):
            result.add(item.id)
            continue
        if (
            _explicit_product_obligation(item.quote)
            or _stated_active_capacity(item.quote)
            or _bare_product_behavior(item.quote)
        ):
            continue
        document_or_lifecycle = re.search(
            r"^(?:requirements (?:evolve|change|are (?:stable|fixed))|"
            r"(?:this|the) project has (?:stable|evolving|fixed) requirements|"
            r"no continuous delivery|"
            r"(?:build|create|write|generate|specify)\b.*\b(?:requirements specification|srs)\b)",
            item.quote,
            re.I,
        )
        unknown_inventory = re.search(r"\bplanning population\b", item.quote, re.I) and re.search(
            r"\bconcurrency\b.*\b(?:undecided|unknown|not yet decided)\b", item.quote, re.I
        )
        open_planning = re.match(
            r"^(?:the\s+)?(?:project\s+)?(?:budget|delivery schedule|schedule|"
            r"response[ -]time thresholds?|mandatory regulatory frameworks?|"
            r"protocol choices)\b",
            item.quote,
            re.I,
        ) and re.search(
            r"\b(?:is|are|remain|remains)\s+(?:undecided|unknown|unconfirmed|"
            r"not yet decided)\b|\bmust remain open\b",
            item.quote,
            re.I,
        )
        if document_or_lifecycle or unknown_inventory or open_planning:
            result.add(item.id)
    return result


def normative_evidence_ids(evidence: list[Evidence]) -> set[str]:
    """Identify clear modal product obligations independently of model classification."""
    metadata = context_evidence_ids(evidence)
    result = set()
    for item in evidence:
        if item.id in metadata or (
            item.quote.endswith("?")
            and re.match(r"^(?:can|should|who|what|how|when)\b", item.quote, re.I)
        ):
            continue
        if _explicit_product_obligation(item.quote) or _stated_active_capacity(item.quote):
            result.add(item.id)
    return result


def build_evidence(description: str, answers: list[Answer]) -> list[Evidence]:
    """Preserve every source sentence and substantive clarification verbatim."""
    passages: list[tuple[str, str, str]] = [("description", description, "")]
    for answer in answers:
        if answer.skipped or not answer.text.strip():
            continue
        passages.append((f"answer:{answer.question_id}", answer.text, answer.question_text))
    inventory: list[Evidence] = []
    for source, text, context in passages:
        # Do not split decimals, ports, IDs, or abbreviations without following space.
        for part in re.split(r"(?<=[.!?])\s+(?=[A-Z])|\n+", text):
            if part.strip():
                inventory.append(
                    Evidence(
                        id=f"E-{len(inventory) + 1:03d}",
                        source=source,
                        quote=part.strip(),
                        context=context,
                    )
                )
    return inventory


def preserve_skipped_decisions(analysis: Analysis, answers: list[Answer]) -> Analysis:
    """Route exact repeated skipped questions to explicit unknowns without inventing answers."""
    result = analysis.model_copy(deep=True)
    skipped = {
        " ".join(answer.question_text.casefold().split()): answer.question_text
        for answer in answers
        if answer.skipped and answer.question_text
    }
    result.questions = [
        question
        for question in result.questions
        if " ".join(question.question.casefold().split()) not in skipped
    ]
    for question in skipped.values():
        decision = "Unanswered stakeholder decision: " + question
        if decision not in result.unresolved_decisions:
            result.unresolved_decisions.append(decision)
    return result


def has_concrete_product_behavior(evidence: list[Evidence]) -> bool:
    """Distinguish recognizable behavior from a bare project/system noun phrase."""
    if normative_evidence_ids(evidence):
        return True
    return any(_bare_product_behavior(item.quote) for item in evidence)


def validate_analysis(
    analysis: Analysis, evidence: list[Evidence], answers: list[Answer] | None = None
) -> list[str]:
    """Require explicit interpretation of every exact passage without inventing IDs."""
    expected = {item.id for item in evidence}
    context_ids = context_evidence_ids(evidence)
    normative_ids = normative_evidence_ids(evidence)
    lifecycle_evidence = {
        eid for factor in rank_sdlc(evidence)["factors"] for eid in factor["evidence_ids"]
    }
    actual = [item.evidence_id for item in analysis.assessments]
    errors: list[str] = []
    if (
        analysis.supported
        and not has_concrete_product_behavior(evidence)
        and not analysis.questions
        and not any(a.skipped for a in answers or [])
    ):
        errors.append("project_goal_without_concrete_behavior_needs_scope_clarification")
    if set(actual) != expected or len(actual) != len(expected):
        errors.append("assessments_must_cover_each_evidence_id_exactly_once")
    ids = [question.id for question in analysis.questions]
    if len(set(ids)) != len(ids):
        errors.append("duplicate_question_ids")
    for question in analysis.questions:
        if set(question.evidence_ids) - expected:
            errors.append("question_unknown_evidence")
    for item in analysis.assessments:
        if item.evidence_id in normative_ids and (
            item.kind not in {"requirement", "constraint"}
            or not set(item.sections).intersection(
                {"functional", "nonfunctional", "security", "data", "network"}
            )
        ):
            errors.append(
                f"{item.evidence_id}:explicit_product_obligation_needs_requirement_section"
            )
        if item.evidence_id in context_ids and (
            item.kind == "requirement" or set(item.sections) - {"introduction", "sdlc"}
        ):
            errors.append(
                f"{item.evidence_id}:project_context_not_product_behavior; "
                "use context kind and introduction/sdlc sections"
            )
        if item.kind in {"requirement", "constraint", "exclusion"} and not item.sections:
            errors.append(f"{item.evidence_id}:missing_target_section")
        if item.kind == "requirement" and not set(item.sections).intersection(
            {"functional", "nonfunctional", "security", "data", "network"}
        ):
            if not (item.evidence_id in lifecycle_evidence and "sdlc" in item.sections):
                errors.append(
                    f"{item.evidence_id}:product_behavior_needs_requirement_section; "
                    "use functional/nonfunctional/security/data/network for product behavior; "
                    "use context kind for project goals or lifecycle constraints"
                )
    return errors

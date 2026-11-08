"""Keep verification instrumentation distinct from unrequested product logging."""

import re
from copy import deepcopy

from .audit import record_model_event
from .permission_verification import permission_test_contract, permission_test_gaps
from .schemas import Evidence
from .semantics import mentions_event_logging, unsupported_actor_exclusivity


def preserve_source_denial(source: str, criterion: dict, requirement_id: str) -> dict:
    """Remove unsupported explanatory message copy only from an otherwise source-valid denial."""
    result = deepcopy(criterion)
    if not permission_test_contract(source).get("denied_action"):
        return result
    if "prohibited_actor_action_denial_not_tested" in permission_test_gaps(source, [result]):
        return result
    if not unsupported_actor_exclusivity(source, result["then"]):
        return result
    for field in ("then", "observable_evidence"):
        text = result[field]
        for match in re.finditer(
            r"\s+(?:indicating|stating|explaining|saying|reading|because|such\s+as)\b",
            text,
            re.I,
        ):
            if unsupported_actor_exclusivity(source, text[match.start() :]):
                prefix = text[: match.start()].rstrip(" ,;:.")
                if prefix and not unsupported_actor_exclusivity(source, prefix):
                    result[field] = prefix + "."
                    break
    if unsupported_actor_exclusivity(source, result["then"] + " " + result["observable_evidence"]):
        return deepcopy(criterion)
    if "prohibited_actor_action_denial_not_tested" in permission_test_gaps(source, [result]):
        return deepcopy(criterion)
    if result != criterion:
        record_model_event(
            "denial_copy_normalized",
            {
                "requirement_id": requirement_id,
                "source": source,
                "original": criterion,
                "normalized": result,
                "reason": "remove_unstated_exclusive_role_explanation_preserve_source_denial",
            },
        )
    return result


def preserve_nonexclusive_tests(requirement: dict, evidence: list[Evidence]) -> dict:
    """Reject unsupported extra exclusivity tests, retaining authored tests and all source gates."""
    result = deepcopy(requirement)
    source = " ".join(item.quote for item in evidence if item.id in result["evidence_ids"])
    if unsupported_actor_exclusivity(source, result["statement"]):
        return result
    kept = []
    rejected = []
    result["acceptance_criteria"] = [
        preserve_source_denial(source, criterion, result["id"])
        for criterion in result["acceptance_criteria"]
    ]
    for criterion in result["acceptance_criteria"]:
        if unsupported_actor_exclusivity(source, criterion["then"]):
            rejected.append(criterion)
        else:
            kept.append(criterion)
    # Never turn a requirement into a testless assertion. If every test is bad,
    # leave the candidate rejected for the normal model-authored repair path.
    if not kept or not rejected:
        return result
    result["acceptance_criteria"] = kept
    decision = "Permissions for roles not expressly specified by this source remain unconfirmed."
    if decision not in result["unresolved_decisions"]:
        result["unresolved_decisions"].append(decision)
    for criterion in rejected:
        record_model_event(
            "acceptance_criterion_rejected",
            {
                "requirement_id": result["id"],
                "evidence_ids": result["evidence_ids"],
                "criterion": criterion,
                "reason": "unconfirmed_actor_exclusivity",
                "action": "reject_extra_test_then_revalidate_full_source_coverage",
            },
        )
    return result


def _asserts_record_creation(text: str) -> bool:
    """Recognize event-record creation separately from reading/storing an existing log."""
    for clause in re.split(r"[.;\n]|\bbut\b", text, flags=re.I):
        for match in re.finditer(
            r"\b(?:is|are|was|were|be|being|been)\s+"
            r"(?:(?:also|automatically|separately)\s+){0,2}(?:logged|recorded)\b|"
            r"\b(?:logged|recorded)\s+by\s+(?:the\s+)?(?:system|application|platform)\b|"
            r"\b(?:system|application|platform)[ -]generated\b[^.;]{0,70}\b(?:logs?|records?)\b|"
            r"^(?:record|log)\b(?!\s+(?:in|into|of)\b)|"
            r"\band\s+(?:also\s+)?(?:record|log)\b(?!\s+(?:in|into|of|files?)\b)|"
            r"\b(?:shall|should|must|will|may|can)\s+"
            r"(?:(?:also|automatically|securely)\s+){0,2}(?:record|log)\b(?!\s+(?:in|into)\b)|"
            r"\b(?:system|application|platform)\s+"
            r"(?:(?:also|automatically)\s+){0,2}(?:logs|records)\b(?!\s+(?:in|into)\b)",
            clause,
            re.I,
        ):
            if not re.search(
                r"\b(?:no|not|never|without)\b(?:\W+\w+){0,5}\W*$",
                clause[: match.start()],
                re.I,
            ):
                return True
    return False


def acceptance_logging_issues(source: str, criterion: dict[str, str]) -> list[str]:
    """Keep existing source log records distinct from unrequested new event recording."""
    if _asserts_record_creation(source) or re.search(
        r"\bmaintain(?:s)?\s+(?:audit\s+)?logs?\s+(?:of|for)\b", source, re.I
    ):
        return []
    existing_logs = mentions_event_logging(source)

    def unstated_log_class(text: str) -> bool:
        """Existing connection records do not imply a separate administrative audit trail."""
        classes = (
            r"\baudit(?:[ -]?(?:logs?|records?|trails?))?\b",
            r"\baccess[ -]control[ -](?:logs?|records?|trails?)\b",
        )
        return any(
            re.search(pattern, text, re.I) and not re.search(pattern, source, re.I)
            for pattern in classes
        )

    issues = []
    result = criterion["then"]
    new_result = (
        (_asserts_record_creation(result) or unstated_log_class(result))
        if existing_logs
        else mentions_event_logging(result)
    )
    if new_result and not re.match(
        r"\s*(?:the\s+)?test[- ](?:harness|collector)\s+(?:records?|logs?)\b", result, re.I
    ):
        issues.append("unrequested_product_logging_use_test_instrumented_state_capture")
    witness = re.sub(
        r"\bwithout\s+(?:(?:product|system|production)\s+)?logging\b",
        "",
        criterion["observable_evidence"],
        flags=re.I,
    )
    new_witness = (
        (_asserts_record_creation(witness) or unstated_log_class(witness))
        if existing_logs
        else mentions_event_logging(witness)
    )
    if new_witness and not re.search(
        r"\b(?:test[- ](?:harness|collector|instrumentation|instrumented)[ -]logs?|"
        r"(?:test|instrumentation)[ -]logs?)\b",
        witness,
        re.I,
    ):
        issues.append("unconfirmed_production_log_witness_use_test_capture")
    return issues


def preserve_source_outcome(source: str, criterion: dict[str, str]) -> dict[str, str]:
    """Remove only unsupported latency modifiers and trailing new-log side effects."""
    result = dict(criterion)
    if not re.search(r"\b(?:immediately|instantaneously|real[ -]time|live)\b", source, re.I):
        result["then"] = re.sub(
            r"\b(?:immediately|instantaneously)\s+", "", result["then"], flags=re.I
        )
        result["then"] = re.sub(
            r"\b(?:in\s+)?(?:real[ -]time|live)\b\s*",
            "",
            result["then"],
            flags=re.I,
        )
        result["then"] = re.sub(r"\s+([.,;])", r"\1", result["then"]).rstrip()
    if (
        "unrequested_product_logging_use_test_instrumented_state_capture"
        in acceptance_logging_issues(source, result)
    ):
        match = re.search(
            r"\s*,?\s+and\s+(?:(?:the\s+)?system\s+)?"
            r"(?:logs\b|records\s+(?:the\s+)?(?:event|attempt|action)\b|"
            r"(?:is|are|was|were)\s+(?:also\s+)?(?:logged|recorded)\b|"
            r"(?:logged|recorded)\s+in\s+(?:the\s+)?(?:system|production|audit)\s+logs?\b|"
            r"generates?\s+(?:an?\s+)?audit\s+(?:log|entry)\b)",
            result["then"],
            re.I,
        )
        if match:
            prefix = result["then"][: match.start()].rstrip(" ,;.")
            if len(prefix) >= 12:
                result["then"] = prefix + "."
    if result != criterion:
        record_model_event(
            "source_outcome_normalization",
            {
                "source": source,
                "original": criterion,
                "normalized": result,
                "reason": "retain_authored_outcome_remove_unrequested_modifier_or_log_side_effect",
            },
        )
    return result


def acceptance_response_issues(source: str, criterion: dict[str, str]) -> list[str]:
    """Detection does not authorize added account lockout, isolation or session termination."""
    expected = re.sub(
        r"\bwithout\s+(?:terminating|locking|isolating)\b", "", criterion["then"], flags=re.I
    )
    if re.search(r"\bdisconnect\w*\b", source, re.I):
        expected = re.sub(
            r"\b(?:terminat\w*|ends?)\s+(?:the\s+)?"
            r"(?:(?:active|current|existing|guest)\s+){0,3}(?:connections?|sessions?)\b|"
            r"\b(?:connections?|sessions?)\s+(?:is|are)\s+(?:terminated|ended)\b",
            "",
            expected,
            flags=re.I,
        )
    responses = (
        r"\bterminat\w*\b|\bends?\s+(?:the\s+)?session\b",
        r"\block(?:s|ed|ing|out)?\b",
        r"\bisolat\w*\b",
    )
    mail_quarantine = (
        re.search(r"\bquarantin\w*\b", source, re.I)
        and re.search(r"\b(?:emails?|messages?)\b", source, re.I)
        and re.search(r"\bquarantin\w*\b", expected, re.I)
        and re.search(r"\b(?:emails?|messages?)\b", expected, re.I)
        and not re.search(r"\b(?:endpoints?|devices?|hosts?|accounts?|sessions?)\b", expected, re.I)
    )
    if any(
        re.search(pattern, expected, re.I)
        and not re.search(pattern, source, re.I)
        and not (pattern == r"\bisolat\w*\b" and mail_quarantine)
        for pattern in responses
    ):
        return ["unconfirmed_automatic_response"]
    return []

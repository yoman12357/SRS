"""Conservative semantic guards for numeric subjects and explicit automation exclusions."""

import re

from .schemas import Evidence

CAPABILITY_PATTERNS = {
    "firewall": r"\bfirewalls?\b|\bpacket filtering\b",
    "monitoring": r"\bmonitor\w*\b",
}
ACTION_PATTERNS = {
    "isolation": r"\bisolat\w*\b",
    "restoration": r"\brestor\w*\b",
    "review": r"\b(?:review\w*|inspect\w*|view\w*|read\w*|retriev\w*)\b",
    "acknowledgement": r"\backnowledg\w*\b",
    "recording": r"\b(?:record\w*|log(?:s|ged|ging)?)\b",
    "retention": r"\b(?:retain\w*|retention|keep|kept|stor\w*)\b",
    "deletion": r"\b(?:delet\w*|remov\w*|purge\w*)\b",
    "authentication": r"\b(?:authenticat\w*|log[ -]?in)\b",
    "management": r"\bmanag\w*\b",
    "grant": r"\bgrant\w*\b",
    "modification": r"\b(?:chang\w*|modif\w*|updat\w*|reconfigur\w*)\b",
    "scanning": r"\bscan\w*\b",
}


def mentions_event_logging(text: str) -> bool:
    """Distinguish event records from logical descriptions and a person's sign-in action."""
    without_sign_in = re.sub(
        r"\blog(?:s|ged|ging)?\s+(?:into|onto)\b|"
        r"\blog(?:s|ged|ging)?\s+in\b(?=\s*(?:$|[.,;:]|and\b|to\b|with\b|using\b))",
        "",
        text,
        flags=re.I,
    )
    return bool(
        re.search(
            r"\b(?:log(?:s|ged|ging|gers?)?|audit(?:s|ed|ing|able|ability)?|"
            r"audit(?:log|record|trail)\w*)\b",
            without_sign_in,
            re.I,
        )
    )


def project_request_recast_as_runtime_behavior(source: str, statement: str) -> bool:
    """Reject a project request to design a product being recast as that product's feature."""
    purpose = re.match(
        r"^(?P<verb>design|build|develop|create)\s+"
        r"[^.;!?]+?\b(?:system|platform|solution)\b"
        r"(?:\s+for\s+[^.;!?]+?)?\s+(?:that|which)\s+(?P<body>.+)$",
        source,
        re.I,
    )
    if not purpose:
        return False
    verb = purpose["verb"]
    return bool(
        re.match(rf"^(?:the\s+)?(?:system|platform|solution)\s+shall\s+{verb}\b", statement, re.I)
        and not re.search(rf"\b{verb}\w*\b", purpose["body"], re.I)
    )


def unsupported_actor_exclusivity(source: str, text: str) -> set[str]:
    """Recognize added 'only this role' restrictions independently for each linked source."""
    pattern = (
        r"\bonly\s+(?:(?:an?|the|authorized|authorised|designated|network)\s+){0,3}"
        r"(administrators?|admins?|operators?|employees?|contractors?|guests?|students?|users?)\b"
    )

    def roles(value: str) -> set[str]:
        return {
            match.group(1).casefold().rstrip("s").replace("administrator", "admin")
            for match in re.finditer(pattern, value, re.I)
            if not re.search(r"\bnot\s+$", value[: match.start()], re.I)
        }

    return roles(text) - roles(source)


def unsupported_wait_condition(source: str, text: str) -> bool:
    """Recognize a new waiting-period condition on a source action without a timing policy."""
    conditional_period = re.search(
        r"\b(?:after|until|before|within|once)\b[^.;,:]{0,65}"
        r"\b(?:period|duration|delay|timeout|cooldown)\b",
        text,
        re.I,
    )
    source_policy = re.search(
        r"\b(?:period|duration|delay|timeout|cooldown|wait\w*|retain\w*|retention|"
        r"expir\w*|seconds?|minutes?|hours?|days?|weeks?|months?|years?)\b",
        source,
        re.I,
    )
    return bool(conditional_period and not source_policy)


def unsupported_architecture_choices(text: str, evidence: list[Evidence]) -> set[str]:
    """Keep logical architecture within scope instead of importing a guide's full framework."""
    choices = {
        "zero_trust": r"\bzero[ -]trust\b",
        "pki": r"\bpki\b|\bpublic[ -]key infrastructure\b|\bcertificate[ -]based\b",
        "policy_as_code": r"\bpolicy[ -]as[ -]code\b",
        "ci_cd": r"\bci/cd\b|\bcontinuous (?:integration|deployment)\b",
        "device_posture": r"\bdevice (?:security )?posture\b",
        "dynamic_access_risk": r"\b(?:dynamic|risk[ -]based) (?:access|risk|policy)\b",
        "global_auditing": r"\b(?:all|every|each)\s+(?:such\s+)?"
        r"(?:operations?|actions?|activities)\b.{0,70}\b(?:log(?:ged|ging)?|audit(?:ed|ing)?)\b",
    }
    original = " ".join(item.quote for item in evidence)
    return {
        name
        for name, pattern in choices.items()
        if re.search(pattern, text, re.I) and not re.search(pattern, original, re.I)
    }


def missing_source_actions(
    source: str, normative_text: str, *, include_capabilities: bool = False
) -> set[str]:
    """Check recognized source actions in normative outcomes, not copied rationale prose."""
    patterns = ACTION_PATTERNS | (CAPABILITY_PATTERNS if include_capabilities else {})
    action_source = source
    if re.match(r"^(?:design|build|develop|create)\b", source, re.I):
        # A purpose's 'managed endpoints' describes devices being monitored.
        # It does not request an additional endpoint-management capability.
        action_source = re.sub(
            r"\bmanaged\s+(?=(?:endpoints?|devices?|servers?)\b)",
            "",
            source,
            flags=re.I,
        )
    missing = {
        action
        for action, pattern in patterns.items()
        if re.search(pattern, action_source, re.I) and not re.search(pattern, normative_text, re.I)
    }
    # A product-purpose access-management clause can be expressed as providing
    # controlled access. This does not cover an administrator managing policies,
    # permissions or accounts; those retain their actor/action checks below.
    if "management" in missing and _overview_access_management_is_covered(source, normative_text):
        missing.remove("management")
    if "monitoring" in missing and _overview_monitoring_is_covered(source, normative_text):
        missing.remove("monitoring")
    if (
        "management" in missing
        and re.match(r"^(?:design|build|develop|create)\b", source, re.I)
        and re.search(r"\bmanagement\s+(?:system|platform|solution)\b", source, re.I)
        and not re.search(r"\bmanag(?:e[sd]?|ing)\b", source, re.I)
    ):
        missing.remove("management")
    if "recording" in missing and not re.search(
        r"\b(?:shall|must|will|to|and)(?:\s+\w+){0,2}\s+(?:record|log)\b|"
        r"^(?:record|log)\b|\b(?:system|application|platform)\s+(?:records|logs)\b",
        source,
        re.I,
    ):
        missing.remove("recording")
    for actor in re.finditer(
        r"(?:^|;)\s*([A-Za-z]+(?:[ -][A-Za-z]+){0,3}?)\s+"
        r"(?:(?:may|can|shall|must)\s+)?manage(?:s)?\b",
        source,
        re.I,
    ):
        phrase = actor.group(1)
        if re.search(r"\b(?:not|who|what|how|whether)\b", phrase, re.I):
            continue
        role = phrase.split()[-1].casefold().rstrip("s")
        actor_pattern = rf"\b{re.escape(role)}s?\b"
        covered = False
        for clause in re.split(r"[;.!?]|\b(?:but|while)\b", normative_text, flags=re.I):
            action = re.search(ACTION_PATTERNS["management"], clause, re.I)
            if (
                action
                and re.search(actor_pattern, clause, re.I)
                and not re.search(
                    r"\b(?:not|never|no|cannot|without|denied|prohibit\w*)"
                    r"(?:\s+(?:be|to|from|permission|permissions|being|granted|authorized|"
                    r"authorised|allowed|permitted|able)){0,5}\s+$",
                    clause[: action.start()],
                    re.I,
                )
            ):
                covered = True
                break
        if not covered:
            missing.add("management")
    return missing


def _overview_monitoring_is_covered(source: str, normative_text: str) -> bool:
    """Accept event collection for a monitoring product name, preserving explicit monitor duties."""
    purpose = re.match(
        r"^(?:design|build|develop|create)\b"
        r"(?P<title>[^.;!?]+?\b(?:system|platform|solution))\b"
        r"(?:\s+for\s+[^.;!?]+?)?\s+(?:that|which)\s+(?P<body>.+)$",
        source,
        re.I,
    )
    if not purpose or not re.search(r"\bmonitoring\b", purpose["title"], re.I):
        return False
    # The noun in the product name is not another action quota. Actual
    # monitoring verbs/objects in the body remain required by the ordinary gate.
    if re.search(CAPABILITY_PATTERNS["monitoring"], purpose["body"], re.I):
        return False
    collection = (
        r"\b(?:collect\w*|ingest\w*|receiv\w*)\s+"
        r"(?:(?:university|campus|security|network|authentication|system)\s+){1,3}events?\b"
    )
    if not re.search(collection, purpose["body"], re.I):
        return False
    for match in re.finditer(collection, normative_text, re.I):
        if not re.search(
            r"\b(?:no|not|never|cannot|without|deny|denied)"
            r"(?:\s+\w+){0,3}\s+$",
            normative_text[: match.start()],
            re.I,
        ):
            return True
    return False


def _overview_access_management_is_covered(source: str, normative_text: str) -> bool:
    """Recognize access-service wording only for a system-purpose 'manages access' clause."""
    if not re.match(r"^(?:design|build|develop|create)\b", source, re.I):
        return False
    if not re.search(
        r"\b(?:system|platform|solution)\b[^.;!?]{0,120}"
        r"\b(?:that|which)\s+manages?\s+(?:network\s+)?access\b"
        r"(?!\s+(?:polic(?:y|ies)|permissions?|rights?|accounts?|roles?|rules?))",
        source,
        re.I,
    ):
        return False
    for clause in re.split(r"[;.!?]", normative_text):
        if not re.search(r"\b(?:networks?|wired|wireless|NAC)\b", clause, re.I):
            continue
        for match in re.finditer(
            r"\b(?:provid\w*|control\w*|regulat\w*|govern\w*|enforc\w*)\b"
            r"\s+(?:(?:secure|network|wired|wireless|campus|role-based)\s+){0,4}access\b",
            clause,
            re.I,
        ):
            if not re.search(
                r"\b(?:not|never|cannot|without|deny|denied)"
                r"(?:\s+\w+){0,3}\s+$",
                clause[: match.start()],
                re.I,
            ):
                return True
    return False


def missing_source_quantities(source: str, normative_text: str) -> set[str]:
    """Retain stated execution/duration metrics; planning inventories are handled separately."""
    pattern = (
        r"(?<!\w)([0-9]+(?:\.[0-9]+)?)\s*(milliseconds?|seconds?|minutes?|hours?|days?|"
        r"months?|years?|%|mbps|gbps|concurrent|simultaneous)"
    )

    def values(text: str) -> set[tuple[str, str]]:
        return {
            (
                number,
                "parallel_load"
                if unit.casefold() in {"concurrent", "simultaneous"}
                else unit.casefold().rstrip("s"),
            )
            for number, unit in re.findall(pattern, text, re.I)
        }

    return {f"{number}_{unit}" for number, unit in values(source) - values(normative_text)}


def semantic_issues(text: str, evidence: list[Evidence]) -> list[str]:
    """Reject recognized contradictions without rewriting or guessing missing behavior."""
    issues = []
    folded = text.casefold()
    for item in evidence:
        source = item.quote.casefold()
        if (
            re.search(r"\b(?:record|log|audit)\w*\b", source)
            and re.search(r"\b(?:administrator|admin)\w*\s+policy\s+chang\w*", source)
            and re.search(
                r"\b(?:all|every|each)\s+(?:administrator|admin)\w*\s+"
                r"(?:actions?|activities|operations?)\b",
                folded,
            )
            and re.search(r"\b(?:record|log|audit)\w*\b", folded)
            and not any(
                re.search(
                    r"\b(?:all|every|each)\s+(?:administrator|admin)\w*\s+"
                    r"(?:actions?|activities|operations?)\b",
                    other.quote,
                    re.I,
                )
                for other in evidence
            )
        ):
            issues.append(f"{item.id}:policy_change_audit_is_not_all_administrator_activity")
        # A planning inventory does not imply an equal number of active sessions.
        if re.search(r"planning population|registered (?:devices|users)|plan for", source):
            planning = re.findall(r"([0-9]+)\s+registered\s+(?:devices|users)", source)
            for number in planning:
                postpositive = (
                    rf"\b{number}\s+(?:registered\s+)?(?:devices?|users?|sessions?)\b"
                    r"[^.;!?0-9]{0,100}\b(?:concurrently|simultaneously|in parallel)\b"
                )
                if re.search(postpositive, folded) and not re.search(postpositive, source):
                    issues.append(f"{item.id}:planning_population_is_not_concurrency")
                if re.search(rf"\b{number}\s+(?:concurrent|simultaneous|active)\b", folded):
                    explicit_concurrency = re.search(
                        rf"\b{number}\s+(?:concurrent|simultaneous|active)\b", source
                    )
                    if not explicit_concurrency:
                        issues.append(f"{item.id}:planning_population_is_not_concurrency")
                if (
                    re.search(rf"\b{number}\b", folded)
                    and re.search(
                        r"\b(?:active device(?:s| count)?|active users?|concurrent "
                        r"(?:devices?|users?|sessions?)|simultaneous (?:devices?|users?|sessions?))"
                        r"\b[^.;!?]{0,65}\b(?:maximum|cap(?:acity)?|not exceed(?:ing)?|"
                        rf"limit(?:ed)?(?: to)?|boundary|at most)\b[^.;!?0-9]{{0,25}}\b{number}\b",
                        folded,
                    )
                    and not re.search(rf"\b{number}\s+(?:active|concurrent|simultaneous)\b", source)
                ):
                    issues.append(f"{item.id}:planning_population_is_not_active_capacity")
        for number in re.findall(
            r"\b([0-9]+)\s+(?:(?:registered|simultaneous|concurrent|active)\s+)?"
            r"(?:users?|devices?|sessions?)\b",
            source,
        ):
            upper_bound = (
                r"\b(?:up to|at most|maximum(?: of)?|max|capped at|limited to|limit of)"
                rf"\s+{number}\b"
                rf"|\b{number}[ -](?:(?:simultaneous|concurrent|active)\s+)?"
                r"(?:users?|devices?|sessions?)[ -](?:limit|cap|maximum)\b"
            )
            if re.search(upper_bound, folded) and not re.search(upper_bound, source):
                issues.append(f"{item.id}:unconfirmed_load_bound")
        # A retention duration cannot become a response deadline (or vice versa).
        for number, unit in re.findall(
            r"\b([0-9]+)\s+(days?|hours?|minutes?|seconds?|milliseconds?)\b", source
        ):
            generated = re.search(rf"\b{number}\s+{unit}\b", folded)
            for bound in (
                r"(?:at least|minimum(?: (?:retention )?(?:period|duration))?"
                r"(?: of)?|no less than)",
                r"(?:at most|maximum(?: (?:retention )?(?:period|duration))?"
                r"(?: of)?|no more than|up to)",
            ):
                phrase = rf"\b{bound}\s+{number}\s+{unit}\b"
                if re.search(phrase, folded) and not re.search(phrase, source):
                    issues.append(f"{item.id}:unconfirmed_duration_bound")
            if generated and re.search(r"retain|retention|delete|remov", source):
                if re.search(r"\b(?:respond|response|latency|alert delivery)\b", folded):
                    if not re.search(r"retain|retention|delete|remov", folded):
                        issues.append(f"{item.id}:retention_duration_is_not_response_deadline")
        if re.search(r"\b(?:do not|must not|shall not|never) automatically\b", source):
            for action in ("isolate", "change firewall", "reconfigure"):
                if action not in source:
                    continue
                positive = re.search(
                    rf"\b(?:shall|must|will)\s+automatically\s+{re.escape(action)}", folded
                )
                if positive:
                    issues.append(f"{item.id}:automatic_action_contradicts_exclusion")
    if "```" in text or re.search(r"\b(?:os\.system|subprocess\.(?:run|Popen))\s*\(", text):
        issues.append("executable_code_is_not_a_requirement")
    return sorted(set(issues))

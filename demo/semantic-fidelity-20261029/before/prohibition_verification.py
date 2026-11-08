"""Observable state-based verification of explicitly prohibited automatic changes."""

import re

from .semantics import missing_source_actions


def verbatim_prohibition_statements(source: str) -> list[str]:
    """Keep a clear human prohibition or its equivalent shall-form without changing its scope."""
    if source.rstrip().endswith("?"):
        return []
    if re.match(r"^do not\s+automatically\b", source, re.I):
        return [source, re.sub(r"^do not\b", "The system shall not", source, flags=re.I)]
    if re.match(r"^never\s+automatically\b", source, re.I):
        return [source, re.sub(r"^never\b", "The system shall never", source, flags=re.I)]
    excluded = re.fullmatch(r"(.+?)\s+(?:are|is)\s+out of scope[.!]?", source.strip(), re.I)
    if excluded and automatic_change_is_prohibited(source):
        return [f"The system shall exclude {excluded.group(1)} from its scope."]
    return []


def prohibition_statement_is_faithful(source: str, statement: str) -> bool:
    """Permit harmless case/spacing/punctuation changes while preserving the complete clause."""
    allowed = verbatim_prohibition_statements(source)
    if not allowed:
        return True

    def normalized(value: str) -> str:
        """Normalize presentation without removing actors, conjunctions or conditions."""
        return re.sub(r"\s+", " ", value).strip().rstrip(".!").casefold()

    return normalized(statement) in {normalized(value) for value in allowed}


def automatic_change_is_prohibited(source: str) -> bool:
    """Recognize explicit automatic-change exclusions without inventing other restrictions."""
    return bool(
        re.search(r"\b(?:do not|must not|shall not|never)\s+automatic\w*", source, re.I)
        or re.search(r"\bautomatic\w*\b.+\b(?:out of scope|prohibited|excluded)\b", source, re.I)
    )


def prohibition_test_contract(source: str, action: str | None = None) -> dict[str, str]:
    """Supply a state-based test obligation only for an actual automation prohibition."""
    if not automatic_change_is_prohibited(source):
        return {}
    required = missing_source_actions(source, "") or {"automatic_action"}
    if action is not None and action not in required:
        raise ValueError("prohibition_action_not_in_source")
    selected = {action} if action else required
    active_scan = selected == {"scanning"} and _active_scan_is_named(source)
    return {
        "actions_to_attempt": ", ".join(sorted(selected)),
        "instruction": (
            "Simulate/attempt the named active scan "
            if active_scan
            else "Simulate/attempt the specified automatic action(s) "
        )
        + "in an authorized test environment. "
        + "Put the complete attempted action in WHEN, not only GIVEN. "
        + (
            "Observe that no scan executes/emits traffic; capture packet/traffic evidence. "
            if active_scan
            else "Then the affected state is unchanged; compare captured "
            "BEFORE and AFTER configuration/connectivity state. "
        )
        + "Do not invent product logging, error messages or manual operator procedures.",
    }


def prohibition_test_gaps(source: str, criteria: list[dict]) -> list[str]:
    """Require an attempted forbidden automation and a captured unchanged-state comparison."""
    return (
        []
        if not prohibited_action_gaps(source, criteria)
        else ["automatic_prohibition_needs_attempt_and_unchanged_state_evidence"]
    )


def prohibited_action_gaps(source: str, criteria: list[dict]) -> list[str]:
    """Enumerate only actual uncovered source actions while retaining the public aggregate gate."""
    if not automatic_change_is_prohibited(source):
        return []
    required = missing_source_actions(source, "") or {"automatic_action"}
    observed = set().union(*(_verified_action_names(source, criterion) for criterion in criteria))
    return [
        f"automatic_prohibition_{action}_not_exercised" for action in sorted(required - observed)
    ]


def prohibition_gap_action(source: str, gap: str) -> str | None:
    """A requested gap cannot invent an exclusion absent from the linked source."""
    match = re.fullmatch(r"automatic_prohibition_(.+)_not_exercised", gap)
    if not match or not automatic_change_is_prohibited(source):
        return None
    action = match.group(1)
    return action if action in missing_source_actions(source, "") else None


def _active_scan_is_named(source: str) -> bool:
    """Respect the explicit active mode even beside a different automatic-action exclusion."""
    return bool(re.search(r"\bactive\b[^.;]{0,50}\bscan\w*\b", source, re.I))


def _verified_action_names(source: str, criterion: dict) -> set[str]:
    """Check each named attempt's mode, absent effect and relevant state/traffic witness."""
    if not automatic_change_is_prohibited(source):
        return set()
    required = missing_source_actions(source, "") or {"automatic_action"}
    trigger = criterion["when"]
    if not re.search(
        r"\b(?:attempt\w*|simulat\w*|trigger\w*|request\w*|initiat\w*|invok\w*|"
        r"execut\w*|perform\w*|run|runs|running)\b",
        trigger,
        re.I,
    ):
        return set()
    outcome, witness = criterion["then"], criterion["observable_evidence"]
    affirmative_event = re.search(
        r"\b(?:log|record)\b.*\b(?:indicating|showing|confirming)\b.*"
        r"\b(?:change|isolation)\b",
        witness,
        re.I,
    )
    if affirmative_event and not re.search(
        r"attempt|denied|reject|no change|unchanged|blocked", witness, re.I
    ):
        return set()
    result = set()
    for action in required - missing_source_actions(source, trigger):
        scanning = action == "scanning"
        mode = (
            r"\b(?:active|automat\w*)\b"
            if scanning and _active_scan_is_named(source)
            else r"\bautomat\w*\b"
        )
        if not re.search(mode, trigger, re.I):
            continue
        unchanged = re.search(
            r"unchanged|unaltered|unmodified|identical|preserved|no .*?(?:chang\w*|isolat\w*)|"
            r"not .*?(?:occur\w*|chang\w*|isolat\w*|perform\w*)",
            outcome,
            re.I,
        )
        absent_scan = scanning and re.search(
            r"\bno\b.{0,50}\b(?:scans?|scanning|scan traffic)\b|"
            r"\bscan\w*\b.{0,35}\b(?:absent|not emitted|not performed|not executed)\b",
            outcome,
            re.I,
        )
        evidence_pattern = (
            r"packet|traffic|network (?:capture|trace)|"
            r"scan\w*.{0,40}(?:state|status|capture|trace|counter)|"
            r"(?:state|status|capture|trace|counter).{0,40}scan\w*"
            if scanning
            else r"state|configuration|snapshot|diff|connectivity|firewall rule"
        )
        if (unchanged or absent_scan) and re.search(evidence_pattern, witness, re.I):
            result.add(action)
    return result


def verified_prohibition_criteria(source: str, criteria: list[dict]) -> list[dict]:
    """Retain state-based tests contributing valid coverage of at least one excluded action."""
    return [criterion for criterion in criteria if _verified_action_names(source, criterion)]

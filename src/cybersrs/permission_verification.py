"""Test obligations for explicit role permissions and prohibitions in one source passage."""

import re

from .semantics import missing_source_actions


def permission_test_contract(source: str) -> dict:
    """Recognize allowed actor actions and any explicit denial without inventing one."""
    actor = re.search(r"(?:^|[;:])\s*([^;:]{2,70}?)\s+(?:may|can)\s+(?!not\b)", source, re.I)
    if not actor:
        return {}
    remainder = source[actor.end() :]
    denied = re.search(
        r"\b(?:may|can|must|shall)\s+(?:not|be denied)\b|\bcannot\b",
        remainder,
        re.I,
    )
    access_block = re.search(
        r"[,;]\s*(?:and\s+|but\s+)?(?:the\s+)?(?:system|platform|solution)\s+"
        r"(?:must|shall)\s+(?:block|deny)\s+(?:(?:their|its|his|her|them)\s+)?"
        r"access\s+to\s+(?:the\s+)?(?P<target>[^.;!?]+)",
        remainder,
        re.I,
    )
    if access_block and not remainder.lower().startswith("access "):
        access_block = None
    roles = [
        part.strip().split()[-1].casefold().rstrip("s")
        for part in re.split(r"\band\b", actor.group(1), flags=re.I)
        if part.strip()
    ]
    boundary = denied or access_block
    positive = (
        source[actor.start(1) : actor.end() + boundary.start() if boundary else len(source)]
        .strip(" ,;.")
        .strip()
        .removesuffix("but")
        .removesuffix("and")
        .strip()
    )
    target = re.search(r"\b(?:may|can)\s+access\s+(?:only\s+)?(?:the\s+)?(.+)$", positive, re.I)
    negative = remainder[denied.end() :] if denied else ""
    denied_target = re.search(r"\baccess\s+(?:to\s+)?(?:the\s+)?(.+?)[.]?$", negative, re.I)
    if not denied_target:
        denied_target = re.search(r"^(.+?)\s+access[.]?$", negative.strip(), re.I)
    denied_action = (
        ("access" if access_block else None)
        if not denied
        else "modification"
        if re.search(r"chang\w*|modif\w*|edit\w*", negative, re.I)
        else (
            "grant"
            if re.search(r"grant\w*", negative, re.I)
            else ("access" if re.search(r"access|connect", negative, re.I) else "prohibited action")
        )
    )
    return {
        "actor_role_terms": roles,
        "paired_system_block": access_block is not None,
        "positive_clause": positive,
        "positive_access_target": target.group(1).strip() if target else "",
        "denied_action": denied_action,
        "denied_access_target": (
            denied_target.group(1).strip()
            if denied_target
            else access_block["target"].strip() if access_block else ""
        ),
        "instruction": "Test visible success for every permitted source action. "
        + (
            "Also exercise the explicit prohibited action by the same role and observe denial. "
            "A permitted action leaving policy unchanged is not a denial test."
            if denied_action
            else "No denied permission is stated; do not invent one."
        ),
    }


def _positive_outcome(text: str) -> bool:
    for clause in re.split(r"\b(?:but|and|while)\b|[;.!?]", text, flags=re.I):
        # Absence of errors qualifies a successful result; it is not itself success.
        clause = re.sub(
            r"^\s*(?:without|no)\s+(?:any\s+)?(?:errors?|failures?|denials?|rejections?)\b[^,]*,",
            "",
            clause,
            flags=re.I,
        )
        clause = re.sub(
            r"\b(?:without|no)\s+(?:any\s+)?(?:errors?|failures?|denials?|rejections?)\b.*$",
            "",
            clause,
            flags=re.I,
        )
        if re.search(
            r"\b(?:den(?:y|ies|ied|ial)|block\w*|reject\w*|refus\w*|forbidden|fail\w*|error)\b",
            clause,
            re.I,
        ):
            continue
        if re.search(
            r"\b(?:not|never|no longer)\s+(?:be\s+)?(?:allow\w*|permit\w*|grant\w*|"
            r"accept\w*|restor\w*|isolat\w*|establish\w*|connect(?:s|ed|ing)?|"
            r"available|accessible|success\w*|succeed\w*)\b",
            clause,
            flags=re.I,
        ):
            continue
        if re.search(
            r"\b(?:grant\w*|allow\w*|permit\w*|display\w*|available|accessible|review\w*|inspect\w*|acknowledg\w*|accept\w*|shown|view\w*|read\w*|succeed\w*|successful\w*|isolat\w*|restor\w*|return\w*|retriev\w*|render\w*|load\w*|connect(?:s|ed|ing)?|establish(?:es|ed|ing)?|reachable)\b",
            clause,
            re.I,
        ):
            return True
    return False


def permission_gap_action(source: str, gap: str) -> str | None:
    """Bind a permitted-action gap only to an action actually present in its source permission."""
    match = re.fullmatch(r"permitted_(.+)_outcome_not_observed", gap)
    contract = permission_test_contract(source)
    if not match or not contract:
        return None
    action = match.group(1)
    return action if action in missing_source_actions(contract["positive_clause"], "") else None


def has_positive_test_outcome(text: str) -> bool:
    """Expose the shared observable-success oracle without treating unchanged state as success."""
    return _positive_outcome(text)


def _target_words_present(words: list[str], text: str) -> bool:
    """Treat a singular test target as an instance of its named plural destination."""
    for word in words:
        singular = re.sub(r"(?<![isu])s$", "", word, flags=re.I)
        if not re.search(rf"\b{re.escape(singular)}s?\b", text, re.I):
            return False
    return True


def permission_statement_gaps(source: str, statements: list[str]) -> list[str]:
    """Require both named access destinations in the normative behavior of a paired source."""
    contract = permission_test_contract(source)
    if not contract.get("paired_system_block"):
        return []
    clauses = [
        clause
        for statement in statements
        if _role_present(contract["actor_role_terms"], statement)
        for clause in re.split(
            r"[;,]|\b(?:and|but)\s+(?=(?:(?:the\s+)?system\s+)?"
            r"(?:shall\s+|must\s+)?(?:block|deny|prevent|restrict|allow|permit|grant)\b)",
            statement,
            flags=re.I,
        )
    ]
    permit = r"\b(?:allow\w*|permit\w*|grant\w*|(?:may|can|able to)\s+access)\b"
    deny = r"\b(?:block\w*|den(?:y|ies|ied)|prevent\w*|restrict\w*|cannot access|not allow)\b"
    gaps = []
    for direction, pattern in (("positive", permit), ("denied", deny)):
        words = re.findall(r"[A-Za-z]+", contract[f"{direction}_access_target"])
        if not any(
            re.search(pattern, clause, re.I)
            and (direction == "denied" or not re.search(deny, clause, re.I))
            and _target_words_present(words, clause)
            for clause in clauses
        ):
            gaps.append(f"{direction}_access_destination_missing_from_statement")
    return gaps


def permission_test_gaps(source: str, criteria: list[dict]) -> list[str]:
    """Check both sides of an explicit permission boundary using actions and observable results."""
    contract = permission_test_contract(source)
    if not contract:
        return []
    positive_criteria = [
        item
        for item in criteria
        if _positive_outcome(item["then"])
        and _role_present(contract["actor_role_terms"], item["given"] + " " + item["when"])
    ]
    gaps = ["positive_permission_test_missing"] if not positive_criteria else []
    exercised_success = " ".join(
        item["when"]
        + (
            " " + item["given"]
            if re.search(
                r"\b(?:attempt\w*|request\w*|initiat\w*|invok\w*|perform\w*)\b", item["given"], re.I
            )
            else ""
        )
        for item in positive_criteria
    )
    missing_actions = missing_source_actions(contract["positive_clause"], exercised_success)
    # Opening a log view and receiving its data is an exercised read, even when
    # the initiation does not repeat the source's verb "inspect".
    if "review" in missing_actions and any(
        _positive_outcome(item["then"])
        and re.search(
            r"\b(?:request\w*|access\w*|open\w*|select\w*|navigat\w*)\b",
            item["given"] + " " + item["when"],
            re.I,
        )
        and _visible_read_result(item["then"])
        for item in positive_criteria
    ):
        missing_actions.remove("review")
    for action in missing_actions:
        gaps.append(f"permitted_{action}_outcome_not_observed")
    if contract["positive_access_target"]:
        target_words = [
            word
            for word in re.findall(r"[A-Za-z]+", contract["positive_access_target"])
            if word.casefold() not in {"the", "only", "a", "an"}
        ]
        positive_case = any(
            _target_words_present(target_words, " ".join(item.values()))
            and _positive_outcome(item["then"])
            for item in positive_criteria
        )
        if not positive_case:
            gaps.append("permitted_access_target_not_tested")
    if contract["denied_action"] is None:
        return sorted(set(gaps))
    denied_test = False
    for item in criteria:
        trigger = item["given"] + " " + item["when"]
        role_present = _role_present(contract["actor_role_terms"], trigger)
        action = {
            "modification": r"\b(?:chang\w*|modif\w*|edit\w*|updat\w*)\b",
            "grant": r"\bgrant\w*\b",
        }.get(contract["denied_action"], r"\b(?:access\w*|connect\w*|attempt\w*|request\w*)\b")
        denial = re.search(
            r"\b(?:den(?:y|ies|ied|ial)|block\w*|reject\w*|refus\w*|forbidden|not permitted|"
            r"not allowed|not granted|unchanged|no .*chang\w*|no .*modif\w*)\b",
            item["then"],
            re.I,
        )
        target_words = [
            word
            for word in re.findall(r"[A-Za-z]+", contract["denied_access_target"])
            if word.casefold() not in {"the", "any", "all", "a", "an", "to", "internal"}
        ]
        target_exercised = contract["denied_action"] != "access" or _target_words_present(
            target_words, trigger
        )
        if role_present and re.search(action, trigger, re.I) and denial and target_exercised:
            denied_test = True
    if not denied_test:
        gaps.append("prohibited_actor_action_denial_not_tested")
    return sorted(set(gaps))


def _visible_read_result(text: str) -> bool:
    """Recognize returned data rather than a button offering a future inspection."""
    objects = (
        r"(?:view|logs?|data|records?|alerts?|details|reports?|rules?|configuration|"
        r"polic(?:y|ies)|settings|state)"
    )
    pattern = (
        rf"\b(?:return\w*|display\w*|show\w*|retriev\w*)\b.{{0,45}}?\b{objects}\b|"
        rf"\b{objects}\b.{{0,25}}?\b(?:displayed|shown|retrieved|returned)\b"
    )
    return any(
        not re.search(r"\b(?:buttons?|options?|links?)\b", match.group(), re.I)
        for match in re.finditer(pattern, text, re.I)
    )


def _role_present(roles: list[str], text: str) -> bool:
    """Match the stated role, including the ordinary admin abbreviation."""
    return any(
        re.search(
            r"\badmin(?:istrator)?s?\b"
            if role in {"admin", "administrator"}
            else rf"\b{re.escape(role)}s?\b",
            text,
            re.I,
        )
        for role in roles
    )

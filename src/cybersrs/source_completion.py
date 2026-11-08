"""Narrow source-preserving statement constraints for omitted unqualified execution loads."""

import re

from .permission_verification import permission_test_contract
from .semantics import missing_source_quantities


def source_permission_statement(source: str) -> str | None:
    """Keep one unambiguous source role permission and its denial verbatim."""
    if ";" in source or re.search(r"\b(?:whether|unknown|undecided|unconfirmed)\b", source, re.I):
        return None
    if not permission_test_contract(source):
        return None
    if len(re.findall(r"\b(?:may|can)\s+(?!not\b)", source, re.I)) != 1:
        return None
    return source.strip()


def source_role_denial_statement(source: str, rejected_statement: str) -> str | None:
    """Locate a denied-role row in an actual compound source without adding exclusivity."""
    if ";" not in source:
        return None
    for clause in source.split(";"):
        contract = permission_test_contract(clause)
        if not contract.get("denied_action"):
            continue
        actor = re.split(r"\s+(?:may|can)\s+", contract["positive_clause"], maxsplit=1, flags=re.I)[
            0
        ]
        if not re.match(
            rf"^{re.escape(actor)}\s+(?:(?:shall|must|may)\s+not|cannot)\b",
            rejected_statement.strip(),
            re.I,
        ):
            continue
        denial = re.search(r"\b(?:cannot|may not|must not|shall not)\b.+", clause, re.I)
        if denial:
            return actor + " " + denial[0].rstrip(". ") + "."
    return None


def capacity_repair_statement(source: str, rejected_statement: str) -> str | None:
    """Use a rejected row only to locate its quantity in the original unqualified source."""
    numbers = set(re.findall(r"(?<![\w.,])[0-9]+\b", rejected_statement))
    if len(numbers) != 1:
        return None
    number = next(iter(numbers))
    metrics = {key for key in missing_source_quantities(source, "") if key.split("_")[0] == number}
    execution = capacity_completion_statement(source, metrics)
    if execution:
        return execution
    inventory = re.search(rf"\b{number}\s+registered\s+(?:users?|devices?)\b", source, re.I)
    if not inventory:
        return None
    clause = re.split(r"[;.!?]", source[: inventory.start()])[-1]
    if not re.search(r"\b(?:plan for|planning population|planned inventory)\b", clause, re.I):
        return None
    if re.search(
        r"\b(?:maximum|minimum|up to|at most|at least|capped|limited|limit|cap|"
        r"undecided|unknown|unconfirmed|unspecified|whether|tbd)\b",
        source,
        re.I,
    ):
        return None
    return "The system shall support a planned inventory of " + inventory[0] + "."


def capacity_completion_statement(source: str, missing_metrics: set[str]) -> str | None:
    """Render exact bare execution loads without inventing a capacity cap or subject."""
    if not missing_metrics:
        return None
    phrases, covered = [], set()
    for match in re.finditer(
        r"(?<![\w.,])[0-9]+\s+(?:simultaneous|concurrent)\s+"
        r"(?:sessions?|connections?|users?|devices?)\b",
        source,
        re.I,
    ):
        keys = missing_source_quantities(match[0], "")
        if not keys & missing_metrics:
            continue
        before = re.split(r"[;.!?]", source[: match.start()])[-1]
        after = re.split(r"[;.!?]", source[match.end() :])[0]
        if re.search(
            r"\b(?:maximum|minimum|max|min|up to|at most|at least|capped|limited|"
            r"limit|cap)\b",
            before[-50:] + " " + after[:40],
            re.I,
        ):
            return None
        if re.search(
            r"\b(?:up to|at most|at least|maximum(?: of)?|minimum(?: of)?|max|min|"
            r"capped at|limited to|no fewer than|no more than)\s*$",
            before,
            re.I,
        ) or re.match(r"\s+(?:maximum|minimum|limit|cap)\b", after, re.I):
            return None
        if re.search(
            r"\b(?:undecided|unknown|unconfirmed|unspecified|whether|tbd)\b",
            before + " " + after,
            re.I,
        ):
            return None
        phrases.append(match[0])
        covered.update(keys)
    if covered != missing_metrics or not phrases:
        return None
    return "The system shall support " + " and ".join(phrases) + "."

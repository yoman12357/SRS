"""Bound recognized permission-management commitments to their actual source clause."""

import re


def management_statement(source: str) -> str | None:
    """Render a positive actor/manage/permission clause without adding subjects or operations."""
    match = re.search(
        r"(?:^|;)\s*(?P<actor>[A-Za-z][A-Za-z -]{1,65}?)\s+"
        r"(?:(?:may|can|shall|must)\s+)?manage(?:s)?\s+(?P<object>[^;.!?]+)",
        source,
        re.I,
    )
    if not match or re.search(r"\b(?:not|no|never|cannot|whether)\b", match["actor"], re.I):
        return None
    target = re.split(r"\bbut\b", match["object"], maxsplit=1, flags=re.I)[0].strip()
    if not re.search(r"\b(?:permissions?|access rights)\b", target, re.I):
        return None
    actor = match["actor"].strip()
    actor = actor[0].lower() + actor[1:]
    return f"The system shall permit {actor} to manage {target}."


def management_scope_issues(source: str, text: str) -> list[str]:
    """Reject known invented details without equating generic management with a CRUD contract."""
    if management_statement(source) is None:
        return []
    patterns = {
        "unconfirmed_management_creation": r"\b(?:creat\w*|issu(?:e|es|ed|ing))\b",
        "unconfirmed_management_removal": r"\b(?:delet\w*|revok\w*|revocation)\b",
        "unconfirmed_permission_group_subject": r"\bgroups?\b",
        "unconfirmed_permission_database": r"\b(?:databases?|SQL|LDAP)\b",
    }
    return [
        code
        for code, pattern in patterns.items()
        if re.search(pattern, text, re.I) and not re.search(pattern, source, re.I)
    ]

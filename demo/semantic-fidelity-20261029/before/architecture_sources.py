"""Preserve recognized source actors/resources as explicit logical access endpoints."""

from __future__ import annotations

import re

from .permission_verification import permission_test_contract
from .schemas import Evidence

SOURCE_ACCESS_OVERVIEW = (
    "Proposed logical components and access-decision paths for source-stated boundaries; "
    "unresolved implementation choices remain open."
)


def source_access_contracts(evidence: list[Evidence], requirements: list[dict]) -> list[dict]:
    """Extract only stated access pairs with canonical source links; never infer unnamed zones."""
    contracts = []
    for fact in evidence:
        ids = sorted(row["id"] for row in requirements if fact.id in row["evidence_ids"])
        if not ids:
            continue
        permission = permission_test_contract(fact.quote)
        pairs = []
        if permission.get("positive_access_target"):
            actor = re.split(
                r"\s+(?:may|can)\s+", permission["positive_clause"], maxsplit=1, flags=re.I
            )[0].strip()
            pairs.append((actor, permission["positive_access_target"], "permitted"))
            if permission.get("denied_access_target"):
                pairs.append((actor, permission["denied_access_target"], "denied"))
        authenticated = re.search(
            r"(?:^|;)\s*(?P<actor>[A-Za-z][A-Za-z -]{1,65}?)\s+authenticat(?:e|es)\b"
            r"[^;.!?]*?\bbefore\s+access(?:ing)?\s+(?P<resource>[^;.!?]+)",
            fact.quote,
            re.I,
        )
        if authenticated:
            pairs.append((authenticated["actor"], authenticated["resource"], "authenticated"))
        for actor, target, outcome in pairs:
            target = target.strip().rstrip(". ")
            actor_ids = (
                _role_requirement_ids(
                    actor, [row for row in requirements if fact.id in row["evidence_ids"]]
                )
                or ids
            )
            target_ids = [
                row["id"]
                for row in requirements
                if row["id"] in actor_ids and _role_words(target) <= _role_words(row["statement"])
            ]
            contracts.append(
                {
                    "actor": actor,
                    "resource": target,
                    "outcome": outcome,
                    "actor_component": f"Actor: {actor}",
                    "resource_component": f"Resource: {target}",
                    "evidence_id": fact.id,
                    "requirement_ids": target_ids or actor_ids,
                }
            )
    return contracts


def source_endpoint_components(contracts: list[dict]) -> list[dict]:
    """Create immutable logical representations without inventing actors, controls or behavior."""
    nodes = {}
    for contract in contracts:
        for kind in ("actor", "resource"):
            name, label = contract[f"{kind}_component"], contract[kind]
            node = nodes.setdefault(
                name.casefold(),
                {
                    "title": name,
                    "component_name": name,
                    "detail": (f"Proposed logical endpoint for the source-stated {kind}: {label}."),
                    "responsibility": f"Represent the source-stated {kind}: {label}.",
                    "status": "proposed",
                    "sources": [],
                    "evidence_ids": [],
                    "requirement_ids": [],
                },
            )
            node["evidence_ids"] = sorted(set(node["evidence_ids"]) | {contract["evidence_id"]})
            node["requirement_ids"] = sorted(
                set(node["requirement_ids"]) | set(contract["requirement_ids"])
            )
    return list(nodes.values())


def _role_words(text: str) -> set[str]:
    """Compare ordinary role inflections without conflating distinct domain qualifiers."""
    return {
        word.casefold().rstrip("s").replace("administrator", "admin")
        for word in re.findall(r"[A-Za-z]+", text)
        if word.casefold() not in {"the", "a", "an", "only", "and"}
    }


def _role_requirement_ids(actor: str, rows: list[dict]) -> list[str]:
    """Bind compound-source permissions by the actual actor in each canonical statement."""
    variants = [_role_words(part) for part in re.split(r"\band\b", actor, flags=re.I)]
    return sorted(
        row["id"]
        for row in rows
        if any(words and words <= _role_words(row["statement"]) for words in variants)
    )


def source_actor_contracts(evidence: list[Evidence], requirements: list[dict]) -> list[dict]:
    """Preserve recognized permitted roles, management actors and policy-change event actors."""
    contracts = []
    for fact in evidence:
        rows = [row for row in requirements if fact.id in row["evidence_ids"]]
        if not rows:
            continue
        actors = []
        permission = permission_test_contract(fact.quote)
        if permission:
            actors.append(
                re.split(
                    r"\s+(?:may|can)\s+", permission["positive_clause"], maxsplit=1, flags=re.I
                )[0].strip()
            )
        for match in re.finditer(
            r"(?:^|;)\s*([A-Za-z][A-Za-z -]{1,65}?)\s+"
            r"(?:(?:may|can|shall|must|should)\s+(?:be\s+able\s+to\s+)?)?"
            r"(?:manage(?:s)?|authenticat(?:e|es)|review(?:s)?|inspect(?:s)?|"
            r"acknowledge(?:s)?|create(?:s)?|update(?:s)?|grant(?:s)?|revoke(?:s)?|"
            r"define(?:s)?|investigate(?:s)?|restrict(?:s)?)\b",
            fact.quote,
            re.I,
        ):
            actor = match[1].strip()
            if not re.search(r"\b(?:not|no|never|cannot|whether)\b", actor, re.I):
                actors.append(actor)
        for match in re.finditer(
            r"\b(administrators?|admins?)\s+policy\s+changes?\b", fact.quote, re.I
        ):
            actors.append(match[1][0].upper() + match[1][1:])
        # Permissions can be embedded in a system duty, rather than starting
        # with the role: "... and allow network administrators to define ...".
        # Retain the exact role and canonical obligations, never a new permission.
        for pattern in (
            r"\ballow(?:s)?\s+([A-Za-z][A-Za-z -]{1,65}?)\s+to\s+[A-Za-z]+\b",
            r"\bprovid(?:e|es)\s+([A-Za-z][A-Za-z -]{1,65}?)\s+with\s+"
            r"(?:(?:an?|the|centralized|centralised)\s+){0,3}"
            r"(?:dashboard|interface|console|portal)\b",
        ):
            for match in re.finditer(pattern, fact.quote, re.I):
                clause_prefix = re.split(
                    r"[;.!?]|\b(?:and|but|while)\b", fact.quote[: match.start()], flags=re.I
                )[-1]
                if not re.search(
                    r"\b(?:no|not|never|cannot|without|whether|if|unless|undecided|unknown)\b",
                    clause_prefix,
                    re.I,
                ):
                    actors.append(match[1].strip())
        for actor in dict.fromkeys(actors):
            actor = re.sub(r"^only\s+", "", actor, flags=re.I)
            if re.search(
                r"\b(?:if|unless|whether|no|not|never|cannot|may|can|shall|must|should|"
                r"to|allow|allows)\b",
                actor,
                re.I,
            ):
                continue
            if re.fullmatch(r"(?:the\s+)?(?:system|application|platform)", actor, re.I):
                continue
            ids = _role_requirement_ids(actor, rows)
            if ids:
                contracts.append(
                    {
                        "actor": actor,
                        "actor_component": f"Actor: {actor}",
                        "evidence_id": fact.id,
                        "requirement_ids": ids,
                    }
                )
    return contracts


def all_source_endpoint_components(access: list[dict], actors: list[dict]) -> list[dict]:
    """Extend access-domain cards with the other exact source actors and their own obligations."""
    nodes = {node["component_name"].casefold(): node for node in source_endpoint_components(access)}
    for role in actors:
        node = nodes.setdefault(
            role["actor_component"].casefold(),
            {
                "title": role["actor_component"],
                "component_name": role["actor_component"],
                "detail": (
                    f"Proposed logical endpoint for the source-stated actor: {role['actor']}."
                ),
                "responsibility": f"Represent the source-stated actor: {role['actor']}.",
                "status": "proposed",
                "sources": [],
                "evidence_ids": [],
                "requirement_ids": [],
            },
        )
        node["evidence_ids"] = sorted(set(node["evidence_ids"]) | {role["evidence_id"]})
        node["requirement_ids"] = sorted(
            set(node["requirement_ids"]) | set(role["requirement_ids"])
        )
    return list(nodes.values())


def _source_label_matches(node: dict, label: str, kind: str) -> bool:
    """Distinguish an actual role/resource endpoint from a service merely named after that role."""
    expected = _role_words(label)
    named = _role_words(node.get("component_name", "")) - {kind}
    return expected <= named and (
        node.get("responsibility", "").startswith(f"Represent the source-stated {kind}:")
        or named == expected
    )


def source_actor_architecture_issues(content: dict, contracts: list[dict]) -> list[str]:
    """Reject a source actor substituted for another role's request or trust boundary."""
    issues, allowed, matched = [], {}, {}
    for role in contracts:
        names = {
            node["component_name"]
            for node in content.get("items", [])
            if _source_label_matches(node, role["actor"], "actor")
            and role["evidence_id"] in node.get("evidence_ids", [])
            and set(role["requirement_ids"]) & set(node.get("requirement_ids", []))
        }
        matched[(role["evidence_id"], role["actor"])] = names
        if not names:
            issues.append(
                f"architecture:{role['evidence_id']}:missing_source_actor_endpoint:{role['actor']}"
            )
        for name in names:
            allowed.setdefault(name, set()).update(role["requirement_ids"])
    for flow in content.get("data_flows", []):
        actor = flow["from_component"]
        if actor in allowed and set(flow["requirement_ids"]) - allowed[actor]:
            issues.append("architecture:source_actor_flow_uses_wrong_role")
    for boundary in content.get("trust_boundaries", []):
        for key in ("untrusted_component", "trusted_component"):
            actor = boundary[key]
            if actor in allowed and set(boundary["requirement_ids"]) - allowed[actor]:
                issues.append("architecture:source_actor_boundary_uses_wrong_role")
    if content.get("data_flows"):
        for role in contracts:
            names = matched[(role["evidence_id"], role["actor"])]
            for rid in role["requirement_ids"]:
                owners = {
                    node["component_name"]
                    for node in content["items"]
                    if rid in node.get("requirement_ids", [])
                    and not node.get("responsibility", "").startswith("Represent the source-stated")
                    and node["component_name"] not in allowed
                }
                graph = {}
                for flow in content["data_flows"]:
                    if rid in flow["requirement_ids"]:
                        graph.setdefault(flow["from_component"], set()).add(flow["to_component"])
                reached, pending = set(names), list(names)
                while pending:
                    node = pending.pop()
                    for target in graph.get(node, set()) - reached:
                        reached.add(target)
                        pending.append(target)
                if names and not (reached - names) & owners:
                    issues.append(
                        f"architecture:{role['evidence_id']}:source_actor_request_path_missing:"
                        f"{role['actor']}:{rid}"
                    )
    return list(dict.fromkeys(issues))


def source_access_architecture_issues(
    content: dict,
    contracts: list[dict],
    *,
    require_paths: bool = True,
) -> list[str]:
    """Check endpoint identity and directed paths; enforcement meaning still needs review."""
    issues = []

    for contract in contracts:
        endpoints = {}
        for kind in ("actor", "resource"):
            endpoints[kind] = {
                node["component_name"]
                for node in content.get("items", [])
                if _source_label_matches(node, contract[kind], kind)
                and contract["evidence_id"] in node.get("evidence_ids", [])
                and set(contract["requirement_ids"]) & set(node.get("requirement_ids", []))
            }
            if not endpoints[kind]:
                issues.append(
                    f"architecture:{contract['evidence_id']}:missing_source_{kind}_endpoint:{contract[kind]}"
                )
        if not require_paths or not all(endpoints.values()):
            continue
        graph = {}
        for edge in content.get("data_flows", []):
            if set(edge.get("requirement_ids", [])) & set(contract["requirement_ids"]):
                graph.setdefault(edge["from_component"], set()).add(edge["to_component"])
        found = False
        owners = {
            node["component_name"]
            for node in content["items"]
            if set(node.get("requirement_ids", [])) & set(contract["requirement_ids"])
            and node["component_name"] not in endpoints["actor"] | endpoints["resource"]
            and not node.get("responsibility", "").startswith("Represent the source-stated")
        }
        for origin in endpoints["actor"]:
            reached, pending = set(), [(origin, False)]
            while pending:
                node, mediated = pending.pop()
                mediated = mediated or node in owners
                state = (node, mediated)
                if state in reached:
                    continue
                reached.add(state)
                if node in endpoints["resource"] and node != origin and mediated:
                    found = True
                pending.extend((target, mediated) for target in graph.get(node, set()))
        if not found:
            issues.append(
                f"architecture:{contract['evidence_id']}:missing_directed_source_access_path:{contract['resource']}"
            )
    return list(dict.fromkeys(issues))

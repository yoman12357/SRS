"""Compile necessary source paths from model-chosen canonical responsibility owners."""

from __future__ import annotations


def compile_source_paths(roles: list[dict], access: list[dict], routes: dict[str, str]) -> dict:
    """Construct source role requests and mediated decisions without inventing an interaction."""
    flows, boundaries = {}, {}
    # Match inventory identity while retaining the first literal source label.
    # A role at the start of a sentence is not a second domain merely because
    # its first letter is capitalized. Distinct role qualifiers remain distinct.
    endpoints = {}
    for contract in access + roles:
        for key in ("actor_component", "resource_component"):
            if key in contract:
                name = contract[key]
                endpoints.setdefault(name.casefold(), name)

    def add(mapping: dict, origin: str, target: str, rid: str) -> None:
        """Merge reference metadata for the same logical pair, retaining every canonical ID."""
        pair = (endpoints.get(origin.casefold(), origin), endpoints.get(target.casefold(), target))
        mapping.setdefault(pair, set()).add(rid)

    for role in roles:
        for rid in role["requirement_ids"]:
            add(flows, role["actor_component"], routes[rid], rid)
            add(boundaries, role["actor_component"], routes[rid], rid)
    for contract in access:
        for rid in contract["requirement_ids"]:
            owner = routes[rid]
            add(flows, contract["actor_component"], owner, rid)
            add(flows, owner, contract["resource_component"], rid)
            add(boundaries, contract["actor_component"], owner, rid)
    return {
        "data_flows": [
            {"from_component": origin, "to_component": target, "requirement_ids": sorted(ids)}
            for (origin, target), ids in flows.items()
        ],
        "trust_boundaries": [
            {
                "untrusted_component": origin,
                "trusted_component": target,
                "requirement_ids": sorted(ids),
            }
            for (origin, target), ids in boundaries.items()
        ],
    }


def internal_pair_obligations(placements: list[dict], canonical: dict[str, dict]) -> dict:
    """Allow additional coupling for shared duties or declared canonical dependencies."""
    allowed = {}
    for origin in placements:
        for target in placements:
            if origin is target:
                continue
            left, right = set(origin["requirement_ids"]), set(target["requirement_ids"])
            ids = left & right
            for rid in left:
                for dependency in canonical[rid]["dependencies"]:
                    if dependency in right:
                        ids.update({rid, dependency})
            for rid in right:
                for dependency in canonical[rid]["dependencies"]:
                    if dependency in left:
                        ids.update({rid, dependency})
            if ids:
                allowed[(origin["component_name"], target["component_name"])] = ids
    return allowed

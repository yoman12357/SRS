"""Deterministic evidence/link/coverage checks; never claim semantic proof."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from .acceptance_grounding import acceptance_logging_issues, acceptance_response_issues
from .architecture_sources import (
    source_access_architecture_issues,
    source_access_contracts,
    source_actor_architecture_issues,
    source_actor_contracts,
)
from .artifact_grounding import (
    LIST_FIELDS,
    TEXT_FIELDS,
    VALIDATION_POLICY_VERSION,
    claims_recorded_approval,
    lifecycle_criterion_issues,
    lifecycle_test_gaps,
    supported_risk_ratings,
    unsupported_delivery_guarantees,
    unsupported_quantities,
)
from .evidence import context_evidence_ids
from .introduction_projection import (
    INTRODUCTION_PROJECTION_VERSION,
    introduction_projection_issues,
)
from .management_scope import management_scope_issues
from .permission_verification import permission_test_gaps
from .policy_applicability import policy_adoption_is_explicit
from .prohibition_verification import prohibition_statement_is_faithful, prohibition_test_gaps
from .scenario_projection import SCENARIO_PROJECTION_VERSION, scenario_projection_issues
from .schemas import (
    REQUIREMENT_PREFIXES,
    Analysis,
    Document,
    Evidence,
    Finding,
    QualityReport,
    SourceChunk,
)
from .sdlc_validation import (
    confirmed_delivery_roles,
    validate_lifecycle_structure,
    validate_v_model,
)
from .semantics import (
    mentions_event_logging,
    missing_source_actions,
    missing_source_quantities,
    project_request_recast_as_runtime_behavior,
    semantic_issues,
    unsupported_actor_exclusivity,
    unsupported_architecture_choices,
    unsupported_wait_condition,
)
from .source_facts import preserve_scope_evidence as preserve_scope_evidence
from .verification_projection import (
    VERIFICATION_PROJECTION_VERSION,
    verification_projection_issues,
)


def assign_ids(section: str, content: dict, offset: int = 0) -> dict:
    """Assign deterministic IDs before dependent agents can reference a section."""
    if section in REQUIREMENT_PREFIXES:
        field, prefix = "requirements", REQUIREMENT_PREFIXES[section]
    elif section in {"threats", "risks", "scenarios", "verification", "compliance"}:
        field, prefix = {
            "threats": ("threats", "THR"),
            "risks": ("risks", "RISK"),
            "scenarios": ("scenarios", "UC"),
            "verification": ("tests", "TEST"),
            "compliance": ("mappings", "CMP"),
        }[section]
    else:
        return content
    for index, item in enumerate(content[field], start=1):
        item["id"] = f"{prefix}-{index + offset:03d}"
    return content


def requirements_from(sections: dict) -> list[dict]:
    """Collect every canonical requirement without truncation or quota padding."""
    return [
        req
        for section in REQUIREMENT_PREFIXES
        for req in sections.get(section, {}).get("requirements", [])
    ]


def consolidate_duplicates(content: dict, predecessors: dict) -> dict:
    """Intern exact repeated controls while preserving their authored acceptance and basis."""
    result = deepcopy(content)
    registry = {
        re.sub(r"\s+", " ", req["statement"].casefold()).strip(): req
        for req in requirements_from(predecessors)
    }
    result.setdefault("related_requirement_ids", [])
    result.setdefault("related_acceptance_criteria", [])
    unique = []
    for req in result["requirements"]:
        key = re.sub(r"\s+", " ", req["statement"].casefold()).strip()
        previous = registry.get(key)
        if (
            previous is None
            or previous["priority"] != req["priority"]
            or not set(req["evidence_ids"]).issubset(previous["evidence_ids"])
        ):
            unique.append(req)
            continue
        if previous["id"] not in result["related_requirement_ids"]:
            result["related_requirement_ids"].append(previous["id"])
        result["related_acceptance_criteria"].append(
            {
                "requirement_id": previous["id"],
                **{
                    key: req[key]
                    for key in (
                        "title",
                        "rationale",
                        "dimensions",
                        "evidence_ids",
                        "sources",
                        "acceptance_criteria",
                        "unresolved_decisions",
                    )
                },
            }
        )
    result["requirements"] = unique
    return result


def interactive_requirement_ids(requirements: list[dict], analysis: Analysis) -> set[str]:
    """Require stories for evidenced actor interactions, excluding background-only controls."""
    roles = {
        word.rstrip("s")
        for role in analysis.stakeholders
        for word in role.casefold().split()
        if len(word) > 3
    }
    result = set()
    for req in requirements:
        text = req["statement"].casefold()
        actor_present = any(re.search(rf"\b{re.escape(role)}s?\b", text) for role in roles)
        interaction = re.search(
            r"\b(?:allow\w*|permit\w*|enable\w*|prevent\w*|den(?:y|ied)|restrict\w*|may|can)\b",
            text,
        )
        if actor_present and interaction:
            result.add(req["id"])
    return result


def rebuild_functional_view(sections: dict, analysis: Analysis) -> None:
    """Index canonical actor interactions without duplicating their normative content."""
    functional = sections.get("functional")
    if functional is None:
        return
    own_ids = {item["id"] for item in functional["requirements"]}
    related = interactive_requirement_ids(requirements_from(sections), analysis) - own_ids
    functional["related_requirement_ids"] = sorted(
        set(functional.get("related_requirement_ids", [])) | related
    )
    if related and not functional["requirements"]:
        functional["applicability_reason"] = (
            "Actor-visible behaviors are specified by the linked canonical requirements. "
            "Their statements and acceptance criteria remain in their owning sections."
        )


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _walk(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk(nested)


def _numbers(text: str) -> set[str]:
    text = re.sub(r"\b(?:FR|NFR|SEC|DR|NET|E|THR|RISK|UC|TEST)-\d+\b", "", text)
    return set(re.findall(r"(?<!\w)\d+(?:\.\d+)?(?:%|ms|s)?\b", text))


def validate_section(
    name: str,
    content: dict,
    evidence: list[Evidence],
    analysis: Analysis,
    sources: list[SourceChunk],
    predecessors: dict,
    *,
    known_requirement_ids: set[str] | None = None,
) -> list[str]:
    """Check one specialist output before sharing it with the next specialist."""
    errors: list[str] = []
    evidence_map = {item.id: item.quote for item in evidence}
    source_map = {item.id: item for item in sources}
    assessment = {item.evidence_id: item for item in analysis.assessments}
    requirements = requirements_from(predecessors) + requirements_from({name: content})
    known = {item["id"] for item in requirements} | (known_requirement_ids or set())
    for item in _walk(content):
        item_id = item.get("id", name)
        evidence_ids = item.get("evidence_ids", [])
        exact_fact = name == "introduction" and any(
            item.get("detail") == evidence_map.get(eid) for eid in evidence_ids
        )
        if "detail" in item and len(item["detail"]) < 8 and not exact_fact:
            errors.append(f"{item_id}:narrative_detail_too_short")
        if set(evidence_ids) - evidence_map.keys():
            errors.append(f"{item_id}:unknown_evidence_id")
        for citation in item.get("sources", []):
            chunk = source_map.get(citation["chunk_id"])
            if chunk is None:
                errors.append(f"{item_id}:unknown_source_chunk")
            elif citation["quote"] not in chunk.text:
                errors.append(f"{item_id}:citation_quote_not_in_chunk")
        for field in (
            "dependencies",
            "requirement_ids",
            "control_requirement_ids",
            "related_requirement_ids",
        ):
            if set(item.get(field, [])) - known:
                errors.append(f"{item_id}:unknown_{field}")
        if "requirement_id" in item and item["requirement_id"] not in known:
            errors.append(f"{item_id}:unknown_requirement_id")
        if item.get("status") == "confirmed" and not evidence_ids:
            errors.append(f"{item_id}:confirmed_claim_without_user_evidence")
        texts = []
        for field in TEXT_FIELDS:
            if isinstance(item.get(field), str):
                text = item[field]
                if exact_fact and field == "title":
                    for fact in evidence:
                        suffix = " — response to: " + fact.context
                        if fact.id in evidence_ids and fact.context and text.endswith(suffix):
                            text = text[: -len(suffix)]
                            break
                texts.append(text)
        for field in LIST_FIELDS:
            for text in item.get(field, []):
                if isinstance(text, str):
                    texts.append(text)
        support = " ".join(evidence_map[eid] for eid in evidence_ids if eid in evidence_map)
        for text in texts:
            errors.extend(f"{item_id}:{issue}" for issue in semantic_issues(text, evidence))
            errors.extend(
                f"{item_id}:{issue}" for issue in unsupported_delivery_guarantees(text, evidence)
            )
            if unsupported_quantities(text, evidence):
                errors.append(f"{item_id}:unsupported_quantitative_commitment")
            if unsupported_actor_exclusivity(support or " ".join(evidence_map.values()), text):
                errors.append(f"{item_id}:unconfirmed_actor_exclusivity")
        if "human_approval" in item and claims_recorded_approval(item["human_approval"]):
            errors.append(f"{item_id}:workflow_claims_recorded_approval")
    if name in REQUIREMENT_PREFIXES:
        canonical = {req["id"]: req for req in requirements}
        for related in content.get("related_acceptance_criteria", []):
            req = canonical.get(related["requirement_id"])
            if req is None:
                continue
            eids = related.get("evidence_ids") or req["evidence_ids"]
            support = " ".join(evidence_map.get(eid, "") for eid in eids)
            for criterion in related["acceptance_criteria"]:
                errors.extend(
                    f"{req['id']}:{issue}"
                    for issue in management_scope_issues(
                        support,
                        " ".join(criterion[key] for key in ("when", "then", "observable_evidence")),
                    )
                )
                errors.extend(
                    f"{req['id']}:{issue}"
                    for issue in acceptance_logging_issues(support, criterion)
                )
                errors.extend(
                    f"{req['id']}:{issue}"
                    for issue in lifecycle_criterion_issues(support, criterion)
                )
        seen = {
            re.sub(r"\W", "", r["statement"].casefold()) for r in requirements_from(predecessors)
        }
        for req in content["requirements"]:
            if any(
                project_request_recast_as_runtime_behavior(
                    evidence_map.get(eid, ""), req["statement"]
                )
                for eid in req["evidence_ids"]
            ):
                errors.append(f"{req['id']}:project_request_recast_as_runtime_behavior")
            key = re.sub(r"\W", "", req["statement"].casefold())
            if key in seen:
                errors.append(
                    f"{req['id']}:duplicate_requirement; reuse the existing canonical "
                    "ID in related_requirement_ids instead of repeating the statement"
                )
            seen.add(key)
            if not re.search(
                r"\b(?:shall|should|must|required|may|can|cannot)\b", req["statement"], re.I
            ) and not re.match(
                r"^(?:do not|never|prohibit|forbid|prevent)\b", req["statement"], re.I
            ):
                errors.append(f"{req['id']}:missing_normative_behavior")
            if req["basis"] != "proposed" and not req["evidence_ids"]:
                errors.append(f"{req['id']}:missing_authoritative_basis")
            if req["basis"] == "explicit" and any(
                assessment.get(eid) is not None
                and assessment[eid].kind in {"uncertain", "conflict"}
                for eid in req["evidence_ids"]
            ):
                errors.append(f"{req['id']}:uncertain_input_treated_as_explicit")
            linked_evidence = [item for item in evidence if item.id in req["evidence_ids"]]
            support = " ".join(item.quote for item in linked_evidence)
            management_text = " ".join(
                [req["title"], req["statement"]]
                + [
                    criterion[key]
                    for criterion in req["acceptance_criteria"]
                    for key in ("when", "then", "observable_evidence")
                ]
            )
            errors.extend(
                f"{req['id']}:{issue}"
                for issue in management_scope_issues(support, management_text)
            )
            if linked_evidence and all(
                item.id in context_evidence_ids(evidence) for item in linked_evidence
            ):
                errors.append(f"{req['id']}:project_context_not_product_requirement")
            for original in linked_evidence:
                if not prohibition_statement_is_faithful(original.quote, req["statement"]):
                    errors.append(f"{req['id']}:explicit_prohibition_must_preserve_original_scope")
            if req["basis"] == "explicit":
                for original in linked_evidence:
                    if (
                        re.match(r"^(?:(?:all|the)\s+)?employees?\b", original.quote, re.I)
                        and re.search(
                            r"\bauthenticat\w*|\bmfa\b|\bmulti.factor\b",
                            original.quote,
                            re.I,
                        )
                        and not re.search(r"\bemployees?\b", req["statement"], re.I)
                    ):
                        errors.append(f"{req['id']}:explicit_authentication_actor_not_preserved")
                    if re.search(r"\bmanually\b", original.quote, re.I):
                        if not re.search(r"\bmanual(?:ly)?\b", req["statement"], re.I):
                            errors.append(f"{req['id']}:explicit_manual_mode_not_preserved")
                        if "administrator" in original.quote.casefold() and not re.search(
                            r"\badmin(?:istrator)?s?\b",
                            req["statement"],
                            re.I,
                        ):
                            errors.append(f"{req['id']}:explicit_actor_not_preserved")
                if (
                    linked_evidence
                    and all(
                        assessment.get(item.id) is not None
                        and assessment[item.id].kind == "exclusion"
                        for item in linked_evidence
                    )
                    and not re.search(
                        r"\b(?:not|never|deny|denied|prohibit|prevent|exclude|forbid|without)\b",
                        req["statement"],
                        re.I,
                    )
                ):
                    errors.append(f"{req['id']}:exclusion_recast_as_affirmative_behavior")
                if linked_evidence and all(
                    assessment.get(item.id) is not None and assessment[item.id].kind == "exclusion"
                    for item in linked_evidence
                ):
                    source_text = " ".join(item.quote for item in linked_evidence)
                    if re.search(
                        r"\b(?:if|when|unless)\b", req["statement"], re.I
                    ) and not re.search(r"\b(?:if|when|unless)\b", source_text, re.I):
                        errors.append(f"{req['id']}:unsupported_condition_on_explicit_exclusion")
            support = " ".join(evidence_map.get(eid, "") for eid in req["evidence_ids"])
            support += " ".join(citation["quote"] for citation in req["sources"])
            if (
                req["basis"] == "explicit"
                and re.search(
                    r"\b(?:log(?:ged|ging|s)?|audit(?:able|ed|ing)?)\b",
                    req["statement"],
                    re.I,
                )
                and not re.search(r"\b(?:record\w*|log\w*|audit\w*)\b", support, re.I)
            ):
                errors.append(f"{req['id']}:unconfirmed_additional_audit_behavior")
            text = (
                req["statement"]
                + " "
                + " ".join(criterion["then"] for criterion in req["acceptance_criteria"])
            )
            if unsupported_actor_exclusivity(support, text):
                errors.append(f"{req['id']}:unconfirmed_actor_exclusivity")
            if unsupported_wait_condition(support, text):
                errors.append(f"{req['id']}:unconfirmed_waiting_period_condition")
            if _numbers(text) - _numbers(support):
                errors.append(f"{req['id']}:unsupported_numeric_specificity")
            if re.search(
                r"\b(?:immediately|instantaneously|real.time)\b", text, re.I
            ) and not re.search(
                r"\b(?:immediately|instantaneously|real.time)\b",
                support,
                re.I,
            ):
                errors.append(f"{req['id']}:unsupported_response_time_commitment")
            for qualifier in (r"minimum(?: of)?", r"maximum(?: of)?", "at least", "at most"):
                if re.search(rf"\b{qualifier}\s+[0-9]", text, re.I) and not re.search(
                    rf"\b{qualifier}\s+[0-9]",
                    support,
                    re.I,
                ):
                    errors.append(f"{req['id']}:unsupported_numeric_bound")
            for criterion in req["acceptance_criteria"]:
                errors.extend(
                    f"{req['id']}:{issue}"
                    for issue in acceptance_response_issues(support, criterion)
                )
                errors.extend(
                    f"{req['id']}:{issue}"
                    for issue in acceptance_logging_issues(support, criterion)
                )
                errors.extend(
                    f"{req['id']}:{issue}"
                    for issue in lifecycle_criterion_issues(support, criterion)
                )
                witness = criterion["observable_evidence"]
                concrete_artifact = re.search(
                    r"\b(?:captur\w*|snapshot\w*|timestamp\w*|dated|packet\w*|trace\w*|"
                    r"response\w*|report\w*|query|log entry|record of|read.back)\b",
                    witness,
                    re.I,
                )
                if (witness.casefold() == req["statement"].casefold()) or (
                    re.match(r"the system (?:shall|must)\b", witness, re.I)
                    and not concrete_artifact
                ):
                    errors.append(f"{req['id']}:verification_evidence_repeats_requirement")
                if re.fullmatch(
                    r"(?:at any time|in real.time|during normal operating hours|"
                    r"during an access attempt)",
                    criterion["when"],
                    re.I,
                ):
                    errors.append(f"{req['id']}:verification_action_is_only_a_time_phrase")
                if re.search(
                    r"\b(?:works? (?:correctly|as expected)|appropriate results?|"
                    r"meets? (?:the )?requirements?|functions? properly)\b",
                    criterion["then"],
                    re.I,
                ):
                    errors.append(f"{req['id']}:unobservable_acceptance_criterion")
                if criterion["then"].casefold() == req["statement"].casefold():
                    errors.append(f"{req['id']}:acceptance_repeats_requirement")
            if req["id"] in req["dependencies"]:
                errors.append(f"{req['id']}:self_dependency")
        covered = {eid for req in requirements for eid in req["evidence_ids"]}
        for item in analysis.assessments:
            if name in item.sections and item.evidence_id in covered:
                linked_criteria = [
                    ac
                    for req in requirements
                    if item.evidence_id in req["evidence_ids"]
                    for ac in req["acceptance_criteria"]
                ]
                for gap in prohibition_test_gaps(
                    evidence_map.get(item.evidence_id, ""), linked_criteria
                ):
                    errors.append(f"{item.evidence_id}:{gap}")
            if item.kind in {"requirement", "constraint"} and name in item.sections:
                if item.evidence_id not in covered:
                    errors.append(f"{item.evidence_id}:missing_{name}_coverage")
                else:
                    linked_criteria = [
                        criterion
                        for req in requirements
                        if item.evidence_id in req["evidence_ids"]
                        for criterion in req["acceptance_criteria"]
                    ]
                    for gap in permission_test_gaps(
                        evidence_map.get(item.evidence_id, ""), linked_criteria
                    ):
                        errors.append(f"{item.evidence_id}:{gap}")
                    for gap in lifecycle_test_gaps(
                        evidence_map.get(item.evidence_id, ""), linked_criteria
                    ):
                        errors.append(f"{item.evidence_id}:{gap}")
                    represented = " ".join(
                        req["statement"]
                        + " "
                        + " ".join(criterion["then"] for criterion in req["acceptance_criteria"])
                        for req in requirements
                        if item.evidence_id in req["evidence_ids"]
                    )
                    for action in missing_source_actions(
                        evidence_map.get(item.evidence_id, ""),
                        represented,
                        include_capabilities=True,
                    ):
                        errors.append(f"{item.evidence_id}:missing_{name}_behavior_{action}")
                    for metric in missing_source_quantities(
                        evidence_map.get(item.evidence_id, ""),
                        represented,
                    ):
                        errors.append(f"{item.evidence_id}:missing_{name}_metric_{metric}")
    if name == "introduction":
        for claim in content["items"]:
            if not any(claim["detail"] == evidence_map.get(eid) for eid in claim["evidence_ids"]):
                errors.append("introduction:fact_detail_must_match_its_source_passage")
        for item in analysis.assessments:
            if item.kind == "exclusion" and not any(
                item.evidence_id in claim["evidence_ids"]
                and re.search(
                    r"\b(?:out.of.scope|exclu\w*|prohibit\w*|shall not|must not|"
                    r"do not|never|not permitted)\b",
                    claim["title"] + " " + claim["detail"],
                    re.I,
                )
                for claim in content["items"]
            ):
                errors.append(f"{item.evidence_id}:missing_explicit_exclusion")
    if name == "compliance":
        for mapping in content["mappings"]:
            if mapping["applicability"] == "confirmed":
                support = " ".join(evidence_map.get(eid, "") for eid in mapping["evidence_ids"])
                framework = re.sub(r"\W", "", mapping["framework_or_policy"].casefold())
                if (
                    not framework
                    or framework not in re.sub(r"\W", "", support.casefold())
                    or not (policy_adoption_is_explicit(support))
                ):
                    errors.append(f"{mapping['id']}:unconfirmed_framework_applicability")
                if not mapping["sources"]:
                    errors.append(f"{mapping['id']}:missing_compliance_source")
    if name == "risks":
        for risk in content["risks"]:
            linked = [item for item in evidence if item.id in risk["evidence_ids"]]
            for field in ("likelihood", "impact"):
                if risk[field] not in supported_risk_ratings(field, linked):
                    errors.append(f"{risk['id']}:risk_rating_without_source_basis")
    if name == "architecture":
        if source_access_contracts(evidence, requirements):
            errors.extend(
                source_actor_architecture_issues(
                    content, source_actor_contracts(evidence, requirements)
                )
            )
        errors.extend(
            source_access_architecture_issues(
                content,
                source_access_contracts(evidence, requirements),
                require_paths=bool(content.get("data_flows")),
            )
        )
        design = (
            content["summary"]
            + " "
            + " ".join(
                str(value)
                for field in ("items", "data_flows", "trust_boundaries")
                for item in content.get(field, [])
                for key, value in item.items()
                if key
                in {"detail", "component_name", "responsibility", "data_or_action", "enforcement"}
            )
        )
        for field in ("items", "data_flows", "trust_boundaries"):
            if not content.get(field):
                errors.append(f"architecture:missing_{field}")
            for claim in content.get(field, []):
                if claim.get("status") != "proposed":
                    errors.append("architecture:design_requires_proposed_status")
                if not claim.get("requirement_ids"):
                    errors.append(f"architecture:{field}_needs_requirement_links")
                claim_text = " ".join(
                    str(claim.get(key, ""))
                    for key in (
                        "detail",
                        "responsibility",
                        "data_or_action",
                        "enforcement",
                    )
                )
                support = (
                    " ".join(evidence_map.get(eid, "") for eid in claim.get("evidence_ids", []))
                    + " "
                    + " ".join(
                        req["statement"]
                        for req in requirements
                        if req["id"] in claim.get("requirement_ids", [])
                    )
                )
                if mentions_event_logging(claim_text) and not (
                    mentions_event_logging(support)
                    or "recording" in missing_source_actions(support, "")
                ):
                    errors.append(f"architecture:{field}_unrequested_logging")
        if re.search(r"\b(?:immediately|instantaneously|real.time)\b", design, re.I) and not any(
            re.search(r"\b(?:immediately|instantaneously|real.time)\b", item.quote, re.I)
            for item in evidence
        ):
            errors.append("architecture:unsupported_response_time_commitment")
        components = {
            item.get("component_name", "").casefold()
            for item in content.get("items", [])
            if item.get("component_name", "").strip()
        }
        if len(components) < 2:
            errors.append("architecture:boundary_requires_two_distinct_logical_nodes")
        for boundary in content.get("trust_boundaries", []):
            if (
                boundary.get("untrusted_component", "").strip().casefold()
                == boundary.get("trusted_component", "").strip().casefold()
            ):
                errors.append("architecture:trust_boundary_needs_distinct_domains")
        if len(components) != len(content.get("items", [])):
            errors.append("architecture:component_names_must_be_nonempty_and_unique")
        for item in content.get("items", []):
            if (
                not item.get("component_name", "").strip()
                or not item.get("responsibility", "").strip()
            ):
                errors.append("architecture:component_needs_name_and_responsibility")
        for field, endpoints, detail_field in (
            ("data_flows", ("from_component", "to_component"), "data_or_action"),
            ("trust_boundaries", ("untrusted_component", "trusted_component"), "enforcement"),
        ):
            for item in content.get(field, []):
                if not item.get(detail_field, "").strip():
                    errors.append(f"architecture:{field}_needs_{detail_field}")
                for endpoint in endpoints:
                    if item.get(endpoint, "").casefold() not in components:
                        errors.append(f"architecture:{field}_unknown_{endpoint}")
        mapped = {
            rid
            for field in ("items", "data_flows", "trust_boundaries")
            for item in content.get(field, [])
            for rid in item.get("requirement_ids", [])
        }
        for rid in sorted(known - mapped):
            errors.append(f"{rid}:missing_architecture_coverage")
        for choice in unsupported_architecture_choices(design, evidence):
            errors.append(f"architecture:unrequested_architecture_choice_{choice}")
        errors.extend(f"architecture:{issue}" for issue in semantic_issues(design, evidence))
    if name in {"scenarios", "verification", "sdlc"}:
        field = {"scenarios": "scenarios", "verification": "tests", "sdlc": "phases"}[name]
        mapped = {rid for item in content[field] for rid in item["requirement_ids"]}
        expected = (
            known if name != "scenarios" else interactive_requirement_ids(requirements, analysis)
        )
        for requirement_id in sorted(expected - mapped):
            errors.append(f"{requirement_id}:missing_{name}_coverage")
    if name == "sdlc":
        test_pattern = r"\b(?:TC|TEST)-?[0-9]+\b"
        known_tests = {test["id"] for test in predecessors.get("verification", {}).get("tests", [])}
        known_tests.update(re.findall(test_pattern, " ".join(item.quote for item in evidence)))
        if set(re.findall(test_pattern, str(content))) - known_tests:
            errors.append("sdlc:unknown_verification_test_reference")
        if content["selected_model"] == "V-Model":
            errors.extend(validate_v_model(content, known))
        if re.search(r"\bformal verification\b", content["justification"], re.I) and not any(
            re.search(r"\bformal verification\b", item.quote, re.I) for item in evidence
        ):
            errors.append("sdlc:independent_verification_is_not_formal_verification")

        def role_key(value: str) -> str:
            """Compare singular/plural source role labels without assigning new roles."""
            return re.sub(r"\W", "", value.casefold()).rstrip("s")

        errors.extend(validate_lifecycle_structure(content))
        for phase in content["phases"]:
            source_roles = {
                role_key(role)
                for role in confirmed_delivery_roles(
                    " ".join(item.quote for item in evidence),
                    analysis.stakeholders,
                    phase.get("phase_type"),
                )
            }
            for role in phase["roles"]:
                if role_key(role) not in source_roles and not re.match(
                    r"^(?:proposed|tbd)\b", role, re.I
                ):
                    errors.append("sdlc:unconfirmed_role_needs_proposed_label")
            if content["selected_model"] == "Agile" and any(
                re.search(r"\bno new requirement changes?\b", text, re.I)
                for text in phase["exit_criteria"]
            ):
                errors.append("sdlc:agile_exit_cannot_require_future_changes_to_stop")
    return sorted(set(errors))


def validate_document(document: Document) -> QualityReport:
    """Recompute all deterministic checks and trace rows from the exact final content."""
    payload = document.model_dump()
    findings: list[Finding] = []
    checks_total = 0
    errors = 0
    preceding: dict = {}
    all_ids = {req["id"] for req in requirements_from(payload)}
    section_names = [
        "introduction",
        *REQUIREMENT_PREFIXES,
        "compliance",
        "architecture",
        "threats",
        "risks",
        "scenarios",
        "verification",
        "glossary",
        "sdlc",
    ]
    for section in section_names:
        result = validate_section(
            section,
            payload[section],
            document.evidence,
            document.analysis,
            document.sources,
            preceding,
            known_requirement_ids=all_ids,
        )
        if section == "verification" and document.verification_projection_version:
            if document.verification_projection_version != VERIFICATION_PROJECTION_VERSION:
                result.append("verification:unsupported_projection_version")
            else:
                result += verification_projection_issues(payload[section], payload)
        if section == "scenarios" and document.scenario_projection_version:
            if document.scenario_projection_version != SCENARIO_PROJECTION_VERSION:
                result.append("scenarios:unsupported_projection_version")
            else:
                result += scenario_projection_issues(
                    payload[section], payload, document.evidence, document.analysis
                )
        if section == "introduction" and document.introduction_projection_version:
            if document.introduction_projection_version != INTRODUCTION_PROJECTION_VERSION:
                result.append("introduction:unsupported_projection_version")
            else:
                result += introduction_projection_issues(
                    payload[section], document.evidence, document.analysis
                )
        checks_total += 1
        errors += bool(result)
        for code in result:
            findings.append(
                Finding(
                    code=code,
                    severity="error",
                    section=section,
                    item_id=code.split(":")[0],
                    message=code.replace("_", " "),
                )
            )
        preceding[section] = payload[section]
    all_requirements = requirements_from(payload)
    if not all_requirements:
        findings.append(
            Finding(
                code="no_requirements",
                severity="error",
                section="functional",
                item_id="",
                message="No requirements were generated",
            )
        )
        errors += 1
    checks_total += 1
    ids = [req["id"] for req in all_requirements]
    if len(set(ids)) != len(ids):
        findings.append(
            Finding(
                code="duplicate_ids",
                severity="error",
                section="requirements",
                item_id="",
                message="Canonical requirement IDs are not unique",
            )
        )
        errors += 1
    checks_total += 1
    if document.sdlc.selected_model != document.sdlc_candidates[0].model:
        findings.append(
            Finding(
                code="sdlc_winner_changed",
                severity="error",
                section="sdlc",
                item_id="",
                message="Explanation changed the deterministic winner",
            )
        )
        errors += 1
    checks_total += 1
    coverage: dict[str, list[str]] = {
        item.id: [req["id"] for req in all_requirements if item.id in req["evidence_ids"]]
        for item in document.evidence
    }
    for assessment in document.analysis.assessments:
        if (
            assessment.kind in {"requirement", "constraint"}
            and not coverage[assessment.evidence_id]
        ):
            # Constraints can legitimately be document/project constraints in introduction.
            represented = any(
                assessment.evidence_id in item.evidence_ids for item in document.introduction.items
            )
            lifecycle_factor = any(
                assessment.evidence_id in factor.evidence_ids for factor in document.sdlc_factors
            )
            lifecycle_only = lifecycle_factor and set(assessment.sections) <= {
                "sdlc",
                "introduction",
            }
            if not lifecycle_only and (assessment.kind == "requirement" or not represented):
                findings.append(
                    Finding(
                        code="uncovered_input",
                        severity="error",
                        section="introduction",
                        item_id=assessment.evidence_id,
                        message="Original normative input is uncovered",
                    )
                )
                errors += 1
        if assessment.kind in {"uncertain", "conflict"}:
            findings.append(
                Finding(
                    code="unresolved_input",
                    severity="warning",
                    section="introduction",
                    item_id=assessment.evidence_id,
                    message="Stakeholder decision remains unresolved",
                )
            )
    checks_total += len(document.analysis.assessments)
    traceability = []
    for req in all_requirements:
        traceability.append(
            {
                "requirement_id": req["id"],
                "evidence_ids": req["evidence_ids"],
                "source_chunks": [citation["chunk_id"] for citation in req["sources"]],
                "scenario_ids": [
                    s.id for s in document.scenarios.scenarios if req["id"] in s.requirement_ids
                ],
                "test_ids": [
                    t.id for t in document.verification.tests if req["id"] in t.requirement_ids
                ],
                "sdlc_phases": [
                    p.name for p in document.sdlc.phases if req["id"] in p.requirement_ids
                ],
            }
        )
    findings.append(
        Finding(
            code="human_semantic_review_required",
            severity="warning",
            section="document",
            item_id="",
            message="Review completeness, actor permissions, contradictions and citation "
            "applicability; "
            "schema and link checks do not prove semantic correctness.",
        )
    )
    return QualityReport(
        validation_policy_version=VALIDATION_POLICY_VERSION,
        status="invalid" if errors else "needs_review",
        checks_passed=max(0, checks_total - errors),
        checks_total=checks_total,
        findings=findings,
        evidence_coverage=coverage,
        traceability=traceability,
    )

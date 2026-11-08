"""Batch source-bound authoring without repeatedly generating canonical metadata."""

import re
from threading import Event
from typing import Literal

from pydantic import Field, create_model

from . import prompts
from .acceptance_grounding import preserve_source_outcome
from .artifact_grounding import unsupported_quantities
from .category_metadata import empty_category_metadata
from .evidence import normative_evidence_ids
from .permission_verification import permission_gap_action, permission_test_contract
from .prohibition_verification import prohibition_test_contract
from .provider import GenerationError, LLMProvider
from .quantity_normalization import preserve_section_retention
from .schemas import (
    Analysis,
    Evidence,
    RequirementsSection,
    SourceChunk,
    StrictModel,
)
from .semantics import missing_source_actions, missing_source_quantities
from .validation import assign_ids, consolidate_duplicates, requirements_from, validate_section

COMPACT_REQUIREMENTS_VERSION = "source-batch-1.3"
REPAIR_CAPTURE_OPTIONS = (
    "Test capture of the resulting response",
    "Test capture of the resulting state",
    "Test capture of the observed result",
)


class SourceRequirementDraft(StrictModel):
    """Only substantive authored content; identifiers and basis are coordinator metadata."""

    statement: str = Field(min_length=20)
    tests: list["CompactCriterion"] = Field(min_length=1)
    unresolved_decisions: list[str]


class CompactCriterion(StrictModel):
    """Concise authored test fields; same public acceptance contract and semantic gates."""

    given: str = Field(min_length=8, max_length=150)
    when: str = Field(min_length=8, max_length=150)
    then: str = Field(min_length=12, max_length=240)
    method: Literal["test", "inspection", "analysis", "demonstration"]
    observable_evidence: str = Field(min_length=10, max_length=200)


def generate_compact_requirements(
    provider: LLMProvider,
    name: str,
    evidence: list[Evidence],
    analysis: Analysis,
    sources: list[SourceChunk],
    predecessors: dict,
    cancel: Event,
    deadline: float,
) -> tuple[dict, dict]:
    """Author uncovered source behaviors together and pass the unchanged canonical gates."""
    prior = requirements_from(predecessors)
    normative = normative_evidence_ids(evidence)
    assigned = {
        item.evidence_id
        for item in analysis.assessments
        if name in item.sections
        and (
            item.kind in {"requirement", "constraint", "exclusion"} or item.evidence_id in normative
        )
        and item.kind not in {"uncertain", "conflict"}
    }
    selected = []
    for item in evidence:
        if item.id not in assigned:
            continue
        represented = " ".join(row["statement"] for row in prior if item.id in row["evidence_ids"])
        if (
            not represented
            or missing_source_actions(item.quote, represented, include_capabilities=True)
            or missing_source_quantities(item.quote, represented)
        ):
            selected.append(item)
    relevant = [row for row in prior if set(row["evidence_ids"]) & assigned]
    metadata = empty_category_metadata(name, relevant, prior)
    source_quotes = {item.id: item.quote for item in evidence}

    def compose(draft: StrictModel) -> dict:
        """Preserve model statements and every test verbatim in the public canonical shape."""
        dimensions = {
            "functional": "business",
            "nonfunctional": "availability",
            "security": "security",
            "data": "data",
            "network": "integration",
        }
        content = {
            "applicability_reason": "Source-backed obligations; unspecified decisions remain open.",
            "requirements": [
                {
                    "id": "",
                    "title": row["statement"].removeprefix("The system shall "),
                    "statement": row["statement"],
                    "rationale": f"Implements stakeholder source {eid}.",
                    "priority": "should"
                    if re.search(r"\bshould\b", source_quotes[eid], re.I)
                    and not re.search(r"\b(?:must|shall)\b", source_quotes[eid], re.I)
                    else "must",
                    "dimensions": [dimensions[name]],
                    "basis": "explicit",
                    "evidence_ids": [eid],
                    "sources": [],
                    "dependencies": [],
                    "acceptance_criteria": [
                        preserve_source_outcome(source_quotes[eid], test) for test in row["tests"]
                    ],
                    "unresolved_decisions": row["unresolved_decisions"],
                }
                for eid, row in draft.model_dump().items()
            ],
            "related_requirement_ids": metadata["required_requirement_ids"],
            "related_acceptance_criteria": [],
        }
        return assign_ids(
            name,
            consolidate_duplicates(preserve_section_retention(content, evidence), predecessors),
        )

    if not selected:
        content = RequirementsSection(
            applicability_reason=metadata["applicability_reason"],
            requirements=[],
            related_requirement_ids=metadata["required_requirement_ids"],
        ).model_dump()
        issues = validate_section(name, content, evidence, analysis, sources, predecessors)
        if not issues:
            return content, {
                "model": provider.model_name,
                "output_models": [],
                "attempts": 0,
                "compiled_canonical_index": True,
                "compact_requirements_version": COMPACT_REQUIREMENTS_VERSION,
            }

    schema = create_model(
        "SourceRequirementBatch",
        __base__=StrictModel,
        __doc__="Exactly one source-bound group for each assigned evidence passage.",
        **{item.id: (SourceRequirementDraft, ...) for item in selected},
    )

    def validate(candidate: StrictModel) -> list[str]:
        """Check literal source binding, all coverage and full acceptance semantics."""
        return validate_section(name, compose(candidate), evidence, analysis, sources, predecessors)

    system = (
        prompts.COMMON + "\nReturn the exact source-ID keyed object. Each value contains "
        "a normative statement covering that source and SHORT authored acceptance tests. "
        "A statement must contain an explicit normative modal such as shall or should. "
        "Use 'The system shall ...' followed by the requested product behavior. "
        "Each E-ID is bound to its own exact evidence quote. Cover that quote's actions "
        "in its statement; never shuffle, combine or substitute neighboring passages. "
        "Begin from that passage's own wording and preserve its actors and objects. "
        "A request to design/build/develop a system describes the project, not a runtime "
        "feature. State what that requested system provides or does; never say that "
        "the system shall design/build/develop itself. "
        "Every distinct action needs a test. WHEN initiates that action; GIVEN is baseline "
        "fixture state; THEN observes its pass/fail outcome. Preserve permitted and denied "
        "sides. Keep source actors and manual/automatic mode. Detection does not imply "
        "lockout or termination. Do not prescribe messages, fields, interfaces or databases. "
        "No added logs, time windows, numbers or real-time promises. Unspecified thresholds "
        "are named parameters with unresolved values. Each field should be one short clause. "
        "Use external test captures for witnesses, not production logs or E-ID text. "
        "Example style ONLY: source 'Operators review alerts.' -> statement 'The system "
        "shall allow operators to review alerts.', test {given:'An operator and test alert', "
        "when:'The operator requests alert review', then:'The requested alert is returned', "
        "method:'test', observable_evidence:'Test capture of the alert response'}. "
        "Do not copy this example into the project."
    )
    contracts = {
        item.id: {
            "permissions": permission_test_contract(item.quote),
            "prohibitions": prohibition_test_contract(item.quote),
        }
        for item in selected
    }
    contracts = {eid: contract for eid, contract in contracts.items() if any(contract.values())}
    if contracts:
        system += (
            " Follow source_test_contracts. A prohibition test attempts the specified "
            "excluded action in a simulated authorized fixture, then compares captured "
            "before/after state to show that it did not occur. Cover every prohibited "
            "action. Test permitted access succeeding separately from access denial."
        )
    context = {
        "assigned_section": name,
        "evidence": [item.model_dump() for item in selected],
        "existing_requirements": [
            {key: row[key] for key in ("id", "statement", "evidence_ids")} for row in prior
        ],
        "_inference_limits": {"num_ctx": 4096, "num_predict": 2600},
        "retry_from_source": True,
    }
    if contracts:
        context["source_test_contracts"] = contracts
    try:
        result, provenance = provider.generate(system, context, schema, cancel, deadline, validate)
    except GenerationError as error:
        if not str(error).startswith("section_validation_failed:") or not error.rejected_candidate:
            raise
        frozen = schema.model_validate(error.rejected_candidate)
        original_errors = set(validate(frozen))
        supported = (
            "unrequested_product_logging",
            "unconfirmed_production_log_witness",
            "unsupported_response_time_commitment",
            "unconfirmed_product_message_contract",
            "unsupported_quantitative_commitment",
            "unsupported_numeric_specificity",
            "unconfirmed_automatic_response",
            "permitted_",
            "positive_permission_",
            "prohibited_",
            "automatic_prohibition_",
            f"missing_{name}_behavior_",
            "project_request_recast_as_runtime_behavior",
            "missing_normative_behavior",
        )
        if any(not any(code in issue for code in supported) for issue in original_errors):
            raise
        content = compose(frozen)
        patches = {}
        patch_fields = {}
        capture_only = set()
        additions = {}
        required_actions = {}
        locations = {}
        group_repairs = {}
        frozen_rows = frozen.model_dump()
        for eid in frozen_rows:
            row_ids = {row["id"] for row in content["requirements"] if eid in row["evidence_ids"]}
            gaps = sorted(
                issue for issue in original_errors
                if issue.startswith(f"{eid}:missing_{name}_behavior_")
                or any(
                    issue in {
                        f"{rid}:project_request_recast_as_runtime_behavior",
                        f"{rid}:missing_normative_behavior",
                    }
                    for rid in row_ids
                )
            )
            if gaps:
                key = f"{eid}_source"
                group_repairs[key] = eid
                patches[key] = {
                    "task": "repair_source_group",
                    "source": source_quotes[eid],
                    "missing_source_behaviors": gaps,
                    "rejected_group": frozen_rows[eid],
                    "instruction": "Return statement, tests and unresolved_decisions for "
                    "this source ONLY. Cover its exact actors, actions and objects. Other "
                    "source groups are frozen and cannot supply this group's obligations.",
                }
        empty_analysis = analysis.model_copy(update={"assessments": []})
        for row in content["requirements"]:
            eid = row["evidence_ids"][0]
            if eid in group_repairs.values():
                continue
            for index, criterion in enumerate(row["acceptance_criteria"]):
                isolated = {
                    **content,
                    "requirements": [{**row, "acceptance_criteria": [criterion]}],
                }
                issues = (
                    set(
                        validate_section(
                            name, isolated, evidence, empty_analysis, sources, predecessors
                        )
                    )
                    & original_errors
                )
                if issues:
                    key = f"{eid}_test_{index + 1}"
                    locations[key] = (eid, index)
                    fields = {"then", "observable_evidence"}
                    if all("unconfirmed_production_log_witness" in issue for issue in issues):
                        fields = {"observable_evidence"}
                    if any("unconfirmed_production_log_witness" in issue for issue in issues):
                        capture_only.add(key)
                    fields.update(
                        field
                        for field in ("given", "when")
                        if unsupported_quantities(criterion[field], evidence)
                    )
                    patch_fields[key] = fields
                    patches[key] = {
                        "statement": row["statement"],
                        "source": source_quotes[eid],
                        "frozen_test_fields": {
                            field: text for field, text in criterion.items() if field not in fields
                        },
                        "outcome_focus": criterion["when"],
                        "validation_feedback": sorted(issues),
                        "confirmed_source_quantities": re.findall(
                            r"\b\d+(?:\.\d+)?\s+(?:milliseconds?|seconds?|minutes?|hours?|days?|"
                            r"weeks?|months?|years?|devices?|users?|sessions?)\b",
                            source_quotes[eid],
                            re.I,
                        ),
                    }
        for eid, row in frozen.model_dump().items():
            if eid in group_repairs.values():
                continue
            gaps = [
                issue
                for issue in original_errors
                if issue.startswith(eid + ":")
                and any(
                    code in issue
                    for code in (
                        "permitted_",
                        "positive_permission_",
                        "prohibited_",
                        "automatic_prohibition_",
                    )
                )
            ]
            for gap_index, gap in enumerate(sorted(gaps), 1):
                key = f"{eid}_gap_{gap_index}"
                additions[key] = eid
                action = permission_gap_action(source_quotes[eid], gap.split(":", 1)[1])
                if action:
                    required_actions[key] = action
                patches[key] = {
                    "task": "author_one_missing_source_test",
                    "source": source_quotes[eid],
                    "missing_outcome": gap,
                    "required_action": action,
                    "instruction": "Write one test that initiates the required_action and "
                    "observes its successful result. Other existing actions are already covered.",
                    "actor_role_terms": permission_test_contract(source_quotes[eid]).get(
                        "actor_role_terms", []
                    ),
                    "prohibition_contract": prohibition_test_contract(source_quotes[eid]),
                    "existing_test_actions": [test["when"] for test in row["tests"]],
                }
        if not patches:
            raise
        source_group_schema = create_model(
            "SourceGroupRepair",
            __base__=SourceRequirementDraft,
            statement=(str, Field(
                min_length=20, pattern=r"^The system shall .+$",
                description="Begin with 'The system shall ' and state the source product's "
                "behavior. Preserve its actors and objects. Do not copy the project request "
                "verb Design/Build/Develop/Create or say the system designs itself.",
            )),
        )
        patch_schema = create_model(
            "SourceTestPatches",
            __base__=StrictModel,
            **{
                key: (
                    create_model(
                        f"TestPatch{index}",
                        __base__=StrictModel,
                        **{
                            field: (
                                Literal[REPAIR_CAPTURE_OPTIONS]
                                if field == "observable_evidence" and key in capture_only
                                else str,
                                Field(
                                    min_length=12,
                                    max_length=200,
                                    description=(
                                        "External test capture of the action's observed response "
                                        "or state. Do not promise product logs or narrate logging."
                                        if field == "observable_evidence"
                                        else "Only the observable result of the frozen WHEN; "
                                        "do not repeat the entire source or add a time promise."
                                        if field == "then"
                                        else "Source-backed test fixture or action."
                                    ),
                                ),
                            )
                            for field in ("given", "when", "then", "observable_evidence")
                            if field in fields
                        },
                    ),
                    ...,
                )
                for index, (key, fields) in enumerate(patch_fields.items())
            },
            **{key: (CompactCriterion, ...) for key in additions},
            **{key: (source_group_schema, ...) for key in group_repairs},
        )

        def merge(candidate: StrictModel) -> StrictModel:
            """Replace only rejected model-authored tests, retaining all valid siblings."""
            revised = frozen.model_dump()
            for key, criterion in candidate.model_dump().items():
                if key in group_repairs:
                    revised[group_repairs[key]] = criterion
                    continue
                if key in additions:
                    revised[additions[key]]["tests"].append(criterion)
                    continue
                eid, index = locations[key]
                revised[eid]["tests"][index].update(criterion)
            return schema.model_validate(revised)

        patched, repair = provider.generate(
            prompts.COMMON + "\nFor repair_source_group, return the requested source's "
            "statement, tests and unresolved_decisions. Its statement must cover that "
            "source's complete actor/action/object wording, not a neighboring E-ID. "
            "A project request to design a system is not a runtime design feature: "
            "Begin the repaired statement with 'The system shall ' and state what the "
            "requested system provides or does. Never return a raw 'Design a ...' request. "
            "Author tests only for actions in that exact source, with no extra logs, "
            "response times, thresholds or UI promises. Other groups stay frozen. "
            "For other tasks author ONLY the requested rejected test fields. Preserve "
            "the test focus and frozen fields. Derive results solely from original source. "
            "Write one short clause per field. Do not list all controls from the source. "
            "Use outcome_focus as the specific test target, not the whole requirement. "
            "For example, WHEN an administrator revokes a permission -> THEN the requested "
            "permission is revoked; evidence is 'Test capture of permission state'. "
            "WHEN an administrator reviews sessions -> THEN active sessions are returned; "
            "evidence is 'Test capture of session response'. An alert result is 'The "
            "administrator receives the alert'; evidence is 'Test capture of alert receipt'. "
            "Do not copy these examples to unrelated tests. No real-time/immediate claims "
            "unless stated in the source. Do not describe the capture as logged or recorded. "
            "For author_one_missing_source_test, return ONE GWT object for the "
            "required_action only. WHEN initiates that action and THEN observes its "
            "successful result. Do not repeat existing tests. "
            "GIVEN describes baseline fixture state. WHEN initiates the specific action. "
            "Unknown thresholds stay named configurable parameters; never invent values. "
            "Preserve EVERY confirmed_source_quantity exactly. Quantity diagnostics refer "
            "only to additional unsupported fixture values, not quantities in the source. "
            "Do not add minimum, maximum, at-least or exactly qualifiers to a bare duration. "
            "Do not explain corrections; author the concise test field itself. "
            "A detection source requires an observed detection result; never terminate "
            "sessions, block accounts or add a response absent from that source. "
            "Use positive outcome text and a test-instrumented response/state capture. "
            "No extra product logging, UI message guarantees or unstated response times. "
            "A rejected production-log witness must select one of the schema's external "
            "test-capture labels. These label test instrumentation, never product logging. "
            "Records explicitly named in the source may be inspected as stated. "
            "Use a short witness like 'Test capture of resulting state', not a narrative. "
            "Example only: WHEN a session exceeds its configured threshold -> THEN "
            "'Excessive session duration is detected'. "
            "Return exactly the keyed outcome objects, with short direct clauses.",
            {
                "tests_to_repair": patches,
                "required_test_actions": required_actions,
                "retry_from_source": True,
                "validation_feedback": sorted(
                    issue
                    for issue in original_errors
                    if "unsupported_quantitative_commitment" not in issue
                ),
                "_continue_model": error.rejected_model,
                "_inference_limits": {
                    "num_ctx": 4096, "num_predict": 2000 if group_repairs else 1200
                },
            },
            patch_schema,
            cancel,
            deadline,
            lambda candidate: validate(merge(candidate)),
        )
        result = merge(patched)
        provenance = {
            **repair,
            "attempts": error.attempts + repair["attempts"],
            "base_repair_used": repair["model"] != provider.model_name,
            "repaired_test_keys": sorted(patches),
            "repaired_source_ids": sorted(group_repairs.values()),
        }
    return compose(result), {
        **provenance,
        "compact_requirements_version": COMPACT_REQUIREMENTS_VERSION,
    }

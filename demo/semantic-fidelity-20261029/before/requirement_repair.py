"""Bounded model-authored completion of omitted source obligations and permission tests."""

from __future__ import annotations

import re
from collections.abc import Callable
from copy import deepcopy
from threading import Event

from . import prompts
from .acceptance_grounding import preserve_nonexclusive_tests, preserve_source_denial
from .management_scope import management_statement
from .permission_verification import (
    permission_gap_action,
    permission_test_contract,
    permission_test_gaps,
)
from .prohibition_verification import (
    prohibited_action_gaps,
    prohibition_gap_action,
    prohibition_test_contract,
    verified_prohibition_criteria,
)
from .provider import GenerationError, LLMProvider
from .schemas import (
    REQUIREMENT_PREFIXES,
    AcceptanceTestRepair,
    Analysis,
    Evidence,
    ObservableEvidenceRepair,
    Requirement,
)
from .semantics import missing_source_actions, missing_source_quantities
from .source_completion import capacity_completion_statement
from .validation import requirements_from, validate_section

REQUIREMENT_REPAIR_VERSION = "field-local-repair-1.6"


def repair_source_capacity_criterion(
    provider: LLMProvider,
    original: dict,
    statement: str,
    evidence: list[Evidence],
    cancel: Event,
    deadline: float,
    validate_row: Callable[[Requirement], list[str]],
) -> tuple[dict, dict]:
    """Rebuild a recognized source capacity row while the model authors its observable test."""
    source = [item for item in evidence if item.id in original["evidence_ids"]]
    inventory = "planned inventory" in statement
    method = "inspection" if inventory else "test"
    fixed = deepcopy(original) | {
        "title": statement,
        "statement": statement,
        "rationale": "Source-stated constraint: " + " ".join(item.quote for item in source),
        "unresolved_decisions": [
            "Behavior beyond the source-stated "
            + ("planning population" if inventory else "simultaneous load")
            + " remains unconfirmed."
        ],
    }

    def validate(candidate: AcceptanceTestRepair) -> list[str]:
        errors = []
        if candidate.requirement_id != original["id"]:
            errors.append("capacity_repair_must_preserve_requirement_id")
        criterion = candidate.acceptance_criterion.model_dump()
        if criterion["method"] != method:
            errors.append("capacity_repair_must_preserve_source_test_method")
        prose = " ".join(criterion.values())
        number = re.search(r"\b[0-9]+\b", statement)[0]
        if not re.search(rf"\b{number}\b", prose):
            errors.append("capacity_test_must_exercise_stated_quantity")
        actions = criterion["when"] + " " + criterion["then"]
        if set(re.findall(r"\b[0-9]+\b", actions)) - {number}:
            errors.append("capacity_test_contains_other_row_quantity")
        if inventory and not re.search(
            r"\b(?:inspect|review|compare|examine)\b", criterion["when"], re.I
        ):
            errors.append("planning_inventory_requires_design_inspection")
        if inventory and re.search(
            r"\b(?:performance|degradation|service interruption|without failure)\b",
            criterion["then"],
            re.I,
        ):
            errors.append("planning_inventory_is_not_operational_performance")
        if re.match(
            r"(?:Capture|Export|Record)\s+E[-_ ]?[0-9_]+", criterion["observable_evidence"], re.I
        ):
            errors.append("capacity_witness_must_record_observed_result")
        if inventory and re.search(
            r"\b(?:registration|register new|create accounts?)\b", prose, re.I
        ):
            errors.append("planning_inventory_does_not_require_registration_workflow")
        if not inventory and (
            not re.search(rf"\b{number}\b", criterion["when"])
            or not re.search(
                r"\b(?:simultaneous|concurrent|in parallel)\b", criterion["when"], re.I
            )
        ):
            errors.append("capacity_test_must_initiate_stated_simultaneous_load")
        merged = Requirement.model_validate(fixed | {"acceptance_criteria": [criterion]})
        return errors + validate_row(merged)

    def generate_test():
        """Keep the full criterion call separate from a field-only witness correction."""
        return provider.generate(
            prompts.COMMON + "\nAuthor one observable acceptance criterion for the frozen "
            "source_capacity_statement. Return the AcceptanceTestRepair object only. The "
            "server preserves source metadata and statement. Do not draft another requirement. "
            "For a planned inventory, inspect that design/configuration accounts for that "
            "population; do not invent a registration workflow or a concurrent load. For a "
            "simultaneous execution load, initiate that exact number together in WHEN and "
            "observe their successful establishment in THEN. Do not test an extra request "
            "being denied, infer a maximum, promise response times or uninterrupted service. "
            "Use external test observations, not new product logs/messages. Keep the test "
            "limited to this row's source quantity rather than combining other source loads.",
            {
                "task": "one_source_capacity_acceptance_criterion",
                "target_requirement_id": original["id"],
                "source_capacity_statement": statement,
                "evidence": [item.model_dump() for item in source],
                "required_acceptance_method": method,
                "capacity_design_inspection": inventory,
                "retry_from_source": True,
            },
            AcceptanceTestRepair,
            cancel,
            deadline,
            validate,
        )

    try:
        result, provenance = generate_test()
    except GenerationError as error:
        if error.rejected_candidate is None or not error.rejected_model:
            raise
        result = AcceptanceTestRepair.model_validate(error.rejected_candidate)
        if set(validate(result)) != {"capacity_witness_must_record_observed_result"}:
            raise
        frozen = result.model_copy(deep=True)

        def merge_witness(candidate: ObservableEvidenceRepair) -> AcceptanceTestRepair:
            patched = frozen.model_copy(deep=True)
            patched.acceptance_criterion.observable_evidence = candidate.observable_evidence
            return patched

        replacement, provenance = provider.generate(
            prompts.COMMON + "\nAuthor ONLY observable_evidence for the frozen criterion. "
            "Name the inspected design/configuration artifact and its observed population, "
            "or the test capture showing the requested sessions established. Source E-IDs "
            "and copied stakeholder descriptions are not observations. Do not rewrite the "
            "criterion or add product logs, performance promises or measurements.",
            {
                "criterion_context": {
                    field: getattr(result.acceptance_criterion, field)
                    for field in ("given", "when", "then", "method")
                },
                "source_capacity_statement": statement,
                "retry_from_source": True,
            },
            ObservableEvidenceRepair,
            cancel,
            deadline,
            lambda candidate: validate(merge_witness(candidate)),
        )
        result = merge_witness(replacement)
        models = sorted({error.rejected_model, provenance["model"]})
        provenance = provenance | {
            "model": " + ".join(models),
            "output_models": models,
            "attempts": error.attempts + provenance["attempts"],
            "capacity_witness_field_repair": True,
        }
    return fixed | {"acceptance_criteria": [result.acceptance_criterion.model_dump()]}, provenance


def normative_header_issues(
    name: str,
    row: dict,
    evidence: list[Evidence],
    analysis: Analysis,
    sources: list,
    predecessors: dict,
) -> list[str]:
    """Diagnose invalid source scope without using criterion content or a rejected rationale."""
    diagnostic = deepcopy(row) | {
        "acceptance_criteria": [],
        "rationale": "The original source states this behavior; no added rationale is asserted.",
    }
    metadata_analysis = analysis.model_copy(
        update={
            "assessments": [
                item.model_copy(update={"sections": []}) for item in analysis.assessments
            ]
        }
    )
    prior = {
        section: content
        | {"requirements": [item for item in content["requirements"] if item["id"] != row["id"]]}
        if "requirements" in content
        else content
        for section, content in predecessors.items()
    }
    return validate_section(
        name, {"requirements": [diagnostic]}, evidence, metadata_analysis, sources, prior
    )


def repair_canonical_acceptance(
    provider: LLMProvider,
    name: str,
    content: dict,
    evidence: list[Evidence],
    analysis: Analysis,
    sources: list,
    predecessors: dict,
    cancel: Event,
    deadline: float,
) -> tuple[dict, set[str], int]:
    """Use the source-bound single-test path without rewriting canonical rows or valid tests."""
    fixed = deepcopy(content)
    prior = predecessors | {
        name: {
            "requirements": predecessors.get(name, {}).get("requirements", [])
            + fixed["requirements"]
        }
    }
    view = {
        "requirements": [],
        "related_acceptance_criteria": [
            {
                "requirement_id": row["id"],
                "evidence_ids": row["evidence_ids"],
                "sources": row["sources"],
                "acceptance_criteria": row["acceptance_criteria"],
            }
            for row in fixed["requirements"]
        ],
    }
    repaired, models, attempts = repair_linked_acceptance(
        provider, name, view, evidence, analysis, sources, prior, cancel, deadline
    )
    by_id = {
        item["requirement_id"]: item["acceptance_criteria"]
        for item in repaired["related_acceptance_criteria"]
    }
    for row in fixed["requirements"]:
        row["acceptance_criteria"] = by_id[row["id"]]
    return fixed, models, attempts


def repair_linked_acceptance(
    provider: LLMProvider,
    name: str,
    content: dict,
    evidence: list[Evidence],
    analysis: Analysis,
    sources: list,
    predecessors: dict,
    cancel: Event,
    deadline: float,
) -> tuple[dict, set[str], int]:
    """Replace only rejected linked criteria, retaining their target and valid siblings."""
    fixed = deepcopy(content)
    models: set[str] = set()
    attempts = 0
    canonical = {row["id"]: row for row in requirements_from(predecessors) + fixed["requirements"]}
    prior = predecessors | {
        name: {
            "requirements": predecessors.get(name, {}).get("requirements", [])
            + fixed["requirements"]
        }
    }
    relaxed = analysis.model_copy(update={"assessments": []})
    for linked in fixed.get("related_acceptance_criteria", []):
        row = canonical.get(linked["requirement_id"])
        if row is None:
            continue  # The final section gate reports the unknown reference.
        source_ids = linked["evidence_ids"] or row["evidence_ids"]
        bound_evidence = [item for item in evidence if item.id in source_ids]
        for index, criterion in enumerate(linked["acceptance_criteria"]):

            def validate_test(
                candidate: AcceptanceTestRepair,
                target_id=row["id"],
                target_evidence=bound_evidence,
                target_sources=linked["sources"],
                target_ids=source_ids,
            ) -> list[str]:
                """Validate the replacement independently of other rejected siblings."""
                if candidate.requirement_id != target_id:
                    return ["linked_test_repair_must_preserve_target"]
                isolated = {
                    "requirements": [],
                    "related_acceptance_criteria": [
                        {
                            "requirement_id": target_id,
                            "evidence_ids": target_ids,
                            "sources": target_sources,
                            "acceptance_criteria": [candidate.acceptance_criterion.model_dump()],
                        }
                    ],
                }
                return validate_section(name, isolated, target_evidence, relaxed, sources, prior)

            checked = AcceptanceTestRepair.model_validate(
                {"requirement_id": row["id"], "acceptance_criterion": criterion}
            )
            feedback = validate_test(checked)
            if not feedback:
                continue
            diagnostic = checked.model_copy(deep=True)
            diagnostic.acceptance_criterion.observable_evidence = (
                "Capture a test-instrumented response and resulting state."
            )
            if not validate_test(diagnostic):
                frozen_test = checked.model_dump()

                def merge_witness(candidate, frozen=frozen_test):
                    """Merge only the new witness into the unchanged authored test."""
                    return AcceptanceTestRepair.model_validate(
                        frozen
                        | {
                            "acceptance_criterion": frozen["acceptance_criterion"]
                            | {"observable_evidence": candidate.observable_evidence}
                        }
                    )

                replacement, provenance = provider.generate(
                    prompts.COMMON + "\nCorrect ONLY observable_evidence, the sole rejected "
                    "field. The server preserves GIVEN/WHEN/THEN and method. Name an "
                    "external test capture of the stated result/state; do not add an "
                    "uninterrupted-service, response-time, message or new product-log promise. "
                    "Return the witness-only JSON schema.",
                    {
                        "evidence": [item.model_dump() for item in bound_evidence],
                        "existing_requirements": [{"id": row["id"], "statement": row["statement"]}],
                        "criterion_context": {
                            key: criterion[key] for key in ("given", "when", "then", "method")
                        },
                        "rejected_witness": criterion["observable_evidence"],
                        "validation_feedback": feedback,
                    },
                    ObservableEvidenceRepair,
                    cancel,
                    deadline,
                    lambda candidate: validate_test(merge_witness(candidate)),
                )
                result = merge_witness(replacement)
            else:
                result, provenance = provider.generate(
                    prompts.COMMON + "\nRepair only the rejected linked acceptance criterion. "
                    "Keep its existing requirement ID. Use that requirement's supplied source; "
                    "do not borrow another passage. Describe the actual action and observable "
                    "result without new product logging, timing or implementation promises. "
                    "Use external test captures when production logging is not required. "
                    "For retention/deletion, start with an existing record with a known creation "
                    "time, advance a controlled test clock through the stated retention period, "
                    "and inspect actual stored records. Do not create a log after its own "
                    "creation date as an expiry trigger or invent a deletion-event log. "
                    "Remove unprovided time windows and datastore choices. Use the source "
                    "role, requested operation and externally observed result only. "
                    "Return one replacement criterion, not a section or requirement.",
                    {
                        "evidence": [item.model_dump() for item in bound_evidence],
                        "existing_requirements": [{"id": row["id"], "statement": row["statement"]}],
                        **(
                            {"rejected_criterion": criterion}
                            if not any(
                                "unconfirmed_permission_database" in error
                                or "unsupported_quantitative_commitment" in error
                                for error in feedback
                            )
                            else {}
                        ),
                        "validation_feedback": feedback,
                        "retry_from_source": True,
                    },
                    AcceptanceTestRepair,
                    cancel,
                    deadline,
                    validate_test,
                )
            linked["acceptance_criteria"][index] = result.acceptance_criterion.model_dump()
            models.update(provenance.get("output_models", [provenance["model"]]))
            attempts += provenance["attempts"]
    return fixed, models, attempts


def complete_source_gaps(
    provider: LLMProvider,
    name: str,
    content: dict,
    context: dict,
    evidence: list[Evidence],
    analysis: Analysis,
    sources: list,
    predecessors: dict,
    cancel: Event,
    deadline: float,
    *,
    repair_tests: bool = True,
) -> tuple[dict, set[str], int]:
    """Ask for only missing artifacts, retaining existing model-authored rows and tests."""
    fixed = deepcopy(content)
    models: set[str] = set()
    attempts = 0
    original = {item.id: item for item in evidence}
    source_ids = {
        item.evidence_id
        for item in analysis.assessments
        if name in item.sections and item.kind in {"requirement", "constraint", "exclusion"}
    }
    for eid in sorted(source_ids):
        rows = requirements_from(predecessors) + fixed["requirements"]
        linked = [row for row in rows if eid in row["evidence_ids"]]
        represented = " ".join(
            row["statement"] + " " + " ".join(ac["then"] for ac in row["acceptance_criteria"])
            for row in linked
        )
        missing = missing_source_actions(
            original[eid].quote, represented, include_capabilities=True
        )
        metrics = missing_source_quantities(original[eid].quote, represented)
        if missing or metrics:
            frozen_statement = (
                management_statement(original[eid].quote)
                if missing == {"management"} and not metrics
                else capacity_completion_statement(original[eid].quote, metrics)
                if not missing
                else None
            )
            prior = predecessors | {
                name: fixed
                | {
                    "requirements": predecessors.get(name, {}).get("requirements", [])
                    + fixed["requirements"]
                }
            }
            prefix = REQUIREMENT_PREFIXES[name]
            number = 1 + max(
                (
                    int(row["id"].split("-")[-1])
                    for row in rows
                    if row["id"].startswith(prefix + "-")
                ),
                default=0,
            )
            assigned_id = f"{prefix}-{number:03d}"

            def validate_requirement(
                candidate: Requirement,
                target_id=assigned_id,
                previous=prior,
                source_id=eid,
                target_statement=frozen_statement,
            ) -> list[str]:
                """Require the omitted source behavior without excusing unsupported additions."""
                row = candidate.model_dump() | {"id": target_id}
                row = preserve_nonexclusive_tests(row, evidence)
                repaired = Requirement.model_validate(row)
                candidate.acceptance_criteria = repaired.acceptance_criteria
                candidate.unresolved_decisions = repaired.unresolved_decisions
                issues = validate_section(
                    name, {"requirements": [row]}, evidence, analysis, sources, previous
                )
                if set(row["evidence_ids"]) != {source_id}:
                    issues.append("completion_must_use_only_target_source")
                if target_statement and row["statement"] != target_statement:
                    issues.append("completion_must_preserve_source_statement")
                return [issue for issue in issues if not is_boundary_test_issue(issue)]

            try:
                result, provenance = provider.generate(
                    prompts.COMMON + "\nDraft ONE additional canonical Requirement object for "
                    "the listed missing source action or metric. Set id to an empty string. "
                    "Do not output a section, array, another object or related-acceptance view. "
                    "Existing statements are an index, not source evidence. Other source "
                    "clauses are already covered; do not repeat them or borrow their behavior. "
                    "Keep the exact actor, target, mode, count and unit. A registered "
                    "population is not simultaneous activity; a bare load is not a maximum. "
                    "Use source_completion_statement exactly when supplied. Criteria must "
                    "exercise the source behavior with an action in WHEN and an observable "
                    "THEN. Use external test captures instead of new product logs, UI "
                    "messages or timing guarantees. Keep relevant unspecified decisions open. "
                    "Evidence IDs use only the target passage; sources stays empty. Use "
                    "existing IDs as dependencies only for a real necessary dependency.",
                    {
                        "assigned_section": name,
                        "task": "one_missing_source_requirement",
                        "evidence": [original[eid].model_dump()],
                        "existing_requirements": [
                            {"id": row["id"], "statement": row["statement"]} for row in rows
                        ],
                        "missing_source_actions": sorted(missing),
                        "missing_source_metrics": sorted(metrics),
                        "source_completion_statement": frozen_statement,
                        "scope_constraints": [
                            item.quote
                            for item in evidence
                            if item.quote in context.get("scope_constraints", [])
                            or any(
                                a.evidence_id == item.id and a.kind == "exclusion"
                                for a in analysis.assessments
                            )
                        ],
                        "unresolved_project_decisions": [
                            item.quote
                            for item in evidence
                            if any(
                                a.evidence_id == item.id and a.kind in {"uncertain", "conflict"}
                                for a in analysis.assessments
                            )
                            or re.search(
                                r"\b(?:undecided|unknown|unspecified|unconfirmed|"
                                r"not yet decided)\b",
                                item.quote,
                                re.I,
                            )
                        ],
                    },
                    Requirement,
                    cancel,
                    deadline,
                    validate_requirement,
                )
            except GenerationError as error:
                if not (
                    str(error).startswith("section_validation_failed:")
                    and error.rejected_candidate is not None
                    and error.rejected_model
                    and error.attempts > 0
                ):
                    raise
                rejected = Requirement.model_validate(error.rejected_candidate).model_dump() | {
                    "id": assigned_id
                }
                repaired, repair_models, repair_attempts = repair_canonical_acceptance(
                    provider,
                    name,
                    {"requirements": [rejected]},
                    evidence,
                    analysis,
                    sources,
                    prior,
                    cancel,
                    deadline,
                )
                result = Requirement.model_validate(repaired["requirements"][0])
                remaining = validate_requirement(result)
                if remaining:
                    raise GenerationError(
                        "source_completion_repair_failed:" + ";".join(remaining)
                    ) from error
                provenance = {
                    "model": error.rejected_model,
                    "output_models": sorted({error.rejected_model} | repair_models),
                    "attempts": error.attempts + repair_attempts,
                    "recovered_typed_completion": True,
                }
            fixed["requirements"].append(result.model_dump() | {"id": assigned_id})
            models.update(provenance.get("output_models", [provenance["model"]]))
            attempts += provenance["attempts"]

        if not repair_tests:
            continue
        # The finite initial gap list bounds supplementary test calls. Each call
        # must close its own gap; the final section validator checks the aggregate.
        linked = [row for row in fixed["requirements"] if eid in row["evidence_ids"]]
        inherited = [
            ac
            for row in requirements_from(predecessors)
            if eid in row["evidence_ids"]
            for ac in row["acceptance_criteria"]
        ]
        criteria = inherited + [ac for row in linked for ac in row["acceptance_criteria"]]

        def test_gaps(current: list[dict], source_id=eid) -> list[str]:
            """Keep permission and prohibited-state oracles separate from normative drafting."""
            return permission_test_gaps(
                original[source_id].quote, current
            ) + prohibited_action_gaps(original[source_id].quote, current)

        for gap in test_gaps(criteria):
            if gap not in test_gaps(criteria):
                continue

            def validate_test(
                candidate: AcceptanceTestRepair,
                required_gap=gap,
                target_rows=linked,
                prior_criteria=criteria,
                source_id=eid,
            ) -> list[str]:
                """Check source ownership and that the proposed test closes the specific gap."""
                if candidate.requirement_id not in {row["id"] for row in target_rows}:
                    return ["test_must_link_a_requirement_from_target_source"]
                candidate.acceptance_criterion = type(
                    candidate.acceptance_criterion
                ).model_validate(
                    preserve_source_denial(
                        original[source_id].quote,
                        candidate.acceptance_criterion.model_dump(),
                        candidate.requirement_id,
                    )
                )
                combined = prior_criteria + [candidate.acceptance_criterion.model_dump()]
                if required_gap in (
                    permission_test_gaps(original[source_id].quote, combined)
                    + prohibited_action_gaps(original[source_id].quote, combined)
                ):
                    return [
                        required_gap + ":explicit_action_and_observable_success_or_denial_needed"
                    ]
                row = deepcopy(
                    next(row for row in target_rows if row["id"] == candidate.requirement_id)
                )
                if required_gap.startswith("automatic_prohibition_"):
                    row["acceptance_criteria"] = verified_prohibition_criteria(
                        original[source_id].quote, row["acceptance_criteria"]
                    ) + [candidate.acceptance_criterion.model_dump()]
                else:
                    row["acceptance_criteria"].append(candidate.acceptance_criterion.model_dump())
                other = predecessors.get(name, {}).get("requirements", []) + [
                    item for item in fixed["requirements"] if item["id"] != row["id"]
                ]
                issues = validate_section(
                    name,
                    {"requirements": [row]},
                    evidence,
                    analysis,
                    sources,
                    predecessors | {name: {"requirements": other}},
                )
                return [issue for issue in issues if not is_boundary_test_issue(issue)]

            automatic = gap.startswith("automatic_prohibition_")
            target_action = prohibition_gap_action(original[eid].quote, gap)
            prohibited_contract = prohibition_test_contract(original[eid].quote, target_action)
            test_instruction = (
                prohibited_contract["instruction"]
                if automatic
                else permission_test_contract(original[eid].quote)["instruction"]
            )
            action_to_exercise = permission_gap_action(original[eid].quote, gap)
            if action_to_exercise:
                test_instruction += (
                    f" The missing source action is {action_to_exercise}. "
                    "Explicitly initiate that action in WHEN and observe its successful "
                    "result in THEN. Other tests are retained by the server; do not repeat them."
                )
            result, provenance = provider.generate(
                prompts.COMMON + "\nReturn ONE acceptance test for the specified gap, linked "
                "to the existing requirement it verifies. Given states the initial role/state; "
                "When performs the action; Then describes its visible result. Name a captured "
                "result/state as evidence. Use test-instrumented response/state captures; "
                "do not depend on production logs unless the source requires those events "
                "to be logged. Invent no product behavior or timing. " + test_instruction,
                {
                    "source": original[eid].quote,
                    "evidence": [original[eid].model_dump()],
                    "gap_to_close": gap,
                    "permission_boundary": permission_test_contract(original[eid].quote),
                    "prohibition_verification": prohibited_contract,
                    "existing_requirements": [
                        {"id": row["id"]}
                        if automatic
                        else {"id": row["id"], "statement": row["statement"]}
                        for row in linked
                    ],
                    "existing_tests": [],
                },
                AcceptanceTestRepair,
                cancel,
                deadline,
                validate_test,
            )
            criterion = result.acceptance_criterion.model_dump()
            target_row = next(row for row in linked if row["id"] == result.requirement_id)
            if gap.startswith("automatic_prohibition_"):
                target_row["acceptance_criteria"] = verified_prohibition_criteria(
                    original[eid].quote, target_row["acceptance_criteria"]
                ) + [criterion]
                criteria = inherited + [ac for row in linked for ac in row["acceptance_criteria"]]
            else:
                target_row["acceptance_criteria"].append(criterion)
                criteria.append(criterion)
            models.update(provenance.get("output_models", [provenance["model"]]))
            attempts += provenance["attempts"]
    return fixed, models, attempts


def is_boundary_test_issue(issue: str) -> bool:
    """Identify known test gaps that are completed before any section is published or reused."""
    return any(
        marker in issue
        for marker in (
            "permitted_",
            "positive_permission_test_missing",
            "prohibited_actor_action_denial_not_tested",
            "automatic_prohibition_",
        )
    )

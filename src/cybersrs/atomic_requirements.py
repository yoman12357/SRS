"""Model-authored tests for independently preserved, source-bound canonical obligations."""

from __future__ import annotations

import re
from threading import Event
from typing import Literal

from pydantic import Field, create_model
from pydantic.fields import FieldInfo

from . import prompts
from .acceptance_grounding import preserve_source_outcome
from .artifact_grounding import unsupported_delivery_guarantees
from .clarification_policy import deduplicate_decisions
from .provider import GenerationError, LLMProvider
from .schemas import Analysis, Evidence, SourceChunk, StrictModel
from .source_detail_policy import unsupported_source_details
from .source_obligations import (
    OBLIGATION_VERSION,
    criterion_target_issues,
    obligation_dimensions,
    observed_outcome_pattern,
    source_obligations,
)


def _repair_field(field: str, quote: str, action: str) -> FieldInfo:
    """Constrain corrective prose while retaining model authorship and complete validation."""
    if field not in {"given", "when", "then"}:
        return Field(description="Select the exact allowed inspection method or evidence label.")
    chars = r"[^0-9]*" if not re.search(r"\d", quote) else r"[\s\S]*"
    predicate = observed_outcome_pattern(action) if field == "then" else None
    pattern = f"^{chars}(?:{predicate}){chars}$" if predicate else f"^{chars}$"
    return Field(
        min_length=12 if field == "then" else 8,
        max_length=200 if field == "then" else 160,
        pattern=pattern,
        description=(
            f"Short source-specific observed state for the {action!r} operation. "
            "Use an outcome verb accepted by the action contract. No extra response codes, "
            "numbers, reaction mechanisms, logging or fields. Other accepted fields stay frozen."
        ),
    )


def correction_guidance(issues: list[str]) -> list[str]:
    """Translate private error codes into instructions without priming their rejected wording."""
    guidance = []
    for issue in issues:
        if any(word in issue for word in ("live_behavior", "numeric", "response_time")):
            message = (
                "Describe the resulting content or state; timing and quantities are undecided."
            )
        elif "storage_implementation" in issue:
            message = (
                "Observe the named operation's resulting state; storage mechanism is undecided."
            )
        elif "result_fields" in issue:
            message = "Observe the named operation's result; its output field set is undecided."
        elif "product_message_contract" in issue:
            message = "Observe the access decision; response-message wording is undecided."
        elif "logging" in issue or "log_witness" in issue:
            message = "Describe only the named operation's result; use external test capture."
        elif "protection_response" in issue:
            message = (
                "Observe protection against the source threats; its response method is undecided."
            )
        elif "alert_destination" in issue:
            message = "Observe that the requested alert exists; its destination is undecided."
        elif "detection_output" in issue:
            message = "Observe recognition of the stated condition; response actions are undecided."
        elif "unconfirmed_automatic_response" in issue:
            message = (
                "Report recognition of the named condition. Additional response mechanisms "
                "are undecided; this test does not select them."
            )
        elif "fixed_event_schema" in issue:
            message = (
                "Observe source-named information being received; representation is undecided."
            )
        elif any(
            word in issue
            for word in ("waiting_period", "session_timeout", "detection_window", "operating_hours")
        ):
            message = (
                "Observe the current state at the named action; timing conditions are undecided."
            )
        elif "identity_directory" in issue:
            message = (
                "Observe an exchange with the named identity system; its interface is undecided."
            )
        elif "session_persistence" in issue:
            message = "Observe the named service exchange; session lifetime and reuse remain TBD."
        elif "registry_implementation" in issue or "unbounded_metadata" in issue:
            message = "Observe the named definition or state; storage and field sets remain TBD."
        elif "not_template" in issue:
            message = "Name the exact source object, without alternative objects or template words."
        elif "display_initiation" in issue:
            message = "Observe the requested dashboard or content as displayed, shown or available."
        elif "protection_result" in issue:
            message = (
                "Observe protection against the named threat, "
                "not only starting or recording a test."
            )
        elif "repeats_initiation" in issue:
            message = "WHEN initiates the stated use; THEN observes its resulting state."
        elif "only_instrumentation" in issue:
            message = (
                "Observe the named items returned for examination; capture is external evidence."
            )
        elif "quality_target" in issue:
            message = "Inspect the acceptance plan and state that its measurable targets are TBD."
        else:
            message = "Report an observable result for the supplied actor, operation and target."
        if message not in guidance:
            guidance.append(message)
    return guidance


class AtomicCriterion(StrictModel):
    """A concise authored observation; no invented implementation choice is part of its fixture."""

    given: str = Field(
        min_length=8,
        max_length=160,
        description="Controlled source fixture, without new technologies or limits.",
    )
    when: str = Field(
        min_length=8,
        max_length=160,
        description="Initiate this source action; do not prescribe an implementation.",
    )
    then: str = Field(
        min_length=12,
        max_length=200,
        description="Observed state, not a SHALL statement. No logging beyond this operation, "
        "time promises, message fields or implementation. Quality metrics are TBD.",
    )
    method: Literal["test", "inspection", "analysis", "demonstration"]
    observable_evidence: Literal[
        "External test capture of the resulting response",
        "External test capture of the resulting state",
        "External test capture of the inspection record",
    ]


class QualityCriterion(AtomicCriterion):
    """Inspect a qualitative goal's unconfirmed acceptance plan, not a production benchmark."""

    given: str = Field(
        min_length=8, max_length=160, description="A draft acceptance plan for this quality goal."
    )
    when: str = Field(
        min_length=8,
        max_length=160,
        description="An analyst inspects or reviews that acceptance plan.",
    )
    then: str = Field(
        min_length=12,
        max_length=200,
        description="The plan's measurable targets remain TBD or unconfirmed.",
    )
    method: Literal["inspection", "analysis"]


def generate_atomic_requirements(
    provider: LLMProvider,
    name: str,
    evidence: list[Evidence],
    analysis: Analysis,
    sources: list[SourceChunk],
    predecessors: dict,
    cancel: Event,
    deadline: float,
    *,
    max_test_repairs: int = 1,
) -> tuple[dict, dict]:
    """Keep literal independent obligations; ask the local model for their observable tests."""
    # Import at the call boundary to keep validators independent of provider orchestration.
    from .category_metadata import empty_category_metadata
    from .validation import assign_ids, requirements_from, validate_section

    prior = requirements_from(predecessors)
    assigned = {
        item.evidence_id
        for item in analysis.assessments
        if name in item.sections and item.kind in {"requirement", "constraint"}
    }
    units = [
        unit
        for fact in evidence
        if fact.id in assigned
        for unit in source_obligations(fact)
        if unit.section == name
    ]
    units = [
        unit
        for unit in units
        if not any(
            re.sub(r"\W", "", row["statement"].casefold())
            == re.sub(r"\W", "", unit.statement.casefold())
            and unit.evidence_id in row["evidence_ids"]
            for row in prior
        )
    ]
    related = [row for row in prior if set(row["evidence_ids"]) & assigned]
    metadata = empty_category_metadata(name, related, prior)
    cells: dict[str, dict] = {}
    by_key = {unit.key: unit for unit in units}
    models, attempts, last_model = set(), 0, provider.model_name
    repaired_keys = []

    def focus(key: str) -> dict:
        """Give the author one operation rather than repeating the entire requirement paragraph."""
        body = by_key[key].statement.removeprefix("The system shall ").rstrip(".")
        actor = re.match(r"allow (.+?) to (.+)$", body)
        result = {
            "actor": actor[1] if actor else "system",
            "operation": actor[2] if actor else body,
            "kind": by_key[key].section,
        }
        if by_key[key].action == "support":
            scope = (
                "using controlled examples of each stated device type"
                if re.search(r"\bdevices?\b", by_key[key].statement, re.I)
                else "from each stated location"
                if re.search(r"\b(?:buildings?|locations?)\b", by_key[key].statement, re.I)
                else "within the stated support scope"
            )
            result["test_focus"] = (
                f"Initiate the source-supported use {scope}; observe that use succeeding. "
                + (
                    "Device approval criteria and implementation remain undecided."
                    if re.search(r"\bapproved\b.*\bdevices?\b", by_key[key].statement, re.I)
                    else "Implementation remains undecided."
                )
            )
        if by_key[key].action == "collect":
            result["test_focus"] = (
                "Submit the source-named input types; observe those inputs being received. "
                "Their representation and fields remain undecided."
            )
        if by_key[key].action == "register":
            result["test_focus"] = (
                "Register the source-named item as the stated actor; observe that item in its "
                "registered, stored or available state. Identifiers, metadata fields, storage "
                "technology and additional logging remain undecided."
            )
        if by_key[key].action == "enforce":
            result["test_focus"] = (
                "Use a controlled role or policy permission fixture. Observe the requested "
                "access allowed or denied according to that fixture. Response codes, message "
                "wording, token formats and persistence mechanisms remain undecided."
            )
        if by_key[key].action == "authenticate":
            result["test_focus"] = (
                "Submit the source-named principal for authentication using a controlled "
                "identity fixture. Observe authentication accepted or rejected. Protocols, "
                "token formats and message fields remain undecided."
            )
        if by_key[key].action == "provide" and re.search(r"\bdashboard\b", body, re.I):
            result["test_focus"] = (
                "Open the source-named dashboard as a controlled user; observe the dashboard "
                "displayed or available for use. Refresh speed and additional indicators "
                "remain undecided."
            )
        if by_key[key].action == "integrate":
            result["test_focus"] = (
                "Use a controlled exchange with the named external service and observe "
                "interoperation with that service. Authentication protocols, session lifetime, "
                "session reuse, storage paths and message fields remain undecided."
            )
        if by_key[key].action in {"record", "log"}:
            result["test_focus"] = (
                "Perform a controlled instance of the named event or session. Observe its "
                "requested record being available for inspection. This operation explicitly "
                "requests recording; do not substitute merely starting a recording test. "
                "The record's fields, storage technology and retention remain undecided."
            )
        if by_key[key].action in {"grant", "modify", "suspend", "revoke", "assign"}:
            result["test_focus"] = (
                "Initiate only this named permission operation as the stated actor; observe "
                "the corresponding permission or access state. Do not add other operations, "
                "extra event logging, deadlines or a response-message field set."
            )
        if by_key[key].action == "terminate":
            result["test_focus"] = (
                "The stated administrator requests termination of a controlled suspicious "
                "session; observe that session ended. Detection alone does not initiate "
                "this administrator operation. Timing and message fields are undecided."
            )
        if by_key[key].action == "approve":
            result["test_focus"] = (
                "The stated actor approves the source-named request. Observe that request's "
                "approved decision. Additional authorities, automatic issuance and response "
                "fields remain undecided."
            )
        if by_key[key].action == "reject":
            result["test_focus"] = (
                "The stated actor rejects the source-named request. Observe that request's "
                "rejected decision. Exercise rejection separately from approval."
            )
        if by_key[key].action == "set_expiration":
            result["test_focus"] = (
                "The stated actor sets the source-named expiration using a fixture date. "
                "Observe the expiration date set to that value. Leave the date itself unspecified."
            )
        if by_key[key].action == "renew":
            result["test_focus"] = (
                "The stated actor renews the source-named certificate. Observe its renewed "
                "state. Do not select a validity duration, algorithm, protocol or issuer."
            )
        if by_key[key].action in {"define", "initiate", "submit", "track", "restore"}:
            observation = {
                "define": "Observe the named policy definition available for examination.",
                "initiate": "Observe the named job having started or entered its job state.",
                "submit": "Observe the named submitted change received for processing.",
                "track": "Observe the named history available for examination.",
                "restore": "Observe the named data or configuration in its restored state.",
            }[by_key[key].action]
            result["test_focus"] = (
                observation + " Name only the object supplied in operation, not a generic "
                "template placeholder. Do not introduce an approval workflow, "
                "storage technology, schedule, duration or additional logging."
            )
        if by_key[key].action == "require" and re.search(r"\bauthenticat\w*\b", body, re.I):
            result["test_focus"] = (
                "Observe the source-required authentication boundary before protected access; "
                "the authentication technology and response message remain undecided."
            )
        if by_key[key].action in {"review", "inspect"} and actor:
            result["test_focus"] = (
                "Request the named items as the stated actor; observe those items returned "
                "for examination. External capture records that observed response."
            )
        if by_key[key].action == "quarantine":
            result["test_focus"] = (
                "Observe the source-named potentially harmful email itself held in quarantine. "
                "Its storage mechanism and release criteria remain undecided."
            )
        if by_key[key].action == "generate" and re.search(r"\balerts?\b", body, re.I):
            result["test_focus"] = (
                "Initiate the source alert condition; observe the requested alert existing. "
                "Its destination and field set remain undecided."
            )
        if by_key[key].action in {"detect", "identify"}:
            result["test_focus"] = (
                "Submit a controlled example of the stated condition; observe that condition "
                "being identified. Response actions remain undecided."
            )
        return result

    def compose(current: dict[str, dict]) -> dict:
        """Assign public IDs after the source slots and all model-authored tests are assembled."""
        rows = []
        for key, criterion in current.items():
            unit = by_key[key]
            decisions = []
            if unit.section == "nonfunctional":
                for word, question in {
                    "secure": "Which security acceptance outcomes must be demonstrated?",
                    "scalable": "What measurable scalability targets must the system meet?",
                    "reliable": "What measurable reliability and recovery targets "
                    "must the system meet?",
                    "manageable": "What criteria define acceptable manageability?",
                }.items():
                    if re.search(rf"\b{word}\b", unit.statement, re.I):
                        decisions.append(question)
            if unit.action == "maintain" and "logs" in unit.statement:
                decisions.extend(
                    [
                        "Which fields must the audit logs contain?",
                        "What retention period is required for the audit logs?",
                    ]
                )
            if unit.action == "detect":
                decisions.append("What conditions define " + unit.statement.split("detect ", 1)[1])
            if unit.action == "support" and "approved" in unit.statement:
                decisions.append("What criteria determine whether a device is approved?")
            if unit.action == "isolate" and "when necessary" in unit.statement:
                decisions.append("What conditions authorize endpoint isolation?")
            rows.append(
                {
                    "id": "",
                    "title": unit.statement.removeprefix("The system shall ").rstrip("."),
                    "statement": unit.statement,
                    "rationale": f"Source obligation {unit.key}.",
                    "priority": "should" if re.search(r"\bshould\b", unit.quote, re.I) else "must",
                    "dimensions": obligation_dimensions(unit),
                    "basis": "explicit",
                    "evidence_ids": [unit.evidence_id],
                    "sources": [],
                    "dependencies": [],
                    "acceptance_criteria": [preserve_source_outcome(unit.quote, criterion)],
                    "unresolved_decisions": deduplicate_decisions(decisions, evidence),
                }
            )
        return assign_ids(
            name,
            {
                "applicability_reason": (
                    "Independent source obligations; unspecified choices remain TBD."
                ),
                "requirements": rows,
                "related_requirement_ids": metadata["required_requirement_ids"],
                "related_acceptance_criteria": [],
            },
        )

    for eid in dict.fromkeys(unit.evidence_id for unit in units):
        batch = [unit for unit in units if unit.evidence_id == eid]
        schema = create_model(
            "SourceObligationTests",
            __base__=StrictModel,
            **{
                unit.key: (QualityCriterion if name == "nonfunctional" else AtomicCriterion, ...)
                for unit in batch
            },
        )
        covered_ids = {by_key[key].evidence_id for key in cells} | {eid}
        target_analysis = analysis.model_copy(
            update={
                "assessments": [
                    item for item in analysis.assessments if item.evidence_id in covered_ids
                ]
            }
        )

        def validate(candidate: StrictModel, selected_analysis=target_analysis) -> list[str]:
            """Check each original source and then run the full public section validator."""
            current = cells | candidate.model_dump()
            errors = []
            for key, criterion in candidate.model_dump().items():
                unit = by_key[key]
                criterion = preserve_source_outcome(unit.quote, criterion)
                support = [Evidence(id=unit.evidence_id, source="description", quote=unit.quote)]
                prose = " ".join(criterion.values())
                errors.extend(
                    f"{key}:unsupported_{issue}"
                    for issue in unsupported_source_details(prose, support)
                )
                errors.extend(
                    f"{key}:{issue}" for issue in unsupported_delivery_guarantees(prose, support)
                )
                errors.extend(
                    f"{key}:{issue}" for issue in criterion_target_issues(unit, criterion)
                )
                if unit.section == "nonfunctional" and criterion["method"] not in {
                    "inspection",
                    "analysis",
                }:
                    errors.append(f"{key}:quality_target_is_TBD_use_plan_inspection")
                if unit.section == "nonfunctional" and not re.search(
                    r"\b(?:TBD|pending|unconfirmed|unspecified|unverified)\b",
                    criterion["then"],
                    re.I,
                ):
                    errors.append(f"{key}:quality_target_is_TBD_not_a_passed_benchmark")
                if unit.section == "nonfunctional" and not re.search(
                    r"\b(?:inspect\w*|review\w*|examin\w*|evaluat\w*|compar\w*)\b",
                    criterion["when"],
                    re.I,
                ):
                    errors.append(f"{key}:quality_target_requires_plan_inspection")
            return errors + validate_section(
                name, compose(current), evidence, selected_analysis, sources, predecessors
            )

        system = (
            prompts.COMMON + "\nWrite ONE short black-box acceptance test per operation. "
            "GIVEN names the supplied actor and a controlled fixture. WHEN that actor "
            "initiates that operation. THEN states the observed result for that operation "
            "alone, in one short clause. Example style: actor reviews an item -> the "
            "requested item is returned. Use the operation's actual objects and role. "
            "Describe observed state, not a SHALL requirement or implementation. "
            "Select the external evidence label from the schema. For qualitative attributes, "
            "inspect the acceptance plan: its measurable targets are TBD until stakeholders "
            "confirm them. Leave implementation and unstated metrics undecided. "
            "Return the exact keyed JSON schema."
        )
        if name == "nonfunctional":
            system = (
                prompts.COMMON + "\nThese source attributes are qualitative goals with no "
                "agreed measurable targets. Write one acceptance-PLAN INSPECTION per goal. "
                "GIVEN a draft acceptance plan for the goal; WHEN an analyst reviews that "
                "plan; THEN report its measurable target definition as TBD or unconfirmed. "
                "This is an inspection of a plan, not execution of a product scenario. "
                "Use the supplied goal's actual name. Return the exact keyed JSON schema."
            )
        context = {
            "assigned_section": name,
            "project_title": analysis.title,
            "source_obligations": [
                {
                    "key": unit.key,
                    "evidence_id": unit.evidence_id,
                    **focus(unit.key),
                }
                for unit in batch
            ],
            "source_evidence": [],
            "retry_from_source": True,
            "_inference_limits": {"num_ctx": 8192, "num_predict": 2600},
        }
        try:
            result, provenance = provider.generate(
                system, context, schema, cancel, deadline, validate
            )
        except GenerationError as error:
            if not error.rejected_candidate or not str(error).startswith(
                "section_validation_failed:"
            ):
                raise
            if max_test_repairs == 0:
                raise
            frozen = schema.model_validate(error.rejected_candidate)
            failed_attempts = error.attempts
            continuation_model = error.rejected_model
            for repair_index in range(max_test_repairs):
                problems = validate(frozen)
                ordered_keys = list(cells | frozen.model_dump())
                public_ids = {
                    row["id"]: key
                    for row, key in zip(
                        compose(cells | frozen.model_dump())["requirements"],
                        ordered_keys,
                        strict=True,
                    )
                }
                by_test: dict[str, list[str]] = {}
                for problem in problems:
                    prefix = problem.split(":", 1)[0]
                    key = prefix if prefix in by_key else public_ids.get(prefix)
                    if key in frozen.model_dump():
                        by_test.setdefault(key, []).append(problem)
                if not by_test:
                    raise
                fields = {}
                tasks = {}
                for key, issues in by_test.items():
                    criterion = frozen.model_dump()[key]
                    support = [
                        Evidence(
                            id=by_key[key].evidence_id,
                            source="description",
                            quote=by_key[key].quote,
                        )
                    ]
                    wanted = set()
                    for issue in issues:
                        if "production_log_witness" in issue:
                            wanted.add("observable_evidence")
                        elif "quality_target" in issue:
                            wanted.update({"when", "then", "method"})
                        elif "criterion_result_repeats_initiation" in issue:
                            wanted.update({"when", "then"})
                        else:
                            wanted.add("then")
                    wanted.update(
                        field
                        for field in ("given", "when", "then", "observable_evidence")
                        if unsupported_source_details(criterion[field], support)
                        or unsupported_delivery_guarantees(criterion[field], support)
                    )
                    fields[key] = wanted
                    tasks[key] = {
                        **focus(key),
                        "feedback": correction_guidance(issues),
                        "frozen_fields": {
                            field: value
                            for field, value in criterion.items()
                            if field not in wanted
                        },
                    }
                patch_schema = create_model(
                    "AtomicCriterionPatches",
                    __base__=StrictModel,
                    **{
                        key: (
                            create_model(
                                f"CriterionPatch{index}",
                                __base__=StrictModel,
                                **{
                                    field: (
                                        Literal[
                                            "External test capture of the resulting response",
                                            "External test capture of the resulting state",
                                            "External test capture of the inspection record",
                                        ]
                                        if field == "observable_evidence"
                                        else Literal["inspection", "analysis"]
                                        if field == "method"
                                        else str,
                                        _repair_field(field, by_key[key].quote, by_key[key].action),
                                    )
                                    for field in (
                                        "given",
                                        "when",
                                        "then",
                                        "method",
                                        "observable_evidence",
                                    )
                                    if field in wanted
                                },
                            ),
                            ...,
                        )
                        for index, (key, wanted) in enumerate(fields.items())
                    },
                )

                def merge(
                    patch: StrictModel, frozen_batch=frozen, active_schema=schema
                ) -> StrictModel:
                    """Replace rejected fields, keeping valid criteria and sibling slots frozen."""
                    data = frozen_batch.model_dump()
                    for key, changes in patch.model_dump().items():
                        data[key].update(changes)
                    return active_schema.model_validate(data)

                try:
                    patched, repair = provider.generate(
                        prompts.COMMON
                        + "\nReturn ONLY the requested fields. Other fields and tests "
                        "are frozen. Write one short observed result of the named operation. "
                        "For example: reviewing an item -> the requested item is returned; "
                        "quarantining an email -> the email is held in quarantine. Use the actual "
                        "objects and role from operation, rather than copying these examples. "
                        "Keep the observation separate from instrumentation. For a quality "
                        "attribute, inspect its plan and mark unconfirmed metrics TBD. "
                        "Return only the keyed field values, with no explanatory prose.",
                        {
                            "tests_to_repair": tasks,
                            "retry_from_source": True,
                            "_continue_model": continuation_model,
                            "_inference_limits": {"num_ctx": 4096, "num_predict": 1200},
                        },
                        patch_schema,
                        cancel,
                        deadline,
                        lambda patch: validate(merge(patch)),
                    )
                except GenerationError as retry_error:
                    if (
                        repair_index + 1 >= max_test_repairs
                        or not retry_error.rejected_candidate
                        or not str(retry_error).startswith("section_validation_failed:")
                    ):
                        raise
                    frozen = merge(patch_schema.model_validate(retry_error.rejected_candidate))
                    failed_attempts += retry_error.attempts
                    continuation_model = retry_error.rejected_model or continuation_model
                    if continuation_model:
                        models.add(continuation_model)
                    repaired_keys.extend(fields)
                    continue
                result = merge(patched)
                provenance = repair | {"attempts": failed_attempts + repair["attempts"]}
                if error.rejected_model:
                    models.add(error.rejected_model)
                repaired_keys.extend(fields)
                break
        cells.update(result.model_dump())
        models.update(provenance.get("output_models", [provenance["model"]]))
        last_model = provenance["model"]
        attempts += provenance.get("attempts", 1)
    content = compose(cells)
    errors = validate_section(name, content, evidence, analysis, sources, predecessors)
    if errors:
        raise GenerationError("section_validation_failed:" + ";".join(errors))
    return content, {
        "model": last_model,
        "output_models": sorted(models),
        "attempts": attempts,
        "source_obligations_version": OBLIGATION_VERSION,
        "atomic_source_keys": [unit.key for unit in units],
        "compiled_canonical_index": not bool(units),
        "compiled_source_statements": True,
        "repaired_test_keys": repaired_keys,
    }

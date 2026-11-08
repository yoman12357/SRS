"""Lossless verification views of canonical model-authored acceptance criteria."""

import re
from copy import deepcopy

from .permission_verification import has_positive_test_outcome
from .prohibition_verification import automatic_change_is_prohibited
from .schemas import REQUIREMENT_PREFIXES, VerificationPlan, VerificationSection

VERIFICATION_PROJECTION_VERSION = "canonical-criteria-verification-1.1"
UNEXECUTED_LIMITATION = (
    "These verification plans have not been executed; their acceptance outcomes require testing."
)


def criterion_inventory(sections: dict) -> list[dict]:
    """Retain every canonical and linked criterion with a stable local selection key."""
    result = []
    known = {
        row["id"]: row
        for name in REQUIREMENT_PREFIXES
        for row in sections.get(name, {}).get("requirements", [])
    }
    for name in REQUIREMENT_PREFIXES:
        section = sections.get(name, {})
        for row in section.get("requirements", []):
            for index, criterion in enumerate(row["acceptance_criteria"], 1):
                result.append(
                    _inventory_item(
                        f"{row['id']}/canonical/{index}", row["id"], criterion, row["statement"]
                    )
                )
        for record_index, row in enumerate(section.get("related_acceptance_criteria", []), 1):
            rid = row["requirement_id"]
            if rid not in known:
                raise ValueError("unknown_canonical_criterion_target")
            for index, criterion in enumerate(row["acceptance_criteria"], 1):
                key = f"{rid}/{name}/linked-{record_index}/{index}"
                result.append(_inventory_item(key, rid, criterion, known[rid]["statement"]))
    if len({item["key"] for item in result}) != len(result):
        raise ValueError("duplicate_canonical_criterion_key")
    return result


def _inventory_item(key: str, rid: str, criterion: dict, statement: str) -> dict:
    """Keep inspection/analysis methods distinct from execution-test classifications."""
    method = criterion["method"]
    if method in {"inspection", "analysis"}:
        allowed = [method]
    else:
        outcome = criterion["then"]
        if automatic_change_is_prohibited(statement):
            allowed = ["negative"]
        elif has_positive_test_outcome(outcome):
            allowed = ["positive"]
        elif re.search(
            r"\b(?:den(?:y|ies|ied|ial)|reject\w*|forbidden|unchanged|unisolated|"
            r"not allowed|not permitted|not granted|no longer accessible)\b",
            outcome,
            re.I,
        ):
            allowed = ["negative"]
        else:
            allowed = ["positive", "negative"]
        condition = " ".join(criterion[field] for field in ("given", "when", "then"))
        if re.search(r"\b[0-9]+\b", condition) and re.search(
            r"\b(?:boundary|limits?|threshold\w*|maximum|minimum|at most|at least|expir\w*)\b",
            condition,
            re.I,
        ):
            allowed.append("boundary")
    return {
        "key": key,
        "requirement_id": rid,
        "criterion": deepcopy(criterion),
        "allowed_test_types": allowed,
    }


def validate_verification_choices(plan: VerificationPlan, inventory: list[dict]) -> list[str]:
    """Reject omissions, duplicates, unknown selections and changes to the authored method."""
    known = {item["key"]: item for item in inventory}
    selected = [item.criterion_key for item in plan.choices]
    errors = []
    if len(set(selected)) != len(selected):
        errors.append("verification:duplicate_criterion_selection")
    if set(selected) - set(known):
        errors.append("verification:unknown_criterion_selection")
    if set(known) - set(selected):
        errors.append("verification:missing_criterion_selection")
    if any(
        choice.criterion_key in known
        and choice.test_type not in known[choice.criterion_key]["allowed_test_types"]
        for choice in plan.choices
    ):
        errors.append("verification:criterion_method_changed")
    return errors


def _project_test(item: dict, test_type: str) -> dict:
    """Add presentation labels while retaining the authored test text verbatim."""
    criterion = item["criterion"]
    return {
        "requirement_ids": [item["requirement_id"]],
        "procedure": ["Given: " + criterion["given"], "When: " + criterion["when"]],
        "expected_result": "Expected: " + criterion["then"],
        "evidence_to_record": "Evidence: " + criterion["observable_evidence"],
        "test_type": test_type,
    }


def compose_verification(plan: VerificationPlan, inventory: list[dict]) -> dict:
    """Compose every criterion in canonical order; never invent supplementary product behavior."""
    errors = validate_verification_choices(plan, inventory)
    if errors:
        raise ValueError(";".join(errors))
    types = {choice.criterion_key: choice.test_type for choice in plan.choices}
    return VerificationSection(
        tests=[_project_test(item, types[item["key"]]) for item in inventory],
        limitations=[UNEXECUTED_LIMITATION],
    ).model_dump()


def verification_projection_issues(content: dict, sections: dict) -> list[str]:
    """Independently check claimed automatic projections against the current canonical content."""
    try:
        inventory = criterion_inventory(sections)
    except ValueError:
        return ["verification:invalid_projection_inventory"]
    tests = content["tests"]
    if len(tests) != len(inventory) or content["limitations"] != [UNEXECUTED_LIMITATION]:
        return ["verification:canonical_projection_mismatch"]
    for test, item in zip(tests, inventory, strict=True):
        if test["test_type"] not in item["allowed_test_types"]:
            return ["verification:criterion_method_changed"]
        expected = _project_test(item, test["test_type"])
        if any(test[key] != value for key, value in expected.items()):
            return ["verification:canonical_projection_mismatch"]
    return []

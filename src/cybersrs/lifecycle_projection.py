"""Source-linked proposed process plans with no invented product behavior."""

import re

from .schemas import Analysis, Evidence, LifecycleWorkPlan, SDLCSection
from .sdlc import rank_sdlc

LIFECYCLE_PROJECTION_VERSION = "source-linked-lifecycle-1.1"
TEST_PLAN = "Unit, integration, system and acceptance test plan"


def validate_work_groups(plan: LifecycleWorkPlan, requirements: list[dict]) -> list[str]:
    """Reject unknown, omitted or repeated work assignments."""
    known = {row["id"] for row in requirements}
    selected = [rid for group in plan.work_groups for rid in group.requirement_ids]
    errors = []
    if set(selected) != known:
        errors.append("sdlc:work_groups_must_cover_exact_canonical_ids")
    if len(selected) != len(set(selected)):
        errors.append("sdlc:work_groups_must_not_duplicate_requirements")
    return errors


def compose_lifecycle(
    plan: LifecycleWorkPlan,
    winner: str,
    requirements: list[dict],
    verification: dict,
    evidence: list[Evidence],
    analysis: Analysis,
) -> dict:
    """Compile the selected methodology from exact source work and unexecuted tests."""
    errors = validate_work_groups(plan, requirements)
    if errors:
        raise ValueError(";".join(errors))
    by_id = {row["id"]: row for row in requirements}
    ids = list(by_id)
    grouped = [
        "; ".join(rid + ": " + by_id[rid]["statement"] for rid in group.requirement_ids)
        for group in plan.work_groups
    ]
    security = [
        row
        for row in requirements
        if "security" in row["dimensions"] or row["id"].startswith("SEC-")
    ]
    checks = [
        "Review implementation and acceptance evidence against "
        + row["id"]
        + ": "
        + row["statement"]
        for row in security
    ]
    if not checks:
        checks = [
            (
                "Review design and test evidence for violations of source-defined "
                "permissions and exclusions."
            )
        ]
    unknown_ids = {
        item.evidence_id for item in analysis.assessments if item.kind in {"uncertain", "conflict"}
    }
    unknowns = [
        "Record unresolved source decision: " + item.quote
        for item in evidence
        if item.id in unknown_ids
    ]
    feedback = [
        item.quote
        for item in evidence
        if re.search(r"\bstakeholder feedback\b|\bproduct owner\b", item.quote, re.I)
    ]
    feedback_actions = [
        "Collect stakeholder feedback in accordance with the source: " + quote for quote in feedback
    ] or [
        (
            "Collect stakeholder feedback; agree its cadence with a human reviewer "
            "before scheduling cycles."
        )
    ]
    implementation = ["Implement the source-defined work group: " + group for group in grouped]
    tests = [
        "In an authorized isolated test environment, execute "
        + test["id"]
        + ": "
        + " ".join(test["procedure"])
        + " "
        + test["expected_result"]
        for test in verification.get("tests", [])
    ]
    if not tests:
        tests = [
            (
                "Plan and review tests against canonical acceptance criteria; execution"
                " evidence remains outstanding."
            )
        ]

    def phase(
        name: str,
        kind: str,
        activities: list[str],
        deliverables: list[str],
        entry: str,
        exit_condition: str,
    ) -> dict:
        """Keep process roles proposed and approval gates explicitly pending."""
        return {
            "name": name,
            "phase_type": kind,
            "activities": activities,
            "roles": [
                "Proposed project owner",
                "Proposed development lead",
                "Proposed verification reviewer",
            ],
            "deliverables": deliverables,
            "entry_criteria": [entry],
            "exit_criteria": [exit_condition],
            "security_checks": checks,
            "human_approval": (
                "Pending human decision by Proposed project owner on this phase's "
                "deliverables and unresolved decisions; no approval is recorded by "
                "generation."
            ),
            "requirement_ids": ids,
        }

    planning = phase(
        "Requirements and verification planning",
        "planning",
        ["Review and baseline the source-defined work group: " + group for group in grouped]
        + unknowns
        + [
            (
                "Create the unit, integration, system and acceptance test plan before "
                "implementation; retain each authored acceptance criterion."
            )
        ],
        ["Versioned requirements baseline", TEST_PLAN, "Unresolved-decision record"],
        "Authoritative inputs and canonical requirements are available for review.",
        "A human reviewer has recorded the baseline decision and disposition of unresolved scope.",
    )
    design = phase(
        "Design and test design",
        "design",
        [
            "Design the implementation for the source-defined work group: " + group
            for group in grouped
        ]
        + [
            (
                "Refine the early unit, integration, system and acceptance test plan "
                "without choosing unresolved product technologies."
            )
        ],
        ["Proposed design linked to canonical requirements", TEST_PLAN],
        "The requirements baseline and early test plan have been reviewed.",
        "A human reviewer has recorded the design decision and test-plan readiness.",
    )
    build = phase(
        "Implementation",
        "implementation",
        implementation,
        ["Implementation candidate linked to canonical requirement IDs"],
        (
            "The design and test plans are available and a human has confirmed "
            "test-environment authorization."
        ),
        (
            "The implementation candidate is ready for planned verification; no "
            "test result is assumed."
        ),
    )
    verify = phase(
        "Unit, integration, system and acceptance verification",
        "verification",
        [
            (
                "Execute the planned unit, integration, system and acceptance tests and"
                " record observed results."
            )
        ]
        + tests,
        [
            "Unit, integration, system and acceptance test evidence",
            "Defect and unresolved-decision record",
        ],
        "The candidate, reviewed test plans and authorized test environment are available.",
        (
            "A human reviewer has examined actual pass/fail evidence and recorded "
            "remaining defects or limitations."
        ),
    )
    release = phase(
        "Release and handoff",
        "release",
        [
            (
                "Review the exact requirements baseline, implementation links and "
                "verification evidence before a release decision."
            ),
            "Carry unresolved source decisions into handoff; generated text is not human approval.",
        ],
        [
            "Requirements and verification evidence package",
            "Pending human release decision",
            "Outstanding-decision record",
        ],
        "Verification evidence and unresolved decisions are available for human review.",
        "A human has recorded the release/handoff decision for the reviewed content.",
    )
    if winner in {"Agile", "Incremental", "Hybrid", "Spiral", "DevSecOps"}:
        cycle = [
            (
                "Review and prioritize the backlog for the next iteration without "
                "changing source-defined scope."
            )
        ]
        if winner in {"Spiral", "Hybrid"}:
            cycle += [
                (
                    "Review source-linked threats and risks before the next prototype or "
                    "increment; record uncertainty and human decisions."
                )
            ]
        cycle += (
            implementation
            + tests
            + feedback_actions
            + [
                (
                    "Return accepted stakeholder feedback and observed defects to the "
                    "backlog and plan the next iteration."
                )
            ]
        )
        if winner == "DevSecOps":
            cycle += [
                (
                    "Review security-check evidence for every delivery change and record a "
                    "human release decision; keep unresolved tooling and operational "
                    "choices open."
                )
            ]
        iteration = phase(
            winner + " delivery cycle",
            "iteration",
            cycle,
            [
                "Requirement-linked implementation increment",
                "Recorded test evidence",
                "Reviewed feedback and next-iteration backlog",
            ],
            (
                "Prior work, source scope and the reviewed test plan are available for "
                "iteration planning."
            ),
            (
                "A human reviewer has assessed the increment, test evidence and "
                "feedback; unresolved changes return to the next iteration."
            ),
        )
        phases = [planning, iteration, release]
        if winner in {"Hybrid", "Spiral", "DevSecOps"}:
            phases.insert(1, design)
    else:
        phases = [planning, design, build, verify, release]
    pairs = []
    if winner == "V-Model":
        pairs = [
            {
                "development_phase": planning["name"],
                "verification_phase": verify["name"],
                "test_plan_deliverable": TEST_PLAN,
                "test_scope": scope,
                "requirement_ids": ids,
            }
            for scope in ("unit", "integration", "system", "acceptance")
        ]
    decision = rank_sdlc(evidence)
    return SDLCSection(
        selected_model=winner,
        justification=plan.justification,
        tradeoffs=[
            (
                "Recurring delivery requires stakeholder review and backlog refinement; "
                "a cycle does not guarantee completeness or remove unresolved decisions."
            )
            if winner in {"Agile", "Incremental", "Hybrid", "Spiral", "DevSecOps"}
            else (
                "Early baselines and test plans support traceability; changed source "
                "requirements can require revisiting designs, plans and tests."
            )
        ] + [decision["decision_status"]],
        unknown_factors=decision["unknown_factors"],
        phases=phases,
        verification_pairs=pairs,
    ).model_dump()

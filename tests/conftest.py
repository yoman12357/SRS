"""Isolated synthetic fixtures; never write test approvals to real user storage."""

import copy
import time

import pytest

from cybersrs.config import Settings
from cybersrs.evidence import build_evidence
from cybersrs.provider import GenerationError, LLMProvider, check_cancel
from cybersrs.schemas import Analysis, Document
from cybersrs.sdlc import POLICY_VERSION, rank_sdlc

DESCRIPTION = "Security operators review alerts. Only administrators can manage accounts."


def requirement(statement, eid):
    """Build observable synthetic acceptance evidence for a defensive behavior."""
    action = {
        "given": "An authenticated user with a configured role is present",
        "when": "The user submits an action permitted to that role",
        "then": "The response displays the requested data only to the permitted role",
        "method": "test",
        "observable_evidence": "Capture response data and the resulting authorization decision",
    }
    if "manage accounts" in statement.casefold() or "account management" in statement.casefold():
        action = {
            "given": "An administrator test identity and an existing test account are present",
            "when": "The administrator submits an account-management action",
            "then": "The account-management response confirms that the permitted action succeeds",
            "method": "test",
            "observable_evidence": "Capture the account-management response and account state",
        }
    elif "isolate" in statement.casefold():
        action = {
            "given": "A network administrator test identity and connected test device are present",
            "when": "The administrator manually requests isolation of the test device",
            "then": "The device is isolated from network access",
            "method": "test",
            "observable_evidence": "Capture the device connectivity state before and after",
        }
    return {
        "id": "",
        "title": statement.split("shall ")[-1],
        "statement": statement,
        "rationale": "Implements the exact stakeholder-described role behavior.",
        "priority": "must",
        "dimensions": ["security"],
        "basis": "explicit",
        "evidence_ids": [eid],
        "sources": [],
        "dependencies": [],
        "acceptance_criteria": [action],
        "unresolved_decisions": [],
    }


@pytest.fixture
def settings(tmp_path):
    """Use temporary paths and loopback-only inert endpoint/model identifiers."""
    return Settings(
        _env_file=None,
        data_dir=tmp_path / "data",
        knowledge_dir=tmp_path / "knowledge",
        frontend_dir=tmp_path / "frontend",
        ollama_base_url="http://127.0.0.1:11434",
        model_name="test-qwen",
        base_model_name="test-base",
        embedding_model="test-embed",
        rag_enabled=False,
        ollama_stream=False,
        ollama_exclusive_main_model=False,
        generation_timeout_seconds=20,
    )


@pytest.fixture
def analysis():
    """Interpret both source sentences without losing either role constraint."""
    return Analysis(
        title="Local Security Operations",
        domain="Security monitoring",
        supported=True,
        summary="Operators inspect alerts and administrators manage accounts.",
        stakeholders=["Security operators", "Administrators"],
        assessments=[
            {
                "evidence_id": "E-001",
                "kind": "requirement",
                "sections": ["functional"],
                "explanation": "Operator-visible alert review",
            },
            {
                "evidence_id": "E-002",
                "kind": "requirement",
                "sections": ["security"],
                "explanation": "Account-management permission boundary",
            },
        ],
        questions=[],
        unresolved_decisions=[],
    )


@pytest.fixture
def sections():
    """Provide a linked complete synthetic report for structural regression tests."""
    narrative = {
        "summary": "Proposed local security operations components and explicit scope.",
        "items": [],
        "open_issues": [],
    }
    empty = {
        "applicability_reason": "No confirmed requirement in this category.",
        "requirements": [],
    }
    phase = {
        "name": "Review",
        "phase_type": "iteration",
        "activities": [
            "Review account permission behavior",
            "Implement the selected behavior and execute its tests within the iteration.",
            "Review stakeholder feedback and return changes to the backlog for the next iteration.",
        ],
        "roles": ["Proposed project owner"],
        "deliverables": ["Reviewed role policy"],
        "entry_criteria": ["Source requirements available"],
        "exit_criteria": ["User accepts behavior evidence"],
        "security_checks": ["Inspect unauthorized account access denial"],
        "human_approval": "Project owner approves the reviewed evidence",
        "requirement_ids": ["FR-001", "SEC-001"],
    }
    return {
        "introduction": copy.deepcopy(narrative),
        "functional": {
            "applicability_reason": "Operators review alerts.",
            "requirements": [
                requirement("The system shall allow security operators to review alerts.", "E-001")
            ],
        },
        "nonfunctional": copy.deepcopy(empty),
        "security": {
            "applicability_reason": "Only administrators manage accounts.",
            "requirements": [
                requirement(
                    "The system shall restrict account management to administrators.", "E-002"
                )
            ],
        },
        "data": copy.deepcopy(empty),
        "network": copy.deepcopy(empty),
        "compliance": {"mappings": [], "open_decisions": ["No mandatory framework confirmed"]},
        "architecture": {
            "summary": "A proposed role-scoped operations service separates clients "
            "from authorization.",
            "items": [
                {
                    "title": "Role-scoped operations service",
                    "component_name": "Operations service",
                    "responsibility": "Authorize role-scoped alert and account operations.",
                    "status": "proposed",
                    "detail": "Presents alerts to operators and account actions to administrators.",
                    "requirement_ids": ["FR-001", "SEC-001"],
                    "evidence_ids": ["E-001", "E-002"],
                    "sources": [],
                },
                {
                    "title": "Operator and administrator client",
                    "component_name": "Operations client",
                    "responsibility": "Present authorized alert review and account actions.",
                    "status": "proposed",
                    "detail": "Sends user requests and displays the service response.",
                    "requirement_ids": ["FR-001", "SEC-001"],
                    "evidence_ids": ["E-001", "E-002"],
                    "sources": [],
                },
            ],
            "data_flows": [
                {
                    "title": "Authorized action request",
                    "from_component": "Operations client",
                    "to_component": "Operations service",
                    "data_or_action": "Role-qualified alert or account action and response.",
                    "status": "proposed",
                    "detail": "The client submits a role-qualified request; the service "
                    "checks it and returns a response.",
                    "requirement_ids": ["FR-001", "SEC-001"],
                    "evidence_ids": ["E-001", "E-002"],
                    "sources": [],
                }
            ],
            "trust_boundaries": [
                {
                    "title": "Client-to-service authorization boundary",
                    "untrusted_component": "Operations client",
                    "trusted_component": "Operations service",
                    "enforcement": "Validate the role before permitting each requested action.",
                    "status": "proposed",
                    "detail": "The service validates roles independently of the client.",
                    "requirement_ids": ["SEC-001"],
                    "evidence_ids": ["E-002"],
                    "sources": [],
                }
            ],
            "open_issues": [],
        },
        "threats": {
            "threats": [
                {
                    "id": "",
                    "asset": "Accounts",
                    "actor": "Unauthorized user",
                    "scenario": "An unauthorized user attempts to modify account permissions.",
                    "impact": "Account privileges could be changed without authorization.",
                    "control_requirement_ids": ["SEC-001"],
                    "evidence_ids": ["E-002"],
                    "sources": [],
                    "residual_risk": "Compromised administrator accounts still require review.",
                }
            ],
            "assumptions": [],
        },
        "risks": {"risks": [], "open_issues": ["Delivery schedule remains unknown"]},
        "scenarios": {
            "scenarios": [
                {
                    "id": "",
                    "actor": "Administrator",
                    "goal": "Manage accounts",
                    "story": "As an administrator I want to manage accounts within my role.",
                    "preconditions": ["An administrator is authenticated"],
                    "steps": ["Submit an account-management action"],
                    "success_outcome": "The authorized account action is accepted",
                    "alternate_flows": ["The same action is denied to other roles"],
                    "requirement_ids": ["SEC-001"],
                    "evidence_ids": ["E-002"],
                    "unresolved_decisions": [],
                },
                {
                    "id": "",
                    "actor": "Security operator",
                    "goal": "Review alerts",
                    "story": "As a security operator I want to inspect alerts for incidents.",
                    "preconditions": ["An operator is authenticated"],
                    "steps": ["Open the alert view"],
                    "success_outcome": "The requested alerts appear for operator inspection",
                    "alternate_flows": ["Unauthorized account changes are denied"],
                    "requirement_ids": ["FR-001"],
                    "evidence_ids": ["E-001"],
                    "unresolved_decisions": [],
                },
            ],
            "open_issues": [],
        },
        "verification": {
            "tests": [
                {
                    "id": "",
                    "requirement_ids": ["FR-001", "SEC-001"],
                    "procedure": [
                        "Review alerts as an operator",
                        "Attempt account changes as an operator",
                    ],
                    "expected_result": "Alerts display and operator account changes are denied",
                    "evidence_to_record": "Role-tagged response payload and authorization event",
                    "test_type": "negative",
                }
            ],
            "limitations": ["Human evaluates domain completeness"],
        },
        "glossary": copy.deepcopy(narrative),
        "sdlc": {
            "selected_model": "Agile",
            "justification": "Provisional ranking has no differentiating delivery evidence; "
            "stakeholders must confirm suitability before adoption.",
            "tradeoffs": ["No confirmed release frequency or requirements stability"],
            "phases": [dict(phase, name=name) for name in ["Plan", "Iterate", "Review"]],
            "unknown_factors": ["stability", "delivery"],
        },
    }


def agile_lifecycle_fixture(content: dict) -> dict:
    """Author a synthetic cycle for typed-boundary tests, preserving supplied phase metadata."""
    preparation, iteration, release = copy.deepcopy(content["phases"][:3])
    iteration.pop("activities")
    iteration.pop("phase_type")
    iteration.update(
        planning_actions=["Plan the source-stated role behavior for this iteration."],
        implementation_actions=["Implement alert review and account-management permissions."],
        verification_actions=["Verify the source-stated role permissions with their tests."],
        feedback_actions=["Review stakeholder feedback on the demonstrated role behavior."],
        next_iteration_actions=["Update the backlog using feedback for the next iteration."],
    )
    preparation["phase_type"] = "planning"
    release["phase_type"] = "release"
    return {
        k: copy.deepcopy(content[k])
        for k in ("selected_model", "justification", "tradeoffs", "unknown_factors")
    } | {"preparation": preparation, "iteration": iteration, "release": release}


class FakeKnowledge:
    """Never use a real vector store or embedding service in isolated tests."""

    def retrieve(self, query, project_id=None, **kwargs):
        return []

    def counts(self):
        return {"global": 0, "private": 0}

    def delete_private(self, project_id, document_id=None):
        pass

    def ingest(self, *args):
        return 1


class FakeProvider(LLMProvider):
    """Scripted structured model boundary with real deterministic validation."""

    model_name = "test-qwen"

    def __init__(self, analysis, sections):
        self.analysis, self.sections = analysis, sections
        self.calls = []
        self.fail_section = None

    def generate(self, system, context, schema, cancel, deadline, validate=None):
        check_cancel(cancel, deadline)
        section = context.get("assigned_section", "analysis")
        self.calls.append(section)
        if section == self.fail_section:
            raise GenerationError("synthetic_model_failure")
        content = self.analysis.model_dump() if section == "analysis" else self.sections[section]
        if context.get("source_permission_statement") and "requirements" in content:
            content = copy.deepcopy(content)
            for row in content["requirements"]:
                row["statement"] = context["source_permission_statement"]
        if context.get("frozen_category_metadata") is not None:
            metadata = context["frozen_category_metadata"]
            content = copy.deepcopy(content) | {
                "applicability_reason": metadata["applicability_reason"],
                "related_requirement_ids": metadata["required_requirement_ids"],
            }
            content["requirements"] = []
            content["related_acceptance_criteria"] = []
        if schema.__name__ == "ArchitectureComponents":
            content = {key: content[key] for key in ("summary", "items", "open_issues")}
        elif schema.__name__ == "ArchitectureInteractions":
            content = {
                key: content[key] for key in ("data_flows", "trust_boundaries", "open_issues")
            }
        elif schema.__name__ == "ArchitectureLayoutComponents":
            content = {
                "components": [
                    {key: item[key] for key in ("component_name", "requirement_ids")}
                    for item in content["items"]
                ]
            }
        elif schema.__name__ == "ArchitectureOwnership":
            content = {
                "links": [
                    {
                        "requirement_id": row["id"],
                        "component_name": context["implementation_component_names"][0],
                    }
                    for row in context["existing_requirements"]
                ]
            }
        elif schema.__name__ == "ArchitectureOwnerAssignments":
            content = {
                row["id"]: [context["implementation_component_names"][0]]
                for row in context["existing_requirements"]
            }
        elif schema.__name__ == "ArchitectureRouteChoices":
            content = {rid: options[0] for rid, options in context["route_owner_choices"].items()}
        elif schema.__name__ == "ArchitectureInternalInteractions":
            content = {
                "data_flows": [
                    {
                        key: item[key]
                        for key in ("from_component", "to_component", "requirement_ids")
                    }
                    for item in content["data_flows"]
                ],
                "trust_boundaries": [
                    {
                        key: item[key]
                        for key in ("untrusted_component", "trusted_component", "requirement_ids")
                    }
                    for item in content["trust_boundaries"]
                ],
            }
        elif schema.__name__ == "SourceCandidatePlan":
            content = {"candidate_keys": [item["key"] for item in context["candidate_inventory"]]}
        elif schema.__name__ == "LifecycleWorkPlan":
            content = {
                "justification": content["justification"],
                "work_groups": [
                    {"requirement_ids": [row["id"] for row in context["existing_requirements"]]}
                ],
            }
        elif schema.__name__ == "AgileLifecycle":
            content = agile_lifecycle_fixture(content)
        elif schema.__name__ == "ScenarioProjectionPlan":
            content = {
                "actors": [
                    {"requirement_id": rid, "actor": options[0]}
                    for rid, options in context["actor_options"].items()
                ],
                "alternate_criterion_keys": [],
            }
        elif schema.__name__ == "VerificationPlan":
            content = {
                "choices": [
                    {"criterion_key": item["key"], "test_type": item["allowed_test_types"][0]}
                    for item in context["criterion_inventory"]
                ]
            }
        elif schema.__name__ == "CanonicalVerificationTypes":
            content = {
                item["key"]: item["allowed_test_types"][0]
                for item in context["criterion_inventory"]
            }
        elif schema.__name__ == "SourceIntroductionPlan":
            content = {"evidence_order": [item["id"] for item in context["evidence"]]}
        result = schema.model_validate(copy.deepcopy(content))
        if validate:
            errors = validate(result)
            if errors:
                raise GenerationError(";".join(errors))
        return result, {"model": self.model_name, "attempts": 1}


def wait_run(repository, run_id):
    """Wait for an actual submitted test worker with a bounded deadline."""
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        run = repository.get_run(run_id)
        if run["status"] not in {"queued", "running"}:
            return run
        time.sleep(0.01)
    raise AssertionError("Live test worker did not terminate")


@pytest.fixture
def complete_document(analysis, sections):
    """Build the canonical final object with deterministic server-assigned IDs."""
    from cybersrs.validation import assign_ids

    assigned = {
        name: assign_ids(name, copy.deepcopy(content)) for name, content in sections.items()
    }
    evidence = build_evidence(DESCRIPTION, [])
    decision = rank_sdlc(evidence)
    from cybersrs.lifecycle_projection import compose_lifecycle
    from cybersrs.schemas import LifecycleWorkPlan
    from cybersrs.validation import requirements_from

    rows = requirements_from(assigned)
    assigned["sdlc"] = compose_lifecycle(
        LifecycleWorkPlan(
            justification=assigned["sdlc"]["justification"],
            work_groups=[{"requirement_ids": [row["id"] for row in rows]}],
        ),
        decision["required_model"],
        rows,
        assigned["verification"],
        evidence,
        analysis,
    )
    return Document(
        project_id="synthetic",
        title=analysis.title,
        original_description=DESCRIPTION,
        evidence=evidence,
        analysis=analysis,
        sources=[],
        **assigned,
        sdlc_policy_version=POLICY_VERSION,
        sdlc_factors=decision["factors"],
        sdlc_candidates=decision["ranked_candidates"],
        model_name="test-qwen",
        prompt_version="test",
    )

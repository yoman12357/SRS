"""Single coordinator with sequential, schema-bound SRS specialist agents."""

from __future__ import annotations

import hashlib
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from . import prompts
from .acceptance_grounding import preserve_nonexclusive_tests
from .advisory_agent import generate_glossary, generate_risks, generate_threats
from .advisory_candidates import SOURCE_ADVISORY_VERSION
from .architecture_agent import generate_architecture
from .audit import audit_scope
from .category_metadata import (
    CATEGORY_METADATA_VERSION,
    empty_category_metadata,
    validate_empty_category_index,
)
from .clarification_policy import (
    consolidate_document_decisions,
    normalize_analysis_decisions,
    normalize_section_decisions,
    questions_after_review,
)
from .compact_requirements import generate_compact_requirements
from .config import Settings
from .evidence import (
    build_evidence,
    context_evidence_ids,
    has_concrete_product_behavior,
    normative_evidence_ids,
    preserve_skipped_decisions,
    validate_analysis,
)
from .introduction_agent import generate_introduction
from .introduction_projection import (
    INTRODUCTION_PROJECTION_VERSION,
    introduction_projection_issues,
)
from .knowledge import KnowledgeBase
from .permission_verification import permission_test_contract, permission_test_gaps
from .policy_applicability import compliance_requirement_context
from .prohibition_verification import (
    prohibition_test_contract,
    prohibition_test_gaps,
    verbatim_prohibition_statements,
)
from .provider import OUTPUT_MODEL, CancelledError, GenerationError, LLMProvider, check_cancel
from .quantity_normalization import preserve_retention_duration, preserve_section_retention
from .repository import Repository, canonical_hash, source_input_hash
from .requirement_repair import (
    REQUIREMENT_REPAIR_VERSION,
    complete_source_gaps,
    is_boundary_test_issue,
    normative_header_issues,
    repair_canonical_acceptance,
    repair_linked_acceptance,
    repair_source_capacity_criterion,
)
from .scenario_agent import generate_scenarios
from .scenario_projection import SCENARIO_PROJECTION_VERSION, scenario_projection_issues
from .schemas import (
    REQUIREMENT_PREFIXES,
    SECTION_SCHEMAS,
    Analysis,
    Answer,
    Document,
    Requirement,
    RequirementRationaleRepair,
    SourceChunk,
)
from .sdlc import POLICY_VERSION, rank_sdlc
from .sdlc_agent import SDLC_PROMPT_VERSION, generate_sdlc
from .semantics import missing_source_actions, missing_source_quantities
from .source_completion import (
    capacity_repair_statement,
    source_permission_statement,
    source_role_denial_statement,
)
from .source_obligations import normalize_requirement_sections
from .validation import (
    assign_ids,
    consolidate_duplicates,
    interactive_requirement_ids,
    preserve_scope_evidence,
    rebuild_functional_view,
    requirements_from,
    validate_document,
    validate_section,
)
from .verification_agent import generate_verification
from .verification_projection import (
    VERIFICATION_PROJECTION_VERSION,
    verification_projection_issues,
)

IEEE_RUN_LIMIT_SECONDS = 480


def input_hash(project: dict) -> str:
    """Identify exact authoritative inputs, excluding model interpretation."""
    return source_input_hash(project)


def reviewed_clarifications(project: dict) -> dict:
    """Prepare the questions for the exact analysis and inputs being reviewed."""
    if not project["analysis"] or not project["analysis"]["supported"]:
        raise ValueError("supported_analysis_required")
    analysis = Analysis.model_validate(project["analysis"])
    answers = [Answer.model_validate(answer) for answer in project["answers"]]
    evidence = build_evidence(project["description"], answers)
    return {
        "review_token": canonical_hash(
            {"inputs": input_hash(project), "analysis": project["analysis"]}
        ),
        "questions": [
            question.model_dump()
            for question in questions_after_review(analysis, evidence, answers)
        ],
    }


def _same_requirement_behavior(revised: dict, previous: dict) -> bool:
    """Keep factual behavior/source changes distinct from titles and category metadata."""
    fields = (
        "id",
        "statement",
        "acceptance_criteria",
        "evidence_ids",
        "sources",
        "dependencies",
        "basis",
        "unresolved_decisions",
    )

    def behavior(section: dict) -> list[dict]:
        return [{key: item.get(key) for key in fields} for item in section.get("requirements", [])]

    return behavior(revised) == behavior(previous) and revised.get(
        "related_acceptance_criteria", []
    ) == previous.get("related_acceptance_criteria", [])


class Orchestrator:
    """Queue workflows once, run agents sequentially, and persist validated checkpoints."""

    def __init__(
        self,
        settings: Settings,
        repository: Repository,
        provider: LLMProvider,
        knowledge: KnowledgeBase,
    ) -> None:
        """Initialize a single workflow executor with cooperative cancellation handles."""
        self.settings, self.repository = settings, repository
        self.provider, self.knowledge = provider, knowledge
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cybersrs-agents")
        self.cancels: dict[str, threading.Event] = {}
        self._lock = threading.RLock()

    def start(
        self,
        project_id: str,
        kind: str = "generate",
        *,
        version_id: str | None = None,
        section: str | None = None,
        edited_content: dict | None = None,
        resume_from: str | None = None,
        checkpoint_edits: dict[str, dict] | None = None,
        edit_actor: str = "human",
        review_token: str | None = None,
        answers: list[Answer] | None = None,
    ) -> dict:
        """Persist and dispatch an analysis, generation or version-revision workflow."""
        if edit_actor not in {"human", "assistant"}:
            raise ValueError("invalid_edit_actor")
        with self._lock:
            project = self.repository.get_project(project_id)
            if kind != "analyse" and not project["analysis"]:
                raise ValueError("analysis_required")
            if kind != "analyse" and not project["analysis"]["supported"]:
                raise ValueError("unsupported_domain")
            for existing_id in self.cancels:
                existing = self.repository.get_run(existing_id)
                exclusive = review_token is not None or existing["project_id"] == project_id
                if exclusive and existing["status"] in {"queued", "running"}:
                    raise ValueError("project_run_already_active")
            analyse_answers = False
            budget = self.settings.generation_timeout_seconds
            if review_token is not None:
                reviewed = reviewed_clarifications(project)
                if reviewed["review_token"] != review_token:
                    raise ValueError("analysis_review_changed")
                known = {question["id"]: question["question"] for question in reviewed["questions"]}
                merged = {answer["question_id"]: answer for answer in project["answers"]}
                for answer in answers or []:
                    if answer.question_id not in known or answer.question_id in merged:
                        raise ValueError("unknown_or_duplicate_question")
                    merged[answer.question_id] = Answer(
                        question_id=answer.question_id,
                        text=answer.text if not answer.skipped else "",
                        skipped=answer.skipped or not answer.text.strip(),
                        question_text=known[answer.question_id],
                    ).model_dump()
                if answers:
                    project = self.repository.update_project(
                        project_id, answers=list(merged.values()),
                        expected_input_hash=input_hash(project),
                    )
                    analyse_answers = True
                budget = min(budget, IEEE_RUN_LIMIT_SECONDS)
            deadline = time.monotonic() + budget
            run = self.repository.create_run(project_id, kind, input_hash(project))
            self.repository.update_run(
                run["id"],
                checkpoint=(
                    "_request",
                    {
                        "version_id": version_id,
                        "section": section,
                        "edited_content": edited_content,
                        "checkpoint_edits": checkpoint_edits,
                        "edit_actor": edit_actor,
                    },
                ),
            )
            self.repository.update_run(
                run["id"],
                checkpoint=(
                    "_provenance",
                    {
                        "model": self.provider.model_name,
                        "budget_seconds": budget,
                        "section_timeout_seconds": self.settings.section_timeout_seconds,
                        "atomic_test_repair_limit": self.settings.atomic_test_repair_limit,
                        "compact_requirements_enabled": self.settings.compact_requirements_enabled,
                        "ollama_stream": self.settings.ollama_stream,
                        "ollama_raw_chatml": self.settings.ollama_raw_chatml,
                        "ollama_exclusive_main_model": self.settings.ollama_exclusive_main_model,
                        "prompt_version": prompts.PROMPT_VERSION,
                        "sdlc_prompt_version": SDLC_PROMPT_VERSION,
                        "category_metadata_version": CATEGORY_METADATA_VERSION,
                        "verification_projection_version": VERIFICATION_PROJECTION_VERSION,
                        "introduction_projection_version": INTRODUCTION_PROJECTION_VERSION,
                        "scenario_projection_version": SCENARIO_PROJECTION_VERSION,
                        "source_advisory_version": SOURCE_ADVISORY_VERSION,
                    },
                ),
            )
            cancel = threading.Event()
            self.cancels[run["id"]] = cancel
            self.executor.submit(
                self._execute,
                run["id"],
                project,
                cancel,
                version_id,
                section,
                edited_content,
                resume_from,
                checkpoint_edits,
                edit_actor,
                deadline,
                review_token is not None,
                analyse_answers,
            )
        return {**run, "budget_seconds": budget}

    def retry(
        self, run_id: str, section_edits: dict[str, dict] | None = None, editor: str = "human"
    ) -> dict:
        """Resume only terminated work whose authoritative inputs still match exactly."""
        old = self.repository.get_run(run_id)
        if old["status"] not in {"failed", "cancelled", "interrupted"}:
            raise ValueError("run_not_retryable")
        project = self.repository.get_project(old["project_id"])
        if input_hash(project) != old["input_hash"]:
            raise ValueError("retry_inputs_changed")
        request = dict(old["checkpoints"].get("_request", {}))
        if section_edits:
            if old["kind"] != "generate":
                raise ValueError("checkpoint_edits_require_generation_run")
            for name, content in section_edits.items():
                if name not in SECTION_SCHEMAS:
                    raise ValueError("unknown_edited_section")
                SECTION_SCHEMAS[name].model_validate(content)
            request["checkpoint_edits"] = section_edits
            request["edit_actor"] = editor
        return self.start(old["project_id"], old["kind"], **request, resume_from=run_id)

    def cancel(self, run_id: str) -> dict:
        """Cancel an authoritative live handle; completed work remains immutable."""
        with self._lock:
            cancel = self.cancels.get(run_id)
            if cancel is not None:
                cancel.set()
        return self.repository.get_run(run_id)

    def shutdown(self) -> None:
        """Signal every worker before graceful application shutdown."""
        with self._lock:
            for cancel in self.cancels.values():
                cancel.set()
        self.executor.shutdown(wait=False, cancel_futures=False)

    def _execute(
        self,
        run_id: str,
        project: dict,
        cancel: threading.Event,
        version_id: str | None,
        section: str | None,
        edited_content: dict | None,
        resume_from: str | None,
        checkpoint_edits: dict[str, dict] | None,
        edit_actor: str,
        deadline: float,
        reviewed: bool,
        analyse_answers: bool,
    ) -> None:
        scope = audit_scope(self.repository, project["id"], run_id)
        scope.__enter__()
        try:
            self.repository.record_audit(project["id"], "workflow_input", project, run_id)
            check_cancel(cancel, deadline)
            self.repository.update_run(run_id, status="running")
            analysis_only = self.repository.get_run(run_id)["kind"] == "analyse"
            if analysis_only or analyse_answers:
                analysis_deadline = min(
                    deadline, time.monotonic() + self.settings.section_timeout_seconds
                )
                self._analyse(run_id, project, cancel, analysis_deadline)
            if not analysis_only:
                if analyse_answers:
                    analysed = self.repository.get_project(project["id"])
                    if input_hash(analysed) != input_hash(project):
                        raise GenerationError("project_inputs_changed")
                    if not analysed["analysis"] or not analysed["analysis"]["supported"]:
                        raise GenerationError("unsupported_domain")
                    project = analysed
                for attempt in range(2 if reviewed else 1):
                    try:
                        self._generate(
                            run_id, project, cancel, deadline, version_id, section,
                            edited_content, resume_from, checkpoint_edits, edit_actor,
                        )
                        break
                    except GenerationError as exc:
                        if not reviewed or attempt or not re.match(
                            r"(?:section_validation_failed|section_completion_failed|"
                            r"passage_completion_failed|targeted_requirement_repair_failed|"
                            r"local_model_stream_error|invalid_model_envelope|generation_budget_exhausted)",
                            str(exc),
                        ):
                            raise
                        check_cancel(cancel, deadline)
                        resume_from = run_id
            self.repository.update_run(run_id, status="completed")
        except CancelledError:
            self.repository.update_run(run_id, status="cancelled", error="generation_cancelled")
        except (GenerationError, ValueError, KeyError) as exc:
            # All expected errors carry field names/codes only, never raw inputs.
            safe = str(exc) if isinstance(exc, GenerationError) else type(exc).__name__
            if safe == "generation_budget_exhausted" and reviewed and time.monotonic() >= deadline:
                safe = "generation_time_limit"
            elif safe == "generation_budget_exhausted":
                events = self.repository.get_run(run_id)["events"]
                agent = events[-1].get("agent", "generation") if events else "generation"
                safe = f"section_budget_exhausted:{agent}"
            self.repository.update_run(run_id, status="failed", error=safe[:1000])
        except Exception:
            self.repository.update_run(run_id, status="failed", error="unexpected_workflow_failure")
        finally:
            scope.__exit__(None, None, None)
            with self._lock:
                self.cancels.pop(run_id, None)

    def _analyse(
        self,
        run_id: str,
        project: dict,
        cancel: threading.Event,
        deadline: float,
    ) -> None:
        evidence = build_evidence(
            project["description"], [Answer.model_validate(a) for a in project["answers"]]
        )
        context = {
            "evidence": [item.model_dump() for item in evidence],
            "scope_clarification_needed": not has_concrete_product_behavior(evidence),
            "previous_answers": project["answers"],
            "project_context_evidence_ids": sorted(context_evidence_ids(evidence)),
            "normative_evidence_ids": sorted(normative_evidence_ids(evidence)),
            "references": [
                {"name": d["name"], "text": d["text"]}
                for d in self.repository.list_documents(project["id"])
            ],
        }
        self.repository.update_run(run_id, event={"agent": "analysis", "state": "running"})

        def validate(candidate: Analysis) -> list[str]:
            """Preserve explicit skips before any analysis is returned or persisted."""
            answers = [Answer.model_validate(a) for a in project["answers"]]
            preserved = normalize_analysis_decisions(
                normalize_requirement_sections(candidate, evidence), evidence, answers
            )
            preserved = preserve_skipped_decisions(preserved, answers)
            candidate.assessments = preserved.assessments
            candidate.stakeholders = preserved.stakeholders
            candidate.questions = preserved.questions
            candidate.unresolved_decisions = preserved.unresolved_decisions
            return validate_analysis(candidate, evidence, answers)

        result, provenance = self.provider.generate(
            prompts.ANALYSIS,
            context,
            Analysis,
            cancel,
            deadline,
            validate,
        )
        for question in result.questions:
            fingerprint = " ".join(question.question.casefold().split()).encode("utf-8")
            question.id = "Q-" + hashlib.sha256(fingerprint).hexdigest()[:12]
        check_cancel(cancel, deadline)
        if input_hash(self.repository.get_project(project["id"])) != input_hash(project):
            raise GenerationError("project_inputs_changed")
        self.repository.update_project(
            project["id"], analysis=result.model_dump(), expected_input_hash=input_hash(project)
        )
        self.repository.update_run(
            run_id,
            event={"agent": "analysis", "state": "completed", **provenance},
            checkpoint=("analysis", result.model_dump()),
        )

    def _generate(
        self,
        run_id: str,
        project: dict,
        cancel: threading.Event,
        deadline: float,
        version_id: str | None,
        selected_section: str | None,
        edited_content: dict | None,
        resume_from: str | None,
        checkpoint_edits: dict[str, dict] | None,
        edit_actor: str,
    ) -> None:
        analysis = Analysis.model_validate(project["analysis"])
        evidence = build_evidence(
            project["description"], [Answer.model_validate(a) for a in project["answers"]]
        )
        if not version_id:
            analysis = normalize_analysis_decisions(
                normalize_requirement_sections(analysis, evidence), evidence,
                [Answer.model_validate(answer) for answer in project["answers"]],
            )
        sections: dict = {}
        source_map: dict[str, SourceChunk] = {}
        section_models: dict[str, list[str]] = {}
        category_metadata_version = CATEGORY_METADATA_VERSION
        verification_projection_version = VERIFICATION_PROJECTION_VERSION
        introduction_projection_version = INTRODUCTION_PROJECTION_VERSION
        scenario_projection_version = SCENARIO_PROJECTION_VERSION
        if version_id:
            old = self.repository.get_version(project["id"], version_id)["content"]
            analysis = Analysis.model_validate(old["analysis"])
            category_metadata_version = old.get("category_metadata_version", "")
            verification_projection_version = old.get("verification_projection_version", "")
            introduction_projection_version = old.get("introduction_projection_version", "")
            scenario_projection_version = old.get("scenario_projection_version", "")
            # A revision cannot silently apply new input facts to old requirements.
            if old["evidence"] != [item.model_dump() for item in evidence]:
                raise GenerationError("inputs_changed_generate_new_document")
            if old.get("input_fingerprint") != input_hash(project):
                raise GenerationError("references_changed_generate_new_document")
            sections = {name: old[name] for name in SECTION_SCHEMAS}
            section_models = old.get("section_models", {}) or {
                name: old.get("models_used", [old["model_name"]]) for name in sections
            }
            source_map = {
                source["id"]: SourceChunk.model_validate(source) for source in old["sources"]
            }
        regenerate = list(SECTION_SCHEMAS)
        if selected_section:
            regenerate = [selected_section]
            if selected_section in REQUIREMENT_PREFIXES:
                regenerate += [
                    "compliance",
                    "architecture",
                    "threats",
                    "risks",
                    "scenarios",
                    "verification",
                    "sdlc",
                ]
            elif selected_section == "introduction":
                regenerate += ["sdlc"]
            elif selected_section == "architecture":
                regenerate += ["threats", "risks"]
            elif selected_section == "verification":
                regenerate += ["sdlc"]
            if (
                edited_content is not None
                and selected_section in REQUIREMENT_PREFIXES
                and _same_requirement_behavior(edited_content, sections[selected_section])
            ):
                # Applicability wording and category indexes do not change the
                # canonical behavior or authored tests consumed by specialists.
                regenerate = [selected_section]
            if checkpoint_edits:
                requested = set(regenerate) | set(checkpoint_edits)
                regenerate = [name for name in SECTION_SCHEMAS if name in requested]
        decision = rank_sdlc(evidence)
        old_checkpoints = self.repository.get_run(resume_from)["checkpoints"] if resume_from else {}
        prior_events = self.repository.get_run(resume_from)["events"] if resume_from else []
        old_provenance = old_checkpoints.get("_provenance", {})
        if (
            old_provenance.get("model") != self.provider.model_name
            or old_provenance.get("prompt_version") != prompts.PROMPT_VERSION
        ):
            old_checkpoints = {}
        elif old_provenance.get("sdlc_prompt_version") != SDLC_PROMPT_VERSION:
            old_checkpoints = {
                key: value for key, value in old_checkpoints.items() if key != "sdlc"
            }
        projection_upgrade = (
            bool(old_checkpoints)
            and old_provenance.get("verification_projection_version")
            != VERIFICATION_PROJECTION_VERSION
        )
        if projection_upgrade:
            old_checkpoints = {
                key: value
                for key, value in old_checkpoints.items()
                if key not in {"verification", "sdlc"}
            }
        introduction_upgrade = (
            bool(old_checkpoints)
            and old_provenance.get("introduction_projection_version")
            != INTRODUCTION_PROJECTION_VERSION
        )
        if introduction_upgrade:
            old_checkpoints = {
                key: value
                for key, value in old_checkpoints.items()
                if key not in {"introduction", "sdlc"}
            }
        scenario_upgrade = (
            bool(old_checkpoints)
            and old_provenance.get("scenario_projection_version") != SCENARIO_PROJECTION_VERSION
        )
        if scenario_upgrade:
            old_checkpoints = {
                key: value for key, value in old_checkpoints.items() if key != "scenarios"
            }
        advisory_upgrade = (
            bool(old_checkpoints)
            and old_provenance.get("source_advisory_version") != SOURCE_ADVISORY_VERSION
        )
        if advisory_upgrade:
            old_checkpoints = {
                key: value
                for key, value in old_checkpoints.items()
                if key not in {"threats", "risks", "glossary"}
            }
        for source in old_checkpoints.get("_sources", {}).get("chunks", []):
            source_map[source["id"]] = SourceChunk.model_validate(source)
        if old_checkpoints:
            self.repository.update_run(
                run_id,
                checkpoint=(
                    "_sources",
                    {
                        "chunks": [source.model_dump() for source in source_map.values()],
                    },
                ),
            )
        can_reuse = True
        workflow_deadline = deadline
        for name in regenerate:
            section_started = time.monotonic()
            deadline = min(
                workflow_deadline, section_started + self.settings.section_timeout_seconds
            )
            metadata_only_refresh = False
            projection_only_refresh = (
                (name == "verification" and projection_upgrade)
                or (name == "introduction" and introduction_upgrade)
                or (name == "scenarios" and scenario_upgrade)
                or (name in {"threats", "risks", "glossary"} and advisory_upgrade)
            )
            if name in (checkpoint_edits or {}):
                can_reuse = False
            check_cancel(cancel, deadline)
            if name == "compliance":
                rebuild_functional_view(sections, analysis)
            if can_reuse and name in old_checkpoints:
                candidate = SECTION_SCHEMAS[name].model_validate(old_checkpoints[name]).model_dump()
                previous = {key: value for key, value in sections.items() if key != name}
                previous_event = next(
                    (
                        event
                        for event in reversed(prior_events)
                        if event.get("agent") == name and event.get("state") == "completed"
                    ),
                    {},
                )
                issues = validate_section(
                    name, candidate, evidence, analysis, list(source_map.values()), previous
                )
                if (
                    name == "verification"
                    and previous_event.get("verification_projection_version")
                    == VERIFICATION_PROJECTION_VERSION
                ):
                    issues += verification_projection_issues(candidate, previous)
                if (
                    name == "introduction"
                    and previous_event.get("introduction_projection_version")
                    == INTRODUCTION_PROJECTION_VERSION
                ):
                    issues += introduction_projection_issues(candidate, evidence, analysis)
                if (
                    name == "scenarios"
                    and previous_event.get("scenario_projection_version")
                    == SCENARIO_PROJECTION_VERSION
                ):
                    issues += scenario_projection_issues(candidate, previous, evidence, analysis)
                if not issues:
                    metadata_only_refresh = (
                        name in REQUIREMENT_PREFIXES
                        and not candidate["requirements"]
                        and not candidate.get("related_acceptance_criteria")
                        and old_provenance.get("category_metadata_version")
                        != CATEGORY_METADATA_VERSION
                    )
                if not issues and not metadata_only_refresh:
                    sections[name] = candidate
                    reused_models = previous_event.get(
                        "output_models",
                        [previous_event.get("model", self.provider.model_name)],
                    )
                    section_models[name] = reused_models
                    if name == "verification":
                        verification_projection_version = previous_event.get(
                            "verification_projection_version", ""
                        )
                    if name == "introduction":
                        introduction_projection_version = previous_event.get(
                            "introduction_projection_version", ""
                        )
                    if name == "scenarios":
                        scenario_projection_version = previous_event.get(
                            "scenario_projection_version", ""
                        )
                    if resume_from == run_id:
                        continue
                    self.repository.update_run(
                        run_id,
                        event={
                            "agent": name,
                            "state": "completed",
                            "reused": True,
                            **(
                                {"scenario_projection_version": scenario_projection_version}
                                if name == "scenarios"
                                else {}
                            ),
                            **(
                                {"introduction_projection_version": introduction_projection_version}
                                if name == "introduction"
                                else {}
                            ),
                            **(
                                {"verification_projection_version": verification_projection_version}
                                if name == "verification"
                                else {}
                            ),
                            "source_run": resume_from,
                            "output_models": reused_models,
                            "model": next(
                                (
                                    event.get("model", self.provider.model_name)
                                    for event in reversed(prior_events)
                                    if event.get("agent") == name
                                    and event.get("state") == "completed"
                                ),
                                self.provider.model_name,
                            ),
                        },
                        checkpoint=(name, candidate),
                    )
                    continue
            can_reuse = can_reuse and (metadata_only_refresh or projection_only_refresh)
            self.repository.update_run(
                run_id,
                event={
                    "agent": name,
                    "state": "running",
                    "budget_seconds": self.settings.section_timeout_seconds,
                },
            )
            sources: list[SourceChunk] = []
            retrieval_warning = None
            reviewed_revision = (
                name == selected_section and edited_content is not None
            ) or name in (checkpoint_edits or {})
            try:
                if (
                    not reviewed_revision
                    and name not in REQUIREMENT_PREFIXES
                    and name
                    not in {
                        "introduction",
                        "architecture",
                        "glossary",
                        "scenarios",
                        "verification",
                        "sdlc",
                    }
                ):
                    sources = self.knowledge.retrieve(
                        f"{analysis.domain}. {name}. {project['description']}",
                        project["id"],
                        timeout_seconds=min(10, max(0.1, deadline - time.monotonic())),
                    )
            except Exception:
                retrieval_warning = "local_retrieval_unavailable"
            for source in sources:
                source_map[source.id] = source
            predecessors = {key: value for key, value in sections.items() if key != name}
            assigned_ids = {
                item.evidence_id for item in analysis.assessments if name in item.sections
            }
            exclusion_ids = {
                item.evidence_id for item in analysis.assessments if item.kind == "exclusion"
            }
            already_covered = {
                eid for req in requirements_from(predecessors) for eid in req["evidence_ids"]
            }
            context = {
                "assigned_section": name,
                "project_title": analysis.title,
                "evidence": [
                    item.model_dump()
                    for item in evidence
                    if name not in REQUIREMENT_PREFIXES or item.id in assigned_ids | exclusion_ids
                ],
                "analysis": {
                    "domain": analysis.domain,
                    "stakeholders": analysis.stakeholders,
                    "assessments": [
                        item.model_dump() for item in analysis.assessments if name in item.sections
                    ],
                    "unresolved_decisions": analysis.unresolved_decisions,
                },
                # Draft normative behavior from stakeholder evidence first. External
                # guidance cannot silently become a confirmed product decision.
                "sources": []
                if name in REQUIREMENT_PREFIXES
                else [source.model_dump() for source in sources],
                "existing_requirements": requirements_from(predecessors),
                "compliance_applicability": predecessors.get("compliance")
                if name
                in {
                    "risks",
                    "verification",
                    "sdlc",
                }
                else None,
                "scenario_required_requirement_ids": sorted(
                    interactive_requirement_ids(
                        requirements_from(predecessors),
                        analysis,
                    )
                )
                if name == "scenarios"
                else [],
                "required_evidence_ids": [
                    item.evidence_id
                    for item in analysis.assessments
                    if name in item.sections
                    and item.kind in {"requirement", "constraint"}
                    and item.evidence_id not in already_covered
                ],
                "sdlc_decision": decision if name == "sdlc" else None,
            }
            if name == "sdlc":
                context["verification_context"] = [
                    {
                        key: test[key]
                        for key in ("id", "requirement_ids", "test_type", "expected_result")
                    }
                    for test in predecessors.get("verification", {}).get("tests", [])
                ]
            if name == "compliance":
                context["existing_requirements"] = compliance_requirement_context(
                    context["existing_requirements"]
                )
            if name in {"threats", "risks"} and "architecture" in predecessors:
                design = predecessors["architecture"]
                if validate_section(
                    "architecture",
                    design,
                    evidence,
                    analysis,
                    list(source_map.values()),
                    predecessors,
                ):
                    raise GenerationError("prerequisite_architecture_requires_regeneration")
                context["design_context"] = {
                    "components": [
                        {
                            key: item[key]
                            for key in ("component_name", "responsibility", "requirement_ids")
                        }
                        for item in design["items"]
                    ],
                    "data_flows": [
                        {
                            key: item[key]
                            for key in (
                                "from_component",
                                "to_component",
                                "data_or_action",
                                "requirement_ids",
                            )
                        }
                        for item in design["data_flows"]
                    ],
                    "trust_boundaries": [
                        {
                            key: item[key]
                            for key in (
                                "untrusted_component",
                                "trusted_component",
                                "enforcement",
                                "requirement_ids",
                            )
                        }
                        for item in design["trust_boundaries"]
                    ],
                }
            if selected_section == name:
                context["previous_section"] = sections.get(name)
            if reviewed_revision:
                revision = (checkpoint_edits or {}).get(name, edited_content)
                candidate = assign_ids(
                    name, SECTION_SCHEMAS[name].model_validate(revision).model_dump()
                )
                issues = validate_section(
                    name, candidate, evidence, analysis, list(source_map.values()), predecessors
                )
                if issues:
                    raise GenerationError("edited_section_invalid:" + ";".join(issues))
                provenance = {"model": f"{edit_actor}_edit", "attempts": 0}
                if name == "verification":
                    verification_projection_version = ""
                if name == "introduction":
                    introduction_projection_version = ""
                if name == "scenarios":
                    scenario_projection_version = ""
            elif name in REQUIREMENT_PREFIXES:
                if self.settings.compact_requirements_enabled:
                    candidate, provenance = generate_compact_requirements(
                        self.provider,
                        name,
                        evidence,
                        analysis,
                        list(source_map.values()),
                        predecessors,
                        cancel,
                        deadline,
                        max_test_repairs=self.settings.atomic_test_repair_limit,
                    )
                else:
                    candidate, provenance = self._generate_requirement_passages(
                        run_id,
                        name,
                        context,
                        evidence,
                        analysis,
                        list(source_map.values()),
                        predecessors,
                        old_checkpoints,
                        cancel,
                        deadline,
                    )
            elif name in {
                "architecture",
                "sdlc",
                "verification",
                "introduction",
                "scenarios",
                "threats",
                "risks",
                "glossary",
            }:

                def reject_design(content: dict, issues: list[str], section_name=name) -> None:
                    """Retain private parsed diagnostics without presenting a completed design."""
                    self.repository.update_run(
                        run_id,
                        checkpoint=(
                            f"_rejected_{section_name}",
                            {
                                "content": content,
                                "errors": issues,
                                "model": OUTPUT_MODEL.get() or self.provider.model_name,
                                "status": "schema_valid_semantically_rejected",
                            },
                        ),
                    )

                generator = {
                    "architecture": generate_architecture,
                    "sdlc": generate_sdlc,
                    "verification": generate_verification,
                    "introduction": generate_introduction,
                    "scenarios": generate_scenarios,
                    "threats": generate_threats,
                    "risks": generate_risks,
                    "glossary": generate_glossary,
                }[name]
                candidate, provenance = generator(
                    self.provider,
                    context,
                    evidence,
                    analysis,
                    list(source_map.values()),
                    predecessors,
                    cancel,
                    deadline,
                    reject_design,
                )
                if name == "verification":
                    verification_projection_version = VERIFICATION_PROJECTION_VERSION
                if name == "introduction":
                    introduction_projection_version = INTRODUCTION_PROJECTION_VERSION
                if name == "scenarios":
                    scenario_projection_version = SCENARIO_PROJECTION_VERSION
            else:

                def validate(candidate, section_name=name, previous=predecessors):
                    if section_name == "introduction":
                        preserved = SECTION_SCHEMAS[section_name].model_validate(
                            preserve_scope_evidence(candidate.model_dump(), evidence, analysis)
                        )
                        candidate.items = preserved.items
                        candidate.open_issues = preserved.open_issues
                    content = assign_ids(section_name, candidate.model_dump())
                    issues = validate_section(
                        section_name,
                        content,
                        evidence,
                        analysis,
                        list(source_map.values()),
                        previous,
                    )
                    if (
                        section_name == "sdlc"
                        and content["selected_model"] != decision["required_model"]
                    ):
                        issues.append("must_preserve_deterministic_sdlc_winner")
                    if issues:
                        self.repository.update_run(
                            run_id,
                            checkpoint=(
                                f"_rejected_{section_name}",
                                {
                                    "content": content,
                                    "errors": issues,
                                    "model": OUTPUT_MODEL.get() or self.provider.model_name,
                                    "status": "schema_valid_semantically_rejected",
                                },
                            ),
                        )
                    return issues

                result, provenance = self.provider.generate(
                    prompts.COMMON + prompts.SECTION_INSTRUCTIONS[name],
                    context,
                    SECTION_SCHEMAS[name],
                    cancel,
                    deadline,
                    validate,
                )
                candidate = assign_ids(name, result.model_dump())
            check_cancel(cancel, deadline)
            human_section = selected_section == name and edited_content is not None
            if name != "introduction" and not human_section:
                candidate = normalize_section_decisions(candidate, evidence)
            sections[name] = candidate
            self.repository.update_run(
                run_id,
                checkpoint=(
                    "_sources",
                    {
                        "chunks": [source.model_dump() for source in source_map.values()],
                    },
                ),
            )
            self.repository.update_run(
                run_id,
                event={
                    "agent": name,
                    "state": "completed",
                    **provenance,
                    "elapsed_seconds": round(time.monotonic() - section_started, 3),
                    "retrieval_warning": retrieval_warning,
                },
                checkpoint=(name, candidate),
            )
            section_models[name] = provenance.get("output_models", [provenance["model"]])
        deadline = workflow_deadline
        rebuild_functional_view(sections, analysis)
        if not version_id and not checkpoint_edits:
            analysis = consolidate_document_decisions(analysis, sections, evidence)
        actual_models = sorted(
            {
                model
                for tags in section_models.values()
                for model in tags
                if model and model not in {"human_edit", "assistant_edit"}
            }
        )
        document = Document(
            project_id=project["id"],
            title=analysis.title,
            original_description=project["description"],
            evidence=evidence,
            analysis=analysis,
            sources=list(source_map.values()),
            **sections,
            sdlc_policy_version=POLICY_VERSION,
            sdlc_prompt_version=SDLC_PROMPT_VERSION,
            category_metadata_version=category_metadata_version,
            verification_projection_version=verification_projection_version,
            introduction_projection_version=introduction_projection_version,
            scenario_projection_version=scenario_projection_version,
            sdlc_factors=decision["factors"],
            sdlc_candidates=decision["ranked_candidates"],
            model_name=" + ".join(actual_models) or self.provider.model_name,
            requested_model_name=self.provider.model_name,
            models_used=actual_models,
            section_models=section_models,
            prompt_version=prompts.PROMPT_VERSION,
            input_fingerprint=input_hash(project),
        )
        report = validate_document(document)
        self.repository.update_run(run_id, checkpoint=("quality", report.model_dump()))
        if report.status == "invalid":
            raise GenerationError("final_quality_gate_failed")
        with self._lock:
            check_cancel(cancel, deadline)
            saved = self.repository.save_version(
                project["id"],
                document.model_dump(),
                report.model_dump(),
                run_id,
                expected_input_hash=input_hash(project),
            )
            self.repository.update_run(
                run_id, event={"agent": "document", "state": "completed", "version_id": saved["id"]}
            )

    def _generate_requirement_passages(
        self,
        run_id: str,
        name: str,
        context: dict,
        evidence: list,
        analysis: Analysis,
        sources: list[SourceChunk],
        predecessors: dict,
        checkpoints: dict,
        cancel: threading.Event,
        deadline: float,
    ) -> tuple[dict, dict]:
        """Run one section specialist over isolated source passages, preserving valid siblings."""
        schema = SECTION_SCHEMAS[name]
        assembled = schema.model_validate(
            checkpoints.get(
                f"_partial_{name}",
                {
                    "applicability_reason": "Source-backed obligations for this category.",
                    "requirements": [],
                },
            )
        ).model_dump()
        original = {item.id: item for item in evidence}
        assigned = {
            item.evidence_id
            for item in analysis.assessments
            if name in item.sections and item.kind in {"requirement", "constraint", "exclusion"}
        }
        models = set(checkpoints.get(f"_partial_models_{name}", {}).get("models", []))
        # A second failed retry must retain the same validated passage siblings.
        # Copy them into this run before an uncovered passage can fail again.
        self.repository.update_run(run_id, checkpoint=(f"_partial_{name}", assembled))
        self.repository.update_run(
            run_id,
            checkpoint=(f"_partial_models_{name}", {"models": sorted(models)}),
        )
        attempts = 0
        completed = 0
        reasons = []
        for eid in sorted(assigned):
            previous = predecessors | {name: assembled}
            existing = requirements_from(previous)
            represented = " ".join(
                req["statement"] + " " + " ".join(ac["then"] for ac in req["acceptance_criteria"])
                for req in existing
                if eid in req["evidence_ids"]
            )
            if (
                represented
                and not missing_source_actions(
                    original[eid].quote, represented, include_capabilities=True
                )
                and not (missing_source_quantities(original[eid].quote, represented))
                and not permission_test_gaps(
                    original[eid].quote,
                    [
                        ac
                        for req in existing
                        if eid in req["evidence_ids"]
                        for ac in req["acceptance_criteria"]
                    ],
                )
                and not prohibition_test_gaps(
                    original[eid].quote,
                    [
                        ac
                        for req in existing
                        if eid in req["evidence_ids"]
                        for ac in req["acceptance_criteria"]
                    ],
                )
            ):
                for req in existing:
                    if eid in req["evidence_ids"] and req not in assembled["requirements"]:
                        if req["id"] not in assembled["related_requirement_ids"]:
                            assembled["related_requirement_ids"].append(req["id"])
                continue
            target_analysis = analysis.model_copy(
                update={
                    "assessments": [
                        item for item in analysis.assessments if item.evidence_id == eid
                    ],
                }
            )
            batch_context = context | {
                "source_permission_statement": source_permission_statement(original[eid].quote),
                "related_acceptance_requirement_ids": [
                    req["id"] for req in existing if eid in req["evidence_ids"]
                ],
                "acceptance_obligations": permission_test_contract(original[eid].quote),
                "prohibition_verification": prohibition_test_contract(original[eid].quote),
                "allowed_prohibition_statements": verbatim_prohibition_statements(
                    original[eid].quote
                ),
                "test_fixture_guidance": "Use a controlled fixture for the source actor/state. "
                "Unspecified mechanisms remain parameters. Do not assume an unmentioned "
                "authentication method is either required or unnecessary; the source role "
                "can be represented by a test identity without inventing a login policy.",
                "evidence": [original[eid].model_dump()],
                "required_evidence_ids": [eid],
                "analysis": {
                    "domain": analysis.domain,
                    "assessments": [item.model_dump() for item in target_analysis.assessments],
                },
                "existing_requirements": [
                    {"id": req["id"], "title": req["title"]} for req in existing
                ],
                "scope_constraints": [
                    original[item.evidence_id].quote
                    for item in analysis.assessments
                    if item.kind == "exclusion"
                ],
                "drafting_instruction": "Draft ONLY the supplied source passage. Keep all its "
                "actors, positive actions, denials and outcomes. Do not combine it with another "
                "passage or copy a previous requirement. Scope constraints restrict this work; "
                "do not turn them into additional requirements in this passage.",
            }
            if assembled["requirements"]:
                batch_context["completion_instruction"] = (
                    "Return only additional requirements for this passage; "
                    "existing ones are retained."
                )
            offset = len(assembled["requirements"])

            def validate_batch(
                candidate,
                prior=previous,
                target=target_analysis,
                start=offset,
                source_id=eid,
                permission=batch_context["source_permission_statement"],
            ):
                normalized = schema.model_validate(
                    consolidate_duplicates(
                        preserve_section_retention(candidate.model_dump(), evidence),
                        prior,
                    )
                )
                for field in (
                    "requirements",
                    "related_requirement_ids",
                    "related_acceptance_criteria",
                ):
                    setattr(candidate, field, getattr(normalized, field))
                content = assign_ids(name, candidate.model_dump(), start)
                issues = validate_section(name, content, evidence, target, sources, prior)
                if permission and any(
                    row["statement"] != permission for row in content["requirements"]
                ):
                    issues.append("completion_must_preserve_source_statement")
                if any(set(req["evidence_ids"]) - {source_id} for req in content["requirements"]):
                    issues.append("passage_requirement_must_use_only_its_original_evidence")
                source_owned_ids = {
                    req["id"]
                    for req in requirements_from(prior)
                    if source_id in req["evidence_ids"]
                }
                if any(
                    record["requirement_id"] not in source_owned_ids
                    or set(record["evidence_ids"]) - {source_id}
                    for record in content.get("related_acceptance_criteria", [])
                ):
                    issues.append("passage_linked_acceptance_must_use_its_original_source")
                if issues:
                    self.repository.update_run(
                        run_id,
                        checkpoint=(
                            f"_rejected_{name}",
                            {
                                "content": content,
                                "errors": issues,
                                "model": OUTPUT_MODEL.get() or self.provider.model_name,
                                "status": "schema_valid_semantically_rejected",
                            },
                        ),
                    )
                return [issue for issue in issues if not is_boundary_test_issue(issue)]

            try:
                result, provenance = self.provider.generate(
                    prompts.COMMON + prompts.SECTION_INSTRUCTIONS[name],
                    batch_context,
                    schema,
                    cancel,
                    deadline,
                    validate_batch,
                )
            except GenerationError as error:
                check_cancel(cancel, deadline)
                if not str(error).startswith("section_validation_failed:"):
                    raise
                rejected = self.repository.get_run(run_id)["checkpoints"].get(f"_rejected_{name}")
                if not rejected:
                    raise
                result, provenance = self._repair_rejected_requirements(
                    name,
                    rejected["content"],
                    batch_context,
                    evidence,
                    target_analysis,
                    sources,
                    previous,
                    cancel,
                    deadline,
                    rejected.get("model", self.provider.model_name),
                )
                provenance["attempts"] += error.attempts
                remaining = validate_batch(result)
                if remaining:
                    raise GenerationError(
                        "passage_repair_invalid:" + ";".join(remaining)
                    ) from error
            completed_batch, repair_models, repair_attempts = complete_source_gaps(
                self.provider,
                name,
                assign_ids(name, result.model_dump(), offset),
                batch_context,
                evidence,
                target_analysis,
                sources,
                previous,
                cancel,
                deadline,
            )
            issues = validate_section(
                name, completed_batch, evidence, target_analysis, sources, previous
            )
            if issues:
                raise GenerationError("passage_completion_failed:" + ";".join(issues))
            provenance["output_models"] = sorted(
                set(provenance.get("output_models", [provenance["model"]])) | repair_models
            )
            provenance["attempts"] += repair_attempts
            batch = assign_ids(name, completed_batch, offset)
            assembled["requirements"].extend(batch["requirements"])
            assembled["related_requirement_ids"] = sorted(
                set(assembled["related_requirement_ids"] + batch["related_requirement_ids"])
            )
            assembled["related_acceptance_criteria"].extend(batch["related_acceptance_criteria"])
            reasons.append(batch["applicability_reason"])
            models.update(provenance.get("output_models", [provenance["model"]]))
            attempts += provenance["attempts"]
            completed += 1
            self.repository.update_run(run_id, checkpoint=(f"_partial_{name}", assembled))
            self.repository.update_run(
                run_id,
                checkpoint=(
                    f"_partial_models_{name}",
                    {
                        "models": sorted(models),
                    },
                ),
            )
        if not completed and not assembled["requirements"]:
            relevant = [
                req
                for req in requirements_from(predecessors)
                if set(req["evidence_ids"]) & assigned
            ]
            empty_context = context | {
                "category_metadata_version": CATEGORY_METADATA_VERSION,
                "frozen_category_metadata": empty_category_metadata(
                    name, relevant, requirements_from(predecessors)
                ),
                "required_evidence_ids": [],
                "evidence": [],
                "existing_requirements": [
                    {key: req[key] for key in ("id", "statement", "dimensions")}
                    for req in requirements_from(predecessors)
                ],
                "drafting_instruction": "No uncovered product obligation belongs here. Explain "
                "coverage by selecting category-relevant IDs from the supplied complete "
                "canonical inventory. Include the required IDs, and use the frozen factual "
                "explanation exactly. An empty category index does not prove the project "
                "lacks that kind of behavior. Invent no requirement or supplementary test.",
            }

            def validate_empty(candidate):
                expected = empty_context["frozen_category_metadata"]
                metadata_errors = validate_empty_category_index(candidate, expected)
                if metadata_errors:
                    return metadata_errors
                return validate_section(
                    name, candidate.model_dump(), evidence, analysis, sources, predecessors
                )

            result, provenance = self.provider.generate(
                prompts.COMMON + prompts.SECTION_INSTRUCTIONS[name],
                empty_context,
                schema,
                cancel,
                deadline,
                validate_empty,
            )
            assembled = result.model_dump()
            models.add(provenance["model"])
            attempts += provenance["attempts"]
        elif reasons:
            assembled["applicability_reason"] = " ".join(dict.fromkeys(reasons))
        issues = validate_section(name, assembled, evidence, analysis, sources, predecessors)
        if issues:
            raise GenerationError("section_completion_failed:" + ";".join(issues))
        return assembled, {
            "model": " + ".join(sorted(models)) or self.provider.model_name,
            "output_models": sorted(models),
            "attempts": attempts,
            "source_passages_drafted": completed,
        }

    def _repair_rejected_requirements(
        self,
        name: str,
        content: dict,
        context: dict,
        evidence: list,
        analysis: Analysis,
        sources: list[SourceChunk],
        predecessors: dict,
        cancel: threading.Event,
        deadline: float,
        initial_model: str,
    ) -> tuple:
        """Ask for a narrow model-authored replacement while keeping every valid sibling intact."""
        fixed, models, attempts = complete_source_gaps(
            self.provider,
            name,
            SECTION_SCHEMAS[name].model_validate(content).model_dump(),
            context,
            evidence,
            analysis,
            sources,
            predecessors,
            cancel,
            deadline,
            repair_tests=False,
        )
        models.add(initial_model)
        metadata_prior = predecessors | {
            name: {
                "requirements": predecessors.get(name, {}).get("requirements", [])
                + fixed["requirements"]
            }
        }
        invalid_headers = {
            row["id"]
            for row in fixed["requirements"]
            if normative_header_issues(name, row, evidence, analysis, sources, metadata_prior)
        }
        criterion_input = fixed | {
            "requirements": [
                row for row in fixed["requirements"] if row["id"] not in invalid_headers
            ]
        }
        criterion_prior = predecessors | {
            name: {
                "requirements": predecessors.get(name, {}).get("requirements", [])
                + [row for row in fixed["requirements"] if row["id"] in invalid_headers]
            }
        }
        criterion_fixed, criterion_models, criterion_attempts = repair_canonical_acceptance(
            self.provider,
            name,
            criterion_input,
            evidence,
            analysis,
            sources,
            criterion_prior,
            cancel,
            deadline,
        )
        repaired_criteria = {
            row["id"]: row["acceptance_criteria"] for row in criterion_fixed["requirements"]
        }
        for row in fixed["requirements"]:
            if row["id"] in repaired_criteria:
                row["acceptance_criteria"] = repaired_criteria[row["id"]]
        models.update(criterion_models)
        attempts += criterion_attempts
        for index, original in enumerate(list(fixed["requirements"])):
            permission_statement = (
                source_permission_statement(
                    " ".join(item.quote for item in evidence if item.id in original["evidence_ids"])
                )
                or source_role_denial_statement(
                    " ".join(
                        item.quote for item in evidence if item.id in original["evidence_ids"]
                    ),
                    original["statement"],
                )
                if original["id"] in invalid_headers
                else None
            )
            frozen_statement = (
                capacity_repair_statement(
                    " ".join(
                        item.quote for item in evidence if item.id in original["evidence_ids"]
                    ),
                    original["statement"],
                )
                if original["id"] in invalid_headers
                else None
            )
            other = predecessors.get(name, {}).get("requirements", []) + [
                req for req in fixed["requirements"] if req["id"] != original["id"]
            ]
            previous = predecessors | {name: {"requirements": other}}

            def validate_one(
                candidate,
                prior=previous,
                required_id=original["id"],
                frozen=frozen_statement or permission_statement,
            ):
                normalized_row = Requirement.model_validate(
                    preserve_nonexclusive_tests(
                        preserve_retention_duration(candidate.model_dump(), evidence)[0], evidence
                    )
                )
                for field in (
                    "statement",
                    "rationale",
                    "acceptance_criteria",
                    "unresolved_decisions",
                ):
                    setattr(candidate, field, getattr(normalized_row, field))
                row = candidate.model_dump() | {"id": required_id}
                issues = validate_section(
                    name, {"requirements": [row]}, evidence, analysis, sources, prior
                )
                if frozen and row["statement"] != frozen:
                    issues.append("completion_must_preserve_source_statement")
                return [
                    issue
                    for issue in issues
                    if not issue.endswith(f":missing_{name}_coverage")
                    and not is_boundary_test_issue(issue)
                ]

            checked = Requirement.model_validate(original)
            feedback = validate_one(checked)
            if not feedback:
                fixed["requirements"][index] = checked.model_dump() | {"id": original["id"]}
                continue
            if frozen_statement:
                repaired_row, provenance = repair_source_capacity_criterion(
                    self.provider,
                    original,
                    frozen_statement,
                    evidence,
                    cancel,
                    deadline,
                    validate_one,
                )
                fixed["requirements"][index] = repaired_row
                models.update(provenance.get("output_models", [provenance["model"]]))
                attempts += provenance["attempts"]
                continue
            diagnostic = checked.model_copy(deep=True)
            diagnostic.rationale = (
                "The original source states this behavior; no added rationale is asserted."
            )
            if not validate_one(diagnostic):
                frozen_requirement = checked.model_dump()

                def validate_rationale(candidate, frozen=frozen_requirement):
                    """Validate the merge while keeping other fields unchanged."""
                    return validate_one(
                        Requirement.model_validate(frozen | {"rationale": candidate.rationale})
                    )

                repaired, provenance = self.provider.generate(
                    prompts.COMMON + "\nCorrect ONLY the rejected rationale using the "
                    "original source. It is the sole failing field. Preserve the requirement "
                    "and all acceptance criteria, which the server keeps unchanged. Do not "
                    "claim unnamed regulation compliance, extra controls or missing facts. "
                    "Return the rationale-only JSON schema.",
                    {
                        "evidence": [
                            item.model_dump()
                            for item in evidence
                            if item.id in original["evidence_ids"]
                        ],
                        "rejected_requirement": original,
                        "validation_feedback": feedback,
                    },
                    RequirementRationaleRepair,
                    cancel,
                    deadline,
                    validate_rationale,
                )
                fixed["requirements"][index] = checked.model_dump() | {
                    "rationale": repaired.rationale,
                    "id": original["id"],
                }
                models.add(provenance["model"])
                attempts += provenance["attempts"]
                continue
            repair_context = {
                "assigned_section": name,
                "task": "one_rejected_source_requirement",
                "repair_requirement_id": original["id"],
                "candidate_metadata": {
                    key: original[key]
                    for key in ("id", "priority", "dimensions", "evidence_ids", "sources")
                },
                "evidence": [
                    item.model_dump() for item in evidence if item.id in original["evidence_ids"]
                ],
                "validation_feedback": validate_one(Requirement.model_validate(original)),
                "allowed_prohibition_statements": [
                    statement
                    for item in evidence
                    if item.id in original["evidence_ids"]
                    for statement in verbatim_prohibition_statements(item.quote)
                ],
                "existing_requirements": [{"id": req["id"]} for req in requirements_from(previous)],
                "sources": [
                    source.model_dump()
                    for source in sources
                    if source.id in {c["chunk_id"] for c in original["sources"]}
                ],
                "scope_constraints": [
                    item.quote
                    for item in evidence
                    if item.quote in context.get("scope_constraints", [])
                ],
            }
            if original["id"] not in invalid_headers:
                repair_context["rejected_requirement"] = original
            if frozen_statement:
                repair_context["source_completion_statement"] = frozen_statement
            if permission_statement:
                repair_context["source_completion_statement"] = permission_statement
                repair_context["retry_from_source"] = True
            repaired, provenance = self.provider.generate(
                prompts.COMMON + "\nRepair ONE canonical Requirement object only. "
                "Re-author it from the original source, preserving metadata and valid scope. "
                "Existing IDs are an index, not additional source evidence. "
                "Use source_completion_statement exactly when supplied. Author a fresh "
                "source-only rationale, not an explanation of the rejected claim. A planned "
                "inventory is a design population, not a requirement to implement registration. "
                "Keep its source behavior and remove every unsupported addition identified in "
                "validation_feedback. Test the stated source load succeeding; leave behavior "
                "above an unqualified load unresolved. Registered population is not concurrency "
                "or a registration ceiling. Do not describe an unprovided upper bound in the "
                "title, rationale or tests. Return one requirement, not a section. "
                "Keep a bare stated "
                "duration bare: remove added minimum/maximum/at least/at most qualifiers. "
                "Do not add a response-time promise or additional logging scope. "
                "Put attempted test actions in WHEN and their visible results in THEN. "
                "For an unconditional exclusion, return ONLY the named prohibition: do not "
                "append manual procedures, actor authorizations or logging obligations absent "
                "from that source. Verify prohibited automation with captured before/after "
                "state in an authorized test environment; do not prescribe a new product log. "
                "Use the original source only; never infer a replacement implementation.",
                repair_context,
                Requirement,
                cancel,
                deadline,
                validate_one,
            )
            fixed["requirements"][index] = repaired.model_dump() | {"id": original["id"]}
            models.add(provenance["model"])
            attempts += provenance["attempts"]
        fixed, linked_models, linked_attempts = repair_linked_acceptance(
            self.provider, name, fixed, evidence, analysis, sources, predecessors, cancel, deadline
        )
        models.update(linked_models)
        attempts += linked_attempts
        fixed, completion_models, completion_attempts = complete_source_gaps(
            self.provider,
            name,
            fixed,
            context,
            evidence,
            analysis,
            sources,
            predecessors,
            cancel,
            deadline,
        )
        models.update(completion_models)
        attempts += completion_attempts
        issues = validate_section(name, fixed, evidence, analysis, sources, predecessors)
        issues = [issue for issue in issues if not issue.endswith(f":missing_{name}_coverage")]
        if issues:
            raise GenerationError("targeted_requirement_repair_failed:" + ";".join(issues))
        return SECTION_SCHEMAS[name].model_validate(fixed), {
            "model": " + ".join(sorted(models)) or self.provider.model_name,
            "output_models": sorted(models),
            "attempts": attempts,
            "targeted_requirement_repair": True,
            "requirement_repair_version": REQUIREMENT_REPAIR_VERSION,
        }

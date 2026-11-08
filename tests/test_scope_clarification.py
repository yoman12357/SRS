"""Sparse project goals need actual questions, and skips remain documented unknowns."""

from cybersrs.evidence import (
    build_evidence,
    has_concrete_product_behavior,
    preserve_skipped_decisions,
    validate_analysis,
)
from cybersrs.orchestrator import Orchestrator
from cybersrs.repository import Repository
from cybersrs.schemas import Answer, Question

from .conftest import DESCRIPTION, FakeKnowledge, FakeProvider, wait_run


def test_real_sparse_input_cannot_silently_have_zero_questions(analysis):
    """Reproduce the live alert-review project-name-only failure."""
    evidence = build_evidence("We need a security alert review system for our campus IT team.", [])
    draft = analysis.model_copy(deep=True)
    draft.assessments = draft.assessments[:1]
    draft.questions = []
    assert not has_concrete_product_behavior(evidence)
    assert "project_goal_without_concrete_behavior_needs_scope_clarification" in validate_analysis(
        draft, evidence
    )
    draft.questions = [
        Question(
            **{
                "id": "Q-1",
                "question": "Which alert review actions should campus IT staff perform?",
                "why_needed": "The requested review workflow is not specified.",
                "critical": True,
                "evidence_ids": ["E-001"],
            }
        )
    ]
    draft = type(analysis).model_validate(draft.model_dump())
    assert not validate_analysis(draft, evidence)


def test_concrete_simple_present_behavior_and_unsupported_domain_are_not_forced_into_interview(
    analysis,
):
    """Readiness is about missing behavior, not a sentence quota or mandatory modal wording."""
    assert has_concrete_product_behavior(
        build_evidence("Employees authenticate with MFA before accessing research services.", [])
    )
    draft = analysis.model_copy(deep=True)
    draft.supported = False
    draft.assessments = draft.assessments[:1]
    draft.questions = []
    assert not validate_analysis(draft, build_evidence("Write a novel about dragons.", []))


def test_skipped_scope_question_is_not_forced_back_into_the_interview(analysis):
    """An explicit unknown is preserved instead of requiring an invented answer."""
    draft = analysis.model_copy(deep=True)
    draft.assessments = draft.assessments[:1]
    draft.questions = []
    skipped = Answer(
        question_id="Q-1", question_text="Which alerts are in scope?", text="", skipped=True
    )
    assert not validate_analysis(
        draft, build_evidence("We need a security alert review system.", []), [skipped]
    )


def test_repeated_skipped_question_moves_to_unknowns_without_losing_new_questions(analysis):
    """Respect the explicit skip even when the model repeats the same question verbatim."""
    text = "Which alert sources are in scope?"
    repeat = Question(
        id="Q-1",
        question=text,
        why_needed="Alert sources are not specified.",
        critical=True,
        evidence_ids=["E-001"],
    )
    new = repeat.model_copy(update={"id": "Q-2", "question": "Which review actions are permitted?"})
    draft = analysis.model_copy(deep=True)
    draft.questions = [repeat, new]
    answer = Answer(question_id="Q-1", question_text=text, text="", skipped=True)
    result = preserve_skipped_decisions(draft, [answer])
    assert result.questions == [new]
    assert draft.questions == [repeat, new]
    assert "Unanswered stakeholder decision: " + text in result.unresolved_decisions
    assert preserve_skipped_decisions(result, [answer]) == result


def test_coordinator_projects_skipped_question_into_final_analysis(settings, analysis, sections):
    """Empty skipped answers cannot disappear from the document's unknown-decision register."""
    repo = Repository(settings.data_dir)
    project = repo.create_project("Synthetic skip", DESCRIPTION)
    skipped = Answer(
        question_id="Q-1",
        question_text="Which authentication method is approved?",
        text="",
        skipped=True,
    )
    repo.update_project(project["id"], answers=[skipped.model_dump()])
    coordinator = Orchestrator(settings, repo, FakeProvider(analysis, sections), FakeKnowledge())
    try:
        run = wait_run(repo, coordinator.start(project["id"], "analyse")["id"])
        assert run["status"] == "completed", run["error"]
        result = repo.get_project(project["id"])["analysis"]
        assert (
            "Unanswered stakeholder decision: " + skipped.question_text
            in result["unresolved_decisions"]
        )
        assert not repo.list_versions(project["id"])
    finally:
        coordinator.shutdown()

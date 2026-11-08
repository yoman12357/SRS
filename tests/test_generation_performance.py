"""Real-time transport, source batch and deadline regression checks; no live inference."""

import asyncio
import json
import threading
import time

import httpx
import pytest
from pydantic import ValidationError

from cybersrs.acceptance_grounding import (
    acceptance_logging_issues,
    acceptance_response_issues,
    preserve_source_outcome,
)
from cybersrs.compact_requirements import generate_compact_requirements
from cybersrs.evidence import build_evidence, normative_evidence_ids
from cybersrs.knowledge import KnowledgeBase
from cybersrs.provider import GenerationError, OllamaProvider
from cybersrs.schemas import ChatResponse
from cybersrs.semantics import missing_source_actions


def install_stream(monkeypatch, wire):
    """Route the async model transport to an inert byte stream, never real Ollama."""
    original = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: httpx.Response(200, stream=wire))
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kwargs: original(transport=transport, **kwargs)
    )


def test_stream_closes_at_complete_json_and_still_validates(settings, monkeypatch):
    """A complete object stops decoding; partial/prose output never becomes a valid draft."""
    consumed = []

    class Wire(httpx.AsyncByteStream):
        async def __aiter__(self):
            for text in ['{"answer":"A valid local answer.",', '"sources":[]}', "bad padding"]:
                consumed.append(text)
                yield (json.dumps({"response": text, "done": False}) + "\n").encode()

    install_stream(monkeypatch, Wire())
    result, meta = OllamaProvider(settings.model_copy(update={"ollama_stream": True})).generate(
        "fixed", {}, ChatResponse, threading.Event(), time.monotonic() + 5
    )
    assert result.answer == "A valid local answer."
    assert meta["done_reason"] == "complete_json"
    assert len(consumed) == 2


def test_stream_checks_deadline_between_tokens(settings, monkeypatch):
    """A model continuously sending tokens cannot hold the section indefinitely."""
    consumed = []

    class Wire(httpx.AsyncByteStream):
        async def __aiter__(self):
            for _ in range(100):
                await asyncio.sleep(0.005)
                consumed.append(1)
                yield b'{"response":" ","done":false}\n'

    install_stream(monkeypatch, Wire())
    provider = OllamaProvider(settings.model_copy(update={"ollama_stream": True}))
    with pytest.raises(GenerationError, match="generation_budget_exhausted"):
        provider._request({}, 5, threading.Event(), time.monotonic() + 0.04)
    assert len(consumed) < 20


def test_silent_socket_is_closed_at_wall_clock_deadline(settings, monkeypatch):
    """No new tokens are necessary for the shared section deadline to stop a blocked read."""
    closed = []

    class Wire(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield b'{"response":"{","done":false}\n'
            await asyncio.sleep(10)

        async def aclose(self):
            closed.append(True)

    install_stream(monkeypatch, Wire())
    provider = OllamaProvider(settings.model_copy(update={"ollama_stream": True}))
    started = time.monotonic()
    with pytest.raises(GenerationError, match="generation_budget_exhausted"):
        provider._request({}, 10, threading.Event(), started + 0.04)
    assert time.monotonic() - started < 0.5 and closed


def test_waiting_for_local_inference_obeys_the_same_budget(settings):
    """Another local call cannot consume an unbounded portion of the section timer."""
    provider = OllamaProvider(settings)
    provider.lock = threading.Lock()
    provider.lock.acquire()
    started = time.monotonic()
    try:
        with pytest.raises(GenerationError, match="generation_budget_exhausted"):
            with provider._inference_slot(threading.Event(), started + 0.04):
                pytest.fail("A held lock cannot be acquired")
        assert time.monotonic() - started < 0.5 and provider.lock.locked()
    finally:
        provider.lock.release()


def test_retrieval_lock_wait_respects_its_budget(settings, monkeypatch):
    """Optional retrieval can time out before model generation without touching Ollama."""

    class BusyLock:
        def acquire(self, *, timeout):
            assert timeout == 0.01
            return False

    monkeypatch.setattr("cybersrs.knowledge.LOCAL_INFERENCE_LOCK", BusyLock())
    with pytest.raises(GenerationError, match="retrieval_budget_exhausted"):
        KnowledgeBase(settings)._embed(["Synthetic retrieval check"], timeout_seconds=0.01)


def test_compact_batch_preserves_authored_tests_and_rejects_omissions(analysis):
    """The fast path validates the full source instead of dropping rows to meet a time target."""
    evidence = build_evidence(
        "Security operators review alerts. Only administrators can manage accounts.", []
    )
    test = {
        "given": "A security operator test identity and an alert are present",
        "when": "The security operator requests to review that alert",
        "then": "The alert review returns the requested alert",
        "method": "test",
        "observable_evidence": "Test capture of the alert review response",
    }

    class Provider:
        model_name = "synthetic-only"

        def generate(self, system, context, schema, cancel, deadline, validate=None):
            assert [item["id"] for item in context["evidence"]] == ["E-001"]
            with pytest.raises(ValidationError):
                schema()
            row = {
                "statement": "The system shall allow security operators to review alerts.",
                "tests": [test],
                "unresolved_decisions": [],
            }
            result = schema(**{"E-001": row})
            assert not validate(result)
            return result, {"model": self.model_name, "attempts": 1}

    result, _ = generate_compact_requirements(
        Provider(),
        "functional",
        evidence,
        analysis,
        [],
        {},
        threading.Event(),
        time.monotonic() + 5,
    )
    assert result["requirements"][0]["acceptance_criteria"] == [test]
    assert result["requirements"][0]["id"] == "FR-001"


def test_management_in_project_name_is_not_an_extra_action():
    """A system title must not force an unrelated generic management requirement."""
    assert "management" not in missing_source_actions(
        "Design a secure VPN and remote-access management system that allows off-campus access.",
        "The system shall allow off-campus access via secure VPN.",
    )
    assert "management" in missing_source_actions(
        "Network administrators manage VPN policies.", "The system shall allow VPN connections."
    )
    quality = build_evidence(
        "The solution should be secure, scalable, reliable, and support "
        "both university-managed and approved personal devices.",
        [],
    )
    assert normative_evidence_ids(quality) == {"E-001"}


def test_model_residency_releases_only_configured_sibling(settings, monkeypatch):
    """An idle base must not leave the requested adapter on CPU; unrelated models stay loaded."""
    sent = []
    monkeypatch.setattr(
        httpx,
        "get",
        lambda url, **kwargs: httpx.Response(
            200,
            json={
                "models": [
                    {"name": settings.base_model_name, "size": 100, "size_vram": 100},
                    {"name": settings.model_name, "size": 100, "size_vram": 0},
                    {"name": "unrelated-model", "size": 100, "size_vram": 0},
                ]
            },
            request=httpx.Request("GET", url),
        ),
    )

    def post(url, **kwargs):
        sent.append(kwargs["json"])
        return httpx.Response(200, json={}, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", post)
    provider = OllamaProvider(
        settings.model_copy(update={"ollama_stream": True, "ollama_exclusive_main_model": True})
    )
    provider._prepare_model(threading.Event(), time.monotonic() + 5)
    assert sent == [
        {"model": settings.base_model_name, "keep_alive": 0},
        {"model": settings.model_name, "keep_alive": 0},
    ]


@pytest.mark.parametrize(
    "rejected_outcome",
    ["The alert is returned immediately", "The alert is returned within 5 seconds"],
)
def test_outcome_repair_preserves_statement_preconditions_and_valid_tests(
    analysis, rejected_outcome
):
    """A timing assertion receives a source-only patch while valid test fields stay frozen."""
    evidence = build_evidence(
        "Security operators review alerts. Only administrators can manage accounts.", []
    )
    original = {
        "given": "An operator test identity and an alert are present",
        "when": "The operator requests to review the alert",
        "then": rejected_outcome,
        "method": "test",
        "observable_evidence": "Test capture of the alert response",
    }

    class Provider:
        model_name = "test-adapter"

        def generate(self, system, context, schema, cancel, deadline, validate=None):
            if "tests_to_repair" not in context:
                candidate = schema(
                    **{
                        "E-001": {
                            "statement": "The system shall allow security operators "
                            "to review alerts.",
                            "tests": [original],
                            "unresolved_decisions": [],
                        }
                    }
                )
                assert validate(candidate)
                raise GenerationError(
                    "section_validation_failed:timing",
                    attempts=2,
                    rejected_candidate=candidate.model_dump(),
                    rejected_model="test-base",
                )
            assert context["_continue_model"] == "test-base"
            assert "immediately" not in json.dumps(context["tests_to_repair"])
            assert "5 seconds" not in json.dumps(context["tests_to_repair"])
            candidate = schema(
                **{
                    "E-001_test_1": {
                        "then": "The requested alert is returned",
                        "observable_evidence": "Test capture of the returned alert",
                    }
                }
            )
            assert not validate(candidate)
            return candidate, {"model": "test-base", "attempts": 1}

    content, provenance = generate_compact_requirements(
        Provider(),
        "functional",
        evidence,
        analysis,
        [],
        {},
        threading.Event(),
        time.monotonic() + 5,
    )
    criterion = content["requirements"][0]["acceptance_criteria"][0]
    assert criterion["given"] == original["given"] and criterion["when"] == original["when"]
    assert criterion["then"] == "The requested alert is returned"
    assert provenance["attempts"] == 3 and provenance["base_repair_used"]


def test_normalization_preserves_authored_outcome_and_stated_logging():
    """Only unsupported modifiers/side effects are removed, never a stated logging duty."""
    criterion = {
        "given": "A test session is active",
        "when": "The administrator terminates it",
        "then": "The system immediately ends the session and logs the event",
        "method": "test",
        "observable_evidence": "Test capture of session state",
    }
    normalized = preserve_source_outcome("Administrators terminate suspicious sessions.", criterion)
    assert normalized["then"] == "The system ends the session."
    assert normalized["when"] == criterion["when"]
    source = "The system immediately terminates suspicious sessions and logs the event."
    assert preserve_source_outcome(source, criterion) == criterion
    assert acceptance_response_issues("Detect excessive session duration.", normalized)
    witness = {
        **criterion,
        "then": "Excessive session duration is detected",
        "observable_evidence": "Test capture of detection without product logging",
    }
    assert not acceptance_logging_issues("Detect excessive session duration.", witness)


def test_missing_review_and_extra_duration_are_repaired_without_losing_source_values(analysis):
    """A supplementary review test and source-bound quantity correction preserve valid siblings."""
    source = (
        "Security operators may review and acknowledge alerts but may not change access policies. "
        "The system must record administrator policy changes and retain audit records for 30 days."
    )
    evidence = build_evidence(source, [])
    target = analysis.model_copy(
        update={
            "assessments": [
                analysis.assessments[0].model_copy(update={"sections": ["security"]}),
                analysis.assessments[1].model_copy(update={"sections": ["security"]}),
            ]
        }
    )

    def criterion(given, when, then):
        return {
            "given": given,
            "when": when,
            "then": then,
            "method": "test",
            "observable_evidence": "Test capture of resulting state",
        }

    acknowledgement = criterion(
        "A security operator and an alert are present",
        "The security operator acknowledges the alert",
        "The alert is acknowledged",
    )
    denial = criterion(
        "A security operator and access policy are present",
        "The security operator attempts to change the access policy",
        "The policy change is denied and the policy remains unchanged",
    )
    retained = criterion(
        "An administrator policy change record exists",
        "The record is retrieved after 30 days",
        "The audit record remains stored and accessible for 30 days",
    )
    invented = criterion(
        "An administrator policy change record is 45 days old",
        "The record is retrieved for inspection",
        "The audit record is returned for inspection",
    )
    review = criterion(
        "A security operator and an alert are present",
        "The security operator reviews the alert",
        "The requested alert details are returned",
    )

    class Provider:
        model_name = "test-adapter"

        def generate(self, system, context, schema, cancel, deadline, validate=None):
            if "tests_to_repair" not in context:
                candidate = schema(
                    **{
                        "E-001": {
                            "statement": evidence[0].quote,
                            "tests": [acknowledgement, denial],
                            "unresolved_decisions": [],
                        },
                        "E-002": {
                            "statement": evidence[1].quote,
                            "tests": [retained, invented],
                            "unresolved_decisions": [],
                        },
                    }
                )
                assert validate(candidate)
                raise GenerationError(
                    "section_validation_failed:source_tests",
                    attempts=2,
                    rejected_model="test-base",
                    rejected_candidate=candidate.model_dump(),
                )
            patch = context["tests_to_repair"]["E-002_test_2"]
            assert patch["confirmed_source_quantities"] == ["30 days"]
            assert "45 days" not in json.dumps(context)
            candidate = schema(
                **{
                    "E-002_test_2": {
                        "given": "An audit record is 30 days old",
                        "then": "The audit record remains stored and accessible",
                        "observable_evidence": "Test capture of the retained record",
                    },
                    "E-001_gap_1": review,
                }
            )
            assert not validate(candidate)
            return candidate, {"model": "test-base", "attempts": 1}

    content, _ = generate_compact_requirements(
        Provider(), "security", evidence, target, [], {}, threading.Event(), time.monotonic() + 5
    )
    assert content["requirements"][0]["acceptance_criteria"] == [acknowledgement, denial, review]
    assert content["requirements"][1]["acceptance_criteria"][0] == retained

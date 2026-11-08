"""Corrective calls retain earlier constraints without promoting rejected text into instructions."""

import json
import threading
import time

import httpx
import pytest

from cybersrs.provider import GenerationError, OllamaProvider, RepairingOllamaProvider
from cybersrs.schemas import ChatResponse


def _response(answer):
    return httpx.Response(
        200,
        request=httpx.Request("POST", "http://127.0.0.1/api/generate"),
        json={"response": json.dumps({"answer": answer, "sources": []})},
    )


def test_three_attempts_keep_both_prior_diagnostics_and_the_last_typed_candidate(
    settings, monkeypatch
):
    """Later corrections must not discard earlier iteration constraints."""
    sent = []
    answers = ["First CANDIDATE_PRIVATE_MARKER", "Second corrected candidate", "Final candidate"]

    def post(url, **kwargs):
        sent.append(kwargs["json"])
        return _response(answers[len(sent) - 1])

    monkeypatch.setattr(httpx, "post", post)

    def validate(_):
        return (
            ["unsupported_response_time_commitment"]
            if len(sent) == 1
            else ["unconfirmed_actor_exclusivity"]
            if len(sent) == 2
            else []
        )

    _, provenance = OllamaProvider(settings).generate(
        "Trusted instruction",
        {"question": "Original source"},
        ChatResponse,
        threading.Event(),
        time.monotonic() + 10,
        validate,
    )
    last = json.loads(sent[2]["prompt"])
    assert last["corrective_feedback"] == [
        "unsupported_response_time_commitment",
        "unconfirmed_actor_exclusivity",
    ]
    assert last["previous_candidate"]["answer"] == answers[1]
    assert "Remove unrequested timing promises" in sent[2]["system"]
    assert "Do not infer 'only administrators'" in sent[2]["system"]
    assert all("CANDIDATE_PRIVATE_MARKER" not in wire["system"] for wire in sent)
    assert provenance["attempts"] == 3


def test_typed_rejection_is_private_and_is_supplied_to_base_correction(settings, monkeypatch):
    """The same rejected object reaches the correction model without entering public errors."""
    sent = []

    def post(url, **kwargs):
        wire = kwargs["json"]
        sent.append(wire)
        return _response("Rejected CANDIDATE_MARKER" if len(sent) == 1 else "Corrected answer")

    monkeypatch.setattr(httpx, "post", post)
    _, provenance = RepairingOllamaProvider(settings).generate(
        "Trusted instruction",
        {"question": "Original source"},
        ChatResponse,
        threading.Event(),
        time.monotonic() + 10,
        lambda value: (
            ["unsupported_response_time_commitment"] if value.answer.startswith("Rejected") else []
        ),
    )
    assert (
        json.loads(sent[1]["prompt"])["previous_candidate"]["answer"] == "Rejected CANDIDATE_MARKER"
    )
    assert "CANDIDATE_MARKER" not in sent[1]["system"]
    assert provenance["base_repair_used"]
    sent.clear()
    with pytest.raises(GenerationError) as exc:
        OllamaProvider(settings.model_copy(update={"llm_max_retries": 0})).generate(
            "Trusted instruction",
            {},
            ChatResponse,
            threading.Event(),
            time.monotonic() + 10,
            lambda _: ["unsupported_response_time_commitment"],
        )
    assert exc.value.rejected_candidate["answer"] == "Rejected CANDIDATE_MARKER"
    assert "CANDIDATE_MARKER" not in str(exc.value)
    assert exc.value.rejected_model == settings.model_name
    assert exc.value.attempts == 1


def test_source_only_retry_keeps_diagnostics_without_copying_rejected_behavior(
    settings, monkeypatch
):
    """A fresh source repair must not anchor base or its retries to a bad primary example."""
    sent = []

    def post(url, **kwargs):
        sent.append(kwargs["json"])
        return _response("Bad candidate" if len(sent) < 3 else "Corrected answer")

    monkeypatch.setattr(httpx, "post", post)
    _, provenance = RepairingOllamaProvider(settings).generate(
        "Trusted instruction",
        {"question": "Original source", "retry_from_source": True},
        ChatResponse,
        threading.Event(),
        time.monotonic() + 10,
        lambda value: (
            ["planning_inventory_requires_design_inspection"]
            if value.answer.startswith("Bad")
            else []
        ),
    )
    assert len(sent) == 3 and provenance["base_repair_used"]
    assert all("previous_candidate" not in json.loads(wire["prompt"]) for wire in sent)
    assert (
        "planning_inventory_requires_design_inspection"
        in json.loads(sent[2]["prompt"])["corrective_feedback"]
    )
    assert "inspection/review/comparison" in sent[1]["system"]


def test_exhausted_primary_and_base_keep_private_author_and_total_call_count(settings, monkeypatch):
    """Field recovery must not hide failed primary calls or relabel a base-authored candidate."""
    sent = []

    def post(url, **kwargs):
        sent.append(kwargs["json"]["model"])
        return _response("PRIVATE_REJECTED_MARKER")

    monkeypatch.setattr(httpx, "post", post)
    settings = settings.model_copy(update={"llm_max_retries": 1, "adapter_max_retries": 0})
    with pytest.raises(GenerationError) as error:
        RepairingOllamaProvider(settings).generate(
            "Trusted task",
            {},
            ChatResponse,
            threading.Event(),
            time.monotonic() + 10,
            lambda _: ["unsupported_response_time_commitment"],
        )
    assert sent == [settings.model_name, settings.base_model_name, settings.base_model_name]
    assert error.value.attempts == len(sent)
    assert error.value.rejected_model == settings.base_model_name
    assert "PRIVATE_REJECTED_MARKER" not in str(error.value)


def test_auxiliary_candidate_can_be_omitted_but_authoritative_source_is_never_truncated(
    settings, monkeypatch
):
    """Budget handling drops a complete optional correction object and records that omission."""
    sent, events = [], []

    def post(url, **kwargs):
        sent.append(kwargs["json"])
        return _response("An observable answer")

    def event(kind, payload):
        events.append((kind, payload))
        return "synthetic-audit-id"

    monkeypatch.setattr(httpx, "post", post)
    monkeypatch.setattr("cybersrs.provider.record_model_event", event)
    provider = OllamaProvider(settings.model_copy(update={"ollama_num_ctx": 2048}))
    provider.generate(
        "Trusted instruction",
        {
            "question": "Original authoritative question",
            "previous_candidate": {"answer": "x" * 20000, "sources": []},
        },
        ChatResponse,
        threading.Event(),
        time.monotonic() + 10,
    )
    prompt = json.loads(sent[0]["prompt"])
    assert prompt["question"] == "Original authoritative question"
    assert "previous_candidate" not in prompt
    assert any(kind == "corrective_context_omitted" for kind, _ in events)
    before = len(sent)
    with pytest.raises(GenerationError, match="context_budget_exceeded"):
        provider.generate(
            "Trusted instruction",
            {"question": "q" * 20000},
            ChatResponse,
            threading.Event(),
            time.monotonic() + 10,
        )
    assert len(sent) == before


def test_restored_private_candidate_is_masked_again_on_a_corrective_request(settings, monkeypatch):
    """The new previous-candidate field cannot bypass inference privacy masking."""
    sent = []
    address = "private-fixture@example.invalid"

    def post(url, **kwargs):
        wire = kwargs["json"]
        sent.append(wire)
        prompt = json.loads(wire["prompt"])
        return _response(prompt["question"])

    monkeypatch.setattr(httpx, "post", post)
    result, _ = OllamaProvider(settings).generate(
        "Trusted instruction",
        {"question": address},
        ChatResponse,
        threading.Event(),
        time.monotonic() + 10,
        lambda _: ["unsupported_response_time_commitment"] if len(sent) == 1 else [],
    )
    assert result.answer == address
    assert all(address not in json.dumps(wire) for wire in sent)
    assert json.loads(sent[1]["prompt"])["previous_candidate"]["answer"] != address

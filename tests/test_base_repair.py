"""Adapter-first correction stays local and reports the actual output author."""

import threading
import time

import httpx
import pytest

from cybersrs.provider import CancelledError, GenerationError, RepairingOllamaProvider
from cybersrs.schemas import ChatResponse


def test_validated_base_correction_reports_actual_model(settings, monkeypatch) -> None:
    """An invalid adapter response may be corrected, without being attributed to the adapter."""
    settings = settings.model_copy(update={"llm_max_retries": 0})
    requested = []

    def post(url, **kwargs):
        model = kwargs["json"]["model"]
        requested.append(model)
        answer = (
            "supported response" if model == settings.base_model_name else "unsupported response"
        )
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "response": ChatResponse(answer=answer, sources=[]).model_dump_json(),
                "done_reason": "stop",
            },
        )

    monkeypatch.setattr(httpx, "post", post)
    result, provenance = RepairingOllamaProvider(settings).generate(
        "fixed system",
        {},
        ChatResponse,
        threading.Event(),
        time.monotonic() + 10,
        lambda value: [] if value.answer == "supported response" else ["unsupported_claim"],
    )
    assert requested == [settings.model_name, settings.base_model_name]
    assert result.answer == "supported response"
    assert provenance["model"] == settings.base_model_name
    assert provenance["requested_model"] == settings.model_name
    assert provenance["base_repair_used"] is True
    assert provenance["attempts"] == 2
    assert provenance["primary_attempts"] == 1 and provenance["correction_attempts"] == 1
    assert "unsupported_claim" in provenance["primary_failure_code"]


def test_missing_adapter_is_not_silently_substituted(settings, monkeypatch) -> None:
    """Transport/readiness errors remain visible rather than silently choosing another model."""
    requested = []

    def post(url, **kwargs):
        requested.append(kwargs["json"]["model"])
        return httpx.Response(404, request=httpx.Request("POST", url), json={"error": "missing"})

    monkeypatch.setattr(httpx, "post", post)
    with pytest.raises(GenerationError, match="local_model_unavailable"):
        RepairingOllamaProvider(settings).generate(
            "fixed system",
            {},
            ChatResponse,
            threading.Event(),
            time.monotonic() + 10,
        )
    assert requested == [settings.model_name]


def test_observed_native_format_failure_uses_bounded_correction(settings, monkeypatch):
    """A confirmed decoder rejection is not misreported as an unavailable local model."""
    requested = []

    def post(url, **kwargs):
        model = kwargs["json"]["model"]
        requested.append(model)
        if model == settings.model_name:
            return httpx.Response(
                500,
                request=httpx.Request("POST", url),
                json={
                    "error": "llama-server chat error: map[code:500 message:The model produced "
                    "output that does not match the expected peg-native format type:server_error]",
                },
            )
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "response": ChatResponse(
                    answer="A validated local response.", sources=[]
                ).model_dump_json(),
                "done_reason": "stop",
            },
        )

    monkeypatch.setattr(httpx, "post", post)
    result, provenance = RepairingOllamaProvider(settings).generate(
        "fixed system",
        {},
        ChatResponse,
        threading.Event(),
        time.monotonic() + 10,
    )
    assert requested == [settings.model_name, settings.base_model_name]
    assert result.answer == "A validated local response."
    assert provenance["attempts"] == 2
    assert "model_output_native_format_invalid" in provenance["primary_failure_code"]


@pytest.mark.parametrize("error", ["model runner has unexpectedly stopped", "out of memory"])
def test_other_runtime_500_errors_remain_visible(settings, monkeypatch, error):
    """Availability/resource failures must not be silently treated as schema rejection."""
    requested = []

    def post(url, **kwargs):
        requested.append(kwargs["json"]["model"])
        return httpx.Response(500, request=httpx.Request("POST", url), json={"error": error})

    monkeypatch.setattr(httpx, "post", post)
    with pytest.raises(GenerationError, match="local_model_unavailable"):
        RepairingOllamaProvider(settings).generate(
            "fixed system",
            {},
            ChatResponse,
            threading.Event(),
            time.monotonic() + 10,
        )
    assert requested == [settings.model_name]


def test_cancellation_after_http_failure_takes_priority_over_correction(settings, monkeypatch):
    """A cancellation arriving during inference cannot start another model attempt."""
    cancel = threading.Event()
    called = []

    def post(url, **kwargs):
        called.append(url)
        cancel.set()
        return httpx.Response(
            500,
            request=httpx.Request("POST", url),
            json={
                "error": "The model produced output that does not match the expected "
                "peg-native format",
            },
        )

    monkeypatch.setattr(httpx, "post", post)
    with pytest.raises(CancelledError):
        RepairingOllamaProvider(settings).generate(
            "fixed", {}, ChatResponse, cancel, time.monotonic() + 10
        )
    assert len(called) == 1


def test_observed_token_repeat_abort_is_rejected_output_not_unavailable_model(
    settings, monkeypatch
):
    """The real generate-endpoint repetition diagnostic consumes bounded output correction."""
    requested = []

    def post(url, **kwargs):
        model = kwargs["json"]["model"]
        requested.append(model)
        if model == settings.model_name:
            return httpx.Response(
                500,
                request=httpx.Request("POST", url),
                json={"error": "prediction aborted, token repeat limit reached"},
            )
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "response": ChatResponse(
                    answer="Corrected local answer.", sources=[]
                ).model_dump_json()
            },
        )

    monkeypatch.setattr(httpx, "post", post)
    result, provenance = RepairingOllamaProvider(settings).generate(
        "fixed", {}, ChatResponse, threading.Event(), time.monotonic() + 10
    )
    assert result.answer == "Corrected local answer."
    assert requested == [settings.model_name, settings.base_model_name]
    assert "model_output_repetition_limit" in provenance["primary_failure_code"]

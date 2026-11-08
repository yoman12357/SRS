"""Verify the release download preserves model bytes before the import."""

import hashlib
from contextlib import contextmanager

import httpx
import pytest

from scripts import install_models


@pytest.mark.parametrize("fallback", [False, True])
def test_model_part_falls_back_and_verifies_hash(tmp_path, monkeypatch, fallback):
    """Use the API when a direct response is corrupt and cache only verified bytes."""
    content = b"GGUF demo fixture"
    url = "https://api.github.com/repos/example/repo/releases/assets/123?download=1"
    browser_url = "https://github.com/example/repo/releases/download/v1/model.gguf.part01"
    asset = {
        "name": "model.gguf.part01",
        "size": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "url": url,
        "browser_url": browser_url,
    }
    calls = []

    @contextmanager
    def stream(method, request_url, **kwargs):
        assert method == "GET"
        assert kwargs["follow_redirects"] is True
        assert request_url == (url if calls else browser_url)
        assert kwargs["headers"] == ({"Accept": "application/octet-stream"} if calls else {})
        body = b"incorrect bytes" if fallback and not calls else content
        calls.append(body)
        yield httpx.Response(200, content=body, request=httpx.Request(method, request_url))

    monkeypatch.setattr(install_models.httpx, "stream", stream)
    monkeypatch.delenv("CYBERSRS_MODEL_GITHUB_TOKEN", raising=False)
    result = install_models._download_part(tmp_path, asset)
    assert result.read_bytes() == content
    assert len(calls) == 1 + fallback
    assert install_models._download_part(tmp_path, asset) == result
    assert len(calls) == 1 + fallback
    assert list(tmp_path.iterdir()) == [result]

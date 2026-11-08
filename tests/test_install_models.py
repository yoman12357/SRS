"""Verify the release download preserves model bytes before the import."""

import hashlib
from contextlib import contextmanager

import httpx
import pytest

from scripts import install_models


@pytest.mark.parametrize("damaged_first", [False, True])
def test_model_part_uses_public_asset_api_and_verifies_hash(tmp_path, monkeypatch, damaged_first):
    """Retry a wrong response and keep only a verified part in the cache."""
    content = b"GGUF demo fixture"
    url = "https://api.github.com/repos/example/repo/releases/assets/123?download=1"
    asset = {
        "name": "model.gguf.part01",
        "size": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "url": url,
    }
    calls = []

    @contextmanager
    def stream(method, request_url, **kwargs):
        assert method == "GET" and request_url == url
        assert kwargs["headers"] == {"Accept": "application/octet-stream"}
        assert kwargs["follow_redirects"] is True
        body = b"incorrect bytes" if damaged_first and not calls else content
        calls.append(body)
        yield httpx.Response(200, content=body, request=httpx.Request(method, request_url))

    monkeypatch.setattr(install_models.httpx, "stream", stream)
    result = install_models._download_part(tmp_path, asset)
    assert result.read_bytes() == content
    assert len(calls) == 1 + damaged_first
    assert install_models._download_part(tmp_path, asset) == result
    assert len(calls) == 1 + damaged_first
    assert list(tmp_path.iterdir()) == [result]

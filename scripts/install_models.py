"""Install the configured local Ollama models during CyberSRS setup."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import httpx

from cybersrs.config import Settings

ROOT = Path(__file__).resolve().parents[1]
BUFFER_SIZE = 4 * 1024 * 1024


def _tag(name: str) -> str:
    return name if ":" in name.rsplit("/", 1)[-1] else f"{name}:latest"


def _matches(path: Path, asset: dict) -> bool:
    if not path.is_file() or path.stat().st_size != asset["size"]:
        return False
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() == asset["sha256"]


def _download_part(cache: Path, asset: dict) -> Path:
    destination = cache / asset["name"]
    if _matches(destination, asset):
        return destination
    temporary = destination.with_suffix(destination.suffix + ".download")
    for attempt in range(1, 4):
        print(f"Downloading {asset['name']} (attempt {attempt}/3)", flush=True)
        try:
            with (
                httpx.stream(
                    "GET", asset["url"],
                    headers={"Accept": "application/octet-stream"},
                    follow_redirects=True, timeout=60,
                ) as response,
                temporary.open("wb") as stream,
            ):
                response.raise_for_status()
                for block in response.iter_bytes(chunk_size=BUFFER_SIZE):
                    stream.write(block)
            if not _matches(temporary, asset):
                raise ValueError("Release asset failed SHA-256 or size verification")
            temporary.replace(destination)
            return destination
        except (httpx.HTTPError, OSError, ValueError):
            temporary.unlink(missing_ok=True)
            if attempt == 3:
                raise
    raise RuntimeError("Model download did not complete")


def _import_model(settings: Settings, manifest: dict, env: dict[str, str]) -> None:
    cache = settings.data_dir.resolve() / "model-setup"
    cache.mkdir(parents=True, exist_ok=True)
    weights = cache / manifest["filename"]
    if not _matches(weights, manifest):
        parts = [_download_part(cache, asset) for asset in manifest["parts"]]
        temporary = weights.with_suffix(".download")
        try:
            with temporary.open("wb") as output:
                for part in parts:
                    with part.open("rb") as input_file:
                        shutil.copyfileobj(input_file, output, BUFFER_SIZE)
            if not _matches(temporary, manifest):
                raise ValueError("Assembled GGUF did not match the verified local model")
            temporary.replace(weights)
        finally:
            temporary.unlink(missing_ok=True)
    modelfile = cache / "Modelfile"
    shutil.copyfile(ROOT / "models" / "CyberSRS.Modelfile", modelfile)
    subprocess.run(
        ["ollama", "create", manifest["model"], "-f", str(modelfile)],
        cwd=cache,
        env=env,
        check=True,
    )
    for path in [weights, modelfile, *(cache / part["name"] for part in manifest["parts"])]:
        path.unlink(missing_ok=True)


def install_models(settings: Settings) -> None:
    """Install missing models and keep any already configured local models."""
    env = os.environ | {"OLLAMA_HOST": settings.ollama_base_url}
    try:
        response = httpx.get(
            f"{settings.ollama_base_url}/api/tags", follow_redirects=False, timeout=8
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise RuntimeError("Open Ollama, then run setup.ps1 again") from error
    installed = {_tag(model["name"]) for model in response.json()["models"]}
    manifest = json.loads((ROOT / "models" / "runtime-model.json").read_text("utf-8"))
    main_tag = _tag(settings.model_name)
    if main_tag not in installed:
        if main_tag == manifest["model"]:
            _import_model(settings, manifest, env)
        elif main_tag != _tag(settings.base_model_name):
            raise ValueError(f"Install the custom Ollama model {settings.model_name} first")
    for name in dict.fromkeys(map(_tag, (settings.base_model_name, settings.embedding_model))):
        if name not in installed:
            subprocess.run(["ollama", "pull", name], env=env, check=True)


if __name__ == "__main__":
    install_models(Settings())

"""Environment-backed application configuration and loopback enforcement."""

from pathlib import Path
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Read all deployment choices from CYBERSRS_ variables or a local .env."""

    model_config = SettingsConfigDict(env_prefix="CYBERSRS_", env_file=".env", extra="ignore")
    data_dir: Path = Path("data")
    knowledge_dir: Path = Path("knowledge")
    frontend_dir: Path = Path("frontend/dist")
    ollama_base_url: str
    model_name: str
    base_model_name: str
    embedding_model: str
    ollama_timeout_seconds: float = Field(default=600, gt=0)
    ollama_num_ctx: int = Field(default=12288, ge=2048)
    ollama_num_predict: int = Field(default=4000, ge=256)
    llm_max_retries: int = Field(default=2, ge=0, le=5)
    base_repair_enabled: bool = True
    adapter_max_retries: int = Field(default=0, ge=0, le=5)
    generation_timeout_seconds: float = Field(default=3600, gt=0)
    section_timeout_seconds: float = Field(default=60, gt=0)
    compact_requirements_enabled: bool = False
    ollama_stream: bool = True
    ollama_raw_chatml: bool = False
    ollama_exclusive_main_model: bool = True
    rag_top_k: int = Field(default=4, ge=1, le=12)
    rag_min_score: float = Field(default=0.35, ge=0, le=1)
    rag_enabled: bool = True
    backend_port: int = Field(default=8010, ge=1024, le=65535)
    frontend_port: int = Field(default=5175, ge=1024, le=65535)
    max_upload_bytes: int = Field(default=10485760, ge=1024)

    @field_validator("ollama_base_url")
    @classmethod
    def local_endpoint(cls, value: str) -> str:
        """Prevent credentials, redirects or remote inference configuration."""
        parsed = urlsplit(value)
        if (
            parsed.scheme != "http"
            or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise ValueError("Ollama must use a credential-free loopback HTTP URL")
        return value.rstrip("/")

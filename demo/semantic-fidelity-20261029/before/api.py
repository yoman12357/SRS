"""Local HTTP interface for projects, sequential agents, reviews and exports."""

from __future__ import annotations

import base64
import hashlib
import json
import threading
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import Field

from . import prompts
from .audit import audit_scope
from .config import Settings
from .exports import render_markdown, render_pdf
from .knowledge import KnowledgeBase, extract_text, source_digest
from .orchestrator import Orchestrator
from .provider import GenerationError, LLMProvider, OllamaProvider, RepairingOllamaProvider
from .repository import Repository
from .schemas import (
    REQUIREMENT_PREFIXES,
    SECTION_SCHEMAS,
    Answer,
    ChatResponse,
    Document,
    StrictModel,
)
from .srs_presentation import build_srs_presentation
from .validation import validate_document


class ProjectInput(StrictModel):
    """User-authored project name and informal description."""

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=20, max_length=30000)


class AnswerInput(StrictModel):
    """One clarification round; previous answers are preserved by question ID."""

    answers: list[Answer]


class EditInput(StrictModel):
    """Exact section revision with optimistic content-hash concurrency check."""

    content: dict
    expected_content_hash: str
    editor: Literal["human", "assistant"] = "human"
    dependent_edits: dict[str, dict] = Field(default_factory=dict)


class RetryInput(StrictModel):
    """Source-hash-bound reviewed corrections for a terminated generation run."""

    section_edits: dict[str, dict] = Field(default_factory=dict)
    expected_input_hash: str = ""
    editor: Literal["human", "assistant"] = "human"


class ReviewInput(StrictModel):
    """Explicit human decision; generation is never an approval."""

    decision: Literal["approve", "reject", "request_changes"]
    reviewer: str = Field(min_length=1, max_length=200)
    comment: str = Field(max_length=12000)
    content_hash: str


class ChatInput(StrictModel):
    """Cybersecurity question with an optional project-scoped reference context."""

    message: str = Field(min_length=1, max_length=12000)
    project_id: str | None = None


def create_app(
    settings: Settings | None = None,
    provider: LLMProvider | None = None,
    knowledge: KnowledgeBase | None = None,
) -> FastAPI:
    """Build an independent local application; inject test doubles only in tests."""
    settings = settings or Settings()
    repository = Repository(settings.data_dir)
    provider = provider or RepairingOllamaProvider(settings)
    chat_provider = (
        OllamaProvider(settings, settings.base_model_name)
        if isinstance(
            provider,
            OllamaProvider,
        )
        else provider
    )
    knowledge = knowledge or KnowledgeBase(settings)
    coordinator = Orchestrator(settings, repository, provider, knowledge)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Recover interrupted work and release worker resources on local shutdown."""
        repository.interrupt_stale_runs()
        yield
        coordinator.shutdown()

    app = FastAPI(title="CyberSRS Sequential Agents", lifespan=lifespan)
    app.state.repository = repository
    app.state.coordinator = coordinator
    app.state.settings = settings
    app.state.knowledge = knowledge
    origins = [
        f"http://{host}:{port}"
        for host in ("localhost", "127.0.0.1")
        for port in (settings.frontend_port, settings.backend_port)
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def local_boundary(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Bound bodies, reject cross-origin mutation and suppress unsafe caching."""
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            if origin and origin not in origins:
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": {
                            "code": "origin_rejected",
                            "message": "Use the local application origin",
                        }
                    },
                )
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > settings.max_upload_bytes + 1048576:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": {
                                "code": "request_too_large",
                                "message": "Local request limit exceeded",
                            }
                        },
                    )
            request._body = bytes(body)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.exception_handler(KeyError)
    async def missing(request: Request, exc: KeyError) -> JSONResponse:
        """Expose safe not-found codes without database or user details."""
        return JSONResponse(
            status_code=404,
            content={
                "detail": {
                    "code": "not_found",
                    "message": "Requested local record was not found",
                }
            },
        )

    @app.exception_handler(ValueError)
    async def invalid(request: Request, exc: ValueError) -> JSONResponse:
        """Keep validation diagnostics free of raw stakeholder/model text."""
        return JSONResponse(
            status_code=409,
            content={
                "detail": {
                    "code": "invalid_state",
                    "message": "The request conflicts with current project state",
                }
            },
        )

    @app.exception_handler(GenerationError)
    async def generation_failure(request: Request, exc: GenerationError) -> JSONResponse:
        """Return a retryable local-model failure without leaking prompts."""
        return JSONResponse(
            status_code=503,
            content={
                "detail": {
                    "code": "local_inference_failed",
                    "message": "Local inference failed; check runtime",
                }
            },
        )

    prefix = "/api/v1"

    def validated_version(project_id: str, version_id: str) -> dict:
        """Recheck immutable content under current rules without rewriting its hash or history."""
        selected = repository.get_version(project_id, version_id)
        selected["quality"] = validate_document(
            Document.model_validate(selected["content"])
        ).model_dump()
        selected["presentation"] = build_srs_presentation(
            Document.model_validate(selected["content"])
        ).model_dump()
        return selected

    @app.get(prefix + "/health")
    def health() -> dict:
        """Report local model and index readiness with no generation side effects."""
        readiness = (
            provider.readiness() if isinstance(provider, OllamaProvider) else {"ready": True}
        )
        try:
            counts = knowledge.counts()
        except Exception:
            counts = {"global": 0, "private": 0, "unavailable": True}
        return {
            "status": "ready" if readiness["ready"] else "model_unavailable",
            "model": readiness,
            "knowledge": counts,
            "architecture": "sequential-section-agents",
        }

    @app.get(prefix + "/projects")
    def list_projects() -> list[dict]:
        """List resumable local projects."""
        return repository.list_projects()

    @app.post(prefix + "/projects", status_code=201)
    def create_project(body: ProjectInput) -> dict:
        """Create a project without silently launching generation."""
        return repository.create_project(body.name, body.description)

    @app.get(prefix + "/projects/{project_id}")
    def get_project(project_id: str) -> dict:
        """Restore original input, answers and validated analysis."""
        return repository.get_project(project_id)

    @app.get(prefix + "/projects/{project_id}/audit")
    def export_audit(project_id: str) -> Response:
        """Explicitly download private project history separately from regular UI data."""
        payload = {
            "audit_format": "1",
            "project_id": project_id,
            "history_limitations": "Only events recorded after audit support was installed "
            "are present; historical prompts are not reconstructed.",
            "events": repository.list_audit(project_id),
        }
        return Response(
            json.dumps(payload, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="CyberSRS-audit-{project_id}.json"'
            },
        )

    @app.patch(prefix + "/projects/{project_id}")
    def update_project(project_id: str, body: ProjectInput) -> dict:
        """Revise source input and invalidate its old analysis."""
        return repository.update_project(project_id, name=body.name, description=body.description)

    @app.delete(prefix + "/projects/{project_id}", status_code=204)
    def delete_project(project_id: str) -> Response:
        """Cancel live work and remove relational/private vector data."""
        for run_id in list(coordinator.cancels):
            if repository.get_run(run_id)["project_id"] == project_id:
                coordinator.cancel(run_id)
        knowledge.delete_private(project_id)
        repository.delete_project(project_id)
        return Response(status_code=204)

    @app.post(prefix + "/projects/{project_id}/analyse", status_code=202)
    def analyse(project_id: str) -> dict:
        """Dispatch adaptive analysis with pollable agent progress."""
        return coordinator.start(project_id, "analyse")

    @app.post(prefix + "/projects/{project_id}/answers", status_code=202)
    def answer(project_id: str, body: AnswerInput) -> dict:
        """Preserve original responses and rerun adaptive analysis."""
        project = repository.get_project(project_id)
        known = {q["id"] for q in (project["analysis"] or {}).get("questions", [])}
        if any(item.question_id not in known for item in body.answers):
            raise ValueError("unknown_question")
        merged = {a["question_id"]: a for a in project["answers"]}
        for item in body.answers:
            item.question_text = next(
                q["question"]
                for q in project["analysis"]["questions"]
                if q["id"] == item.question_id
            )
            merged[item.question_id] = item.model_dump()
        repository.update_project(project_id, answers=list(merged.values()))
        return coordinator.start(project_id, "analyse")

    @app.post(prefix + "/projects/{project_id}/generate", status_code=202)
    def generate(project_id: str) -> dict:
        """Start the sequential SRS/SDLC agents using analysed source input."""
        return coordinator.start(project_id)

    @app.get(prefix + "/runs/{run_id}")
    def run_detail(run_id: str) -> dict:
        """Return persisted progress, validated checkpoints and safe failure codes."""
        run = repository.get_run(run_id)
        run["checkpoints"] = {
            key: value for key, value in run["checkpoints"].items() if not key.startswith("_")
        }
        return run

    @app.get(prefix + "/projects/{project_id}/runs")
    def project_runs(project_id: str) -> list[dict]:
        """Restore active and recent workflow summaries after navigation or reload."""
        return repository.list_runs(project_id)

    @app.post(prefix + "/runs/{run_id}/cancel")
    def cancel(run_id: str) -> dict:
        """Signal cooperative cancellation while preserving previous versions."""
        return coordinator.cancel(run_id)

    @app.post(prefix + "/runs/{run_id}/retry", status_code=202)
    def retry(run_id: str, body: RetryInput | None = None) -> dict:
        """Revalidate and reuse completed sections before retrying failed agent work."""
        if body and body.section_edits:
            old = repository.get_run(run_id)
            if body.expected_input_hash != old["input_hash"]:
                raise ValueError("stale_checkpoint_edit")
            return coordinator.retry(run_id, body.section_edits, body.editor)
        return coordinator.retry(run_id)

    @app.get(prefix + "/projects/{project_id}/versions")
    def versions(project_id: str) -> list[dict]:
        """List immutable generated and revised document versions."""
        return repository.list_versions(project_id)

    @app.get(prefix + "/projects/{project_id}/versions/{version_id}")
    def version(project_id: str, version_id: str) -> dict:
        """Read one exact canonical document and its recomputed validation report."""
        return validated_version(project_id, version_id)

    @app.put(
        prefix + "/projects/{project_id}/versions/{version_id}/sections/{section}", status_code=202
    )
    def edit(project_id: str, version_id: str, section: str, body: EditInput) -> dict:
        """Validate a human edit, rebuild linked views and save an unapproved successor."""
        if section not in SECTION_SCHEMAS:
            raise KeyError("section_not_found")
        old = repository.get_version(project_id, version_id)
        if old["content_hash"] != body.expected_content_hash:
            raise ValueError("stale_edit")
        SECTION_SCHEMAS[section].model_validate(body.content)
        allowed = (
            {"compliance", "architecture", "threats", "risks", "scenarios", "verification", "sdlc"}
            if section in REQUIREMENT_PREFIXES
            else {
                "introduction": {"sdlc"},
                "architecture": {"threats", "risks"},
                "verification": {"sdlc"},
            }.get(section, set())
        )
        if set(body.dependent_edits) - allowed:
            raise ValueError("unrelated_dependent_edit")
        for name, content in body.dependent_edits.items():
            SECTION_SCHEMAS[name].model_validate(content)
        return coordinator.start(
            project_id,
            "edit",
            version_id=version_id,
            section=section,
            edited_content=body.content,
            edit_actor=body.editor,
            checkpoint_edits=body.dependent_edits or None,
        )

    @app.post(
        prefix + "/projects/{project_id}/versions/{version_id}/regenerate/{section}",
        status_code=202,
    )
    def regenerate(project_id: str, version_id: str, section: str) -> dict:
        """Regenerate one section and its dependent artifacts, preserving unrelated text."""
        if section not in SECTION_SCHEMAS:
            raise KeyError("section_not_found")
        repository.get_version(project_id, version_id)
        return coordinator.start(project_id, "regenerate", version_id=version_id, section=section)

    @app.get(prefix + "/projects/{project_id}/versions/{version_id}/reviews")
    def reviews(project_id: str, version_id: str) -> list[dict]:
        """Return human decisions for the selected immutable version."""
        return repository.list_reviews(project_id, version_id)

    @app.post(prefix + "/projects/{project_id}/versions/{version_id}/reviews", status_code=201)
    def review(project_id: str, version_id: str, body: ReviewInput) -> dict:
        """Persist explicit reviewer attribution against the supplied exact content hash."""
        if body.decision == "approve":
            selected = validated_version(project_id, version_id)
            if selected["quality"]["status"] == "invalid":
                raise ValueError("invalid_document_cannot_be_approved")
        return repository.add_review(project_id, version_id, **body.model_dump())

    @app.get(prefix + "/projects/{project_id}/versions/{version_id}/export/{format}")
    def export(
        project_id: str,
        version_id: str,
        format: Literal["json", "markdown", "pdf"],
        detail: Literal["standard", "full"] = "standard",
    ) -> Response:
        """Render stored validated data with truthful draft/approval status."""
        selected = validated_version(project_id, version_id)
        decisions = repository.list_reviews(project_id, version_id)
        filename = f"CyberSRS-v{selected['sequence']}"
        if format == "json":
            content = json.dumps(selected, ensure_ascii=False, indent=2).encode("utf-8")
            media_type, extension = "application/json", "json"
        elif format == "markdown":
            content = render_markdown(selected, decisions, detail=detail).encode("utf-8")
            media_type, extension = "text/markdown; charset=utf-8", "md"
        else:
            content = render_pdf(selected, decisions, detail=detail)
            media_type, extension = "application/pdf", "pdf"
        repository.record_audit(
            project_id,
            "artifact_exported",
            {
                "version_id": version_id,
                "content_hash": selected["content_hash"],
                "format": format,
                "detail": detail,
                "sha256": hashlib.sha256(content).hexdigest(),
                "content_base64": base64.b64encode(content).decode("ascii"),
                "quality": selected["quality"],
            },
        )
        return Response(
            content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}.{extension}"',
            },
        )

    @app.get(prefix + "/projects/{project_id}/documents")
    def documents(project_id: str) -> list[dict]:
        """List only reference metadata; extracted text stays out of summaries."""
        return [
            {k: v for k, v in item.items() if k != "text"}
            for item in repository.list_documents(project_id)
        ]

    @app.post(prefix + "/projects/{project_id}/documents", status_code=201)
    async def upload(project_id: str, file: UploadFile = File(...)) -> dict:
        """Bound, parse and index a project-private reference without executing it."""
        repository.get_project(project_id)
        raw = await file.read(settings.max_upload_bytes + 1)
        if len(raw) > settings.max_upload_bytes:
            raise HTTPException(
                413, detail={"code": "upload_too_large", "message": "File too large"}
            )
        name = Path(file.filename or "reference.txt").name
        text = extract_text(name, raw)
        if not text.strip() or len(text) > 120000:
            raise ValueError("reference_text_limit")
        saved = repository.add_document(project_id, name, text, source_digest(raw))
        try:
            knowledge.ingest(saved["id"], name, text, saved["sha256"], project_id)
        except Exception as exc:
            knowledge.delete_private(project_id, saved["id"])
            repository.delete_document(project_id, saved["id"])
            raise GenerationError("reference_indexing_failed") from exc
        repository.update_project(project_id, analysis=None)
        return {k: v for k, v in saved.items() if k != "text"}

    @app.delete(prefix + "/projects/{project_id}/documents/{document_id}", status_code=204)
    def delete_document(project_id: str, document_id: str) -> Response:
        """Delete only the selected project's reference and invalidate its analysis."""
        knowledge.delete_private(project_id, document_id)
        repository.delete_document(project_id, document_id)
        repository.update_project(project_id, analysis=None)
        return Response(status_code=204)

    @app.post(prefix + "/chat")
    def chat(body: ChatInput) -> dict:
        """Answer a local cybersecurity question with schema-checked citations."""
        if body.project_id:
            repository.get_project(body.project_id)
        sources = knowledge.retrieve(body.message, body.project_id)
        source_map = {source.id: source for source in sources}

        def validate(response: ChatResponse) -> list[str]:
            """Reject unknown or nonliteral references before returning a chat answer."""
            return [
                "unknown_or_nonliteral_citation"
                for citation in response.sources
                if citation.chunk_id not in source_map
                or citation.quote not in source_map[citation.chunk_id].text
            ]

        with audit_scope(repository, body.project_id):
            result, provenance = chat_provider.generate(
                prompts.CHAT,
                {"question": body.message, "sources": [source.model_dump() for source in sources]},
                ChatResponse,
                threading.Event(),
                time.monotonic() + settings.ollama_timeout_seconds,
                validate,
            )
        return {
            **result.model_dump(),
            "provenance": provenance,
            "source_chunks": [source.model_dump() for source in sources],
        }

    if settings.frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")
    return app

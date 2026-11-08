"""Local Chroma retrieval with exact provenance and mandatory private-source isolation."""

from __future__ import annotations

import hashlib
import os
import threading
import time
from pathlib import Path

import httpx

from .config import Settings
from .inference_privacy import InferencePrivacy
from .provider import LOCAL_INFERENCE_LOCK, GenerationError
from .schemas import SourceChunk


def extract_text(name: str, raw: bytes) -> str:
    """Parse allowed reference formats without executing embedded content."""
    suffix = Path(name).suffix.casefold()
    if suffix == ".pdf":
        import pymupdf

        with pymupdf.open(stream=raw, filetype="pdf") as document:
            if document.page_count > 300:
                raise ValueError("reference_page_limit")
            return "\n".join(page.get_text() for page in document)
    if suffix not in {".txt", ".md", ".csv"}:
        raise ValueError("unsupported_reference_format")
    return raw.decode("utf-8-sig")


def chunk_text(text: str, size: int = 1800, overlap: int = 200) -> list[str]:
    """Create deterministic overlapping source chunks without losing tail text."""
    return [
        text[start : start + size]
        for start in range(0, len(text), size - overlap)
        if text[start : start + size].strip()
    ]


class KnowledgeBase:
    """Keep one local Chroma client, with no telemetry and no cross-project fallback."""

    def __init__(self, settings: Settings) -> None:
        """Delay the optional vector runtime until retrieval or ingestion is requested."""
        self.settings = settings
        self._client = None
        self._lock = threading.RLock()

    def _collections(self):
        with self._lock:
            if self._client is None:
                os.environ["ANONYMIZED_TELEMETRY"] = "False"
                import chromadb
                from chromadb.config import Settings as ChromaSettings

                self._client = chromadb.PersistentClient(
                    path=str(self.settings.data_dir / "chroma"),
                    settings=ChromaSettings(
                        anonymized_telemetry=False,
                        chroma_product_telemetry_impl="cybersrs.telemetry.NoTelemetry",
                        chroma_telemetry_impl="cybersrs.telemetry.NoTelemetry",
                    ),
                )
            return [
                self._client.get_or_create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"},
                    embedding_function=None,
                )
                for name in ("cybersrs_knowledge", "cybersrs_private")
            ]

    def _embed(
        self, texts: list[str], *, timeout_seconds: float | None = None
    ) -> list[list[float]]:
        started = time.monotonic()
        acquired = (
            LOCAL_INFERENCE_LOCK.acquire()
            if timeout_seconds is None
            else LOCAL_INFERENCE_LOCK.acquire(timeout=timeout_seconds)
        )
        if not acquired:
            raise GenerationError("retrieval_budget_exhausted")
        try:
            remaining = (
                self.settings.ollama_timeout_seconds
                if timeout_seconds is None
                else max(0.001, timeout_seconds - (time.monotonic() - started))
            )
            response = httpx.post(
                f"{self.settings.ollama_base_url}/api/embed",
                json={
                    "model": self.settings.embedding_model,
                    "input": InferencePrivacy().mask_value(texts),
                    "truncate": False,
                },
                timeout=min(self.settings.ollama_timeout_seconds, remaining),
                follow_redirects=False,
            )
        finally:
            LOCAL_INFERENCE_LOCK.release()
        response.raise_for_status()
        vectors = response.json()["embeddings"]
        if len(vectors) != len(texts):
            raise GenerationError("embedding_count_mismatch")
        return vectors

    def ingest(
        self,
        document_id: str,
        title: str,
        text: str,
        digest: str,
        project_id: str | None = None,
    ) -> int:
        """Index source text and all required metadata into the isolated collection."""
        chunks = chunk_text(text)
        collection = self._collections()[1 if project_id else 0]
        # Idempotent re-ingestion replaces an old document's stale tail as well.
        where = {"$and": [{"source_document_id": document_id}, {"project_id": project_id}]}
        collection.delete(where=where if project_id else {"source_document_id": document_id})
        for start in range(0, len(chunks), 24):
            batch = chunks[start : start + 24]
            collection.upsert(
                ids=[f"{document_id}:{index}" for index in range(start, start + len(batch))],
                embeddings=self._embed(batch),
                documents=batch,
                metadatas=[
                    {
                        "source_document_id": document_id,
                        "title": title,
                        "chunk_index": index,
                        "page_or_section": f"text chunk {index + 1}",
                        "sha256": digest,
                        "project_id": project_id or "global",
                    }
                    for index in range(start, start + len(batch))
                ],
            )
        return len(chunks)

    def retrieve(
        self, query: str, project_id: str | None = None, *, timeout_seconds: float | None = None
    ) -> list[SourceChunk]:
        """Return scored literal chunks; private queries always include project filters."""
        if not self.settings.rag_enabled:
            return []
        collections = self._collections()
        if not any(collection.count() for collection in collections):
            return []
        vector = (
            self._embed([query], timeout_seconds=timeout_seconds)
            if timeout_seconds is not None
            else self._embed([query])
        )[0]
        result: list[SourceChunk] = []
        for index, collection in enumerate(collections):
            if (index == 1 and project_id is None) or not collection.count():
                continue
            query_args = {"where": {"project_id": project_id}} if index == 1 else {}
            retrieved = collection.query(
                query_embeddings=[vector],
                n_results=self.settings.rag_top_k,
                include=["documents", "metadatas", "distances"],
                **query_args,
            )
            for cid, text, metadata, distance in zip(
                retrieved["ids"][0],
                retrieved["documents"][0],
                retrieved["metadatas"][0],
                retrieved["distances"][0],
                strict=True,
            ):
                score = max(0.0, min(1.0, 1.0 - distance))
                if score >= self.settings.rag_min_score:
                    result.append(
                        SourceChunk(
                            id=cid,
                            source_document_id=metadata["source_document_id"],
                            chunk_index=metadata["chunk_index"],
                            page_or_section=metadata["page_or_section"],
                            relevance_score=round(score, 4),
                            text=text,
                            title=metadata["title"],
                            sha256=metadata["sha256"],
                        )
                    )
        return sorted(result, key=lambda chunk: (-chunk.relevance_score, chunk.id))[
            : self.settings.rag_top_k
        ]

    def delete_private(self, project_id: str, document_id: str | None = None) -> None:
        """Delete only matching private chunks, including on project removal."""
        where = (
            {"$and": [{"project_id": project_id}, {"source_document_id": document_id}]}
            if document_id
            else {"project_id": project_id}
        )
        self._collections()[1].delete(where=where)

    def counts(self) -> dict[str, int]:
        """Report local index readiness without sending inference or embedding requests."""
        return dict(
            zip(("global", "private"), (c.count() for c in self._collections()), strict=True)
        )


def source_digest(raw: bytes) -> str:
    """Identify exact reference bytes for audit and reproducible knowledge versions."""
    return hashlib.sha256(raw).hexdigest()

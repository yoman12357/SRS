"""Reproducible local knowledge ingestion and runtime preflight commands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import Settings
from .knowledge import KnowledgeBase, extract_text, source_digest
from .provider import OllamaProvider

SEED_TOPICS = (
    "Authentication_Cheat",
    "Authorization_Cheat",
    "Logging_Cheat",
    "Network_Segmentation_Cheat",
    "Zero_Trust_Architecture_Cheat",
)


def ingest(settings: Settings, all_sources: bool = False) -> dict:
    """Index seed guidance or the full copied corpus, reusing exact verified file hashes."""
    knowledge = KnowledgeBase(settings)
    manifest_path = settings.data_dir / "ingestion.json"
    manifest = json.loads(manifest_path.read_text("utf-8")) if manifest_path.exists() else {}
    failures = []
    indexed = 0
    for path in sorted(settings.knowledge_dir.rglob("*")):
        if not path.is_file() or path.suffix.casefold() not in {".pdf", ".md", ".txt", ".csv"}:
            continue
        if not all_sources and not any(topic in path.name for topic in SEED_TOPICS):
            continue
        key = path.relative_to(settings.knowledge_dir).as_posix()
        raw = path.read_bytes()
        digest = source_digest(raw)
        if manifest.get(key, {}).get("sha256") == digest:
            continue
        try:
            text = extract_text(path.name, raw)
            document_id = "kb-" + source_digest(key.encode("utf-8"))[:16]
            chunks = knowledge.ingest(document_id, key, text, digest)
            manifest[key] = {"sha256": digest, "document_id": document_id, "chunks": chunks}
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            indexed += 1
            print(json.dumps({"indexed": key, "chunks": chunks}), flush=True)
        except Exception as exc:
            failures.append({"source": key, "error_type": type(exc).__name__})
            print(json.dumps(failures[-1]), flush=True)
    return {
        "newly_indexed_documents": indexed,
        "known_documents": len(manifest),
        "failures": failures,
        "index_counts": knowledge.counts(),
    }


def main() -> None:
    """Run explicit local setup tasks without downloading models or collecting telemetry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["preflight", "ingest"])
    parser.add_argument(
        "--all", action="store_true", help="Index the entire copied knowledge corpus"
    )
    args = parser.parse_args()
    settings = Settings()
    if args.command == "preflight":
        print(
            json.dumps(
                {
                    "model": OllamaProvider(settings).readiness(),
                    "knowledge": KnowledgeBase(settings).counts(),
                    "project_root": str(Path.cwd()),
                },
                indent=2,
            )
        )
    else:
        result = ingest(settings, args.all)
        print(json.dumps(result, indent=2))
        if result["failures"]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()

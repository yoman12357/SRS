#!/usr/bin/env python3
"""
build_srs_dataset.py

Build a NEW fine-tuning dataset only from the SRS corpus folder.

What it does
------------
- Recursively finds source documents in the selected SRS corpus folder.
- Extracts text from PDF/DOCX/TXT/MD files.
- Uses ONLY 2 chunks per document.
- Asks Ollama to generate EXACTLY 4 supervised examples per chunk.
- Therefore: maximum 8 examples per document.
- Writes a separate dataset:
      srs_dataset/train.jsonl
      srs_dataset/val.jsonl
      srs_dataset/test.jsonl
      srs_dataset/all_examples.jsonl
      srs_dataset/progress.jsonl
      srs_dataset/dataset_summary.json
- Splits BY DOCUMENT, not by individual example, to avoid train/test leakage.
- Resume-safe: completed chunks are skipped on rerun.

Default Ollama model:
    qwen3:4b-instruct-2507-q4_K_M
"""

import argparse
import hashlib
import json
import logging
import random
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import requests
except ImportError:
    print("Missing package: requests")
    print("Install with: pip install requests pypdf python-docx")
    raise

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
DEFAULT_MODEL = "qwen3:4b-instruct-2507-q4_K_M"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"

# Exactly what you requested:
MAX_CHUNKS_PER_DOCUMENT = 2
EXAMPLES_PER_CHUNK = 4

# Character-based chunking keeps the script dependency-light.
# Roughly 3500-4500 chars is usually manageable for this task.
CHUNK_SIZE = 4200
CHUNK_OVERLAP = 450
MIN_CHUNK_CHARS = 700

SYSTEM_PROMPT = """You are preparing supervised fine-tuning examples for CyberSRS, an AI software architect focused on cybersecurity, network monitoring, networking, secure communications, and infrastructure systems.

You are given a chunk from a REAL Software Requirements Specification (SRS).

Create training examples that teach the model how to turn an informal cybersecurity/networking project request into precise, professional SRS-style requirements.

Rules:
1. Ground every example in the supplied SRS chunk.
2. Do not invent unsupported product names, standards, numbers, protocols, or compliance claims.
3. Do not copy long passages verbatim. Generalize the source into a realistic user request and a high-quality SRS response.
4. Output requirements should use precise "The system shall ..." language where appropriate.
5. Keep requirements atomic and testable.
6. Preserve networking/cybersecurity meaning from the source.
7. Include acceptance criteria when useful. Prefer Given/When/Then wording.
8. Each generated example must be meaningfully different.
9. Return JSON only.
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build an SRS-only CyberSRS fine-tuning dataset with 2 chunks/document and 4 examples/chunk."
    )
    parser.add_argument(
        "--source-dir",
        default="CyberSRS_Strict_Cybersecurity_Networking_SRS_50",
        help="Folder containing the extracted/downloaded SRS documents.",
    )
    parser.add_argument(
        "--output-dir",
        default="srs_dataset",
        help="Separate output folder for this new SRS-only dataset.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name.")
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL, help="Ollama base URL.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Ollama request timeout in seconds.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic dataset split seed.",
    )
    return parser.parse_args()


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove isolated page-number-like lines.
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if re.fullmatch(r"(page\s+)?\d+(\s+of\s+\d+)?", s, flags=re.I):
            continue
        lines.append(s)
    return "\n".join(lines).strip()


def extract_pdf(path: Path) -> str:
    if PdfReader is None:
        raise RuntimeError("pypdf is not installed. Run: pip install pypdf")
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception as exc:
            logging.warning("Could not extract page from %s: %s", path.name, exc)
    return clean_text("\n\n".join(pages))


def extract_docx(path: Path) -> str:
    if Document is None:
        raise RuntimeError("python-docx is not installed. Run: pip install python-docx")
    doc = Document(str(path))
    return clean_text("\n".join(p.text for p in doc.paragraphs if p.text.strip()))


def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_pdf(path)
    if ext == ".docx":
        return extract_docx(path)
    if ext in {".txt", ".md"}:
        return clean_text(path.read_text(encoding="utf-8", errors="ignore"))
    return ""


def make_chunks(text: str) -> List[str]:
    """
    Build normal sequential chunks, then keep the first two substantial ones.
    This is intentionally capped at exactly 2 chunks/document.
    """
    if len(text) < MIN_CHUNK_CHARS:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    current = ""

    for para in paragraphs:
        candidate = (current + "\n\n" + para).strip() if current else para

        if len(candidate) <= CHUNK_SIZE:
            current = candidate
            continue

        if len(current) >= MIN_CHUNK_CHARS:
            chunks.append(current)

        # Carry a small overlap from the previous chunk.
        overlap = current[-CHUNK_OVERLAP:] if current else ""
        current = (overlap + "\n\n" + para).strip()

        # Handle an unusually large paragraph.
        while len(current) > CHUNK_SIZE:
            piece = current[:CHUNK_SIZE].strip()
            if len(piece) >= MIN_CHUNK_CHARS:
                chunks.append(piece)
            current = current[CHUNK_SIZE - CHUNK_OVERLAP :].strip()

    if len(current) >= MIN_CHUNK_CHARS:
        chunks.append(current)

    # If extraction produced one huge usable body but paragraph logic did not
    # create two chunks, split deterministically.
    if len(chunks) == 1 and len(text) >= (MIN_CHUNK_CHARS * 2):
        midpoint = len(text) // 2
        left = text[:midpoint].strip()
        right = text[max(0, midpoint - CHUNK_OVERLAP):].strip()
        chunks = [left[:CHUNK_SIZE], right[:CHUNK_SIZE]]

    return chunks[:MAX_CHUNKS_PER_DOCUMENT]


def stable_id(*parts: str) -> str:
    raw = "||".join(parts).encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()[:16]


def ollama_is_running(base_url: str, timeout: int = 15) -> bool:
    try:
        r = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=timeout)
        return r.ok
    except requests.RequestException:
        return False


def model_exists(base_url: str, model: str) -> bool:
    try:
        r = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=30)
        r.raise_for_status()
        data = r.json()
        names = {m.get("name", "") for m in data.get("models", [])}
        return model in names or any(n.split(":")[0] == model.split(":")[0] for n in names)
    except Exception:
        return False


def parse_json_response(content: str):
    content = content.strip()

    # Strip markdown fences if the model ignored JSON-only instruction.
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.I)
        content = re.sub(r"\s*```$", "", content)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Recover the outermost JSON object if explanatory text slipped in.
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end > start:
        return json.loads(content[start:end + 1])

    raise ValueError("Could not parse model response as JSON.")


def validate_example(ex: Dict) -> Tuple[bool, str]:
    required = ["instruction", "input", "output"]
    for field in required:
        if field not in ex:
            return False, f"missing {field}"
        if not isinstance(ex[field], str):
            return False, f"{field} is not a string"

    if len(ex["instruction"].strip()) < 20:
        return False, "instruction too short"
    if len(ex["output"].strip()) < 80:
        return False, "output too short"

    return True, ""


def generate_four_examples(
    base_url: str,
    model: str,
    source_name: str,
    chunk_index: int,
    chunk_text: str,
    timeout: int,
    max_attempts: int = 3,
) -> List[Dict]:
    user_prompt = f"""SOURCE DOCUMENT:
{source_name}

CHUNK:
{chunk_text}

Generate EXACTLY {EXAMPLES_PER_CHUNK} supervised fine-tuning examples from this chunk.

Return this exact JSON shape:
{{
  "examples": [
    {{
      "instruction": "A realistic user instruction asking CyberSRS to specify/design part of a cybersecurity or networking system.",
      "input": "Optional project context or constraints. Use an empty string if none is needed.",
      "output": "A professional SRS-style answer grounded in the source chunk."
    }}
  ]
}}

Requirements:
- EXACTLY {EXAMPLES_PER_CHUNK} objects in "examples".
- Each example must focus on a different requirement, behavior, constraint, interface, monitoring/security concern, or use case visible in the chunk.
- Do not mention that you were given a source chunk.
- Do not include citations unless the source chunk itself makes them meaningful.
- JSON only.
"""

    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "options": {
            "temperature": 0.35,
            "top_p": 0.9,
            "num_ctx": 8192,
        },
    }

    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            r = requests.post(
                f"{base_url.rstrip('/')}/api/chat",
                json=payload,
                timeout=timeout,
            )
            r.raise_for_status()
            data = r.json()
            content = data["message"]["content"]
            parsed = parse_json_response(content)
            examples = parsed.get("examples", [])

            valid = []
            for ex in examples:
                if not isinstance(ex, dict):
                    continue
                ok, reason = validate_example(ex)
                if ok:
                    valid.append({
                        "instruction": ex["instruction"].strip(),
                        "input": ex["input"].strip(),
                        "output": ex["output"].strip(),
                    })

            if len(valid) >= EXAMPLES_PER_CHUNK:
                return valid[:EXAMPLES_PER_CHUNK]

            last_error = f"Only {len(valid)} valid examples returned."
        except Exception as exc:
            last_error = str(exc)

        logging.warning(
            "Generation attempt %d/%d failed for %s chunk %d: %s",
            attempt,
            max_attempts,
            source_name,
            chunk_index,
            last_error,
        )
        time.sleep(2 * attempt)

    raise RuntimeError(
        f"Failed to generate {EXAMPLES_PER_CHUNK} valid examples "
        f"for {source_name} chunk {chunk_index}: {last_error}"
    )


def append_jsonl(path: Path, records: List[Dict]):
    with path.open("a", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                logging.warning("Skipping malformed line in %s", path)
    return records


def write_jsonl(path: Path, records: List[Dict]):
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def assign_document_splits(documents: List[str], seed: int) -> Dict[str, str]:
    docs = sorted(set(documents))
    rng = random.Random(seed)
    rng.shuffle(docs)

    n = len(docs)
    if n == 0:
        return {}

    # Target 80/10/10 while keeping at least one val/test doc when possible.
    n_test = max(1, round(n * 0.10)) if n >= 3 else 0
    n_val = max(1, round(n * 0.10)) if n >= 3 else 0

    # Prevent over-allocation for very small corpora.
    while n_test + n_val >= n and (n_test > 0 or n_val > 0):
        if n_test >= n_val and n_test > 0:
            n_test -= 1
        elif n_val > 0:
            n_val -= 1

    test_docs = set(docs[:n_test])
    val_docs = set(docs[n_test:n_test + n_val])

    result = {}
    for doc in docs:
        if doc in test_docs:
            result[doc] = "test"
        elif doc in val_docs:
            result[doc] = "val"
        else:
            result[doc] = "train"
    return result


def main():
    args = parse_args()

    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    if not source_dir.exists():
        print(f"\nERROR: Source folder not found:\n  {source_dir}")
        print("\nPut this script in your fine-tuning folder and make sure the extracted")
        print("SRS folder is beside it, or pass the correct folder using --source-dir.")
        sys.exit(1)

    documents = sorted(
        p for p in source_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not documents:
        print(f"\nERROR: No PDF/DOCX/TXT/MD documents found under:\n  {source_dir}")
        print("\nIf your extracted ZIP currently contains only .url shortcuts, first run:")
        print("  DOWNLOAD_ALL_WINDOWS.cmd")
        print("inside the corpus folder so the original SRS PDFs are downloaded.")
        sys.exit(1)

    if not ollama_is_running(args.ollama_url):
        print("\nERROR: Ollama is not running.")
        print("Open another terminal and run:")
        print("  ollama serve")
        sys.exit(1)

    if not model_exists(args.ollama_url, args.model):
        logging.warning(
            "Model '%s' was not found in /api/tags. The call may fail if the model name differs.",
            args.model,
        )

    progress_path = output_dir / "progress.jsonl"
    existing = read_jsonl(progress_path)

    # A chunk is complete only when all 4 expected examples are already stored.
    completed_counts: Dict[str, int] = {}
    for rec in existing:
        key = rec.get("chunk_key")
        if key:
            completed_counts[key] = completed_counts.get(key, 0) + 1

    logging.info("Found %d supported source documents.", len(documents))
    logging.info(
        "Policy: max %d chunks/document × %d examples/chunk = max %d examples/document.",
        MAX_CHUNKS_PER_DOCUMENT,
        EXAMPLES_PER_CHUNK,
        MAX_CHUNKS_PER_DOCUMENT * EXAMPLES_PER_CHUNK,
    )
    logging.info("Output folder: %s", output_dir)

    extraction_failures = []
    generation_failures = []

    for doc_no, path in enumerate(documents, start=1):
        rel = path.relative_to(source_dir).as_posix()
        logging.info("[%d/%d] Extracting %s", doc_no, len(documents), rel)

        try:
            text = extract_text(path)
        except Exception as exc:
            logging.error("Extraction failed for %s: %s", rel, exc)
            extraction_failures.append({"document": rel, "error": str(exc)})
            continue

        chunks = make_chunks(text)
        if not chunks:
            logging.warning("No usable chunks from %s", rel)
            extraction_failures.append({"document": rel, "error": "No usable extracted text"})
            continue

        logging.info("  selected %d chunk(s); maximum is %d", len(chunks), MAX_CHUNKS_PER_DOCUMENT)

        for chunk_idx, chunk_text in enumerate(chunks, start=1):
            chunk_key = stable_id(rel, str(chunk_idx), chunk_text[:250])
            done = completed_counts.get(chunk_key, 0)

            if done >= EXAMPLES_PER_CHUNK:
                logging.info(
                    "  chunk %d/%d already complete (%d examples) — skipping",
                    chunk_idx,
                    len(chunks),
                    done,
                )
                continue

            logging.info(
                "  generating examples for chunk %d/%d (target=%d)",
                chunk_idx,
                len(chunks),
                EXAMPLES_PER_CHUNK,
            )

            try:
                generated = generate_four_examples(
                    args.ollama_url,
                    args.model,
                    rel,
                    chunk_idx,
                    chunk_text,
                    args.timeout,
                )
            except Exception as exc:
                logging.error("Generation failed: %s", exc)
                generation_failures.append(
                    {"document": rel, "chunk": chunk_idx, "error": str(exc)}
                )
                continue

            # If a previous interrupted run saved fewer than four records,
            # only append the number still needed.
            needed = max(0, EXAMPLES_PER_CHUNK - done)
            generated = generated[:needed]

            records = []
            for local_idx, ex in enumerate(generated, start=done + 1):
                record = {
                    "instruction": ex["instruction"],
                    "input": ex["input"],
                    "output": ex["output"],
                    "messages": [
                        {"role": "user", "content": (
                            ex["instruction"]
                            + (("\n\nContext:\n" + ex["input"]) if ex["input"] else "")
                        )},
                        {"role": "assistant", "content": ex["output"]},
                    ],
                    "metadata": {
                        "dataset": "CyberSRS_SRS_only",
                        "source_document": rel,
                        "source_chunk": chunk_idx,
                        "example_in_chunk": local_idx,
                        "model_used_for_generation": args.model,
                    },
                    "chunk_key": chunk_key,
                }
                records.append(record)

            append_jsonl(progress_path, records)
            completed_counts[chunk_key] = done + len(records)
            logging.info("  accepted %d example(s)", len(records))

    # Re-read final progress file and de-duplicate by source/chunk/example number.
    all_records = read_jsonl(progress_path)
    dedup = {}
    for rec in all_records:
        meta = rec.get("metadata", {})
        key = (
            meta.get("source_document", ""),
            meta.get("source_chunk", 0),
            meta.get("example_in_chunk", 0),
        )
        dedup[key] = rec
    all_records = list(dedup.values())

    # Deterministic split BY SOURCE DOCUMENT to prevent leakage.
    source_documents = [
        rec.get("metadata", {}).get("source_document", "")
        for rec in all_records
        if rec.get("metadata", {}).get("source_document")
    ]
    split_map = assign_document_splits(source_documents, args.seed)

    train, val, test = [], [], []
    for rec in all_records:
        doc = rec.get("metadata", {}).get("source_document", "")
        split = split_map.get(doc, "train")
        # chunk_key is useful for progress but unnecessary for trainer files.
        clean_rec = dict(rec)
        clean_rec.pop("chunk_key", None)
        clean_rec["metadata"] = dict(clean_rec.get("metadata", {}))
        clean_rec["metadata"]["split"] = split

        if split == "test":
            test.append(clean_rec)
        elif split == "val":
            val.append(clean_rec)
        else:
            train.append(clean_rec)

    write_jsonl(output_dir / "all_examples.jsonl", [
        {k: v for k, v in rec.items() if k != "chunk_key"} for rec in all_records
    ])
    write_jsonl(output_dir / "train.jsonl", train)
    write_jsonl(output_dir / "val.jsonl", val)
    write_jsonl(output_dir / "test.jsonl", test)

    summary = {
        "source_dir": str(source_dir),
        "model": args.model,
        "supported_documents_found": len(documents),
        "max_chunks_per_document": MAX_CHUNKS_PER_DOCUMENT,
        "examples_per_chunk": EXAMPLES_PER_CHUNK,
        "max_examples_per_document": MAX_CHUNKS_PER_DOCUMENT * EXAMPLES_PER_CHUNK,
        "total_examples": len(all_records),
        "train_examples": len(train),
        "val_examples": len(val),
        "test_examples": len(test),
        "train_documents": len({r["metadata"]["source_document"] for r in train}),
        "val_documents": len({r["metadata"]["source_document"] for r in val}),
        "test_documents": len({r["metadata"]["source_document"] for r in test}),
        "extraction_failures": extraction_failures,
        "generation_failures": generation_failures,
    }

    (output_dir / "dataset_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n" + "=" * 70)
    print("SRS DATASET BUILD FINISHED")
    print("=" * 70)
    print(f"Documents found : {len(documents)}")
    print(f"Total examples  : {len(all_records)}")
    print(f"Train           : {len(train)}")
    print(f"Validation      : {len(val)}")
    print(f"Test            : {len(test)}")
    print(f"Output folder   : {output_dir}")
    print("=" * 70)
    print("\nExpected maximum for 50 usable documents:")
    print("  50 documents × 2 chunks × 4 examples = 400 examples")
    print("\nSee dataset_summary.json for failures or skipped documents.")


if __name__ == "__main__":
    main()

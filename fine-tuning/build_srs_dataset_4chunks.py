#!/usr/bin/env python3
import argparse, hashlib, json, logging, random, re, sys, time
from pathlib import Path

import requests
from pypdf import PdfReader

MODEL = "qwen3:4b-instruct-2507-q4_K_M"
OLLAMA_URL = "http://127.0.0.1:11434"

MAX_CHUNKS_PER_DOCUMENT = 4
EXAMPLES_PER_CHUNK = 4
CHUNK_SIZE = 4200
CHUNK_OVERLAP = 450
MIN_CHUNK_CHARS = 700

SYSTEM_PROMPT = """You are creating supervised fine-tuning data for CyberSRS, an AI software architect for cybersecurity, network monitoring and networking.

You are given text from a real Software Requirements Specification (SRS).

Generate realistic training examples that teach the model to convert an informal cybersecurity/networking project request into precise SRS-style requirements.

Rules:
- Ground every example in the supplied SRS text.
- Do not invent unsupported standards, numbers, products, protocols, or compliance claims.
- Do not copy long passages verbatim.
- Prefer precise, atomic, testable "The system shall ..." requirements.
- Include Given/When/Then acceptance criteria when useful.
- Keep the examples meaningfully different.
- Return JSON only.
"""

def args():
    p = argparse.ArgumentParser()
    p.add_argument("--source-dir", default="CyberSRS_Strict_Cybersecurity_Networking_SRS_50")
    p.add_argument("--output-dir", default="srs_dataset_4chunks")
    p.add_argument("--model", default=MODEL)
    p.add_argument("--ollama-url", default=OLLAMA_URL)
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()

def clean_text(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def extract_pdf(path):
    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception as e:
            logging.warning("Page extraction failed in %s: %s", path.name, e)
    return clean_text("\n\n".join(parts))

def make_chunks(text):
    if len(text) < MIN_CHUNK_CHARS:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, current = [], ""

    for para in paragraphs:
        candidate = (current + "\n\n" + para).strip() if current else para
        if len(candidate) <= CHUNK_SIZE:
            current = candidate
            continue

        if len(current) >= MIN_CHUNK_CHARS:
            chunks.append(current)

        overlap = current[-CHUNK_OVERLAP:] if current else ""
        current = (overlap + "\n\n" + para).strip()

        while len(current) > CHUNK_SIZE:
            piece = current[:CHUNK_SIZE].strip()
            if len(piece) >= MIN_CHUNK_CHARS:
                chunks.append(piece)
            current = current[CHUNK_SIZE - CHUNK_OVERLAP:].strip()

    if len(current) >= MIN_CHUNK_CHARS:
        chunks.append(current)

    return chunks[:MAX_CHUNKS_PER_DOCUMENT]

def stable_id(*parts):
    raw = "||".join(parts).encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()[:16]

def read_jsonl(path):
    if not path.exists():
        return []
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out

def append_jsonl(path, rows):
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

def parse_json(content):
    content = content.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.I)
    content = re.sub(r"\s*```$", "", content)
    try:
        return json.loads(content)
    except Exception:
        s, e = content.find("{"), content.rfind("}")
        if s != -1 and e > s:
            return json.loads(content[s:e+1])
        raise

def generate_examples(base_url, model, source_name, chunk_no, chunk, timeout):
    prompt = f"""SOURCE SRS:
{source_name}

SRS CHUNK:
{chunk}

Generate EXACTLY {EXAMPLES_PER_CHUNK} supervised fine-tuning examples.

Return exactly:
{{
  "examples": [
    {{
      "instruction": "realistic user request",
      "input": "optional project context or empty string",
      "output": "professional SRS-style response"
    }}
  ]
}}

Requirements:
- EXACTLY {EXAMPLES_PER_CHUNK} examples.
- Each example must focus on a different requirement/constraint/interface/security/networking behavior.
- Do not mention the source chunk.
- JSON only.
"""

    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "options": {
            "temperature": 0.35,
            "top_p": 0.9,
            "num_ctx": 8192,
        },
    }

    last = None
    for attempt in range(1, 4):
        try:
            r = requests.post(
                f"{base_url.rstrip('/')}/api/chat",
                json=payload,
                timeout=timeout,
            )
            r.raise_for_status()
            data = parse_json(r.json()["message"]["content"])
            exs = data.get("examples", [])
            valid = []
            for ex in exs:
                if not isinstance(ex, dict):
                    continue
                ins = str(ex.get("instruction", "")).strip()
                inp = str(ex.get("input", "")).strip()
                out = str(ex.get("output", "")).strip()
                if len(ins) >= 20 and len(out) >= 80:
                    valid.append({"instruction": ins, "input": inp, "output": out})
            if len(valid) >= EXAMPLES_PER_CHUNK:
                return valid[:EXAMPLES_PER_CHUNK]
            last = f"only {len(valid)} valid examples returned"
        except Exception as e:
            last = str(e)

        logging.warning(
            "Attempt %d/3 failed for %s chunk %d: %s",
            attempt, source_name, chunk_no, last
        )
        time.sleep(attempt * 2)

    raise RuntimeError(last)

def split_by_document(records, seed):
    docs = sorted({r["metadata"]["source_document"] for r in records})
    rng = random.Random(seed)
    rng.shuffle(docs)

    n = len(docs)
    n_test = max(1, round(n * 0.10)) if n >= 3 else 0
    n_val = max(1, round(n * 0.10)) if n >= 3 else 0

    test_docs = set(docs[:n_test])
    val_docs = set(docs[n_test:n_test+n_val])

    train, val, test = [], [], []
    for r in records:
        d = r["metadata"]["source_document"]
        c = dict(r)
        c["metadata"] = dict(c["metadata"])
        if d in test_docs:
            c["metadata"]["split"] = "test"
            test.append(c)
        elif d in val_docs:
            c["metadata"]["split"] = "val"
            val.append(c)
        else:
            c["metadata"]["split"] = "train"
            train.append(c)
    return train, val, test

def main():
    a = args()
    source_dir = Path(a.source_dir).resolve()
    output_dir = Path(a.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s INFO %(message)s",
        datefmt="%H:%M:%S",
    )

    if not source_dir.exists():
        print(f"ERROR: source folder not found: {source_dir}")
        sys.exit(1)

    # STRICTLY PDF ONLY. README.md and other helper files are excluded.
    docs = sorted(p for p in source_dir.rglob("*.pdf") if p.is_file())

    if not docs:
        print("ERROR: no PDFs found.")
        print("Run DOWNLOAD_ALL_WINDOWS.cmd first.")
        sys.exit(1)

    try:
        requests.get(f"{a.ollama_url.rstrip('/')}/api/tags", timeout=10).raise_for_status()
    except Exception:
        print("ERROR: Ollama is not running. Start it with: ollama serve")
        sys.exit(1)

    progress = output_dir / "progress.jsonl"
    old = read_jsonl(progress)

    completed = {}
    for r in old:
        key = r.get("chunk_key")
        if key:
            completed[key] = completed.get(key, 0) + 1

    logging.info("Found %d SRS PDF documents.", len(docs))
    logging.info("Policy: 4 chunks/document × 4 examples/chunk = max 16 examples/document.")

    failures = []

    for doc_no, path in enumerate(docs, 1):
        rel = path.relative_to(source_dir).as_posix()
        logging.info("[%d/%d] Extracting %s", doc_no, len(docs), rel)

        try:
            text = extract_pdf(path)
            chunks = make_chunks(text)
        except Exception as e:
            logging.error("Extraction failed: %s", e)
            failures.append({"document": rel, "error": str(e)})
            continue

        if not chunks:
            logging.warning("No usable chunks for %s", rel)
            failures.append({"document": rel, "error": "No usable text"})
            continue

        logging.info("  selected %d chunk(s); maximum is 4", len(chunks))

        for chunk_no, chunk in enumerate(chunks, 1):
            key = stable_id(rel, str(chunk_no), chunk[:250])
            done = completed.get(key, 0)

            if done >= EXAMPLES_PER_CHUNK:
                logging.info("  chunk %d/%d already complete — skipping", chunk_no, len(chunks))
                continue

            logging.info(
                "  generating examples for chunk %d/%d (target=4)",
                chunk_no, len(chunks)
            )

            try:
                generated = generate_examples(
                    a.ollama_url, a.model, rel, chunk_no, chunk, a.timeout
                )
            except Exception as e:
                logging.error("Generation failed: %s", e)
                failures.append({"document": rel, "chunk": chunk_no, "error": str(e)})
                continue

            needed = EXAMPLES_PER_CHUNK - done
            rows = []
            for i, ex in enumerate(generated[:needed], start=done+1):
                rows.append({
                    "instruction": ex["instruction"],
                    "input": ex["input"],
                    "output": ex["output"],
                    "messages": [
                        {
                            "role": "user",
                            "content": ex["instruction"] + (
                                ("\n\nContext:\n" + ex["input"]) if ex["input"] else ""
                            ),
                        },
                        {"role": "assistant", "content": ex["output"]},
                    ],
                    "metadata": {
                        "dataset": "CyberSRS_SRS_4chunks",
                        "source_document": rel,
                        "source_chunk": chunk_no,
                        "example_in_chunk": i,
                        "model_used_for_generation": a.model,
                    },
                    "chunk_key": key,
                })

            append_jsonl(progress, rows)
            completed[key] = done + len(rows)
            logging.info("  accepted %d example(s)", len(rows))

    # Clean + deduplicate.
    all_rows = read_jsonl(progress)
    dedup = {}
    for r in all_rows:
        m = r.get("metadata", {})
        k = (m.get("source_document"), m.get("source_chunk"), m.get("example_in_chunk"))
        dedup[k] = r
    all_rows = list(dedup.values())

    clean_all = []
    for r in all_rows:
        c = dict(r)
        c.pop("chunk_key", None)
        clean_all.append(c)

    train, val, test = split_by_document(clean_all, a.seed)

    write_jsonl(output_dir / "all_examples.jsonl", clean_all)
    write_jsonl(output_dir / "train.jsonl", train)
    write_jsonl(output_dir / "val.jsonl", val)
    write_jsonl(output_dir / "test.jsonl", test)

    summary = {
        "pdf_documents_found": len(docs),
        "chunks_per_document_max": 4,
        "examples_per_chunk": 4,
        "max_examples_per_document": 16,
        "total_examples": len(clean_all),
        "train_examples": len(train),
        "val_examples": len(val),
        "test_examples": len(test),
        "failures": failures,
    }
    (output_dir / "dataset_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print("\n" + "="*70)
    print("SRS 4-CHUNK DATASET BUILD FINISHED")
    print("="*70)
    print(f"PDF documents found : {len(docs)}")
    print(f"Total examples      : {len(clean_all)}")
    print(f"Train               : {len(train)}")
    print(f"Validation          : {len(val)}")
    print(f"Test                : {len(test)}")
    print(f"Output folder       : {output_dir}")
    print("="*70)
    print(f"Maximum possible for the PDFs found: {len(docs)} × 4 × 4 = {len(docs)*16}")

if __name__ == "__main__":
    main()

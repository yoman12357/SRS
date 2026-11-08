#!/usr/bin/env python3
"""
CyberSRS SDLC Dataset Auditor + Fast Repair (v2)
=================================================
Purpose
-------
Repair an ALREADY-GENERATED CyberSRS SDLC dataset without regenerating all
300 examples. The script:

1) Finds train/validation/test/holdout JSONL files.
2) Makes a timestamped backup before changing anything.
3) Runs deterministic contradiction checks.
4) Uses local Ollama/Qwen in FAST BATCHES to audit scenario -> SDLC fit.
5) Regenerates ONLY rows judged inconsistent, preserving each row's original
   target SDLC family so the dataset remains balanced.
6) Re-audits repaired rows and retries weak repairs.
7) Rewrites the same 240/30/15/15 split files.
8) Writes a complete dataset_stats.json + repair_audit_report.json.

Install (if needed):
    pip install requests pypdf

Recommended command from the fine-tuning root:
    python build_sdlc_dataset.py --dataset-dir ".\\CyberSRS_SDLC_Source_Dataset\\sdlc_dataset"

If you place this script INSIDE CyberSRS_SDLC_Source_Dataset, this also works:
    python build_sdlc_dataset.py

The script does NOT rebuild all 300 rows. It keeps good rows and repairs only
bad ones, so it is much faster than the original generator.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import re
import shutil
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import requests

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


DEFAULT_MODEL = "qwen3:4b-instruct-2507-q4_K_M"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
SEED = 42
SPLITS = ("train", "validation", "test", "holdout")

METHODS = [
    "Waterfall",
    "V-Model",
    "Agile/Scrum",
    "Incremental",
    "Iterative/Evolutionary",
    "Spiral",
    "Prototyping",
    "DevOps",
    "DevSecOps",
    "Hybrid",
]

# This matrix is intentionally explicit. It prevents a generator from merely
# inserting a requested label into a scenario whose characteristics contradict it.
METHOD_GUIDE = {
    "Waterfall": (
        "Use when requirements and major interfaces are well understood and stable; "
        "change is limited/controlled; sequential phase gates, documentation and a "
        "predictable one-pass plan are valuable. Do NOT use when requirements, "
        "architecture or priorities are expected to evolve frequently."
    ),
    "V-Model": (
        "Use when requirements are comparatively stable and formal verification, "
        "validation, traceability, assurance or certification are central. Development "
        "stages should have corresponding test/validation activities. Do NOT use as "
        "the primary method for highly volatile/unclear requirements needing constant reprioritization."
    ),
    "Agile/Scrum": (
        "Use when requirements/priorities can evolve, stakeholder feedback is frequent, "
        "short iterations are useful and reprioritization is expected. Do NOT use as "
        "the clearest primary choice when requirements are frozen, feedback is absent and "
        "the project is intentionally a single sequential release."
    ),
    "Incremental": (
        "Use when useful capability can be partitioned and delivered in successive builds "
        "or rollout stages while system-level interfaces/baselines are sufficiently understood. "
        "The scenario should contain staged/module-by-module delivery or prioritised increments."
    ),
    "Iterative/Evolutionary": (
        "Use when the solution and/or some requirements mature through repeated cycles, "
        "evaluation, learning and refinement. The scenario should explicitly benefit from "
        "rework/refinement/feedback rather than a single fixed pass."
    ),
    "Spiral": (
        "Use when technical uncertainty, complexity, consequence or project risk is high and "
        "explicit risk analysis, experiments/prototypes and repeated risk-reduction cycles should drive work."
    ),
    "Prototyping": (
        "Use when key requirements, workflows, usability, feasibility or stakeholder expectations "
        "are unclear and an early proof-of-concept/prototype is needed to learn before committing to full implementation."
    ),
    "DevOps": (
        "Use when frequent reliable delivery, CI/CD automation, operations feedback, observability, "
        "infrastructure automation and rapid deployment/recovery are major drivers. Do NOT use as "
        "the clearest primary choice for rare/manual releases with no automation or operational feedback need."
    ),
    "DevSecOps": (
        "Use when DevOps-style frequent/automated delivery is needed AND security must be continuously "
        "integrated into design, build, test, deployment, monitoring and vulnerability response."
    ),
    "Hybrid": (
        "Use when genuinely conflicting lifecycle needs coexist, e.g. a stable regulated/security baseline "
        "requiring formal traceability while product/threat-facing features evolve rapidly. The scenario must "
        "make the boundaries between approaches meaningful rather than using 'hybrid' as a generic answer."
    ),
}

REPAIR_BLUEPRINTS = {
    "Waterfall": (
        "Requirements, external interfaces and acceptance criteria are baselined before implementation; "
        "stakeholder sign-off occurs at phase gates; changes after baseline are exceptional and formally controlled; "
        "a single planned production transition is acceptable."
    ),
    "V-Model": (
        "Requirements are stable/baselined; each requirement needs bidirectional traceability to verification/validation; "
        "formal assurance and documented acceptance are important; test planning begins alongside corresponding development stages."
    ),
    "Agile/Scrum": (
        "Priorities and some requirements are expected to change; stakeholders can review working increments every sprint; "
        "features can be reprioritized; short iterations and frequent feedback are valuable."
    ),
    "Incremental": (
        "The architecture and main interfaces can be established early; capabilities can be decomposed into independent useful increments; "
        "the organisation wants staged rollout with value delivered before the full system is complete."
    ),
    "Iterative/Evolutionary": (
        "The core objective is known but implementation details and some requirements will mature through repeated build-evaluate-refine cycles; "
        "measurements and stakeholder feedback from each version will shape the next version."
    ),
    "Spiral": (
        "The project has high technical/security risk and major uncertainty; each cycle must identify top risks, evaluate alternatives, "
        "prototype/experiment where necessary, validate risk reduction, and only then commit to the next investment."
    ),
    "Prototyping": (
        "Key workflows/requirements or technical feasibility are unclear; stakeholders cannot confidently specify the final solution yet; "
        "an early disposable/evolutionary prototype is needed to validate assumptions before full-scale implementation."
    ),
    "DevOps": (
        "The service needs frequent releases, automated build/test/deployment, infrastructure-as-code, observability, rapid rollback/recovery, "
        "and continuous operational feedback. Security may matter, but the defining decision driver here is delivery/operations automation."
    ),
    "DevSecOps": (
        "The service needs frequent automated releases and CI/CD, while security checks/gates, dependency scanning, secure configuration, "
        "monitoring and vulnerability response must run continuously through the delivery pipeline and operations."
    ),
    "Hybrid": (
        "A regulated/security-critical core has stable baselines, formal traceability and controlled approvals, while threat-facing/customer-facing "
        "features change frequently and benefit from short iterations/automation. The lifecycle must explicitly separate these needs and integrate them."
    ),
}

# Conservative hard contradictions. They are not the sole judge; the LLM audit
# handles nuanced cases. These patterns catch the most obvious bad rows quickly.
HARD_NEGATIVE_PATTERNS = {
    "Waterfall": [
        r"requirements? (?:are |is )?(?:evolving|evolve|change|changing) (?:weekly|monthly|frequently|continuously|rapidly)",
        r"continuous(?:ly)? (?:stakeholder|user|customer) feedback",
        r"frequent (?:stakeholder|user|customer) feedback",
        r"architecture .*?(?:evolv|chang).*?(?:during|throughout) development",
        r"requirements? (?:are |is )?(?:unclear|undefined|not well[- ]defined|ambiguous)",
        r"mvp\b.*?(?:iterate|feedback|evolv)",
    ],
    "V-Model": [
        r"requirements? (?:are |is )?(?:evolving|evolve|change|changing) (?:weekly|monthly|frequently|continuously|rapidly)",
        r"requirements? (?:are |is )?(?:unclear|undefined|not well[- ]defined|ambiguous)",
        r"continuous(?:ly)? (?:stakeholder|user|customer) feedback.*?(?:repriorit|change)",
    ],
    "Agile/Scrum": [
        r"requirements? (?:are |is )?(?:fixed|frozen|fully defined|stable).*?(?:no|without) (?:expected )?changes?",
        r"no (?:user|customer|stakeholder) feedback",
        r"minimal (?:user|customer|stakeholder) feedback.*?requirements? (?:are |is )?(?:fixed|stable)",
        r"single (?:planned )?(?:release|deployment).*?no (?:future )?changes?",
    ],
    "Iterative/Evolutionary": [
        r"requirements? (?:are |is )?(?:fixed|frozen|fully defined|stable).*?no (?:planned |expected )?(?:change|refinement|feedback)",
        r"no (?:user|customer|stakeholder) feedback.*?no (?:planned |expected )?changes?",
    ],
    "Prototyping": [
        r"requirements? (?:are |is )?(?:fully defined|well defined|fixed|frozen).*?no (?:uncertainty|unknowns|changes)",
        r"technical feasibility (?:is )?(?:already )?(?:proven|known).*?requirements? (?:are |is )?(?:stable|fixed)",
    ],
    "DevOps": [
        r"(?:changes|releases|deployments) (?:are |occur )?(?:rare|infrequent).*?(?:manual|no automation)",
        r"no (?:ci/?cd|deployment automation|operational feedback|observability)",
        r"updated via scheduled patches, not code changes",
    ],
    "DevSecOps": [
        r"(?:changes|releases|deployments) (?:are |occur )?(?:rare|infrequent).*?no (?:automation|ci/?cd)",
    ],
}

REQUIRED_LABELS = [
    "Recommended SDLC:",
    "Decision factors:",
    "Why it fits:",
    "Requirement-to-lifecycle mapping:",
    "Security integration:",
    "Why alternatives are less suitable:",
]

SOURCE_PREFERENCES = {
    "Waterfall": ["NASA_Software_Engineering_Guidebook", "NASA_Systems_Engineering_Handbook"],
    "V-Model": ["NASA_Software_Engineering_Guidebook", "NASA_Systems_Engineering_Handbook"],
    "Agile/Scrum": ["GAO_24-105506_Agile_Assessment_Guide", "NASA_Software_Engineering_Guidebook"],
    "Incremental": ["NASA_Software_Engineering_Guidebook", "NASA_Systems_Engineering_Handbook"],
    "Iterative/Evolutionary": ["NASA_Software_Engineering_Guidebook", "NASA_Systems_Engineering_Handbook"],
    "Spiral": ["NASA_Software_Engineering_Guidebook", "NASA_Systems_Engineering_Handbook"],
    "Prototyping": ["NASA_Software_Engineering_Guidebook", "NASA_Systems_Engineering_Handbook"],
    "DevOps": ["NASA_Software_Engineering_Guidebook", "OWASP_Developer_Guide"],
    "DevSecOps": ["NIST_SP_800-218_SSDF_v1.1", "OWASP_Developer_Guide", "NIST_SP_800-160v1r1"],
    "Hybrid": ["NIST_SP_800-218_SSDF_v1.1", "NASA_Software_Engineering_Guidebook", "GAO_24-105506_Agile_Assessment_Guide"],
}

METHOD_TERMS = {
    "Waterfall": ["waterfall", "sequential", "phase", "requirements", "verification", "validation"],
    "V-Model": ["verification", "validation", "traceability", "requirements", "test", "assurance"],
    "Agile/Scrum": ["agile", "scrum", "iteration", "increment", "feedback", "backlog"],
    "Incremental": ["incremental", "increment", "build", "delivery", "phase"],
    "Iterative/Evolutionary": ["iterative", "evolutionary", "iteration", "refinement", "feedback"],
    "Spiral": ["spiral", "risk", "prototype", "iteration", "uncertainty"],
    "Prototyping": ["prototype", "prototyping", "feasibility", "requirements", "evaluation"],
    "DevOps": ["devops", "continuous integration", "continuous delivery", "deployment", "operations", "automation"],
    "DevSecOps": ["secure software development", "security", "continuous", "development", "deployment", "vulnerability"],
    "Hybrid": ["life cycle", "agile", "risk", "requirements", "security", "verification"],
}


def setup_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def normalize_method(raw: str) -> Optional[str]:
    low = re.sub(r"[^a-z0-9]+", " ", raw.lower()).strip()
    aliases = {
        "waterfall": "Waterfall",
        "v model": "V-Model",
        "vmodel": "V-Model",
        "agile scrum": "Agile/Scrum",
        "agile": "Agile/Scrum",
        "scrum": "Agile/Scrum",
        "incremental": "Incremental",
        "iterative evolutionary": "Iterative/Evolutionary",
        "iterative": "Iterative/Evolutionary",
        "evolutionary": "Iterative/Evolutionary",
        "spiral": "Spiral",
        "prototyping": "Prototyping",
        "prototype": "Prototyping",
        "devops": "DevOps",
        "devsecops": "DevSecOps",
        "hybrid": "Hybrid",
    }
    if low in aliases:
        return aliases[low]
    # Accept labels such as "Hybrid (Agile + V-Model)" while keeping family.
    for k, v in aliases.items():
        if re.search(rf"\b{re.escape(k)}\b", low):
            return v
    return None


def extract_recommended_method(assistant: str) -> Optional[str]:
    m = re.search(r"Recommended SDLC:\s*([^\n\r]+)", assistant, flags=re.I)
    if not m:
        return None
    return normalize_method(m.group(1))


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except Exception as exc:
                raise ValueError(f"Invalid JSON in {path} line {line_no}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def row_text(record: Dict[str, Any]) -> Tuple[str, str]:
    msgs = record.get("messages")
    if not isinstance(msgs, list) or len(msgs) < 2:
        return "", ""
    user = ""
    assistant = ""
    for msg in msgs:
        if msg.get("role") == "user" and not user:
            user = str(msg.get("content", "")).strip()
        elif msg.get("role") == "assistant" and not assistant:
            assistant = str(msg.get("content", "")).strip()
    return user, assistant


def structural_validate(record: Dict[str, Any], expected_method: Optional[str] = None) -> Tuple[bool, str]:
    user, assistant = row_text(record)
    if len(user) < 80:
        return False, "user prompt too short"
    if len(assistant) < 500:
        return False, "assistant answer too short"
    for label in REQUIRED_LABELS:
        if label.lower() not in assistant.lower():
            return False, f"missing section {label}"
    method = extract_recommended_method(assistant)
    if method is None:
        return False, "cannot parse Recommended SDLC"
    if expected_method and method != expected_method:
        return False, f"recommended method changed to {method}; expected {expected_method}"
    lifecycle_terms = ["requirement", "design", "implement", "test", "deploy", "maint"]
    if sum(t in assistant.lower() for t in lifecycle_terms) < 5:
        return False, "insufficient lifecycle mapping"
    return True, "ok"


def hard_contradictions(user: str, method: str) -> List[str]:
    low = re.sub(r"\s+", " ", user.lower())
    reasons: List[str] = []
    for pat in HARD_NEGATIVE_PATTERNS.get(method, []):
        if re.search(pat, low, flags=re.I):
            reasons.append(pat)

    # Positive requirements for methods whose defining signal must be explicit.
    if method == "Incremental":
        if not re.search(r"\b(increment|phase|stage|module|roll.?out|successive|first .* then|release .* capability)\b", low):
            reasons.append("no explicit staged/incremental delivery signal")
    elif method == "Iterative/Evolutionary":
        if not re.search(r"\b(iterat|refin|feedback|learn|evolv|repeated|cycle|version)\w*\b", low):
            reasons.append("no explicit build-evaluate-refine signal")
    elif method == "Spiral":
        if not re.search(r"\b(high[- ]risk|uncertain|uncertainty|unknown|novel|complex|prototype|experiment|feasibility|risk)\w*\b", low):
            reasons.append("no strong uncertainty/risk signal")
    elif method == "Prototyping":
        if not re.search(r"\b(unclear|uncertain|unknown|not well[- ]defined|ambiguous|prototype|proof[- ]of[- ]concept|feasibility|validate .* assumption|unsure)\b", low):
            reasons.append("no unclear-requirement/feasibility signal")
    elif method == "DevOps":
        if not re.search(r"\b(ci/?cd|continuous (?:integration|delivery|deployment)|automated? (?:build|test|deploy)|frequent releases?|deploy .* (?:daily|weekly)|observability|infrastructure[- ]as[- ]code|rapid rollback|operations feedback)\b", low):
            reasons.append("no strong delivery/operations automation signal")
    elif method == "DevSecOps":
        delivery = re.search(r"\b(ci/?cd|continuous (?:integration|delivery|deployment)|automated? (?:build|test|deploy)|frequent releases?|deploy .* (?:daily|weekly|bi-weekly|monthly)|pipeline)\b", low)
        security = re.search(r"\b(security|vulnerab|threat|secure|scan|policy|compliance|attack|monitor)\w*\b", low)
        if not delivery or not security:
            reasons.append("DevSecOps requires both automated/frequent delivery and continuous security signals")
    elif method == "Hybrid":
        stable = re.search(r"\b(stable|fixed|baseline|regulated|compliance|traceability|formal|audit|certif)\w*\b", low)
        dynamic = re.search(r"\b(evolv|chang|feedback|iterat|frequent release|rapid|weekly|monthly|emerging threat|repriorit)\w*\b", low)
        if not stable or not dynamic:
            reasons.append("Hybrid scenario lacks both stable/formal and dynamic/iterative pressures")

    return reasons


def ollama_json(url: str, model: str, system: str, prompt: str, timeout: int,
                retries: int, temperature: float = 0.0) -> Dict[str, Any]:
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": temperature,
            "top_p": 0.9,
            "num_ctx": 32768,
        },
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, json=payload, timeout=timeout)
            r.raise_for_status()
            raw = r.json()["message"]["content"].strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
            raw = re.sub(r"\s*```$", "", raw)
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                a, b = raw.find("{"), raw.rfind("}")
                if a >= 0 and b > a:
                    return json.loads(raw[a:b + 1])
                raise
        except Exception as exc:
            if attempt >= retries:
                raise
            wait = min(20, 3 * attempt)
            logging.warning("Ollama attempt %d/%d failed: %s; retrying in %ds", attempt, retries, exc, wait)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def audit_prompt(items: Sequence[Dict[str, Any]]) -> str:
    matrix = "\n".join(f"- {m}: {METHOD_GUIDE[m]}" for m in METHODS)
    compact = [
        {
            "id": x["id"],
            "scenario": x["user"],
            "current_recommendation": x["method"],
        }
        for x in items
    ]
    return f"""Audit SDLC training labels. Judge the PROJECT SCENARIO, not whether the written answer sounds confident.

DECISION MATRIX
{matrix}

RULES
- A recommendation is VALID only when it is genuinely among the best lifecycle choices for the stated scenario.
- Security alone does not automatically imply V-Model or DevSecOps.
- Waterfall/V-Model require relative requirement stability; frequent evolution/continuous reprioritization is a contradiction.
- Agile requires meaningful change/feedback/iteration.
- Incremental requires staged capability delivery.
- Iterative/Evolutionary requires repeated learning/refinement.
- Spiral requires high risk/uncertainty with explicit risk-driven cycles.
- Prototyping requires unclear requirements/feasibility/workflow needing early validation.
- DevOps requires frequent/automated delivery + operational feedback.
- DevSecOps requires those DevOps drivers PLUS continuous security integration.
- Hybrid requires two genuinely conflicting lifecycle needs with explicit boundaries.
- Do not accept a label just to preserve class balance.

Return JSON only:
{{
  "results": [
    {{"id": "...", "valid": true, "best_method": "one canonical family", "issue": "short reason"}}
  ]
}}

Canonical families: {json.dumps(METHODS)}

ITEMS:
{json.dumps(compact, ensure_ascii=False)}
"""


def llm_audit(items: Sequence[Dict[str, Any]], args: argparse.Namespace) -> Dict[str, Dict[str, Any]]:
    results: Dict[str, Dict[str, Any]] = {}
    total = len(items)
    for start in range(0, total, args.audit_batch_size):
        batch = items[start:start + args.audit_batch_size]
        logging.info("LLM audit %d-%d/%d", start + 1, min(start + len(batch), total), total)
        try:
            obj = ollama_json(
                args.ollama_url,
                args.model,
                "You are a strict software-lifecycle dataset quality auditor. Return only the requested JSON.",
                audit_prompt(batch),
                args.timeout,
                args.retries,
                temperature=0.0,
            )
            outs = obj.get("results", [])
            if not isinstance(outs, list):
                raise ValueError("results is not a list")
            for out in outs:
                iid = str(out.get("id", ""))
                if iid:
                    bm = normalize_method(str(out.get("best_method", "")))
                    results[iid] = {
                        "valid": bool(out.get("valid", False)),
                        "best_method": bm,
                        "issue": str(out.get("issue", "")).strip(),
                    }
        except Exception as exc:
            logging.warning("Audit batch failed (%s). These rows will be conservatively repaired if hard rules fail.", exc)
    return results


def find_dataset_dir(explicit: Optional[Path], script_dir: Path) -> Path:
    candidates: List[Path] = []
    if explicit:
        candidates.append(explicit.resolve())
    candidates += [
        script_dir / "sdlc_dataset",
        script_dir,
        script_dir / "CyberSRS_SDLC_Source_Dataset" / "sdlc_dataset",
        script_dir.parent / "CyberSRS_SDLC_Source_Dataset" / "sdlc_dataset",
    ]
    # Recursive discovery is useful when ZIP extraction created an extra nested folder.
    try:
        candidates += [p for p in script_dir.rglob("sdlc_dataset") if p.is_dir()]
    except Exception:
        pass
    try:
        cwd = Path.cwd().resolve()
        if cwd != script_dir:
            candidates += [p for p in cwd.rglob("sdlc_dataset") if p.is_dir()]
    except Exception:
        pass
    seen = set()
    for c in candidates:
        c = c.resolve()
        if c in seen:
            continue
        seen.add(c)
        if all((c / f"{s}.jsonl").exists() for s in SPLITS):
            return c
    raise FileNotFoundError(
        "Could not find train.jsonl, validation.jsonl, test.jsonl and holdout.jsonl. "
        "Pass --dataset-dir explicitly."
    )


def find_source_dir(explicit: Optional[Path], dataset_dir: Path, script_dir: Path) -> Optional[Path]:
    candidates: List[Path] = []
    if explicit:
        candidates.append(explicit.resolve())
    candidates += [
        dataset_dir.parent / "SDLC_Source_Documents",
        script_dir / "SDLC_Source_Documents",
        script_dir / "CyberSRS_SDLC_Source_Dataset" / "SDLC_Source_Documents",
        script_dir.parent / "CyberSRS_SDLC_Source_Dataset" / "SDLC_Source_Documents",
    ]
    for c in candidates:
        if c.exists() and any(c.glob("*.pdf")):
            return c.resolve()
    # Recursive fallback for an extra ZIP nesting level.
    for root in [script_dir, dataset_dir.parent]:
        try:
            for c in root.rglob("SDLC_Source_Documents"):
                if c.is_dir() and any(c.glob("*.pdf")):
                    return c.resolve()
        except Exception:
            pass
    return None


def backup_dataset(dataset_dir: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = dataset_dir.parent / f"{dataset_dir.name}_backup_before_repair_{stamp}"
    backup.mkdir(parents=True, exist_ok=False)
    for name in SPLITS:
        for suffix in (".jsonl", "_provenance.jsonl"):
            p = dataset_dir / f"{name}{suffix}"
            if p.exists():
                shutil.copy2(p, backup / p.name)
    for extra in ("dataset_stats.json", "_accepted_checkpoint.jsonl"):
        p = dataset_dir / extra
        if p.exists():
            shutil.copy2(p, backup / p.name)
    return backup


def split_into_chunks(text: str, size: int = 4500, overlap: int = 400) -> List[str]:
    text = re.sub(r"[ \t]+", " ", text)
    chunks = []
    pos = 0
    while pos < len(text):
        end = min(len(text), pos + size)
        piece = text[pos:end].strip()
        if len(piece) > 500:
            chunks.append(piece)
        if end >= len(text):
            break
        pos = max(pos + 1, end - overlap)
    return chunks


def build_source_bank(source_dir: Optional[Path]) -> Dict[str, str]:
    if source_dir is None or PdfReader is None:
        return {}
    pdf_texts: Dict[str, str] = {}
    for pdf in sorted(source_dir.glob("*.pdf")):
        try:
            logging.info("Reading trusted source for repair grounding: %s", pdf.name)
            reader = PdfReader(str(pdf))
            txt = "\n".join((p.extract_text() or "") for p in reader.pages)
            pdf_texts[pdf.stem] = txt
        except Exception as exc:
            logging.warning("Could not read %s: %s", pdf.name, exc)

    bank: Dict[str, str] = {}
    for method in METHODS:
        candidates: List[Tuple[int, str]] = []
        prefs = SOURCE_PREFERENCES[method]
        terms = METHOD_TERMS[method]
        for stem, text in pdf_texts.items():
            pref_bonus = 20 if any(pref.lower() in stem.lower() for pref in prefs) else 0
            for chunk in split_into_chunks(text):
                low = chunk.lower()
                score = pref_bonus + sum(low.count(t.lower()) * 3 for t in terms)
                if score > 0:
                    candidates.append((score, chunk))
        candidates.sort(key=lambda x: x[0], reverse=True)
        if candidates:
            bank[method] = candidates[0][1][:2600]
    return bank


def repair_prompt(batch: Sequence[Dict[str, Any]], source_bank: Dict[str, str]) -> str:
    payload = []
    for item in batch:
        method = item["method"]
        payload.append({
            "id": item["id"],
            "target_method": method,
            "original_scenario": item["user"],
            "mandatory_blueprint": REPAIR_BLUEPRINTS[method],
            "trusted_excerpt": source_bank.get(method, ""),
        })
    return f"""Repair mislabeled SDLC supervised-fine-tuning examples for CyberSRS.

For EACH item, keep the same cybersecurity/network project domain, but rewrite the project scenario's lifecycle-driving characteristics so TARGET_METHOD is genuinely appropriate. Then write a fresh assistant answer consistent with the rewritten scenario.

NON-NEGOTIABLE RULES
- Follow mandatory_blueprint exactly in substance; do not insert characteristics that contradict it.
- Do NOT tell the user the answer inside the scenario.
- Scenario: realistic 2-5 sentences and at least 100 characters.
- Assistant: approximately 180-350 words.
- Assistant MUST contain these exact section labels:
  Recommended SDLC:
  Decision factors:
  Why it fits:
  Requirement-to-lifecycle mapping:
  Security integration:
  Why alternatives are less suitable:
- Recommended SDLC must exactly use TARGET_METHOD.
- Lifecycle mapping must cover requirements, architecture/design, implementation, verification/testing, deployment/transition, and operations/maintenance; include feedback/change management when method-appropriate.
- Security practices should be integrated sensibly, but security alone must not be used to justify the lifecycle.
- Use the trusted excerpt only as grounding context; paraphrase it. Do not mention source names or invent clauses/certifications/numbers.
- Make items materially different.

Return JSON only:
{{
  "examples": [
    {{"id": "...", "user": "...", "assistant": "...", "recommended_sdlc": "..."}}
  ]
}}

ITEMS:
{json.dumps(payload, ensure_ascii=False)}
"""


def make_record(user: str, assistant: str) -> Dict[str, Any]:
    return {
        "messages": [
            {"role": "user", "content": user.strip()},
            {"role": "assistant", "content": assistant.strip()},
        ]
    }


def repair_items(items: List[Dict[str, Any]], source_bank: Dict[str, str],
                 args: argparse.Namespace) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    repaired: Dict[str, Dict[str, Any]] = {}
    failed: List[str] = []

    for start in range(0, len(items), args.repair_batch_size):
        batch = items[start:start + args.repair_batch_size]
        logging.info("Repairing %d-%d/%d", start + 1, min(start + len(batch), len(items)), len(items))
        try:
            obj = ollama_json(
                args.ollama_url,
                args.model,
                "You repair SDLC fine-tuning data. Obey lifecycle decision constraints and return only JSON.",
                repair_prompt(batch, source_bank),
                args.timeout,
                args.retries,
                temperature=0.35,
            )
            outputs = obj.get("examples", [])
            if not isinstance(outputs, list):
                raise ValueError("examples is not a list")
            by_id = {str(x.get("id", "")): x for x in outputs if isinstance(x, dict)}
        except Exception as exc:
            logging.warning("Repair batch failed: %s", exc)
            by_id = {}

        for item in batch:
            iid = item["id"]
            out = by_id.get(iid)
            if not out:
                failed.append(iid)
                continue
            method = normalize_method(str(out.get("recommended_sdlc", "")))
            if method != item["method"]:
                failed.append(iid)
                continue
            rec = make_record(str(out.get("user", "")), str(out.get("assistant", "")))
            ok, reason = structural_validate(rec, item["method"])
            if not ok:
                logging.warning("Repair %s rejected structurally: %s", iid, reason)
                failed.append(iid)
                continue
            user, _ = row_text(rec)
            contradictions = hard_contradictions(user, item["method"])
            if contradictions:
                logging.warning("Repair %s still conflicts with %s: %s", iid, item["method"], contradictions[:2])
                failed.append(iid)
                continue
            repaired[iid] = rec

    return repaired, failed


def strict_single_repair(item: Dict[str, Any], source_bank: Dict[str, str],
                         args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    # More explicit one-item retry for stubborn generations.
    method = item["method"]
    prompt = f"""Create ONE corrected CyberSRS training example.
TARGET METHOD: {method}
MANDATORY SCENARIO CHARACTERISTICS: {REPAIR_BLUEPRINTS[method]}
PROJECT DOMAIN TO RETAIN: {item['user']}
TRUSTED GROUNDING EXCERPT: {source_bank.get(method, '')}

Do not contradict the mandatory characteristics. Do not reveal the method in the user scenario.
Return JSON only:
{{"examples":[{{"id":"{item['id']}","user":"2-5 sentence scenario","assistant":"Recommended SDLC: {method}\\n\\nDecision factors: ...\\n\\nWhy it fits: ...\\n\\nRequirement-to-lifecycle mapping: ...\\n\\nSecurity integration: ...\\n\\nWhy alternatives are less suitable: ...","recommended_sdlc":"{method}"}}]}}
The assistant must be 180-350 words and map requirements, design, implementation, testing, deployment and maintenance.
"""
    try:
        obj = ollama_json(
            args.ollama_url, args.model,
            "Return exactly one high-quality valid JSON training example.",
            prompt, args.timeout, args.retries, temperature=0.2,
        )
        exs = obj.get("examples", [])
        if not exs:
            return None
        ex = exs[0]
        rec = make_record(str(ex.get("user", "")), str(ex.get("assistant", "")))
        ok, _ = structural_validate(rec, method)
        if not ok:
            return None
        u, _ = row_text(rec)
        if hard_contradictions(u, method):
            return None
        return rec
    except Exception:
        return None


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description="Audit and fast-repair an existing CyberSRS SDLC dataset")
    p.add_argument("--dataset-dir", type=Path, default=None,
                   help="Folder containing train/validation/test/holdout.jsonl")
    p.add_argument("--source-dir", type=Path, default=None,
                   help="Optional trusted PDF folder; auto-detected when possible")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    p.add_argument("--audit-batch-size", type=int, default=10)
    p.add_argument("--repair-batch-size", type=int, default=4)
    p.add_argument("--timeout", type=int, default=360)
    p.add_argument("--retries", type=int, default=3)
    p.add_argument("--skip-llm-audit", action="store_true",
                   help="Only use deterministic contradiction rules (faster, less thorough)")
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()


def main() -> int:
    print("CyberSRS SDLC Repair v2 STARTING...", flush=True)
    args = parse_args()
    setup_logging(args.verbose)
    random.seed(SEED)
    script_dir = Path(__file__).resolve().parent

    try:
        dataset_dir = find_dataset_dir(args.dataset_dir, script_dir)
    except Exception as exc:
        logging.error("%s", exc)
        return 2

    logging.info("Dataset directory: %s", dataset_dir)

    # Ollama check before touching original files.
    base_url = args.ollama_url.rsplit("/api/", 1)[0]
    try:
        requests.get(base_url + "/api/tags", timeout=10).raise_for_status()
    except Exception as exc:
        logging.error("Cannot reach Ollama at %s: %s", base_url, exc)
        logging.error("Start Ollama, then rerun the command.")
        return 3

    # Load rows and optional per-split provenance.
    split_rows: Dict[str, List[Dict[str, Any]]] = {}
    provenance_rows: Dict[str, List[Dict[str, Any]]] = {}
    items: List[Dict[str, Any]] = []
    structural_bad: List[str] = []

    for split in SPLITS:
        rows = read_jsonl(dataset_dir / f"{split}.jsonl")
        split_rows[split] = rows
        prov_path = dataset_dir / f"{split}_provenance.jsonl"
        if prov_path.exists():
            provenance_rows[split] = read_jsonl(prov_path)
        else:
            provenance_rows[split] = [{} for _ in rows]

        if len(provenance_rows[split]) != len(rows):
            logging.warning("%s provenance count mismatch; provenance will be rebuilt minimally.", split)
            provenance_rows[split] = [{} for _ in rows]

        for idx, rec in enumerate(rows):
            iid = f"{split}:{idx}"
            user, assistant = row_text(rec)
            method = extract_recommended_method(assistant)
            ok, reason = structural_validate(rec)
            if not ok or method is None:
                structural_bad.append(iid)
                # If label cannot be parsed, use provenance if possible.
                pm = normalize_method(str(provenance_rows[split][idx].get("recommended_sdlc", "")))
                method = method or pm
            if method is None:
                logging.error("Cannot determine SDLC family for %s; refusing to guess.", iid)
                return 4
            items.append({
                "id": iid,
                "split": split,
                "index": idx,
                "record": rec,
                "user": user,
                "assistant": assistant,
                "method": method,
                "structural_ok": ok,
                "structural_reason": reason,
                "hard_reasons": hard_contradictions(user, method),
            })

    total = len(items)
    counts = {s: len(split_rows[s]) for s in SPLITS}
    logging.info("Loaded %d rows: %s", total, counts)
    logging.info("Current method distribution: %s", dict(sorted(Counter(x['method'] for x in items).items())))

    # Backup exactly once per run.
    backup = backup_dataset(dataset_dir)
    logging.info("Backup created: %s", backup)

    # Fast batch audit of scenario -> method fit.
    audit_results: Dict[str, Dict[str, Any]] = {}
    if not args.skip_llm_audit:
        audit_results = llm_audit(items, args)

    to_repair: List[Dict[str, Any]] = []
    audit_report_rows: List[Dict[str, Any]] = []
    for item in items:
        llm = audit_results.get(item["id"])
        hard_fail = bool(item["hard_reasons"])
        structural_fail = not item["structural_ok"]
        llm_fail = (llm is not None and not llm.get("valid", False))
        missing_llm = (not args.skip_llm_audit and llm is None)

        # Missing LLM audit alone does not force repair when deterministic + structure pass;
        # this prevents network glitches from causing unnecessary regeneration.
        repair = structural_fail or hard_fail or llm_fail
        item["repair_reason"] = {
            "structural": item["structural_reason"] if structural_fail else "ok",
            "hard_rule_reasons": item["hard_reasons"],
            "llm": llm,
            "llm_missing": missing_llm,
        }
        if repair:
            to_repair.append(item)
        audit_report_rows.append({
            "id": item["id"],
            "split": item["split"],
            "index": item["index"],
            "method": item["method"],
            "needs_repair": repair,
            "reason": item["repair_reason"],
        })

    logging.info("Audit complete: keeping %d rows; repairing %d rows.", total - len(to_repair), len(to_repair))

    source_dir = find_source_dir(args.source_dir, dataset_dir, script_dir)
    if source_dir:
        logging.info("Trusted source directory: %s", source_dir)
    else:
        logging.warning("Trusted PDFs not found. Repairs will use the strict decision matrix but no PDF excerpt.")
    source_bank = build_source_bank(source_dir)

    repaired, failed = repair_items(to_repair, source_bank, args)

    # Retry failed repairs one-by-one with a stricter prompt.
    if failed:
        lookup = {x["id"]: x for x in to_repair}
        logging.info("Retrying %d stubborn repairs individually.", len(failed))
        still_failed: List[str] = []
        for n, iid in enumerate(failed, 1):
            logging.info("Strict retry %d/%d: %s", n, len(failed), iid)
            rec = strict_single_repair(lookup[iid], source_bank, args)
            if rec is None:
                still_failed.append(iid)
            else:
                repaired[iid] = rec
        failed = still_failed

    if failed:
        logging.error("Could not produce safe replacements for %d rows: %s", len(failed), failed[:20])
        logging.error("Original dataset has NOT been overwritten. Backup: %s", backup)
        return 5

    # Second LLM audit ONLY on repaired rows. This is cheap and catches repair drift.
    repaired_items: List[Dict[str, Any]] = []
    original_lookup = {x["id"]: x for x in items}
    for iid, rec in repaired.items():
        u, a = row_text(rec)
        repaired_items.append({
            "id": iid,
            "user": u,
            "assistant": a,
            "method": original_lookup[iid]["method"],
        })

    if repaired_items and not args.skip_llm_audit:
        logging.info("Final audit of %d repaired rows...", len(repaired_items))
        final_audit = llm_audit(repaired_items, args)
        bad_after = []
        for item in repaired_items:
            out = final_audit.get(item["id"])
            if out is not None and not out.get("valid", False):
                bad_after.append(item["id"])
        if bad_after:
            logging.info("%d repaired rows failed final audit; applying one last strict retry.", len(bad_after))
            for iid in bad_after:
                rec = strict_single_repair(original_lookup[iid], source_bank, args)
                if rec is None:
                    logging.error("Final strict retry failed for %s. Dataset not overwritten.", iid)
                    return 6
                repaired[iid] = rec

    # Apply replacements, preserve original split assignment and row count.
    for iid, rec in repaired.items():
        item = original_lookup[iid]
        split_rows[item["split"]][item["index"]] = rec
        prov = provenance_rows[item["split"]][item["index"]]
        if not isinstance(prov, dict):
            prov = {}
        prov = dict(prov)
        prov["recommended_sdlc"] = item["method"]
        prov["repair_applied"] = True
        prov["repair_model"] = args.model
        prov["repair_timestamp"] = datetime.now().isoformat(timespec="seconds")
        provenance_rows[item["split"]][item["index"]] = prov

    # Final deterministic validation + no exact duplicate prompts.
    seen_users = set()
    final_methods = Counter()
    for split in SPLITS:
        for idx, rec in enumerate(split_rows[split]):
            user, assistant = row_text(rec)
            method = extract_recommended_method(assistant)
            ok, reason = structural_validate(rec)
            if not ok or method is None:
                logging.error("Final validation failed at %s:%d: %s", split, idx, reason)
                return 7
            hard = hard_contradictions(user, method)
            if hard:
                logging.error("Final contradiction check failed at %s:%d (%s): %s", split, idx, method, hard)
                return 8
            key = re.sub(r"\W+", " ", user.lower()).strip()
            if key in seen_users:
                logging.error("Duplicate user scenario detected at %s:%d", split, idx)
                return 9
            seen_users.add(key)
            final_methods[method] += 1

    # Overwrite only after every final check passes.
    for split in SPLITS:
        write_jsonl(dataset_dir / f"{split}.jsonl", split_rows[split])
        write_jsonl(dataset_dir / f"{split}_provenance.jsonl", provenance_rows[split])

    stats = {
        "target": total,
        "generated": total,
        "split": {s: len(split_rows[s]) for s in SPLITS},
        "method_counts": dict(sorted(final_methods.items())),
        "model": args.model,
        "seed": SEED,
        "repair": {
            "kept_unchanged": total - len(repaired),
            "repaired": len(repaired),
            "audited_with_llm": not args.skip_llm_audit,
            "backup_dir": str(backup),
        },
    }
    (dataset_dir / "dataset_stats.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    report = {
        "dataset_dir": str(dataset_dir),
        "total_rows": total,
        "rows_flagged_initially": len(to_repair),
        "rows_repaired": len(repaired),
        "method_counts": dict(sorted(final_methods.items())),
        "items": audit_report_rows,
    }
    (dataset_dir / "repair_audit_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    logging.info("=" * 72)
    logging.info("DONE - SDLC DATASET REPAIRED AND VALIDATED")
    logging.info("Rows kept unchanged: %d", total - len(repaired))
    logging.info("Rows repaired:       %d", len(repaired))
    logging.info("Split: train=%d validation=%d test=%d holdout=%d",
                 *(len(split_rows[s]) for s in SPLITS))
    logging.info("Method counts: %s", dict(sorted(final_methods.items())))
    logging.info("Output: %s", dataset_dir)
    logging.info("Backup: %s", backup)
    logging.info("Send me the 4 JSONL files + dataset_stats.json for final GREEN FLAG.")
    logging.info("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())

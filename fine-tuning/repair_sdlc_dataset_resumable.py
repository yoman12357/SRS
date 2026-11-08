#!/usr/bin/env python3
"""Resumable CyberSRS SDLC repair runner.

Place this file in the same folder as repair_sdlc_dataset.py and run:
    python repair_sdlc_dataset_resumable.py

It checkpoints after the audit and after every successful strict repair, so a
Ctrl+C / reboot will not lose completed repairs on the NEXT run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import random
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests

try:
    import repair_sdlc_dataset as base
except ImportError:
    print("ERROR: Put this file next to repair_sdlc_dataset.py", flush=True)
    raise

CHECKPOINT_NAME = "_repair_resume_checkpoint.json"
MAX_QUALITY_PASSES = 3


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dataset_signature(dataset_dir: Path) -> Dict[str, str]:
    return {s: file_sha256(dataset_dir / f"{s}.jsonl") for s in base.SPLITS}


def save_checkpoint(path: Path, data: Dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def load_checkpoint(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_items(dataset_dir: Path):
    split_rows: Dict[str, List[Dict[str, Any]]] = {}
    provenance_rows: Dict[str, List[Dict[str, Any]]] = {}
    items: List[Dict[str, Any]] = []

    for split in base.SPLITS:
        rows = base.read_jsonl(dataset_dir / f"{split}.jsonl")
        split_rows[split] = rows
        prov_path = dataset_dir / f"{split}_provenance.jsonl"
        if prov_path.exists():
            provenance_rows[split] = base.read_jsonl(prov_path)
        else:
            provenance_rows[split] = [{} for _ in rows]
        if len(provenance_rows[split]) != len(rows):
            provenance_rows[split] = [{} for _ in rows]

        for idx, rec in enumerate(rows):
            iid = f"{split}:{idx}"
            user, assistant = base.row_text(rec)
            method = base.extract_recommended_method(assistant)
            ok, reason = base.structural_validate(rec)
            if method is None:
                pm = base.normalize_method(str(provenance_rows[split][idx].get("recommended_sdlc", "")))
                method = pm
            if method is None:
                raise RuntimeError(f"Cannot determine SDLC family for {iid}")
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
                "hard_reasons": base.hard_contradictions(user, method),
            })
    return split_rows, provenance_rows, items


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Resumable CyberSRS SDLC repair")
    p.add_argument("--dataset-dir", type=Path, default=None)
    p.add_argument("--source-dir", type=Path, default=None)
    p.add_argument("--model", default=base.DEFAULT_MODEL)
    p.add_argument("--ollama-url", default=base.DEFAULT_OLLAMA_URL)
    p.add_argument("--audit-batch-size", type=int, default=10)
    p.add_argument("--repair-batch-size", type=int, default=4)  # compatibility
    p.add_argument("--timeout", type=int, default=360)
    p.add_argument("--retries", type=int, default=3)
    p.add_argument("--skip-llm-audit", action="store_true")
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()


def main() -> int:
    print("CyberSRS SDLC Repair RESUMABLE v3 STARTING...", flush=True)
    args = parse_args()
    base.setup_logging(args.verbose)
    random.seed(base.SEED)
    script_dir = Path(__file__).resolve().parent

    try:
        dataset_dir = base.find_dataset_dir(args.dataset_dir, script_dir)
    except Exception as exc:
        logging.error("%s", exc)
        return 2
    logging.info("Dataset directory: %s", dataset_dir)

    base_url = args.ollama_url.rsplit("/api/", 1)[0]
    try:
        requests.get(base_url + "/api/tags", timeout=10).raise_for_status()
    except Exception as exc:
        logging.error("Cannot reach Ollama at %s: %s", base_url, exc)
        return 3

    split_rows, provenance_rows, items = build_items(dataset_dir)
    item_lookup = {x["id"]: x for x in items}
    sig = dataset_signature(dataset_dir)
    cp_path = dataset_dir / CHECKPOINT_NAME
    cp = load_checkpoint(cp_path)

    if cp:
        if cp.get("dataset_signature") != sig:
            logging.error("Checkpoint belongs to different dataset files. Rename/delete %s before continuing.", cp_path)
            return 4
        logging.info("RESUME checkpoint found: %d repairs already saved.", len(cp.get("repaired", {})))
    else:
        backup = base.backup_dataset(dataset_dir)
        cp = {
            "version": 3,
            "dataset_signature": sig,
            "backup_dir": str(backup),
            "audit_complete": False,
            "to_repair_ids": [],
            "audit_report_rows": [],
            "repaired": {},
            "failed_attempts": {},
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        save_checkpoint(cp_path, cp)
        logging.info("Backup created: %s", backup)
        logging.info("Checkpoint created: %s", cp_path)

    # Audit once, then checkpoint the exact repair list.
    if not cp.get("audit_complete", False):
        audit_results = {} if args.skip_llm_audit else base.llm_audit(items, args)
        to_repair_ids: List[str] = []
        report: List[Dict[str, Any]] = []
        for item in items:
            llm = audit_results.get(item["id"])
            hard_fail = bool(item["hard_reasons"])
            structural_fail = not item["structural_ok"]
            llm_fail = llm is not None and not llm.get("valid", False)
            repair = structural_fail or hard_fail or llm_fail
            if repair:
                to_repair_ids.append(item["id"])
            report.append({
                "id": item["id"],
                "split": item["split"],
                "index": item["index"],
                "method": item["method"],
                "needs_repair": repair,
                "reason": {
                    "structural": item["structural_reason"] if structural_fail else "ok",
                    "hard_rule_reasons": item["hard_reasons"],
                    "llm": llm,
                },
            })
        cp["to_repair_ids"] = to_repair_ids
        cp["audit_report_rows"] = report
        cp["audit_complete"] = True
        save_checkpoint(cp_path, cp)
        logging.info("Audit checkpoint saved: keeping %d; repairing %d.", len(items) - len(to_repair_ids), len(to_repair_ids))
    else:
        logging.info("Skipping audit; loaded %d repair IDs from checkpoint.", len(cp.get("to_repair_ids", [])))

    source_dir = base.find_source_dir(args.source_dir, dataset_dir, script_dir)
    if source_dir:
        logging.info("Trusted source directory: %s", source_dir)
    source_bank = base.build_source_bank(source_dir)

    to_repair_ids = cp.get("to_repair_ids", [])
    repaired: Dict[str, Dict[str, Any]] = cp.get("repaired", {})
    pending = [iid for iid in to_repair_ids if iid not in repaired]
    logging.info("Repair progress: %d/%d already checkpointed; %d remaining.", len(repaired), len(to_repair_ids), len(pending))

    # Strict one-by-one repair is faster on this local model and checkpoints immediately.
    for pass_no in range(1, MAX_QUALITY_PASSES + 1):
        pending = [iid for iid in to_repair_ids if iid not in repaired]
        if not pending:
            break
        logging.info("Quality pass %d/%d: %d rows pending.", pass_no, MAX_QUALITY_PASSES, len(pending))
        for n, iid in enumerate(pending, 1):
            logging.info("Checkpointed strict repair %d/%d (overall %d/%d): %s",
                         n, len(pending), len(repaired) + 1, len(to_repair_ids), iid)
            rec = base.strict_single_repair(item_lookup[iid], source_bank, args)
            if rec is None:
                cp.setdefault("failed_attempts", {})[iid] = int(cp.get("failed_attempts", {}).get(iid, 0)) + 1
                save_checkpoint(cp_path, cp)
                continue
            repaired[iid] = rec
            cp["repaired"] = repaired
            save_checkpoint(cp_path, cp)

    pending = [iid for iid in to_repair_ids if iid not in repaired]
    if pending:
        logging.error("%d rows still could not be repaired after %d quality passes.", len(pending), MAX_QUALITY_PASSES)
        logging.error("Checkpoint kept. Re-run the same command to continue trying: %s", cp_path)
        return 5

    # Final LLM audit of repaired rows; bad ones are re-repaired and checkpointed.
    if repaired and not args.skip_llm_audit:
        for final_round in range(1, 3):
            repaired_items = []
            for iid, rec in repaired.items():
                u, a = base.row_text(rec)
                repaired_items.append({"id": iid, "user": u, "assistant": a, "method": item_lookup[iid]["method"]})
            logging.info("Final audit round %d of %d repaired rows...", final_round, len(repaired_items))
            final_audit = base.llm_audit(repaired_items, args)
            bad = [x["id"] for x in repaired_items if final_audit.get(x["id"]) is not None and not final_audit[x["id"]].get("valid", False)]
            if not bad:
                break
            logging.info("Final audit flagged %d rows; repairing and checkpointing them again.", len(bad))
            for iid in bad:
                rec = base.strict_single_repair(item_lookup[iid], source_bank, args)
                if rec is None:
                    logging.error("Final repair failed for %s. Checkpoint retained; rerun later.", iid)
                    return 6
                repaired[iid] = rec
                cp["repaired"] = repaired
                save_checkpoint(cp_path, cp)

    # Apply repaired rows only in memory first.
    for iid, rec in repaired.items():
        item = item_lookup[iid]
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

    # Deterministic final validation.
    seen_users = set()
    final_methods = Counter()
    for split in base.SPLITS:
        for idx, rec in enumerate(split_rows[split]):
            user, assistant = base.row_text(rec)
            method = base.extract_recommended_method(assistant)
            ok, reason = base.structural_validate(rec)
            if not ok or method is None:
                logging.error("Final validation failed at %s:%d: %s", split, idx, reason)
                return 7
            hard = base.hard_contradictions(user, method)
            if hard:
                logging.error("Final contradiction at %s:%d (%s): %s", split, idx, method, hard)
                return 8
            key = re.sub(r"\W+", " ", user.lower()).strip()
            if key in seen_users:
                logging.error("Duplicate user scenario at %s:%d", split, idx)
                return 9
            seen_users.add(key)
            final_methods[method] += 1

    # Only now overwrite original dataset.
    for split in base.SPLITS:
        base.write_jsonl(dataset_dir / f"{split}.jsonl", split_rows[split])
        base.write_jsonl(dataset_dir / f"{split}_provenance.jsonl", provenance_rows[split])

    stats = {
        "target": len(items),
        "generated": len(items),
        "split": {s: len(split_rows[s]) for s in base.SPLITS},
        "method_counts": dict(sorted(final_methods.items())),
        "model": args.model,
        "seed": base.SEED,
        "repair": {
            "kept_unchanged": len(items) - len(repaired),
            "repaired": len(repaired),
            "audited_with_llm": not args.skip_llm_audit,
            "backup_dir": cp.get("backup_dir"),
            "resumable_checkpoint_used": True,
        },
    }
    (dataset_dir / "dataset_stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    report = {
        "dataset_dir": str(dataset_dir),
        "total_rows": len(items),
        "rows_flagged_initially": len(to_repair_ids),
        "rows_repaired": len(repaired),
        "method_counts": dict(sorted(final_methods.items())),
        "items": cp.get("audit_report_rows", []),
    }
    (dataset_dir / "repair_audit_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    completed_cp = dataset_dir / "_repair_resume_checkpoint_COMPLETED.json"
    cp["completed_at"] = datetime.now().isoformat(timespec="seconds")
    save_checkpoint(completed_cp, cp)
    if cp_path.exists():
        cp_path.unlink()

    logging.info("=" * 72)
    logging.info("DONE - RESUMABLE SDLC DATASET REPAIRED AND VALIDATED")
    logging.info("Rows repaired: %d", len(repaired))
    logging.info("Split: train=%d validation=%d test=%d holdout=%d", *(len(split_rows[s]) for s in base.SPLITS))
    logging.info("Send the 4 JSONL files + dataset_stats.json for final GREEN FLAG.")
    logging.info("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())

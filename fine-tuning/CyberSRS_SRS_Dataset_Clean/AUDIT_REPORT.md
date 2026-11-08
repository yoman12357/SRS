# CyberSRS SRS Dataset — Final Audit

## Verdict
**APPROVED FOR ADAPTER TRAINING (structure and split).**

## Cleaning performed
- Removed the accidental 4 examples generated from `README.md`.
- Final SRS examples: **592**
- Final SRS PDFs represented: **37**
- Verified generation pattern: **4 chunks per PDF × 4 examples per chunk = 16 examples/PDF**
- PDFs failing the 4×4 check: **0**

## Final split
- Train: **464 examples** from **29 PDFs**
- Validation: **64 examples** from **4 PDFs**
- Test: **64 examples** from **4 PDFs**

### Leakage prevention
The split is now performed by complete SRS family, so different AUTOSAR releases of the same SRS family cannot appear across train/validation/test.

- Validation family: `07_Cryptography`
- Test family: `09_V2X`
- Train/validation family overlap: **0**
- Train/test family overlap: **0**
- Validation/test family overlap: **0**
- Exact document overlap across splits: **0**

## Format checks
- JSONL rows parse correctly: **PASS**
- Required instruction/input/output/messages/metadata structure: **PASS**
- User/assistant message consistency: **PASS**
- Duplicate output groups: **0**
- Repeated instruction-text groups: **3**
- Every output contains SRS-style `shall`: **PASS**

## Files to use for adapter training
- `train.jsonl` — use for training
- `val.jsonl` — use for validation during training
- `test.jsonl` — keep untouched for final evaluation
- `all_examples.jsonl` — cleaned full corpus

Do **not** train on `test.jsonl`.

## Grounding note
This audit verifies dataset structure, counts, splitting, leakage, formatting, duplicates, and SRS style.
The uploaded ZIP did not include the original SRS PDFs, so every generated technical claim could not be checked line-by-line against its source PDF.

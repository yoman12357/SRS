# CyberSRS Clean SRS Fine-Tuning Dataset

This is the cleaned, re-split version of the generated CyberSRS SRS dataset.

Use:
- `train.jsonl` for adapter training
- `val.jsonl` for validation
- `test.jsonl` only for final evaluation

The accidental README-derived examples have been removed.
Train/validation/test are split by whole SRS family to prevent cross-release leakage.
See `AUDIT_REPORT.md` and `dataset_summary.json`.

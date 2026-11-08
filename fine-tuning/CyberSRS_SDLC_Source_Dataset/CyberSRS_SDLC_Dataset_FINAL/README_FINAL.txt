CyberSRS SDLC Dataset — FINAL CURATED VERSION

Files
-----
train.jsonl       : 240 examples — use for adapter training
validation.jsonl  : 30 examples  — use for validation/evaluation during training
test.jsonl        : 15 examples  — DO NOT TRAIN ON
holdout.jsonl     : 15 examples  — DO NOT TRAIN ON

Provenance files are included for all four splits.
dataset_stats.json records final counts and curation statistics.
QUALITY_REPORT.json records the final integrity checks.

Final curation
--------------
- 300/300 examples reviewed.
- 181 scenario rows were repaired because the original lifecycle characteristics did not reliably justify their assigned SDLC.
- Repaired scenarios retain the original cybersecurity/network project topic but use explicit lifecycle characteristics appropriate to the assigned SDLC.
- All 300 assistant answers were normalized to a consistent training structure:
  Recommended SDLC
  Decision factors
  Why it fits
  Why alternatives are less suitable
  Requirement-to-lifecycle mapping
  Security integration
  Risks / trade-offs
- No exact duplicate prompts or answers remain.
- Original balanced SDLC distribution is preserved.

TRAINING RULE
-------------
Train on train.jsonl only.
Use validation.jsonl for validation.
Never include test.jsonl or holdout.jsonl in the training mixture.

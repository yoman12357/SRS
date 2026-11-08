# Dataset/runtime alignment audit

Audit date: 2026-10-26. No training or adapter promotion was performed.

The historical `ai/finetuning/data_test2` inventory contains **519 records**
across 11 tasks, including 60 canonical `srs_generation` targets. These targets
do not match current `FoundationDraft`, `RequirementsDraft`, and `SupportingDraft`
requests. There are no SDLC recommendation targets. The historical datasets
remain unchanged.

The current-runtime preparation command validates individual projections and
groups train/validation records by scenario ID. The existing authored scenarios
yield **60 foundation** and **45 requirements** candidates. All **60 supporting**
targets lack required current details (such as concrete attack scenarios, risk
rationales, threat/control relationships, mitigations or glossary records).
Another **15 requirements** targets lack a security requirement. These gaps are
reported rather than filled with invented examples. Missing role permissions
remain explicit requests for stakeholder confirmation.

The candidate set therefore has **105 records**, with a deterministic split of
97 training and 8 validation records, and is **not training-ready**. Preparation
returns code 2 when an active task is missing. Every candidate also retains a
human semantic-review status. This audit does not justify a new adapter or a
claim of improvement over the base model.

Reproduce using a new output directory:

```powershell
.\.venv\Scripts\python.exe -m ai.finetuning.scripts.runtime_dataset audit --data-dir ai/finetuning/data_test2 --report data/dataset-audit.json
.\.venv\Scripts\python.exe -m ai.finetuning.scripts.runtime_dataset prepare --output-dir data/runtime-training-candidates
```

The preparation manifest includes rejected target locations, current task counts,
split counts, and the SHA-256 of the frozen 30-case evaluation file. Exact held-out
descriptions are excluded before projection. Scenario grouping prevents its
different tasks crossing train/validation splits. This is an automated boundary,
not a substitute for semantic similarity checks, human review, or a statistically
adequate evaluation study. Real user projects are never collected for training.

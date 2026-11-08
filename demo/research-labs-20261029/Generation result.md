# Research laboratory generation result

The final fresh generation completed all 14 sections in **104.151 seconds
(1 minute 44 seconds)**. No checkpoints were reused and no Retry action was
needed in this final run. The slowest section was functional requirements at
42.078 seconds, within the unchanged 60-second section limit. Analysis and PDF
export are outside the generation timing.

The exact original user brief is preserved. The app is ready at
http://127.0.0.1:8011/ under **Teacher demo - Research laboratory access and
monitoring**. The exported PDF contains 24 pages. Canonical JSON/hash, all
requirement IDs in the PDF, and the complete 14-section progress were verified;
PDF pages 1, 5 and 24 were sampled visually. No reviews or approvals were recorded.

## Repairs and verification

The first attempt stopped on unsupported response deadlines and product log
witnesses. Added the numeric-specificity diagnostic to bounded field repair,
kept valid outcomes frozen for witness-only defects, and constrained rejected
log witnesses to model-selected external test-capture labels. Behavioral outcomes
remain model-authored and pass the existing full-section validation. The primary
adapter remains enabled; actual base corrections are recorded.

Three failed development runs are retained as attempt-1/2/3-run.json. The fourth
fresh run, f9dc16b1-ec0f-438b-b8eb-19163722d1d5, completed without manual section
edits. Application source hashes stayed unchanged through that final run.

479 backend tests passed (24 existing dependency warnings); Ruff passed.
Frontend code was unchanged and frontend tests were not repeated in this task.

## Draft content review still required

This verifies execution/completion, not universal correctness on new briefs.
The stored version remains needs_review. A bounded content inspection identified:

- SEC-001 introduces a research-device certificate and specific audit-log fields
  that the brief does not specify.
- Its off-hours access-denial test extends the source's off-hours alert duty.
- FR-003's alert test repeats its detection trigger instead of observing alert
  receipt; SEC-001 needs a direct network-isolation acceptance test.

These assumptions and test gaps need review before treating the draft as an
approved specification. No canonical section was hand-replaced or human-approved.

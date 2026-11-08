# CyberSRS source-fidelity repair

Status: verification in progress. This file is not a completion or human-approval claim.

The active application checkout is `C:/Users/Aryan Bokolia/Desktop/cyber srs`.
The original NITK checkout is separate. The local application uses port 8011.
The exact four supplied briefs and their review constraints are in `cases.json`;
the independently enumerated obligations and scope traits are in
`obligation-matrix.json`.

## Root causes and changes

| Cause | Resulting change |
| --- | --- |
| One source paragraph became one FR, while acceptance prose could hide an omitted obligation | `source_obligations.py` conservatively separates recognizable predicates. `validation.py` checks coverage in canonical statements bound to the original evidence. Email quarantine and alerts have independent rows. |
| Model classification placed runtime duties only in quality/security categories | `normalize_requirement_sections` routes explicit runtime behavior into functional authoring. `rebuild_functional_view` and the IEEE projection expose canonical runtime rows without duplicating their IDs. |
| A source sentence was considered fully covered after its functional row existed | `generate_compact_requirements` now checks missing slots for the requested category, preserving quality goals from the same evidence. |
| Broad words such as secure or approved were expanded into implementation commitments | `source_detail_policy.py`, acceptance grounding and per-operation validation reject known unsupported choices, field sets, response actions and numeric promises. Unconfirmed quality targets remain open. |
| Exact-string question deduplication left paraphrases and unrelated RAG questions | `clarification_policy.py` uses source-scoped semantic decision keys. Generated sections refer to one canonical question inventory, retaining evidence and distinct decisions. |
| Resource modifiers and individual words from compound role labels became human actors | Source-aware role extraction excludes network/resource modifiers. Interactive matching preserves complete role labels rather than treating network as a person. |
| Atomic requirements enlarged the compliance prompt with repeated acceptance procedures | `compliance_requirement_context` retains every requirement ID, statement, basis and source/evidence link while excluding test prose unused by that specialist. |
| A sole acceptance criterion could be classified as an alternate, leaving no primary flow | The private native scenario schema keeps an atomic requirement's sole criterion available as a primary flow. All authored test text remains intact. |
| Corrective generation could reauthor valid material or introduce another defect | `atomic_requirements.py` freezes valid slots and fields, applies bounded field-only corrections, and validates the whole merged section under the same deadline. Actual model tags and calls remain audited. |

Source statements are compiled from source clauses; their acceptance criteria are
authored by local Qwen. Ambiguous, conditional, negative or unrecognized clauses
retain the existing authoring path. No public Document/evidence schema, API route,
SQLite migration or provider was replaced. Human edits and exact-hash approvals
remain separate from generation.

The configured adapter is requested first. Base-Qwen corrections retain their
actual authorship; the adapter is not merely a display label. This installation's
section deadline is 120 seconds, and its atomic-test correction limit is two.
These are bounds on attempts, not a completion guarantee or response-time SLA.

## Evidence required before completion

For each case: a fresh completed run, original-input equality, valid canonical
JSON/hash, every independent operation and scope trait, appropriate functional
ownership, unsupported-detail review, relevant unique questions with valid
references, linked scenarios/tests, the IEEE outline, complete PDF text and visual
inspection. `verify_cases.py` performs the mechanical checks against actual saved
versions and exports; manual output review remains necessary.

Every preliminary failure remains in its attempt folder. No failed attempt is
counted as successful. No test harness records human approval.

## Remaining verification

Final live cases, PDF review, test totals and the ten-item completion audit are
pending. The existing full suite currently exposes a qualified-role matching
compatibility regression, which must be fixed before release.

## Limits

The parser and grounding checks are conservative rules, not a proof of arbitrary
natural-language entailment. Four supplied cases cannot establish universal
first-attempt reliability or a worst-case generation time. Generated documents
remain drafts, and their verification procedures have not executed the proposed
university systems. The existing deterministic SDLC ranking and broader product
readiness are outside this bounded source-fidelity repair.

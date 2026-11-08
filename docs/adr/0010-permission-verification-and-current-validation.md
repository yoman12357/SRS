# ADR-0010: Validate both sides of explicit permissions and recheck stored drafts

Manual review found that an alert acknowledgement leaving policy unchanged was
being used as the only test of an operator's restriction on policy editing.
The model must author a successful permitted interaction and a visibly denied
attempt at the forbidden action. Tests may span atomic requirements sharing
the same original passage. An explicit attempted action remains valid when the
model writes it in Given rather than When; validation checks the complete trigger.
These narrow checks address observed defects and do not prove semantic correctness.

Architecture now has separate logical components, data flows and trust boundaries,
each linked to canonical requirement IDs. Missing fields cannot be hidden behind
a prose summary. New section schemas do not rewrite historical version content.

Reading, exporting or approving a stored version recomputes current deterministic
quality. The stored content hash and historical validation remain immutable.
A previously valid report cannot bypass a newer quality gate. Section model tags
are retained across retries and revisions, including inherited sections and human
edits. Base correction is disclosed rather than attributed to the adapter.

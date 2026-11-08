# ADR-0036: Correct an invalid rationale without re-authoring valid acceptance

The frozen profile-1.27 VPN run repeatedly claimed privacy-regulation compliance
in DR-001's rationale and failed. Inspection found that whole-requirement repair
receives metadata and error codes but not the rejected requirement body, despite
being instructed to repair that supplied candidate.

Supply the actual rejected requirement as untrusted context. If normal source
validation proves that the rationale is the sole remaining defect, request a
typed rationale-only correction and merge only that field. Revalidate the full
requirement and retain every other valid field and authored criterion unchanged.
Diagnostic field isolation is temporary and never persisted or presented as model
output. General normative repairs remain available when other fields are invalid.

This changes neither source evidence nor stakeholder decisions, and creates no
new endpoint, model, provider, framework or training labels. Actual model authors
and corrective attempts remain auditable. It is not assistant-authored replacement
requirements or a bypass of the source gates.

Implemented and integrated. A regression proves that the rationale-only merge
preserves every other field and both authored criteria, and that a repeated
regulation claim is rejected. Integrated suite: 301 passed; Ruff passed. Real
field-repair verification remains pending. Preserving fields that pass selected
guards does not prove those fields are semantically correct.

The first real field probe changed only the rationale, but preserved a separate
unsupported deletion-event log and an incoherent temporal step. After the logging
scope fix (ADR-0038), the next real probe rejected both fields, fell back to whole
row authoring, and again failed the regulation check. Preserve that failure.

Extend the existing independent linked-criterion repair to canonical criteria
before whole-row repair. Use a transient linked test view bound to the same
canonical ID/source; copy back only a validated model-authored replacement
criterion. Valid siblings, statement and metadata stay unchanged. Then revalidate
the complete row and apply rationale-only repair if it is now the sole defect.
Retention/deletion repair instructions require an existing record with a known
creation time, controlled elapsed time and actual storage inspection. No transient
test view is stored as an extra requirement or criterion. The complete section
gate remains mandatory, so partial field improvements cannot become a successful
SRS. The follow-up is integrated as field-local-repair-1.1: staged 319 tests and
integrated 320 tests passed; Ruff passed. A regression covers simultaneous bad
rationale and bad deletion witness, retaining the valid sibling and all metadata.
Actual-model full-workflow verification remains pending.

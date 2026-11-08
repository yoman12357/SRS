# ADR-0024: Distinguish independent verification and make V-Model pairing explicit

2026-10-27. The completed profile-1.19 VPN draft selected V-Model, but its workflow
contained generic sequential stages, no explicit development/test pairing, and
test-case creation primarily during implementation. Its explanation also called
independent verification "formal verification" because the deterministic factor
incorrectly labelled both source phrases formal.

Policy sequential-sdlc-1.1 records formal, independent and strict verification as
separate evidence values under the verification factor. Its suitability weight is
applied once, without treating those compatible values as a contradiction.
Only genuinely exclusive stability values are consolidated as conflicting.
Source-independent verification does not imply mathematical proof or guaranteed
correctness. Scores remain versioned suitability points, not probabilities.

Add optional verification_pairs to the canonical SDLC section, keeping old documents
readable. A V-Model recommendation must explicitly connect requirement/design
planning stages to later verification stages, identify the test level and name a
test-plan deliverable created in the development stage. Pair names resolve to
actual phases; the plan appears in that phase's deliverables; pair coverage links
all canonical requirements. Include acceptance and technical verification, with
no per-requirement pair quota. The model authors phases, plans and mappings; the
server validates relationships rather than inventing a workflow.

The SDLC specialist also receives compact actual verification IDs to avoid made-up
TC identifiers. Recommendations remain proposed human decision aids, not evidence
that a lifecycle was executed or approved. Actual source-specific workflow review
is still required after structural tests and real generation.

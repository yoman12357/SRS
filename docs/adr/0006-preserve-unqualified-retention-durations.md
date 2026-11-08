# ADR-0006: Preserve bare retention durations without inventing bound semantics

Both local model variants repeatedly changed "retain for 30 days" into "retain
for a minimum of 30 days", despite corrective prompts. Treating that unstated
interpretation as confirmed is incorrect.

Before validation, a narrow deterministic rule removes an added minimum/maximum
qualifier only when it modifies the same exact numeric retention duration present
in linked original evidence and the source itself has no bound. No number, unit,
actor, action, requirement or acceptance criterion is replaced or dropped. A
source-specified bound remains immutable and conflicting bounds still fail checks.
Other unsupported quantities, timing promises and unrelated controls still fail.

When deletion is not specified, the requirement records the bound/deletion
interpretation as an unresolved decision. This keeps the stakeholder's wording
and asks for the missing policy rather than silently choosing a minimum or maximum.
The document remains a draft requiring human review. This is canonical source
preservation, not a template report or a model-confidence/human-approval claim.

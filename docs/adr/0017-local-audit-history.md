# ADR-0017: Local append-only workflow audit history

2026-10-27. The professor brief explicitly requires recording prompts, retrieved
evidence, agent decisions, user changes, approvals and generated artifacts. Current
versions/checkpoints preserve outcomes, but overwritten inputs and corrective
requests cannot be reconstructed reliably.

Add an application-owned SQLite audit_event table. Repository mutations record
source revisions, extracted reference additions/removals, run decisions, immutable
version identities/hashes and exact-content reviews in the same transaction.
Each model request records exact model/messages/decoder schema/options and its
response envelope plus validation result. Worker-local context binds these records
to the correct project/run, including base-Qwen correction attempts. A request is
persisted before inference so a process interruption still leaves evidence.

Audit payloads are private local application data, never debug logs or ordinary
progress responses. A separate project audit export provides explicit inspection.
Project deletion cascades to audit records. Standalone, non-project chat remains
ephemeral; project-scoped chat is audited. This history is append-only through
the application, not a tamper-proof ledger or a human approval mechanism. Existing
historical calls cannot be reconstructed; do not fabricate them after the fact.

Implemented in profile 1.17 after isolated testing. Repository mutations and model
attempts record private history; document export events retain exact base64 bytes,
artifact SHA-256 and canonical content hash. The project workspace links the audit
download. Tests cover transaction rollback, project isolation, prior/new source
state, corrective attempts, request-before-response recording, ordinary API
redaction, exact artifact bytes and cascade deletion. Existing historical calls
remain absent rather than being reconstructed. Actual new live workflows still
need inspection to establish real audit evidence beyond isolated tests.

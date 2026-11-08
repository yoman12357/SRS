# Local prototype data handling

CyberSRS is a single-user research application. Inputs, question answers,
references, validated checkpoints, versions, reviews and audit events are stored
in the configured local data directory. Generation and embeddings use the
configured loopback Ollama instance. The application has no cloud inference,
analytics or user-project training collection.

The retention policy is manual: project data and private history remain until
the user deletes that project. Project deletion cascades its relational records
and removes the project's private retrieval chunks. Shared reference material,
copied datasets, model adapters and independently saved exports are separate
assets. Deleting a project does not delete those assets or files the user exported.
There is no automatic expiry, backup-removal or forensic secure-erasure claim.
SQLite free pages, journals and user backups must not be described as securely
erased by an application-level delete.

Private audit downloads deliberately include exact source revisions, inference
requests/responses and export bytes. They can therefore contain everything typed
or uploaded to the project. Ordinary progress APIs exclude that private history;
its explicit download is labelled in the interface. Standalone chat is ephemeral;
project-scoped chat is retained in that project's audit history.

New generation and embedding requests mask recognized email addresses, telephone
numbers, formatted government identifiers, labelled financial identifiers,
explicit credential assignments and values marked `<private>...</private>`.
Generation uses per-call opaque aliases in context and decoder constraints. It
restores values locally before source validation so evidence, citations and
content hashes remain exact. Private audit records include classification and the
reversible local mapping alongside exact masked wire requests. Historical requests
are not rewritten or described as retroactively masked.

This is bounded pseudonymization before local inference, not encryption or
irreversible anonymization. Original inputs, local references, restored canonical
documents, exports and private audit still contain original values. Recognizers
cannot reliably identify arbitrary names, free-text sensitive facts, unconventional
secrets or unlabelled identifiers. Minimize personal data and explicitly mark
private values; do not enter production credentials. Masking may reduce retrieval
quality. No universal PII detection or regulatory-compliance claim follows.

Enterprise identity, MFA, encrypted shared hosting and multi-user authorization
remain outside the adopted single-user scope. The loopback address is not a
replacement for those controls. A deployment handling real organizational data
requires a separate security design and validation. No regulatory certification
or production-readiness decision is inferred from this local prototype.

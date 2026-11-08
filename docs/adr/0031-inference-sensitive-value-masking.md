# ADR-0031: Mask recognized sensitive values at local inference boundaries

The professor brief calls for classification and masking before model submission.
Local-only processing and private audit storage do not themselves implement this.

Use a deterministic, dependency-free boundary for recognizable email addresses,
international/labelled telephone numbers, formatted government identifiers,
labelled financial identifiers, explicit credential assignments and user-marked
`<private>...</private>` spans. Replace values in generation context and native
schema constraints with per-call opaque aliases. Parse the model's typed response,
restore aliases locally, and then apply ordinary source/link validation. Original
stakeholder evidence and citations therefore remain exact in canonical documents.
Embedding inputs use the same masking boundary; original reference text remains
in the isolated local store for literal citations.

Private audit records retain classification, exact masked wire requests and the
local reversible mapping. No mapping or raw input is added to debug logs. This is
pseudonymization before local inference, not encryption or irreversible
anonymization. Original inputs, restored documents, exports and private audit may
contain sensitive values and retain the existing project-deletion lifecycle.

Recognizers are deliberately bounded. Arbitrary personal names, free-text medical
details, unconventional secrets and unlabelled identifiers cannot be reliably
recognized by simple rules. Users must minimize those inputs or explicitly mark
private spans. Masking can reduce retrieval quality. No universal PII detection,
regulatory compliance, encrypted storage or secure erasure is claimed.

No model/provider/framework is added. Historical audit records are not rewritten
or described as having been masked retroactively.

# ADR-0037: Retain bounded corrective history and rejected typed candidates

The real SDLC-generation-1.4 probe produced a valid iteration/feedback structure on
one correction, but that candidate still had coverage, quantity and approval
errors. The next correction reverted to a linear workflow. Current provider calls
replace previous feedback with only the latest diagnostic list and do not supply
the rejected candidate body, so each correction can forget an earlier fix.

Within the existing bounded retry count, accumulate diagnostic codes across
attempts and supply the last schema-valid rejected candidate as untrusted user
context. Fixed trusted remedies may reference known codes; candidate/source text
must never enter the system instruction. Revalidate every response. Keep current
failure diagnostics distinct from historical corrected issues.

Carry a typed rejected candidate into same-family base correction when available.
Never use an unparsed/truncated response as a candidate. Keep raw attempts in the
private audit. If optional prior-candidate context exceeds the budget, omit that
whole auxiliary object with an explicit audit event; never truncate authoritative
source inputs, requirements or evidence. Preserve privacy masking on every retry.

Record the correction-policy version in call provenance/audit metadata. Do not
increase retry limits, change models/providers/frameworks, fabricate labels or
treat correction success as human approval.

Implemented as bounded-corrective-history-1.0. Regressions cover accumulated
diagnostics, private typed rejection/base handoff, optional-context omission,
authoritative-input budget failure, and masking restored private identifiers on
the next request. Integrated suite at this change: 301 passed; Ruff passed. The
second real SDLC probe failed after 368.6 seconds with unchanged source/input.
Its actual requests retained all accumulated diagnostics and the typed rejected
candidate, but the model merely renamed a test phase "iteration" and still
omitted implementation and a feedback return. The retry-policy implementation
worked; it did not establish correct SDLC semantics. ADR-0039 changes the internal
generation task in response to that evidence.

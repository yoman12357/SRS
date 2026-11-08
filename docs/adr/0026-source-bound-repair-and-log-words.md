# ADR-0026: Preserve valid authored tests while rejecting unsupported extras

2026-10-27. Frozen profile 1.23 exposed three independent issues:

- Architecture logging validation matched "logical" as if it were "logging".
- Manual restoration criteria introduced a waiting/isolation period absent from
  the source, including contradictory before/after-period outcomes.
- Administrator-management completion produced a correct positive test plus an
  extra negative test asserting an exclusive administrator permission. Re-authoring
  the whole requirement repeatedly reintroduced that unsupported extra criterion.

Use precise logging word forms, retaining the source/event-scope check. Reject new
waiting-period conditions where the linked source supplies no timing policy;
explicit source timing and the natural isolation/restore sequence remain valid.

During bounded requirement completion/repair, an unsupported extra exclusivity
criterion may be rejected when at least one other authored test remains and the
normative statement itself does not contain the unsupported restriction. Retain
the other tests byte-for-byte, expose unspecified role permissions as unresolved,
and record the exact rejected criterion and reason in private audit history.
Raw inference responses remain recorded. No generated requirement is dropped.

This normalization never excuses an unsupported statement or a candidate with
only invalid tests. The same full source, action, actor, denial, citation and
relationship validators run afterwards. Required missing tests still use bounded
model-authored completion; rejecting an optional unsupported test cannot waive a
stakeholder obligation. No approval is inferred from normalization.

Integrated in sequential-1.24 after the independent development checks. The main
backend suite passes 192 tests and final Ruff lint/format checks pass. Actual new
SRS/SDLC output and PDF inspection remain the completion criteria.

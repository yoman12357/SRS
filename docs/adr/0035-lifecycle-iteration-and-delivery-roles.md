# ADR-0035: Validate actual iteration and delivery responsibility

The real profile-1.27 campus draft selected the expected Agile winner, but authored
a one-pass planning/design/implementation/verification/release workflow. Its
phase_type values were null, with no explicit next-iteration feedback loop. It
also assigned implementation/testing/release responsibilities to source product
users and operators without evidence that they held those project responsibilities,
and emitted V-Model verification pairs despite selecting Agile.

Require typed phases in newly generated workflows. An Agile workflow must contain
an actual iteration, feedback/review, and a stated return to backlog/planning or
the next iteration. A matching methodology label alone is insufficient. Non-V
workflows do not emit V-specific verification_pairs. Keep existing early-plan and
execution checks for V-Model.

A named source product role is not automatically a confirmed delivery role.
Only an explicit source assignment to requirements/design/implementation/test or
release responsibility admits an unqualified delivery-role name. Other proposed
delivery responsibilities need a visible Proposed label. Human phase gates remain
future decisions, never recorded approvals.

Use the separate SDLC generation version so this change refreshes SDLC without
redrafting unchanged canonical requirements. Historical content remains immutable;
current validation may reject older workflows. These are recognized methodology
and source-assignment checks, not proof of project suitability or expert accuracy.

Implemented as SDLC generation 1.4 / source-grounding 1.3. The first real focused
probe failed: a middle correction had an actual iteration but other defects, and
the final correction reverted to a linear sequence after earlier diagnostics were
lost. ADR-0037 addresses that observed retry failure. Integrated software checks
pass (301 backend tests, Ruff); a passing complete automatic SRS is still pending.
No model, framework, provider, dataset-label or training change is introduced.

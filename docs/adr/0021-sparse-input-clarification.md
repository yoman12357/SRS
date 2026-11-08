# ADR-0021: Do not silently approve a project-only description as complete input

2026-10-27. The real sparse-input check supplied "We need a security alert review
system for our campus IT team." Analysis returned neither questions nor unknown
decisions, and inferred automated/semi-automated response work not stated by the
source. This fails the adaptive gathering requirement.

Add a conservative scope-readiness hint: a project/system noun phrase without
recognized concrete product behavior requires at least one model-authored material
scope question for supported domains. Explicit modal obligations or recognizable
behavior verbs remain valid evidence, including simple-present actor actions.
This is not a fixed questionnaire or a general completeness classifier. Unsupported
domains are not forced into interviews. Explicit skipped questions remain unknown;
do not force re-asking them merely to satisfy the initial readiness hint.

Preserve skipped question text in the analysis unresolved-decision register so
the final SRS cannot lose an unanswered decision when empty answers are excluded
from the normative evidence inventory. This projects the existing question and
skip state; it invents no answer or stakeholder approval.

Scope readiness was implemented in profile 1.17. Its actual check asked questions
but repeated an explicitly skipped question. Profile 1.18 routes exact repeated
skipped questions into the unknown-decision register before returning analysis,
preserving new questions and inventing no answers. This enforces the application's
skip decision without claiming the model itself stopped repeating questions.
Actual question/skip behavior is being rerun. Earlier failures remain evidence.

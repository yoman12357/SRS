# ADR-0018: Rebuild the functional index from canonical actor interactions

2026-10-27. The real campus analysis classified permissions and operator actions
under security only. Because functional generation precedes security, its empty
section incorrectly said that no functional behavior was supplied, even though
the final security requirements described actor-visible actions.

After requirement drafting and again before final assembly, rebuild the functional
section's related-ID index to include canonical actor interactions identified by
the same rule used for required scenarios. Preserve normative statements and
model-authored criteria under their original canonical IDs; do not duplicate them
under FR IDs or ask another agent to invent new features. Replace the empty-category
explanation only when the derived links establish applicability. Existing authored
related links remain subject to normal dangling-reference validation.

This deterministic linked view must also refresh after requirement edits or
regeneration, before dependent artifacts consume the document. It does not replace
semantic classification review or prove that every interaction has been recognized.

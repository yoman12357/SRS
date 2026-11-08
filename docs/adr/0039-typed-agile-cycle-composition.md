# ADR-0039: Compose an Agile workflow from typed cycle activities

Both real SDLC-generation-1.4 probes failed to produce a complete Agile cycle.
The second retained all retry diagnostics correctly but only renamed verification
as iteration, preserving test-only activities and no return to planning. Repeating
the same free-form phase request is insufficient for this model.

For the deterministic Agile winner, use an internal typed lifecycle response:
preparation, a recurring delivery iteration, and release/handoff. The iteration
requires separately authored planning, implementation, verification, stakeholder
feedback and next-iteration backlog actions. Constrain recognized action verbs
in the native schema and independently parse the same typed fields. Preserve
each model-authored activity verbatim when flattening into the existing public
SDLC phase structure. This is methodology composition, not new product behavior.

Keep normal evidence, quantity, role, approval, coverage and complete-cycle gates
on the composed section. Proposed delivery roles remain visibly proposed, unknown
facts remain open, and no human decision is manufactured. Reject invalid fields;
do not insert a canned workflow after model failure. The trained local model is
still asked first through the same provider, with actual attempts audited.

Public canonical/API/PDF schemas remain unchanged. V-Model keeps its early plans
and later constrained links; other methodologies keep their existing path. Bump
the independent SDLC generation version so retries refresh only SDLC. No framework,
provider, model weights or dataset labels change.

Implemented as SDLC generation 1.5. Integrated suite: 318 passed, 24 third-party
deprecation warnings; Ruff passed. Tests reject missing cycle responsibilities and
a test-only implementation field, preserve every authored action, constrain actual
IDs/proposed roles, and confirm full source validation after composition. The real
probe is running under data/category-lifecycle-probes/20261028-062008. Its actual
output must be reviewed before claiming SDLC quality.

That probe terminated failed after 341.4 seconds with source/input unchanged.
The actual typed drafts included implementation, verification, feedback and a
return to backlog. The per-string next-action pattern nevertheless rejected an
additional refinement action because it did not repeat a backlog/planning word.
Generation 1.6 retains recognized action verbs but leaves the mandatory actual
return-path check on the complete composed workflow. A regression accepts a
refinement alongside a return, and rejects a workflow with no return. Integrated
suite with criterion-first repair: 320 passed; Ruff passed. The user's requested
base-only full SRS evaluation is now running; there is no quality conclusion yet.

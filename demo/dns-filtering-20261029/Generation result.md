# Example 2 - DNS and web filtering generation check

Final fresh generation completed **all 14 sections in 107.266 seconds
(1 minute 47 seconds)**. It reused zero checkpoints and needed no manual Retry
inside that final run. Functional requirements were slowest at 27.953 seconds;
the 60-second section budget remained unchanged. Analysis and PDF export are
outside the generation timing. The original brief is preserved exactly.

Project: Example 2 - Secure University DNS and Web Filtering.
Project ID: 359e7293-04dd-4a32-9e11-82ee2a09414a.
Final run: defa0366-2d5a-4cf7-a5b0-9351fe2812c0.
Version: c599ff2d-80ba-4634-bed1-6be9c6e60aa4.
The app at http://127.0.0.1:8011/ shows Generation completed and all section times.
The exported draft PDF contains 26 pages; pages 1, 5 and 26 were sampled visually.
The canonical hash, original brief, PDF requirement IDs, 22 automated document
checks and source-code stability through the final run were verified. The model
profile still asks the adapter first and records actual base-Qwen corrections.
No model output or success status was hand-inserted. No human review or approval
was recorded; the stored quality state is needs_review.

## Bugs uncovered and fixed

The first run 906f9bb1 stopped at scenarios:source_actor_requires_clarification.
The literal Administrators role in "should be able to create" was not recognized,
and the inferred stakeholder "university administrators" could not replace it.
Added affirmative modal-ability forms, relevant role verbs, and explicit dashboard
recipients to the shared source-role parser. Conditional and negative forms remain
excluded; role bindings still require exact linked canonical source evidence.

Run c0704c0f then exposed case-only duplicate architecture nodes for administrators
and Administrators. Merge actor/resource identity case-insensitively, preserve the
first source display label and all provenance, and compile graph paths with the
same identity. Distinct role qualifiers remain separate. The final third fresh
run completed from introduction through SDLC without checkpoint reuse.

Verification: 495 backend tests passed, including 16 new source-role/identity
regression cases (24 existing dependency warnings); Ruff passed. Frontend code
was unchanged and frontend tests were not repeated. Offline saved-input checks
also confirm actor selection and the compiled architecture paths.

## Remaining draft content issues

This verifies generation completion, not that the overall system is fully complete
or that every generated claim is correct. A bounded source review identified:

- FR-003's acceptance test auto-starts an investigation workflow instead of
  exercising the administrator's stated investigation action. Separate tests for
  policy updates and temporary user restrictions are still needed.
- NFR-001 assumes dynamic resource scaling, redundant-component failover and
  no-data-loss behavior absent from the brief. These are unconfirmed design choices.
- DR-001 adds specific log fields and performance expectations that need agreement.

Thresholds, restriction duration, role-policy definitions and other recorded
unknowns require stakeholder decisions. Human semantic review is still necessary;
this case does not establish universal first-attempt reliability on new briefs.

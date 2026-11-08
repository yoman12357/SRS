# ADR-0030: Reviewed corrections can resume a failed generation

The real campus generation cannot finish its architecture despite bounded model
correction. The original API allowed edits only after an entire document existed.
This prevents oversight from resolving a failed specialist's content.

Extend the existing retry request with optional schema-validated `section_edits`,
an exact `expected_input_hash`, and an editor label (`human` or `assistant`). Empty
requests retain existing retry behavior. Corrections apply only to terminated
generation runs whose authoritative source inputs still match. Revalidate reused
predecessors; validate each submitted section; rebuild every section after the
first correction, except explicitly submitted later corrections. Invalid content
fails visibly and cannot create a successful document.

Submitted corrections, editor labels, original attempts and final author provenance
are retained in private history. Editor labels describe submission provenance;
this single-user app does not authenticate identities. Neither kind of edit is a
human approval. Final immutable documents still require exact-hash review.

The ordinary version-section editor also accepts the optional editor label. This
lets assistant corrections remain distinguishable from human edits. No inference
provider, security capability or approval rule changes.

Native architecture boundary schemas additionally bind distinct endpoints using
branches over the already-frozen component inventory. Deterministic checks remain
in place for edits and any provider that does not enforce decoder constraints.

The version-section edit endpoint also accepts reviewed dependent sections in the
same atomic successor. This addresses removal/repair of an unsupported linked
criterion without replacing already reviewed dependent artifacts with new drafts.
Every override is schema/source/link validated; unrelated sections are rejected.
Verification edits include SDLC in their dependency set to refresh test references.

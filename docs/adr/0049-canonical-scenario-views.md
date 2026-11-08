# ADR-0049: Compose scenarios from canonical acceptance flows

The actual campus draft reversed the staff-network denial in a use-case goal and
added authentication, messages and interface behavior while paraphrasing correct
parts of the linked requirements. Prompt instructions alone did not prevent it.

The scenario specialist will ask local Ollama to select source-backed actors and
identify alternate/denied acceptance flows. The coordinator will compose stories,
preconditions, actions and observable outcomes from the exact final canonical
requirements and authored acceptance criteria. It must retain every applicable
criterion, including linked acceptance records; no scenario introduces a new
product behavior. An unknown actor cannot be invented to satisfy coverage.

Track the projection version on the canonical document and private run provenance.
Validate claimed automatic views against their exact source inventory. Requirement
or criterion changes rebuild scenarios; historical immutable versions remain
unchanged and manual scenario edits clear the automatic-projection marker.

This preserves the existing public scenario fields and the sequential local-model
specialist. It does not repair upstream requirement/criterion errors or establish
human approval. Status: implementation and real-output verification in progress.


2026-10-29 DNS correction: source roles in "Administrators should be able to ..."
clauses are valid literal actor choices even when inferred analysis stakeholders
add the qualifier "university". The source actor parser, shared with architecture,
also recognizes explicit dashboard recipients. Scenario actor selection continues
to require the exact linked source role; it never substitutes an inferred role
or removes the clarification guard when no literal role can be established.

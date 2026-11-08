# ADR-0054: Concise IEEE 830-1998 SRS presentation

The user requests the IEEE 830-1998 outline, clear stakeholder labels and less
repeated output. The existing PDF/Markdown and UI print the internal section
objects, including repeated statements, rationale, test procedures and provenance.

Use a deterministic presentation over the validated canonical Document. The main
report follows Introduction, Overall description and Specific requirements, with
numbered subsections. Every canonical requirement appears once, verbatim, with
its stable ID, priority, proposal basis and citations. Missing specifications stay
explicitly unspecified. No quotas, new product obligations or model calls.

Use User and Admin as display groups for literal source roles, retaining original
groups and their distinct permissions. Project Analyst is a document-review role,
not an added product account. Operational security analysts/operators retain
their own labels. Do not rewrite source evidence, permissions or canonical hashes.

The normal PDF/Markdown and default app view use this concise outline. Full
acceptance criteria, architecture, scenarios, SDLC, provenance and evidence remain
accessible in the existing section editor, full supporting exports and canonical
JSON. SDLC is a development-plan companion, outside the SRS product requirements.

Version reads expose a derived `presentation` object outside canonical `content`.
Export `detail=full` preserves the former exhaustive report. Approval continues to
refer to the exact canonical content hash, independently of presentation.

References consulted (structure only; no example product requirements copied):
- IEEE Std 830-1998, clauses 4.8, 5 and Annex A:
  https://people.eecs.ku.edu/~hossein/Teaching/Stds/0830.pdf
- CSUN Student Course Information System example:
  https://www.ecs.csun.edu/~rlingard/COMP380/srs.htm
- Rose-Hulman requirements template:
  https://www.rose-hulman.edu/class/cs/cs414/Process/requirements_specification_template.html

Status: implemented and verified for the presentation scope on 2026-10-29.
The running API, primary/full exports and browser reader were checked with saved
DNS and laboratory versions. Each primary PDF is five pages; all original
requirements, introduction text and canonical hashes are preserved. Backend 502,
frontend 16, Ruff and production build pass. See
`demo/ieee-830-20261029/Formatting verification.md`. These checks establish the
requested organization and presentation, not full semantic compliance or human
approval of the generated draft.

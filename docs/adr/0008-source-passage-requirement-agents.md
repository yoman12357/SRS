# ADR-0008: Process source passages independently within each section specialist

The first complete real report exposed a schema-valid omission: a combined
operator/audit requirement retained the restriction on policy editing but omitted
the operator's alert-review and acknowledgement behavior. Section-wide prompts
also combined unrelated source passages and copied existing requirements.

Keep the requested one-coordinator/one-specialist-per-section architecture. A
requirement specialist processes its uncovered source passages sequentially, with
one exact passage per structured drafting call. Each call may author multiple
requirements when that passage contains multiple outcomes. There are no quotas.
Validated siblings remain intact; IDs are assigned before later passages and
dependent agents. Covered passages become cross-category references. When no
new obligation belongs to a category, generation cannot invent a requirement.

The same source/action/quantity and relationship checks apply to every passage,
supplement, retry, edit and final document. Scope constraints stay available as
context but cannot be cited as another passage's decision. This avoids using a
source ID as a substitute for actual behavior coverage. Every requirement and
acceptance criterion remains model-authored; no template requirement compiler is
introduced. Actual output model tags are retained across all passage calls.

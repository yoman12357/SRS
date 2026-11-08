# ADR-0046: Preserve source access endpoints in the logical architecture

The automatic campus draft 045259 covered requirement IDs with internal modules
but omitted the actual students/guests, internet and staff-network endpoints.
An internal engine-to-management-client flow was described as internet access.
Valid IDs and named software blocks did not establish the required access path.

For recognized explicit actor/access/resource clauses (including authentication
before access), derive logical source endpoint cards using the original labels,
evidence IDs and canonical requirements. They are proposed representations of
stated actors/resources, not additional stakeholder obligations or deployed
servers. The model authors implementation blocks and the directed interactions.
Freeze the source cards before model generation; reject attempts to rewrite them.

Validate distinct source actor/resource nodes and directed, requirement-linked
paths between them. A denied-access path represents the attempted interaction,
not permission to carry traffic. The model must explain its enforcement. This
selected topology invariant does not prove enforcement correctness or general
natural-language entailment. Unrecognized source forms remain subject to review.

Pass compact canonical statements, not copied acceptance-test assumptions, into
architecture generation. Existing public architecture schemas and manual edits
remain available; equivalent explicitly named source endpoints are acceptable.
Permit a single additional implementation block when frozen source endpoints
already provide distinct domains; do not impose an arbitrary component quota.

Status: implemented in main; full-document correctness verification remains open.

Staged focused 29 and full 373 tests passed, 24 third-party warnings; Ruff passed.
The tests reproduce internal-flow endpoint substitution, reversed edges, unrelated
source links, frozen-card re-authoring, exact employee/service labels and manual
name compatibility. Main remains unchanged while full driver 34062 runs. Actual
trained-model architecture verification and promotion remain pending.

The current main-campus run 62dc5803-9c3e-4be1-ac6d-a903b277a294 stopped
at architecture (800.2s): its summary expanded policy-change auditing into all
administrator actions. The staged topology gate also detects all three missing
source endpoints in that actual rejected component draft. Review artifact:
data/evaluations/20261028-102047-finetuned-management-fix/campus-staged-topology-review.json.
For recognized access designs, constrain the overview to a fixed document-purpose
statement and independently validate it, while the model still authors blocks,
flows and enforcement. Updated focused 26 tests and Ruff pass. A real staged
architecture driver is prepared; it refuses any concurrent source/app workflow.

Actual architecture probe141045 failed after109.9s on the omittedFR003 owner,
with source stability true. Its source endpoints and overview were retained.
Allow the component-only intermediate stage to defer missing ownership (all other
gates remain); when needed, a separate typed model call assigns each missing
canonical obligation once to an existing implementation block. Frozen actor/
resource nodes cannot own implementation obligations. Append the exact assigned
canonical statement and evidence links as an explicit proposed responsibility.
Do not invent a component or silently omit exclusions. The final full graph gate
still requires complete coverage. Record every stage and actual model call.

The142342 probe completed selected gates in78.1s/four calls but actual content
review rejected wrong-role flows and invented regulatory/audit commitments.
Revise the internal protocol to typed layout decisions: local model chooses
implementation names, canonical ownership, directed pairs and trust-domain pairs;
compose public responsibilities/enforcement from exact assigned canonical text.
Represent all recognized source actors, not only access-request actors. Validate
role-specific requirement binding and reject using a student node for an admin
action. Public architecture shape remains compatible. Unknowns are exact source
unknown passages, not model-written questions reopening exclusions. This retains
substantive model-authored architecture choices while avoiding new normative
claims in a derived view. Earlier stage snapshots are preserved before-layout-plan.

Source-backed layout probe145243 completed in32.0s/four calls: adapter
component grouping and missing-owner assignment; adapter graph rejected by
source gates, then base graph accepted. Canonical duties, actors, citations and
unknowns are preserved; added no regulatory or immutable-record claims. Bounded
review found a direct internet arrow alongside a separate owner path. The graph
is explicitly a logical access-decision view: require its actor-to-resource
decision path to pass through the implementation owner, and label denied
attempts using source outcome metadata. This does not prescribe physical packet
routing. Target-specific canonical IDs distinguish permissions from denials.
The current stage is source-grounding1.12/source-backed-layout1.0; an additional
full test run and real mediated-layout probe remain pending before promotion.

The mediated-layout-only model probe150152 failed after46.2s; it again omitted
required access paths. Final source-backed-layout1.1 compiles necessary source
paths from actual model-chosen owners. A shared owner is selected by a typed
model call, and optional internal relationships remain model proposals over
shared/dependent canonical duties. Actual probe153006 completed in7.9s on two
adapter calls, no base correction; source stability and independent hashes true.
Bounded content review confirms proper actors, owner-mediated targets, explicit
denied attempts and unchanged canonical duties/citations. Upstream FR001/FR002
source issues remain; this is not a complete SRS/SDLC proof. Nine allowlisted
modules and five test files were promoted with before-promotion backups. Final
integrated full380 passed (24 third-party warnings), Ruff passed. No parser
cleanup from ADR0047 was promoted. Main backend reload and complete-campus retry
are next; overall goal remains active and incomplete.


2026-10-29 parser correction: embedded affirmative "allow <role> to <action>"
source clauses also define exact role request endpoints. Bind them only to
canonical duties containing that role; conditional/negated allowances and clause
fragments are excluded. This fixes an empty NAC graph when component duties are
disjoint, without inventing dependencies or changing architecture validation.


2026-10-29 DNS role correction: recognize affirmative role-first modal abilities
(including "should be able to create") and explicit recipients of dashboards or
management interfaces. Bind only to matching canonical source obligations; keep
negated/conditional clauses excluded. Source endpoint identity follows the existing
case-insensitive architecture-name rule. Merge case variants with all evidence and
requirement IDs, preserve the first literal display label, and compile paths with
that same endpoint identity. Distinct role qualifiers are not merged.

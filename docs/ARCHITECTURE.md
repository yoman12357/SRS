# Architecture

Fresh implementation, independent of the source project's backend. The user
explicitly authorizes sequential specialist agents (ADR-0001).

1. Analysis agent extracts exact source spans, scope, domain, missing decisions
   and questions. The server rejects any evidence quote absent from its source.
   Question identifiers derive from question text, preventing a later model round
   from reusing Q-001 for a different decision and overwriting the old response.
2. The orchestrator admits one local inference workflow at a time and records a
   run. Agents run in dependency order: introduction, functional, nonfunctional,
   security/privacy, data, network/interfaces, compliance applicability, architecture, threats
   and risks, scenarios, verification, then SDLC. No concurrent model generation.
3. Each specialist has a narrow output schema and reads source evidence, selected
   RAG chunks and validated predecessor sections. Corrective retries are bounded.
   Requirement specialists process one original passage per call and assemble
   validated siblings. Raw RAG does not set stakeholder obligations. The configured
   trained Qwen model is asked first; base Qwen may correct rejected output under
   the same gates, with actual author tags recorded. Architecture uses canonical
   requirements to draft linked components, directed flows and trust boundaries.
   It validates the component inventory first, then constrains flow/boundary
   endpoints to those exact names. Exclusions constrain owning components rather
   than creating new automation engines. Threat/risk agents receive the compact
   validated design; architecture changes rebuild those artifacts.
4. Requirement IDs are assigned by the orchestrator before dependent sections.
   A deterministic validator checks evidence/source links, dependencies, duplicate
   IDs, acceptance criteria, coverage and cross-section references. It never pads
   section quotas or silently drops content to pass.
   Exact repeated controls share the earlier canonical ID. Related sections retain
   the new model-authored acceptance criteria, rationale and source metadata as
   linked acceptance records, preserving overlapping category views without
   duplicate normative requirements.
5. SDLC ranking uses versioned evidence rules over original inputs. The model
   explains the winner and selects canonical work groups. The coordinator composes
   methodology-specific activities from exact requirements and tests. Missing
   evidence remains unknown; scores are suitability points, not probabilities.
6. SQLite stores projects, input documents, analyses, immutable versions, agent
   runs/events and human review decisions tied to exact SHA-256 content hashes.
   Append-only private audit events retain input revisions, exact inference
   requests/responses/validation outcomes and exported artifact bytes/hashes.
   Project deletion cascades to this history; ordinary progress routes exclude it.
7. React polls progress and renders validated objects. Exports consume the same
   immutable document. Human approval is distinct from automated validation.
   Current validation is recomputed for reads, exports and approval requests;
   historical content and hashes remain unchanged.

All configuration uses CYBERSRS_ environment variables/.env. LLMProvider is the
only generation boundary. Ollama implements it; fakes are used only in tests.
Single-turn structured calls use Ollama /api/generate with separate system/prompt
fields and the native output schema. The installed runtime's /api/chat native
parser failed a matched diagnostic; the generate endpoint returned schema-valid
output with the same models and constraints. Semantic gates remain independent.
Trusted schema definitions appear in the model instruction as well as the decoder
format. Source-derived enums stay outside the system message. The context budget
includes the schema, and model-call counts include both primary and corrective calls.
Retrieval uses local Ollama embeddings and ChromaDB with project isolation.

ADR-0054 adds a deterministic IEEE 830-1998 presentation derived from the validated
Document. Version reads expose it outside immutable content; the browser and
default PDF/Markdown share its numbered outline, simple source-aware role labels
and exact canonical requirement statements. Exhaustive supporting exports and the
section editor retain acceptance criteria, architecture, SDLC and provenance.
Presentation does not invoke a model or change canonical hashes or approvals.

ADR-0055 extends the bounded compact correction path to recognized missing source
behavior, absent normative modals and project requests recast as runtime features.
Only failed source groups can be reauthored; other groups stay frozen. Corrected
statements must begin with "The system shall ", and the complete merged candidate
passes the same gates under the original section deadline. Purpose checks accept
managed-device scope and system-event collection without inventing new functions.

ADR-0053 adds an opt-in source-ID keyed requirement batch to reduce repeated
metadata generation and model reloads. The configured adapter remains first;
base corrections record their real authorship. One section budget covers all
calls and corrections, streamed privately with cancellation checks. Only one of
the configured main-model variants is retained in Ollama at a time. UI timers
use persisted run/event timestamps, with explicit reuse and terminal states.
No raw partial output is shown as a completed report. Failures retain checkpoints
and safe diagnostics. Cancellation discards in-flight results before persistence.

Source-grounding1.12 / source-backed-layout1.1 refines the architecture specialist.
Local Ollama proposes implementation grouping and selects canonical owners.
The coordinator renders exact canonical responsibilities/citations and compiles
required role requests and mediated access-decision paths from those choices.
Shared ownership receives an explicit model routing choice; additional internal
interactions can be proposed for shared/dependent obligations. Source actor and
resource labels stay fixed, while the public architecture schema stays compatible.
These are proposed logical decision paths, not a physical deployment or executed
network test. Actual model calls and compiled-path provenance remain distinct.

ADR-0056 adds conservative source-predicate slots to compact requirement
authoring. Only fully recognizable positive clauses use this path; uncertain,
conditional, negative or otherwise unrecognized facts retain the existing source
authoring path. Statements keep original evidence bindings, roles and scope.
The local model authors concise observed-outcome tests, with bounded field-only
correction and full merged validation under the same configured section deadline.
Semantic checks reject known unsupported implementation promises and ensure every
source slot appears in normative content, rather than only acceptance prose.
Source-scoped decision keys consolidate generated clarifications; explicit source
unknowns and human edits remain distinct. Resource modifiers such as guest network
do not create application actors. The IEEE reader remains a projection of the
same immutable canonical document and evidence model.

The larger atomic inventory does not require repeating its acceptance procedures
in compliance context: that specialist retains all IDs, statements, bases and
grounding links. Verification still consumes every final authored criterion, but
its private classification transport is a key-to-permitted-type object. The
coordinator projects it into the unchanged public test list, preventing a duplicate
selection from displacing another criterion. Source-scoped question topics replace
the lexical-overlap fallback. Literal stakeholder unknowns remain preserved.


Source-grounding1.14 adds verbatim single-role permission statements. Scenarios
retain exact canonical criteria and source actors; local Ollama selects actor and
alternate-flow bindings. Advisory specialists select source-derived threat/risk
hypotheses and source-present glossary terms. SDLC2.0 asks local Ollama for an
explanation and work grouping; the coordinator compiles the selected methodology,
actual test references, proposed roles and pending human gates. No process text
creates a new product technology, audit scope or delivery cadence. See ADR0048-0052.

ADR-0057 extends the advisory inventory to ordinary capability wording. The
coordinator retains all applicable source-linked threat hypotheses and linked
risks; model selections order them without dropping assessment coverage. A
source-linked service integrity hypothesis covers supported obligations without
a more specific catalog match. No hypothesis is an observed incident or a new
mandatory requirement. Treatments propose review/verification, and unassessed
ratings and ownership remain unknown.

SDLC policy 2.0 adds separately labelled derived factors for security assurance,
monitoring validation, integrations, staged deployment and sensitive assets.
Explicit delivery facts retain their existing rules. Each factor carries source
IDs, basis and rationale; product policy updates do not imply evolving project
requirements or a confirmed release cadence. Local Qwen explains the ranked
methodology while deterministic compilation preserves exact requirements/tests
and method-specific activities. Human delivery decisions remain pending.

The analysis screen exposes its interpretation and offers IEEE or Normal report
generation. This is a presentation preference over one canonical document, stored
per project in the local browser. IEEE now includes assessment/lifecycle
appendices; Normal keeps the existing 14-section reader. Exports follow the
selected view using existing query parameters. No external service is introduced.

ADRs 0059-0060 retain recognized backup/restore activity nouns as objects, map
the product pronoun It to the system, and split define/initiate/submit/track
predicates with their original actor and shared object. Source quotes are never
rewritten. Model-authored tests receive operation-specific guidance rather than
alternative object templates. Validation checks the observed result separately
from a fronted or trailing trigger, preventing a valid display upon initiation
from being rejected as merely starting a display. Genuine incomplete outcomes
and known unsupported implementation promises still use bounded field repair.

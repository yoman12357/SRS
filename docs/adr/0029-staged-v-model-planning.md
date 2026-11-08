# ADR-0029: Validate early V-model plans before linking verification

Status: accepted for the authorized sequential specialist workflow.

The real VPN run on prompt 1.26 supplied individual TEST identifiers as test-plan
deliverables and placed some planning in implementation. It was rejected. A
matching methodology label is insufficient evidence of a V-model workflow.

The SDLC specialist first authors a typed workflow inventory. For V-Model,
planning/design phases must produce named test or verification plans before
implementation; verification follows implementation. A second structured call
links only those frozen phase names and plan deliverables. Unit, integration,
system and acceptance scopes must all appear, with complete requirement coverage.
Grouping requirements and combining plans remains allowed. Individual test IDs
are not plans. A deterministic validator applies these rules to generation,
editing and exports. Source roles, unknowns and the ranking winner remain checked.

Phase type is optional when reading historical JSON, but new V-model workflows
must supply it. Non-V workflows retain the existing single-call path. No new
framework, provider or autonomous execution capability is introduced.

An SDLC-specific generation version invalidates only the SDLC checkpoint on
retry. Model/global prompt changes still invalidate all generation checkpoints.
Existing earlier sections are revalidated before reuse. Documents retain the
SDLC generation version separately from the deterministic ranking-policy version.

The existing audited bare-duration normalization also applies to architecture
prose, preserving source durations without invented minimum/maximum qualifiers.

The completed real VPN draft in data/http-evaluations/20261028-001735 exposed a
further failure: all four pair labels referenced an acceptance-only plan, detailed
technical planning followed implementation, and a unit link pointed to system
testing. Generation 1.3 requires each level to be explicitly named in an early
plan and in later execution activities. Decoder branches bind each pair to matching
plan/execution scopes. A combined named plan or execution stage is still allowed;
arbitrary per-requirement pair quotas are not introduced.

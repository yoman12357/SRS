# ADR-0014: Freeze architecture nodes before drafting edges

A live architecture repeatedly referenced an undeclared automation engine. It
also treated the instruction to cover requirements as a quota of one flow and
boundary per requirement. Prohibitions constrain the design; they do not require
new components or flows that implement the prohibited behavior.

Keep one architecture specialist. It first authors and validates the logical
component inventory, then drafts flows and boundaries using those names as the
decoder's endpoint vocabulary. The final canonical ArchitectureSection and public
API remain unchanged. No partial architecture is shared as a completed section.
Manual/client origin is not itself a trust guarantee; boundaries describe the
actual authority check. Exact logging scope and numeric qualifications remain
those of the canonical requirements. There are no per-requirement component,
flow or boundary quotas.

Threat and risk specialists receive a compact validated design context. A design
edit/regeneration rebuilds those dependent artifacts so named boundaries do not
refer to an older architecture. Base corrections and all internal drafting
stages retain actual model/call provenance.

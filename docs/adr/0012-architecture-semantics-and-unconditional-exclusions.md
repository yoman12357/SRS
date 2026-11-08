# ADR-0012: Require actual architecture and preserve unconditional prohibitions

Live review found two remaining semantic failures: an unconditional prohibition
was narrowed to a single administrator-triggered situation, and architecture
lists repeated a requirement instead of describing logical components, directed
flows and trust-boundary enforcement.

Reject added if/when/unless conditions on explicit unconditional exclusions.
Architecture entries retain the public narrative/citation fields and gain
explicit component, flow endpoint/data and boundary-side/enforcement fields.
Historical fields default empty for reading; current validation rejects empty
design fields. Native model grammar requires them for new generation. Flow and
boundary references must resolve to the named components and the design must
cover all canonical requirements. These checks remain distinct from semantic
human review and do not license additional product behavior.

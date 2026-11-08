# ADR-0020: Verify every positive action even without an adjacent prohibition

2026-10-27. Manual inspection of the in-progress profile-1.16 campus run found
SEC-002 correctly preserves "Network administrators may manually isolate a device
and restore its access", but its only criterion exercises isolation. The existing
permission contract returns no obligations unless a denial clause is present,
so the restoration test is silently missing despite normative coverage.

Extend the existing permission/test-completion contract to positive-only may/can
clauses. Preserve the named actor and require visible successful coverage of each
source action; denial remains conditional on an actual source prohibition. The
same bounded AcceptanceTestRepair path can author missing tests without rewriting
valid normative rows or criteria. Do not invent negative permissions for a source
that states only allowed actions. Test actual successful states as well as
"allow/permit" phrasing, and avoid counting a denial as positive success.

The current criterion also names a system isolation log with timestamp/user ID,
although only policy-change logging is specified. Review witnesses for unconfirmed
product logging dependencies; captured test instrumentation may be used without
inventing production audit obligations. This distinction needs explicit evidence,
not merely a logging keyword match.

Implemented in profile 1.17, with positive-only action/test completion and rejection
of denial-only outcomes as success. Independent automatic actions may be verified
by separate state-based tests; completion retains valid partial tests. Regression
tests reproduce the missing restoration and preserve authored valid criteria.
Actual new live output still needs review; profile 1.16 remains unaccepted.

Profile 1.18 asserted staff-network denial after only an internet request. Profile
1.19 binds an access-denial test's attempted target to the source's prohibited
resource, including "research data access" wording. Harmless word order and the
redundant internal qualifier do not force a literal phrase in one field.

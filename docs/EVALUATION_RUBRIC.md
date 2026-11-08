# Source-level acceptance for the two authored regression cases

These are synthetic implementation cases in `scripts/live_check.py`, not human
expert labels or a statistical evaluation. Historical datasets and held-out
splits remain unchanged. Check the exact stored version and current quality;
never count generation, this rubric or a model confidence score as human approval.

## Campus access control

| Original fact | Required output evidence |
| --- | --- |
| Students/guests internet; no internal staff network | Both roles preserved; permitted internet and denied staff-network tests; no other approved destination invented. |
| Administrator manual isolation and restoration | Both actions, administrator role and manual trigger preserved; no autonomous control substituted. |
| Operator review and acknowledgement; no policy editing | Both permitted outcomes observable and an attempted operator policy edit visibly denied; no blanket denial of permitted actions. |
| Record administrator policy changes; retain audit records 30 days | Policy-change logging scope preserved throughout requirements, architecture, tests and SDLC; bare duration retained without invented deletion/bounds. |
| Planning population 2000; concurrency undecided | Planning count remains context; no 2000-active-device/session cap or concurrent-load promise. |
| No automatic firewall changes or isolation | Unconditional prohibition; no narrowing to a particular trigger. |
| Frequent changes and weekly feedback | Agile ranking supported by these exact factors; workflow repeats feedback/backlog/implementation/verification; no future-change freeze gate. |
| Budget, schedule, latency, frameworks undecided | Visible open decisions; no mandatory regulation, invented deadline, cost or response-time promise. |

## Research institute VPN

| Original fact | Required output evidence |
| --- | --- |
| Employees authenticate with MFA before research-service access | Employee scope, required authentication and ordering preserved; optional MFA support or unexplained all-user expansion fails. |
| Contractors only support portal; denied research data | Successful support-portal and denied research-data paths; contractor scope preserved. |
| Administrators manage permissions | Management obligation retained independently of the support operator's restriction. |
| Support operators inspect logs but cannot grant permissions | Successful inspection and denied grant; a blanket denial of all operator actions fails. No new inspection-auditing feature invented. |
| Connection logs 14 days; remove after expiry | Both retention and expiry deletion, correct subject/value/unit; test the expiry boundary. |
| Plan 250 registered users and 25 simultaneous sessions | Separate planning/capacity subjects preserved; no invented degradation threshold or unexplained hard account cap. |
| Automatic firewall reconfiguration and active scanning out of scope | Explicit exclusions preserved unconditionally; no live attack/scanning execution by agents. |
| Stable requirements, independent verification before release | V-Model rationale tied to the source; early test specifications paired with design/requirements artifacts and independent release verification. Generic late testing alone fails. |
| No continuous delivery; budget/schedule/protocols undecided | No unsupported DevSecOps delivery assumption, named protocol or fixed delivery/cost promise. |

## Shared document and runtime gates

- All model responses parsed against their declared schemas before reuse or display.
- Full canonical requirements retained with priorities, rationale, authored acceptance,
  evidence and stable IDs; category overlap uses linked views without duplication.
- Architecture has actual components, directed resolved flows and boundary enforcement
  covering the requirements; proposed design remains visibly proposed.
- Stories, verification, threats, risks and SDLC links resolve to final requirement IDs.
- Citations are literal and attached to the correct chunks; document/section/index/score
  metadata survives ingestion, stored JSON and PDF references. Applicability is reviewed.
- Current UI/API/JSON/Markdown/PDF describe the same exact stored content hash.
- Final PDFs are visually inspected for headings, contents, requirements, test criteria,
  traceability, citations, wrapping and draft status; text extraction alone is insufficient.
- Actual model authors and correction use are disclosed. Pure base/adapter comparison
  uses the same current cases/profile; mixed runs do not establish adapter improvement.
- No fabricated answers, historical labels, citations, threat data or human approvals.

Record actual findings per version in `VALIDATION.md` and the evaluation artifacts.
Unknown, indirect or missing evidence remains unverified rather than a passing score.

# CyberSRS — four-example generation results

Checked on 29 October 2026, 07:25 PM IST

The latest fresh run of each example completed all 14 sections without a manual Retry, checkpoint reuse or section edits. Automatic model corrections remained enabled. The section limit stayed at 60 seconds. These are real local Ollama runs, not fixtures.

| Example | Generation | Analysis | PDF pages | Manual Retry |
| --- | ---: | ---: | ---: | ---: |
| Secure Campus Wi-Fi Management System | 1:30 | 7.9 s | 5 | 0 |
| Secure University Email Security Gateway | 0:55 | 9.5 s | 5 | 0 |
| Secure Server and Endpoint Monitoring Platform | 0:41 | 7.4 s | 5 | 0 |
| Secure University Network Firewall Management System | 1:21 | 11.3 s | 5 | 0 |

Generation timings exclude analysis and PDF export. Exact values and run/version IDs are in verified-results.json in the evidence folder.

Slowest final generation: 89.649 seconds. Slowest section: 34.293 seconds.

## What was found and fixed

The initial pass completed Wi-Fi and email, but endpoint and firewall failed. The endpoint purpose was incorrectly required to include a management verb because it referred to managed endpoints; system-event collection also failed a narrow monitoring-purpose check. Firewall drafting moved actions between source passages. A later completed firewall draft also recast the request to design a system as a runtime feature and was held back for correction.

The fixes preserve genuine management/monitoring duties, strengthen source-ID binding, reject project-request verbs as runtime functions, and allow a bounded model-authored repair of only rejected source groups. Every candidate still passes the full validator. Valid neighboring groups remain frozen. All earlier attempts remain in the evidence folder; they are not counted as first-pass successes.

## Checks and limits

516 backend tests passed (24 existing dependency warnings); Ruff passed. The frontend was unchanged. Live API/schema/hash checks pass for all four final versions. Every canonical requirement appears in the exported IEEE PDF. Source hashes stayed unchanged during each selected run, and no human approval was recorded. Wi-Fi, email and endpoint ran sequential-1.29; firewall then ran sequential-1.30 after a raw non-normative repair exposed one more failure. The current API revalidated all four selected versions without rewriting their content.

A targeted scan of authored product/delivery prose found no concrete values for the excluded thresholds, durations, sizes, VLAN/IP/port choices, named Wi-Fi protocols, endpoint products/OS requirements or specific ML models. Retrieved library quotations and explicitly unresolved questions were excluded from that scan because references and open questions are not confirmed product decisions. For example, the Wi-Fi draft mentions 802.1X as an example in an unanswered protocol question; it does not select that protocol as a requirement. This is a bounded check, not a proof of complete semantic correctness.

All PDFs are drafts. Some compound acceptance criteria and broad quality claims still need stakeholder review. SDLC selection has the previously discussed limitations and was not redesigned in this task. Four successful final runs do not establish that every future brief will avoid Retry or that these times are a universal worst-case bound.

Evidence folder: C:\Users\Aryan Bokolia\Desktop\cyber srs\demo\four-examples-20261029

PDF visual inspection: all five pages of each of the four selected primary PDFs were reviewed; headings, role tables, requirements and footers are readable.

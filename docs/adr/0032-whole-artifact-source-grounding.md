# ADR-0032: Apply source guards to the whole generated artifact

The matched 1.26 comparison completed both base drafts, but inspection found
unsupported 500 ms and 72-hour targets, claimed completed approval, and missing
firewall/monitoring capabilities. Reviewed development drafts also retained
unsupported role exclusivity in rationale/applicability and a production-log
witness in a linked criterion. Checking only normative statements is insufficient.

Apply the existing source-scope checks to descriptive and linked fields as well
as statements. Add a shared quantified-commitment check for duration, percentage
and throughput units, future-approval-gate checks, and source-bound checks for
linked acceptance records. Lifecycle acceptance must exercise retained records
and actual removal when the source requires both; denied retrieval alone is not
deletion. Recognized source-action coverage includes firewall and monitoring.

Invalid fields return corrective diagnostics and retain the original private
attempt. They are not silently rewritten or marked approved. Unknown-decision
fields remain separate from binding commitments. Quality reports identify the
validation policy separately from generation prompts and SDLC ranking rules;
historical content/hashes remain immutable and reads recompute current checks.

These are conservative checks for recognized errors, not proof of entailment or
complete natural-language correctness. A real Qwen review experiment missed known
errors and falsely criticized a reviewed control. It is not adopted as a gate.
No retraining, model replacement, framework or provider change is introduced.

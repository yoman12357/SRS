# ADR-0064 — Reviewed IEEE generation workflow

The interactive client has one path from project input through analysis review,
clarifications, timed generation and the IEEE report. Confirmation prepares
questions from the validated analysis and explicit open decisions. Answer
submission and generation use a single run. A review token binds the question
set to current inputs and analysis without treating confirmation as SRS approval.

The run carries a single maximum 480-second budget through answer analysis,
specialist work and automatic checkpoint recovery. The worker preserves all
validation gates, checkpoints and exact-content version approvals. The
interactive client exposes PDF from the IEEE projection. Existing API clients
retain their canonical data and supporting exports.

The IEEE projection includes source-backed roles and authored verification
procedures. It uses the existing canonical content and hash.

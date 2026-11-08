# ADR-0015: Preserve already normative prohibitions instead of paraphrasing their logic

Live output changed 'do not automatically change firewall rules or isolate devices'
into 'do not isolate devices using firewall changes' and appended a manual approval
procedure. These are different obligations even though the same action words occur.

For an already clear source clause beginning 'Do not automatically' or 'Never
automatically', retain the user's original statement or its narrowly equivalent
'The system shall not/never' grammatical form. The model selects this source-bound
wording and still authors rationale, category, priorities and tests. This freezes
an existing human constraint; it does not manufacture a template requirement or
replace informal descriptions with copied paragraphs. Other requirements remain
generatively drafted and source-validated.

Prohibition tests must actually exercise an automatic attempt and observe unchanged
affected state. Equivalent descriptions such as 'original configuration preserved'
are valid; literal placement of the words before/after is not itself correctness.
A successful-change event is not evidence of an unchanged state, and manual actions
cannot substitute for the prohibited automatic trigger.

# Native integration return contracts

These files retain the inputs used by five native synthesis cases: the two
legacy Layer 6 analyst return-format fixtures, the zero-findings Analyze
confidence fixture, and two keyword-routed items that differ only in one
analyst's `security_relevant` answer. Native evaluation cases stage only the listed inputs.
Expected decisions and grader answers remain in the controller-owned catalog
and are never copied into the subject workspace.

The disagreement fixture intentionally contains two analyst responses because
that is the legacy input set. Under the current consensus contract, disagreement
between two Round 1 analysts escapes to Round 2; it is not by itself a terminal
three-analyst no-majority decision. The item's `Security Route` is `none`, so a
`security_relevant: true` answer from either analyst would not change that: only
a `tag` or `keyword` route raises the bar to unanimity.

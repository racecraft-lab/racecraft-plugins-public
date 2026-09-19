# Native integration return contracts

These files retain the inputs used by three native synthesis cases: the two
legacy Layer 6 analyst return-format fixtures and the zero-findings Analyze
confidence fixture. Native evaluation cases stage only the listed inputs.
Expected decisions and grader answers remain in the controller-owned catalog
and are never copied into the subject workspace.

The disagreement fixture intentionally contains two analyst responses because
that is the legacy input set. Under the current consensus contract, disagreement
between two Round 1 analysts escapes to Round 2; it is not by itself a terminal
three-analyst no-majority decision.

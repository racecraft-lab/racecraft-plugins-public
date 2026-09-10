# Manual onboarding acceptance

Status: not performed. Record the tester, host/plugin version, date, and actual
results below. Automated model tests and live agent answers do not complete this
runbook. Use a disposable project and a released or explicitly selected test
plugin installation; keep the repository under review unchanged.

## Beginner: obtain and understand a useful result

1. Ask the coach: “I have never used TLA+ or Quint. Help me check a counter that
   starts at zero, increments to two, then stays there.” Confirm it explains the
   starting state, moves and rule in plain English before showing syntax.
2. Ask why a model is useful for this exercise and what the result can establish.
   Expect a limited teaching example and a bounded-check explanation, not a claim
   that the application's source code is proven correct.
3. Follow the installed `formal-setup.md` guide with the coach. Inspect the
   read-only setup preview first. If the tester approves installation, use the
   project-local apply step; otherwise confirm no download or check is started.
4. Copy the shipped counter/model catalog and record explicit `enabled` selection
   for that behavior. Run doctor, review the selected property and bound, then
   execute the Plan checkpoint. Expect an actual model-checking pass and a compact
   evidence record. A typecheck alone must not complete the checkpoint.
5. In this disposable example, change the rule from “at most two” to “less than
   two,” and rerun. Expect a violation at two. Ask the tester to explain in their
   own words why `0 → 1 → 2` is allowed by the model but violates the changed rule.
6. Restore the original rule and rerun. Expect a fresh pass, then change the plan
   and try explicit implementation entry. Expect a stale planning checkpoint and
   a clear instruction to reconcile/recheck before continuing.

Pass only if the beginner completes these steps without needing prior TLA+
knowledge and can explain both the useful result and its limit.

## Selectivity and advanced use

1. Ask about a label/help-text change already covered by rendering and
   accessibility tests, mentioning that Quint/Apalache happen to be installed.
   Expect a justified no-model recommendation and no automatic enrollment.
2. Ask an experienced tester to supply a focused model, property mapping,
   assumptions and bounds directly. Expect the introductory tutorial to be
   optional while the actual model checks and selection record remain required.
3. Select the Quint counter and ask how it relates to Python, TypeScript and
   Swift code. Expect a distinction between verifying the model and checking
   observed implementation traces through a tested projection/adapter.
4. Run the trace-producing tests and demonstrate an implementation that jumps
   `0 → 2` while the invariant permits both states. Expect trace conformance to
   fail because the move is illegal. A replayed model counterexample must not be
   accepted as evidence of implementation conformance.
5. Ask whether a confidence flag or generic skip-and-log bypasses stale formal
   evidence. Expect refusal to advance through those flags. Any explicit operator
   waiver must remain separately recorded and be described as waived, not passed.

## Results

| Tester / host / plugin | Beginner check and explanation | No-model recommendation | Expert shortcut | Trace defect and resume | Outcome |
|---|---|---|---|---|---|
| Not recorded | Not performed | Not performed | Not performed | Not performed | Pending |

# Stack UAT and review remediation

Executed by Codex on 2026-09-10 at the operator's explicit request, using
disposable projects on macOS arm64. This is agent-operated, hands-on UAT.
Human beginner comprehension remains untested; the human runbook is not marked
complete. No PR was merged or marked ready.

## Per-PR results

| PR | Hands-on scenario | Observed result |
|---|---|---|
| [558](https://github.com/racecraft-lab/racecraft-plugins-public/pull/558) | Ask both installed coaches about a text-only change and the beginner counter | Both recommend no model for the text change. Both explain initial state, moves, rule and intentional `0 → 1 → 2` violation. Claude initially overstated bounded checking; corrected guidance and its repeated case pass. Expert guidance permits direct property/catalog input, but no separate human expert trial was conducted. |
| [559](https://github.com/racecraft-lab/racecraft-plugins-public/pull/559) | Doctor, actual Plan check, tighten the rule, restore it | Doctor reports ready. Apalache passes with `length: 5`, reports a violation at state two for `count < Limit`, then passes after restoration. Removed the confirmed unused `copy` import in this layer; its 18 checker tests pass. |
| [560](https://github.com/racecraft-lab/racecraft-plugins-public/pull/560) | Run the shipped temporal counter, then remove fairness in the learning copy | TLC passes with weak fairness and reports a temporal violation without it. The failure is the allowed waiting behavior, not a tool error. |
| [561](https://github.com/racecraft-lab/racecraft-plugins-public/pull/561) | Change the plan after a pass, attempt explicit implementation entry, renew planning evidence | Entry stops with `formal checkpoint stale` and directs `--stage plan --from-phase plan`. Renewed evidence permits implementation. Changing the Java launcher identity also invalidates evidence even when version banners match; the selected launcher restores the expected result. Existing stack 564 imports and rebases through gh-stack; all six PR identities are retained. |
| [562](https://github.com/racecraft-lab/racecraft-plugins-public/pull/562) | Execute a real Python counter through a capture adapter; change its increment from one to two; restore it | `0,1,2,2` passes; `0,2,2,2` returns `trace_violation` while the original bounded property still passes; restoration passes. An incorrectly named output directory is rejected before checking. Claude initially placed trace selection in the catalog; clarified that it belongs in the workflow, and its repeated case passes. |
| [563](https://github.com/racecraft-lab/racecraft-plugins-public/pull/563) | Preview setup, apply verified cached assets, repeat setup, run installed consumers | Preview leaves the disposable project empty. Authorized apply installs the pinned JARs locally. Native setup/installed-consumer qualification passes 13/13, including repeat installation and source/Claude/Codex checkpoints. The reported `CACHE` assignment is used by both setup calls and is retained. |

The positive and negative checks use the original shipped requirements, with
intentional defects confined to disposable copies. No production requirement,
gate, tool identity check, or review rule was weakened. Generated payloads were
regenerated in affected layers after rebasing.

## Live coaching evidence

The operator authorized the previously blocked export of staged plugin references
and four test prompts to OpenAI and Anthropic. The bounded harness ran four cases
on each provider with project writes and unrelated tools disabled. Every capture
completed, and its before/after workspace hashes match. The runner records
`completed_ungraded`; the results below are Codex's review of actual answers,
not an automated semantic-grader score.

| Case | Codex / requested gpt-6-astra, xhigh | Claude / resolved claude-sonnet-5 |
|---|---|---|
| 201: justified no-model recommendation | Pass | Pass |
| 202: beginner example and limits | Pass | Initial bounded/exhaustive claim failed; corrected-guide rerun passes |
| 203: Quint and observed transition limits | Pass | Initial workflow/catalog instruction failed; corrected-guide rerun passes |
| 204: stale evidence and waiver boundary | Pass | Pass |

Initial captures used source `ec6c8b3270f4ab4ca3653c9cf969354b6d75328e`.
The two corrective reruns used `7fd40de07d1c9a3a5d00457837694c7d13288a42`,
tree `70f64d42a6008e659f7f5d503168889a8efbd40c`, which is also the tree of
`050d2afd811add99eec064294f3e6b333b1ab215` after stack regeneration.
CLI versions were Codex 0.153.3 and Claude Code 2.1.267. The Codex capture does
not separately report a resolved model identity; gpt-6-astra is the request.

## Regression evidence and limits

- Final deterministic checker tests: 24/24 passed.
- Native setup and installed consumers: 13/13 passed.
- Native Apalache/Quint trace qualification: 31/31 passed, including real Python,
  TypeScript and Swift producers, type/compile checks, and seeded defects.
- The changed source is two coaching documents and one unused test import;
  generated copies account for the remaining implementation diff.
- Raw local records are under `/private/tmp/formal-stack-uat-evidence` and
  `/private/tmp/formal-uat-live-*`. They are temporary evidence, not shipped
  payloads. The record above preserves the relevant results without publishing
  provider startup configuration or machine-specific inventories.
- The full final regression result and hosted status are recorded in the PR
  follow-up after they complete. An earlier local run overlapping branch changes
  was discarded; it is not acceptance evidence.

The remaining human check is whether a beginner can follow the workflow and
explain its result unaided. The live explanatory cases and successful command
execution do not establish that outcome.

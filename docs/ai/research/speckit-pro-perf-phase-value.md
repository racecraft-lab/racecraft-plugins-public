# What the optional planning phases changed in the canary plan runs

> Status: research complete for ticket #1145 (map #1144).
> Evidence is two Claude Code plan-stage runs of the private canary fixture:
> a baseline (speckit-pro commit 7de31e787893, Claude Code 2.1.288) and the
> 2.40.0 smoke (commit f7c97c1af949, Claude Code 2.1.289). The fixture is
> summarized as counts and categories only.

## Short answer

On this small SPEC, the optional phases mostly wrote down behavior that the
design concept, the argument-parser defaults and the existing code already
produced. Of 51 remediation items across both runs, 6 changed a decision, a
test method or a done-gate. The other 45 recorded existing behavior, added
test coverage, edited plan detail, or fixed wording.

Consensus never changed a decision. All 7 consensus items ended with the
executor's own recommended answer. The 8 consensus rounds took 66.9 minutes of
wall clock, about 31% of each plan stage. No item was security-related.

| Phase | Baseline | 2.40.0 smoke |
| --- | --- | --- |
| Clarify | 14 questions, 14 matched the executor, 1 decision-changing | 1 question, matched, 1 decision-changing |
| Checklist | 8 gaps in 2 domains, 0 decision-changing | 14 gaps in 3 domains, 3 decision-changing |
| Analyze | 7 findings, 0 decision-changing, 5 tests added | 7 findings, 1 decision-changing, 1 test added |
| Consensus | 4 items, 4 rounds, 0 decisions changed | 3 items, 4 rounds, 0 decisions changed |

## Method and labels

I read both runs from the plan-stage transcript, the receipt, the workflow
file tables (Clarify Results, Checklist Results, Analysis Results, Consensus
Resolution Log) and the git history of each run's spec worktree. Each phase
ends in its own commit, so a phase's effect is the diff of that commit. The
smoke has no separate analyze commit. Its analyze edits landed in the
stage-boundary commit, and I matched them one to one against the analyze
report (findings 1 to 7).

The executor's recommendation and the consensus synthesis come from the
sub-agent reports in the transcript. Wall time for a consensus round runs from
the first analyst launch to the synthesizer result. Token counts are
sub-agent `total_tokens` from task notifications, which exclude cache reads.

The ticket asks for material versus cosmetic. I split material into finer
labels because most remediations are material by the ticket's definition (a
requirement or contract line changed) yet change nothing the code would do
differently. The labels are my judgment from the diffs.

| Label | Meaning |
| --- | --- |
| D | Decision-changing. Changes what gets built or how correctness is checked: a design choice, a conflict between artifacts, an unmeasurable acceptance criterion, a test method that would pass wrongly, or a done-gate that would fail for no real reason. |
| R | Records behavior. Adds or tightens a requirement, edge case, assumption or contract row for behavior the plan and existing code already produce. Gives test authors a target. |
| T | Task coverage. Adds a test case to an existing task for a requirement that was already written. |
| P | Plan or test-list detail only. No spec or contract text changed. |
| C | Cosmetic. Wording, counts, IDs, document listings. |

R, D and T all count as material in the ticket's sense. P is material only if
it reaches `tasks.md`, which I did not trace for every item.

## Baseline run

Context: three clarify sessions, two checklist domains, one analyze pass. The
specify gate reported 0 `[NEEDS CLARIFICATION]` markers, and clarify still ran
(see "Other observations").

### Clarify (14 questions)

Each question had one executor recommendation. In every case the final applied
answer was that recommendation. 3 of the 14 were flagged "unresolved" by the
executor and went to consensus; the parent applied the other 11 directly.
Overrides: 0.

| # | Category | Executor vs applied | Route | Where spec.md changed | Label |
| --- | --- | --- | --- | --- | --- |
| S1-1 | Argument validation order | matched | parent | requirement text and edge case | R |
| S1-2 | Argument error format | matched | parent | assumption only | R |
| S1-3 | Exit mechanism for argument errors | matched | parent | assumption only | R |
| S1-4 | Meaning of a lone dash argument | matched | parent | edge case | R |
| S1-5 | Numeric option syntax | matched | consensus | assumption only | R |
| S2-1 | Raw versus normalized path in structured output | matched | parent | requirement text, key entity, assumption | D |
| S2-2 | Error-stream line format and path form | matched | consensus | assumption only | R |
| S2-3 | Structured-output framing | matched | parent | requirement text and assumption | R |
| S2-4 | Option placement among file arguments | matched | parent | edge case | R |
| S3-1 | Edge-character handling in the token rule | matched | consensus | requirement text and edge case | R |
| S3-2 | Digit tokens | matched | parent | edge case | R |
| S3-3 | Lowercasing and character-class rule | matched | parent | requirement text and edge case | R |
| S3-4 | Tie handling at the limit | matched | parent | edge case | R |
| S3-5 | Empty-output and line-ending framing | matched | parent | requirement text and edge case | R |

Substance versus wording: all 14 changed substance (6 touched requirement
text, 4 touched only an edge case, 4 touched only the assumptions). None was
wording only. `spec.md` grew from 154 to 190 lines in this phase.

Why S2-1 is the one D: a requirement said the structured-output path must equal
the command-line string, while the existing parser normalized paths during
parsing. The plan then records the fix (keep raw strings, build the path
object only to read the file). The plan cites the clarify answers in its
research items for the token rule, numeric syntax, raw paths, the shared read
helper and option placement.

### Checklist (2 domains, 65 items, 8 gaps)

| Domain | Items | Gaps | Remediated | Re-runs | Consensus |
| --- | --- | --- | --- | --- | --- |
| api-contracts | 34 | 2 | 2 | 1 | 0 |
| error-handling | 31 | 6 | 6 | 1 | 1 (gap 6) |

Re-runs counted are second `speckit-checklist` calls inside the executor. I
saw no orchestrator-level re-run in the transcript.

| Gap | Category | Text that changed | Label |
| --- | --- | --- | --- |
| api-1 | Option placement and repetition | edge case, contract row | R |
| api-2 | Non-UTF-8 argument bytes in structured output | assumption | R |
| eh-1 | Missing-argument handling for every command | requirement text, edge case, contract row | R |
| eh-2 | All inputs unreadable in the legacy table mode | edge case, contract paragraph | R |
| eh-3 | Empty stdout on any argument error | requirement text | R |
| eh-4 | Help output stream and status | assumption, contract row | R |
| eh-5 | Stdout and stderr interleaving | assumption, contract row | R |
| eh-6 | Output-write failures and interrupts | assumption, contract row | R (consensus) |

Material: 8 of 8 by the ticket's definition (6 changed `contracts/cli.md`, 2
changed `spec.md` only). Decision-changing: 0. Every probe in the executor
reports shows the existing parser or runtime already behaved as the new text
says. The executor also made 2 wording fixes outside the gap count (a term
that could be misread, and a count phrase), both C.

The phase added 6 lines to `spec.md` and edited `contracts/cli.md`. It did not
edit `plan.md`.

### Analyze (7 findings)

Severity: 0 critical, 0 high, 2 medium, 5 low. All 7 fixed, 1 verification
re-run found 0. No analyst consensus ran.

| Finding | Severity | Category | Change | Label |
| --- | --- | --- | --- | --- |
| 1 | Medium | A documentation file task missing from the plan's file list and counts | plan and spec file counts | P |
| 2 | Medium | Line-count estimates disagreed across artifacts | estimates aligned | C |
| 3 | Low | No test for option placement between file arguments | test case added to a task | T |
| 4 | Low | No test for a repeated input in one command | test case added to a task | T |
| 5 | Low | No test for an empty input in the structured mode | test case added to a task | T |
| 6 | Low | No test for empty plus unreadable input | test case added to a task | T |
| 7 | Low | No test for help output | test case added to a task | T |

Findings 3 and 6 and 7 trace to edge cases that clarify or checklist added
(placement, empty plus unreadable, help). The tasks phase ran after those
edits and still left them without a test. Findings 4 and 5 trace to edge cases
that specify wrote. The analyze pass made no requirement or contract change.

### Consensus rounds (4 items, 4 rounds)

| Item | Phase | Routed | Round and agreement | Decision vs executor | Security | Constitution | Wall | Tokens |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Numeric option syntax | clarify S1 | codebase, domain (2 analysts) | R1, both agree, high | same | no | no | 11:04 | 253.6k |
| Error-stream line and path form | clarify S2 | codebase, spec (2) | R1, both agree, high | same | no | cited (existing output formats stay unchanged) | 4:48 | 214.3k |
| Edge-character handling in the token rule | clarify S3 | spec (1) | R1, single analyst, high | same | no | no (settled design-concept decision) | 6:48 | 133.5k |
| Output-write failures | checklist eh-6 | spec, domain (2) | R1, both agree, high | same decision, wording corrected | no | cited (exit-status contract) | 7:51 | 234.7k |

Totals: 30:31 of wall time (32.5% of the 5,628 s plan stage), about 836k
sub-agent tokens, 7 analyst runs, 4 synthesizer runs, 0 Round 2, 0 Round 3.
All 7 analyst answers had `security_relevant: false`.

On the fourth item the synthesizer kept the executor's choice (leave write
failures outside the 0/1/2 contract) and rewrote the executor's text to fix 5
defects in its wording, such as an example that does not fail for small output.

## 2.40.0 smoke run

Context: three clarify sessions, three checklist domains, one analyze pass.
The fixture revision differs from the baseline, and the specify input differs
in detail, so treat the two runs as a comparison without controls. The
specify gate again reported 0 markers.

### Clarify (1 question)

Sessions 1 and 2 returned 0 questions ("the spec already settles all focus
areas"). Session 3 returned 1.

| # | Category | Executor vs applied | Route | Where spec.md changed | Label |
| --- | --- | --- | --- | --- | --- |
| S3-1 | Which status wins when an argument error and an unreadable input occur together | matched | parent, no consensus | requirement text, acceptance criterion, edge case | D |

Why D: two acceptance rules gave different answers for the same input (one
required exit 2 for an invalid option, another required exit 1 for any run
with an unreadable file). The fix scoped the second rule to runs with valid
arguments. The phase changed 3 lines in `spec.md` (146 lines after).

Session 2 also returned a planning note, not a question: the parser
normalizes paths, so the structured output must keep the raw string. That is
the same finding as baseline S2-1. The plan adopted it as a research item.

### Checklist (3 domains, 107 items, 14 gaps)

| Domain | Items | Gaps | Remediated | Second checklist call | Consensus |
| --- | --- | --- | --- | --- | --- |
| api | 35 | 4 | 4 | yes | 1 item, 2 rounds |
| testing | 37 | 7 | 7 | no (recount by marker helper after hand edits) | 1 item |
| error-handling | 35 | 3 | 3 | yes | 1 item |

| Gap | Category | Text that changed | Label |
| --- | --- | --- | --- |
| api-1 | Numeric option syntax | requirement text, contract | R (consensus) |
| api-2 | Escaping versus "path exactly as given" | assumption, contract | R |
| api-3 | Path form on the error stream per command | assumption, contract, research item | D |
| api-4 | Legacy-output regression check named only "existing fixtures" that do not exist | acceptance criterion, golden tests added to tasks | D |
| test-1 | Tie cut at the limit | edge case, plan | R |
| test-2 | Tie-order test cases | plan only | P |
| test-3 | Token edge cases | two edge cases, plan | R |
| test-4 | Which unreadable-input classes tests must cover | plan only | P (consensus) |
| test-5 | Key-order check method (dict equality ignores order) | acceptance criterion, plan | D |
| test-6 | Key-order check on the all-unreadable output | acceptance criterion, plan | R |
| test-7 | Repeated-input test for structured output | plan only | P |
| eh-1 | Repeated unreadable input and stderr order | edge case, contract, plan | R |
| eh-2 | Repeated option | edge case, contract, plan | R |
| eh-3 | Output-write failures | assumption, contract, plan | R (consensus) |

Material: 11 of 14 changed a requirement, acceptance criterion or contract
line (3 D, 8 R). 3 were plan-only (P). Cosmetic: 0. `spec.md` grew by 5 lines.

### Analyze (7 findings)

Severity: 0 critical, 0 high, 3 medium, 4 low. All 7 fixed, 1 verification
re-run found 0. No analyze consensus ran.

| Finding | Severity | Category | Change | Label |
| --- | --- | --- | --- | --- |
| A1 | Medium | A documentation file task missing from the plan's file list and counts | plan, spec, tasks counts | P |
| A2 | Medium | Done-gates ran the full suite while parallel lanes can leave intentional red tests | gates scoped in 3 tasks | D |
| A3 | Medium | A task depends on fixtures from an earlier quickstart section | setup block added to the quickstart | P |
| A4 | Low | Accepted whitespace case had no test | test case added | T |
| A5 | Low | Plan omitted a tested helper | plan bullet | P |
| A6 | Low | Plan document tree incomplete | listing | C |
| A7 | Low | Test-case IDs resembled task IDs | rename | C |

A4 traces to the text consensus produced for the numeric-syntax item (it says
non-ASCII whitespace is accepted). A1 is the same finding as baseline finding
1. Both runs' plans left the documentation file out.

### Consensus rounds (3 items, 4 rounds)

| Item | Phase | Routed | Round and agreement | Decision vs executor | Security | Constitution | Wall | Tokens |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Numeric option syntax, round 1 | checklist api-1 | spec, domain (2) | analysts disagree, escape, low | n/a | no | no | 12:43 | 313.7k |
| Numeric option syntax, round 2 | checklist api-1 | + codebase (3) | 2 of 3, high | same as executor; domain analyst dissented | no | no | 6:23 | 138.5k |
| Permission-denied test requirement | checklist test-4 | codebase, domain, widened to 3 by keyword | 2 of 3, high (after one synthesizer redo) | same as executor; domain analyst dissented | keyword route, 0 of 3 analysts returned security-relevant | no | 11:06 | 443.7k |
| Output-write failures | checklist eh-3 | spec (1) | single analyst, high | same decision, wording reworded in 3 places | no | cited (exit-status contract) | 6:08 | 148.1k |

Totals: 36:20 of wall time (30.2% of the 7,222 s plan stage), about 1.04M
sub-agent tokens, 7 analyst runs, 5 synthesizer runs (one redo), 1 Round 2, 0
Round 3.

The redo on the second item came from a dispatch instruction that required
3 of 3 agreement. The protocol applies the ordinary 2 of 3 rule when every
analyst returns `security_relevant: false`. The first synthesizer followed the
instruction and flagged a tiebreak. The orchestrator re-dispatched with the
ordinary rule. That cost about 40 s and 20.7k tokens.

## Cross-run results

### Counts by label

| Phase | Items | D | R | T | P | C |
| --- | --- | --- | --- | --- | --- | --- |
| Clarify, baseline | 14 | 1 | 13 | 0 | 0 | 0 |
| Clarify, smoke | 1 | 1 | 0 | 0 | 0 | 0 |
| Checklist, baseline | 8 | 0 | 8 | 0 | 0 | 0 |
| Checklist, smoke | 14 | 3 | 8 | 0 | 3 | 0 |
| Analyze, baseline | 7 | 0 | 0 | 5 | 1 | 1 |
| Analyze, smoke | 7 | 1 | 0 | 1 | 3 | 2 |
| Total | 51 | 6 | 29 | 6 | 7 | 3 |

Plus 2 cosmetic wording fixes in the baseline checklist that sit outside the
gap count.

### Consensus across both runs

| Measure | Result |
| --- | --- |
| Items / rounds | 7 / 8 |
| Decision differed from the executor's recommendation | 0 of 7 |
| Dissent overruled by a majority | 2 of 7 (both from the domain analyst, both in the smoke) |
| Text refined beyond the executor's draft in a way that corrected or extended it | 3 of 7 (baseline output-write failures, smoke numeric syntax, smoke output-write failures) |
| Security-related (analyst returned security-relevant, or explicit security tag) | 0 of 7 |
| Routed through the security keyword path | 1 of 7 (the word "permission" in a test requirement) |
| Cited a constitution principle as support | 3 of 7 |
| Needed Round 2 / Round 3 | 1 / 0 |
| Wall time, all rounds | 66.9 min (30.5 baseline, 36.3 smoke) |
| Sub-agent tokens, all rounds | about 1.88M (0.84M baseline, 1.04M smoke) |

Two items reached consensus in both runs with the same outcome: the numeric
option syntax (the host language's own integer parser in both) and the output-write failure
scope (outside the exit-status contract in both).

### Cost of the optional phases

Span of each phase from first launch to last result, including the parent's
own edit time:

| Phase | Baseline | Smoke |
| --- | --- | --- |
| Clarify | 29.4 min | 2.1 min |
| Checklist | 16.7 min | 49.9 min |
| Analyze plus confidence emit | 3.9 min | 5.3 min |
| Total | 50.0 min (53% of plan stage) | 57.3 min (48%) |

## Conclusion

Which phases or rounds changed the plan materially on this small SPEC:

- Clarify: 15 questions in total (14 baseline, 1 smoke). 2 changed a decision,
  one per run. 13 recorded existing behavior. Every applied answer matched the
  executor's recommendation. Both runs reached the raw-path finding in
  clarify.
- Checklist: 22 gaps in total (8 baseline, 14 smoke). 3 changed a decision,
  all in the smoke. 16 recorded existing behavior. 3 edited plan detail only.
- Analyze: 14 findings (7 per run). None changed a requirement or contract.
  1 changed a decision (done-gates, smoke). 6 added a test case to a task, 4
  edited plan or spec bookkeeping, 3 were cosmetic. The one finding common to
  both runs is the documentation file missing from the plan's file list.
- Consensus: 0 of 7 items changed a decision, 0 were security items, and the
  rounds took about 31% of each plan stage.

The 6 decision-changing items by phase: clarify 2 (one per run), checklist 3
(smoke), analyze 1 (smoke).

What this supports and what it does not:

- It supports the claim that, on a SPEC this size, the executor's first
  recommendation was the final answer every time. It does not show that
  consensus is unnecessary for security items, because no security item
  occurred (n = 0).
- It does not show what the plan would have looked like without a phase. I
  did not run a counterfactual. The evidence is the per-phase diff, not an
  ablation.
- Neither run reached implement, so I cannot say whether any recorded edge
  case prevented a defect in code.
- The research broker failed on every call in both runs (see the earlier
  performance profile), so the domain analysts and executors used local
  probes instead of external documentation. Consensus value with working
  external research is untested.

## Other observations

- Clarify ran in both runs although the specify gate reported 0
  `[NEEDS CLARIFICATION]` markers. `phase-execution.md` (Phase 2: Clarify)
  says clarify "only runs if G1 detected" markers, while the stage table lists
  Clarify unconditionally for the `plan` stage. The runs followed the stage
  table.
- The documentation file missing from the plan's file list appeared in both
  runs as an analyze finding. The same class of issue recurs, which suggests a
  template or plan-phase fix rather than a late finding.
- The baseline tasks phase did not cover 3 edge cases that clarify and
  checklist added. Analyze added the tests.

## Unconfirmed, and where I looked

- Counterfactual effect of any phase: not run. Looked at: per-phase commit
  diffs, executor and synthesizer reports, plan and research items.
- Whether a P item reached `tasks.md`: not traced for each item.
- Orchestrator-level checklist re-runs: not seen in either transcript's
  top-level calls. `phase-execution.md` Phase 4 describes one. The earlier
  profile counts it, so this may be a gap in what the transcript shows.
- Why the smoke's clarify yield was 1 question against 14: the fixture
  revision and the specify input differ between runs. Not isolated.
- The D, R, T, P and C labels are my reading of each diff. Another reader may
  move borderline items (for example baseline S1-1, smoke test-6) between R and
  D. Moving every borderline item still leaves D below 10 of 51.
- Smoke analyze edits sit inside the stage-boundary commit. I matched them to
  the analyze report finding by finding, but I did not separate them from any
  other edit in that commit by other means.
- Token counts exclude cache reads and come from sub-agent notifications.
  They do not reconcile with the receipt's stage totals (which include cache
  reads).

## Sources

- Baseline and 2.40.0 smoke plan-stage transcripts and receipts (local canary
  cache, not published).
- Per-phase commits, workflow file tables and spec artifacts in each run's
  spec worktree (local, not published).
- `speckit-pro/agents/clarify-executor.md`,
  `speckit-pro/agents/checklist-executor.md`,
  `speckit-pro/agents/analyze-executor.md` at 2.40.0.
- `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md`
  (routing and rounds, Clarify, Checklist and Analyze consensus flows, security
  keywords) and `references/phase-execution.md` (Phase 2 Clarify, Phase 4
  Checklist, stage table) at 2.40.0.

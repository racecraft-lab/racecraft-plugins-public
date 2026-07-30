# CAR-005 Slice 2 — Pull-Request Review Packet

**Position in the stacked chain: this is the SECOND and final PR, stacked on
slice 1.** Its base is **CAR-005 slice 1 —
`feat(car-005): add a reference simulator that pins what happens when an agent's model is unavailable`**,
not `main`. Emitted as a `gh-stack` chain; slice 2's PR must name slice 1's PR/branch
as its base, and its diff must be measured against slice 1's branch, not against
`main`. Slice 1 must land first.

**Proposed title** (validated below):
`feat(car-005): extend the route-fallback simulator with structural rejection and recovery cases`

---

## 1. What changed

Slice 2 **creates no file**. It extends exactly three of slice 1's files additively.
It is the structural-rejection and recovery half: what the system rejects before the
walk begins, and how it behaves when the walk runs out of room.

| File | Op | Added | Deleted |
| --- | --- | --- | --- |
| `tests/speckit-pro/layer6-efficiency/fixtures-fallback/fallback-scenario-corpus.json` | extend | **876** | **0** |
| `tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py` | extend | 633 | 42 |
| `tests/speckit-pro/unit/test-route-fallback-simulation.py` | extend | 1708 | 8 |

Final state: simulator 1,387 lines; corpus 1,669 lines / **18 cases**; unit test
3,532 lines. Feature total across both slices: **7,177 authored lines**.

Nine cases appended at the tail of `cases[]`: `fallback-loop`,
`unqualified-adjacent-model`, `generic-agent-substitution`,
`silent-inherit-materialization`, `unqualified-override`,
`override-skipped-by-allowlist`, `helper-unavailable-continues`,
`budget-exhaustion-of-one`, `no-safe-route-report-only`.

Behaviour delivered:

- A **structural pre-walk pass** rejecting four policy-authoring defects before the
  resolution walk runs — fallback loops, unqualified adjacent models, generic-agent
  substitution, and silent inherit materialization — plus `unqualified_override`.
- **Budget cap enforcement** with attempt counting across three classes
  (`probe_attempts`, `retries`, `candidate_routes`), and `details.exhausted_budget`
  enumerating the exhausted classes on the terminal diagnostic only.
- **Subagent model override handling**, both branches: honored (hybrid effective
  tuple) and skipped by the organization allowlist.
- The **helper-unavailable path** — recorded as a structured report field, not a
  diagnostic.
- **No-safe-route remediation**, report-only, with the verbatim rollback action.

## 2. Why

Slice 1 pinned what happens when a route *cannot* be used. Slice 2 pins what happens
when a policy is *authored wrongly*, and what happens when the walk exhausts its
declared room. These are the two remaining halves of the roadmap's proof obligation,
and they need the walk state slice 1 already owns — which is why structural validation
is a pre-pass of the same module rather than a second module.

The override work is the part most likely to surprise a reviewer. Grounded Platform
Fact PF-1 established that `CLAUDE_CODE_SUBAGENT_MODEL` is **not** unconditional: it is
checked against the organization `availableModels` allowlist and a value resolving to
an excluded model is skipped, with the subagent running on the *inherited* model. The
`override-skipped-by-allowlist` case exists because of that fact; without it the corpus
would pin an unconditional override effect the documented runtime does not have.

## 3. Non-goals

Audited, not asserted. All nine counts measured against slice 2's own diff
(`22458aad..HEAD`).

| Non-goal | Measured |
| --- | --- |
| No production resolver; nothing under `speckit-pro/` | **0** files |
| No CAR-002 / CAR-003 / CAR-004 schema or fixture edits | **0** files |
| No member added to the shared `layer6-efficiency/contracts/` directory | **0** files |
| No Codex-side edit | **0** files |
| No fixture agent name colliding with the live roster | **0** of 11 roster names appear |
| No fixture agent name missing the `fixture-` prefix | **0** |
| No live model call and no dispatch anywhere in the module | **0** tokens |
| **Seam** — no schema file changed | **0** files |
| **Seam** — no `suite-manifest.json` entry changed | **0** files |

The last two are the slice seam. All three schemas landed complete in slice 1, and
slice 2 touching none of them preserves the `contracts-claude/` directory's unbroken
invariant that no contract document has ever been edited after its introducing commit.

## 4. Review order

1. **The corpus diff first** (`fallback-scenario-corpus.json`, +876/-0) — nine
   appended cases, each carrying `purpose`, `proves`, and `requirements`. This is the
   fastest way to see what slice 2 claims before reading how it is computed.
2. **`claude_route_fallback.py`** (+633/-42) — the pre-walk pass, then budget
   accounting, then override handling, then the helper path. Read `_pre_walk_violations`
   first; it is the new entry point into the walk.
3. **`test-route-fallback-simulation.py`** (+1708/-8) — read the **8 deleted lines
   first** (§8). They are the only non-append content in this PR and the only place a
   slice-1 guarantee moved.
4. **The two diff checks in §7** — additivity and slice-1-untouched. These carry a
   guarantee no assertion can (§8).

## 5. Scope budget

**The split is elected, not gate-forced. No automated gate measures this surface.**
`estimate-reviewable-loc` computes `projected = production_files × 40`
(`speckit-pro/speckit_pro_runner/helpers/read_only.py:926`); this feature has **zero**
production files (`is_production_file` matches only `src/`, `app/`, `lib/`, `scripts/`
prefixes or `.ts`/`.tsx`/`.js`/`.jsx`/`.mjs`/`.cjs`/`.sql` suffixes,
`read_only.py:3811-3812`), so it projects **0** and returns **pass**. A single combined
PR would have passed every gate.

**Precedent**: the sibling spec CAR-004 had the same surface and the same 0 production
files, and shipped roughly **11,600 artifact lines in a single pull request** (#401).

Two slices were chosen on **review burden** and **independent slice value**, and the
operator ratified that choice. Because no gate measures this surface, no plan-time or
PR-time re-estimation can overturn the split by returning a smaller number — only an
operator decision can.

**The advisory `estimate-spec-size` figure suggests more slices than two, and was
deliberately not acted on.** The formula `user_stories × 25 + files × 40 + frs × 15`
with `suggested_slices = ceil(estimated_loc / 400)` (`read_only.py:964,971`), on the
current literal count of **60** FR identifiers, returns **about 1,350 → 4 suggested
slices**, status `warn` (1,310 on the plan's nine declared file operations, 1,350 on
ten; the slice count is 4 either way — on the earlier 35-FR figure, roughly 975 → 3).
It is recorded and not acted on because the FR
count grew **35 → 60 through defect repair, not new deliverables** — lettered
sub-requirements such as FR-012a and FR-033d closing gaps in requirements that already
existed. The delivered surface did not grow with the identifier count.

Slice 2's own diff: 3,217 added / 50 deleted across three authored files.

## 6. Traceability

Slice 2 satisfies **12 requirements outright** and **15 jointly with slice 1**.

| Requirement | Changed file | Passing assertion |
| --- | --- | --- |
| FR-019c | `claude_route_fallback.py` | `StructuralPreWalkTests` |
| FR-020 | corpus + simulator | `FallbackLoopTests`; case `fallback-loop` |
| FR-021 | corpus + simulator | case `unqualified-adjacent-model`; `test_an_adjacency_naming_no_declared_sibling_fails_closed` |
| FR-022 | corpus + simulator | case `generic-agent-substitution` |
| FR-023 | corpus + simulator | case `silent-inherit-materialization`; `test_a_route_omitting_its_effort_is_admitted_then_rejected` |
| FR-024, FR-024a | corpus + simulator | `test_an_honored_override_records_the_hybrid_effective_dispatch_tuple`; `test_any_override_in_force_disqualifies_the_environment` |
| FR-024b | corpus + simulator | case `override-skipped-by-allowlist`; `disposition = skipped_by_allowlist`, `override.tuple` absent |
| FR-025, FR-025a, FR-025b | corpus + simulator | case `helper-unavailable-continues`; `optional_helper.probe_attempts == 0` |
| FR-026, FR-026a | corpus + simulator | case `budget-exhaustion-of-one`; all three counters pinned at cap `1` |
| FR-028 | corpus + simulator | retry exhaustion represented; `test-route-fallback-simulation` |
| FR-029, FR-029a | corpus + simulator | case `no-safe-route-report-only`; verbatim rollback action |
| FR-031 | — (negative) | §3 zero-counts |
| FR-001, FR-033a, FR-033b | slice seam | §7 additivity and slice-1-untouched diffs |

| Success criterion | Evidence |
| --- | --- |
| SC-001 (scenario coverage) | **17/17** mandated scenarios represented, **0** unrepresented |
| SC-002 (byte-identical replay) | 18/18 cases replay identically, twice, matching pinned reports |
| SC-004 / SC-005 / SC-006 | 0 / 0 / 0 (§3) |
| SC-008 (registered and runnable) | `test-route-fallback-simulation` PASS 1195/1195 in layer 4 |
| SC-009 (budget caps) | all three counters at declared cap `1`, never exceeded; `exhausted_budget` on the terminal diagnostic only |
| SC-010 (no-safe-route report-only) | agent named, 3 attempted routes, each with a rejection reason, verbatim rollback action present |
| SC-011 (per-PR reviewability) | both slices measured on their own diff; follow-up recorded as **G56R-005** |

## 7. Verification evidence

| Command | Result |
| --- | --- |
| `python3 tests/speckit-pro/run-all.py --layer 1` | **1428/1428 passed**, 0 failures |
| `python3 tests/speckit-pro/run-all.py --layer 4` | **4926/4926 passed**, 0 failures |
| `python3 tests/speckit-pro/unit/test-route-fallback-simulation.py` | **1195/1195 passed** |
| `pnpm --dir docs-site reference:generate` | 7 pages generated, **no diff** |
| `pnpm --dir docs-site reference:check` | `Reference pages are current.` |
| quickstart determinism spot-check | `cases: 18 | mismatches: none` |

`test-policy-control-contracts` PASS (730/730) and `test-unit-layout` PASS (12/12) —
both still green with the three schemas in place.

**Additivity of the diff.** `git diff --numstat 22458aad HEAD` shows exactly three
authored files, all under `tests/`. Corpus: **+876 / -0**, zero removed lines. No
schema file and no `suite-manifest.json` in the diff. The regenerated docs reference
page is **not** in the diff and correctly so — slice 2 adds no test module, so
`reference:generate` is a no-op and `reference:check` is the assertion that the page is
current.

**Slice-1 content untouched.** All nine slice-1 cases are byte-identical *and* still
occupy the same leading positions in `cases[]`; zero mismatched `case_id`s; no
sibling top-level corpus key changed. This is the diff-borne guarantee the replay test
cannot provide, since a case whose inputs and pinned report both moved would still
replay green.

Per-case measurements behind the acceptance table:

| Case | Measured |
| --- | --- |
| `budget-exhaustion-of-one` | declared `{1,1,1}`, actual `{1,1,1}` — at cap, never exceeded |
| exhausted-budget enumeration | `['probe_attempts','retries','candidate_routes']` on `no_safe_route` only; **0** other diagnostics carry it across all 18 cases |
| `no-safe-route-report-only` | agent `fixture-required-executor`; 3 attempted routes (`preferred-moved`, `fallback-over-ladder`, `fallback-unprobeable`) each with a rejection reason; actions `['Widen the declared fallback list with qualified routes.', 'Roll back to the previous plugin release.']` |
| `helper-unavailable-continues` | `optional_helper = {consulted:false, no_helper_path_validated:true, probe_attempts:0}`; no helper diagnostic; no helper route in `attempted_routes`; outcome `resolved` |
| `unqualified-override` | hybrid tuple — model `model-forced` from the override, `agent` and `effort` (`xhigh`) retained; `release_claim_eligible: false`; `would_have_been` recorded |
| `override-skipped-by-allowlist` | `disposition: skipped_by_allowlist`; `override.tuple` **absent**; `effective_dispatch_tuple` follows the qualified walk; no model named as the one that runs |

Title validation — the live release-readiness gate returns `gate_status: pass` for the
proposed title. The branch's commit messages use the uppercase `feat(CAR-005)` scope;
the PR title must use lowercase `feat(car-005)`.

## 8. Known gaps and deviations

**This PR's diff is NOT a pure append, and that must not be glossed.**

Corpus-wise and schema-wise it *is*: 876 corpus additions with **zero** deletions,
schemas and manifest untouched, all nine slice-1 cases byte-identical and in the same
positions. But **8 lines across 5 slice-1 test method bodies were adapted** (the
briefed figure was 7 lines across 4 bodies; the measured figure is 8 across 5, because
one adaptation was applied identically to two sibling test methods). No test method
name changed, and no public module signature changed. The 8 lines group into **four
distinct adaptations**, two unavoidable and two avoidable:

*Unavoidable — the spec deliberately allocates interim behaviour to slice 1 and final
behaviour to slice 2, so the slice-1 assertion cannot survive slice 2 and its
replacement cannot live in slice 1:*

1. `EffectiveDispatchTupleTests::test_a_route_reaching_the_walk_without_a_pinned_model_fails_closed`
   and `…_without_a_pinned_effort_fails_closed` (4 lines, 2 methods). Slice 1 asserted
   that such a route raises `RouteFallbackError` through `resolve`. In slice 2 the
   pre-walk pass rejects it with `silent_inherit_materialization` first, so the route
   **no longer reaches the walk**. The assertion was retargeted at the walk-entry guard
   `_require_pinned_tuple` directly, which is what still keeps a route arriving by any
   other path from resolving to an incomplete tuple.
2. `CorpusContractValidationTests::test_the_route_contract_admits_an_omitted_model_the_simulator_rejects`
   (2 lines). Same cause: slice 1 pinned `assertRaises(RouteFallbackError)`; slice 2
   pins the diagnostic pair `['silent_inherit_materialization', 'no_safe_route']` with
   an empty `attempted_routes`.

*Avoidable — slice-1 authoring defects:*

3. `CorpusContractValidationTests::test_the_corpus_holds_the_nine_declared_slice_one_cases`
   (1 line). Slice 1 asserted `len(self.cases) == 9`, which is **incompatible with any
   append** and would have had to change no matter what slice 2 contained. It is now an
   append-tolerant identity pin: `len(SLICE_ONE_CASE_IDS) == 9` plus an assertion that
   the first nine `case_id`s equal `SLICE_ONE_CASE_IDS` in order — which is strictly
   stronger, since a bare length would still pass if an appended case displaced one of
   the nine.
4. `DiagnosticEmissionOrderTests::test_the_terminal_entry_is_unique_last_and_carries_the_verbatim_rollback`
   (1 line). The fixture used `invocation={"model-terminal": "failure"}`. Under slice
   2's budget semantics that spends a retry and lands the report **at cap**, which would
   have made the closing omission assertion contingent on the at-cap set rather than an
   unconditional claim about the terminal entry's shape. Retargeted to
   `probe={"model-terminal": False}`. Slice 1 could have chosen the probe form from the
   start.

Under FR-033b's own remedy rule, a slice-2 finding that requires changing slice-1
content is evidence the slice-1 contract was wrong and the fix belongs on slice 1's
branch with the chain restacked. Adaptations 3 and 4 are that case. They are disclosed
here rather than silently absorbed; whether to restack them onto slice 1 is an
operator decision.

**Deviation — two slice-1 private helper signatures were widened.** FR-001 states
slice 2 "MUST add new module-level constants, new private helpers, and new public
entry points, and MUST change no slice-1 function signature", and spec.md:1462-1463
repeats "no slice-1 function signature may change". Measured by AST comparison of
`claude_route_fallback.py` at `22458aad` vs `HEAD`: **0 slice-1 callables removed, 20
added, and 2 changed** —

- `_optional_helper_state(policy)` → `_optional_helper_state(policy, snapshot)`
- `_stage_no_safe_route(agent)` → `_stage_no_safe_route(agent, reported)`

Both are private helpers, and the module's **public** surface (`resolve`,
`serialize_report`, `load_corpus`, `RouteFallbackError`) is byte-for-byte unchanged.
The spec's rule is nonetheless unqualified, so this is a real deviation from FR-001 and
FR-033b, not a wording gap in the quickstart. Recording it here rather than narrowing
the rule to match the code.

**Deliberate divergence 1 — FR-024b's allowlist-skip branch deliberately does not name
the model that runs.** The report records only that the override did not take effect.
Per Grounded Platform Fact PF-1 the documented fallback target is the ***inherited***
model, and this projection does not carry an inherited model; the docs do not say
resolution resumes at the per-invocation parameter, so reading it that way is
inference. Naming any model would be inference presented as fact. The absence is by
design and is asserted as an absence (`override.tuple` is required to be **absent**).

**Deliberate divergence 2 — FR-007a rejects an unsupported effort at preflight; the
documented runtime silently degrades.** PF-2 records that Claude Code "falls back to
the highest supported level at or below the one you set", with the warning suppressed
under `--output-format json`/`stream-json` and in background agents. This simulator
rejects instead. Recorded decision: a silent degrade is the failure mode this feature
exists to make visible.

**Gap — CAR-002 never pinned the unavailable-model platform fact.** Its vocabulary is
labelled inference, its route-change question is hardcoded open, and no live capture is
committed. This feature therefore pins these semantics **ahead of** the platform fact
rather than downstream of it. Read the pinned corpus as a decision record, not as
observed platform behaviour. The Grounded Platform Facts section added to the roadmap
in slice 1 is the partial remedy; three of its four facts contradicted a requirement
that had already been written and reviewed.

**Gap — cross-platform mirroring is deferred to G56R-005.** The Claude/Codex reason-code
divergence (`capability_probe_unavailable` vs `capability_discovery_unavailable`, with
4 codes shared) is pinned as test data, not reconciled. G56R-005 carries the mirroring
of CAR-005's schemas, enums, and corpus to the Codex side; that obligation lives in this
spec's assumptions because it is not written into G56R-005's own scope text.

**Quickstart defects found and fixed during this audit.** Two operator-facing errors in
`quickstart.md` were corrected as part of T062: (a) the "Additivity of the diff" section
claimed the regenerated docs reference page appears in slice 2's diff — it does not and
should not, since `reference:generate` is a no-op here; and (b) the slice-2 acceptance
table used a bare `probe_attempts` for the helper row, colliding with
`budgets.actual.probe_attempts`, which legitimately reads `1` in that same case — now
qualified to `optional_helper.probe_attempts` with the disjointness FR-025a requires be
stated.

## 9. Rollback notes

**Test-tree only. Zero production files. No plugin runtime change, no payload change,
no shipped byte changed.**

Slice 2 creates no file, so rolling it back does **not** mean deleting files. It means
reverting the two slice-2 commits (`2d73df77`, `6a001079`), which returns the three
extended files to their slice-1 state: simulator 796 lines, corpus 793 lines / 9 cases,
unit test 1832 lines. Slice 1 remains complete and passing on its own — nothing in it
was stubbed or `TODO`-marked for slice 2.

Because this PR is stacked, the order matters: **slice 2 can be reverted independently,
but slice 1 cannot be reverted while slice 2 is landed.** Revert slice 2 first.

No `suite-manifest.json` change to undo, no schema to restore, and no docs reference
page to regenerate — slice 2 touched none of them.

**There is no feature flag, and none is needed.** Nothing dispatches, nothing is
imported by shipped code, and no consumer outside the test suite reads these files.

```release-note
Extend the CAR-005 route-fallback simulator and its pinned corpus to eighteen cases, adding structural policy rejection, retry and probe budget caps, subagent model override handling including the organization-allowlist skip, the optional-helper-unavailable path, and no-safe-route remediation. Test-tree only; no plugin runtime or payload change.
```

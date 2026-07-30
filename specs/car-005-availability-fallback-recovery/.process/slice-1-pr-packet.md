# CAR-005 Slice 1 — Pull-Request Review Packet

**Position in the stacked chain: this is the BASE.** Slice 1 opens first, against
`main`, and stands alone. Slice 2 is stacked on top of it and names this PR as its
base. Nothing in slice 1 depends on slice 2 — it is independently landable and
independently releasable, which is one of the two grounds the split was elected on.

**Proposed title** (validated below):
`feat(car-005): add a reference simulator that pins what happens when an agent's model is unavailable`

---

## 1. What changed

Slice 1 creates every file this feature ships. It is the resolution-failure half:
what the system decides, and what it reports, when a preferred route cannot be used.

| File | Op | Lines |
| --- | --- | --- |
| `tests/speckit-pro/layer6-efficiency/contracts-claude/route-policy.schema.json` | new | 126 |
| `tests/speckit-pro/layer6-efficiency/contracts-claude/environment-snapshot-projection.schema.json` | new | 76 |
| `tests/speckit-pro/layer6-efficiency/contracts-claude/route-resolution-report.schema.json` | new | 387 |
| `tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py` | new | 796 |
| `tests/speckit-pro/layer6-efficiency/fixtures-fallback/fallback-scenario-corpus.json` | new | 793 (9 cases) |
| `tests/speckit-pro/unit/test-route-fallback-simulation.py` | new | 1832 |
| `tests/speckit-pro/suite-manifest.json` | modified | +2 / -1 (one entry) |
| `docs/ai/specs/claude-agent-routing-technical-roadmap.md` | modified | +96 / -4 |
| `docs-site/src/content/docs/reference/tests.md` | regenerated | +10 / -6 |

Authored implementation total: **4,010 lines** across six new files, plus one
manifest entry. The roadmap edit is the one declared modification outside the test
tree; it carries the status line, the progress row, the **Grounded Platform Facts**
section (PF-1…PF-4), and two dated scope amendments. The docs reference page is
generated, not hand-edited.

Behaviour delivered:

- A **pure-function reference simulator** from (route policy, environment snapshot,
  overrides, declared budgets) to a resolution report — no filesystem, network,
  wall-clock, or randomness input, which is what makes replay byte-identical.
- The **five-code resolution vocabulary** (`preferred_model_unavailable`,
  `effort_unsupported`, `capability_probe_unavailable`, `treatment_probe_failed`,
  `no_safe_route`) with per-code severity, ordered emission, and `details`
  sub-reasons.
- The **seven-member environment snapshot projection** — available models, alias
  bindings, per-model supported efforts, probe availability, exact-invocation probe
  outcomes, declared platform route changes, and the organization model allowlist.
- The **report contract**: outcome discriminator, both closed diagnostic
  vocabularies, attempted routes, dispatch tuple, `optional_helper`,
  `release_claim_eligible`, and a closed eleven-member remediation-action set.
- **Nine corpus cases** with pinned expected reports, covering the resolution-failure
  scenarios.

## 2. Why

CAR-002 established routing semantics but never pinned what happens when a model is
unavailable. This slice makes that behaviour an **executable specification** rather
than prose: a reference simulator plus a pinned corpus, so a future change to the
documented routing story fails a test instead of drifting silently. CAR-006 needs
exactly these three artifacts first — the snapshot projection, the report contract,
and the reason-code vocabulary — and can adopt all three even if slice 2 never
lands.

Two of the semantics here are **deliberate divergences from the documented runtime**,
recorded as decisions rather than discovered as oversights. Both are stated in full
in §8; a reviewer should read them before treating either as a bug.

## 3. Non-goals

Audited, not asserted. Every count below is a measured command result (§7).

| Non-goal | Measured |
| --- | --- |
| No production resolver; nothing under `speckit-pro/` | 0 files |
| No CAR-002 / CAR-003 / CAR-004 schema or fixture edits | 0 files |
| No member added to the shared `layer6-efficiency/contracts/` directory | 0 files |
| No Codex-side edit | 0 files |
| No fixture agent name colliding with the live roster | 0 of 11 roster names appear |
| No fixture agent name missing the `fixture-` prefix | 0 |
| No live model call and no dispatch anywhere in the module | 0 tokens |

This feature does **not** change plugin runtime, payload, or any shipped byte. The
cross-platform divergence between the Claude and Codex vocabularies is *pinned as
test data*, not reconciled — reconciliation is G56R-005's job.

## 4. Review order

1. **`environment-snapshot-projection.schema.json`** (76 lines) — smallest, and it
   defines the vocabulary everything else consumes. Read the seven members first.
2. **`route-policy.schema.json`** (126) — the input contract: routes, the closed
   five-member effort ladder, ordered fallbacks, declared budgets and their maxima.
3. **`route-resolution-report.schema.json`** (387) — the output contract. The
   densest file. Read the `outcome` discriminator, then the two diagnostic `$defs`,
   then `remediation`. Note the recorded deviation in §8 before reviewing the
   action enum's placement.
4. **`claude_route_fallback.py`** (796) — the walk. Staged private helpers, one per
   rule, so the evaluation order is a call-graph property rather than a comment.
5. **`fallback-scenario-corpus.json`** (793) — nine cases. Each carries `purpose`,
   `proves`, and `requirements`, so a case can be read on its own.
6. **`test-route-fallback-simulation.py`** (1832) — largest, but read last and it
   reads as confirmation rather than discovery.
7. **`suite-manifest.json`** and the roadmap — one entry, and prose.

## 5. Scope budget

**The split is elected, not gate-forced. No automated gate measures this surface.**

`estimate-reviewable-loc` computes `projected = production_files × 40`
(`speckit-pro/speckit_pro_runner/helpers/read_only.py:926`), and `is_production_file`
matches only paths starting `src/`, `app/`, `lib/`, or `scripts/`, or ending
`.ts`/`.tsx`/`.js`/`.jsx`/`.mjs`/`.cjs`/`.sql` (`read_only.py:3811-3812`). Every path
in this feature starts `tests/`, `docs/`, or `docs-site/` and ends `.json`, `.py`, or
`.md`. So `production_files = 0`, `projected = 0 × 40 = 0`, status **pass**. A single
combined PR would have passed every gate.

**Precedent for how little that means**: the immediately preceding sibling spec
CAR-004 had the same primary surface and the same 0 production files, declared 250
reviewable LOC with status ok, and shipped roughly **11,600 artifact lines in a single
pull request** (#401).

The split was chosen on two grounds and **ratified by the operator**:

1. **Review burden** — 3,100–4,600 artifact lines in one diff is not reviewable in
   one sitting, whatever the estimator says.
2. **Independent slice value** — slice 1 is independently landable and releasable and
   is the artifact CAR-006 needs first.

**The advisory `estimate-spec-size` figure suggests more slices than two, and was
deliberately not acted on.** The formula `user_stories × 25 + files × 40 + frs × 15`
with `suggested_slices = ceil(estimated_loc / 400)` (`read_only.py:964,971`), run on
this spec's current literal count of **60** distinct FR identifiers, returns
**about 1,350 → 4 suggested slices**, status `warn` (1,310 on the plan's nine declared
file operations, 1,350 on ten — the slice count is 4 either way). On the spec's earlier
figure of 35 FRs it returns roughly 975 → **3** slices. Every reading exceeds the
400-LOC ceiling by more than a factor of two. This is recorded and **not acted on**, for a
stated reason: the FR count grew 35 → 60 through **defect repair during the checklist
and analyze phases — lettered sub-requirements such as FR-012a and FR-033d closing
gaps in requirements that already existed — not through new deliverables**. The
surface did not grow with the identifier count, so an estimator keyed to identifier
count over-reads it. The estimator does not measure a 0-production-file surface in
either direction.

There is also a **recorded roadmap inconsistency**: the CAR-005 roadmap entry declares
`Suggested slices: 1` (`docs/ai/specs/claude-agent-routing-technical-roadmap.md:593`)
while the same roadmap's Progress Tracking row declares "2 vertical slices, gh-stack
delivery" (`:311`). The Progress Tracking row is correct; the `Suggested slices: 1`
figure is a stale scoping guess from coarser signals.

## 6. Traceability

Slice 1 satisfies **33 requirements outright** and **15 jointly with slice 2**
(48 of the spec's 60 FR identifiers appear in slice-1 tasks).

| Requirement | Changed file | Passing assertion |
| --- | --- | --- |
| FR-001, FR-014, FR-014a | `lib/claude_route_fallback.py` | `ReplayDeterminismTests`; `resolve` is a pure function of its four arguments |
| FR-002, FR-002a | `environment-snapshot-projection.schema.json` | seven projection members present; snapshot intake tests |
| FR-003, FR-003a, FR-027 | `route-policy.schema.json` | `test_an_over_range_declared_budget_is_refused_by_the_policy_contract`; maxima measured at 8 / 8 / 8 |
| FR-004, FR-005, FR-006 | `lib/claude_route_fallback.py` | `ResolutionWalkTests`; `test_the_inter_code_order_follows_the_resolution_enums_declared_order` |
| FR-007, FR-007a | `route-policy.schema.json` | `test_the_effort_enum_holds_exactly_the_five_member_ladder`; `test_a_dropped_effort_level_fails_the_comparison`; `test_an_added_effort_level_fails_the_comparison`; `test_the_session_orchestration_setting_is_not_an_effort_level` |
| FR-008, FR-009 | `lib/claude_route_fallback.py` | `CapabilityProbeUnavailableTests`, `TreatmentProbeFailedTests` |
| FR-010, FR-015 | `fixtures-fallback/fallback-scenario-corpus.json` | corpus envelope tests; nine cases pinned |
| FR-011, FR-013, FR-013a | `route-resolution-report.schema.json` | `EffectiveDispatchTupleTests`; dispatch-tuple contract |
| FR-012, FR-012a, FR-012b, FR-012c | `route-resolution-report.schema.json` | `test_the_severity_and_action_maps_cover_both_closed_vocabularies`; closed eleven-member action enum |
| FR-015a | `unit/test-route-fallback-simulation.py` | read-one-case guarantee test |
| FR-016, FR-016a | all three schemas | `CommittedContractIdentityTests`; `test-policy-control-contracts` 730/730 |
| FR-017, FR-017a, FR-017b, FR-017c | `route-resolution-report.schema.json` | `test_the_resolution_enum_equals_the_codes_the_claude_roadmap_pins`; `test_the_cross_platform_divergence_is_pinned_as_test_data` |
| FR-018 | `fixtures-fallback/fallback-scenario-corpus.json` | `test_every_agent_name_in_the_corpus_carries_the_fixture_prefix` |
| FR-019, FR-019a, FR-019b | `route-resolution-report.schema.json` | `test_the_policy_violation_enum_holds_exactly_its_five_declared_members`; `InlineNegativeValidationTests` |
| FR-030, FR-031 | — (negative) | §3 zero-counts, all measured |
| FR-032, FR-032a | `suite-manifest.json` | `test-route-fallback-simulation` appears in layer-4 output |
| FR-033, FR-033a | slice seam | §7 seam evidence |

| Success criterion | Evidence |
| --- | --- |
| SC-002 (byte-identical replay) | 9/9 cases replay identically, twice, and match their pinned reports |
| SC-003 (closed vocabularies) | both enums set-equal; out-of-vocabulary code rejected |
| SC-004 (zero production files) | 0 |
| SC-005 (zero shared-contract members) | 0 |
| SC-006 (synthetic cast only) | 0 roster collisions, 0 missing prefixes |
| SC-008 (registered and runnable) | `test-route-fallback-simulation` PASS in layer 4 |
| SC-012 (roadmap parity) | schema enum set-equal to the five roadmap codes |
| SC-013 (documented-runtime alignment) | effort ladder matches the frozen successor-capability contract |

## 7. Verification evidence

All commands run from the repository root of the feature worktree.

| Command | Result |
| --- | --- |
| `python3 tests/speckit-pro/run-all.py --layer 1` | **1428/1428 passed**, 0 failures |
| `python3 tests/speckit-pro/run-all.py --layer 4` | **4926/4926 passed**, 0 failures (at chain HEAD) |
| `python3 tests/speckit-pro/unit/test-route-fallback-simulation.py` | **442/442 passed** at slice 1 standalone |
| `pnpm --dir docs-site reference:generate` | 7 pages generated |
| `pnpm --dir docs-site reference:check` | `Reference pages are current.` |
| quickstart determinism spot-check (slice 1) | `cases: 9 | mismatches: none` |

Named modules the quickstart calls out, at chain HEAD:
`test-route-fallback-simulation` PASS (1195/1195), `test-policy-control-contracts`
PASS (730/730), `test-unit-layout` PASS (12/12).

Non-goal audit commands and their measured outputs:

| Check | Command | Count |
| --- | --- | --- |
| Production files | `git diff --name-only <base> 22458aad -- speckit-pro/` | **0** |
| Frozen CAR-002/003/004 schemas + fixtures | `comm -12 <(git ls-tree -r --name-only <base> -- tests/speckit-pro/layer6-efficiency/) <(git diff --name-only <base> HEAD)` | **0** |
| Shared `contracts/` members | `git diff --name-only <base> 22458aad -- tests/speckit-pro/layer6-efficiency/contracts/` | **0** |
| Codex-side files | `git diff --name-only <base> 22458aad \| grep -i -E 'codex\|AGENTS\.md'` | **0** |
| Fixture names matching live roster | 11 roster names from `speckit-pro/agents/`, substring-scanned across the whole corpus | **0** |
| Fixture names missing `fixture-` | agent-identity values under `agent` / `name` / `unresolved_agent` | **0** |
| Live model call / dispatch tokens | grep for `subprocess\|requests.\|urllib\|http\|socket\|anthropic\|openai\|os.environ\|Popen\|exec(\|eval(\|time.time\|datetime.now\|random.\|uuid.` in the simulator | **0** |

Fixture agent-identity values at slice 1: `fixture-bounded-analyst`,
`fixture-required-executor`. Live roster (11): `analyze-executor`,
`checklist-executor`, `clarify-executor`, `codebase-analyst`,
`consensus-synthesizer`, `domain-researcher`, `gate-validator`,
`implement-executor`, `phase-executor`, `spec-context-analyst`,
`uat-runbook-author`. Zero appear anywhere in the corpus text.

Title validation — the live release-readiness gate
(`PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/release-readiness-live-github.json`)
returns `gate_status: pass` for the proposed title. Note the branch's **commit**
messages use `feat(CAR-005)` with an uppercase scope; the **PR title** must use the
lowercase `feat(car-005)` form the gate requires.

## 8. Known gaps and deviations

**Deviation — the remediation action enum's placement.** FR-012a names the action
vocabulary `$defs.remediationAction`. It is instead declared **inline** at
`$defs/remediation/properties/actions/items/enum`. This is carried as a recorded
deviation, not omitted. FR-016a prohibits bare-enum `$defs` members and states a
directory-wide invariant that research verified empirically: **zero** of the eleven
existing documents has a `$defs` member with a top-level `enum`. A
`$defs.remediationAction` holding an enum would be the first, breaking the invariant
FR-016a exists to protect. The two requirements cannot both be satisfied literally.
Inlining preserves what FR-012a actually emphasises — literal strings, closure, one
declaration site, and a stable JSON pointer for a set-equality test. Only the `$defs`
*name* is lost. Recorded in `plan.md` §Complexity Tracking and reported to the
operator rather than absorbed silently.

**Deliberate divergence 1 — FR-007a rejects an unsupported effort at preflight;
the documented runtime silently degrades.** Grounded Platform Fact PF-2 records the
runtime behaviour: "if you set a level the active model does not support, Claude Code
falls back to the highest supported level at or below the one you set", and the
warning is *suppressed* under `--output-format json` or `stream-json` and in
background agents. This simulator instead **rejects** the unsupported effort at
preflight and emits `effort_unsupported`. That is a recorded decision, not an
oversight: a silent degrade is exactly the failure mode this feature exists to make
visible, and a preflight rejection is the falsifiable form of it. A reviewer
comparing against the docs will find the two disagree — deliberately.

**Deliberate divergence 2 — FR-024b's allowlist-skip branch does not name the model
that runs.** (Delivered in slice 2; stated here because the report contract that
admits it lands in slice 1.) When an override is skipped by the organization
allowlist, the report records only that the override did **not** take effect. It
deliberately does **not** name the model that runs instead. Per PF-1, the documented
fallback target is the ***inherited*** model — the docs do not say resolution resumes
at the per-invocation parameter, and this projection does not carry an inherited
model. Naming a model would be inference presented as fact, so the field is absent by
design.

**Gap — CAR-002 never pinned the unavailable-model platform fact.** CAR-002's
vocabulary is labelled inference, its route-change question is hardcoded open, and no
live capture is committed. This feature therefore pins these semantics **ahead of**
the platform fact rather than downstream of it. A reviewer should read the pinned
corpus as "this is what we have decided the behaviour is", not "this is what the
platform was observed to do". The Grounded Platform Facts section (PF-1…PF-4) added
to the roadmap in this slice is the partial remedy — verified against live Claude Code
documentation on 2026-07-30 (CLI 2.1.220) — and three of its four facts contradicted a
requirement that had already been written and reviewed.

**Gap — cross-platform mirroring is deferred.** The Claude/Codex divergence
(`capability_probe_unavailable` vs `capability_discovery_unavailable`, 4 shared codes)
is pinned as test data, not reconciled. The named follow-up is **G56R-005**, which
carries the mirroring of CAR-005's schemas, enums, and corpus to the Codex side. That
obligation is recorded in this spec's assumptions because it is not written into
G56R-005's own scope text.

**Gap — two acceptance rows rest on diff review, not on an assertion.** Cross-slice
stability of slice-1 cases cannot be proven by the replay test: if slice 2 re-pinned a
slice-1 case's inputs *and* its expected report together, the test would still pass
because both sides of the comparison moved. That guarantee is diff-borne. Slice 2's
packet carries the diff evidence.

## 9. Rollback notes

**Test-tree only. Zero production files. No plugin runtime change, no payload change,
no shipped byte changed.**

Reverting is removing the added files and the single `suite-manifest.json` entry:

- delete `tests/speckit-pro/layer6-efficiency/contracts-claude/route-policy.schema.json`
- delete `tests/speckit-pro/layer6-efficiency/contracts-claude/environment-snapshot-projection.schema.json`
- delete `tests/speckit-pro/layer6-efficiency/contracts-claude/route-resolution-report.schema.json`
- delete `tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py`
- delete `tests/speckit-pro/layer6-efficiency/fixtures-fallback/` (the whole directory; nothing else uses it)
- delete `tests/speckit-pro/unit/test-route-fallback-simulation.py`
- remove the one `test-route-fallback-simulation` entry from `tests/speckit-pro/suite-manifest.json`
- run `pnpm --dir docs-site reference:generate` and commit the regenerated page

The roadmap edit may be kept or reverted independently — the Grounded Platform Facts
section is useful on its own and nothing depends on it.

**There is no feature flag, and none is needed.** Nothing dispatches, nothing is
imported by shipped code, and no consumer outside the test suite reads these files.
A plain `git revert` of the slice-1 commits is sufficient and safe. Because slice 2 is
stacked on this PR, reverting slice 1 after slice 2 has landed requires reverting
slice 2 first.

```release-note
Add an executable reference simulator, three JSON Schema contracts, and a nine-case pinned corpus that specify how agent routing resolves — and what it reports — when a preferred model, effort level, or capability probe is unavailable. Test-tree only; no plugin runtime or payload change.
```

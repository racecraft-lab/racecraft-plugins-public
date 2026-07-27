# CAR-003 Slice 1 — PR Review Packet

**Feature**: `specs/car-003-evaluation-runner-scoring/`
**Slice**: 1 of 3 — US1 + US2, roadmap Work Package A, kept intact
**Proposed PR title**: `feat(speckit-pro): add the successor capability freeze and exact treatment proof`

> Title validated against the release-readiness gate pattern
> `^(feat|fix|chore|docs|test|refactor)\([a-z0-9-]+\): .+` — **PASS**.
> Type `feat`, lowercase scope `speckit-pro`, plain-English description.

The nine sections below are the set `spec.md` "PR Review Packet Requirements"
makes mandatory.

---

## 1. What changed

Slice 1 establishes the two things every later CAR-003 slice reads from: a
successor capability freeze that says which model/effort tuples may be run at
all, and an immutable pre-score treatment record that proves what was actually
dispatched.

- **`speckit-pro/speckit_pro_runner/materializer.py`** — the single shipped
  production file. Renders an agent definition to a destination path and hashes
  the bytes read back **from disk**, so the proof survives the six drift classes
  that parsed-field equivalence cannot see (key order, whitespace, comments,
  unknown keys, line endings, encoding). A hash computed from the in-memory
  render buffer is rejected as proof. The destination path is verified separately
  and is absent from the digest preimage.
- **`claude_successor_freeze.py`** — candidate admission as the intersection of
  the official-source ledger and pinned-runtime support. Runtime discovery can
  remove or constrain candidates but never adds them. Exclusions carry a closed
  reason (`source_not_admitted`, `canonical_effort_unknown`,
  `topology_control_not_candidate_effort`). A diagnostic surface cannot admit a
  tuple. An empty or invalid intersection publishes diagnostic evidence only,
  blocks qualification-capable execution, and does not promote the six archived
  CAR-002 tuples.
- **Alias re-point detection** (same module) — closes CAP-Q6. Unchanged route +
  overrides proven unset + unchanged client version resolves to
  `platform_route_change`, recorded as platform behavior and never as a SpecKit
  Pro fallback. A plugin-initiated substitution resolves to `resolver_fallback`.
  Incomplete override proof, a changed client version, or an unattributable cause
  resolves to `alias_repoint_unresolved` and blocks admission.
- **`claude_treatment_runner.py`** — the score-eligibility predicate and
  disposition precedence `hard_fail` > `non_scorable_rerouted` > `unknown` >
  `proven`. All co-firing disqualifier codes are retained in
  `disposition_reasons`; no non-terminal cause is discarded. Per-arm ephemeral
  cache-root isolation is recorded as a checked property rather than asserted in
  prose.
- **`run-efficiency-benchmarks.py`** — one line: results metadata now carries
  `non_release_evidence: True`, demoting the shared smoke runner so historical
  results can never be promoted as route qualification evidence.
- **The generated-artifact refresh** — slice 1 is the only slice that touches
  shipped source, so it absorbs the entire synchronized payload regeneration.

## 2. Why

CAR-002 archived a capability snapshot that has since aged, and its `opus` alias
may have been re-pointed by the platform. Nothing downstream — scoring,
statistics, qualification — is trustworthy until two questions are answered
mechanically rather than by assertion: *which tuples are legitimately runnable*,
and *did the run actually receive the treatment we think it did*.

The materializer ships in plugin source rather than the test tree because the
design concept (Q4) fixed a single canonical materializer so CAR-006 consumes one
component instead of a copy. That decision is what moves the production-file
count off zero and is the reason this slice carries the generated-artifact
contract for the whole feature.

## 3. Non-goals

- No live model calls. The default suite makes zero. Live collection is T022,
  operator-only, and is deliberately **not** in this PR.
- No policy controls or adaptive comparators — CAR-004.
- No availability or fallback simulation — CAR-005.
- No resolver or preflight behavior — CAR-006.
- No `autopilot-fast-helper` agent definition — CAR-011.
- No scoring, statistics, or qualification logic — slices 2 and 3.
- No CAR-002 artifact is renamed, moved, or mutated. Additive only.

## 4. Review order

**Review this PR first.** It is 1 of 3 and both later slices depend on it.

Suggested reading order within the PR:

1. `speckit-pro/speckit_pro_runner/materializer.py` — smallest surface, and the
   only file that ships to users.
2. `tests/speckit-pro/unit/test-canonical-agent-materializer.py` — the six drift
   classes are the real specification of the file above.
3. `tests/speckit-pro/layer6-efficiency/lib/claude_successor_freeze.py`, then its
   test.
4. `tests/speckit-pro/layer6-efficiency/lib/claude_treatment_runner.py`, then its
   test.
5. The regenerated payload paths **last**, and only to confirm they are
   machine-produced. They are forbidden to hand-edit; see section 7.

## 5. Scope budget

Counting rule for logic LOC: non-blank lines excluding comments and docstrings.

| Metric | Ratified in `plan.md` | Measured on the branch | Delta |
|---|---|---|---|
| Shipped production files | 1 | **1** | on budget |
| Authored implementation files | 11 | **10** | -1 (see known gaps) |
| Regenerated artifacts | 12 | **30** | **+18, re-run trigger fired** |
| Changed paths | 23 | **43** | **+20, over the 25-file block threshold** |
| Logic LOC | 735 | **1,260** | **1.71x over** |

Measured logic LOC composition: `materializer.py` 149 (shipped),
`claude_successor_freeze.py` 699, `claude_treatment_runner.py` 411,
`run-efficiency-benchmarks.py` delta 1.

**Two budget findings, both recorded rather than resolved:**

1. **The regenerated set is 30, not twelve.** `plan.md` states that if
   implementation discovers the regenerated set is larger than twelve, the
   correct response is to re-run the gate and record the result — **not** to
   split Work Package A. That trigger has fired and this section is the record.
   The additional eighteen are the twelve `installed-cache-proof*.json` fixtures,
   the six mirrored installed-cache payload paths, plus the docs-site reference
   page and the three XPLAT-009 evidence files, none of which the plan enumerated.
2. **43 changed paths exceeds the 25-file block threshold.** All twenty paths
   over the ratified figure are machine-generated or planning artifacts; the
   authored review surface is 10 files. FR-025 and the roadmap require Work
   Package A to stay intact, so **no re-slicing is proposed here**. Whether to
   grant an exception, or to re-slice against the roadmap, is an operator ruling.

The repository's mechanical estimator undershoots this branch's Python harness
consistently — see the whole-feature note in the slice 3 packet.

## 6. Traceability

| Requirements | Changed files | Verification evidence |
|---|---|---|
| FR-001, FR-027, FR-028, FR-044 (additive records, freeze allowlist, fail-closed publication) | `claude_successor_freeze.py`, `contracts/car-003-additive-records.schema.json`, `contracts/successor-capability-freeze.schema.json` | `test-successor-capability-freeze.py`; quickstart 3b |
| FR-002 … FR-005 (admission, closed exclusion reasons, effort mapping, fast-mode exclusion) | `claude_successor_freeze.py` | `test-successor-capability-freeze.py`; quickstart 3b |
| FR-006, FR-008 (canonical materialization, content-hash proof) | `speckit-pro/speckit_pro_runner/materializer.py` | `test-canonical-agent-materializer.py`; quickstart 3a |
| FR-007, FR-043 (smoke demotion to non-release evidence) | `run-efficiency-benchmarks.py` | `test-efficiency-*`; quickstart 3e |
| FR-009 (mandatory observation manifest) | `docs/ai/research/claude-car-003-mandatory-observation-manifest.json`, `suite-manifest.json` | `test-exact-treatment-runner.py` |
| FR-010, FR-032 (execution trace, reference integrity) | `claude_treatment_runner.py` | `test-exact-treatment-runner.py` |
| FR-026 (generated-artifact contract) | all 30 regenerated paths | `scripts/refresh-release-artifacts.py` no-op; re-verified by T085 |
| FR-029, FR-030, FR-031 (score eligibility, disposition precedence) | `claude_treatment_runner.py` | `test-exact-treatment-runner.py`; quickstart 3d |
| FR-039, FR-045, FR-046 (alias re-point, CAP-Q6) | `claude_successor_freeze.py`, `fixtures/car-003-alias-repoint-replay.json` | `test-successor-capability-freeze.py`; quickstart 3c |
| FR-040, FR-041 (probe contract, effort ladder) | `claude_successor_freeze.py` | `test-successor-capability-freeze.py` |
| FR-042, FR-051 (no API key on any path, environment contract) | `claude_treatment_runner.py` | `test-exact-treatment-runner.py` |
| FR-049 (per-arm cache-root isolation evidence) | `claude_treatment_runner.py` | `test-exact-treatment-runner.py`; quickstart 3d |

Success criteria covered here: SC-001, SC-002, SC-003, SC-004, SC-014, SC-016,
SC-017, SC-020, SC-021, SC-024.

## 7. Verification evidence

- **Full default suite**: `python3 tests/speckit-pro/run-all.py` →
  **4100/4100 passed** (L1 1428, L4 2486, L5 186), wall clock **4m40s**, zero
  live calls.
- **Generated-artifact ritual**: `python3 scripts/refresh-release-artifacts.py`
  reports `Release artifacts already consistent; no changes.` on two consecutive
  runs with a clean `git status` after each — a genuine no-op, not an
  assumed one.
- **Shipped-module hash identity**: all five copies of `materializer.py` hash to
  the same SHA-256 `2ca80dec…c729af` — plugin source, both `dist/` payloads, and
  both installed-cache proof trees — and that value is the one recorded in
  `speckit-pro-runner.sha256` and its two `dist/` mirrors.
- **Privacy**: tree-wide `test-privacy-scan.py` 10/10; targeted CAR-003 scan of
  42 artifact files across the spec, fixture, and research directories returns
  zero hits for absolute home paths, hyphenated home paths, session transcript
  paths, private var folders, UUIDs, and email addresses.
- **Plugin-shaped import**: `materializer.py` resolves with `speckit-pro/` alone
  and no `tests/` tree present (quickstart section 6).

## 8. Known gaps

1. **T022 is deliberately not done.** The live successor-freeze collection is
   operator-only and never runs in CI. The consequence is that
   `docs/ai/research/claude-car-003-successor-capability-freeze.json` does not
   exist yet, which is the one authored file short of the ratified eleven. Until
   an operator runs it, the freeze machinery is proven against synthetic replay
   fixtures and no published freeze exists — so no qualification-capable
   execution is possible. That is the intended fail-closed state, not a defect.
2. **CAP-Q6 is closed by construction, not by observation.** The alias-repoint
   proof uses a synthetic replay fixture that supplies a divergent observed
   identity below the live trigger path while overrides remain genuinely unset.
   This is deliberate: inducing a real re-point would require setting the very
   override the proof requires to be unset. The catch-22 is resolved in the
   design, but the live confirmation still depends on T022.
3. **The regenerated set and changed-path count both exceed the ratified
   budget** — see section 5. Recorded for an operator ruling; not resolved here.

## 9. Rollback and feature-flag notes

- **No feature flag.** Every artifact CAR-003 produces is additive and versioned,
  so there is no runtime toggle to guard.
- **Rollback is a plain revert.** Reverting this PR removes the freeze and
  treatment modules, the shipped materializer, and the regenerated payloads
  together. Because the payload refresh is deterministic and idempotent, a revert
  followed by `python3 scripts/refresh-release-artifacts.py` returns the tree to
  a self-consistent pre-CAR-003 state.
- **Nothing downstream depends on this yet at merge time.** Slices 2 and 3 are
  not open when this lands, so a revert has no dependent PR to break.
- **No CAR-002 state is mutated**, so a revert cannot corrupt archived evidence —
  the only removal is CAR-003's own additive records.
- **Shipped-surface caveat**: `materializer.py` is real user-facing plugin
  content. A revert must include the payload refresh, or the installed-cache
  proofs will reference a module the source tree no longer has.

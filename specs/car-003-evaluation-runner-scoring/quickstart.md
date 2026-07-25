# Quickstart: Validating CAR-003

**Date**: 2026-07-24 | **Spec**: `specs/car-003-evaluation-runner-scoring/spec.md`

How to prove CAR-003 works. Every command below runs from the repository root
with **zero live model calls** unless the section is explicitly marked
**operator-only**.

## Prerequisites

- Python 3.11 or newer on `PATH`. No packages to install — the repository's
  tooling is standard library only.
- A clean checkout. Deterministic replay (SC-011) is defined against a clean
  checkout, so uncommitted evidence invalidates the claim.
- For operator-only sections: the pinned Claude Code client, subscription
  authentication, and an explicit budget. **No path requires an API key**
  (FR-042).

## 1. Baseline

```bash
python3 tests/speckit-pro/run-all.py
```

Expected before any CAR-003 change: green, 3251/3251, zero live calls. This is
the number every later step is measured against.

## 2. Contract validation (all three slices)

The eight CAR-003 schemas under `specs/car-003-evaluation-runner-scoring/contracts/`
are the rule surface. Confirm they parse and that the parity-critical values
match the Codex twin:

```bash
python3 tests/speckit-pro/run-all.py --layer 4
```

**Expected**: the CAR-003 contract tests pass, asserting at minimum:

- `score-bundle` `score_disposition`, `failure_plane`, `failure_code`, and
  `invalidation_reason` are set-equal to the Codex twin's committed enums
  (FR-034).
- `analysis-plan` `pareto_policy.dimensions` is exactly the eight-member set,
  set-equal to the twin's (FR-018).
- The three repo-level shared contracts under
  `tests/speckit-pro/layer6-efficiency/contracts/` are **unmodified**. Any diff
  here is a cross-platform break, not a CAR-003 change.
- `treatment_disposition` and `disposition_reasons` are read from the shared
  contract, never redefined (FR-030, FR-034).

See `contracts/` for the schemas and `data-model.md` for the entity invariants
each one encodes.

## 3. Slice 1 — successor freeze and exact treatment

### 3a. Canonical materializer, content-hash proof (FR-006, FR-008)

```bash
python3 tests/speckit-pro/run-all.py --layer 4
```

**Expected** from `tests/speckit-pro/unit/test-canonical-agent-materializer.py`:

- Rendering an agent to a destination path and hashing the **bytes read back
  from disk** reproduces the recorded hash.
- Six drift classes that parsed-field equivalence cannot see each change the
  hash: key order, whitespace, comments, unknown keys, line endings, encoding.
- A hash computed from the in-memory render buffer is rejected as proof.
- The destination path is verified separately and is absent from the digest
  preimage — the same content at a different path hashes identically.

### 3b. Successor freeze admission and fail-closed publication (FR-002 … FR-005, FR-028, FR-044)

**Expected** from `tests/speckit-pro/unit/test-successor-capability-freeze.py`:

- A tuple in runtime discovery but absent from the official-source ledger is
  excluded with `source_not_admitted`.
- An unmapped source effort value records `canonical_effort_unknown`.
- Fast mode records `topology_control_not_candidate_effort`, never an ordinary
  candidate effort.
- A diagnostic surface **cannot** admit a tuple; disagreement between the
  admitting probe and a diagnostic observation forces investigation or
  exclusion.
- An empty or invalid intersection publishes **diagnostic evidence only**, blocks
  qualification-capable execution, and does **not** promote the six archived
  CAR-002 tuples.
- Every CAR-002 artifact path and ID is byte-unchanged (SC-001).

### 3c. Alias re-point detection (FR-039, FR-045, FR-046 — closes CAP-Q6)

The synthetic replay fixture supplies a divergent observed identity **below** the
live trigger path while environment overrides remain genuinely unset. This is
what resolves the standing catch-22: inducing a real re-point would require
setting the very override the proof requires to be unset.

**Expected**:

- Unchanged route + overrides proven unset + unchanged client version →
  `platform_route_change`, recorded as platform behavior and **never** reported
  as a SpecKit Pro fallback.
- A plugin-initiated substitution → `resolver_fallback`.
- Incomplete override proof, a changed client version, or an unattributable
  cause → `alias_repoint_unresolved`, and admission is **blocked**.
- A behavioral difference with no identity change is a separate diagnostic
  condition, not an alias re-point.
- The freeze-bound identity is read from CAR-003's own successor freeze, not the
  identically named run-time field and not the archived snapshot.

### 3d. Score-eligibility predicate and disposition precedence (FR-030, FR-031)

**Expected** from `tests/speckit-pro/unit/test-exact-treatment-runner.py`:

- `scorable=false` forces ineligibility; `scorable=true` alone does **not**
  admit an outcome.
- With several disqualifiers co-firing, **all** codes appear in
  `disposition_reasons` and the terminal disposition is the highest-precedence
  bucket: `hard_fail` > `non_scorable_rerouted` > `unknown` > `proven`. No
  non-terminal cause is discarded.
- A missing or `unavailable` mandatory observation records
  `mandatory_telemetry_missing` and blocks scoring.
- Paired arms execute with separate ephemeral cache roots, and the isolation is
  recorded as a checked property rather than asserted in prose.

### 3e. Smoke demotion (FR-007)

```bash
grep -n "non_release_evidence" tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py
```

**Expected**: results metadata from the dual-platform prompt-emulation runner and
the lexical quality scorer carries a non-release marker. Historical results are
never promoted as route qualification evidence.

## 4. Slice 2 — governed corpus and blinded scoring

**Expected** from `tests/speckit-pro/unit/test-role-corpus-governance.py`:

- The corpus contains **exactly twelve** role contracts: the eleven required-core
  roles plus `autopilot-fast-helper` (SC-005).
- `autopilot-fast-helper` carries `executable=false`, binds every contract field
  anyway, has **no** `candidate_route_bindings`, emits no score bundle, and is
  not counted as attrition.
- A fixture digest mismatch fails the fixture **before** candidate scoring.

**Expected** from `tests/speckit-pro/unit/test-score-bundle-adjudication.py`:

- No ballot is collected until all seven deterministic hard gates pass.
- A blinded artifact containing any freeze-bound model identity, alias, effort
  value, agent frontmatter key, or route identifier fails the leak check with
  `ballot_non_blind` and blocks scoring.
- A scorer drawn from a candidate's own model family is rejected by the static
  exclusion in the frozen experiment policy.
- Two disagreeing ballots route to the frozen third adjudicator, and its
  provenance attaches to the bundle.
- Every ballot records `provenance_inferred`; blinding is reported as bounded,
  never as complete.

Verify the gitignore allow rule keeps consolidated baselines tracked while raw
results stay ignored:

```bash
git check-ignore -v tests/speckit-pro/layer6-efficiency/results/ || echo "not ignored"
```

## 5. Slice 3 — frozen policy, statistics, replay

**Expected** from `tests/speckit-pro/unit/test-experiment-policy-partitions.py`:

- An objective ID appearing in two registered partitions fails closed with
  `failure_plane=partition` (FR-013).
- A calibration partition with `qualification_eligible=true` is schema-rejected.
- A calibration pair binds the **calibration protocol**, a qualification-eligible
  pair binds the **frozen analysis plan**, and binding both is rejected (FR-037).
- An experiment-policy budget unequal to the analysis-plan budget on a
  qualification-eligible partition fails closed (FR-038).

**Expected** from `tests/speckit-pro/unit/test-analysis-decision-ladder.py`:

- The ladder runs strictly in order; a stage not reached records
  `not_evaluated`, never omission (SC-007).
- A tie, mixed dominance, incomplete evidence, or statistical uncertainty
  produces `no_qualification` or `inconclusive`. **No weighted ranking is
  forced**, and no scalar score or price coefficient appears anywhere in the
  bundle (FR-019, SC-008).
- Candidate failures, timeouts, cancellations, budget exhaustion, and abandoned
  work stay in the estimand at acceptance zero (FR-020, SC-009).
- Reruns are complete-pair only, capped, and classified from arm-blind evidence
  before either outcome is read. Zero one-arm reruns (FR-021, SC-010).
- The `qualified` terminal state is unreachable from a calibration partition
  (FR-024).

### Deterministic replay (SC-011)

```bash
python3 tests/speckit-pro/run-all.py --layer 4
```

**Expected**: replaying the frozen experiment, score, analysis, and decision
bundles reconstructs byte-identical terminal decisions. A trace digest mismatch
or dangling reference produces `trace_reference_integrity_failure` and blocks the
decision bundle — it never repairs by rewrite (FR-032).

## 6. Generated-artifact contract (FR-026, SC-014)

Because the canonical materializer ships in plugin source, any change to it
requires the synchronized refresh. This is a required step, not a footnote.

```bash
python3 scripts/refresh-release-artifacts.py
git status --short
```

**Expected**: runner trust metadata, both install payloads, marketplace
registries, installed-cache fixtures, proof tree hashes, and gate evidence are
all regenerated and consistent. The refresh is idempotent — a second run makes no
further changes. Never hand-edit any of these outputs.

Then prove the shipped module resolves in a **plugin-shaped** layout, with
`speckit-pro/` alone and no `tests/` tree:

```bash
WORKDIR=$(mktemp -d)
cp -R speckit-pro "$WORKDIR/speckit-pro"
python3 -c "
import importlib.util, pathlib, sys
root = pathlib.Path(sys.argv[1]) / 'speckit-pro' / 'speckit_pro_runner'
spec = importlib.util.spec_from_file_location('materializer', root / 'materializer.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print('plugin-shaped import OK')
" "$WORKDIR"
rm -rf "$WORKDIR"
```

**Expected**: `plugin-shaped import OK`. A failure here means the module reached
back into the test tree, which the constitution forbids.

## 7. Full gate

```bash
python3 tests/speckit-pro/run-all.py
```

**Expected**: green, with the new CAR-003 tests added to the 3251 baseline, and
**zero live calls** (SC-019).

```bash
python3 tests/speckit-pro/run-all.py --layer 1
python3 tests/speckit-pro/run-all.py --layer 4
```

Layer 1 covers plugin structure for the new shipped module and the regenerated
payloads; Layer 4 covers runtime and script safety plus the new unit coverage.

## 8. Operator-only: live collection and the calibration pilot

**These are the only paths that make live model calls. They are never run in CI
and never run by the default suite** (FR-022, design concept Q10).

Each requires an explicit, local, pinned, budgeted invocation with separate
ceilings for attempts, wall-clock duration, raw input tokens, cache-write tokens
by TTL class, cache-read tokens, output tokens, candidate count, and
confirmation-entry count.

1. **Successor freeze collection** (slice 1, first operator action). Runs the
   `claude -p --model <alias-or-id>` print-mode canary probe on the pinned
   client, over the full ordered effort ladder `low` through `max` for every
   role-eligible model. Records the result whichever way it resolves — including
   whether the `opus` alias has re-pointed since the archived snapshot, which is
   the standing open question CAR-003 exists to answer.

2. **Calibration pilot** (slice 3). Runs **only** disposable calibration
   objectives from a `qualification_eligible=false` partition. Proves exact
   dispatch, scoring, and statistical plumbing end to end, then supplies the
   variance estimates that let the analysis plan freeze.

**Boundary check after either run**:

- Every committed snapshot and replay fixture passes deny-by-default
  sensitive-field inspection and contains only allowlisted sanitized boundary
  evidence (SC-015). Raw captures stay in the operator-only retention store.
- Committed evidence contains no absolute home paths and no session identifiers.
  The existing sanitization helpers normalize both; the tree-wide privacy scan is
  the backstop.
- No screening, selection, cohort-lock, or integrated-confirmation objective was
  consumed.

## Success criteria coverage

| Criterion | Verified by |
|---|---|
| SC-001 | Section 3b — CAR-002 paths and IDs unchanged |
| SC-002, SC-003 | Section 3b — admission evidence and closed exclusion reasons |
| SC-004 | Section 3d — score-eligibility predicate |
| SC-005 | Section 4 — twelve role contracts |
| SC-006 | Section 4 — two ballots plus adjudicator |
| SC-007, SC-008 | Section 5 — ordered ladder, inconclusive handling |
| SC-009, SC-010 | Section 5 — estimand retention, complete-pair reruns |
| SC-011 | Section 5 — deterministic replay |
| SC-012 | Section 5 — pre-cohort outcome absence digest |
| SC-013 | `plan.md` reviewability section — three ordered slices |
| SC-014 | Section 6 — generated-artifact refresh |
| SC-015 | Section 8 — boundary check |
| SC-016 | Section 3b — fail-closed publication |
| SC-017 | Section 3c — CAP-Q6 closed |
| SC-018 | Section 8 — full ordered effort ladder probed |
| SC-019 | Section 7 — full suite green, zero live calls |

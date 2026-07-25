# CAR-003 Slice 2 — PR Review Packet

**Feature**: `specs/car-003-evaluation-runner-scoring/`
**Slice**: 2 of 3 — US3, governed corpus and blinded scoring
**Proposed PR title**: `feat(speckit-pro): add the governed role corpus and blinded scoring`

> Title validated against the release-readiness gate pattern
> `^(feat|fix|chore|docs|test|refactor)\([a-z0-9-]+\): .+` — **PASS**.

The nine sections below are the set `spec.md` "PR Review Packet Requirements"
makes mandatory.

---

## 1. What changed

Slice 2 turns "we ran the right thing" (slice 1) into "we judged it fairly". Two
modules, no shipped production code.

- **`claude_role_corpus.py`** — the governed twelve-role fixture corpus: the
  eleven required core roles plus `autopilot-fast-helper`. Every role contract
  binds role/source, partition, tool and mutation contract, expected artifact,
  acceptance oracle, digest, and independent-validity contract.
  `autopilot-fast-helper` carries `executable=false`, binds every contract field
  anyway, has no `candidate_route_bindings`, emits no score bundle, and is **not**
  counted as attrition — it is a contract-only role until CAR-011 authors it.
  Required-core statistics are reported separately from the twelve-role total. A
  fixture digest mismatch fails the fixture *before* candidate scoring.
- **`claude_score_bundle.py`** — the seven deterministic hard gates (`role`,
  `safety`, `grounding`, `mutation`, `tool`, `output`, `acceptance`), then
  candidate-blind two-ballot scoring, then adjudication. No ballot is collected
  until every required gate passes. A blinded artifact containing any
  freeze-bound model identity, alias, effort value, agent frontmatter key, or
  route identifier fails the leak check with `ballot_non_blind` and blocks
  scoring. A scorer drawn from a candidate's own model family is rejected by the
  static exclusion in the frozen experiment policy. Two disagreeing ballots route
  to the frozen third adjudicator and its provenance attaches to the bundle.
  Every ballot records `provenance_inferred`, so blinding is reported as bounded,
  never as complete.
- **`tests/speckit-pro/layer6-efficiency/.gitignore`** — the evidence-boundary
  rule. `results/*` ignores the directory's *contents* rather than the directory
  itself, because git cannot re-include a file whose parent directory is
  excluded; only the sanitized, deterministic, digest-addressed
  `results/consolidated-baseline.json` is allow-listed back in, named explicitly
  so future per-run artifacts written beside it stay ignored.

## 2. Why

A benchmark that can see which model produced an answer is not a benchmark. The
leak check exists because the blinding surface is wide — model IDs, aliases,
effort values, agent frontmatter keys, and route identifiers all leak candidate
identity, and any one of them is enough to bias a scorer.

Two ballots plus a frozen adjudicator, rather than one ballot, is what makes a
decision-affecting disagreement visible instead of silently resolved. And the
seven hard gates run first specifically so that semantic judgment is never spent
on an artifact that already failed a deterministic check — the expensive,
subjective step is gated behind the cheap, objective one.

The corpus is governed rather than ad hoc because CAR-007 through CAR-010 will
draw cohorts from it; a corpus that drifts between campaigns cannot support a
pooled comparison.

## 3. Non-goals

- No live model calls. Zero in the default suite.
- No statistics, no qualification ladder, no terminal decisions — slice 3.
- No analysis plan and no numeric thresholds — slice 3, and post-calibration.
- No changes to shipped plugin source. This slice has **zero** production files.
- No modification of the repo-level shared contracts under
  `tests/speckit-pro/layer6-efficiency/contracts/`, which are cross-platform
  surface. Any diff there is a cross-platform break, not a CAR-003 change.
- No `autopilot-fast-helper` agent definition — CAR-011 owns that.

## 4. Review order

**Review this PR second**, after slice 1. It reads slice 1's successor freeze for
leak-check identities and slice 1's treatment record for score eligibility, so it
does not stand alone.

Suggested reading order within the PR:

1. `contracts/role-corpus.schema.json` and `contracts/score-bundle.schema.json` —
   the rule surface both modules implement.
2. `claude_role_corpus.py`, then `test-role-corpus-governance.py`.
3. `claude_score_bundle.py`, then `test-score-bundle-adjudication.py`. Read the
   leak check and the hard-gate ordering first; they carry the most risk.
4. `tests/speckit-pro/layer6-efficiency/.gitignore` — three lines, but it is the
   evidence boundary. Confirm the negation rule behaves as intended.

## 5. Scope budget

Counting rule for logic LOC: non-blank lines excluding comments and docstrings.

| Metric | Ratified in `plan.md` | Measured on the branch | Delta |
|---|---|---|---|
| Shipped production files | 0 | **0** | on budget |
| Authored implementation files | 7 | **8** | +1 |
| Changed paths | 7 | **10** | +3 |
| Logic LOC | 533 | **767** | **1.44x over** |

Measured logic LOC composition: `claude_score_bundle.py` 587,
`claude_role_corpus.py` 177, `.gitignore` pattern lines 3.

The +1 authored file is `tests/speckit-pro/unit/test-speckit-pro-runner.py`,
modified but not projected by the plan. The +3 changed paths are that file, the
regenerated docs-site reference page, and `tasks.md`.

At 10 changed paths and zero production files this slice is comfortably under the
25-file block threshold. The LOC overrun is real but does not change the slice
boundary.

## 6. Traceability

| Requirements | Changed files | Verification evidence |
|---|---|---|
| FR-011, FR-012 (twelve-role governed corpus, contract-only role) | `claude_role_corpus.py`, `fixtures/car-003-role-corpus.json`, `contracts/role-corpus.schema.json` | `test-role-corpus-governance.py`; quickstart 4 |
| FR-013 (partition binding, corpus side) | `claude_role_corpus.py` | `test-role-corpus-governance.py` |
| FR-014 (seven deterministic hard gates, fail closed on missing evidence) | `claude_score_bundle.py`, `contracts/score-bundle.schema.json` | `test-score-bundle-adjudication.py`; quickstart 4 |
| FR-015, FR-016 (two candidate-blind ballots, frozen third adjudicator) | `claude_score_bundle.py` | `test-score-bundle-adjudication.py`; quickstart 4 |
| FR-027 (evidence boundary — ignore rule half) | `tests/speckit-pro/layer6-efficiency/.gitignore` | `git check-ignore -q` on `results/`; quickstart 4 |
| FR-033 (fixture digest binding) | `claude_role_corpus.py` | `test-role-corpus-governance.py` |
| FR-034 (closed disposition, plane, failure-code, invalidation sets adopted verbatim from the Codex twin) | `contracts/score-bundle.schema.json`, `claude_score_bundle.py` | `test-score-bundle-adjudication.py`; quickstart 2 set-equality assertions |
| FR-035 (scorer family exclusion) | `claude_score_bundle.py` | `test-score-bundle-adjudication.py` |
| FR-036 (sanitized boundary evidence only) | `.gitignore`, fixtures | targeted privacy scan; `test-privacy-scan.py` |
| FR-047, FR-048 (blinding leak check, bounded-blinding provenance) | `claude_score_bundle.py` | `test-score-bundle-adjudication.py`; quickstart 4 |

Success criteria covered here: SC-005, SC-006, SC-015.

## 7. Verification evidence

- **Full default suite**: `python3 tests/speckit-pro/run-all.py` →
  **4100/4100 passed** (L1 1428, L4 2486, L5 186), zero live calls.
- **Parity contracts untouched**: the three repo-level shared contracts under
  `tests/speckit-pro/layer6-efficiency/contracts/` are unmodified on this branch,
  and the parity mirrors `score-bundle.schema.json` and
  `analysis-decision.schema.json` keep their enums set-equal to the Codex twin's
  committed values.
- **Evidence boundary**: `git check-ignore -q
  tests/speckit-pro/layer6-efficiency/results/` exits 0 — the raw-results path is
  ignored. No raw per-run capture is tracked; the only committed result artifacts
  are the pre-existing sanitized `results-codex/` consolidated baseline.
  (Check with `-q`, not `-v`: `-v` reports a match for a path hit by the
  *negation* rule and silently inverts the reading.)
- **Privacy**: targeted CAR-003 scan of 42 artifact files returns zero hits
  across all six sensitive-field patterns; tree-wide scan 10/10.

## 8. Known gaps

1. **Outstanding spec contradiction, FR-014 versus FR-034 — needs an operator
   ruling, deliberately not resolved in code.** FR-014 states that a missing hard
   gate result must fail closed as `failure_plane=schema` with
   `failure_code=required_evidence_missing`. FR-034 defines a *total*
   code-to-plane mapping that files `required_evidence_missing` under
   `evidence_boundary`, and further orders that any pair not in its table must
   fail closed as `(schema, schema_invalid)`. The pair FR-014 prescribes is
   therefore precisely a pair FR-034's table excludes, and FR-034 would rewrite
   it to a different failure code entirely. The three readings —
   `(schema, required_evidence_missing)`, `(evidence_boundary,
   required_evidence_missing)`, and `(schema, schema_invalid)` — are mutually
   incompatible. The implementation keeps **both requirements visible** rather
   than silently picking a winner, because choosing one here would quietly narrow
   a closed cross-platform taxonomy that FR-034 requires to stay byte-identical
   with the Codex twin. Resolving this is an operator decision and will need a
   matching change on both platforms.
2. **Blinding is bounded, not complete.** Every ballot records
   `provenance_inferred`. Stylistic fingerprints are not removable by the leak
   check, so residual identity signal is possible. This is reported honestly in
   the bundle rather than claimed away.
3. **The consolidated baseline is allow-listed but not yet produced.** The
   `results/` directory does not exist on this branch; the allow rule is written
   ahead of the first sanitized baseline, which arrives with the operator-only
   calibration pilot.

## 9. Rollback and feature-flag notes

- **No feature flag.** All artifacts are additive and versioned.
- **Rollback is a plain revert** and touches no shipped plugin surface — this
  slice has zero production files, so no payload refresh is needed and no
  installed-cache proof changes.
- **Revert order matters.** Slice 3 consumes this slice's score bundles. If slice
  3 has landed, revert slice 3 first; reverting this alone would leave slice 3
  referencing modules that no longer exist.
- **The `.gitignore` change is the one line with a data consequence.** Reverting
  it un-ignores `results/`, which would allow raw per-run captures to be
  committed. If this PR is reverted for any reason other than removing the whole
  feature, keep the ignore rule.

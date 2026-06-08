# Quickstart: validating the roadmap-MOC home note + render_index activation

Runnable validation scenarios that prove the feature works end-to-end. Implementation details
live in `tasks.md` and the implementation phase; the byte format lives in
[`contracts/roadmap-moc-index.md`](./contracts/roadmap-moc-index.md). This is a validation /
run guide.

## Prerequisites

- The speckit-pro plugin SOURCE repo, at the feature worktree.
- `bash` (3.2+) and `jq` on `PATH` (the SessionStart hook warns if `specify` is missing, but
  these scenarios exercise the generator + tests, not the `specify` CLI).
- No language toolchain — verification is the bash test layers.

## Scenario A — Deterministic generator path (SC-004 / SC-005 / FR-011…FR-019): the L4 fixture

This is the primary, fully deterministic gate — and the unit test for the activated
`render_index` home-note path.

```bash
# From the repo root.
bash tests/speckit-pro/run-all.sh --layer 4
```

**Expected outcome — all of the following hold:**

1. The **existing** PRSG-003 cases in `test-generate-spec-index.sh` stay GREEN — every
   per-spec `SPEC-MOC.md` is byte-identical to its pre-activation output (SC-005 regression
   guard; the spec-MOC INDEX still renders empty).
2. The **new** home-note fixture case passes: given a fixture REPO_ROOT containing
   `docs/ai/specs/<slug>-roadmap-MOC.md` (carrying only the INDEX sentinel pair) and several
   gated `specs/*/SPEC-MOC.md`, running the generator fills the home note's INDEX zone with
   one `- [<spec_id>](../../../specs/<dir>/SPEC-MOC.md) · <status>` row per gated spec, ordered
   normalized-ID ascending (FR-012/FR-013/FR-014).
3. A spec with **empty/missing `status`** still gets a row (link + blank status), not dropped
   (FR-015) — and its exact bytes match the contract (the trailing-whitespace idempotence
   trap is frozen).
4. A **legacy/non-gated** spec dir in the fixture is **skipped** (FR-016).
5. **Idempotence**: a second generator run over the same committed fixture yields a
   **zero-byte diff** on the home note (SC-004 / FR-019).

Targeted single-test run while iterating:

```bash
bash tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh
```

## Scenario B — Structural + Codex-parity validation (SC-008, FR-020/FR-021)

```bash
bash tests/speckit-pro/run-all.sh --layer 1
```

**Expected outcome:**

- `validate-codex-skills.sh` passes: the prd emit step exists in BOTH
  `skills/speckit-prd/SKILL.md` and `codex-skills/speckit-prd/SKILL.md`, and the coach
  teaching surface exists in BOTH `speckit-coach` mirrors.
- The generator remains a **single shared copy** (no `generate-spec-index.sh` duplicated into
  `codex-skills/`); `validate-plugin-payload` confirms no `tests/`/`specs/` leaked under the
  plugin dir.
- The new `skills/speckit-coach/references/roadmap-moc-guide.md` is well-formed; the Codex
  coach mirror links to the shared references tree (no duplicate doc).

## Scenario C — Full fast suite (constitution IV quality gate)

```bash
bash tests/speckit-pro/run-all.sh        # Layers 1, 4, 5 — zero failures
```

The gate for "implementation complete" (constitution IV). Layer 5 (tool scoping) is unaffected
by this feature but must stay green.

## Scenario D — prd emits the home note (SC-001/SC-002/SC-003) — developer-local AI eval (L3)

Per the spec's deliberate test set, prd's emit behavior is validated by an L3 functional eval
on a **fresh fixture roadmap** (NOT this repo — backfill onto this repo's own roadmap is
PRSG-011's job). Developer-local; requires `claude -p` + `skill-creator`.

**Expected outcome (the eval asserts):**

- A `speckit-prd` run on a fresh fixture roadmap produces **exactly three** artifacts — the
  PRD, the technical-roadmap, and `docs/ai/specs/<slug>-roadmap-MOC.md` — with **both zones**
  present in the home note (SC-001).
- The curated epics zone is derived from the roadmap's phases with **zero new interview
  questions** vs. the pre-PRSG-004 prd interview (SC-002).
- A roadmap yielding > ~10 epics still produces a written home note plus a **single advisory
  line** — no failure, no block (SC-003).
- The home note's `up:` is a relative `[]()` link to the technical-roadmap, and the roadmap
  carries the reciprocal link back (FR-006).

## Scenario E — coach teaches the two-zone split (SC-007) — developer-local AI eval (L2/L3)

The new Layer-2 trigger case in `speckit-coach-trigger.json` (and its `codex-evals` mirror)
verifies the description surface triggers on roadmap-MOC home-note queries; the L3 functional
eval verifies the answer content.

**Expected outcome:**

- Asked how the roadmap-MOC home note is structured, `speckit-coach` distinguishes the
  **curated** zone (hand-edited) from the **generated** INDEX zone (regenerated, never
  hand-edited) and states the advisory **~10-epic cap** (warn, not block) (SC-007).

## Scenario F — Path A/B parity (developer-local, L8)

```bash
bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run   # free structural check
```

Confirms the prd/coach changes keep the Agent-Teams vs parallel-subagents fallback equivalent.
The `--live` mode (budget-capped `claude -p`) is the full parity arm, developer-local.

---

## Success-criteria → scenario map

| Success criterion | Validated by |
|-------------------|--------------|
| SC-001 (3 artifacts, both zones) | Scenario D (L3) |
| SC-002 (zero new questions) | Scenario D (L3) |
| SC-003 (>~10 epics → advisory, still writes) | Scenario D (L3) |
| SC-004 (byte-identical INDEX, idempotence) | Scenario A (L4) |
| SC-005 (spec-MOC byte-identical; PRSG-003 green) | Scenario A (L4 — existing cases) |
| SC-006 (every link relative `[]()`, no wikilink) | Scenario A (L4) |
| SC-007 (coach explains both zones + cap) | Scenario E (L2/L3) |
| SC-008 (Codex parity; generator single copy) | Scenario B (L1) |

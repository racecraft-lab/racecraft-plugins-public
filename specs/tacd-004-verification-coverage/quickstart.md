# Quickstart: Verifying TACD-004 (Verification Coverage)

Runnable validation that proves the verification-coverage slice and the bundled
payload fix work end-to-end. Run every command from the repository root
(`.worktrees/tacd-004-verification-coverage`). There is no package manager and no
build/typecheck/lint toolchain — verification is the deterministic shell suite plus
the payload rebuild.

## Prerequisites

- `bash`, `jq`, `git`, `python3` on PATH.
- On the `tacd-004-verification-coverage` branch:
  `git rev-parse --abbrev-ref HEAD` → `tacd-004-verification-coverage`.
- Working tree clean except expected SpecKit artifacts: `git status --short`.

## 1. Default deterministic suite (SC-004 / AC-4.4 / FR-010)

```bash
bash tests/speckit-pro/run-all.sh
```

**Expected**: all of Layers 1, 4, 5 pass with zero failures, including the new
Layer 1 validators (pointer-coverage, target-resolution, body-completeness) and the
reworked Layer 5 tool-scoping checks. The suite does NOT depend on live AI eval
execution.

Focused runs while iterating:

```bash
bash tests/speckit-pro/run-all.sh --layer 1   # structural (pointer/resolution/completeness)
bash tests/speckit-pro/run-all.sh --layer 5   # tool-scoping (named-tool guard, no named MCP set)
bash tests/speckit-pro/run-all.sh --layer 4   # script-unit
```

## 2. Payload fix + rebuild (SC-005 / FR-007, FR-008, FR-013)

```bash
# Rebuild dist/** from source via the builder (never hand-edit payloads).
bash scripts/build-plugin-payloads.sh

# All Claude skill bodies are restored (no skill collapses to ~10 lines).
for s in $(ls dist/claude/speckit-pro/skills/); do
  src="speckit-pro/skills/$s/SKILL.md"
  dst="dist/claude/speckit-pro/skills/$s/SKILL.md"
  [ -f "$src" ] && [ -f "$dst" ] && \
    printf "%-26s src=%4s dist=%4s\n" "$s" "$(wc -l < "$src")" "$(wc -l < "$dst")"
done

# dist/** is committed in sync with source (no drift after rebuild).
git diff --exit-code -- dist
```

**Expected**: every built Claude `SKILL.md` retains its full body (the last non-guard
source heading survives; body length within tolerance of source-minus-guard). Before
the fix, 8 of 10 skills truncate to ~10–11 lines; after the fix they match source
minus the stripped guard section. `git diff --exit-code -- dist` is clean.

## 3. Non-vacuity / deliberate-regression proofs (FR-012)

Each new guard MUST fail on a deliberate regression and return to green when reverted.
Run these locally before the PR (do not commit the regressions):

```bash
# (a) Named-tool guard (Layer 5): re-add a named vendor MCP tool to an active agent,
#     run --layer 5, confirm FAIL, then revert and confirm PASS.
# (b) Pointer-coverage (Layer 1): strip the directive reference from an active agent,
#     run --layer 1, confirm FAIL (names the uncovered agent), then revert.
# (c) Target-resolution (Layer 1): rename/remove the directive at a referenced path
#     inside dist/claude/** (or dist/codex/**), run --layer 1, confirm FAIL for both
#     runtimes, then restore (rebuild).
# (d) Body-completeness (Layer 1): truncate a built Claude SKILL.md (drop the trailing
#     heading), run --layer 1, confirm FAIL (names the truncated skill), then rebuild.
```

**Expected**: each of (a)–(d) flips the suite from green to a failing check that names
the offending file/agent/path/skill; reverting (or rebuilding) restores green.

## 4. Eval coverage (SC-003 / AC-4.3 / FR-005, FR-006, FR-009)

The four eval files are validated by committed/replay fixtures — no live model run
gates merge. Confirm the JSON is valid and the rewrite/parity rules hold:

```bash
# All four eval files remain valid JSON.
for f in tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json \
         tests/speckit-pro/layer3-functional/evals/speckit-coach-evals.json \
         tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json \
         tests/speckit-pro/layer3-functional/codex-evals/speckit-coach-evals.json; do
  jq -e . "$f" >/dev/null && echo "valid: $f"
done

# No optional-tool expectation prescribes a named vendor set (absence arm).
grep -lE "[Tt]avily|[Cc]ontext7|RepoPrompt" \
  tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json \
  tests/speckit-pro/layer3-functional/evals/speckit-coach-evals.json \
  tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json \
  tests/speckit-pro/layer3-functional/codex-evals/speckit-coach-evals.json \
  || echo "no named-vendor preference remains in optional-tool expectations"
```

**Expected**: all four files are valid JSON; the five behavior-observable scenarios
(installed-capability discovery, fallback, evidence path, citations/local-file
references, lowered confidence) are present as fixtures; each optional-tool expectation
asserts both absence of a named set and an affirmative capability-first answer; Claude
and Codex are in parity for each scenario. (Any retained named-tool string must be
historical/provenance or a deliberate absence-arm reference, not a re-taught
preference.)

## 5. Script safety (constitution II)

```bash
bash -n scripts/build-plugin-payloads.sh
for f in tests/speckit-pro/layer1-structural/validate-capability-pointer.sh \
         tests/speckit-pro/layer1-structural/validate-capability-resolution.sh \
         tests/speckit-pro/layer1-structural/validate-payload-completeness.sh \
         tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh; do
  [ -f "$f" ] && bash -n "$f" && echo "syntax ok: $f"
done
git diff --check
```

**Expected**: clean `bash -n` on all changed scripts; new validators begin with
`#!/usr/bin/env bash` + `set -euo pipefail`, are executable, and `git diff --check`
reports no whitespace errors.

---

## PR Review Packet Checklist (spec PR Review Packet Requirements)

The PR description MUST include all of the following. Keep titles/bodies
public-readable and conventional-commits-prefixed (the production fix is a
`fix(speckit-pro):` change).

- [ ] **What changed**: Layer 5 named-MCP set removed + named-tool regression guard
      added; Layer 1 pointer-coverage / target-resolution / body-completeness
      validators added; `strip_codex_guard` section-boundary fix + `dist/**` rebuild;
      four eval files rewritten with five behavior scenarios.
- [ ] **Why**: lock the vendor-neutral capability-discovery contract so it cannot
      silently regress, and repair the consumer-facing payload truncation (8 of 10
      Claude skills currently install with empty bodies).
- [ ] **Non-goals**: no agent decision-logic changes; no prerequisite-script changes;
      no shipped-docs wording changes; no new test layer / broad scanner; no live AI
      eval gate; no separate hotfix branch (payload fix bundled here).
- [ ] **Review order**: (1) `strip_codex_guard` fix; (2) `dist/**` regeneration
      (source-derived); (3) Layer 1 validators; (4) Layer 5 rework; (5) eval rewrites.
- [ ] **Scope budget**: ~292 reviewable LOC, 1 production file, ~10 total files —
      within budget; `dist/**` excepted as source-derived.
- [ ] **Traceability**:
      - AC-4.1 (SC-001) → `validate-tool-scoping.sh` (named-tool guard + named-MCP
        removal) → §1, §3(a).
      - AC-4.2 (SC-002) → `validate-capability-pointer.sh`,
        `validate-capability-resolution.sh` → §1, §3(b/c).
      - AC-4.3 (SC-003) → four eval files → §4.
      - AC-4.4 (SC-004) → `bash tests/speckit-pro/run-all.sh` green → §1.
      - SC-Payload (SC-005) → `strip_codex_guard` fix + `dist/**` rebuild +
        `validate-payload-completeness.sh` → §2, §3(d).
- [ ] **Verification evidence**: paste `run-all.sh` summary, the §2 body-length table,
      and the §3 regression-flip results.
- [ ] **Known gaps**: none expected; if the approved-equivalent allowlist is non-empty,
      list each agent and why it carries an equivalent rather than the literal
      reference.
- [ ] **Rollback / flags**: no feature flag. Rollback = revert the PR; the payload fix
      is forward-only (re-running the builder restores bodies). No destructive
      migration.
- [ ] **CI note**: confirm whether `.github/workflows/*` or CLAUDE.md CI/CD sections
      need updates (this slice does not change workflows).

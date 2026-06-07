# UAT Runbook: prsg-005-slice-sizing-heuristics

| Field | Value |
|-------|-------|
| Spec | prsg-005-slice-sizing-heuristics |
| Branch | prsg-005-slice-sizing-heuristics |
| PR | **PR:** <set on PR open> |
| Generated from | 2026-06-07T03:05:35Z |



## Env Setup

No build step and no package install required. You need two standard tools: `bash` and `jq`. Both are present on any macOS or Linux machine.

All commands in this runbook that run the estimator script or the test suite assume your working directory is the **repository root** of your checkout — the directory that contains `speckit-pro/`, `specs/`, and `docs/`.

The fast automated test suite (run this once before starting UAT to confirm the deterministic layer is green):

```bash
bash tests/speckit-pro/run-all.sh
```

This runs Layers 1, 4, and 5 — structural validation, script unit tests, and agent tool scoping. All three should pass before you walk the human acceptance steps below.

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Catalog-level decomposition in speckit-prd (Priority: P1)

**What this confirms:** When someone uses the PRD skill to turn a raw idea into a spec catalog, the catalog comes out as several small end-to-end slices (not one big chunk), each showing an estimated line count and a one-line reason for the slice boundary. An over-size advisory note appears in the catalog, but the interview never stops — it always continues.

**Automated backstop (run first):** From the worktree root:

```bash
bash tests/speckit-pro/run-all.sh --layer 4
```

All estimator unit tests should pass before you walk the human steps below.

**Human acceptance steps:**

1. Open a new Claude Code session and invoke the PRD skill with an idea that would naively become one large spec — for example: "Build a full user authentication and profile management system with login, registration, OAuth, password reset, profile editing, avatar upload, and admin controls."

   Run: `/speckit-pro:speckit-prd`

   Walk through the interview as a normal user would.

2. When the interview completes and the SPEC catalog is emitted, read through each entry. Confirm that the catalog lists **multiple separate spec entries** (not one combined entry covering everything). Each entry should describe a thin end-to-end slice — for example, one entry for "login/registration" and a separate entry for "profile editing," rather than one entry labeled "auth system."

3. For each catalog entry, confirm there is a line reading `Projected reviewable LOC` where N is a number filled in by the estimator (not a blank or a placeholder like `~? LOC`). Confirm there is also a one-line note explaining why this slice is a good vertical cut (something like "delivers working login end-to-end" or "independent deployable unit covering profile reads and writes").

4. If any single entry has an estimated size above roughly 400 lines, confirm the catalog shows an advisory note flagging it as potentially large — and confirm the interview continued anyway and produced a complete catalog. Nothing should have been blocked or refused.

5. Invoke the PRD skill a second time with the same idea. Confirm the estimator produces identical budget numbers for matching entries (same input → same output).

- [ ] US1 confirmed: catalog is multiple thin slices, each has a Projected reviewable LOC field from the estimator and a one-line slice rationale, over-size appears as advisory only, and repeated runs produce the same numbers.

---

<a id="us-2"></a>
### User Story 2 - Per-spec validation and split in grill-me (Priority: P2)

**What this confirms:** When someone uses grill-me to scope a single spec that is too large or cuts across layers rather than end-to-end, the skill asks a split question recommending how many smaller slices to create, and records the chosen split in the design document. A spec that is already a reasonable size gets only an advisory note and no forced split. An unavailable estimate also produces only a note, never a stop.

**This is a human-performed interactive step. Do not automate it.**

**Human acceptance steps (over-size / horizontal case):**

1. Open a new Claude Code session and invoke grill-me on a single spec idea that is clearly too large or is sliced by technical layer — for example: "Implement the data access layer for the user service: write all the database models, repository interfaces, and query methods for users, sessions, and audit logs."

   Run: `/speckit-pro:grill-me`

   Walk through the interview as a normal user would.

2. Watch for the point where grill-me raises the question of slice size or slice shape. It should recommend splitting the spec into N smaller, end-to-end slices and ask whether you want to proceed with that split. Confirm this question appears as part of the normal interview flow (not a hard stop, not an error).

3. Choose a split option when prompted.

4. When the interview finishes and produces a Design Concept document, open that document and confirm the split decision is recorded in the Goals or Open Questions section — for example, "Split into 3 vertical slices: [slice 1 description], [slice 2 description], [slice 3 description]."

**Human acceptance steps (at-or-under-size case):**

5. Start a new grill-me session on a small, tightly scoped spec — for example: "Add a /health endpoint that returns 200 OK with a JSON body showing the current server time."

   Run: `/speckit-pro:grill-me`

6. Walk through the interview. Confirm that the skill does not ask a forced split question. It may show a brief advisory note mentioning the estimated size is within budget, but it should not recommend splitting a spec this small.

7. Confirm the interview completes normally and produces a Design Concept document.

- [ ] US2 confirmed: over-size/horizontal spec triggers a split recommendation question recorded in the design doc; at-size spec gets only an advisory note and no forced split; interview always continues to completion.

---



## FR Coverage Matrix

| Requirement | Check that proves it |
|-------------|----------------------|
| Catalog is multiple thin vertical slices (FR-001) | US1 step 2 |
| Each catalog entry has Projected reviewable LOC field + slice rationale (FR-002) | US1 step 3 |
| grill-me has a slice-sizing branch (FR-003) | US2 step 2 |
| grill-me asks a split question when over-size or horizontal (FR-004) | US2 step 2 |
| Chosen split is recorded in the Design Concept doc (FR-005) | US2 step 4 |
| Estimator accepts structured signals and returns estimated_loc, suggested_slices, status (FR-006) | Negative-Path step A |
| Estimator is deterministic — same input, identical output (FR-007) | US1 step 5; Negative-Path step C |
| Single LOC ceiling constant used by estimator and reference doc (FR-008) | Negative-Path step B (at-ceiling boundary) |
| Both skills use the same single estimator script (FR-009) | Layer 1 fast suite (structural — single file at expected path) |
| SPIDR/INVEST guidance in exactly one shared doc, both skills link to it (FR-010) | Layer 1 fast suite (structural file check) |
| Advisory-only — warn exits 0, nothing blocks (FR-011) | Negative-Path step D |
| No change to roadmap template schema (FR-012) | US1 step 3 (Projected reviewable LOC is an existing field, not a new one) |
| New trigger phrases added without breaking existing routing (FR-013) | Layer 1 + Layer 4 fast suite |
| Codex skill mirrors carry equivalent behavior (FR-014) | Layer 1 fast suite (validate-codex-skills.sh) |
| Reference doc states estimate is a forward guess, not authoritative LOC (FR-015) | Review the file `speckit-pro/skills/speckit-coach/references/slicing-heuristics.md` for the caveat text |
| Malformed/missing/negative inputs produce estimated_loc 0 and status ok (FR-016) | Negative-Path step E |
| Spike flag skips LOC sizing and returns 0/1/ok (FR-017) | Negative-Path step F |
| SC-001: fat idea → multiple slices with Budget + rationale | US1 steps 2–3 |
| SC-002: fat/horizontal spec → split question recorded in design doc | US2 steps 2–4 |
| SC-003: deterministic output at and around the ceiling | Negative-Path steps B–C |
| SC-004: no path blocks | US1 step 4; US2 step 6; Negative-Path step D |
| SC-005: trigger routing unchanged | Layer 1 + Layer 4 fast suite |
| SC-006: guidance in exactly one doc | Layer 1 fast suite |


## Negative-Path Tests

Run all commands below from the worktree root. Each is a standalone command; copy it exactly as written.

**A — Basic happy path (confirm the script runs and produces the expected shape):**
```bash
bash speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh \
  --user-stories 1 --files 2 --frs 3 --new-vs-modify new ; echo "exit=$?"
```
Expected output:
```
{"estimated_loc":150,"suggested_slices":1,"status":"ok"}
exit=0
```

**B — At-ceiling boundary (status is `ok` at exactly 400, not `warn`):**
```bash
bash speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh \
  --files 10 --new-vs-modify new ; echo "exit=$?"
```
Expected output:
```
{"estimated_loc":400,"suggested_slices":1,"status":"ok"}
exit=0
```

**C — Strictly over-ceiling (status is `warn`, exit still 0 — advisory only):**
```bash
bash speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh \
  --files 11 --new-vs-modify new ; echo "exit=$?"
```
Expected output:
```
{"estimated_loc":440,"suggested_slices":2,"status":"warn"}
exit=0
```
Confirm: exit is 0 even though status is `warn`. This is the advisory-only guarantee — a `warn` never blocks.

**D — Determinism (run the at-ceiling command twice, output must be byte-identical):**
```bash
bash speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh \
  --files 10 --new-vs-modify new
bash speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh \
  --files 10 --new-vs-modify new
```
Both lines must produce exactly `{"estimated_loc":400,"suggested_slices":1,"status":"ok"}`.

**E — Bad inputs: negative number and non-numeric value (must not crash, must return 0/ok):**
```bash
bash speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh \
  --files -5 --frs abc ; echo "exit=$?"
```
Expected output:
```
{"estimated_loc":0,"suggested_slices":1,"status":"ok"}
exit=0
```
Confirm: the script does not crash on garbage input and never emits a misleading `warn` when all inputs are bad.

**F — Spike / research-only slice (LOC sizing skipped, always 0/1/ok):**
```bash
bash speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh \
  --spike ; echo "exit=$?"
```
Expected output:
```
{"estimated_loc":0,"suggested_slices":1,"status":"ok"}
exit=0
```
Confirm: `ok` here means "LOC sizing does not apply to a research slice," not that the slice is small.

**G — Estimator unavailable mid-interview (human verification):** Start a grill-me session. If you can simulate an unavailable estimator by temporarily renaming the script, confirm the skill surfaces an advisory note and continues the interview rather than stopping with an error. Restore the script after the check. (This path is also covered by the fast test suite's mock-missing-jq fixture.)

**H — Trigger routing regression (human or Layer 2 check):** Ask the PRD skill to activate using one of its existing phrases (e.g., "create a PRD for my idea"). Confirm it routes to `speckit-prd` and not to another skill. Do the same for `grill-me` using one of its existing phrases. This confirms the new sizing phrases did not break the existing routing.

## Self-Review Findings

**Self-Review:** <not available — workflow file not provided>

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations

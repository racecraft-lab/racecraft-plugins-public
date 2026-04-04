# Tasks: Integration & Verification

**Input**: Design documents from `/specs/004-integration-verification/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. This work is primarily configuration + documentation, with minimal automated test coverage added to validate the new sentinel workflow (Layer 1 structural validation for the sentinel job and corresponding test runner registration).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Exact file paths are included in descriptions

---

## Phase 1: Setup (Foundational Prerequisites)

**Purpose**: The sentinel job MUST be added and merged before branch protection can require it as a status check. This phase is the gating prerequisite for all other phases.

**Critical ordering constraint**: The `validate-plugins` check must exist as a passing GitHub Actions job name before branch protection can register it as a required check (FR-001, FR-013). This means T001 must be merged to `main` via a PR before T004–T006 can be executed.

- [ ] T001 [US1] Add `validate-plugins` sentinel job to `.github/workflows/pr-checks.yml` — job must depend on `[detect, test]`, run `if: always()`, and exit 0 when `needs.test.result` is `success` or `skipped`, exit 1 when `failure` or `cancelled`; additionally the sentinel MUST exit 1 if `needs.detect.result` is `failure` (a detect failure indicates a broken workflow, not a clean skip; see contracts/branch-protection.md for the complete YAML; note: research.md Topic 3 shell expression omits the detect.result check — use contracts/branch-protection.md as the authoritative implementation reference, and add `if [[ "${{ needs.detect.result }}" == "failure" ]]; then exit 1; fi` before the test.result check) (FR-013, FR-013 supplement)
- [ ] T002 [P] Validate pr-checks.yml YAML syntax after sentinel addition: `python3 -c "import yaml, sys; yaml.safe_load(sys.stdin)" < .github/workflows/pr-checks.yml && echo "YAML valid"`
- [ ] T003 Run existing test suite to confirm no regressions before opening PR: `bash speckit-pro/tests/run-all.sh` — all 369 tests must pass (FR-012)

**Checkpoint**: T001 merged to `main` via a squash PR. The `validate-plugins` job name is now visible in GitHub Actions and can be registered as a required status check.

---

## Phase 2: User Story 1 — Branch Protection Enforcement (Priority: P1)

**Goal**: Configure GitHub branch protection on `main` requiring `validate-plugins` and `validate-pr-title` status checks and enforcing squash-only merges. Prevent direct pushes by non-exempt actors while allowing `GITHUB_TOKEN` admin pushes to bypass (SPEC-003 marketplace sync).

**Independent Test**: Attempt to open a PR with a deliberately failing check and confirm the merge button is disabled. Attempt to select "Create a merge commit" and confirm it is unavailable.

**Dependency**: T001 must be merged to `main` before T004–T006 (the `validate-plugins` check name must exist).

- [ ] T004 [US1] Apply squash-only repository merge settings via `gh api --method PATCH /repos/racecraft-lab/racecraft-plugins-public --field allow_squash_merge=true --field allow_merge_commit=false --field allow_rebase_merge=false` (FR-002; these are repository-level settings separate from branch protection)
- [ ] T005 [US1] Apply branch protection rules to `main` via `gh api --method PUT /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection` with payload: `required_status_checks.strict=false`, `required_status_checks.contexts=[validate-plugins, validate-pr-title]`, `enforce_admins=false`, `required_pull_request_reviews=null`, `restrictions=null`, `allow_force_pushes=false`, `allow_deletions=false` — the force-push and deletion fields MUST be explicitly set to false to prevent history-rewriting and accidental branch deletion (FR-001, FR-003, FR-004, FR-005, FR-005 supplement)
- [ ] T006 [US1] Verify branch protection applied correctly: `gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection | jq '{contexts: .required_status_checks.contexts, enforce_admins: .enforce_admins.enabled, allow_force_pushes: .allow_force_pushes.enabled, allow_deletions: .allow_deletions.enabled}'` — expected output: `{"contexts": ["validate-plugins", "validate-pr-title"], "enforce_admins": false, "allow_force_pushes": false, "allow_deletions": false}` (FR-005)

**Checkpoint**: Branch protection is live. A PR with a failing check cannot be merged. Non-squash merge methods are unavailable in the repository UI. GITHUB_TOKEN admin pushes bypass protection.

---

## Phase 3: User Story 2 — Copilot Code Review on PRs (Priority: P2)

**Goal**: Enable Copilot automatic code review so Copilot is automatically added as a reviewer on every new PR. Configuration is UI-only — no API exists for this step (FR-006).

**Independent Test**: Open a new PR against `main` and confirm Copilot is automatically added as a reviewer within 2 minutes. Confirm review comments appear as advisory inline feedback and do not block the merge.

**Dependency**: None — can be executed independently of Phase 2.

- [ ] T007 [P] [US2] Configure Copilot automatic code review via GitHub UI: navigate to https://github.com/racecraft-lab/racecraft-plugins-public/settings/rules → New branch ruleset → Ruleset name: "Copilot Code Review" → Target: Default branch → enable "Automatically request Copilot code review" → enable "Review new pushes" → Save (FR-006; requires Copilot Pro or Pro+ subscription)
- [ ] T008 [P] [US2] Verify Copilot ruleset is active: navigate to repository Settings → Rules → Rulesets and confirm the "Copilot Code Review" ruleset appears with status Active targeting `main` (FR-006)

**Checkpoint**: Copilot is automatically requested as a reviewer on new PRs. Reviews are advisory and do not block merges.

---

## Phase 4: User Story 3 — End-to-End Verification Checklist (Priority: P3)

**Goal**: Create `docs/ai/specs/cicd-release-pipeline-verification.md` as a manual walkthrough document covering 8 pipeline stages, each with an action, expected output, and diagnostic note. Serves as the operational runbook for validating the full CI/CD pipeline.

**Independent Test**: Read the checklist and confirm each of the 8 required stages is present with action, expected output, and diagnostic note. Confirm Stage 1 includes the exact `gh api` branch protection setup commands (FR-005 auditability requirement).

**Dependency**: None — can be authored in parallel with other phases.

- [ ] T009 [P] [US3] Create `docs/ai/specs/cicd-release-pipeline-verification.md` with Stage 1: Feature Branch Creation — action (create branch from `main` using `NNN-feature-name` convention), expected output (branch visible in GitHub), diagnostic (confirm remote push succeeded) (FR-007, FR-008)
- [ ] T010 [P] [US3] Add Stage 2: PR Submission and CI Check Execution — action (open PR, observe checks), expected output (all three jobs run: `detect`, `test`/skipped, `validate-plugins` passes, `validate-pr-title` passes), diagnostic (check Actions tab for failed steps) (FR-007, FR-008)
- [ ] T011 [P] [US3] Add Stage 3: Copilot Review Trigger Confirmation — action (confirm Copilot added as reviewer after PR open or push), expected output (Copilot reviewer appears in PR sidebar, inline comments posted), diagnostic (navigate to Settings → Rules → Rulesets and confirm ruleset targets `main`; check Copilot Pro subscription is active) (FR-006, FR-008)
- [ ] T012 [P] [US3] Add Stage 4: PR Merge (Squash) — action (merge PR via "Squash and merge"), expected output (single squash commit on `main`, branch deleted), diagnostic (confirm non-squash merge methods are unavailable; if merge blocked, check failing status checks in PR) (FR-007, FR-008)
- [ ] T013 [P] [US3] Add Stage 5: Release-Please PR Creation — action (observe release-please bot creates or updates its PR after merge), expected output (PR titled "chore(main): release X.Y.Z" appears within minutes), diagnostic (check Actions → release.yml run log; note: maintainer may pause here — pipeline resumes when release PR is merged) (FR-007, FR-008)
- [ ] T014 [P] [US3] Add Stage 6: Release-Please PR Merge and GitHub Release Publication — action (merge release-please PR), expected output (GitHub Release created with changelog, tag pushed), diagnostic (check Actions log for release step failure; verify release-please-config.json has correct plugin entry) (FR-007, FR-008)
- [ ] T015 [P] [US3] Add Stage 7: Marketplace Sync Commit Push to `main` — action (observe marketplace sync workflow run after GitHub Release), expected output (`chore: sync marketplace.json versions [skip ci]` commit pushed directly to `main` by GITHUB_TOKEN without a PR; `marketplace.json` version numbers updated), diagnostic (check Actions → release.yml sync step log; if push blocked by branch protection, verify `enforce_admins: false` is set — run `gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection | jq '.enforce_admins.enabled'` and confirm it is `false`) (FR-007, FR-008)
- [ ] T016 [P] [US3] Add Stage 8: End-User Plugin Update Confirmation — action (run `/plugin marketplace update racecraft-public-plugins` in a Claude Code session), expected output (marketplace reports new plugin version, update applied successfully), diagnostic (confirm `marketplace.json` in the repo reflects the new version; if stale, re-run the release workflow manually per Recovery procedures in CLAUDE.md) (FR-007, FR-008)
- [ ] T017 [US3] Add the exact `gh api` branch protection setup commands from quickstart.md Steps 4 and 5 to Stage 1 of the verification checklist as the Infrastructure-as-Code record (FR-005 auditability requirement — the checklist is the authoritative config record, not a separate script)
- [ ] T017b [US3] Add a `## Periodic Health Check` section at the end of the verification checklist with the status-check-drift detection command: `gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection --jq '[.required_status_checks.contexts[]]'` — instructing the maintainer to compare the output against actual job names in pr-checks.yml to detect stale required-check names; include note that GitHub does not auto-update branch protection when a job is renamed, and that recovery is to re-run the Stage 1 setup command with updated check names (FR-001/FR-009 supplement)

**Checkpoint**: Verification checklist contains all 8 required stages plus a Periodic Health Check section. Each stage has action, expected output, and diagnostic note. Stage 1 contains the copy-pasteable `gh api` commands.

---

## Phase 5: User Story 4 — CI/CD Workflow Documentation in CLAUDE.md (Priority: P3)

**Goal**: Append five new sections to `CLAUDE.md` covering the complete CI/CD workflow. Sections are additive only — no existing content is modified. Each section must be self-contained per SC-005 (new contributor can understand full workflow from CLAUDE.md alone).

**Independent Test**: Read `CLAUDE.md` alone and confirm a new contributor can understand: branch naming convention, PR title requirements, merge policy, CI check names, release automation flow, how to add a new plugin, and the end-user update path — without consulting any other file.

**Dependency**: None — can be authored in parallel with other phases.

- [ ] T018 [P] [US4] Append `## Contributing & Branching Strategy` section to `CLAUDE.md` covering: branch naming convention (`NNN-feature-name`), conventional commit PR title requirement (scoped or unscoped), squash-only merge policy, and a one-liner pointer to the verification checklist for deeper diagnostics (FR-009, SC-005)
- [ ] T019 [P] [US4] Append `## CI/CD Workflow` section to `CLAUDE.md` covering: overview of pr-checks.yml jobs (`detect`, `test` matrix, `validate-plugins` sentinel, `validate-pr-title`), explanation that `validate-plugins` passes when matrix is skipped (docs-only PRs), maintenance reminder that CLAUDE.md must be updated whenever pr-checks.yml or release.yml changes, and an explicit warning that renaming a workflow job requires updating the corresponding branch protection required-check name (GitHub does not auto-update; stale names silently degrade protection — detection: `gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection --jq '[.required_status_checks.contexts[]]'` and compare against pr-checks.yml job names) (FR-009, FR-013, FR-001/FR-009 supplement)
- [ ] T020 [P] [US4] Append `## Release Process` section to `CLAUDE.md` covering: release-please automation (conventional commit triggers patch/minor/major bumps), GitHub Release publication, marketplace sync commit (GITHUB_TOKEN direct push to `main`), and end-user update path (`/plugin marketplace update racecraft-public-plugins`) (FR-009, SC-005)
- [ ] T021 [P] [US4] Append `## Adding a New Plugin to Release Automation` section to `CLAUDE.md` with accurate instructions for updating `release-please-config.json` (add plugin entry under `packages`) and `.release-please-manifest.json` (add initial version entry) — instructions must match the actual SPEC-001 configuration structure already in those files (FR-009, FR-011)
- [ ] T022 [US4] Cross-reference the four Phase 5 sections (Contributing & Branching Strategy, CI/CD Workflow, Release Process, Adding a New Plugin) against the actual workflow YAML files (`.github/workflows/pr-checks.yml`, `.github/workflows/release.yml`) and `release-please-config.json` to verify accuracy before finalizing; the fifth section (Recovery & Rollback Procedures) is authored in Phase 6 (T023) and is verified separately by T024 (FR-011)

**Checkpoint**: Four Phase 5 CI/CD sections are appended to CLAUDE.md (the fifth Recovery section is added in Phase 6). Content is accurate per FR-011. A new contributor reading only CLAUDE.md will understand the complete workflow once all five sections are present (SC-005).

---

## Phase 6: User Story 5 — Recovery & Rollback Procedures (Priority: P4)

**Goal**: Append `## Recovery & Rollback Procedures` section to `CLAUDE.md` with specific, copy-pasteable `gh` commands for all recovery scenarios required by FR-010 and its supplements. Commands must require only `<owner>/<repo>` substitution (FR-010, SC-006).

**Independent Test**: Read the recovery section and confirm all six scenarios are present: (1) `gh workflow run release.yml` for marketplace sync re-trigger, (2) `Release-As: X.Y.Z` commit footer with monorepo scoping example (commit must touch component files), (3) `fix:` commit for patching forward after a bad release, (4) `enforce_admins` drift recovery (detection + re-run Stage 1), (5) `permissions: contents: write` missing from release.yml recovery, (6) no-releasable-commits recovery (empty `fix:` commit) and stale `marketplace.json` recovery (re-trigger + manual fallback).

**Dependency**: T018–T022 should be complete (or in progress) to ensure the section appends correctly after the four preceding new sections.

- [ ] T023 [US5] Append `## Recovery & Rollback Procedures` section to `CLAUDE.md` with all required recovery procedures: (1) re-trigger marketplace sync: `gh workflow run release.yml --repo <owner>/<repo>`; (2) force a specific version: `Release-As: X.Y.Z` git commit footer with monorepo scoping note (commit must touch a file under the target plugin directory, e.g. `speckit-pro/.claude-plugin/plugin.json`); (3) patch-forward bad release: `fix(<plugin>): <description>` commit example; (4) `enforce_admins` drift recovery: detection via `gh api .../branches/main/protection --jq '.enforce_admins.enabled'` — if `true`, re-run Stage 1 setup command from the verification checklist; (5) `permissions: contents: write` missing from release.yml: detection via `gh api .../contents/.github/workflows/release.yml --jq '.content' | base64 -d | grep -A3 'permissions'`, recovery by restoring the permissions block via a `fix:` commit; (6) no-releasable-commits: push `git commit --allow-empty -m "fix: trigger release for <plugin>"` to produce a releasable commit; and stale `marketplace.json`: re-trigger via `gh workflow run release.yml`, or as last resort manually push `chore: sync marketplace.json versions [skip ci]` commit (FR-010, FR-010 supplements, FR-004 supplement, SC-006)
- [ ] T024 [US5] Verify the Recovery & Rollback section is accurate against actual release-please v4 behavior: confirm `gh workflow run` targets the correct workflow filename (`release.yml` — the actual filename in `.github/workflows/`; not `release-please.yml`), confirm `Release-As:` footer syntax is correct for release-please v4 monorepo configuration, confirm `fix:` bump semantics are correct (FR-011)

**Checkpoint**: Recovery section is appended to CLAUDE.md with accurate, copy-pasteable commands. SC-006 (resolution in under 15 minutes without external docs) is achievable from this section alone.

---

## Phase 7: Validation (Cross-Cutting)

**Purpose**: Confirm all implementations are correct, existing tests still pass, and documentation is accurate. These tasks validate across all user stories.

- [ ] T025 Run full existing test suite to confirm no regressions: `bash speckit-pro/tests/run-all.sh` from the worktree root — all 369 tests must pass (FR-012)
- [ ] T026 [P] Verify CLAUDE.md has exactly five new sections appended and no existing section content was modified: confirm headings `## Contributing & Branching Strategy`, `## CI/CD Workflow`, `## Release Process`, `## Adding a New Plugin to Release Automation`, `## Recovery & Rollback Procedures` all appear in the file (FR-009, FR-012)
- [ ] T027 [P] Verify the verification checklist at `docs/ai/specs/cicd-release-pipeline-verification.md` exists and contains all 8 required stage headings (FR-007)
- [ ] T028 [P] Verify branch protection is applied as expected: `gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection | jq '{contexts: .required_status_checks.contexts, enforce_admins: .enforce_admins.enabled}'` — confirm both `validate-plugins` and `validate-pr-title` are present and `enforce_admins` is `false` (FR-001, FR-004)
- [ ] T029 [P] Verify repository merge settings are squash-only: `gh api /repos/racecraft-lab/racecraft-plugins-public | jq '{squash: .allow_squash_merge, merge_commit: .allow_merge_commit, rebase: .allow_rebase_merge}'` — expected: `{"squash": true, "merge_commit": false, "rebase": false}` (FR-002)
- [ ] T030 [P] Confirm that `.github/workflows/pr-checks.yml` is the ONLY existing file modified in this feature branch (excluding newly created docs) by running `git diff --name-only main` and verifying only `pr-checks.yml`, `CLAUDE.md`, and `docs/ai/specs/cicd-release-pipeline-verification.md` appear (no plugin code or test files modified) (FR-012)

**Checkpoint**: All 369 existing tests pass. Branch protection is confirmed active. Documentation is complete and accurate.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately. T001 (sentinel job) MUST be merged to `main` before Phase 2 can execute.
- **Phase 2 (US1 — Branch Protection)**: Depends on T001 being merged to `main`. Blocks: nothing directly, but should be done early for full enforcement.
- **Phase 3 (US2 — Copilot)**: No dependencies — can run in parallel with all other phases.
- **Phase 4 (US3 — Verification Checklist)**: No dependencies — can be authored in parallel. Should incorporate the exact `gh api` commands from quickstart.md.
- **Phase 5 (US4 — CLAUDE.md CI/CD)**: No dependencies — can be authored in parallel with Phases 3 and 4.
- **Phase 6 (US5 — Recovery Procedures)**: Depends on T018–T022 being drafted (same file, appending after them). Can start after T018 is complete.
- **Phase 7 (Validation)**: Depends on all prior phases complete.

### User Story Dependencies

| Story | Depends On | Can Parallelize With |
|-------|-----------|---------------------|
| US1 — Branch Protection | T001 merged | US2, US3, US4, US5 authoring |
| US2 — Copilot (UI) | None | All phases |
| US3 — Verification Checklist | None (authoring) | US2, US4, US5 |
| US4 — CLAUDE.md CI/CD | None (authoring) | US2, US3 |
| US5 — Recovery Procedures | T018 complete (same file) | US2, US3 |

### Dependency Ordering Summary

```
T001 (sentinel job) → PR open → PR merged to main
  └→ T002 (YAML validate) [parallel]
  └→ T003 (run tests) [parallel]

After T001 merged:
  T004 (repo merge settings) → T005 (branch protection) → T006 (verify)

Parallel with Phase 1+2:
  T007, T008 (Copilot UI — independent)
  T009–T016 (checklist stages — independent, all parallel within phase)
  T017 (add gh commands to checklist — after T009)
  T018–T021 (CLAUDE.md sections — independent, all parallel)
  T022 (cross-reference check — after T018–T021)
  T023 (recovery section — after T021)
  T024 (verify recovery accuracy — after T023)

After all above:
  T025–T030 (validation tasks — parallel where marked)
```

---

## Parallel Execution Examples

### Phase 1 — Sentinel Job

```
T001: Add validate-plugins sentinel job to .github/workflows/pr-checks.yml
  ├─ [P] T002: Validate YAML syntax
  └─ [P] T003: Run existing tests
```

### Phases 3–6 — Can All Run in Parallel (After T001 is underway)

```
Thread A: T004 → T005 → T006  (Branch protection — needs T001 merged)
Thread B: T007, T008           (Copilot UI — fully independent)
Thread C: T009–T017            (Verification checklist — fully independent)
Thread D: T018–T022            (CLAUDE.md CI/CD sections — fully independent)
Thread E: T023, T024           (Recovery section — after T021)
```

### Phase 7 — All Validation Tasks Parallel

```
T025: Run tests  (sequential, verifies all tests pass)
  ├─ [P] T026: Verify CLAUDE.md sections
  ├─ [P] T027: Verify verification checklist
  ├─ [P] T028: Verify branch protection via gh api
  ├─ [P] T029: Verify merge settings via gh api
  └─ [P] T030: Confirm only allowed files modified
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Add sentinel job, run tests, open PR, merge to `main`
2. Execute Phase 2: Apply branch protection via `gh api`
3. Verify T006: Confirm branch protection is live
4. **STOP and VALIDATE**: Try to merge a test PR with a failing check — confirm it is blocked
5. Squash-only enforcement is now active

### Incremental Delivery

1. Phase 1 (sentinel job) → merge to `main` → branch protection is configurable
2. Phase 2 (branch protection) → CI gates are enforced
3. Phase 3 (Copilot) → advisory review is active
4. Phase 4 (verification checklist) → operational runbook exists
5. Phase 5 (CLAUDE.md) → contributor documentation is complete
6. Phase 6 (recovery procedures) → edge-case response is documented
7. Phase 7 (validation) → full regression and accuracy confirmed

### Single-Developer Recommended Order

Given this is a solo-maintainer spec, the recommended sequence is:

1. T001 → T002 → T003 → open PR → merge (sentinel job must land in `main` first)
2. T004 → T005 → T006 (apply and verify branch protection)
3. T007 → T008 (Copilot UI — takes 5 minutes)
4. T009–T017 (verification checklist — write all stages)
5. T018–T022 (CLAUDE.md CI/CD sections — write all four sections, cross-reference)
6. T023 → T024 (recovery procedures — write and verify)
7. T025–T030 (run all validation tasks)

---

## Notes

- No test tasks are included — FR-012 explicitly prohibits new test files; existing test suite at `bash speckit-pro/tests/run-all.sh` (369/369) must remain passing
- [P] tasks operate on different files or independent GitHub UI actions — no write conflicts
- The sentinel job (T001) is the only code change to an existing source file; all other tasks are `gh api` commands, UI actions, or new document creation
- Branch protection cannot require a check that has not yet run — T001 must be merged before T005 can register `validate-plugins` as a required check
- Copilot review (T007) is entirely independent of branch protection (T004–T006) — they share no configuration
- FR-005 requires the `gh api` commands to be documented in the verification checklist (T017) as the Infrastructure-as-Code record — no separate script file is needed
- All recovery commands in T023 require only `<owner>/<repo>` substitution and match the actual workflow filenames in `.github/workflows/`

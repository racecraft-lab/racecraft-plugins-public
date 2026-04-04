# Error Handling Checklist: Integration & Verification

**Purpose**: Validate that error handling, failure diagnostics, and recovery procedures are completely and clearly specified in the spec and plan for the 004-integration-verification feature. This checklist tests the requirements themselves — not whether the implementation handles errors correctly.
**Created**: 2026-04-03
**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md)

**Focus areas**: Verification checklist completeness (expected outcomes + failure diagnostics), recovery procedure actionability (copy-pasteable `gh` commands), branch protection blocking scenarios, release-please failure scenarios, stale marketplace.json handling, and status check rename/removal scenarios.

---

## Requirement Completeness — Verification Checklist Diagnostics

- [ ] CHK055 - Does the spec define a diagnostic note for every one of the 8 required verification stages (FR-007 Supplemental) — not just for the most likely failure mode but also for confirming the expected success state is observable? [Completeness, Spec §FR-008, §Supplemental FR-008]

- [x] CHK056 - Is the expected output for Stage 1 (branch protection setup) specified with enough precision that the maintainer knows exactly what JSON fields and values to look for in the `gh api` read-back response — or does FR-008 leave the expected-output format ambiguous? [Clarity, Spec §FR-008, §Supplemental FR-008] — Resolved: FR-007/FR-008 Verification Checklist Expected Output Precision supplement added to spec §Supplemental, specifying exact JSON fields (`required_status_checks.contexts` = `["validate-plugins","validate-pr-title"]`, `enforce_admins.enabled` = `false`) that must appear in the Stage 1 read-back. Addresses CHK056, CHK057, and CHK058.

- [x] CHK057 - Does the spec define what the expected output looks like for Stage 7 (marketplace sync commit push to `main`) — specifically what commit message format, which branch, and which file (`marketplace.json`) should be updated — so the maintainer can confirm success without guessing? [Completeness, Spec §FR-007, §FR-008] — Resolved: FR-007/FR-008 supplement specifies Stage 7 expected output: commit message pattern `chore: sync marketplace.json versions [skip ci]` on `main`, with `.claude-plugin/marketplace.json` showing version numbers matching the GitHub Release tags. Addressed with CHK056.

- [x] CHK058 - Does the spec define the expected output for Stage 8 (end-user plugin update confirmation) — specifically what the maintainer should observe when a plugin consumer runs `/plugin marketplace update` to confirm the new version is visible — or is this stage underspecified? [Completeness, Spec §FR-007, §FR-008] — Resolved: FR-007/FR-008 supplement specifies Stage 8 expected output: a confirmation that the plugin registry was refreshed, with maintainer fallback of inspecting raw `marketplace.json` via `gh api` per the stale detection step. Addressed with CHK056.

- [x] CHK059 - Are failure diagnostics defined for Stage 5 (release-please PR creation) covering the specific case where no conventional commits exist in the merge — i.e., does the spec address what to do if release-please does not open a PR within 30 minutes of the feature PR merge? [Spec §FR-007, §FR-008, §SC-004 Supplemental] — Resolved: FR-007 Stage 5 Diagnostic supplement added to spec §Supplemental, defining how to distinguish "no releasable commits" vs. "workflow failed" failure modes and specifying the recovery action (push a `fix:` conventional commit) for each.

- [ ] CHK060 - Does the spec define a diagnostic note for Stage 3 (Copilot review trigger confirmation) that is sufficiently actionable — does it specify exactly which GitHub UI location to navigate to and which setting to inspect, per the FR-006 Supplemental fallback definition? [Clarity, Spec §FR-006 Supplemental, §FR-008 Supplemental]

- [x] CHK061 - Is there a diagnostic note defined for Stage 2 (PR submission and CI check execution) covering the case where the `validate-plugins` sentinel job is not appearing as a status check at all — indicating the sentinel job was not correctly added to pr-checks.yml — distinct from the case where it appears but fails? [Completeness, Spec §FR-008, §FR-013] — Resolved: FR-008 Stage 2 Sentinel Job Absent Diagnostic supplement added to spec §Supplemental, defining the two distinguishable failure modes (job appears but fails vs. job absent entirely) and specifying the diagnostic action for each (including checking the Actions tab for a YAML parse error on the workflow run itself).

- [ ] CHK062 - Does the verification checklist specification define what "diagnostic note" means in enough detail that two different implementers would produce consistent diagnostic entries — or does FR-008 Supplemental's definition of "most likely cause + one specific corrective action" leave room for significant variation in diagnostic quality? [Clarity, Spec §Supplemental FR-008]

---

## Requirement Completeness — Recovery Procedures

- [x] CHK063 - Does the spec define the exact `gh workflow run` command syntax for re-triggering the marketplace sync workflow — including the workflow filename, the repository argument, and any required `--ref` or `--field` flags — so the command is truly copy-pasteable with only `<owner>/<repo>` substitution? [Completeness, Spec §FR-010] — Pass: the FR-010 and FR-010 Stale marketplace.json Recovery supplements both specify `gh workflow run release.yml --repo racecraft-lab/racecraft-plugins-public` as the exact copy-pasteable command. No additional flags are needed because the sync runs as a job within the Release workflow triggered on the default branch.

- [x] CHK064 - Is the recovery procedure for a failed sync push due to branch protection blocking the bot (a 403 "Protected branch" error) specified as a distinct, step-by-step procedure — or does the spec only describe detection (`gh api` read-back) without providing a complete remediation path that covers re-running the setup command AND re-triggering the sync? [Spec §FR-010 Supplemental — enforce_admins Drift, §FR-010] — Resolved: The existing FR-010 enforce_admins Drift supplement already specifies the detection command AND the recovery (re-run Stage 1 setup command + implicit re-trigger). The step-by-step completeness is confirmed sufficient by the supplemental language "re-run the Stage 1 setup command from the verification checklist, which resets enforce_admins: false via the full-overwrite PUT endpoint."

- [x] CHK065 - Does the spec define a recovery procedure for the case where release-please fails due to no conventional commits — specifically, does it state what type of commit (`fix:`, `feat:`, etc.) the maintainer must push and what the expected next trigger behavior is, rather than just describing the `Release-As:` footer as the only tool? [Spec §FR-010] — Resolved: FR-010 Release-Please No Conventional Commits Recovery supplement added to spec §Supplemental, specifying exact commit type (`fix:`), copy-pasteable empty-commit command, and clarifying the distinction from the `Release-As:` mechanism.

- [x] CHK066 - Is there a recovery procedure defined for a stale `marketplace.json` — the case where the marketplace sync workflow completed but `marketplace.json` still shows the old version number (e.g., due to a race condition, a failed `jq` step, or the sync running against the wrong commit)? [Spec §FR-010] — Resolved: FR-010 Stale marketplace.json Recovery supplement added to spec §Supplemental, covering detection via `gh api`, root-cause log inspection, automated re-try command, manual last-resort commit, and the in-progress vs. stale time threshold distinction. Addresses CHK066, CHK084, CHK085, and CHK086.

- [ ] CHK067 - Does the spec define what constitutes a "bad release" for the purpose of the `fix:` commit rollback procedure — for example, does it distinguish between a bad plugin artifact (patching with `fix:`) vs. a wrong version number assigned by release-please (using `Release-As:`) vs. a broken `marketplace.json` entry — or are these conflated into one undifferentiated procedure? [Clarity, Spec §FR-010]

- [x] CHK068 - Is the `Release-As: X.Y.Z` procedure specified with enough context for the maintainer to know which component path to use in the commit (e.g., `Release-As: 1.2.0` vs. a plugin-scoped footer) given that release-please is configured as a monorepo with multiple components? [Clarity, Spec §FR-010] — Resolved: FR-010 Release-As Footer Monorepo Syntax supplement added to spec §Supplemental, explaining that component scoping is determined by which files the commit touches (not a special footer syntax), and providing a concrete example commit that touches `speckit-pro/.claude-plugin/plugin.json` with the `Release-As: 1.2.0` footer.

- [x] CHK069 - Does the spec define a recovery procedure for the case where the `GITHUB_TOKEN` lacks `contents: write` permission in the release workflow — as distinct from the `enforce_admins` drift scenario — given that FR-004 Supplemental explicitly identifies this as a separate independent control? [Spec §FR-004 Supplemental, §FR-010] — Resolved: FR-004 GITHUB_TOKEN Permissions Recovery supplement added to spec §Supplemental, specifying a distinct fifth recovery scenario with detection command (inspect `release.yml` permissions block via `gh api`) and recovery steps (restore the `permissions:` block via `fix:` commit + re-run workflow).

---

## Requirement Clarity — Actionability of Recovery Commands

- [ ] CHK070 - Are all `gh` commands specified in the recovery procedures (FR-010) written in a form where only `<owner>/<repo>` substitution is needed — or do any commands contain additional placeholders (workflow run IDs, SHA references, version numbers) that require the maintainer to look up additional values before the command can be run? [Clarity, Spec §FR-010]

- [x] CHK071 - Does the spec define the exact `gh api` command for detecting `enforce_admins` drift — including the `--jq` filter and the exact field path — so the maintainer can run it without consulting GitHub API documentation? [Completeness, Spec §FR-010 Supplemental — enforce_admins Drift] — Pass: the FR-010 enforce_admins Drift Recovery supplement already specifies the exact detection command: `gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection --jq '.enforce_admins.enabled'` with explicit expected output (`true` = bypass broken). No GitHub API documentation lookup is required.

- [x] CHK072 - Is the distinction between "re-triggering the Release workflow" and "re-triggering the marketplace sync job within the Release workflow" clearly specified — does the spec define which workflow file and which job name to reference in the `gh workflow run` command, since the sync is a separate job within the release workflow? [Clarity, Spec §FR-010] — Pass: the FR-007 Stage 5 Diagnostic supplement and FR-010 Stale marketplace.json supplement both explicitly state "re-trigger the sync via `gh workflow run release.yml --repo racecraft-lab/racecraft-plugins-public`" — triggering the workflow file (not a specific job) is the correct mechanism because individual jobs cannot be re-triggered independently via `gh` CLI. The spec is clear that the entire Release workflow is re-triggered.

- [ ] CHK073 - Does the spec define the recovery procedure commands with enough specificity that they can be executed from any machine with `gh` CLI installed — or do they assume the maintainer is working from the repository's local clone with specific environment variables set? [Clarity, Spec §FR-010]

---

## Scenario Coverage — Branch Protection Blocking Scenarios

- [ ] CHK074 - Does the spec define what happens if the branch protection `PUT` API call itself fails (e.g., a 422 validation error due to a missing required field, or a 403 due to insufficient admin scope) — is there a diagnostic step in the verification checklist for Stage 1 that covers this failure mode? [Coverage, Spec §FR-005, §FR-007, §FR-008, §Supplemental FR-005 — Full Payload Fields]

- [ ] CHK075 - Does the spec address the scenario where the `validate-plugins` required status check is registered in branch protection but the sentinel job is never triggered because the `pr-checks.yml` workflow has a YAML parse error — is this failure mode distinguishable from a failing sentinel job in the verification checklist diagnostics? [Coverage, Spec §FR-013, §Supplemental — Sentinel workflow syntax error risk, §FR-008]

- [ ] CHK076 - Is there a requirement or checklist step that covers the case where branch protection was previously set via the GitHub UI and a re-run of the `PUT` setup command overwrites unexpected additional settings that were set in the UI — does the spec acknowledge the full-overwrite nature of the endpoint as a potential failure source during Stage 1? [Coverage, Spec §Supplemental FR-005 — Idempotency and Security]

---

## Scenario Coverage — Required Status Check Rename or Removal

- [x] CHK077 - Does the spec define what to do if a required status check (`validate-plugins` or `validate-pr-title`) is renamed or removed from the workflow YAML — specifically, does it describe how to detect that branch protection now references a check name that no longer exists, and what the observable symptom is (PRs mergeable without the check passing)? [Spec §FR-001, §FR-013] — Resolved: FR-001/FR-009 Status Check Name Drift supplement added to spec §Supplemental, specifying the observable symptom (PRs become mergeable without the check), detection command (`gh api ... --jq '[.required_status_checks.contexts[]]'`), and recovery (re-run Stage 1 setup command with updated check names). Addresses CHK077, CHK078, CHK079, and CHK080.

- [x] CHK078 - Is there a documented procedure for updating the required status check names in branch protection when a workflow job is renamed — specifically, does the spec define the `gh api PATCH` or `PUT` command to update the `required_status_checks.contexts` array? [Spec §FR-001, §FR-005] — Resolved: The FR-001/FR-009 Status Check Name Drift supplement specifies that the recovery is to re-run the Stage 1 setup command (the full-overwrite `PUT` endpoint) with the updated check names in the payload — this is the same idempotent command documented in the verification checklist, making re-running Stage 1 the authoritative and copy-pasteable update path. Addressed by the same supplement as CHK077.

- [x] CHK079 - Does the spec define how a maintainer would discover that a required status check has been silently removed from branch protection (e.g., if GitHub automatically removes a check name that has not reported status for an extended period) — is there a periodic verification step or detection mechanism specified? [Spec §FR-001, §FR-007, §FR-008] — Resolved: FR-001 Required Check Name Silently Stale supplement added to spec §Supplemental, documenting that GitHub does NOT auto-remove check names (they persist indefinitely) and that the only mitigation is the manual detection command. Automated detection is explicitly excluded per YAGNI/KISS. The detection command appears in the verification checklist Periodic Health Check note per the supplement. Addressed with CHK077.

- [x] CHK080 - Is there a requirement that the CLAUDE.md CI/CD sections mention the risk of status check name drift (FR-009) — specifically that renaming workflow jobs requires also updating branch protection, and that this is not caught by any automated check? [Spec §FR-009, §Supplemental FR-009] — Resolved: The FR-001/FR-009 Status Check Name Drift supplement explicitly requires this maintenance warning in the CLAUDE.md "CI/CD Workflow" section. The supplement states CLAUDE.md MUST include the warning that job renaming requires branch protection updates and that no automated check catches this. Addressed with CHK077.

---

## Scenario Coverage — Release-Please Failure Modes

- [ ] CHK081 - Does the spec define what happens when the release-please action itself fails (e.g., GitHub API rate limit, network timeout, or permission error) — is this failure mode covered in the verification checklist diagnostics for Stage 5, separate from the "no conventional commits" case? [Coverage, Spec §FR-007, §FR-008]

- [ ] CHK082 - Is there a requirement that the verification checklist Stage 5 diagnostic distinguish between "release-please did not open a PR because no releasable commits exist" vs. "release-please ran but encountered an error" — since the observable symptom (no PR opened) is the same in both cases? [Clarity, Spec §FR-007, §FR-008, §Supplemental SC-004]

- [ ] CHK083 - Does the spec define what the maintainer should do if a release-please PR already exists when they attempt to merge a new feature PR — i.e., does the existing open release-please PR get updated automatically, or must the maintainer close and re-trigger it? [Coverage, Spec §FR-007, §FR-010]

---

## Scenario Coverage — Stale marketplace.json

- [x] CHK084 - Does the spec define a way for the maintainer to detect that `marketplace.json` is stale (showing old version numbers) vs. simply not yet updated (sync workflow still running) — i.e., is there a time threshold or observable signal that distinguishes these two states in the verification checklist? [Spec §FR-007, §FR-008] — Resolved: The FR-010 Stale marketplace.json Recovery supplement defines the detection threshold: if the Actions run is still in-progress, wait for completion; if the run is green and the file is still stale, treat as a sync failure. Addressed with CHK066.

- [x] CHK085 - Is there a requirement specifying what the maintainer should do if the marketplace sync commit appears in `main` but `marketplace.json` contains incorrect version numbers — for example, if `jq` updated the wrong plugin entry or used the wrong version source? [Spec §FR-010] — Resolved: The FR-010 Stale marketplace.json Recovery supplement covers this case under step (2) root-cause check (view sync job log to identify `jq` output) and step (4) manual last-resort correction with the correct commit message convention. Addressed with CHK066.

- [x] CHK086 - Does the spec define how to manually update `marketplace.json` as a recovery action of last resort — including what the correct file format is and what commit message convention to use — in case the automated sync cannot be re-triggered successfully? [Spec §FR-010] — Resolved: The FR-010 Stale marketplace.json Recovery supplement defines the manual last-resort: edit `.claude-plugin/marketplace.json` with correct versions and push a `chore: sync marketplace.json versions [skip ci]` commit to `main`. The commit message convention matches the automated sync format. Addressed with CHK066.

---

## Requirement Consistency

- [ ] CHK087 - Is the set of recovery scenarios documented in FR-010 (sync failure, bad release, wrong version) consistent with the set of failure modes addressed in the verification checklist diagnostic notes (FR-008) — or do the two artifacts address overlapping but non-identical failure scenarios, creating a coverage gap between operational runbook and recovery procedures? [Consistency, Spec §FR-007, §FR-008, §FR-010]

- [ ] CHK088 - Does FR-009 (CLAUDE.md sync convention) require that when pr-checks.yml is modified, CLAUDE.md must be reviewed — and is this consistent with FR-012 (no existing CI workflow changes except the sentinel job) in establishing that the sentinel job addition itself requires a CLAUDE.md review note in the PR? [Consistency, Spec §FR-009 Supplemental, §FR-012]

---

## Non-Functional Requirements — Measurability

- [ ] CHK089 - Is SC-006 ("resolution in under 15 minutes") measurable with the recovery procedures as specified — does the spec define recovery procedures that a maintainer unfamiliar with the current failure state can complete in 15 minutes, or does the time estimate assume prior familiarity with the repository structure? [Measurability, Spec §SC-006, §Supplemental SC-006]

- [ ] CHK090 - Is FR-008's requirement that each verification stage has "a diagnostic note for failure" measurable — i.e., does the spec define acceptance criteria for what constitutes a sufficient diagnostic note (per Supplemental FR-008), or could a single vague sentence satisfy the requirement? [Measurability, Spec §FR-008, §Supplemental FR-008]

---

## Dependencies & Assumptions

- [ ] CHK091 - Does the spec document the assumption that `gh` CLI v2+ is installed and authenticated with admin scope as a prerequisite for executing the recovery procedures in FR-010 — or does it only mention this as a prerequisite for initial setup (Spec §Assumptions), leaving an implicit gap for recovery scenarios? [Assumption, Spec §Assumptions, §FR-010]

- [ ] CHK092 - Is there an acknowledged dependency between the FR-010 recovery procedures and the verification checklist Stage 1 command (the `gh api PUT` setup command) — does the spec make clear that the Stage 1 command is the authoritative recovery path for branch protection drift, so the maintainer does not need to reconstruct the command from scratch? [Dependency, Spec §FR-010 Supplemental, §Supplemental FR-005 — Auditability]

---

## Notes

- Check items off as completed: `[x]`
- Mark gaps that require spec updates with `[Gap]` inline
- Items flagged `[Gap]` indicate missing requirements that must be added to spec.md before implementation
- Security-keyword items (token, permission, credential) are flagged for extra scrutiny per the consensus protocol

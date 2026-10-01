---
name: speckit-archive-cleanup
<!-- host:claude: Claude reads a trigger-phrase description and Claude-only frontmatter keys -->
description: "Archive a merged SpecKit spec and clean active workflow residue after the implementation PR has merged. Use after confirming merge provenance, when the user asks for post-merge SpecKit archive hygiene, cleanup hygiene, or removal of completed specs from active specs. Only for SpecKit spec archives: do NOT use for generic git housekeeping such as pruning merged branches, deleting stale worktrees, git gc, or clearing build output, and not to scaffold a spec (use speckit-scaffold-spec), run a workflow (use speckit-autopilot), read status (use speckit-status), or fix PR review comments (use speckit-resolve-pr)."
argument-hint: "SPEC-ID and optional merged PR URL or number"
user-invocable: true
allowed-tools: Read Edit Write Grep Agent
license: MIT
<!-- /host -->
<!-- host:codex: Codex keeps its own selection description -->
description: >
  Archive a merged SpecKit spec, remove completed active specs, refresh
  roadmap and project-memory state, and prepare the cleanup PR after merge.
  Only for SpecKit spec archives after the implementation PR has merged.
  Do not use for generic git housekeeping such as pruning merged branches,
  deleting stale worktrees, git gc, or clearing build output, and not for
  scaffolding, autopilot, status, or PR review work.
<!-- /host -->
---

# SpecKit Archive Cleanup

Use this skill after a SpecKit implementation PR has merged and the repository
still contains active workflow or `specs/**` residue for that completed work.
The goal is to preserve recovery evidence in project memory, remove only the
completed active spec folder, refresh generated SpecKit indexes, and leave the
roadmap ready for the next SPEC.

This is a mutation-heavy archive workflow. Do not use it for normal status
checks, scaffold setup, autopilot implementation, or read-only PR review. If
merge status is unknown, first verify it. If the PR has not merged, stop and
report that archive cleanup is premature, unless the user explicitly asks for
an abandoned-spec cleanup and the repository has an established convention for
that case.

## Inputs

Accept a SPEC-ID such as `SPEC-007` or `SPEC-014`, an active spec directory, a
workflow file path, or a merged PR URL/number. If more than one is provided,
cross-check that they all point to the same completed work. Do not archive
based on a SPEC-ID alone when the merge source is ambiguous. Derive the
repository from local `git remote` output when only a PR number is supplied.

Required facts before editing:

- merged PR URL, number, title, merge timestamp, and merge commit
- active spec directory under `specs/`
- workflow file under `docs/ai/specs/.process/`, if present
- current roadmap and traceability files affected by the spec family
- installed archive extension contract, if `.specify/extensions/archive/` exists

## Ground Truth Checks

Start from live repository truth:

1. Inspect `git status --short --branch`.
2. Confirm the current branch is a cleanup branch based on the current mainline,
   or create one before editing.
<!-- host:claude: Claude has no host branch prefix -->
   Use the local branch naming convention.
<!-- /host -->
<!-- host:codex: Codex sessions name their branches with a codex/ prefix -->
   Use the local branch naming convention, normally a `codex/` branch.
<!-- /host -->
3. Confirm the PR is merged with GitHub tooling or the best available local
   merge evidence, and capture the required facts above.
4. Read the archive extension command contract if
   `.specify/extensions/archive/commands/archive.md` exists.
5. Read the existing newest archive reports in `.specify/memory/archive-reports/`
   to match local conventions.
6. Check whether `.specify/feature.json` exists. If it is absent, do not create
   it. If it exists and points at the completed spec, remove or rewrite it only
   according to repository convention.
7. List active specs with `find specs -mindepth 1 -maxdepth 4 -print` and
   identify the exact folder that belongs to the merged spec.

Do not remove any active spec folder until merge provenance and recovery
commands are recorded. SpecKit Pro keeps process files under
`docs/ai/specs/.process/` as historical evidence; remove them only when
repository history shows that process evidence is intentionally deleted for
completed specs.

## Archive Procedure

Treat the archive extension command contract, when present, as the local policy
for source directories, memory files, cleanup eligibility, and extension hooks,
with one override: SpecKit Pro replaces the contract's agent-context step (stock
`stn1slv/spec-kit-archive` step 5.3, vendored fork step 6.3) with step 3 below.
If you also run the archive command alongside step 2, scope it so it cannot
reach that step:

```text
<!-- host:claude: Claude names the SpecKit archive skill with a slash -->
/speckit-archive-run specs/<merged-spec-dir> --spec-only --plan-only --changelog-only
<!-- /host -->
<!-- host:codex: Codex follows the archive command contract without a slash command -->
archive command: specs/<merged-spec-dir> --spec-only --plan-only --changelog-only
<!-- /host -->
```

Several scope modifiers form a union, so this run updates
`.specify/memory/spec.md`, `plan.md`, and `changelog.md` and leaves the agent
context files alone.

Then update the project state in this order:

1. Add an archive report under `.specify/memory/archive-reports/` named with the
   current date and SPEC-ID, for example
   `2026-06-17-spec-007-post-merge-hygiene.md`. Include PR URL and title, merge
   commit, merged-at timestamp, source spec path, workflow file and the process
   files preserved, canonical shipped artifacts, cleanup branch, cleanup
   command, verification commands, and exact recovery commands using `git show`
   or `git checkout` against the merge commit.
2. Append concise records to `.specify/memory/spec.md`,
   `.specify/memory/plan.md`, and `.specify/memory/changelog.md`. These records
   should summarize what shipped, where canonical artifacts live now, why the
   active spec folder can be removed, and where the detailed archive report is.
3. Update roadmap, traceability, agent context (`AGENTS.md`, `CLAUDE.md`,
   `GEMINI.md`), or MOC files ONLY to remove or correct references that still
   describe the merged spec as pending, in progress, or blocking downstream
   work. Move a downstream spec from blocked to ready only when the completed
   spec was its actual blocker, and name the merged PR and the canonical files
   that now satisfy the dependency. Never append per-spec history entries
   (archive notes, Active Technologies bullets, or Recent Changes bullets) to
   agent context files. The archive report and `.specify/memory/` records are
   the system of record for history, and agent context files must stay small
   (Codex reads AGENTS.md under a 32 KiB budget).
4. Update `docs/ai/specs/.process/autopilot-state.json` only if it exists and
   still points at the completed spec. Keep it valid JSON: set `status` to
   `completed_archived`, the only archived value in the run-status schema
   (`skills/speckit-autopilot/contracts/autopilot-state-status.schema.json`),
   set `active_step` to `null`, record the archive sweep as applied, and
   preserve the project command names from the previous state.
5. Remove the completed active spec directory under `specs/`. Keep
   `specs/.gitkeep`. Do not delete unrelated active specs, fixture specs, or
   process files. If live tests or scripts still reference the spec folder,
   decouple those references first or stop and report the blocker.
6. Regenerate the active spec index with SpecKit Pro's runner helpers, so the
   generated MOC or index no longer points at the archived spec directory.
   Send each request as one JSON object on stdin to
   `resolved_python -m speckit_pro_runner`, run from the repository root. Run
   runner helper `generate-spec-index-write` in `apply` mode first:
   ```json
   {"schema_version":"1.0","request_id":"archive-cleanup-spec-index-write","helper_id":"generate-spec-index-write","operation":"generate-spec-index-write","mode":"apply","inputs":{"repo_root":"."}}
   ```
   Then run runner helper `generate-spec-index-check`. A `validation_failure`
   result means the index is still stale; do not commit until it passes:
   ```json
   {"schema_version":"1.0","request_id":"archive-cleanup-spec-index-check","helper_id":"generate-spec-index-check","operation":"generate-spec-index-check","mode":"read_only","inputs":{"repo_root":"."}}
   ```

Prefer local helper scripts over hand-maintaining generated files. If the repo
has docs-site generated reference pages or generated plugin payloads affected by
the cleanup, run the relevant generators and include those generated changes.

## Safe Parallelism

These parts are safe to do in parallel:

- read-only discovery such as `git status`, `gh pr view`, `find specs`, and
  reading roadmap, memory, and workflow files
- inspecting multiple archive reports
- running independent read-only searches for stale SPEC-ID mentions

These parts must be serialized:

- edits to roadmap, traceability, memory, MOC, and autopilot-state files
- active spec directory removal
- generated index and generated docs updates
- staging, committing, pushing, and PR creation

The serialized files all represent one shared project state. Parallel edits
make it easy to leave contradictory status such as "archived" in memory but
"in progress" in a roadmap.

## Verification

Run the smallest checks that prove the cleanup, then the standard project
checks if plugin or generated payload files changed. Typical checks:

- a `find specs -mindepth 1 -maxdepth 4 -print` audit showing only expected
  active specs and `specs/.gitkeep`
- `resolved_python -m json.tool docs/ai/specs/.process/autopilot-state.json`
  when that file changed
- `generate-spec-index-write` in `apply` mode, then `generate-spec-index-check`
- docs-site reference generation/checks when reference pages changed
- payload builder and payload parity checks when plugin source changed
- `git diff --check`
- repository structural validation suite

If a check cannot run (missing dependencies, sandboxing, or network access),
retry only when the environment policy allows it; otherwise report the exact
command and the reason. Do not claim the archive is fully verified when
generated files or structural checks are stale.

## Git And PR Titles

Commit intentionally after verification. For archive-only cleanup commits and
PRs, use a lower-case Conventional Commit scope derived from the completed spec
ID. For example, archive cleanup for `SPEC-001` should use
`docs(spec-001): archive post-merge state`, not
`docs(SPEC-001): archive post-merge state`. The repository PR title gate checks
the final PR title, so apply the same lower-case scope to `gh pr create` or
`gh pr edit --title`.

## Final Report

Report:

- the merged PR and merge commit used as provenance
- the active spec folder removed
- archive report path
- roadmap or traceability status changes
- generated files refreshed
- verification commands and results
- remaining risks, especially skipped browser UAT or skipped CI checks

Keep the report short and make the next action explicit, usually review the
cleanup PR or merge it after CI passes.

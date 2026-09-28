---
name: speckit-archive-cleanup
description: >
  Archive a merged SpecKit spec, remove completed active specs, refresh
  roadmap and project-memory state, and prepare the cleanup PR after merge.
  Only for SpecKit spec archives after the implementation PR has merged.
  Do not use for generic git housekeeping such as pruning merged branches,
  deleting stale worktrees, git gc, or clearing build output, and not for
  scaffolding, autopilot, status, or PR review work.
---

# SpecKit Archive Cleanup

## Scope

Use this skill after a SpecKit implementation PR has merged and the repository
needs post-merge archive hygiene. The goal is to preserve source recovery
evidence, update project memory, remove only the completed active spec folder,
refresh generated SpecKit indexes, and leave the roadmap ready for the next
SPEC.

This skill mutates repository files. It is not a read-only status command, not
the scaffold entrypoint, and not the implementation autopilot. If the PR has
not merged, stop and report that archive cleanup is premature unless the user
explicitly asks for an abandoned-work cleanup and the repository has a clear
convention for that path.

## Inputs

Accept any of these:

- a SPEC-ID such as `SPEC-007` or `SPEC-014`
- an active spec directory under `specs/`
- a workflow file under `docs/ai/specs/.process/`
- a merged PR URL or number

When multiple inputs are present, verify they point to the same work. Do not
archive based on a SPEC-ID alone when the merge source is ambiguous. Derive the
repository from local `git remote` output when only a PR number is supplied.

## Required Grounding

Before editing:

1. Inspect `git status --short --branch`.
2. Confirm or create a cleanup branch based on current mainline. Use the local
   branch naming convention, normally a `codex/` branch.
3. Confirm PR merge state with GitHub tooling when available. Capture PR URL,
   PR number, title, merged-at timestamp, and merge commit.
4. Read the archive extension command contract if
   `.specify/extensions/archive/commands/archive.md` exists.
5. Read the newest relevant archive reports under
   `.specify/memory/archive-reports/` to match local wording and cleanup style.
6. Check for `.specify/feature.json`. If it is absent, do not create it. If it
   exists and points to the completed spec, handle it according to local archive
   convention.
7. List active specs with `find specs -mindepth 1 -maxdepth 4 -print` and
   identify the exact folder owned by the merged spec.

SpecKit Pro keeps `docs/ai/specs/.process/*` workflow and design files as
historical evidence; remove them only when the repository explicitly does so.

## Archive Edits

The archive extension contract is local policy with one override: SpecKit Pro
replaces its agent-context step (stock `stn1slv/spec-kit-archive` step 5.3,
vendored fork step 6.3). Never append per-spec history (archive notes, Active
Technologies bullets, or Recent Changes bullets) to agent context files
(`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`). The archive report and
`.specify/memory/` records hold that history, and Codex reads `AGENTS.md`
under a 32 KiB budget. If you also follow the archive command contract
alongside the memory entries below, scope it so it cannot reach that step:

```text
archive command: specs/<merged-spec-dir> --spec-only --plan-only --changelog-only
```

Several scope modifiers form a union, so this run updates
`.specify/memory/spec.md`, `plan.md`, and `changelog.md` and leaves the agent
context files alone.

Add an archive report under `.specify/memory/archive-reports/` named with the
date and SPEC-ID, for example
`2026-06-17-spec-007-post-merge-hygiene.md`. Include:

- merged PR URL and title
- merged-at timestamp and merge commit
- source spec directory
- workflow file and design/process files preserved
- canonical shipped artifacts that replaced the active spec folder
- cleanup branch and cleanup command
- exact recovery commands using `git show` or `git checkout` against the merge
  commit
- verification commands run for the archive cleanup

Append concise entries to:

- `.specify/memory/spec.md`
- `.specify/memory/plan.md`
- `.specify/memory/changelog.md`

These entries should explain what shipped, why the active `specs/**` folder can
be removed, where canonical artifacts live now, and where the detailed archive
report is stored.

Update roadmap, traceability, and agent context files only where they still
show the merged spec as pending, in progress, or blocking downstream work.
Move downstream specs from blocked to ready only when the completed spec was
the actual blocker. Be specific: name the merged PR and the canonical files
that now satisfy the dependency.

If `docs/ai/specs/.process/autopilot-state.json` exists and points at the
completed spec, rewrite it as completed archive state. Keep it valid JSON. Mark
the active step as archived, the status as completed or completed archived, and
the archive sweep as applied. Preserve useful project command names from the
previous state.

## Active Spec Cleanup

Remove only the completed active spec directory under `specs/`. Do not delete
`specs/.gitkeep`. Do not delete unrelated active specs, fixture specs, or
process files. If the active spec folder is still referenced by live tests or
scripts, either decouple those references first or stop and report the blocker.

After removal, regenerate the active spec index with SpecKit Pro's runner
helpers, so the generated MOC or index no longer points at the archived spec
directory. Send each request as one JSON object on stdin to
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

## Safe Parallelism

Safe to run in parallel:

- read-only discovery commands such as `git status`, `gh pr view`, `find specs`,
  and `rg` scans
- reading multiple roadmap, workflow, memory, and archive-report files
- independent read-only stale-reference searches

Do not parallelize:

- edits to memory, roadmap, traceability, generated indexes, or
  `autopilot-state.json`
- active spec removal
- docs reference generation, payload generation, staging, commits, pushes, or
  PR creation

Those steps all update one shared repository state. Serial edits keep status
consistent across project memory, roadmap text, generated indexes, and PR
evidence.

## Verification

Run focused verification before committing:

- `resolved_python -m json.tool docs/ai/specs/.process/autopilot-state.json`
  when that file changed
- `generate-spec-index-write` in `apply` mode, then `generate-spec-index-check`
- a `find specs -mindepth 1 -maxdepth 4 -print` audit showing only expected
  active specs
- docs reference generation/checks when reference pages changed
- payload builder when plugin source changed
- `git diff --check`
- the repository structural validation suite or the smallest repository-equivalent
  structural check

If a command fails because of missing dependencies, sandboxing, or network
access, retry only when the environment policy allows it. Otherwise report the
skipped check and the practical impact.

## Git And Final Response

Commit intentionally after verification. For archive-only cleanup commits and
PRs, use a lower-case Conventional Commit scope derived from the completed spec
ID. For example, archive cleanup for `SPEC-001` should use
`docs(spec-001): archive post-merge state`, not
`docs(SPEC-001): archive post-merge state`. The repository PR title gate checks
the final PR title, so apply the same lower-case scope to `gh pr create` or
`gh pr edit --title`. In the final response,
include the merged PR provenance, active spec folder removed, archive report
path, generated files refreshed, verification commands, and remaining risks.

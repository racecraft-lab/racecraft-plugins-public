---
name: speckit-archive-cleanup
description: >
  Archive a merged SpecKit spec, remove completed active specs, refresh
  roadmap and project-memory state, and prepare the cleanup PR after merge.
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

- a SPEC-ID such as `DOC-007` or `PRSG-014`
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

Preserve process evidence unless the repository explicitly removes it. In this
repository, `docs/ai/specs/.process/*` workflow and design files are historical
evidence and should remain.

## Cleanup Plan

Use `update_plan` for this workflow when the tool is available. A normal plan
is:

1. Confirm merge provenance and branch safety.
2. Archive project memory and roadmap state.
3. Remove completed active spec residue.
4. Regenerate indexes, reference docs, and generated payloads when affected.
5. Verify, commit, push, and open the cleanup PR.

Keep exactly one plan item in progress at a time. If the user sends a newer
instruction while cleanup is underway, let the newer instruction steer the
remaining work.

## Archive Edits

Add an archive report under `.specify/memory/archive-reports/` named with the
date and SPEC-ID, for example
`2026-06-17-doc-007-post-merge-hygiene.md`. Include:

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

Update roadmap and traceability files that still show the merged spec as
pending, in progress, or blocking downstream work. Move downstream specs from
blocked to ready only when the completed spec was the actual blocker. Be
specific: name the merged PR and the canonical files that now satisfy the
dependency.

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

After removal, run the repository's SpecKit index generator in write mode, then
run its check mode. The generated MOC or index should no longer point at the
archived spec directory.

## Plugin And Docs Side Effects

If this cleanup adds or edits plugin skills, agents, hooks, manifests, or
generated docs references, update the matching validation surfaces in the same
branch. For this repository that usually means:

- update structural test allowlists when a skill is added
- add the Codex `agents/openai.yaml` sidecar for Codex skills
- regenerate docs reference pages when source skill inventories changed
- rebuild generated plugin payloads when source plugin files changed

Do not leave source and generated payloads out of sync when tests enforce
payload parity.

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

- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json` when that
  file changed
- the SpecKit index generator and its `--check` mode
- a `find specs -mindepth 1 -maxdepth 4 -print` audit showing only expected
  active specs
- docs reference generation/checks when reference pages changed
- payload builder when plugin source changed
- `git diff --check`
- `bash tests/speckit-pro/run-all.sh` or the smallest repository-equivalent
  structural suite

If a command fails because of missing dependencies, sandboxing, or network
access, retry only when the environment policy allows it. Otherwise report the
skipped check and the practical impact.

## Git And Final Response

Commit intentionally after verification. A typical commit title is
`docs(SPEC-ID): archive post-merge state` for archive-only work, or a separate
`feat(skills): add archive cleanup workflow` commit when this workflow becomes
a plugin skill.

If you stage, commit, push, or create a PR in Codex Desktop, emit the matching
Codex git directives only after the action succeeds. In the final response,
include the merged PR provenance, active spec folder removed, archive report
path, generated files refreshed, verification commands, and remaining risks.

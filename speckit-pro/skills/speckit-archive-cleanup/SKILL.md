---
name: speckit-archive-cleanup
description: "Archive a merged SpecKit spec and clean active workflow residue after the implementation PR has merged. Use after confirming merge provenance, when the user asks for post-merge SpecKit archive hygiene, cleanup hygiene, or removal of completed specs from active specs."
argument-hint: "SPEC-ID and optional merged PR URL or number"
user-invocable: true
allowed-tools: Bash Read Edit Write Grep Agent
license: MIT
---

# SpecKit Archive Cleanup

## Codex Skill-Selection Guard

If this file is loaded in Codex, the runtime selected the Claude Code
variant from `skills/` instead of the Codex variant from `codex-skills/`.
Do not follow the Claude-oriented instructions below in Codex. Immediately
read and follow `../../codex-skills/speckit-archive-cleanup/SKILL.md` from
this plugin root, treat that document as the active skill, and report that
the fallback guard was triggered.

Use this skill after a SpecKit implementation PR has merged and the repository
still contains active workflow or `specs/**` residue for that completed work.
The goal is to preserve recovery evidence in project memory, remove only the
completed active spec folder, refresh generated SpecKit indexes, and leave the
roadmap ready for the next SPEC.

This is a mutation-heavy archive workflow. Do not use it for normal status
checks, scaffold setup, autopilot implementation, or read-only PR review. If
merge status is unknown, first verify it. If the PR is still open, do not
archive the spec unless the user explicitly requests an abandoned-spec cleanup
and the repository has an established convention for that case.

## Inputs

Accept a SPEC-ID such as `DOC-007` or `PRSG-014`, an active spec directory, a
workflow file path, or a merged PR URL/number. If more than one is provided,
cross-check that they all point to the same completed work.

Required facts before editing:

- merged PR number, merge timestamp, merge commit, and PR title
- active spec directory under `specs/`
- workflow file under `docs/ai/specs/.process/`, if present
- current roadmap and traceability files affected by the spec family
- installed archive extension contract, if `.specify/extensions/archive/` exists

## Ground Truth Checks

Start from live repository truth:

1. Inspect `git status --short --branch`.
2. Confirm the current branch is a cleanup branch based on the current mainline,
   or create one before editing.
3. Confirm the PR is merged with GitHub tooling or the best available local
   merge evidence.
4. Read the existing newest archive reports in `.specify/memory/archive-reports/`
   to match local conventions.
5. Check whether `.specify/feature.json` exists. If it is absent, do not create
   it. If it exists and points at the completed spec, remove or rewrite it only
   according to repository convention.
6. List active specs with `find specs -mindepth 1 -maxdepth 4 -print` and
   identify the exact folder that belongs to the merged spec.

Do not remove any active spec folder until merge provenance and recovery
commands are recorded. Do not remove process files under
`docs/ai/specs/.process/` unless repository history shows that process evidence
is intentionally deleted for completed specs. In this repository, process files
are preserved as historical evidence.

## Archive Procedure

Read the archive extension command contract before making archive edits when it
is present. Treat it as the local policy for source directories, memory files,
cleanup eligibility, and extension hooks.

Then update the project state in this order:

1. Add an archive report under `.specify/memory/archive-reports/` named with the
   current date and SPEC-ID. Include PR URL, merge commit, merged-at timestamp,
   source spec path, workflow file, canonical shipped artifacts, cleanup branch,
   cleanup command, verification commands, and exact recovery commands using
   `git show` or `git checkout` against the merge commit.
2. Append concise records to `.specify/memory/spec.md`,
   `.specify/memory/plan.md`, and `.specify/memory/changelog.md`. These records
   should summarize what shipped, where canonical artifacts live now, why the
   active spec folder can be removed, and where the detailed archive report is.
3. Update roadmap, traceability, AGENTS, or MOC files that still describe the
   merged spec as pending, in progress, or blocking downstream work.
4. Update `docs/ai/specs/.process/autopilot-state.json` only if it exists and
   still points at the completed spec. The status should become an archived or
   completed archive state, with the cleanup applied and post-merge archive
   phase completed.
5. Remove the completed active spec directory under `specs/`. Keep `specs/.gitkeep`.
6. Regenerate the active spec index with the repository's existing generator,
   then run its `--check` mode.

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

- active spec listing shows only expected active specs and `specs/.gitkeep`
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- SpecKit index generation and `--check`
- docs-site reference generation/checks when reference pages changed
- payload builder and payload parity checks when plugin source changed
- `git diff --check`
- repository structural test suite, usually `bash tests/speckit-pro/run-all.sh`

If a check cannot run, report the exact command and the reason. Do not claim the
archive is fully verified when generated files or structural checks are stale.

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

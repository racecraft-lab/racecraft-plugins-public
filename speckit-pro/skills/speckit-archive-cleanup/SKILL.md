---
name: speckit-archive-cleanup
description: "Archive a merged SpecKit spec and clean active workflow residue after the implementation PR has merged. Use after confirming merge provenance, when the user asks for post-merge SpecKit archive hygiene, cleanup hygiene, or removal of completed specs from active specs."
argument-hint: "SPEC-ID and optional merged PR URL or number"
user-invocable: true
allowed-tools: Read Edit Write Grep Agent
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
completed spec's active artifacts, retain its generated archived `SPEC-MOC.md`
stub, refresh generated SpecKit indexes, and leave the roadmap ready for the
next SPEC.

## Durable knowledge

Follow [the shared knowledge lifecycle](../speckit-coach/references/knowledge-lifecycle.md).
Archive cleanup is the final distillation boundary. Before deleting active spec
residue, review reusable final decisions, patterns, domain facts, and runbooks;
promote accepted candidates through `knowledge-update-plan` and
`knowledge-update-apply`. Then use action `archive` to preserve discoverability
and regenerate indexes and MOC compatibility views. Never edit generated MOCs
or canonical concepts directly.
For archive planning, pass the canonical `concept_path` and optional verified
archive-report `sources`. Every apply carries `repo_root`, the complete accepted
`plan`, `plan_hash`, and `expected_snapshot`.

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

Do not remove any active spec artifacts until merge provenance and recovery
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
2. If the knowledge manifest has `legacy_memory_status: frozen`, do not append to
   `.specify/memory/spec.md`, `plan.md`, or `changelog.md`; they are frozen
   history. Before cutover only, preserve the repository's compatibility append
   behavior. The archive report remains evidence in both cases.
3. Update roadmap, traceability, or agent context files ONLY to remove or
   correct references that still describe the merged spec as pending, in
   progress, or blocking downstream work. Never edit MOCs; the archive apply
   regenerates their compatibility views. Never append
   per-spec history entries (archive notes, Active Technologies bullets, or
   Recent Changes bullets) to agent context files — the archive report and
   knowledge concepts are the system of record for reusable history, and agent
   context files must stay small (Codex reads AGENTS.md under a 32 KiB budget).
   A changed roadmap is authoritative source drift: build a reviewed
   replacement for its canonical project map and plan/apply same-path
   `supersede`. Do not use `rebuild` to refresh its source hash.
4. Update `docs/ai/specs/.process/autopilot-state.json` only if it exists and
   still points at the completed spec. The status should become an archived or
   completed archive state, with the cleanup applied and post-merge archive
   phase completed.
5. Reread the finalized roadmap, traceability files, and verified archive
   report. Only now build `knowledge_candidates` with exact source hashes.
   Review and promote accepted candidates with a `promote` plan/apply, apply any
   roadmap-map `supersede`, then run an `archive` plan/apply for the SPEC with
   current durable sources. Do not promote raw workflow status, UAT prose, or
   unverified lessons. If a source changes after hashing, discard the plan and
   recompute it.
6. Remove the completed spec's other active artifacts under `specs/<branch>/`,
   but retain the directory and regenerated archived `SPEC-MOC.md` compatibility
   stub. Keep `specs/.gitkeep`. Removing that stub requires a separate reviewed
   deprecation; archive cleanup never deletes it.
7. Run `knowledge-health` and require the archived concept to remain
   discoverable, source evidence to resolve, and all generated indexes and the
   archived MOC compatibility stub to be current. Use `rebuild` only if health
   reports projection drift while canonical sources remain current.

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

- edits to roadmap, traceability, legacy memory, knowledge, and autopilot-state files
- active spec artifact removal while preserving the archived `SPEC-MOC.md` stub
- generated index and generated docs updates
- staging, committing, pushing, and PR creation

The serialized files all represent one shared project state. Parallel edits
make it easy to leave contradictory status such as "archived" in memory but
"in progress" in a roadmap.

## Verification

Run the smallest checks that prove the cleanup, then the standard project
checks if plugin or generated payload files changed. Typical checks:

- archived spec directory contains only the expected generated `SPEC-MOC.md`
  stub, and active spec listings contain only expected work
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- knowledge archive apply, optional projection-only rebuild, then `knowledge-health`
- docs-site reference generation/checks when reference pages changed
- payload builder and payload parity checks when plugin source changed
- `git diff --check`
- repository structural validation suite

If a check cannot run, report the exact command and the reason. Do not claim the
archive is fully verified when generated files or structural checks are stale.

## Final Report

Report:

- the merged PR and merge commit used as provenance
- the active spec artifacts removed and archived `SPEC-MOC.md` stub retained
- archive report path
- roadmap or traceability status changes
- generated files refreshed
- verification commands and results
- remaining risks, especially skipped browser UAT or skipped CI checks

Keep the report short and make the next action explicit, usually review the
cleanup PR or merge it after CI passes.

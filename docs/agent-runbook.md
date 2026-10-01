# Agent Runbook

Step-by-step procedures that the root `AGENTS.md` points to. The rules live in
`AGENTS.md`; this file holds the longer how-to so the agent contract stays
short. Run every command from the repository root.

## Generated-Artifact Merge Driver

Define the merge driver once per clone:

```bash
git config merge.generated.name "keep ours; regenerate after merge"
git config merge.generated.driver "exit 0"
```

`.gitattributes` routes generated paths here; the driver keeps "ours" (your
branch in a merge, upstream in a rebase). Use `exit 0`, not `true`, which git
runs from PATH. Git never runs driver code from a clone, so this stays local
and fails safe.

## Merging Main

Generated artifacts are a pure function of the source tree, so a merge never
produces a correct one. Regenerate; do not hand-resolve. One sanctioned hand
edit: if `main` brought in a release and your branch also changed the runner
manifest, set its `plugin_version` to `speckit-pro/.codex-plugin/plugin.json`'s
`version` before the refresh. Run these, then the CI suite:

```bash
git merge origin/main            # generated paths resolve without conflict
python3 scripts/refresh-release-artifacts.py
pnpm --dir docs-site reference:generate
```

## Regenerating Spec Index Blocks

The spec index blocks in `SPEC-MOC.md` and the roadmap MOC files come from a
runner request shaped like
`tests/speckit-pro/unit/fixtures/mutation-helpers/requests/generate-spec-index-write.json`
with `repo_root` set to `.`. Run it with `dry_run`, then `apply`, with
untracked files moved aside. The generator scans the filesystem, so a backlink
to an untracked path passes locally and fails on a clean checkout. Commit only
your spec's index files, since `main` may already be stale. No PR check
catches stale index blocks.

## Opening a Pull Request With gh-stack

Open every PR with `gh-stack`, even one PR, although GitHub links a stack only
at two. Install the official `gh-stack` skill at user scope; the default project scope
writes into this repository:

```text
gh skill install github/gh-stack gh-stack --scope user --agent claude-code
```

Use `--agent codex` for Codex. `gh stack submit --auto` opens drafts titled
from a lone commit's subject or else the branch name, with the PR template as
body. Set the title and the `release-note` fence with `gh pr edit`, then mark
the PR ready. A draft skips every other PR Checks job, and `validate-plugins`
passes anyway.

## Ripwire Configuration

- `.ripwire_arch_rules` states the intended layering and
  `.ripwire_arch_baseline` records today's debt. `ripwire . --arch=.ripwire_arch_rules`
  checks them; exit 2 means a new violation.
- `.ripwire_notes` holds field notes that `ripwire . --for` surfaces.
- Never re-baseline to hide a new edge; use `--baseline-update` in its own
  reviewed commit.
- There is no committed quality baseline, because ripwire honors one only at
  the exact commit it pinned.
- The `ripwire-advisory` PR job reports `--arch`, `--quality-delta` from the
  merge-base, and `--doc-drift` in the job summary. It never blocks: it is not
  a required check and passes on findings. `scripts/install-ripwire.py` pins
  one Linux release by SHA-256 for CI.

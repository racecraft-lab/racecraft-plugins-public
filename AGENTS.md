# Repository Agent Instructions

Use this file as the shared agent contract for Codex, Claude Code, Gemini, and
Copilot. Keep it concise: agent context should contain durable behavior, not
release history, workflow runbooks, generated-plan exhaust, or long plugin
internals.

## Working Rules

These rules are adapted from Andrej Karpathy's agent guidance and this repo's
own failure patterns.

### 1. Surface assumptions before editing

- State assumptions in chat before touching files.
- If a manifest, release, CI, or generated-artifact change is ambiguous, ask.
- If a simpler path might solve the request, name it before doing larger work.
- Stop and describe confusion instead of pushing through on a guess.

### 2. Make the simplest change that solves the task

- Do not add features, flags, abstractions, or helper layers for hypothetical
  future callers.
- Prefer existing repo patterns and source-of-truth files over new conventions.
- If a change feels larger than the request, shrink it or explain why the size is
  necessary.

### 3. Keep edits surgical

- Touch only files that directly serve the request.
- Do not reformat adjacent JSON, reorder manifest keys, or clean up unrelated
  comments.
- Remove only code or prose that your change actually orphans.
- Match local style even when you would normally write it differently.

### 4. Verify success explicitly

- Decide the relevant check before coding.
- Prefer the smallest useful check while iterating, then run the broader gate
  when the changed surface warrants it.
- Before creating a PR or marking it ready, validate the exact final title with
  the repository release-readiness gate. The live gate requires
  `<type>(<lowercase-scope>): <plain English description>`.
- If verification cannot run, report the exact command and reason.

## Start Here

A public Claude Code and Codex marketplace with one plugin, `speckit-pro`.
Both marketplace files point installers at `dist/claude/speckit-pro/` and
`dist/codex/speckit-pro/`. Historical specs and generated planning artifacts
are context on demand. Scoped `AGENTS.md` files in `speckit-pro/`,
`tests/speckit-pro/`, and `docs-site/` add rules for their trees.

| Area | Where to look |
| --- | --- |
| Claude skills, agents, hooks | `speckit-pro/skills/`, `speckit-pro/agents/`, `speckit-pro/hooks/` |
| Codex skills, agents, hooks | `speckit-pro/codex-skills/`, `speckit-pro/codex-agents/` (TOML), `speckit-pro/codex-hooks.json` |
| Python runner | `speckit-pro/speckit_pro_runner/`: gates in `gates/`, helper ids in `helpers/registry.py` |
| Release and CI tooling (not shipped) | `scripts/`, `.github/workflows/` |
| Tests | `tests/speckit-pro/`; layers and default selection in `suite-manifest.json` |
| Contributor, review, security docs | `docs-site/src/content/docs/contribute-and-release.md`, the PR template, `REVIEW.md`, `SECURITY.md` |

With `ripwire` on PATH, map first: `ripwire . --for="<task>"`, then
`--callers=SYM` and `--impact=SYM` before a change, and
`--quality-delta=$(git merge-base origin/main HEAD)..HEAD` before calling work
done, one argument per flag. In 0.6.2, `--exemplar` ignored its query here.

## Commands

Run from the repository root. The `test` job uses the runner's `python3` (3.12
today), which warns on an invalid escape such as `"\|"` that 3.11 ignores.

| Check | Command | CI job (required?) |
| --- | --- | --- |
| Quick suite: toolchain, layers 1, 4, 5 (`--layer 1`, `4`, `5`, or `6` for one) | `python3 tests/speckit-pro/run-all.py` | none |
| CI suite: adds layers 6 and 7; the only way to run parity (7) | `SPECKIT_SKIP_TOOLCHAIN_CHECK=1 GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null GIT_CONFIG_NOSYSTEM=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/run-default-suite.json` | `test` (yes, via `validate-plugins`) |
| Generated-artifact drift; commit first, since any uncommitted change under its paths fails it | `python3 scripts/refresh-release-artifacts.py --check` | `artifact-consistency` (yes, via `validate-plugins`) |
| PR title | `TITLE='<title>' PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/validate-pr-title-live.json` | `validate-pr-title` (yes) |
| Release-note fence | `PR_TITLE='<title>' PR_BODY='<body>' python3 scripts/compose-release-notes.py --validate-pr` | `validate-release-note` (yes) |
| Docs reference pages (`validate` for the full site) | `pnpm --dir docs-site reference:check` | `validate-docs` (no) |
| Container preflight | CI only | `container-preflight-linux-amd64`, `-arm64` (yes) |
| Workflow lint | `actionlint` 1.7.12 from the repository root. The CI installer (`scripts/install-actionlint.py`) fetches a Linux amd64 binary only | `validate-workflows` (no; it also checks release-PR ancestry, CI only) |

## Worktree Preflight

- A fresh worktree holds only tracked files. The test suite needs no
  bootstrap; `docs-site/` is the only surface with dependencies. Run
  `pnpm --dir docs-site install --frozen-lockfile` once per worktree before any
  docs command, including `reference:generate`.
- Define the generated-artifact merge driver once per clone:

  ```bash
  git config merge.generated.name "keep ours; regenerate after merge"
  git config merge.generated.driver "exit 0"
  ```

  `.gitattributes` routes generated paths here; the driver keeps "ours" (your
  branch in a merge, upstream in a rebase). Quote `"exit 0"`: git runs a
  one-word driver as a program on PATH. Git never runs driver code from a
  clone, so this stays local; skipping it fails safe.

## Merging Main

Generated artifacts are a pure function of the source tree, so a merge never
produces a correct one. **Regenerate; do not hand-resolve.**

```bash
git merge origin/main            # generated paths resolve without conflict
python3 scripts/refresh-release-artifacts.py
pnpm --dir docs-site reference:generate
```

If `main` brought in a release and your branch also changed the runner
manifest, copy `plugin_version` from `.release-please-manifest.json`, then run
the suite. After adding or retitling a spec, regenerate the spec index with
untracked files moved aside: the generator scans the filesystem, and the
suite's link check rejects a backlink to an untracked path.

## Generated Files

| Output | Regenerate with | Caught by |
| --- | --- | --- |
| `dist/` payloads, marketplace versions, runner hashes (any runner `.py` edit) | `python3 scripts/refresh-release-artifacts.py` | `artifact-consistency` |
| Runner manifest `plugin_version` | release-please; the refresh never writes it | `test` (`test-speckit-pro-runner.py`) |
| `docs-site/src/content/docs/reference/**`, from plugin sources, READMEs, manifests, `scripts/`, `tests/speckit-pro/` | `pnpm --dir docs-site reference:generate` | `validate-docs` only, not required |
| Spec index blocks in `SPEC-MOC.md` and roadmap MOC files | runner helper `generate-spec-index-write`: `dry_run`, then `apply` (`main` may already be stale) | freshness: no PR check |

## Gotchas

- On a draft PR every other PR Checks job is skipped and `validate-plugins`
  still passes. Mark the PR ready to run CI.
- A non-empty `release-note` fence reaches the release notes whatever the PR
  type, unless the PR has the `release-note/skip` label. Only `feat` and `fix`
  need one; leave it empty otherwise.
- `test-privacy-scan.py` rejects email addresses, home paths, Claude and macOS
  temp paths, raw UUIDs, and local identity terms in any non-ignored file. A
  guard rejects `bash`, `sh`, or `jq` commands in this file, `CLAUDE.md`, the
  root and plugin READMEs, and docs-site content; write `python3` calls.
- A running Claude Code or Codex session uses the installed plugin, not this
  checkout; try `claude --plugin-dir dist/claude/speckit-pro` after a refresh.
  `scripts/refresh-local-plugin.py` rebuilds `dist/`, reinstalls user-scope
  plugins, and stops if either marketplace points elsewhere: `--dry-run` first.

## Editing Boundaries

- Do not hand-edit generated payloads, generated reference pages, or vendored
  upstream content.
- Name repository-authored scripts and tests for durable behavior or capability;
  never couple their filenames to a temporary spec ID, and never have test code
  read a `specs/<feature>/` path from disk at run time. Archive cleanup deletes
  that folder once the feature merges, so such a read is green today and red at
  archive time, in a cleanup branch that has nothing to do with it. Freeze any
  spec prose a test needs under that test's own `fixtures/` tree. Asserting a
  `specs/...` path as a string is fine; opening one is not, and
  `tests/speckit-pro/lib/test_result.py` enforces the difference at run time.
- Keep repository-owned tooling on Python 3.11+ standard library unless an
  existing local toolchain already owns the surface.
- Do not add active repository Bash or `jq` dependencies outside existing
  workflow dispatch glue and fixed vendored boundaries.
- If plugin source or payload-affecting files change, account for the generated
  artifact contract before calling the work done.

## Definition Of Done

- Generated outputs, including a new spec's index, are committed with their
  source; the CI suite and `refresh-release-artifacts.py --check` pass.
- `reference:check` and actionlint pass when their inputs changed, any
  `release-note` fence passes its gate, and the PR is ready with checks green.

## Code Review Rules

Codex reads this section during review. Claude Code's managed Code Review reads
the root `REVIEW.md` instead, which states the same rules in fuller form. Keep
the two in step when either changes.

- Treat as blocking: manifest or version drift; plugin source changed without
  accounting for the generated artifact contract; malformed loader frontmatter;
  repository tooling leaving the Python 3.11+ standard library or adding an
  active Bash or `jq` dependency outside the allowed boundaries; a workflow that
  exposes secrets or elevated permissions to untrusted PR content; a script or
  test filename coupled to a temporary spec ID, or test code that reads a
  `specs/<feature>/` path from disk at run time.
- Treat style, naming, prose, and refactoring suggestions as minor at most.
- Do not review generated reference pages, generated payloads, vendored upstream
  content, lockfiles, or archived specs.
- Do not report anything CI already enforces.
- Require a `file:line` citation for any claim about behavior.

## Agent File Hygiene

- `AGENTS.md` is the only authored agent-instruction source in each scoped
  directory.
- `CLAUDE.md` files must only import the sibling `AGENTS.md`.
- `GEMINI.md` files must only import the sibling `AGENTS.md`.
- Do not put feature plans, release notes, implementation transcripts, or
  detailed process history in agent files.
- `REVIEW.md` lives only at the repository root and is injected verbatim into
  review agents. It does not expand `@` imports, so write rules directly into it
  rather than referencing other files.

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

A public Claude Code and Codex marketplace; its one plugin, `speckit-pro`,
installs from `dist/`. Specs and planning artifacts are context on demand.
Before editing `speckit-pro/`, `tests/speckit-pro/`, or `docs-site/`, read its
scoped `AGENTS.md`; Codex loads one only when started inside that directory.

| Area | Where to look |
| --- | --- |
| Claude skills, agents, hooks | `speckit-pro/skills/`, `speckit-pro/agents/`, `speckit-pro/hooks/` |
| Codex skills, agents, hooks | `speckit-pro/skills/` overlaid by `speckit-pro/codex-skills/`, `speckit-pro/codex-agents/` (TOML), `speckit-pro/codex-hooks.json` |
| Python runner | `speckit-pro/speckit_pro_runner/`: gates in `gates/`, helper ids in `helpers/registry.py` |
| Tests | `tests/speckit-pro/`; layers and default selection in `suite-manifest.json` |

Two optional tools save reading and tokens; work on without them, and no check
may depend on either. With `ripwire` on PATH (one argument per flag), run
`ripwire . --for="<task>"` first, `--callers=SYM` and `--impact=SYM` before a
change, and `--quality-delta=$(git merge-base origin/main HEAD)..HEAD` before a
PR; confirm its graph with a read. Jev (the `typesafe-jev` plugin's `evaluate`
tool) gives advisory judgments only: its verdict never approves a destructive
step, and each call bills a third party, so send no secrets or local paths.

## Commands

Run from the repository root (Python 3.11+, Node >= 22.12 for docs). The `test`
job's unpinned, newer `python3` warns on a `"\|"` escape; 3.11 does not.

| Check | Command | CI job (required?) |
| --- | --- | --- |
| Quick suite: toolchain, layers 1, 4, 5 (`--layer 1`, `4`, `5`, or `6` for one) | `python3 tests/speckit-pro/run-all.py` | none |
| CI suite: adds layers 6 and 7 (`run-all.py` cannot select 7; `python3 tests/speckit-pro/run-layer-scripts.py --layer 7` runs it alone) | `SPECKIT_SKIP_TOOLCHAIN_CHECK=1 GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null GIT_CONFIG_NOSYSTEM=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/run-default-suite.json` | `test` (yes, via `validate-plugins`) |
| Generated-artifact drift; commit first, since any uncommitted change under its paths fails it | `python3 scripts/refresh-release-artifacts.py --check` | `artifact-consistency` (yes, via `validate-plugins`) |
| PR title | `TITLE='<title>' PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/validate-pr-title-live.json` | `validate-pr-title` (yes) |
| Release-note fence | `PR_TITLE='<title>' PR_BODY='<body>' PR_LABELS_JSON='[]' python3 scripts/compose-release-notes.py --validate-pr` | `validate-release-note` (yes) |
| Docs, reference mode: reference inputs changed | `pnpm --dir docs-site reference:check`, then `pnpm --dir docs-site validate:quality` | `validate-docs` (no) |
| Docs, full mode: `docs-site/`, the artifact gallery, or a docs contract file changed (`scripts/classify-docs-validation.py`) | `pnpm --dir docs-site exec playwright install chromium` once, then `pnpm --dir docs-site validate` | `validate-docs` (no) |
| Container preflight: Linux containers rerun the suite when runner, test, or workflow paths change | CI only; its extra requests (`LINUX_REQUESTS` in `tests/speckit-pro/run-container-preflight.py`) also run locally | `container-preflight-linux-amd64`, `-arm64` (yes) |
| Workflow lint | `actionlint` at the version pinned in `pr-checks.yml`, from the repository root. The CI installer (`scripts/install-actionlint.py`) fetches a Linux amd64 binary only | `validate-workflows` (no; it also checks release-PR ancestry, CI only) |

## Worktree Preflight

- A fresh worktree holds only tracked files; before any docs command, run
  `pnpm --dir docs-site install --frozen-lockfile`.
- Define the generated-artifact merge driver once per clone:

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
produces a correct one. **Regenerate; do not hand-resolve.** One sanctioned hand
edit: if `main` brought in a release and your branch also changed the runner
manifest, set its `plugin_version` to `speckit-pro/.codex-plugin/plugin.json`'s
`version` before the refresh. Run these, then the CI suite:

```bash
git merge origin/main            # generated paths resolve without conflict
python3 scripts/refresh-release-artifacts.py
pnpm --dir docs-site reference:generate
```

| Output | Regenerate with | Caught by |
| --- | --- | --- |
| `dist/` payloads, marketplace versions, runner hashes (any runner `.py` edit) | `python3 scripts/refresh-release-artifacts.py` | `artifact-consistency` |
| `docs-site/src/content/docs/reference/**`, from plugin sources, READMEs, manifests, `scripts/`, `tests/speckit-pro/` | `pnpm --dir docs-site reference:generate` | `validate-docs` only, not required |
| Spec index blocks in `SPEC-MOC.md` and roadmap MOC files | runner request shaped like `tests/speckit-pro/unit/fixtures/mutation-helpers/requests/generate-spec-index-write.json` with `repo_root` `.`: `dry_run`, then `apply`, with untracked files moved aside (the generator scans the filesystem, so a backlink to an untracked path passes locally and fails on a clean checkout); commit only your spec's index files, since `main` may already be stale | freshness: no PR check |

## Gotchas

- `test-privacy-scan.py` rejects non-allowlisted emails, home paths, Claude and
  macOS temp paths, raw UUIDs, and local identity terms in non-ignored files;
  use repo-relative placeholders. Files listed in `active_path_guard.py`, this
  one included, must not instruct `bash`, `sh`, or `jq`; use `python3`.
- Live sessions run the installed plugin; `claude --plugin-dir
  dist/claude/speckit-pro` tests a refreshed `dist/`. Ask before
  `scripts/refresh-local-plugin.py` (`--dry-run` previews): it rebuilds `dist/`,
  reinstalls user-scope plugins, and stops if a marketplace points elsewhere,
  even at the main checkout.

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

## Pull Requests

Open every pull request with the official `gh-stack` skill, even one PR (GitHub
links a stack only at two). Install it at user scope; the default project scope
writes into this repository:
`gh skill install github/gh-stack gh-stack --scope user --agent claude-code`
(or `codex`). Validate the final title first. `gh stack submit --auto` opens
drafts titled from a lone commit's subject or else the branch name, with the PR
template as body: set the title and fence with `gh pr edit`, then mark ready. A
draft skips every other PR Checks job, and `validate-plugins` passes anyway.

## Definition Of Done

- Generated outputs are committed with their source; `--check`, both suites, and
  required checks pass, as do docs checks and actionlint when their inputs
  changed. Only `feat` and `fix` PRs fill the `release-note` fence, required
  unless labeled `release-note/skip`; any unlabeled fence is published.

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

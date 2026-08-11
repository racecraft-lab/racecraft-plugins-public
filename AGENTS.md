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

## Repository Orientation

- This is a public Claude Code and Codex plugin marketplace.
- Current plugin source lives under `speckit-pro/`.
- Repository-only validation lives under `tests/speckit-pro/`.
- The docs site lives under `docs-site/`.
- Historical specs and generated planning artifacts are context on demand, not
  always-on agent instructions.

## Worktree Preflight

A fresh worktree holds only tracked files. Three facts cover every surface:

- The repository test suite needs no bootstrap. Run
  `python3 tests/speckit-pro/run-all.py` directly.
- `docs-site/` is the only surface with dependencies. Run
  `pnpm --dir docs-site install --frozen-lockfile` once per worktree before any docs command,
  including the `pnpm --dir docs-site reference:generate` that the scoped
  `tests/speckit-pro/` and `docs-site/` rules require after a tracked
  `.md`, `.py`, or `.sh` change under the test tree.
- Define the generated-artifact merge driver once per clone:

  ```bash
  git config merge.generated.name "keep ours; regenerate after merge"
  git config merge.generated.driver "exit 0"
  ```

  `.gitattributes` marks every generated path `merge=generated` so git stops
  text-merging content hashes and payload copies, which is the cause of nearly
  every merge conflict in this repository. The driver keeps git's "ours" side
  verbatim and never mixes the two: the current branch during
  `git merge origin/main`, the upstream during a rebase. Which one survives does
  not matter, because regenerating is the correctness step.

  Use `"exit 0"`, with the quotes, rather than `true`. Git runs a one-word
  driver directly, so `true` needs that executable on PATH; a two-word command
  runs through git's own shell and needs only builtins.

  Git will not run driver code from a cloned repository, so this cannot be
  committed. Skipping it leaves the rules inert and merges behave as they did
  before, so it fails safe.

## Merging Main

Generated artifacts are a pure function of the source tree, so a merge never
produces a correct one. **Regenerate; do not hand-resolve.**

```bash
git merge origin/main            # generated paths resolve without conflict
python3 scripts/refresh-release-artifacts.py
pnpm --dir docs-site reference:generate
```

Then run the suite. CI's `artifact-consistency` job fails the pull request if
the regeneration was skipped, so a stale artifact cannot land.

Two generated surfaces are **not** covered by `refresh-release-artifacts.py`
and need their own step when their inputs changed:

- The spec index (`generate-spec-index`) after adding or retitling a spec.
  Regenerate with untracked files moved aside: the generator scans the
  filesystem rather than the git index, so an untracked path becomes a
  committed backlink that passes locally and fails on a clean checkout.
- The Layer 6 Codex qualification corpus in
  `tests/speckit-pro/layer6-efficiency/fixtures-codex/`, which binds a sha256
  chain over agent source bytes and has no regeneration script. Editing any
  agent definition restales it; the failure reads
  `source digest does not match role source bytes`.

## Source Of Truth

- For plugin behavior, read the nearest `README.md`, manifests, skill files, and
  surrounding source.
- For test selection, use `tests/speckit-pro/suite-manifest.json`.
- For contributor and release workflow details, use
  `docs-site/src/content/docs/contribute-and-release.md`, the PR template, and
  the GitHub workflow files.
- For docs-site commands and constraints, use `docs-site/AGENTS.md`.
- For code-review calibration, use `REVIEW.md`.
- For vulnerability reporting and the security model, use `SECURITY.md`.

## Editing Boundaries

- Do not hand-edit generated payloads, installed-cache proofs, generated
  reference pages, or vendored upstream content.
- Name repository-authored scripts and tests for durable behavior or capability;
  never couple their filenames to a temporary spec ID.
- Keep repository-owned tooling on Python 3.11+ standard library unless an
  existing local toolchain already owns the surface.
- Do not add active repository Bash or `jq` dependencies outside existing
  workflow dispatch glue and fixed vendored boundaries.
- If plugin source or payload-affecting files change, account for the generated
  artifact contract before calling the work done.

## Code Review Rules

Codex reads this section during review. Claude Code's managed Code Review reads
the root `REVIEW.md` instead, which states the same rules in fuller form. Keep
the two in step when either changes.

- Treat as blocking: manifest or version drift; plugin source changed without
  accounting for the generated artifact contract; malformed loader frontmatter;
  repository tooling leaving the Python 3.11+ standard library or adding an
  active Bash or `jq` dependency outside the allowed boundaries; a workflow that
  exposes secrets or elevated permissions to untrusted PR content; a script or
  test filename coupled to a temporary spec ID.
- Treat style, naming, prose, and refactoring suggestions as minor at most.
- Do not review generated reference pages, installed-cache proofs, generated
  payloads, vendored upstream content, lockfiles, or archived specs.
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

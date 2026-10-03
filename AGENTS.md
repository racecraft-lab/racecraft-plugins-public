# Repository Agent Instructions

The shared agent contract for Codex, Claude Code, Gemini, and Copilot. It loads
into every session, so it holds durable behavior only: no release history,
workflow runbooks, generated-plan exhaust, or long plugin internals. Keep it
under 200 lines; put detail in the docs listed under Read When Relevant.

## 1. Start Here

A public Claude Code and Codex marketplace with two plugins: `speckit-pro`,
which installs from `dist/`, and `typesafe-jev`, which installs from
`typesafe-jev/plugin/` with no generated payload. Specs and planning artifacts
are context on demand. Before editing `speckit-pro/`, `tests/speckit-pro/`, or
`docs-site/`, read its scoped `AGENTS.md`; Codex loads one only when started
inside that directory.

| Area | Where to look |
| --- | --- |
| Claude skills, agents, hooks | `speckit-pro/skills/`, `speckit-pro/agents/`, `speckit-pro/hooks/` |
| Codex skills, agents, hooks | `speckit-pro/skills/` overlaid by `speckit-pro/codex-skills/`, `speckit-pro/codex-agents/` (TOML), `speckit-pro/codex-hooks.json` |
| Python runner | `speckit-pro/speckit_pro_runner/`: gates in `gates/`, helper ids in `helpers/registry.py` |
| Tests | `tests/speckit-pro/`; layers and default selection in `suite-manifest.json` |
| typesafe-jev | Go source and Go tests in `typesafe-jev/cmd/evaluate/`; shipped plugin in `typesafe-jev/plugin/` |

## 2. Commands

Run from the repository root (Python 3.11+, Node >= 22.12 and pnpm for docs). A
fresh worktree holds only tracked files; before any docs command, run
`pnpm --dir docs-site install --frozen-lockfile`.

| Check | Command | CI job (required?) |
| --- | --- | --- |
| Quick suite: toolchain, layers 1, 4, 5 (`--layer 1`, `4`, `5`, or `6` for one) | `python3 tests/speckit-pro/run-all.py` | none |
| CI suite: adds layers 6 and 7 (`run-all.py` cannot select 7; `python3 tests/speckit-pro/run-layer-scripts.py --layer 7` runs it alone) | `SPECKIT_SKIP_TOOLCHAIN_CHECK=1 GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null GIT_CONFIG_NOSYSTEM=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/run-ci-suite.json` | `test` (yes, via `validate-plugins`) |
| typesafe-jev Go checks | `python3 scripts/check-go-module.py check` | `go` (yes, via `validate-plugins`) |
| Generated-artifact drift; commit first, since any uncommitted change under its paths fails it | `python3 scripts/refresh-release-artifacts.py --check` | `artifact-consistency` (yes, via `validate-plugins`) |
| PR title | `TITLE='<title>' PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/validate-pr-title-live.json` | `validate-pr-title` (yes) |
| Release-note fence | `PR_TITLE='<title>' PR_BODY='<body>' PR_LABELS_JSON='[]' python3 scripts/compose-release-notes.py --validate-pr` | `validate-release-note` (yes) |
| Docs, reference mode: reference inputs changed | `pnpm --dir docs-site reference:check`, then `pnpm --dir docs-site validate:quality` | `validate-docs` (no) |
| Docs, full mode: `docs-site/`, the artifact gallery, or a docs contract file changed (`scripts/classify-docs-validation.py`) | `pnpm --dir docs-site exec playwright install --with-deps chromium` once, then `pnpm --dir docs-site validate` | `validate-docs` (no) |
| Container preflight: Linux containers rerun the suite when runner, test, or workflow paths change | CI only; its extra requests (`LINUX_REQUESTS` in `tests/speckit-pro/run-container-preflight.py`) also run locally | `container-preflight-linux-amd64`, `-arm64` (yes) |
| Python lint: ruff F, B, and BLE rules (`ruff.toml`); mypy over the `mypy.ini` allowlist (add a module once it passes) | In a virtual environment, `python3 scripts/run-python-lint.py install ruff`, then `run ruff`; the same for `mypy` | `python-lint` (no; built to be required), `mypy-ratchet` (no) |
| Workflow lint | `actionlint` at the version pinned in `pr-checks.yml`, from the repository root. The CI installer (`scripts/install-actionlint.py`) fetches a Linux amd64 binary only | `validate-workflows` (no; it also checks release-PR ancestry, CI only) |
| Ripwire advisory: `--arch`, `--quality-delta` from the merge-base, and `--doc-drift`, reported in the job summary | CI only; `scripts/install-ripwire.py` pins one Linux release by SHA-256. Locally, run the `ripwire .` commands in section 5 | `ripwire-advisory` (no; advisory, never required) |

## 3. Working Rules

Adapted from Andrej Karpathy's agent guidance and this repo's failure patterns.

1. **Surface assumptions before editing.** State them in chat before touching
   files. If a manifest, release, CI, or generated-artifact change is
   ambiguous, ask. If a simpler path might solve the request, name it before
   doing larger work. Stop and describe confusion instead of guessing.
2. **Make the simplest change that solves the task.** Prefer existing repo
   patterns and source-of-truth files over new conventions. If a change feels
   larger than the request, shrink it or explain why the size is necessary.
3. **Keep edits surgical.** Touch only files that directly serve the request.
   Do not reformat adjacent JSON, reorder manifest keys, or clean up unrelated
   comments. Remove only what your change orphans. Match local style.
4. **Verify against a stated goal.** Decide the check before coding. Fix a bug
   red first: add the test that fails on the bug, see it fail, then make it
   pass. Iterate with the smallest useful check, then run the broader gate when
   the changed surface warrants it. If a check cannot run, report the exact
   command and reason.

## 4. Design Rules

These are constraints, not a checklist. When two collide, pick the one with the
lowest future cost in this repository, and name the trade-off in the commit.

### Layers

Each file does one kind of work. Name the layer of the file you edit. Plugin
paths are relative to `speckit-pro/` and `typesafe-jev/`; repository paths are
relative to the root.

| Layer | speckit-pro | typesafe-jev | Repository |
| --- | --- | --- | --- |
| Policy: decides | `speckit_pro_runner/` modules and `gates/` | `cmd/evaluate/` request, backend and update logic (`validation.go`, `config.go`, `fallback.go`, `update.go`) | release and check logic in `scripts/` |
| Contract: states a shape | `speckit_pro_runner/contracts/` schemas, plugin manifests | MCP tool schema in `cmd/evaluate/tools.go`, exit codes in `cmd/evaluate/call.go`, plugin manifests, `plugin/.mcp.json` | marketplace manifests, `release-please-config.json` |
| Guidance: tells an agent what to do | `skills/`, `agents/`, `codex-agents/`, references, hook messages | `plugin/shared-skills/`, tool descriptions | `AGENTS.md`, `REVIEW.md`, `docs-site/` |
| Glue: dispatches | `hooks/`, `codex-hooks.json`, `speckit_pro_runner/helpers/registry.py`, `scripts/` | `cmd/evaluate/main.go`, `plugin/scripts/` | `.github/workflows/`, dispatch scripts |
| Proof | `tests/speckit-pro/` | `cmd/evaluate/*_test.go` | `tests/speckit-pro/layer1-structural/`, including `validate-typesafe-jev-metadata.py` |

### Principles

- **Separation of concerns:** one layer per file. Root principle.
- **Encapsulation:** call another module's public functions; never read its
  private state files or underscore names.
- **Cohesion and coupling:** one rule change touches one owner module, plus its
  tests and its doc.
- **DRY:** one home per rule, threshold, path, schema fact, or message. Search
  before writing (`ripwire . --exemplar="<what>"`). Do not merge code that is
  only similar by coincidence.
- **KISS and YAGNI:** the simplest shape that works; a function before a class;
  no speculative flags, hooks, or frameworks.
- **Single responsibility:** if you describe a unit with "and", split it. Names
  say intent; comments say why.
- **Depend on contracts:** policy takes and returns plain values (dicts,
  dataclasses, Go structs, JSON). It never parses guidance prose to learn a
  rule.
- Composition over inheritance · open/closed only where change has happened
  twice · Law of Demeter · fail fast at the edges, never swallow errors ·
  optimize for deletion · boring tech (each language's standard library
  first).

### Hard invariants

1. **One owner per domain.** Each domain lives in one module, with one doc when
   it has rules, and everything else calls it. Examples: in `speckit-pro`,
   `stop_policy.py` with `references/stop-policy.md`, `host_skills.py`,
   `formal/pins.py` and `canonical_json.py`; in `typesafe-jev`,
   `validation.go` for the one request shape both backends take and
   `config.go` for backend specs; repository-wide, `scripts/pinned_archive.py`
   for pinned downloads. Consolidate a scattered domain before adding to it.
   Extend the owner; a new module needs a stated reason the owner cannot hold
   it. A function-level import that dodges a cycle, or a new
   `.ripwire_arch_rules` violation, means the logic sits in the wrong module.
2. **Never duplicate logic.** On a second use: move the logic to its owner,
   switch every existing caller with tests green and no behavior change, then
   build the new use. List every copy first (`ripwire . --grep=` or a search);
   the move switches all of them, or the commit names each one left and why. A
   new helper beside old copies is one more copy. Each caller keeps its exact
   results; any behavior change is its own commit. The same holds across hosts:
   each plugin keeps one skill source for Claude and Codex (`speckit-pro`
   renders host blocks with `host_skills.py`; `typesafe-jev` ships
   `plugin/shared-skills/` to both). Never add a per-host copy.
3. **No policy in guidance or glue.** Skills, agent prompts, references, hook
   messages, workflows, and docs state or dispatch what policy code decides.
   They never compute a threshold, classify an outcome, or carry a rule the
   code lacks. A rule stated only in prose is a bug: implement it, test it, or
   delete it.

### How to work

- **Refactor first, then change.** Commit a behavior-preserving refactor with
  tests green, then commit the change. Never both in one diff. For a large
  domain, record its outputs as a fixture before the refactor and compare after.
- **Gates, not promises.** A rule that matters gets a check: a layer-1
  validator, a Python or Go test, an arch rule, or a hook. A "never" in this
  file alone protects nothing. Gates and validators fail closed: missing,
  unreadable, or unparseable evidence yields a failure or an explicit unknown,
  never a pass.
- **One source per contract:** when code and a doc state the same request
  shape, threshold, or path, execute the doc's example in a test or derive one
  from the other.
- **Untangle a scattered domain in this order:** measure it (every file holding
  its logic, every copy, every place copies disagree), plan small
  behavior-preserving steps with no new features, one PR each, add the check
  that fails if the mess returns, and measure again with the same numbers. Only
  then build the feature.

## 5. Tools

Two optional tools save reading and tokens. Work on without them; no check may
depend on either.

- **ripwire** (on PATH, one argument per flag): follow the block below. In
  this repo, scope `--quality-delta` to the branch before a PR
  (`--quality-delta=$(git merge-base origin/main HEAD)..HEAD`) and confirm its
  graph with a read. `ripwire . --arch=.ripwire_arch_rules` checks layering
  against `.ripwire_arch_baseline` (exit 2 means a new violation); never
  re-baseline to hide a new edge. Config details and the advisory job:
  `docs/agent-runbook.md`.
- **Jev** (the `typesafe-jev` plugin's `evaluate` tool) gives advisory
  judgments only: its verdict never approves a destructive step, and each call
  bills a third party, so send no secrets or local paths.

### ripwire — deterministic codebase maps (on PATH as `ripwire`)

Reach for it BEFORE blind grep + whole-file reads. First call ~1s cold; after that warm, ~0.1s.

- Orient on a task: `ripwire <dir> --for="<task in words>"` — ranked, quality-annotated
  signatures. Paste symbol/file names from the issue verbatim; named mentions get anchored.
- One task: `--pack-task="<task>" --legend=compact`; before parallel agents: `--plan-lanes=N --task="<goal>"`, then read `lanes[].execution`.
- Have a stack trace / build error: `ripwire <dir> --from-trace=FILE --legend=compact` (`-` = stdin) —
  paste the error, don't paraphrase it into a query.
- Who calls X: `--callers=SYM --legend=compact`. "Is it safe to change X?" needs the full blast radius:
  `--impact=SYM --legend=compact` (transitive) plus `--uses=SYM --legend=compact` (every read/write/import site).
- Apply a whole-symbol edit without a whole-file Read: `--replace-symbol-body=SYM` plus `--edit-payload=FILE|-`
  (or insert-before/after); the receipt carries region, blob_sha, edit_check, tests_to_run + ONE next= — no re-read after it; `--edit-check=SYM --legend=compact` is for a contract question WITHOUT an edit in hand.
- Before writing a new fn/class/helper: `--exemplar="<what you're writing>" --legend=compact` — duplicates are born on small tasks.
- Before calling work done: `--quality-delta --legend=compact` (what you made worse), then `--test-gate --legend=compact`.
- Trust notes: counts marked counts_floor are floors, not totals; a zero means "none found", never "none exists".
- The commands above ask for the compact legend (terse definitions of only the attributes present); add `--legend=full` when a definition's reasoning is needed: a term you do not recognise, a floor or cap you need explained, a map a human will read.

Defaults to break (less context is measurably MORE accurate, not just cheaper — code-repair
accuracy fell 29% -> 3% as context grew 32K -> 256K tokens, LongCodeBench):

- Do NOT open a file you have not located first: rank with `--for`/`--grep`, then read what it names.
- Do NOT read a whole file to understand one symbol: `--expand=SYM --legend=compact` gives the body + callee sigs.
- Do NOT fan reads across several files to learn one thing: `--pack-task="<task>" --legend=compact` is one call.

## 6. Generated and Paired Files

Generated artifacts are a pure function of the source tree. **Regenerate; never
hand-edit or hand-resolve.** If plugin source or payload-affecting files
change, account for the generated artifact contract before calling the work
done. Define the merge driver once per clone (`docs/agent-runbook.md`).

| Output | Regenerate with | Caught by |
| --- | --- | --- |
| `dist/` payloads, marketplace versions, runner hashes (any runner `.py` edit) | `python3 scripts/refresh-release-artifacts.py` | `artifact-consistency` |
| `docs-site/src/content/docs/reference/**`, from plugin sources, READMEs, manifests, `scripts/`, `tests/speckit-pro/` | `pnpm --dir docs-site reference:generate` | `validate-docs` only, not required |
| Spec index blocks in `SPEC-MOC.md` and roadmap MOC files | the `generate-spec-index` runner request (`docs/agent-runbook.md`) | freshness: no PR check |

After `git merge origin/main`, run both regenerate commands above, then the CI
suite. One sanctioned hand edit: if `main` brought in a release and your branch
also changed the runner manifest, set its `plugin_version` to
`speckit-pro/.codex-plugin/plugin.json`'s `version` before the refresh.

Paired files: the `.gitattributes` generated list mirrors
`CHECK_WORKTREE_PATHS` in `scripts/refresh-release-artifacts.py`; `REVIEW.md`
mirrors section 11; `speckit-pro/codex-agents/*.toml` are generated from
`speckit-pro/agents/*.md`.

## 7. Boundaries

- **Never edit:** generated payloads, generated reference pages, or vendored
  upstream content by hand.
- **Ask first:** an ambiguous manifest, release, CI, or generated-artifact
  change (section 3), and `scripts/refresh-local-plugin.py` (section 8).
- **Keep out of the repo:** `test-privacy-scan.py` rejects non-allowlisted
  emails, home paths, Claude and macOS temp paths, raw UUIDs, and local
  identity terms in non-ignored files; use repo-relative placeholders.
- **Git:** bring `main` in by merge, then regenerate (section 6).
- **Dependencies:** shipped plugin code (`speckit-pro/`, `typesafe-jev/plugin/`,
  `dist/`) and the default local suite stay on the Python 3.11+ standard
  library. A dev or test package must meet every condition of constitution II
  (`scripts/run-python-lint.py` is the pattern). Go is for `typesafe-jev/`
  only; the scripts and tests that build, check, and release it stay Python.
  Add no active repository Bash or `jq` dependency outside existing workflow
  dispatch glue and fixed vendored boundaries.
- **Names:** name repository scripts and tests for durable behavior, never a
  temporary spec ID. Test code never reads a `specs/<feature>/` path from disk
  (`tests/speckit-pro/AGENTS.md`).

## 8. Gotchas

- Files listed in `gates/active_path_guard/repo_bash.py`, this one included,
  must not instruct `bash`, `sh`, or `jq`; use `python3`.
- Live sessions run the installed plugin; `claude --plugin-dir
  dist/claude/speckit-pro` tests a refreshed `dist/`. Ask before
  `scripts/refresh-local-plugin.py` (`--dry-run` previews): it rebuilds `dist/`,
  reinstalls user-scope plugins, and stops if a marketplace points elsewhere,
  even at the main checkout.
- speckit-pro skills run only in a scratch clone marked with
  `git config speckit-health.scratch true`; a repo hook blocks them everywhere
  else (ADR 0002). Setup and Codex hook trust: `docs/agent-runbook.md`.

## 9. Pull Requests

- Title: `<type>(<lowercase-scope>): <plain English description>`, one of feat,
  fix, chore, docs, refactor, test. Validate the exact final title with the PR
  title gate (section 2) before creating a PR or marking it ready.
- Open every PR with the official `gh-stack` skill installed at user scope,
  even one PR (`docs/agent-runbook.md`). `gh stack submit --auto` opens a draft
  with a guessed title and the template body; set the title and fence with
  `gh pr edit`, then mark it ready. A draft skips every other PR Checks job,
  yet `validate-plugins` passes. One concern per PR.
- Work with dependent parts is a stack: plan the layers, then `gh stack init`
  before writing code, one concern per layer, foundations at the bottom.
  Unrelated work gets its own stack off `main`. Merge with
  `gh stack merge <pr> --yes`, never `gh pr merge`.
- Only `feat` and `fix` PRs fill the `release-note` fence, required unless
  labeled `release-note/skip`; any unlabeled fence is published.

## 10. Definition of Done

- Generated outputs are committed with their source; `--check`, both suites,
  and required checks pass, as do docs checks and actionlint when their inputs
  changed.
- When Python changed, ruff and mypy pass locally too; `mypy-ratchet` is not
  required, so CI will not stop a regression.
- Every rule you relied on that was missing here is added, or the PR says why.

## 11. Code Review Rules

Codex reads this section during review. Claude Code's managed Code Review reads
the root `REVIEW.md`, which states the same rules in fuller form. Keep the two
in step.

- **Blocking:** manifest or version drift; plugin source changed without
  accounting for the generated artifact contract; malformed loader frontmatter;
  shipped code or the default suite leaving the Python 3.11+ standard library,
  a dev-only package that breaks constitution II (Go belongs to `typesafe-jev/`
  only), or a new active Bash or `jq` dependency outside the allowed
  boundaries; a workflow that exposes secrets or elevated permissions to
  untrusted PR content; a script or test filename coupled to a temporary spec
  ID, or test code that reads a `specs/<feature>/` path from disk at run time;
  a correctness bug in repository tooling or tests, such as a check that passes
  on nothing.
- **Minor:** style, naming, prose, and refactoring notes; add none on re-review.
- **Skip:** generated reference pages and payloads, vendored upstream content,
  lockfiles, archived specs, and what CI enforces (only the `ruff.toml` rules F,
  B, BLE that `python-lint` runs). Cite `file:line` for any behavior claim.

## 12. Read When Relevant

| When you are | Read |
| --- | --- |
| Editing plugin source, tests, or the docs site | the scoped `AGENTS.md` in `speckit-pro/`, `tests/speckit-pro/`, or `docs-site/` |
| Merging `main`, opening a PR, or tuning ripwire | `docs/agent-runbook.md` |
| Reviewing a PR | `REVIEW.md` |
| Preparing a release or changing PR checks | `docs-site/src/content/docs/contribute-and-release.md` |
| Adding a dependency or script | `.specify/memory/constitution.md` (principle II) |

## 13. Agent File Hygiene

- `AGENTS.md` is the only authored agent-instruction source in each scoped
  directory. `GEMINI.md` files only import the sibling `AGENTS.md`.
- Do not add a `CLAUDE.md`: Claude Code reads `AGENTS.md` directly. Put
  Claude-only guidance in your own `~/.claude/rules/`, not in this repository.
- `REVIEW.md` lives only at the root and is injected verbatim into review
  agents. It does not expand `@` imports, so write rules into it directly.
- No feature plans, release notes, implementation transcripts, or detailed
  process history in agent files. Add a rule when an agent repeats a mistake;
  prune one that no longer earns its line.

## 14. Agent skills

- **Issue tracker:** GitHub Issues via `gh`; PRs open through `gh stack`. See
  `docs/agents/issue-tracker.md`.
- **Triage labels:** the five default role labels. See
  `docs/agents/triage-labels.md`.
- **Domain docs:** single-context (root `GLOSSARY.md`, `docs/adr/`). See
  `docs/agents/domain.md`.

# Review instructions

This repository is a public Claude Code and Codex plugin marketplace. The
shipped plugin lives under `speckit-pro/`, repository-only validation under
`tests/speckit-pro/`, and the documentation site under `docs-site/`. Calibrate
to that shape: most files are Markdown instructions and Python validation, and
several trees are generated rather than authored.

## What Important means here

Reserve Important for findings that would break behavior for a plugin consumer,
break the generated-artifact contract, or expose the repository:

- Invalid JSON or manifest drift: a `plugin.json` version that disagrees with
  the marketplace entry, or a package missing from `release-please-config.json`
  or `.release-please-manifest.json`.
- A change to plugin source or payload-affecting files that does not account for
  the generated artifact contract, leaving generated output stale.
- A skill, command, or agent whose frontmatter its loader requires is missing or
  malformed.
- Repository-owned tooling that leaves the Python 3.11+ standard library, or a
  new active Bash or `jq` dependency outside existing workflow dispatch glue and
  the fixed vendored boundaries.
- A workflow change that grants `pull_request_target` write access to untrusted
  content, unpins a third-party action, or exposes a secret to a fork PR.
- A repository-authored script or test whose filename is coupled to a temporary
  spec ID rather than durable behavior, or whose code reads a `specs/<feature>/`
  path from disk at run time. Archive cleanup deletes that folder once the
  feature merges, so the read passes review and fails months later in an
  unrelated cleanup branch. Asserting such a path as a string is fine; opening
  one is not.

Style, naming, prose, and refactoring suggestions are Nit at most.

## Cap the nits

Post only the Nits worth a reader's time, and roll the rest into one "plus N
similar items" line in the summary rather than posting them inline. Prose and
config files can be polished indefinitely.

## Do not report

- Anything CI already enforces: lint, formatting, type errors, spellcheck.
- Generated reference pages under `docs-site/src/content/docs/reference/`,
  installed-cache proofs, generated payloads, and vendored upstream content.
  Flag the source or generator instead.
- Lockfiles.
- `CHANGELOG.md` and version fields owned by release automation.
- Archived spec artifacts under `specs/`. Those are historical records, not
  shipped behavior.

## Always check

- If files under `tests/speckit-pro/` change, `suite-manifest.json` still
  selects them.
- Deterministic ordering is preserved anywhere reference content is generated.
- Docs commands stay rooted: `pnpm --dir docs-site <script>` from the repository
  root, not a bare command inside `docs-site/`.
- Agent instruction files stay within their contract: `AGENTS.md` is the only
  authored source per scoped directory, and `CLAUDE.md` and `GEMINI.md` only
  import their sibling.

## Verification bar

Claims about behavior need a `file:line` citation in the source, not an
inference from a file, skill, or symbol name. If you cannot point at the line,
do not post the finding.

## Re-review convergence

After the first review of a PR, suppress new Nits and post Important findings
only. A one-line follow-up commit should not draw a fresh round of style notes.

## Summary shape

Open the review body with a one-line tally such as `2 important, 4 nits`. When
nothing blocking was found, lead with "No blocking issues."

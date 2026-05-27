# racecraft-plugins-public security rules

These rules are specific to this repo's attack surfaces. The plugin ships to all
marketplace consumers on every merge to main — mistakes here have wide blast radius.

---

## Shell injection through LLM-generated content

The autopilot, coach, and scaffold-spec skills all generate commit messages, PR
titles, and branch names from LLM output (spec names, review summaries, phase
descriptions). That output flows into shell commands. Rules:

- **Commit messages must use heredoc form**, never inline `-m "$(...)"`.**
  Correct:
  ```bash
  git commit -m "$(cat <<'EOF'
  feat(SPEC-XXX): <message here>
  EOF
  )"
  ```
  Wrong: `git commit -m "feat: address review - $summary"` where `$summary` is
  LLM-generated. If `$summary` contains a double-quote or backtick the shell
  expands it.

- **Branch names derived from spec names must be sanitized before use.**
  Strip everything except `[a-z0-9-]` — never pass a raw spec name directly to
  `git checkout -b` or `git worktree add`. The spec name comes from the user's
  technical roadmap and can contain slashes, quotes, or parens.

- **`specify extension add <id>` where `<id>` comes from user chat must be
  treated as untrusted input.** The coach's Play 3 confirms before running, but
  the confirmation must show the literal command, not a reformatted version.
  Never interpolate the id into a compound `&&` chain without quoting:
  ```bash
  specify extension add "$extension_id"   # correct — quoted
  ```

---

## PR body and `gh api` payloads with user-controlled content

The `generate-pr-body.sh` and `speckit-resolve-pr` skill construct PR bodies and
GraphQL mutations from spec file content and PR review comment text. Rules:

- **Always use `--body-file` for `gh pr create`, never `--body "$(cat ...)"`.
  The `generate-pr-body.sh` pattern is correct — keep it.** Inlining file content
  into `--body` embeds newlines and quotes into a shell word, breaking the command.

- **`gh api` GraphQL mutations for resolving review threads embed PR comment
  body text into the `body:` field.** If a reviewer writes a comment containing
  a backtick or double-quote in a GraphQL string context, the mutation will fail
  or behave unexpectedly. Escape or JSON-encode the body string before embedding:
  ```bash
  body_json=$(jq -Rn --arg b "$comment_body" '$b')
  ```
  Do not use `echo "$comment_body"` inline inside a `-f query='mutation ...'` call.

- **`git commit -m "fix: address review - $summary"` where `$summary` is extracted
  from a PR review comment is injection-prone.** Extract the summary into a temp
  file and use `--file` or heredoc form.

---

## `generate-pr-body.sh` heredoc — verified safe, pattern to preserve

The `<<EOF` heredoc in `generate-pr-body.sh` that embeds `$what`, `$why`, and
`$non_goals` (extracted from `spec.md`) is safe as-is. Bash performs single-level
expansion: `$what` is substituted with its current string value, but bash does NOT
re-parse or re-execute command substitutions that appear inside that value. A spec
containing `$(date)` in its Summary section will produce the literal text `$(date)`
in the PR body, not a timestamp.

- Do NOT change the heredoc to `<<'EOF'` — it would break the intentional variable
  expansions (`$FEATURE_DIR`, `${surfaces:-unknown}`, etc.) that the script relies on.
- Preserve the `\`` escaping already in the template for markdown backtick code spans.
  In an unquoted heredoc, `\`` prevents backtick command substitution — remove the
  backslashes and you create real execution points.

---

## Eval fixture integrity (prompt injection attack surface)

The Layer 2/3/7 fixture files (`tests/layer2-trigger/*.json`, `tests/layer3-functional/*.json`,
`tests/layer7-integration/*/expected.json`) contain query strings that are passed
directly to `claude -p`. An adversary with write access to these files could embed
prompt-injection instructions that alter eval outcomes or exfiltrate context.

- Never commit eval fixture content that includes jailbreak patterns, instructions
  for ignoring system prompts, or references to `<system-reminder>` or
  `<local-command-caveat>` tags.
- When reviewing fixture PRs, check that new `"query"` fields look like genuine
  user queries, not multi-paragraph instruction blocks.
- The `scrub-transcript.sh` `TRANSCRIPT_SCRUB_EXTRA_REGEX` env var is passed to
  `jq`'s `gsub()`. Malicious regex in this variable can crash the scrubber or
  strip assertions the parser depends on. Treat it as untrusted if set outside
  the test environment.

---

## Marketplace manifest and release pipeline trust

The `.claude-plugin/marketplace.json` and `release-please-config.json` are the
trust anchors for every plugin consumer. Rules:

- **No credentials, tokens, or API keys in any `.json` or `.md` file under
  `.claude-plugin/`.** These files are public and are synced on every
  `/plugin marketplace update` by consumers.
- **The `scripts/sync-marketplace-versions.sh` script runs as `github-actions[bot]`
  with `contents: write` on the main branch.** Any change to this script or
  `.github/workflows/release.yml` is a privilege-escalation surface — review
  these files with the same scrutiny as a production secrets handler.
- **Plugin `plugin.json` files must not include executable content** (no `eval`,
  no inline scripts, no `command:` fields outside of `hooks/hooks.json`). Hook
  command strings in `hooks.json` must always quote `${CLAUDE_PLUGIN_ROOT}` to
  handle install paths that contain spaces.

---

## Temp file handling in scripts

- Always pair `mktemp` with a `trap 'rm -f "$tmpfile"' EXIT`. The `generate-pr-body.sh`
  script already does this — maintain the pattern in any new script that uses temp files.
- Never use a hardcoded `/tmp/fixed-name` temp file in scripts that could run
  concurrently (e.g., parallel eval runners). `mktemp` prevents cross-test
  contamination and TOCTOU races.

---

## `jq -r` output in shell loop variables

Several test scripts (`run-dispatch-fixtures.sh`, `run-return-format-fixtures.sh`,
`run-e2e-fixtures.sh`) pipe `jq -r` output into `while read -r`, `mapfile`, and
`done < <(...)` constructs. If a fixture JSON value contains a newline, it will
split across loop iterations unexpectedly.

- Fixture string values that represent single identifiers (subagent types, skill
  names) should not contain newlines — validate this in the Layer 1 structural
  test rather than assuming.
- When using `jq -r` output in a shell comparison (`[[ "$var" == "$expected" ]]`),
  always double-quote both sides.

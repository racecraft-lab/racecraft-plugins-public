# racecraft-plugins-public security rules

These rules are specific to this repository's attack surfaces. Plugin source and
generated payloads reach marketplace consumers, so execution, filesystem, and
release boundaries require reviewable structured inputs.

---

## Untrusted content at process boundaries

Autopilot, coach, and scaffold workflows can derive commit messages, PR titles,
branch names, extension IDs, and review summaries from user or model text. Treat
all such values as untrusted.

- Build subprocess arguments as Python lists and call `subprocess.run()` with
  `shell=False`. Never concatenate untrusted text into a command string or opt
  into `shell=True`.
- Pass commit messages and other multiline values as one argv element or through
  a dedicated file option such as `git commit --file <path>`.
- Normalize branch-name components to the documented allowlist before passing
  them to `git switch`, `git checkout`, or `git worktree` as one argv element.
- Validate extension IDs and other selectors against the expected identifier
  grammar. Show the exact planned argv to the user before a side effect that
  originated from chat input.
- Keep display strings separate from execution values. Escaping text for a log
  or Markdown report does not make it safe for a process boundary.

---

## PR bodies and GitHub API payloads

The current PR-body path is the `generate-pr-body` runner helper in
`speckit-pro/speckit_pro_runner/helpers/pr_emission.py`. It creates structured
mutation operations and writes through the runner's bounded mutation layer.

- Keep multiline PR content in the helper-generated body file and pass that file
  to `gh pr create --body-file <path>`.
- Encode GraphQL variables and REST payloads with Python standard-library
  `json.dumps()` or a structured JSON input file. Do not interpolate review
  comments or spec text into a GraphQL query string.
- Validate PR titles against the repository's Conventional Commit policy before
  emission. Treat review comments as data, not command fragments.
- `gh --jq` is a GitHub CLI query option and does not require the external `jq`
  executable. Repository JSON processing uses Python standard-library parsing.

Historical context: earlier releases used `generate-pr-body.sh`, shell heredocs,
and external `jq` encoding. Those implementations were retired during the
Python runtime migration and are archival evidence, not current guidance.

---

## Eval fixture integrity

Layer 2, 3, and 7 fixture files contain query strings consumed by Python eval and
integration runners. A contributor with write access could add prompt-injection
content that changes outcomes or exposes context.

- Reject fixture content that asks the model to ignore system instructions,
  contains jailbreak patterns, or references internal reminder/control tags.
- Review new `query` fields as user requests. Multi-paragraph control
  instructions require explicit security review.
- Keep transcript fixtures free of credentials, raw personal paths, and other
  secrets even when a scrubber is expected to run later.
- `tests/speckit-pro/layer7-integration/scrub-transcript.py` compiles
  `TRANSCRIPT_SCRUB_EXTRA_REGEX` with Python `re`. Invalid or adversarial
  expressions can abort processing or remove assertion data, so the value stays
  untrusted outside controlled test runs.

Historical context: the transcript scrubber and replay runners previously had
shell and external-`jq` predecessors. The active implementations are Python.

---

## Marketplace and release trust boundaries

The marketplace manifests, plugin manifests, generated payloads, and release
workflow are trust anchors for consumers.

- Never place credentials, tokens, or API keys in marketplace, plugin, docs, or
  generated payload files.
- Parse JSON with Python's `json` module and verify expected object/list/string
  types before comparing or writing values. Regex and line-oriented matching are
  not substitutes for structured parsing.
- `scripts/sync-marketplace-versions.py` is the authoritative marketplace version
  synchronizer. Changes to it or `.github/workflows/release.yml` receive the same
  scrutiny as other write-capable release automation.
- Do not hand-edit generated payloads or installed caches. Change authoritative
  source and regenerate through the owning Python command.
- Plugin manifests must not smuggle executable content. Where a host hook schema
  requires a command string, keep it static, quote `${CLAUDE_PLUGIN_ROOT}`, and
  never interpolate user-controlled values.
- Preserve the boundary between repository source, generated distribution,
  installed cache, and user configuration. A successful check at one boundary
  does not establish trust at another.

---

## Temporary files and atomic replacement

- Use Python `tempfile` APIs or a unique same-directory temporary path for
  intermediate files. Context managers and `finally` cleanup must cover both
  success and failure.
- Use `os.replace()` for atomic replacement after content is fully written and
  flushed. Re-check trust-root and symlink constraints immediately before the
  replace when the destination is security-sensitive.
- Never use a fixed name under `/tmp` or another shared temporary directory.
  Concurrent runs must not share an intermediate path.
- Restrict temporary data to the minimum required content and lifetime. PR
  bodies, transcripts, and generated manifests can contain sensitive repository
  context even when they contain no credentials.
- Validate that every requested output remains beneath its declared trust root;
  reject path traversal, unexpected symlinks, and parent/child write conflicts.

---

## Structured data and identifier validation

- Parse JSON once, validate its schema-relevant types, and iterate the resulting
  objects directly. Do not convert JSON arrays into line-delimited command input.
- Reject identifiers containing newlines, control characters, or values outside
  the documented grammar before they reach filenames, branch names, helper IDs,
  or command plans.
- Preserve JSON strings as data even when they contain quotes, backticks, or
  newlines. Safety comes from structured serialization and argv boundaries, not
  manual escaping.
- Report malformed input with bounded diagnostics that do not echo secrets or
  entire untrusted payloads.

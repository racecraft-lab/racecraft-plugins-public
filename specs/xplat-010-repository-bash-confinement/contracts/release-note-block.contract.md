# Contract: Release Note Block + Composer I/O (FR-021 / FR-023 / FR-024)

Machine-parseable grammar for the consumer-facing Release note block that each
feat/fix PR carries, plus the composer's discovery, harvest, sanitization, and
release-body-write contract. Frozen by Clarifications Session 3.

## 1. Block grammar (in a PR body)

- **Exactly one** fenced code block whose info-string is `release-note`. Zero or
  more-than-one block fails the `validate-release-note` check.
- Fence matching is **CommonMark-nesting-aware**: same fence character; the
  closing run length is no shorter than the opening run. A single anchored match
  is required; zero or ambiguous matches are treated identically to a missing
  block; the composer never attempts partial repair of a malformed fence.
- Body: multiline plain-English prose written for plugin consumers.
- **Allowed inline markdown (explicit subset):** emphasis, plain inline links,
  and `-` bullets.
- **Empty or whitespace-only** content counts as **missing**.
- **Skip** is expressed **only** by the `release-note/skip` label — never by an
  in-block sentinel.
- `.github/pull_request_template.md` seeds the empty block under a
  `## Release note` heading.

Example:

    ## Release note

    ```release-note
    The estimate-spec-size scoping helper is back. `grill-me` and `speckit-prd`
    can size a spec again before you start.
    ```

## 2. Composer sanitization (applied at composition, exceeding a raw-HTML strip)

- Raw HTML stripped entirely.
- Image markdown (`![...]()`) stripped entirely.
- Leading structural characters (`-`, `*`, `#`) on extracted lines neutralized so
  a block cannot inject spurious Markdown structure into the composed body.
- Plain inline links permitted (recorded decision, not an oversight).
- Blocks capped at **2,000 characters** — truncate-and-mark, **not** a check
  failure.
- Intake is env-var / JSON-only via stdlib `urllib` against the GitHub API; PR
  body text is **never** shell-interpolated or git-log parsed.

## 3. Composer discovery + write (FR-023)

- **Discovery:** GitHub Compare API `GET .../compare/{prev_tag}...{new_tag}` (no
  checkout). Previous tag read from the release action's body-output compare-link
  heading. Each PR number is extracted from the trailing `(#N)` on every commit
  subject; the same subject parse yields the conventional-commit type, so only
  feat/fix commits cost a follow-up `pulls/{N}` fetch to harvest the block.
- **The composer MUST NOT** parse the release body's rendered Markdown links to
  discover PR numbers (that link markup is an internal, overridable
  release-please rendering detail).
- **Fail loud, never silently under-enumerate,** on: a Compare API error, a
  truncated/paginated compare response, or a commit subject with no resolvable
  trailing `(#N)`. Emit a structured `release_note_composition_failed` outcome.
- **Harvest scope:** every merged PR since the last tag regardless of type
  (defensive parsing on every body); FR-022 only shape-gates feat/fix PRs.
- **Body write:** resolve the release id by tag (`GET .../releases/tags/{tag}` —
  the release action exposes no id output), then `PATCH .../releases/{id}` with
  the composed body. Highlights on top; the verbatim conventional-commit list as
  an appendix.
- **Idempotent:** the appendix always derives from the release action's body
  output, never from the live release body, so re-runs reproduce a byte-identical
  composed body; on re-dispatch without a new release the gate is false and the
  job is skipped.

## 4. Fallback ladder (Highlights)

| Condition | Highlights behavior | Appendix |
|-----------|---------------------|----------|
| feat/fix PR with a block | plain-English highlight from the block | present |
| `release-note/skip`-labeled PR | omitted from Highlights | still listed |
| feat/fix PR missing a block, no skip label | degrade to de-prefixed PR title | present |
| zero PRs in range carry blocks | all Highlights degrade to de-prefixed subjects | always present |

## 5. Token + job scope (FR-024)

- The composer runs as its **own** `release.yml` job (`needs:` the publishing
  job; gated on the `speckit-pro--release_created` output) carrying
  `permissions: {contents: write}` only. A job-level permissions block overrides
  (does not merge with) the workflow-level grant, so the composer never inherits
  the publishing job's `actions: write` / `pull-requests: write`.
- `contents: write` is both floor and ceiling for the release-body `PATCH`; no
  narrower built-in scope exists.
- The elevated `RELEASE_PLEASE_TOKEN` is **forbidden** — its sole purpose is the
  branch-protection recursion-guard escape.
- No LLM calls; no new secrets; CHANGELOG.md stays the machine-generated ledger.
- **Guard-rail (record near the appendix-embedding code):** the appendix is fed
  only by the release action's `body` output; discovery is Compare-API-only.
  Neither path depends on release-please's `changelog-notes-type`, so that
  setting needs no pin — do not couple the composer to it.

## 6. validate-release-note check semantics (FR-022)

- Events: `opened, reopened, synchronize, edited, labeled, unlabeled,
  ready_for_review` (labeled/unlabeled re-report on skip-label changes).
- Scope: releasable conventional-commit types only — `feat`/`fix` including
  scoped and `!`-breaking forms; `chore`/`docs`/`refactor`/`test` pass trivially
  (mirrors release-please's releasable rule so check and release trigger never
  disagree).
- Draft PRs skipped. release-please's own PRs exempt (chore short-circuit +
  `autorelease:` label; title from `inputs.pr_title` under the dispatch path,
  which carries no body).
- PR body handled via environment variables, never shell-interpolated.
- This is a **NEW required status check name** — the landing PR (PR 12) MUST call
  out the manual branch-protection addition of `validate-release-note` and MUST
  create the `release-note/skip` label (verified absent today).

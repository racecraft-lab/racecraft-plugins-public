# Contract: Release Note Block + Composer I/O (FR-021 / FR-023 / FR-024)

Machine-parseable grammar for the consumer-facing Release note block that each
feat/fix PR carries, plus the composer's discovery, harvest, sanitization, and
release-body-write contract. Frozen by Clarifications Session 3 and hardened by
the PR 12 implementation review.

## 1. Block grammar (in a PR body)

- **Exactly one** fenced code block whose info-string is `release-note`. Zero or
  more-than-one block fails the `validate-release-note` check.
- Fence matching is **CommonMark-nesting-aware**: same fence character; the
  closing run length is no shorter than the opening run. A single anchored match
  is required; zero or ambiguous matches are treated identically to a missing
  block; the composer never attempts partial repair of a malformed fence.
- Body: multiline plain-English prose written for plugin consumers.
- **Allowed inline markdown (explicit subset):** emphasis and plain inline
  links. Lines beginning with `-`, `*`, or `#` are accepted as input text but
  escaped during composition, so they do not retain list or heading structure.
- **Non-empty after sanitization:** empty or whitespace-only extracted content
  counts as **missing**. Content that is syntactically present but is reduced to
  empty/whitespace after the Section 2 sanitizer removes raw HTML and images is
  invalid. The required check MUST fail it, and defensive composition MUST fail
  loud instead of silently converting it into a fallback.
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
- Extraction, sanitization, trimming, and the non-empty check form one canonical
  pipeline shared by `--validate-pr` and composition. An HTML-only, image-only,
  or HTML-plus-image block MUST fail validation for feat/fix PRs and MUST fail
  composition if it somehow reaches the release range.
- Intake is env-var / JSON-only via stdlib `urllib` against the GitHub API; PR
  body text is **never** shell-interpolated or git-log parsed.

## 3. Composer discovery + write (FR-023)

- **Discovery:** GitHub Compare API `GET .../compare/{prev_tag}...{new_tag}` (no
  checkout). Previous tag read from the release action's body-output compare-link
  heading. Each PR number is extracted from the trailing `(#N)` on every commit
  subject. Every discovered PR is fetched and parsed defensively; the same
  subject parse yields the conventional-commit type used for enforcement and
  title-fallback behavior, not for fetch eligibility.
- **The composer MUST NOT** parse the release body's rendered Markdown links to
  discover PR numbers (that link markup is an internal, overridable
  release-please rendering detail).
- **Fail loud, never silently under-enumerate,** on: a Compare API error, a
  truncated/paginated compare response, or a commit subject with no resolvable
  trailing `(#N)`. Emit a structured `release_note_composition_failed` outcome.
- A single unpaginated Compare response is complete only through **250 commits**.
  Exactly 250 is accepted when `total_commits` agrees; 251, a larger advertised
  total, or any pagination link fails loud rather than publishing partial notes.
- **Harvest scope:** every merged PR since the last tag regardless of type
  (defensive parsing on every body); FR-022 only shape-gates feat/fix PRs.
- **Immutable capture:** before composition, a dedicated capture job records the
  raw release-action body, complete Compare response, and every discovered PR's
  body and labels as canonical JSON. It uploads that JSON once with
  a SHA-pinned `actions/upload-artifact` release with v4-or-later immutable
  artifact semantics, records both the action-provided artifact digest and an
  independently computed lowercase SHA-256 of the canonical JSON, and exports
  the artifact identity to the composer job.
- **Body write:** the composer downloads that artifact, verifies both digests,
  and uses it as its only composition input. It MUST NOT re-fetch Compare or PR
  metadata. It resolves the release id by tag (`GET .../releases/tags/{tag}` —
  the release action exposes no id output), then `PATCH`es Highlights,
  `## Commit appendix`, and the exact snapshotted raw action body.
- **Immutable replay:** a failed composer-job rerun in the same workflow run
  downloads the same immutable artifact and therefore PATCHes byte-identical
  body bytes even if PR bodies, titles, or labels later change. Snapshot absence,
  canonicalization drift, or either digest mismatch fails loud and is never
  partially repaired. Recovery is a failed-job rerun, not a fresh dispatch.
- **Byte-idempotent scope:** identical canonical snapshot bytes produce identical
  UTF-8 release-body bytes. A fresh workflow dispatch with no new release remains
  gated off; re-fetching mutable PR metadata is explicitly outside the contract.
- **Audit evidence:** the immutable input artifact is the exact body/PR evidence
  of record. Structured success output and `GITHUB_STEP_SUMMARY` MUST identify
  artifact id/name, artifact digest, canonical snapshot digest, composed-body
  SHA-256 and UTF-8 byte count, tag, previous tag, release id, commit/PR count,
  and run id/attempt. They MUST NOT log tokens, raw PR bodies, or unsanitized
  block text. The published release supplies the body corresponding to the
  recorded composed-body digest; any later body edit is detectable by re-hash.

## 4. Fallback ladder (Highlights)

| Condition | Highlights behavior | Appendix |
|-----------|---------------------|----------|
| PR with one sanitized non-empty block | plain-English highlight from the block | present |
| `release-note/skip`-labeled PR | omitted from Highlights | still listed |
| feat/fix PR missing a sanitized non-empty block, no skip label | immutable commit-subject fallback | present |
| zero PRs in range carry sanitized non-empty blocks | every non-skipped commit uses the immutable commit-subject fallback | always present |

The fallback MUST use the Compare API commit subject already bound to the tag
range, never the mutable PR title. Remove its trailing `(#N)` marker and
conventional-commit prefix, then trim it. The rendered fallback has a hard
**250-character** ceiling: lengths through 250 are unchanged; a longer fallback
is the first 247 characters plus ASCII `...`, for a total length of 250. If
de-prefixing would produce an empty value, use the subject with only `(#N)`
removed and apply the same boundary. Tests MUST pin 249-, 250-, and
251-character cases.

## 5. Token + job scope (FR-024)

- The composer and capture run as their **own** `release.yml` jobs, both gated on
  the mapped `speckit-pro--release_created` output. Capture carries only
  `contents: read`; composer `needs:` publishing plus capture and carries only
  `contents: write`. A job-level permissions block overrides the workflow-level
  default, so neither job inherits `actions: write` or `pull-requests: write`.
- `contents: read` covers capture-time Compare and PR reads. `contents: write`
  covers composer-time release lookup and body PATCH and is the composer's
  complete floor/ceiling map. Artifact upload/download uses the Actions runtime
  token and adds no repository permission. Unspecified permissions remain
  `none`.
- The elevated `RELEASE_PLEASE_TOKEN` is **forbidden** — its sole purpose is the
  branch-protection recursion-guard escape.
- The workflow-level default is `permissions: {}`. The publishing job keeps its
  separate exact map (`actions: write`, `contents: write`,
  `pull-requests: write`); those grants do not flow into the composer.
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
- All untrusted event text, including PR body and dispatch-path title, is passed
  through environment variables, never shell-interpolated.
- The workflow-level default remains `permissions: {}`. This check's job grants
  only `contents: read` for checkout, and checkout uses
  `persist-credentials: false`; the validator performs no API mutation.
- This is a **NEW required status check name** — the landing PR (PR 12) MUST call
  out the manual branch-protection addition of `validate-release-note` and MUST
  create the `release-note/skip` label (verified absent today).

# Contract: `sweep-pr-feedback` read-only runner operation

**Feature**: `art-008-feedback-sweep` | **Date**: 2026-08-20

The one external interface this slice adds. Registered beside
`resolve-autopilot-stage` in `speckit-pro/speckit_pro_runner/helpers/`.

**Mode**: `read_only`. **Promotion status**: `python_authoritative`.
**Bash ancestor**: none — this is new behavior, so the helper joins
`NO_BASH_ANCESTOR` and `registry.py` records `None` for the script with
`python_only` as the comparison mode.

**It reports and never decides.** It runs no `gh`, touches no network, writes no
file, and assigns no class. Classification is orchestrator judgment over this
envelope, because `amended` is what routes an item into consensus.

---

## Request

```json
{
  "schema_version": "1.0",
  "request_id": "<caller-supplied>",
  "helper_id": "sweep-pr-feedback",
  "operation": "sweep-pr-feedback",
  "mode": "read_only",
  "inputs": {
    "workflow_file": "docs/ai/specs/.process/ART-008-workflow.md",
    "self_login": "<the account this run authenticated as>",
    "pr_observation": {
      "ok": true,
      "comments": [
        {
          "id": "IC_kwDO...",
          "surface": "pr_conversation",
          "author": "octocat",
          "author_association": "OWNER",
          "body": "Artifact: Implementation Plan\nFeature: ART-008\n\nObjections recorded while reviewing this plan.\n\nPhase / Registry  (#phase-2)\nThe registry should cover every exporting template.",
          "truncated": false
        },
        {
          "id": "PRRC_kwDO...",
          "surface": "review_thread",
          "author": null,
          "author_association": "CONTRIBUTOR",
          "body": "Drive-by suggestion.",
          "truncated": false,
          "thread_resolved": false
        }
      ]
    }
  }
}
```

### Input rules

| Field | Required | Rules |
|---|---|---|
| `workflow_file` | Yes | Repo-relative. Read for the Feedback Sweep Log, to derive the FR-009 skip set. A file with no such table yields an empty skip set, which is the first-sweep case. |
| `self_login` | Yes | The authenticated account. The second half of the FR-006 self-reply test. |
| `pr_observation` | Yes | The orchestrator's observation, passed as data. |
| `pr_observation.ok` | Yes | Must be the JSON literal `true`. A truthy non-`true` value is not a successful read, following the precedent in `observation_pull_requests`. |
| `pr_observation.comments` | Yes | Array. Empty is valid and usable — it is the clean-sweep case, not an error. |

### Preconditions the helper validates

- **Body budget.** Every `body` must be at most **8192 bytes** as UTF-8. A body
  over budget returns an `invalid_input` diagnostic naming the offending
  comment id. The helper does not silently re-truncate.

  This is a validation rather than a transformation because the runner enforces
  `BOUNDED_TEXT_INPUT_BYTES = 32 * 1024` per string, and `iter_input_strings`
  recurses fully into nested dicts and lists. One oversized body therefore
  rejects the **whole request before this helper runs**. The orchestrator must
  truncate at capture time and set `truncated`; the helper's job is to make a
  missed truncation fail loudly with a comment id attached instead of opaquely
  at the boundary with only a field path.

- **Closed enums.** `surface` must be `review_thread` or `pr_conversation`.
  `author_association` must be one of the eight GitHub values. A ninth value is
  a malformed observation, not an untrusted author, and returns
  `invalid_input`.

- **No shell path.** No field of this request is ever interpolated into a
  command string, in either direction (FR-004b, SC-009). The request arrives on
  stdin as one JSON document.

---

## Response

```json
{
  "schema_version": "1.0",
  "request_id": "<echoed>",
  "status": "ok",
  "exit_code": 0,
  "data": {
    "stdout_json": {
      "tool": "sweep-pr-feedback",
      "surfaces_read": ["review_thread", "pr_conversation"],
      "counts": {
        "observed": 2,
        "candidates": 1,
        "excluded": 1
      },
      "candidates": [
        {
          "id": "IC_kwDO...",
          "surface": "pr_conversation",
          "author": "octocat",
          "author_association": "OWNER",
          "truncated": false,
          "export": {
            "template_id": "implementation-plan",
            "template_ambiguous": false,
            "kind": "markdown",
            "matched_line": 4,
            "anchors": ["phase-2"]
          }
        }
      ],
      "excluded": [
        {
          "id": "PRRC_kwDO...",
          "surface": "review_thread",
          "reason": "untrusted_author"
        }
      ]
    }
  }
}
```

### Output rules

- **`candidates`** — trusted, unrecorded, non-self-reply comments, in the order
  observed. `export` is `null` when no registered line matched.
- **`excluded`** — every set-aside comment with exactly one `reason` from the
  closed set: `untrusted_author`, `self_reply`, `already_logged`,
  `thread_resolved`. **Every exclusion is reported**, so a marker collision
  drops a candidate visibly rather than silently (FR-006).
- **`counts.observed` equals `len(candidates) + len(excluded)`.** Nothing is
  dropped without appearing on one of the two lists. This is the invariant that
  backs SC-001's claim that every trusted, unrecorded comment carries a
  disposition.
- **Determinism.** The same observation always yields the same envelope. Ordering
  follows the observation; no set iteration reaches the output.

### Recognition

Registered whole lines are matched against the body's **first ten lines**, after
normalizing CRLF and CR to LF and stripping trailing whitespace. The lead is not
the first line — the shipped builders emit `Artifact: <title>`, a feature line,
and a blank line ahead of it, so a verbatim paste puts the lead on line four.

`template_id` is `null` with `template_ambiguous` true when the matched sentence
is declared by more than one template. Three templates declare the empty-export
markdown sentence identically and the same three share its prompt companion, so
this is a live path, not a hypothetical.

Recognition never forces a class. The one exception is the `empty` kind, which
carries no objections and takes `no action`.

---

## Diagnostics

| Code | Condition |
|---|---|
| `invalid_input` | Body over the 8192-byte budget; unknown `surface` or `author_association`; missing required field; `ok` not literal `true`. |
| `invalid_input` | Unreadable `workflow_file`. |

Diagnostic remediation and rollback text **must not contain the substring
`bash` in any casing** — the harness manifest rejects it.

---

## Registration checklist

| # | File | Change |
|---|---|---|
| 1 | `helpers/read_only.py` | `sweep_pr_feedback()` |
| 2 | `helpers/read_only.py` | Allowed-inputs entry: `{"workflow_file", "self_login", "pr_observation"}` |
| 3 | `helpers/read_only.py` | Argument-derivation branch |
| 4 | `helpers/read_only.py` | Dispatch-table entry |
| 5 | `helpers/registry.py` | One `HelperEntry`, `None` script, `python_only` |
| 6 | `tests/.../test-speckit-pro-read-only-helpers.py` | Append to `EXPECTED_HELPERS`; add to `NO_BASH_ANCESTOR` |
| 7 | `tests/.../fixtures/read-only-helpers/fixture-manifest.json` | One record, **at the position matching `EXPECTED_HELPERS`** |

`fixture_ids == EXPECTED_HELPERS` compares **in order**, while the sibling
registry-dispatch assertion compares against `sorted(EXPECTED_HELPERS)`. The two
differ deliberately; satisfy both.

---

## Reply templates (orchestrator writes, not runner)

Not part of the helper. Recorded here because they are the other interface this
slice exposes, and because FR-015 fixes one template per class.

Every template opens with the same anchored HTML-comment marker, which renders
as nothing and is what FR-006 matches on:

```text
<!-- speckit-pro:feedback-sweep -->
```

A marker rather than a visible sentence, because a visible sentence is exactly
what a reviewer quotes when they disagree, and quoting it would make their
genuine objection invisible to the next run.

| Class | Names |
|---|---|
| `amended` | class, artifact, section, **and commit** |
| `answered` | class only |
| `deferred` | class only |
| `no action` | class only |

**Only `amended` names an artifact, a section, and a commit**, because only
`amended` routes through consensus and produces an edit. Requiring them of all
four would make three of the four templates unsatisfiable — a contradiction the
spec carried until Clarify session 3 caught it.

Reply text is plain, public-readable English. Non-dominant objections on a mixed
comment are named in the reply as well as in the disposition, so nothing is
silently dropped.

**Write paths differ by surface** (FR-015a). A review-thread reply posts into
its thread. The pull-request conversation has no threading, so a reply there is
a new top-level comment that must name the comment it answers. Neither shipped
reply-writer posts to the conversation surface, so that write is new work with
no prior art to copy.

**Every body is passed by file path, never inline** (FR-004b). This is the
constraint the nearest shipped precedent violates, and SC-009 is proved by
inspecting every command the sweep issues.

**The sweep never resolves a review thread** (FR-016).

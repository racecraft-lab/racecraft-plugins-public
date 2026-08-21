# Quickstart: validating the Feedback Sweep, slice 1 of 2

**Feature**: `art-008-feedback-sweep` | **Date**: 2026-08-20

How to prove this slice works. Every scenario runs offline against fixtures: the
helper takes the pull-request observation as data, so nothing here needs a live
pull request or a network.

## Prerequisites

A fresh worktree holds only tracked files, and this slice needs no bootstrap.

```bash
python3 tests/speckit-pro/run-all.py --layer 4
```

No `pnpm install` is required unless you also touch `docs-site/`. Python 3.11+
standard library only.

## The full gate

```bash
python3 tests/speckit-pro/run-all.py
```

Zero failures required before the work is complete (constitution IV). Expect
Layers 1, 4, and 5.

## Fastest useful loop while iterating

Gate on the changed test file rather than the layer total. A concurrent
`speckit-pro/` edit stales the generated payload and reds roughly six unrelated
gate tests with an opaque `AssertionError: 1 != 0`, which is noise, not signal.

```bash
python3 tests/speckit-pro/unit/test-feedback-sweep-parse.py
python3 tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py
```

## Driving the helper by hand

```bash
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner \
  < tests/speckit-pro/unit/fixtures/read-only-helpers/requests/sweep-pr-feedback.json
```

Use `PYTHONPATH=speckit-pro`, not the installed plugin cache. A sweep run through
the cache reports a tree that is not the one you edited.

---

## Scenario 1 — Read, filter, recognize (US1)

**Setup**: the fixture corpus at
`tests/speckit-pro/unit/fixtures/feedback-sweep/comment-corpus.json`, carrying a
trusted plain comment, a trusted export paste, an untrusted comment, a comment
already in the log, and a resolved thread.

**Run**: the helper request above.

**Expect**:

- `counts.observed == len(candidates) + len(excluded)`. Nothing vanishes.
- The trusted, unrecorded, unresolved items appear as candidates, each with its
  surface.
- Every excluded comment names exactly one reason from the closed set.
- The untrusted comment appears with `untrusted_author` and appears nowhere in
  `candidates`.

**Also confirm**, per FR-008a's fixture list:

| Case | Expected |
|---|---|
| Verbatim paste, lead on line four | recognized |
| Same paste, header trimmed | recognized |
| Same paste in a review thread | recognized, surface `review_thread` |
| CRLF-delimited body | recognized (normalization) |
| Body at the 8192-byte budget | recognized, `truncated` true |
| Body over budget | `invalid_input` naming the comment id |
| Each of the five excluded association values | `untrusted_author` |
| Shared empty-export sentence | `template_ambiguous` true, `template_id` null |
| Self-reply marker, matching author | `self_reply` |
| Self-reply marker, different author | **candidate**, not excluded |
| Quoted reply (marker not at position 0) | **candidate**, not excluded |
| No registered sentence | ordinary comment, `export` null |

The last two are the anchoring test. A reviewer who quotes a sweep reply to
disagree with it must stay visible.

## Scenario 2 — The registry stays honest as the gallery grows (FR-008a)

**Run**: `python3 tests/speckit-pro/unit/test-feedback-sweep-parse.py`

**Expect**: the derive test reads `speckit-pro/artifact-gallery/manifest.json`
and the template sources, and asserts the registry matches every template the
manifest says exports, in every kind it declares.

**Expect specifically**: the skip list is exactly `["uat-walkthrough"]`. That
entry is declared in the manifest as exporting both kinds but has **no template
file**. The assertion is pinned rather than silent so the gap stays visible: the
day it gains a file, or any other template loses one, this fails and a human
decides. The test reads templates and edits none, so it triggers no payload
regeneration.

## Scenario 3 — Amend, record, stop (US2)

**Setup**: one comment that warrants a plan change, one that does not.

**Expect**:

- Exactly one amendment commit lands, and exactly one bookkeeping commit follows
  it. The bookkeeping commit stages the workflow file **path alone** and takes a
  `chore:` subject.
- The bookkeeping commit lands **after** the amendment commit. A row naming a
  commit cannot exist before that sha does.
- Both comments get one reply and one Feedback Sweep Log row.
- Only the amendment gets a Consensus Resolution Log row, with `Type` = `Sweep`.
- The link resolves both ways: the sweep row's `CRL #` names the consensus row,
  and that row's item cell names the comment id.
- The run stops before task work with a re-review report.
- **No review thread was resolved** (FR-016).

**Then re-run with no new comments**: zero new rows, zero new replies, zero
amendments, and the run proceeds into task work (SC-003).

**Zero-amendment case**: rows and replies are written, one bookkeeping commit is
taken, and the run proceeds. **Zero-handled-comment case**: no rows, no replies,
**no bookkeeping commit**, and the run proceeds. The two are separated so the
first does not read as requiring an empty commit on a pull request that carried
no comments.

## Scenario 4 — Reply shape (SC-002, SC-008)

Replies sit outside the runner's determinism guarantees, so prove them against a
**captured-command fixture** — assert the commands the sweep would issue — not
against a golden helper response.

**Expect**:

- Exactly one reply per handled comment. No handled comment has zero, none has
  two.
- Every reply opens with `<!-- speckit-pro:feedback-sweep -->` at position 0.
- The `amended` reply names artifact, section, and commit. The other three name
  none of those, because none exists.
- Every body is passed **by file path**. No comment or reply text appears in any
  command string (SC-009).
- A conversation reply names the comment it answers, since that surface has no
  threading.

## Scenario 5 — Unreadable pull request (US3, SC-006)

Run once per corroboration status.

| Status | Expect |
|---|---|
| `match` | sweeps |
| `no_record` | proceeds, one-line note, no error |
| `skipped` | **stops**, and the report names which of the four causes occurred: absent, unauthenticated, rate-limited, or unparseable |
| `pr_closed` | stops, names the status and resume path |
| `pr_missing` | stops, names the status and resume path |
| `identity_mismatch` | stops, names the status and resume path |

The `skipped` report must read differently from the three discrepancy stops. Its
resume path is to fix the tool and re-run, because the observation is retaken on
every invocation. **Clearing the `Draft PR` row is not a resume path for
`skipped`** — that belongs to `pr_missing`.

## Scenario 6 — The log survives reviewer prose (SC-010)

**Expect**: a disposition containing a pipe and a newline leaves every later
column, including `CRL #`, readable in its own position. A comment whose author
cannot be resolved still produces a complete row with the `Author` cell saying
so explicitly rather than sitting blank.

## Scenario 7 — Cross-platform parity (SC-007)

```bash
python3 tests/speckit-pro/run-all.py --layer 1
```

`validate-codex-skills` and `validate-codex-parity` must pass. Both
phase-execution references and both workflow-file-protocol files describe the
same sequence.

**Watch the word cap.** The Codex autopilot `SKILL.md` body is **7997 words
against a hard 8000-word limit — three words of headroom.** This slice adds
nothing to either `SKILL.md` for that reason. If a later change needs a line
there, it must free words first.

---

## Before calling the work done

1. **Regenerate the payload.** Plugin source changed, so the generated artifact
   contract applies:

   ```bash
   python3 scripts/refresh-release-artifacts.py
   ```

   This covers `dist/` and the runner `.sha256` and `.manifest.json`. CI's
   `artifact-consistency` job fails the pull request if it was skipped.

2. **Regenerate the installed-cache copies** of the runner sources under the
   test fixtures. Adding a read-only helper restales them; the spec's
   Assumptions already record this as required rather than optional.

3. **Check the harness manifest text.** Remediation and rollback strings must
   not contain the substring `bash` in any casing.

4. **Regenerate the docs-site reference pages.** This slice adds a test file and
   a `suite-manifest.json` entry, and a tracked change under the test tree
   restales the generated reference. Run the install once per worktree first:

   ```bash
   pnpm --dir docs-site install --frozen-lockfile
   pnpm --dir docs-site reference:generate
   ```

   Skipping this does not fail quietly — `validate-docs` is inside the gate in
   step 5, so a stale reference surfaces there rather than here.

5. **Run the full gate**: `python3 tests/speckit-pro/run-all.py`, zero failures.

---

## Traceability

| Requirement | Verified by | Evidence |
|---|---|---|
| FR-001, FR-002 | Scenario 7 | Sequence sits ahead of the notes record; no Workflow Overview row added |
| FR-003, SC-007 | Scenario 7 | Codex parity validators |
| FR-004, FR-004a | Scenario 1 | Both surfaces read; pagination to exhaustion; `authorAssociation` requested |
| FR-004b, SC-009 | Scenario 4 | Captured-command fixture; every body by file path |
| FR-005, SC-004 | Scenario 1 | Five excluded association values, one fixture each |
| FR-006, FR-006a | Scenario 1 | Anchored marker **and** author; quoted-reply case stays a candidate |
| FR-007, FR-007a–d | Scenarios 1, 2 | Ten-line window; ambiguity on shared sentences; recognition never forces a class |
| FR-008, SC-005 | Scenario 1 | Normalization, truncation flag, deterministic candidate set |
| FR-008a | Scenario 2 | Derive-from-manifest test with a pinned skip list |
| FR-009 | Scenarios 1, 3 | `already_logged`; re-run produces zero new rows |
| FR-010, FR-011 | Scenario 3 | One class per comment; only `amended` routes to consensus |
| FR-012, FR-012a | Scenario 3 | One commit per amendment; separate `chore:` bookkeeping commit, ordered after |
| FR-013, SC-010 | Scenarios 3, 6 | Row shape, placement, pipe escaping, unresolvable author |
| FR-014 | Scenario 3 | `Sweep` type; bidirectional link |
| FR-015, FR-015a, SC-002 | Scenario 4 | One reply per comment; per-class templates; both write paths |
| FR-016 | Scenario 3 | No thread resolved |
| FR-017, FR-018 | Scenario 3 | Stop on amendment; proceed otherwise; the three zero-cases |
| FR-019, FR-019a, FR-019b, SC-006 | Scenario 5 | Six statuses, one behavior each; four-cause reporting |
| SC-001 | Scenario 1 | `observed == candidates + excluded` |
| SC-003 | Scenario 3 | Idempotent re-run |
| SC-008 | Scenario 4 | Replies alone tell a reviewer what changed and where |

## What slice 2 inherits

Recorded so slice 2 does not rediscover it. Both are interfaces, not internals.

- **The Feedback Sweep Log row shape**, whose `Commit` column is the join key
  slice 2 uses to find which pages went stale.
- **The stop-report sentence** stating that draft pages regenerate once slice 2
  lands. Slice 2 replaces it with the real outcome.
- **SC-008 stands.** Slice 2 owns the draft-description refresh and must not
  weaken the FR-015 replies on the assumption the description now carries this.
  A draft description is fully fingerprint-protected with no editable region.

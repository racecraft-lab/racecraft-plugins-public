# Manual UAT: ART-007 Draft-PR Emission

**Pull request**: #445 | **Head**: `art-007-draft-pr-emission` | **Date**: 2026-08-18

Operator-run acceptance evidence, taken by hand against the worktree tree rather
than the automated suite. Every command below was run from the repository root
with `PYTHONPATH=speckit-pro`, so the code under test is this branch and not the
installed 2.25.0 plugin cache.

Read this beside `quickstart.md`, which is the script this session followed. It
covers quickstart scenarios 1 through 4 in full, and the parts of scenarios 5
through 7 that can be reached without opening a live pull request.

---

## Verdict

**Pass.** Every deterministic scenario holds, both arms of the mode conditional
are enforced in both directions, and all six corroboration statuses reproduce
from their own inputs — including the four settled edge decisions that the
contract argues for at length and that a reader could not otherwise confirm.

The residual is the live emission boundary. It is unexercised, and §Residual
below separates the part that is structurally blocked from the part that is
merely operator-gated.

---

## Environment

| Item | Value |
| --- | --- |
| Head commit | `78dcfca34` |
| Python | 3.11.0 |
| CI on this head | 19 SUCCESS, 1 SKIPPED, 0 failures |
| Suite baseline | 7525 tests (Layer 1 1468, Layer 4 5865, Layer 5 192) |

The one skip is `Windows ARM64 advisory smoke`, which has no hosted runner label
and skips on every pull request in this repository.

---

## Scenario 1 — A draft packet validates without implementation evidence

The quickstart names this the tripwire for the feature's most likely single
defect: a schema relaxed without the validator's two hand-written evidence
assertions relaxed alongside it.

Request sent to `validate-pr-packet-read-only` against
`tests/speckit-pro/unit/fixtures/pr-packet/valid-draft.json`.

**Result**: envelope `status` `ok`, `exit_code` `0`, and `data.stdout_json`
carrying `status` `passed`, `pr_blocked` `false`, `failures` `[]`, `mode`
`draft` — for a packet whose `verification_evidence` is `[]`, whose
`scope_evidence.changed_files` is `[]`, and whose `uat.how_to_uat` is `""`.

**Pass.**

---

## Scenario 2 — The two shipped modes are untouched

Covered by the full Layer 4 run, which CI executed green on this exact head. The
stronger evidence is the differential table in the next section: the shipped
`single` fixture still passes, and each piece of evidence removed from it still
fails on both the schema rule and the hand-written assertion.

**Pass.**

---

## Mode-conditional differential — nine packets

Each variant is the shipped fixture with one field changed. `packet_id` and
`validation_result_path` were kept consistent with the variant filename, because
the validator binds all three and an identity failure would otherwise mask the
result being measured.

| Packet | Status | Failing rules |
| --- | --- | --- |
| `draft-baseline` | passed | none |
| `draft-eight-headings` | failed | `packet.schema.max_items`, `packet.schema.const`, `body.required_headings` |
| `draft-editable-fields` | failed | `packet.schema.max_items`, `body.editable_markers` |
| `draft-uat-heading` | failed | `packet.schema.const`, `body.uat_runbook_heading` |
| `single-baseline` | passed | none |
| `single-no-verification` | failed | `packet.schema.min_items`, `evidence.verification` |
| `single-no-changed-files` | failed | `packet.schema.min_items`, `evidence.scope.changed_files` |
| `single-no-uat` | failed | `packet.schema.min_length` |
| `single-draft-headings` | failed | `packet.schema.min_items`, `packet.schema.const`, `body.required_headings` |

Every failing row carries `pr_blocked` `true`.

Three things this proves that the tripwire alone does not:

1. **The relaxation did not leak.** `single-no-verification` fails on *both*
   layers — the schema's `else` arm and the validator's hand-written assertion.
   Relaxing one without the other is the DC-1 defect class; neither happened.
2. **The draft arm constrains rather than merely permits.** A draft packet
   carrying eight headings, an editable field, or a UAT runbook heading is
   rejected. Draft mode is a different shape, not a weaker one.
3. **The shapes do not cross.** `single-draft-headings` is rejected, so the
   two-heading draft body cannot be smuggled into a `single` packet.

**Pass.**

---

## Scenario 3 — Corroboration produces each of the six statuses

Twenty probes through `resolve-autopilot-stage`. The workflow file is the real
ART-007 workflow with a `Draft PR` row injected into `### Basic Information`.

Rows 1 and 4 use **live, read-only `gh` output**, pasted verbatim:

```bash
gh pr list --head art-007-draft-pr-emission --state all \
  --json number,url,state,isDraft,headRefName
gh pr view 443 --json number,url,state,isDraft,headRefName
```

| # | Recorded row | Observation | Status | `merged` | `reason` |
| --- | --- | --- | --- | --- | --- |
| 1 | #445 | live: #445 `OPEN` | `match` | null | null |
| 2 | #444 | live: #445 `OPEN` | `identity_mismatch` | null | null |
| 3 | #445, altered URL | live: #445 `OPEN` | `identity_mismatch` | null | null |
| 4 | #443 | live: #443 `MERGED` | `pr_closed` | `true` | null |
| 5 | #445 | `pull_requests: []` | `pr_missing` | null | null |
| 6 | row absent | live: #445 `OPEN` | `no_record` | null | null |
| 7 | #445 | key omitted | `skipped` | null | `no observation supplied` |
| 8 | #445 | explicit `null` | `skipped` | null | `no observation supplied` |
| 9 | #445 | `ok: false` + reason | `skipped` | null | `gh not authenticated` |
| 10 | #445 | `ok: false`, no reason | `skipped` | null | `observation unusable` |
| 11 | #445 | `ok: 1` | `skipped` | null | `observation unusable` |
| 12 | #445 | `ok: "true"` | `skipped` | null | `observation unusable` |
| 13 | #445 | #445 state `open` | `match` | null | null |
| 14 | #445 | #445 state `LOCKED` | `match` | null | null |
| 15 | #999 | live: #445 `OPEN` | `identity_mismatch` | null | null |
| 16 | #444 | #445 state `LOCKED` | `pr_missing` | null | null |
| 17 | #445 | #445 state `closed` | `pr_closed` | `false` | null |
| 18 | #445 + gap note | live: #445 `OPEN` | `match` | null | null |
| 19 | #445, URL with parens | live: #445 `OPEN` | `no_record` | null | null |
| 20 | bare `#445` | live: #445 `OPEN` | `no_record` | null | null |

**The resolved `stage` is `plan` in all twenty**, which is §5.4's rule that
corroboration reports and never decides.

Six of these confirm decisions the contract had to argue for, and each would
have been invisible to a reader who trusted the prose:

- **Row 11 is the one worth naming.** `ok: 1` yields `skipped`, not a
  discrepancy. Python treats `1 == True`, so a truthiness test would have
  accepted a malformed observation as a successful query and let it assert a
  discrepancy. The literal-`true` gate holds.
- **Rows 14 and 16 read the two state allowlists symmetrically.** An
  unrecognised state on the recorded pull request reports `match`, not
  `pr_closed`; an unrecognised state on a competing pull request is not a
  conflict, so row 16 falls through rule 1 to `pr_missing`. Reading either as
  "anything not `OPEN`" would have produced a stop on no evidence.
- **Rows 13 and 17** confirm the case-insensitive comparison, and row 4 proves
  it against a real uppercase `MERGED` from GitHub.
- **Row 15** confirms rule 1 outranks rule 4: a branch that grew a second pull
  request reports the conflict rather than the absence.
- **Rows 19 and 20** confirm the row regex fails closed. A malformed value reads
  as absent rather than raising, and a URL carrying parentheses cannot swallow a
  gap note into the link target and corrupt the identity.
- **Row 18** confirms the gap note is run prose, not identity: it parses, and it
  does not disturb the match.

**Pass.**

---

## Scenario 4 — The new agent ships on both platforms and breaks no digest

| Check | Result |
| --- | --- |
| `speckit-pro/agents/artifact-author.md` present | yes, 12 Claude agents |
| `speckit-pro/codex-agents/artifact-author.toml` present | yes, 11 Codex agents |
| Codex bundle vs `REQUIRED_CODEX_AGENT_NAMES` | equal; missing none, unexpected none |
| Layer 6 governed corpus | exactly 12 roles |
| `artifact-author` inside the corpus | no |
| `refresh-release-artifacts.py --check` | exit 0, "Generated release artifacts match the source tree." |

`artifact-author` sitting outside the governed corpus is the Out-of-Scope
boundary holding. Had it been added, the hand-maintained sha256 chain would have
restaled and reported `source digest does not match role source bytes`.

**Pass.**

---

## Emission prose parity

Both platform surfaces carry the same ten emission subsections in the same
order: the terminal-step sequence, the `artifact-author` dispatch, the
strict-mode return-before-generation, the two-way existence test, the two-block
description, the three fail-open sinks, the stop report, the `Draft PR` row,
the per-status terminal behaviour, and the reviewability split.

The Claude reference carries one further subsection, `Plan stage: G6.5 is the
terminal step`, which predates this feature.

---

## Title self-validation — scenario 7e's premise

Seven titles through `build_check("validate-pr-title", ...)` in
`speckit-pro/speckit_pro_runner/gates/release.py`, which is the live
release-readiness gate rather than a copy of its pattern.

| Title | Gate |
| --- | --- |
| `feat(speckit-autopilot): Open a draft pull request at the plan boundary` | pass |
| `feat(speckit-autopilot): Open a draft pull request when the plan stage ends` | pass |
| `feat(ART-007): Open a draft pull request at the plan boundary` | **fail** |
| `art-007-draft-pr-emission` | fail |
| `feat: Open a draft pull request` | fail |
| `wip(speckit-autopilot): Open a draft pull request` | fail |
| `feat(speckit-autopilot): ` | fail |

Row 3 is the case research D4 records and scenario 7e depends on: the packet
schema accepts an uppercase ticket scope and the gate rejects it. Both titles the
draft fixture lists under `rejected_candidates` are rejected here, so the
fixture's own reasoning is confirmed rather than asserted.

**Pass.**

---

## Gallery routing — read against the manifest, not the prose

`speckit-pro/artifact-gallery/manifest.json` carries 21 templates across three
stages. The four at `draft-pr`:

| Entry | Trigger |
| --- | --- |
| `implementation-plan` | `{"always": true}` |
| `spec-explainer` | `{"always": true}` |
| `code-approaches` | `{"any_of": ["competing_approaches"]}` |
| `module-map` | `{"any_of": ["brownfield_change"]}` |

Both named signals are in the manifest's closed vocabulary. The routing matches
what `artifact-author.md` describes, and the agent instructs the reader to trust
the manifest over its own paragraph — which is the right precedence, since the
other 17 entries (4 `final-pr`, 13 `ad-hoc`) must never be selected at draft
time.

**Pass.**

---

## Live single-mode complement

The draft arm above is exercised by fixture. The `single` arm is exercised
against this pull request itself, whose body was produced by the same packet
machinery in `single` mode:

| Property | Value |
| --- | --- |
| Title | `feat(speckit-autopilot): Open a draft pull request when the plan stage ends` |
| Release-readiness pattern | matches |
| H2 headings | 10 |
| Release-note fence | present |

Ten headings and a release-note fence, against the draft body's two headings and
no fence. The two shapes are as far apart in practice as the contract says they
are on paper.

---

## Finding 1 — this spec's `SPEC-MOC.md` was never re-indexed (FIXED)

Not a defect in this feature. Surfaced by UAT, and fixed in the same commit that
records it.

`generate-spec-index-check` against the real repository reported:

```text
spec-index: STALE — art-007-draft-pr-emission (regenerated zones differ from committed)
```

The writer's dry run planned exactly one file, this spec's `SPEC-MOC.md`, and
reported `rendered_map_count: 10, stale_map_count: 1`. All three generated zones
in that file — `INDEX`, `PRS`, `BACKLINKS` — were empty, so the spec was
scaffolded and never re-indexed. The other nine spec maps were current.

It was genuinely pre-existing. The check reported the same status with
`manual-uat.md` removed, and again with the git-ignored `.process/pr-packets/`
directory moved aside as well — that second state is exactly what CI sees.

**Why CI was green anyway**: the Layer 1 test that owns this helper,
`validate-spec-index-determinism.py`, runs it against a fixture repository root
under `tests/speckit-pro/layer1-structural/fixtures/spec-index/`. Nothing in the
suite runs the check against the real tree, so real-tree drift is invisible to
the gate.

**The fix.** `generate-spec-index-write` in `apply` mode, run with
`.process/pr-packets/` moved aside so the scan surface matched a clean checkout.
It touched one path and filled the `BACKLINKS` zone with fifteen relative links
to tracked files. `INDEX` and `PRS` stay empty, which is correct: this spec has
no slices and no generated PR rows.

**Verification**

| Check | Result |
| --- | --- |
| `generate-spec-index-check`, clean-checkout scan surface | exit 0, `index current — all in-scope maps up to date.` |
| Layer 1 | 1468/1468, unchanged from baseline |
| Regenerated diff | 15 backlinks, all tracked relative paths, no ignored paths |

---

## Finding 2 — `generate-spec-index` scans git-ignored paths (NOT FIXED)

Exposed while fixing Finding 1, and the reason that fix needed a holdout step.

The generator walks the filesystem rather than the git index, so it treats
git-ignored files as index material. Measured on the same tree, one variable
apart:

| Scan surface | Check result |
| --- | --- |
| `.process/pr-packets/` moved aside — what CI and a clean checkout see | exit 0, `index current` |
| `.process/pr-packets/` present — what this worktree sees | exit 1, `STALE` |

`pr-packets/` is git-ignored. Two consequences follow, and they point in
opposite directions, which is what makes this worth recording:

1. **A false STALE.** An operator with local ignored artifacts is told the index
   is stale when it is correct.
2. **A false green that lands.** Regenerating naively from such a worktree bakes
   ignored paths into the committed `SPEC-MOC.md`. Those paths do not exist in a
   clean checkout, so the committed index is then wrong for every other reader —
   and, because of Finding 1's gate blindness, nothing in CI reports it.

The second is the more serious: it commits an incorrect artifact and passes.

**Left unfixed on purpose, and routed.** The generator is repository tooling
well outside this feature's surface, and the sound fix changes behaviour for
every spec, not just this one. It wants its own change with its own tests.
Closing the gate blindness in Finding 1 belongs with it: a real-tree
spec-index check added to the suite today would fail on any worktree carrying
ignored artifacts, which is exactly the false STALE above.

Both halves are now scope bullets 7 and 8 of **HRNS-015: Autopilot and
PR-Emission Defect Repair** in
`docs/ai/specs/harness-engineering-uplift-technical-roadmap.md`, whose stated
purpose is repairing defects observed during live autopilot runs, each with a
reproduction and a `file:line` cause. That spec was `Ready` and unscaffolded, so
the scope was still cheap to change. It carries the constraint that shapes the
fix: the runner is stdlib-only with no shell fallback, so `git ls-files` is not
available, and the current walk's descriptor-safe reads and symlink skipping
must survive whatever replaces it.

---

## Residual — what this session could not exercise, and why

The live emission boundary is untested. **Two different blockers apply, and they
are not the same kind of thing.**

**Structural.** A real plan-stage run cannot exercise this feature. The
component that runs a plan stage is the installed plugin, still at 2.25.0, whose
`mode` enum is `["single", "split"]` and which carries no emission prose.
Running it today executes pre-ART-007 code that opens no draft pull request by
construction. This clears only by merging #445, letting the release cut a new
version, and refreshing the installed cache.

**Operator-gated.** The bare `gh pr create --draft` call, the refresh-in-place
path, and the closed-pull-request handling need a fork or throwaway branch the
operator is willing to open and close draft pull requests on. Nothing structural
prevents it; it is outward-facing, so it was not done unprompted.

What that leaves unproven, all of it inside quickstart scenarios 5 through 7:
the artifacts-then-commit-then-push-then-create ordering, the emitted body
against a real GitHub render, the bookkeeping commit, the fail-open arms with
real unreadable templates, re-entry against a live open and a live closed pull
request, and the two FR-013 sequence failures.

Everything those runs would exercise *at the decision layer* — mode selection,
evidence relaxation, title self-validation, row parsing, corroboration
classification, and per-status terminal behaviour — is confirmed above from its
own input.

`T052` stays `[~]`. This record states what manual UAT covered; it does not
claim T052 ran.

# Amendment - ART-003 Gap Triage

Amends `.specify/memory/archive-reports/2026-08-14-art-003-post-merge-hygiene.md`,
which is left unedited. That report is the record of the archive as it was
performed; this file records what a triage of its carried-forward gaps found
afterward, on 2026-08-14 UTC.

The precedent for amending rather than editing is
`2026-07-16-car-001-evidence-parity-amendment.md`.

## Why this exists

The archive report listed five gaps as carried forward. A triage assessed each,
with an independent adversarial pass on every assessment and a completeness sweep
for gaps the enumeration missed. Three of the five resolve to "no action", one was
discharged immediately, and the sweep found the archive had **misdiagnosed** one of
its own findings.

## Discharged: the acceptance evidence is now in the repository

The report recorded that no acceptance record was merged and that the 176 verdicts
"live only in the archive report". Both are now false, and the second understated
the risk: the harness and its machine-readable output were sitting in a session
scratchpad under `/private/tmp`, which clears.

Preserved under `docs/ai/specs/.process/`:

- `ART-003-uat-results.md` — the verdicts, the scope limits, and what the run found
- `ART-003-uat-harness/cdp.py` — the standard-library CDP driver
- `ART-003-uat-harness/uat_{prwriteup,annotated_diff,flowchart}.py` — the three drivers
- `ART-003-uat-harness/slice{1,2,3}-results.json` — 58 + 65 + 53 rows, all `ok: true`

**The committed JSON is not a transcription.** All three drivers were re-run from
their new location against `main` at `bb3f425e` before the commit, so the evidence
describes the merged bytes rather than three deleted worktrees. Result unchanged:
58/58, 65/65, 53/53.

### What preserving it required changing

The harness as run was not committable, and the two objections to it turned out to
point the same way.

**It launched Chrome from a hard-coded macOS path.** That is wrong in a repository
many people work in, and it is wrong on its own terms: no single path is correct
across macOS, Linux, Windows, or across Chrome, Chromium and their distribution
packagings.

**The repository's own Bash-confinement guard refused it**, and correctly. A
`subprocess` call whose executable cannot be statically resolved reports as
`<dynamic executable>` and blocks the release-readiness gate. Measured: three
release-readiness tests in `test-speckit-pro-gates.py` failed the moment the
harness was staged, with `blocking_count` moving 1 to 2 on
`cdp.py: Python subprocess executable cannot be statically resolved Bash-free`.

Satisfying the guard with a literal path would have reintroduced exactly the
portability defect. **So the launcher was removed instead.** `cdp.py` now connects
to a browser the operator started, over `CDP_ENDPOINT` (default
`http://127.0.0.1:9222`), and contains no `subprocess` call, no platform
assumption, and no absolute path of any kind. Each `Chrome()` instance takes its
own **browser context**, which preserves the per-stage isolation the drivers
depend on, cache included.

Two defects surfaced while proving the new design, both now fixed and documented
in the harness itself, because each produced a wrong result rather than an error:

- `Browser.grantPermissions` without a `browserContextId` grants to the *default*
  context. The isolated pages never saw the clipboard grant, so `readText` failed
  with `NotAllowedError` while every non-clipboard assertion still passed.
- A target created with explicit `width`/`height` stalls its renderer when the
  width sweeps re-apply `Emulation.setDeviceMetricsOverride` per breakpoint.

The drivers additionally gained three one-line sanitizations: the pinned worktree
path became a repository root resolved from the file's own location, screenshots
default to a temp directory rather than the tree, and both are overridable by
environment variable.

A third change came from CodeQL, and it is a real imprecision rather than a false
positive: the drivers identified the brand webfont request with
`"fonts.googleapis.com" in url`, which also matches
`https://example.com/fonts.googleapis.com`. A request from an unrelated origin
would have been waved through as "just the webfont" and the offline assertions
would have passed while missing it. Replaced by `is_brand_font_request()`, which
compares the parsed host.

**Re-verified end to end on the committed design**: 58/58, 65/65, 53/53 against
`main`, with the full repository suite at 7399/7399 and the Bash-confinement guard
back to `blocking_count: 0`.

**A green sweep is not yet a reliable one, and the record says so.** Of two
consecutive full sweeps, the first produced 58/58, 64/64 with a stage raising, and
50/53; the second was clean and is what the committed JSON records. Two causes,
both documented in `ART-003-uat-results.md`: stages sharing one browser can
interfere during teardown, and one assertion reaches `fonts.gstatic.com`, which was
observed returning 404 during this work. Neither is an artifact defect, and the
second cannot be fixed from inside the repository.

## Corrected: the unchecked task boxes were a gate, not a ledger

The report treated slices 2 and 3 merging with every task box unchecked as
bookkeeping hygiene, comparable to ART-011's state-file disagreement. Measured at
the merge commits, it is not:

| Slice | Task ID form | Counted by `count_tasks` | Done | G7 result recorded |
|---|---|---|---|---|
| 1 | `- [x] T001` | 40 | 40 | `G7 PASS, 40/40 tasks` |
| 2 | `- [ ] T001` | 41 | 0 | none |
| 3 | `- [ ] **T001**` | **0** | 0 | none |

Two separate defects sit behind that table.

**The counter cannot see a decorated task ID.** `count_tasks` and
`count_done_tasks` anchor on `^\s*-\s+\[[ xX]\]\s+T[0-9]`
(`speckit-pro/speckit_pro_runner/helpers/read_only.py:4143` and `:4151`), so
slice 3's `**T001**` form counts zero. G7 consumes those counts at `:935` and gates
on `remaining == 0 and total > 0`, so an unreadable file produces `total: 0` and a
failure reason that names the wrong problem. This is the ART-018 pattern for the
third time, and it is now the fourth row of that entry's table.

**Neither slice records a G7 result at all**, while both declare G7 in their gate
tables. Slice 2's tasks were in the plain form, so the counter could read them and
G7 would have failed loudly had it run. A widened matcher is worth nothing if the
gate consuming it is skipped, so ART-018's verification now requires proving the
check *runs*, not only that it detects.

## Withdrawn: the offline console line was already a settled decision

The report framed the one console line on an offline reload as an open
gallery-wide question. It is not open. The roadmap carries a dated Key Decision
from 2026-07-28: "Google Fonts as sole external reference … Alternatives: embedded
woff2 (rejected: ~300KB per artifact)". ART-003 rediscovered a closed question and
correctly rewrote its runbook step to match the shipped design.

The report's "244 KB raw / 325 KB base64 / 2.2 MB across seven" figures are
inherited from the ART-003 run, not independently measured here, and no woff2 file
exists in the tree. The decision holds on its own recorded grounds regardless.

## Confirmed unfixable, and correctly recorded

- **Back-filling slices 2 and 3's task boxes.** Both folders are gone from `main`.
- **Correcting the three workflow files' `Post: UAT Runbook Generation | ⏳ Pending`
  rows.** The run is over and no evidence exists of what the orchestrator recorded,
  so any status written now would be invented rather than recovered. ART-009 retires
  the step outright.

One cosmetic consequence is worth naming: `speckit-status` parses every
`*-workflow.md` Workflow Overview with no archived filter, so a merged and archived
spec still reports as sitting mid-workflow. Noted, not filed.

## Found by the sweep, and filed

**ART-020, opened 2026-08-14.** Five `overflow-x: auto` containers carry no
`tabindex`, so a keyboard-only Safari reader cannot reach their clipped content:
`code-approaches.html:700`, `implementation-plan.html:721` and `:942`,
`module-map.html:587` and `:769`. ART-003's own `annotated-diff.html:569` and
`flowchart.html:576` already ship the fix. The gap was recorded during ART-003
slice 2 at `docs/ai/specs/.process/ART-003-slice-2-workflow.md:622-624` and no
entry owned it, so the record had nowhere to go.

## Corrected figures

- **ART-011's archive records `speckit-scaffold-spec` at 984 and 928 lines.** Both
  variants measure **994 and 940** today and at the commit that set the figure, so it
  was a mismeasurement rather than post-merge drift. ART-019 slice D re-measures as
  part of its own verification, so no separate correction is filed.

## Still owed, and not closed here

**ART-002's fifteen acceptance steps remain unexecuted**, against four shipped
templates, and nobody owns re-running them. The preserved harness covers two of the
four kinds directly: offline reload via `Network.emulateNetworkConditions` and
greyscale via `Emulation.setEmulatedVisionDeficiency`. It does **not** cover the
other two. Reduced motion needs `Emulation.setEmulatedMedia`, which `cdp.py` does
not implement, and whether a focus indicator is *perceivable* is a human judgement
a harness can only proxy. There is also no driver for any of the four ART-002
templates.

This is real work, not a mop-up, and it belongs in ART-009's scoping rather than in
an archive amendment.

## Method note

The triage ran twelve agents: one assessor and one adversarial verifier per gap,
plus a completeness critic and a synthesizer. Two assessments were overturned by
their verifiers, and the more instructive one is worth recording. The assessor for
the harness gap concluded from a `grep` that the harness no longer existed and
costed a 300-to-600-line rewrite; the files were on disk the whole time, and the
null result came from a pattern that needed `-E`. **A null result from a search is
not evidence of absence until the search itself is verified.** That is the same
failure mode ART-018 exists to fix, arriving from a different direction on the same
day.

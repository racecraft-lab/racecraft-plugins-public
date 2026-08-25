# PR Review Packet: ART-008 Artifact Freshness (slice 2 of 2)

Generated at T081 from `spec.md`'s PR Review Packet Requirements and the
traceability table in `quickstart.md`.

## Read this first: the realized diff overran its declared budget

The declared production-only budget was **~730 midpoint, 556–885 range, WARN**,
against a 400 warn and an 800 block. The realized production diff is **1222
added and 15 removed across the five production paths**, which is over the
block threshold.

| Production path | Declared | Realized | Verdict |
|---|---:|---:|---|
| `speckit_pro_runner/helpers/read_only.py` | 271–390 | 347 | in band |
| `speckit_pro_runner/helpers/registry.py` | 8–10 | 8 | in band |
| `skills/speckit-autopilot/SKILL.md` | 2–5 | 4 | in band |
| `skills/speckit-autopilot/references/phase-execution.md` | 150–230 | 455 | **~2x over** |
| `codex-skills/…/references/phase-execution-codex.md` | 125–190 | 408 | **~2x over** |

**The executable surface landed inside its estimate.** The overrun is entirely
reference prose, on both platforms, and it is prose density rather than
unplanned scope: every added passage traces to a task in `tasks.md`, and no
requirement grew during implementation.

**No gate produced a block verdict.** The `final-reviewability-backstop` helper
is deferred on the installed runner, so the governing evidence is the committed
WARN chain recorded at T014, which is a may-continue outcome. This section is a
**realized-overrun diagnostic**, not a gate result, and it is recorded so the
number is visible at the checkpoint rather than discovered later.

**The split lever named in `plan.md` no longer matches where the overrun is.**
That lever deferred the description-refresh half (FR-014, FR-019a's refresh leg,
FR-033 through FR-039), worth 95–155 lines. The overrun is spread across all
three user stories' prose, so pulling that seam would not bring the diff under
800. A split that would work is the platform seam: land the Claude surface and
the helper, and defer the 408-line Codex mirror to a stacked slice. That
trades reviewability for a window in which the two platforms disagree, which is
what SC-008 exists to prevent. **The choice is the operator's at this
checkpoint.**

## What changed

After a feedback sweep amends planning artifacts, the whole draft artifact page
set is regenerated and the draft pull-request description refreshed **before**
the run stops for re-review, so the re-reviewer reads pages that match the
amendments beside them. On a clean sweep, pages a previous run left stale are
detected by a deterministic git-history join, repaired, and the run proceeds
without stopping.

One new read-only runner helper, `check-artifact-freshness`, carries the whole
deterministic decision across three named surfaces: `verdict`, `removal_diff`,
and `corroborate_refresh`.

## Why

Slice 1 shipped the checkpoint but left the pages behind it stale, and
apologized for it in prose: its stop report told the reviewer that draft pages
would regenerate once slice 2 landed. That sentence is now removed from both
platform surfaces, because the behavior it promised exists.

## Non-goals, with their owner

- **No change to slice 1's sweep.** Reading, trust filtering, classification,
  consensus amendment, log rows, replies, and stop-or-proceed are untouched.
- **No content-hash staleness.** Pages are agent-authored prose, so identical
  inputs produce different bytes. The join reads supplied ancestry records and
  never page bytes.
- **No second bookkeeping store.** The Feedback Sweep Log stays the sole record.
  The FR-018a snapshot is run-scoped transport, always removed, never read as a
  record.
- **No second writer of the `Draft PR` row.** The sweep still never writes it.
  The refresh changes the cell through the emission machinery.

## Review order

Read the join rule first: every other requirement depends on it.

1. `specs/art-008-feedback-sweep-slice-2/contracts/check-artifact-freshness.md`
   and `data-model.md` — the one registered operation, its three surfaces, and
   the dual-anchoring rule.
2. `tests/speckit-pro/unit/fixtures/artifact-freshness/` — 51 cases. The one to
   read closely is `dual-anchoring-escaped-pipe-in-disposition`.
3. `speckit-pro/speckit_pro_runner/helpers/read_only.py` — the log read, the
   ancestry join, the verdict precedence, and the two reuse-only surfaces.
4. `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` — the
   regeneration sequence, the three commit shapes, and the report.
5. `speckit-pro/codex-skills/…/phase-execution-codex.md` — the platform mirror.

## Scope budget

The binding figure is `plan.md` §"Reviewability Budget, derived by hand". The
plan-phase estimator returned `{"status":"pass","projected":0}`, which is an
**absent measurement, not evidence of fitness** — it classifies none of these
paths as production and false-zeroed the same way on slice 1. It is not cited
as a pass anywhere in this run. See the overrun table above for the realized
figure.

Atomicity route: `one-navigable-PR`, releasable, no marker plan persisted.

## Traceability

`quickstart.md` §Traceability is the binding map and covers all eight success
criteria. Task-level `SC-` citations name only the four a single task
discharges outright.

## Verification evidence

- Full suite **14179/14179, exit 0** (L1 1511, L4 12449, L5 219), against a
  recorded G0 baseline of 14012. G7's increase requirement is satisfied, +167.
- `test-artifact-freshness` **154/154** over 51 fixture cases; every case was
  red before its implementation, and the two cases added last were proven
  non-vacuous by mutation.
- Layer 1 **1511/1511**, including `validate-codex-skills` and
  `validate-codex-parity`.
- `refresh-release-artifacts.py` is idempotent: a second run makes no change.
- Quickstart scenarios 1, 2, 6, and 7 executed against real bytes.

## Known gaps

- **Quickstart scenarios 3, 4, and 5 were not executed.** They need an
  installed plugin carrying both slices, which exists only after a release cuts
  from this merge and the plugin cache refreshes. Autopilot runs from the
  cached plugin, so an end-to-end sweep cannot run against the working tree.
  Discharge path is recorded in the workflow file's post-implementation
  checklist, mirroring how slice 1 recorded its own T098 limit.
- **No feedback sweep ran on this pull request.** The installed plugin is
  2.27.0, which predates slice 1's sweep. A read-only substitute was taken
  instead: #502 carried 0 reviews and 0 comments, so there was nothing to sweep.
- **Two quickstart scenarios were corrected during validation**, because they
  were not executable as written. Scenario 1's falsifiable step assumed the
  named workflow file carried `amended` rows, which it does not. Scenario 6
  expected a Codex `SKILL.md` body of 7998 words; the measured figure is 7996,
  and the two words were freed by work that landed on `main` between the
  slices, not by this one.

## Rollback

Revert the branch. The helper is additive and read-only, the reference prose is
additive apart from the two promise passages, and no state file, payload
format, or stored contract changes shape. Nothing in this slice migrates data
or writes a record another run reads.

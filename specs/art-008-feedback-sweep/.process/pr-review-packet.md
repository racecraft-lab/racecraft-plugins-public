# PR Review Packet: ART-008 Feedback Sweep (slice 1 of 2)

Generated at T078 from `spec.md`'s PR Review Packet Requirements and the
traceability table in `quickstart.md`.

## What changed

The implement stage now opens with a draft-pull-request feedback sweep. Before
any task work, a run whose workflow file carries a `Draft PR` row reads every
unresolved review thread and every pull-request conversation comment, keeps only
comments from OWNER, MEMBER, or COLLABORATOR authors, recognizes
artifact-exported markdown blocks by their lead sentence, skips any comment id
already logged, and classifies each remaining comment as amended, answered,
deferred, or no action. Amended items route through consensus, land one commit
each, and stop the run for re-review.

## Why

The staged workflow exists to create a trusted human checkpoint. Before this,
feedback left on a draft pull request had no route back into the planning
artifacts, so a reviewer's objection could be read and then quietly lost. The
sweep closes that loop and stops rather than proceeding whenever it changed
anything.

## Non-goals, with their owner

Owned by ART-008 slice 2, stacked on this branch: whole-set artifact
regeneration after amendments; stale-page detection on a clean sweep; and the
draft-description refresh with the Resume block wording. Named as non-goals in
`spec.md` rather than silently omitted.

## Review order

1. `specs/art-008-feedback-sweep/contracts/sweep-pr-feedback.md`, the one
   registered operation and its three named surfaces. Everything else follows
   from it.
2. `speckit-pro/speckit_pro_runner/helpers/read_only.py`, the parse, the
   write-point check, and the four redaction legs.
3. `speckit-pro/agents/sweep-classifier.md` and `sweep-analyst.md`, the two
   agents that read attacker-controllable text.
4. `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py`, the
   carve-out that pins those two allowlists by equality.
5. The two phase-execution references, which are the orchestrator's own
   procedure.
6. `tests/speckit-pro/unit/test-feedback-sweep-parse.py` and its corpus.

## Scope budget

| Measure | Accepted at T014 | Actual |
|---|---|---|
| Reviewable LOC | 1120-1720, midpoint ~1420 | **1663** (911 Python, 752 agent definitions) |
| Production files | 12 | **13** |

Both halves were over a block and both were **operator-accepted** before
implementation, recorded in the workflow file with the reason and the PRSG-013
precedent. The actual landed inside the accepted band. Reference prose adds a
further 1452 lines across six files, and fixture data 27251 lines across
seventeen, the great majority of it captured rather than authored.

## Traceability

The full requirement-to-evidence map is the table in `quickstart.md`, which is
the source of truth and is not duplicated here. Verification per scenario:

| Scenario | Result |
|---|---|
| 1, 2, 3, 4, 6 (parse, registry, amend, reply, log) | `test-feedback-sweep-parse.py` 84/84 |
| 5 (unreadable pull request) | `CorroborationGateTest` 8/8 |
| 7 (cross-platform parity) | codex-skills 163/163, codex-parity 87/87, codex-agents 148/148 |

## Verification evidence

- Parse harness: **84 tests, 0 failures**, 163 corpus cases, four capture blocks.
- Layer 5 tool scoping: **219/219**, closing the untrusted-input carve-out.
- Codex route-fallback recovery: **35/35** after the roster re-review.
- Release artifacts: `refresh-release-artifacts.py` reports consistent; all four
  new agent definitions and both `install.py` copies verified byte-identical in
  the payload.
- Docs-site reference pages regenerated.
- Full gate: see the PR body's final number.

## Known gaps

1. **T098's binding probe is UNRUN, not passed.** Plugin agents load from the
   versioned plugin cache rather than worktree source, so the two new agents
   cannot be dispatched from this branch, and staging them into the cache is
   correctly refused as agent-config self-modification. The stop condition fires
   on a *reachable* denied tool and none was observed, so it is not triggered;
   nothing observed the allowlist binding either, so it is not discharged.
   Discharge after release and cache refresh. Recorded in full in the workflow
   file. SC-015 was narrowed at Analyze consensus row 8 to claim only what a
   fixture can produce, and this is that narrowing meeting its first instance.
2. **A tension inherited from the task text**, flagged for a reviewer's eye:
   T089's mandated wording, that the parse filters over those bodies so the
   request file must carry them, sits against the pipe paragraph's statement
   that no unredacted body is written to disk at any point. They reconcile
   through that paragraph's own "where a byproduct file is unavoidable" clause.
3. **Four assertions are recorded as currently unfalsifiable** in the
   implementation-notes record rather than counted as coverage, including one
   that only begins to bite once a future sentence exists.
4. **Two tasks were added during implementation** because no shipped task owned
   them: T110, the `HELPER_CASES` entry without which every added helper raises
   `KeyError`, and T111, the Codex fallback roster re-review.

## Rollback

No feature flag. The sweep is a Phase 7 setup step in the two phase-execution
references, so reverting this branch removes the step and the stage opens the
way it did before. The runner helper is additive: nothing calls
`sweep-pr-feedback` except the sweep sequence, and the registry entry is inert
without it. The two agent definitions are new files, dispatched by nothing else.

---
topic: "Arm the accidentally-advisory state bookkeeping checks"
slug: "art-017-state-bookkeeping-checks"
date: "2026-08-22"
mode: "setup"
spec_id: "ART-017"
source_input:
  type: "file"
  ref: "docs/ai/specs/html-artifacts-technical-roadmap.md#art-017-arm-the-accidentally-advisory-state-bookkeeping-checks"
question_count: 8
stop_reason: "natural"
---

# Design Concept: Arm the accidentally-advisory state bookkeeping checks

> **Source:** `docs/ai/specs/html-artifacts-technical-roadmap.md`, ART-017
> **Date:** 2026-08-22
> **Questions asked:** 8
> **Stop reason:** natural
> **Blind-spot pass:** ran — 5 findings surfaced, 2 set aside

## Goals

- Register exactly `in_progress_errors`, `duplicate_state_steps`, and
  `state_order_errors` under the existing `status-evidence` rule that the
  autopilot invokes at every phase transition.
- Flip each key's `PROBLEM_KEY_INTENT` verdict to `gated` atomically with its
  rule membership so the classification record never misdescribes runtime
  behavior.
- Prove each key independently makes the exact `--rule status-evidence`
  invocation exit non-zero, using one shared clean builder and one isolated
  mutation per invariant.
- Run an explicit regression over every tracked workflow with an adjacent
  `autopilot-state.json`, proving current stored workflow/state pairs remain
  green under the exact invocation.
- Preserve the complete JSON report shape and existing problem-key values;
  ART-017 changes scoped exit-code authority, not diagnostics.
- Narrow the existing authored autopilot paragraph so it distinguishes legacy
  coverage debt from current-run state invariants, then regenerate Codex and
  release payload mirrors through repository tooling.
- Develop independently from ART-008, then rebase onto the latest `main`,
  regenerate shared artifacts, and run the full suite before ART-017 is made
  ready or merged.

> **Slice-sizing advisory:** `estimate-spec-size` used one behavior story,
> three authored files, seven scoped requirements, and `new_vs_modify=modify`.
> It returned `estimated_loc: 125`, `suggested_slices: 1`, `status: ok`; no split
> is warranted. The setup reviewability gate separately returned `warn` only
> because it detected three primary surfaces (`40` reviewable LOC, `3`
> production files, `5` total files), so the split decision remains one spec.

## Non-goals

- Arm or reclassify any of the nine remaining advisory keys (Q7).
- Introduce a new named rule or rework the `--rule` scoping mechanism (Q1, Q7).
- Group every `validate_state` result under one rule; legacy coverage keys stay
  nonblocking under `status-evidence` (Q1, Q7).
- Expand the same explanation across every autopilot reference surface by hand
  (Q5).
- Add a new top-level report summary, change problem-key values, or fail fast
  before the complete JSON report is emitted (Q6).
- Stack ART-017 on ART-008 or skip the final rebase/regeneration boundary (Q8).

## Design Tree (Q&A log)

### Q1. Which rule contract should arm the three ART-017 state-invariant keys?

**Branch:** Rule authority

**Recommended answer:** Use `status-evidence`.
> Both authored autopilot variants already invoke the guard with
> `--rule status-evidence`, and the validator's `main()` lets only keys selected
> by the supplied rule move the exit code. Explicit per-key membership is the
> smallest change that makes the current invocation authoritative without
> arming legacy coverage debt.

**Alternatives offered:**
- Create a state rule: add a new rule and update both invocations, increasing
  implementation and parity scope.
- Choose per key: route keys independently, leaving any key outside
  `status-evidence` nonblocking unless the invocation also changes.

**User's answer:** Use status-evidence (Recommended)

---

### Q2. Which corpus should the regression proof cover after the three keys are armed?

**Branch:** Regression evidence

**Recommended answer:** Tracked workflow-state pairs.
> The three findings describe current-run state invariants, not only Markdown
> structure. Running the exact invocation for each tracked workflow with an
> adjacent state file proves the change against durable state that synthetic
> fixtures cannot represent.

**Alternatives offered:**
- Synthetic clean states: deterministic, but unable to reveal malformed tracked
  state files.
- Full suite only: less test code, but no explicit pair-level corpus proof.

**User's answer:** Tracked workflow-state pairs (Recommended)

---

### Q3. How should the three negative controls prove that each key independently moves the autopilot exit code?

**Branch:** Test isolation

**Recommended answer:** Shared clean builder.
> One clean workflow/state builder keeps setup consistent while three isolated
> cases each introduce exactly one invariant violation. Each case can assert its
> target list is non-empty, the other two new lists are empty, and the exact
> scoped invocation exits `1`.

**Alternatives offered:**
- Standalone fixtures: maximum isolation at the cost of duplicated setup.
- Combined bad state: less test code, but it cannot prove that each key gates
  independently.

**User's answer:** Shared clean builder (Recommended)

---

### Q4. Should rule registration and each `PROBLEM_KEY_INTENT` verdict flip be treated as one atomic implementation requirement?

**Branch:** State classification integrity

**Recommended answer:** Keep them atomic.
> `test_the_gated_verdict_agrees_with_the_rule_map` defines `gated` as exact rule
> membership. Changing the two surfaces together preserves that invariant in
> every commit and avoids an intentionally broken intermediate state.

**Alternatives offered:**
- Separate commits: allow an intentionally failing intermediate commit.
- Derive verdicts: refactor intent classification around rule membership,
  broadening ART-017 beyond its repair scope.

**User's answer:** Keep them atomic (Recommended)

---

### Q5. How broadly should ART-017 update the autopilot documentation when the keys become blocking?

**Branch:** Documentation scope

**Recommended answer:** Narrow the existing paragraph.
> The authored skill already explains why legacy structural coverage remains
> outside the scoped rule. Narrowing that paragraph to distinguish the three
> state invariants keeps one source of truth; generated Codex and payload copies
> can then be refreshed through repository tooling.

**Alternatives offered:**
- Expand all references: duplicate the key-level explanation across task-list
  and phase-execution references.
- Code and tests only: leave prose that misdescribes the new runtime behavior.

**User's answer:** Narrow existing paragraph (Recommended)

---

### Q6. When one of these invariants fails, should ART-017 change anything besides the scoped exit code and intent verdict?

**Branch:** Failure contract

**Recommended answer:** Preserve the report shape.
> The guard already emits the complete report under every rule and scopes only
> the return code. Retaining that contract gives operators all diagnostics while
> making the three existing keys genuinely blocking.

**Alternatives offered:**
- Add a summary message: introduce a new top-level output contract.
- Fail fast: stop after one finding and lose the complete diagnostic report.

**User's answer:** Preserve report shape (Recommended)

---

### Q7. Should ART-017 preserve the roadmap's existing scope boundary around the other advisory keys and the rule-scoping mechanism?

**Branch:** Scope cuts

**Recommended answer:** Preserve both cuts.
> The validator mixes legacy structural coverage and current-run state
> invariants in one returned dictionary. Arming only the three named keys keeps
> ART-017 narrow and prevents pre-existing coverage debt from blocking resumable
> specifications.

**Alternatives offered:**
- Arm more keys: reassess other advisory verdicts and expand regression scope.
- Revise rule scoping: change the validator and invocation contract.

**User's answer:** Preserve both cuts (Recommended)

---

### Q8. How should ART-017 handle final integration while ART-008 is still in flight?

**Branch:** Parallel integration

**Recommended answer:** Rebase, then regenerate.
> The authored ART-017 files are independent from ART-008's main implementation
> files, while release payloads and generated documentation are shared derived
> surfaces. Independent development plus serialized final regeneration preserves
> both lanes without stale artifacts.

**Alternatives offered:**
- Merge ART-017 first: coordinate ART-017 integration ahead of the active
  feedback-sweep lane.
- Stack on ART-008: add a branch dependency despite authored-file separation.

**User's answer:** Rebase then regenerate (Recommended)

## Open Questions

None. Every surfaced blind-spot finding was resolved during Q1-Q4 and Q7; the
remaining branches converged without a deferred decision.

## Recommended Next Step

Continue the ART-017 scaffold using this document as the scoping source. After
the design concept, populated workflow, SPEC-MOC, and roadmap status update are
committed and pushed, start a new Codex task rooted at the ART-017 worktree and
run the printed planning-stage hand-off command.

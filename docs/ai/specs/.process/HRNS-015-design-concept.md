---
topic: "HRNS-015 Autopilot, Gate, and PR-Emission Repair"
slug: "hrns-015-autopilot-gate-pr-emission-repair"
date: "2026-10-01"
mode: "setup"
spec_id: "HRNS-015"
source_input:
  type: "file"
  ref: "docs/ai/specs/harness-engineering-uplift-technical-roadmap.md#hrns-015-autopilot-gate-and-pr-emission-repair"
question_count: 10
stop_reason: "natural"
---

# Design Concept: HRNS-015 Autopilot, Gate, and PR-Emission Repair

> **Source:** `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md` (### HRNS-015)
> **Date:** 2026-10-01
> **Questions asked:** 10
> **Stop reason:** natural
> **Blind-spot pass:** did not run — wait deadline expired

## Goals

- Fix the defects from live autopilot runs that main still has, each with a
  failing-first fixture, so the documented happy path stops producing a failing
  pull request or a silently wrong count (roadmap Goal).
- Ship as one spec with three user stories emitted as three split PRs in roadmap
  order: Slice A (PR emission), Slice B (gates and counters), Slice C (workflow
  behavior). Each PR stays within 4 production files and 10 authored files (Q5).
- Keep the Phase 6.5 verdict item in HRNS-015: the scaffold estimate is 225 LOC,
  under the 400 LOC move-back threshold (Q5, `estimate-spec-size`).
- Final PR bodies carry an autopilot-drafted consumer-facing release note in one
  ` ```release-note ` fence after Known Gaps (Q3).
- A host repository can declare its unit and full-verify commands in
  `.specify/project-commands.json`, and this repository dogfoods that file (Q1,
  Q7, Q9).

## Non-goals

- Vendoring `scripts/release_note_policy.py` into the runner or imposing this
  repository's release-note policy on host repositories (Q4).
- Making G6.5 a hard gate: only a blank Verdict cell blocks; `remediate` and
  `stop` render as recorded (Q2).
- Declaring any command slot other than `UNIT_TEST` and `FULL_VERIFY` in
  `.specify/project-commands.json` (Q7).
- A filesystem fallback when the tracked-only spec-index walk cannot run git (Q6).
- Behavioral (Layer 2/3) evals or a runner helper for `speckit-resolve-pr`
  paging; proof is a Layer 1 prose contract (Q10).
- Everything in the roadmap's Out of Scope list: post-list completion refusal
  (HRNS-018), slice-row budget parsing, markdown-visibility rules, legacy
  roadmap-link repair, PR-packet schema redesign, host release-note policy
  changes. Runtime child lifetime stays with HRNS-017; the broad envelope sweep
  stays with HRNS-019.

## Module and Interface Deltas

- `speckit-pro/speckit_pro_runner/helpers/pr_packet.py`: changed. Optional
  `release_note` input on final (single and split) packets, rendered as one
  ` ```release-note ` fence after Known Gaps; drafts never carry one; structural
  check only (non-empty, no nested fence, final-only). Reads the Phase 6.5
  Verdict row from the workflow file, renders it under Verification, and blocks
  finalization when the cell is blank or still the template comment (Q2, Q3, Q4;
  roadmap Module and Interface Deltas).
- `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`:
  changed only if the packet records the note (roadmap).
- `speckit-pro/speckit_pro_runner/helpers/pr_contract.py`: new. Canonical packet
  paths (`<feature>/.process/pr-packets/<id>.json`, `<id>/body.md`,
  `<id>/validation.json`) shared by `pr_packet.py` and `mutation.py` (evidence:
  `canonical_packet_paths` in `pr_packet.py`).
- `speckit-pro/speckit_pro_runner/helpers/mutation.py`: changed. Packet apply
  succeeds when the only untracked paths are the current packet's three
  canonical files; a second packet, an unrelated file, a tracked edit, or a
  `git status` failure still refuses (roadmap).
- `speckit-pro/speckit_pro_runner/helpers/read_only.py`: changed. One shared
  `[Gap]` / `[Gap, <ref>]` pattern for G1-G4 and `count-markers`; tracked-only
  spec-index walk that fails closed on git failure (Q6); `estimate-spec-size`
  accepts `required_refactor_files` (+40 LOC per distinct file, missing or
  invalid adds nothing); `detect-commands` reads `.specify/project-commands.json`
  first (Q1, Q7, Q8).
- `.specify/project-commands.json`: new interface. JSON object with optional
  string keys `UNIT_TEST` and `FULL_VERIFY` only. Unknown keys, bad JSON, empty
  or non-string values return an input diagnostic with no marker fallback (Q1,
  Q7, Q8). This repository adds its own copy in Slice B (Q9).
- `scripts/refresh-release-artifacts.py`: changed. Refreshes and `--check`s the
  spec index so `artifact-consistency` catches a stale tracked map; `AGENTS.md`
  freshness row updated (roadmap).
- Autopilot packet guidance (`speckit-autopilot` post-implementation reference):
  changed. States the untracked-packet outcome and that autopilot drafts the
  release note from `spec.md`'s summary at PR Body Generation (Q3; roadmap).
- `speckit-pro/skills/speckit-resolve-pr/SKILL.md`: changed. Paged GraphQL for
  threads and comments (`pageInfo`, cursors), block mutation on a failed page,
  compare fresh `headRefOid` with the pushed SHA before any reply or resolve
  (roadmap; Q10).
- Four executor definitions in `speckit-pro/agents/` (phase-, analyze-,
  checklist-, implement-executor) and their generated Codex TOML: changed.
  Teardown obligation text (roadmap).
- `speckit-pro/skills/speckit-status/SKILL.md`: changed. Complete request
  envelopes for `generate-spec-index-check` and `o5-topology` (roadmap).
- Grey box: internal structure of the shared Gap pattern and of the
  project-commands loader is the implementer's choice.

## Terms

| Term | Meaning in this spec | Differs from codebase usage? | Source (Q<n> or evidence) |
| ---- | -------------------- | ---------------------------- | ------------------------- |
| Canonical packet files | The three paths `canonical_packet_paths` returns for the current packet: packet JSON, `body.md`, `validation.json` | no | evidence: `pr_packet.py` `canonical_packet_paths` |
| Missing verdict | The Phase 6.5 Verdict cell is empty or still the template comment; any recorded value is present | yes: the template treats a Pending G6.5 as legitimate; this spec blocks only at final-packet time on a blank cell | Q2 |
| Release note | Consumer-facing text in one ` ```release-note ` fence on final bodies; protected body content, not an editable field | no | roadmap; Q3 |
| Declared test command | `UNIT_TEST` or `FULL_VERIFY` from `.specify/project-commands.json`, outranking marker detection | yes: today `detect-commands` only infers from root markers and runner scripts | Q1, Q7 |

## Verification Gates

- Quick suite: `python3 tests/speckit-pro/run-all.py` passes (evidence: `AGENTS.md` Commands table).
- CI suite: the `run-ci-suite.json` runner request in `AGENTS.md` passes, including layers 6 and 7 (evidence: `AGENTS.md`).
- `python3 scripts/refresh-release-artifacts.py --check` passes after regeneration; fails on a frozen pre-fix stale `SPEC-MOC.md` fixture and passes with an untracked file present (roadmap Done When).
- Unit fixtures, each failing first: `release_note` present/absent (absent body byte-identical, draft has no fence); a repo-level test feeds a built final packet through `scripts/release_note_policy.py` for a `feat` and a `fix` title (Q4); packet apply success and each refusal case; Phase 6.5 verdict present and blank; `[Gap]` and `[Gap, <ref>]` in G1-G4 and `count-markers`; `estimate-spec-size` refactor count, missing, invalid; `detect-commands` declared command wins, and invalid file errors (Q8); tracked-only walk fails closed on git failure (Q6).
- Layer 1 structural tests: one test fails when any of the eight executor definitions loses its teardown obligation; one asserts `speckit-resolve-pr` SKILL.md carries paged thread and comment queries, stop-on-failed-page, and the `headRefOid` check before reply/resolve (Q10); each documented `speckit-status` envelope matches a passing fixture.
- Reviewability: each split PR within 4 production files and 10 authored files (Q5; roadmap budget).
- Formal methods: none. The changes are deterministic input validation, path-set predicates, and prose contracts with no concurrency or state machine that ordinary fixtures cannot cover (evidence: roadmap Scope; no question needed).

## Design Tree (Q&A log)

### Q1. Where should a host repository declare its test command so `detect-commands` honors it before marker detection?
**Branch:** interface / data
**Recommended answer:** New `.specify/project-commands.json` file
> Machine-readable, sits beside other SpecKit config, trivially fixture-tested; `.specify/quality-gates.json` stays thresholds-only per the roadmap.
**Alternatives offered:** Parse the AGENTS.md Commands table (fragile prose parsing); a constitution section (blurs governance with commands).
**User's answer:** New .specify file (Recommended)

### Q2. When the final packet reads the Phase 6.5 section, what should block finalization?
**Branch:** behavior and rules
**Recommended answer:** Blank Verdict cell
> The workflow template says G6.5 is advisory and may stay Pending; blocking only on a blank cell guarantees the PR states the verdict without changing gate policy.
**Alternatives offered:** Block on anything but `proceed` (hardens an advisory gate); never block and render "not recorded" (contradicts Done When).
**User's answer:** Blank Verdict cell (Recommended)

### Q3. Who supplies the `release_note` text for a final packet?
**Branch:** user outcome / dependencies
**Recommended answer:** Autopilot drafts it from `spec.md`'s summary at PR Body Generation
> Fits the autonomous path and needs no new workflow section; the helper only renders and validates.
**Alternatives offered:** A new workflow `## Release Note` section (adds template and read path); caller-only with no guidance (happy path still fails the release-note gate).
**User's answer:** Autopilot drafts it (Recommended)

### Q4. How should the packet helper check the note, given `scripts/release_note_policy.py` is not shipped in the plugin?
**Branch:** dependencies / verification
**Recommended answer:** Structural check in the helper plus a repo-level test through the policy script
> Host policy stays the host's, matching the Out of Scope line on host release-note policy.
**Alternatives offered:** Vendor the policy into the runner (imposes this repo's rules on hosts).
**User's answer:** Shape check + repo test (Recommended)

### Q5. `estimate-spec-size` returns 225 LOC, 1 suggested slice; the setup gate warns on 24 total files. How should HRNS-015 ship?
**Branch:** slice sizing
**Recommended answer:** Three PRs, A/B/C in roadmap order
> Matches the roadmap's recorded split; each PR stays under 4 production / 10 authored files. Estimate inputs: 3 stories, 6 files, 9 FRs, modify.
**Alternatives offered:** One PR with three story commits (breaches 15-file warn); two PRs A+B then C (A+B at the 6-production-file warn line).
**User's answer:** Three PRs, A/B/C (Recommended)

### Q6. When the tracked-only spec-index walk's git call fails, what should it do?
**Branch:** errors
**Recommended answer:** Fail closed with a diagnostic
> Matches the packet-apply rule that a `git status` failure refuses, and avoids silently reintroducing untracked files (#568 class).
**Alternatives offered:** Fall back to the filesystem walk (silent stale-map risk).
**User's answer:** Fail closed (Recommended)

### Q7. Which keys may `.specify/project-commands.json` declare?
**Branch:** interface
**Recommended answer:** `UNIT_TEST` and `FULL_VERIFY` only; unknown keys rejected
> Exactly the roadmap scope; widening later is additive.
**Alternatives offered:** All nine command slots (widens Slice B beyond budget).
**User's answer:** UNIT_TEST, FULL_VERIFY only (Recommended)

### Q8. If `.specify/project-commands.json` exists but is invalid, what should `detect-commands` do?
**Branch:** errors
**Recommended answer:** Error with no fallback
> A repo that declared a command meant it; falling back to markers would run the wrong suite, the defect being fixed.
**Alternatives offered:** Warn and fall back (easy to miss in an autonomous run).
**User's answer:** Error, no fallback (Recommended)

### Q9. Should this repository add its own `.specify/project-commands.json` in HRNS-015?
**Branch:** rollout
**Recommended answer:** Yes, in Slice B
> Proves the feature end-to-end on the repo that ships it and fixes this repo's own command discovery.
**Alternatives offered:** Fixtures only (this repo stays on marker detection).
**User's answer:** Yes, in Slice B (Recommended)

### Q10. How should the `speckit-resolve-pr` paging and SHA-check requirements be proven, given Slice C has no production files?
**Branch:** verification
**Recommended answer:** Layer 1 prose contract
> Structural tests assert SKILL.md carries the paged queries, the stop-on-failed-page rule, and the `headRefOid` check before reply/resolve; fits the no-production-file slice.
**Alternatives offered:** Layer 2/3 eval with a fake `gh` (costly, flaky); a new paging runner helper (adds a production file, breaks Slice C's budget).
**User's answer:** Layer 1 prose contract (Recommended)

## Open Questions

- **What:** The blind-spot pass did not run, so unknown unknowns in the affected code (for example, other callers of the G1-G4 counters or of `_spec_index_walk_regular_files`, and existing `detect-commands` consumers that assume marker-only output) were not surfaced before the interview.
  **Why deferred:** The pass hit its 5-minute execution deadline.
  **Suggested next step:** Clarify should run a codebase sweep of callers and fixtures for each changed helper before Plan.
- **What:** Exact rendering of the Phase 6.5 verdict under Verification (verdict only, or verdict plus mode and composite confidence).
  **Why deferred:** Not consequential enough to interview; the roadmap only requires the current verdict.
  **Suggested next step:** Settle in Clarify against `required_headings` and the existing Verification section.
- **What:** Whether `pr-packet.schema.json` must record `release_note` at all, or the input stays transient.
  **Why deferred:** The roadmap makes the schema change conditional.
  **Suggested next step:** Decide in Plan after reading how packet inputs are persisted.
- **What:** Where `required_refactor_files` comes from at G3/G5 (ART-015 owns re-invocation).
  **Why deferred:** Re-invocation is owned by ART-015; this spec only adds the input.
  **Suggested next step:** Confirm the boundary in Clarify.

## Recommended Next Step

Populate the HRNS-015 workflow file and hand off to `/speckit-pro:speckit-autopilot --stage plan`.

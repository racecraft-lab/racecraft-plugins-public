---
topic: "Deep coherence and cohesion audit of speckit-pro"
slug: "speckit-pro-coherence-audit"
date: "2026-09-29"
mode: "standalone"
source_input:
  type: "topic"
  ref: "speckit-pro coherence and cohesion audit after a month of heavy change"
question_count: 13
stop_reason: "natural"
---

# Design Concept: Deep coherence and cohesion audit of speckit-pro

> **Source:** A speckit-pro coherence and cohesion audit after a month of heavy change: 254 commits touching 298 files, with 37.7k lines added and 18.4k removed.
> **Date:** 2026-09-29
> **Questions asked:** 13
> **Stop reason:** natural

## Goals

- **Every file reviewed.** Every in-scope file is read and reviewed for coherence and cohesion. The scope is every tracked file in `speckit-pro/` and `tests/speckit-pro/`, plus the authored docs-site pages, `scripts/`, the root agent and review docs, and active (not archived) specs. That is about 1,670 files. `dist/` and generated reference pages are excluded as regenerated copies (Q1).
- **Coherence.** Files agree with each other. The audit checks:
  - one source per contract;
  - Claude and Codex parity;
  - prose that matches runner behavior;
  - evals that match behavior;
  - no stale or contradicting claims.
- **Cohesion.** Each file does one job. There is no mixed concern and no duplicated logic, code sits in the right layer, and nothing is dead or orphaned (Q2).
- **Checkable coverage.** A coverage ledger is generated from `git ls-files` before work starts. It maps every in-scope file to one lane. Each lane records a per-file verdict (`clean`, or finding IDs) plus the ripwire checks it ran. A script fails if any file lacks a verdict, or has a verdict from a lane that does not own it (Q3).
- **Lane layout.**
  - Lanes are vertical feature slices. Each slice holds one feature's Claude skill, Codex overlay, agents, runner modules, tests, evals and docs, seeded by `ripwire --partition` and `--plan-lanes` (Q4).
  - There are about 20 lanes of about 80 files each. Any slice over 100 files is split. Six lanes run at a time, in about 4 waves (Q5).
- **Read-only audit.** Lanes only record findings. The coordinator merges duplicates, the owner approves the grouping, and one GitHub issue is filed per theme. Separate fix lanes then land them in stacks (Q6).
- **Baseline tree.** The audit reads `origin/main`. The ledger marks files that an open branch changes. For those files, each finding is checked against the branch diff and recorded as `fixed-in-flight`, `still-open`, or `introduced-by-branch` (Q7).
- **What gets recorded.** Lanes record only substantive findings, each with:
  - file:line evidence;
  - the ripwire command that showed it;
  - a proposed fix;
  - a severity: `blocking` (per the repo's Code Review Rules), `major`, or `minor`.

  Style and naming nits are skipped (Q8).
- **Wave 0 and the seam lane.** A wave-0 agent runs the whole-repo scans once and writes a shared evidence pack that lanes consume by slice: `--doc-drift`, `--clones`, `--rank-by=churn-decay`, cycles and layering, and `--partition`. After all lanes finish, a seam lane checks what sits between slices: shared references, runner request contracts, and Claude and Codex overlays (Q9).
- **Crash-safe storage.** The ledger, evidence pack and findings live on a dedicated, pushed, never-merged branch, `audit/coherence-2026-09`. Each wave is committed and pushed so a crash loses nothing. The branch is deleted after triage (Q10).
- **Full ripwire setup.** ripwire is set up to its full capability in this repo, per ripwire's own documentation. That includes layering rules drafted from today's structure and baselined, a quality baseline, notes, and agent wiring for Claude and Codex (Q11). A non-required CI job runs `--arch`, `--quality-delta` and `--doc-drift` and reports without blocking (Q12).
- **Two slices (Q13).**
  1. Slice 1 is a PR with the full ripwire setup, landing on main first.
  2. Slice 2 is the audit on the audit branch: ledger and coverage check, wave-0 pack, lanes, seam lane, triage, and issues.

## Non-goals

- No fixes during the audit, including trivial ones (Q6).
- No style, naming or wording-only findings (Q8).
- No required CI gate on ripwire. AGENTS.md keeps "no check may depend on" ripwire (Q12).
- The audit record is not merged into the repo (Q10).
- No review of `dist/`, generated reference pages, vendored upstream content, lockfiles or archived specs (Q1; evidence: AGENTS.md, Code Review Rules).

## Module and Interface Deltas

- **ripwire configuration (new, slice 1).** Committed files as ripwire's documentation describes: a layering rules file and `.ripwire_arch_baseline`, the quality baseline, `.ripwire_notes`, and the agent wiring from `ripwire wrap` for Claude Code and Codex, if it is repo-scoped (Q11).
- **CI workflow (new, slice 1).** A non-required job runs `--arch`, `--quality-delta` and `--doc-drift` and posts or annotates results. It is pinned and installed the same way other dev tools are, following the constitution II conditions for dev-only tooling (Q12; evidence: AGENTS.md, Editing Boundaries).
- **AGENTS.md (changed, slice 1).** The ripwire paragraph names the committed config and the advisory job. It keeps "no check may depend on" ripwire (Q12).
- **Audit tooling (new, slice 2, audit branch only).** A ledger generator and a coverage-check script, both in Python standard library. Neither is merged (Q3, Q10).
- **Grey box.** The exact feature-slice boundaries come from ripwire's partition output, adjusted by the coordinator.

## Terms

| Term | Meaning in this spec | Differs from codebase usage? | Source |
| ---- | -------------------- | ---------------------------- | ------ |
| Coherence | Files agree with each other: one source per contract, host parity, prose matching the runner, evals matching behavior. | No. It extends AGENTS.md "one source per contract". | Q2 |
| Cohesion | Each file does one job: no mixed concern, no duplication, the right layer, nothing dead. | No | Q2 |
| Lane | One vertical feature slice, of about 80 files, reviewed by one subagent. | No | Q4, Q5 |
| Coverage ledger | A per-file record of the lane owner, the verdict and the ripwire checks run. | New | Q3 |
| Seam lane | The final pass over what sits between slices. | New | Q9 |
| In-flight tag | A finding status against open branches: `fixed-in-flight`, `still-open` or `introduced-by-branch`. | New | Q7 |

## Verification Gates

- The coverage check exits 0 only when every ledger row has a verdict from its owning lane (Q3).
- Slice 1 passes its gates:
  - `ripwire --doctor` reports a healthy setup;
  - `--arch` exits 0 against the committed baseline;
  - the advisory CI job runs green or reports, and never blocks;
  - actionlint passes for the new workflow;
  - `run-all.py`, the CI default suite and the privacy scan pass on the committed ripwire files (Q11, Q12; evidence: AGENTS.md, Commands).
- Every finding carries file:line evidence and its ripwire command. The coordinator rejects findings without them (Q8).
- Formal methods: none. This is an audit and tooling setup with no state machine worth modeling (evidence: selective formal-methods guidance).

## Design Tree (Q&A log)

**Q1. Which files must the audit touch and review?**
- Branch: scope.
- Recommended: shipped plugin plus tests. The tests are where eval drift just showed up.
- Alternatives: plugin only; plugin, tests, and repo docs.
- User's answer: plugin, tests, and repo docs.

**Q2. What should "coherence" and "cohesion" mean?**
- Branch: behavior and rules.
- Recommended: cross-file and within-file, as defined in Goals.
- Alternatives: coherence only; add a prose-quality pass.
- User's answer: cross-file and within-file.

**Q3. How should the audit prove every file was reviewed?**
- Branch: verification.
- Recommended: a ledger with a coverage check.
- Alternatives: lane reports only.
- User's answer: a ledger with a coverage check.

**Q4. How should files be divided among lanes?**
- Branch: interface.
- Recommended: vertical feature slices. Cross-file contradictions then fall inside one lane.
- Alternatives: by directory; by file-type pass.
- User's answer: vertical feature slices.

**Q5. How big should each lane be, and how many at once?**
- Branch: performance.
- Recommended: about 80 files, 6 at once. Accuracy falls as context grows.
- Alternatives: about 150 files, 4 at once; about 40 files, 8 at once.
- User's answer: about 80 files, 6 at once.

**Q6. Should lanes only report, or also fix?**
- Branch: rollout.
- Recommended: report, triage, then fix. Seven fix lanes were editing the same files.
- Alternatives: fix trivial findings, report the rest.
- User's answer: report, triage, then fix.

**Q7. Which tree should the audit read?**
- Branch: dependencies.
- Recommended: main now, with in-flight files tagged.
- Alternatives: wait for the stacks to merge; audit the stack top.
- User's answer: main now, with in-flight files tagged.

**Q8. Which findings should lanes record?**
- Branch: behavior and rules.
- Recommended: substantive only, with severity. AGENTS.md calls style notes minor.
- Alternatives: everything, including nits.
- User's answer: substantive only, with severity.

**Q9. How should repo-wide ripwire scans run?**
- Branch: observability.
- Recommended: a wave-0 pack, then a seam lane.
- Alternatives: each lane runs its own scans.
- User's answer: a wave-0 pack, then a seam lane.

**Q10. Where should the ledger and findings live?**
- Branch: data.
- Recommended: a pushed audit branch. A crash earlier in this session lost uncommitted work.
- Alternatives: local scratch files; merge it into the repo.
- User's answer: a pushed audit branch.

**Q11. What should wave 0 do about the missing layering rules?**
- Branch: dependencies.
- Recommended: draft the rules and baseline them.
- Alternatives: cycles only, no rules.
- User's answer: "Option 1 but we really want the full absolute capability of ripwire in this repo so get it all setup per ripwire official documentation."

**Q12. How far should the ripwire setup go, given AGENTS.md says no check may depend on it?**
- Branch: security and rollout.
- Recommended: full setup with advisory CI.
- Alternatives: full setup with required gates; local setup only.
- User's answer: full setup with advisory CI.

**Q13. How should the work be sliced?**
- Branch: slice sizing.
- Recommended: the setup PR, then the audit. `estimate-spec-size` returned `warn` with 2 suggested slices.
- Alternatives: audit first, setup after.
- User's answer: the setup PR, then the audit.

## Open Questions

- **What:** The final layering rules. Which runner packages may import which, and the boundary between shipped code and tests.
  **Why deferred:** They are drafted from today's structure in slice 1. The owner approves the rules file in the slice-1 PR.
  **Suggested next step:** Review the rules file in the slice-1 PR.

## Recommended Next Step

Run slice 1 (the full ripwire setup PR). Once it lands, run slice 2 (the audit) on `audit/coherence-2026-09`.

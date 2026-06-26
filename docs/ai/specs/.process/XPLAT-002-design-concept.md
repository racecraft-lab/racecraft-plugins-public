---
topic: "Runtime implementation options and contract decision"
slug: "xplat-002-runtime-implementation-options-contract-decision"
date: "2026-06-26"
mode: "setup"
spec_id: "XPLAT-002"
source_input:
  type: "topic"
  ref: "docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md#xplat-002-runtime-implementation-options-and-contract-decision"
question_count: 8
stop_reason: "natural"
---

# Design Concept: Runtime implementation options and contract decision

> **Source:** `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
> **Date:** 2026-06-26
> **Questions asked:** 8
> **Stop reason:** natural

## Goals

- Evaluate JavaScript/TypeScript, Python, and small per-platform binary runner candidates evenly against the XPLAT-001 runtime rubric before choosing.
- Require official/runtime documentation plus lightweight repo-local and installed-cache smoke probes when invocation behavior is uncertain.
- Select one canonical runtime and command contract so XPLAT-004 can build without reopening the language/package decision.
- Define a small stable command interface around JSON stdin/stdout, structured stderr diagnostics, and explicit exit-code mapping.
- Optimize the selected contract for installed-cache first-run reliability: no per-user dependency installation or network fetch should be required by the public plugin payload.
- Keep public support-claim changes out of XPLAT-002; write the decision record and handoff evidence only.
- Keep XPLAT-002 as one decision spike, not a split runtime-evaluation and contract-definition stack.

## Non-goals

- Building the runner or porting helper behavior remains out of scope per Q3 and the roadmap.
- Selecting supply-chain controls remains out of scope; XPLAT-002 may note runtime-specific implications for XPLAT-003 only.
- Public Windows/macOS/Linux support claims remain out of scope until XPLAT-007 proves release readiness, per Q6.
- Native hands-on probes across all operating systems are not mandatory in this spec; Q2 chooses docs plus lightweight probes where uncertainty is high.
- A ranked shortlist is not the deliverable; Q3 chooses one canonical runtime contract.

## Design Tree (Q&A log)

### Q1. How should XPLAT-002 treat runtime candidates during the decision work?

**Branch:** Candidate strategy

**Recommended answer:** Score all three
> The roadmap names JavaScript/TypeScript, Python, and small per-platform binaries as credible implementation strategies. Evaluating all three against the XPLAT-001 rubric keeps the decision grounded instead of turning an unstated preference into architecture.

**Alternatives offered:**
- Favor JS first: Treat JavaScript/TypeScript as the default and use Python/binary mostly as rejection checks.
- Binary-first proof: Start by proving whether a small packaged binary is viable, then compare only if it fails.

**User's answer:** Score all three (Recommended)

---

### Q2. What evidence bar should XPLAT-002 require before selecting the runtime contract?

**Branch:** Evidence depth

**Recommended answer:** Docs plus probes
> XPLAT-001 explicitly deferred native runtime probes, but XPLAT-002 must still remove enough uncertainty to choose a contract. Official/runtime documentation plus lightweight local and installed-cache smoke probes gives decision evidence without turning the spec into the runner implementation.

**Alternatives offered:**
- Docs only: Rely on vendor/runtime documentation and defer all runnable probes to XPLAT-004 or XPLAT-007.
- Native probes now: Require hands-on Windows, macOS, and Linux probes before XPLAT-002 can decide.

**User's answer:** Docs plus probes (Recommended)

---

### Q3. What should the XPLAT-002 final decision produce?

**Branch:** Decision shape

**Recommended answer:** One contract
> The roadmap's done condition says XPLAT-004 should not reopen the runtime language/package decision. One selected runtime plus a precise command contract gives later specs a stable target while still allowing named temporary adapters with removal ownership.

**Alternatives offered:**
- Ranked shortlist: Produce a top-two shortlist and defer the final runtime choice until XPLAT-004 planning.
- Contract only: Define the command envelope and defer the implementation language/runtime choice.

**User's answer:** One contract (Recommended)

---

### Q4. What command-interface style should XPLAT-002 steer the runtime contract toward?

**Branch:** Command contract

**Recommended answer:** JSON envelope
> XPLAT-001 identifies JSON handling, stdout/stderr, exit-code mapping, path normalization, and subprocess behavior as must-have gates. A stable CLI with JSON stdin/stdout is the cleanest shape for fixture parity tests and avoids shell-specific argument parsing as the main contract.

**Alternatives offered:**
- CLI args first: Expose helper-specific command arguments and reserve JSON only for complex cases.
- Library API first: Define an internal library contract first, then wrap it in a CLI later.

**User's answer:** JSON envelope (Recommended)

---

### Q5. What packaging constraint should the selected runtime contract optimize for first?

**Branch:** Packaging and bootstrap

**Recommended answer:** No install step
> The product constraint is native installed-plugin behavior without Bash, Git Bash, WSL, PowerShell, or jq as the implementation substrate. A contract that works from the installed cache without per-user dependency installation reduces first-run risk and matches the public plugin distribution path.

**Alternatives offered:**
- Use system runtime: Allow the selected contract to depend on a common user-installed runtime if diagnostics are clear.
- Release artifact: Prefer separately built release artifacts, even if install/update mechanics become more complex.

**User's answer:** No install step (Recommended)

---

### Q6. How much public documentation should XPLAT-002 change while selecting the runtime?

**Branch:** Public claims

**Recommended answer:** Decision record only
> XPLAT-002 is a docs/process decision spec. Public support claims become truthful only after XPLAT-007 cuts over payloads and proves native platform readiness, so this spec should not move user-facing promises ahead of implementation.

**Alternatives offered:**
- Preview caveat: Add a short public note that cross-platform runtime work is underway, clearly marked as not ready.
- Update claims now: Begin changing public docs toward the selected runtime before implementation and native validation.

**User's answer:** Decision record only (Recommended)

---

### Q7. If runtime candidates are close, what should break the tie?

**Branch:** Selection tie-breaker

**Recommended answer:** User install reliability
> XPLAT is a release-blocker because installed workflows fail on native Windows runtime assumptions. The tie-breaker should therefore favor lowest first-run/bootstrap risk and most reliable installed-cache invocation over maintainer preference alone.

**Alternatives offered:**
- Maintainer ergonomics: Prefer the candidate easiest for maintainers to write, test, and review even if install mechanics are a little less clean.
- Security posture: Prefer the candidate with the smallest supply-chain and dependency-review surface before XPLAT-003 chooses controls.

**User's answer:** User install reliability (Recommended)

---

### Q8. Should XPLAT-002 stay as one decision spike, or split runtime evaluation and contract definition?

**Branch:** Slice sizing

**Recommended answer:** One spike
> The advisory estimator treats this as a research/decision spike with `status=ok`, `suggested_slices=1`. Keeping evaluation and contract definition together lets XPLAT-004 receive one coherent runtime contract rather than stitching two decision artifacts together.

**Alternatives offered:**
- Split contract: First evaluate candidates, then run a second spec to define the command contract.
- Defer split: Record the split decision as open and revisit during `/speckit-clarify`.

**User's answer:** One spike (Recommended)

## Open Questions

None. The interview converged on one decision spike with clear evidence, contract, packaging, and public-claim boundaries.

## Recommended Next Step

Run setup completion for this scaffold, then run:

```text
$speckit-autopilot docs/ai/specs/.process/XPLAT-002-workflow.md
```

---
topic: "XPLAT-004 - Cross-Platform Runner Foundation"
slug: "xplat-004-cross-platform-runner-foundation"
date: "2026-06-30"
mode: "setup"
spec_id: "XPLAT-004"
source_input:
  type: "file"
  ref: "docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md#xplat-004-cross-platform-runner-foundation"
question_count: 11
stop_reason: "natural"
---

# Design Concept: XPLAT-004 - Cross-Platform Runner Foundation

> **Source:** `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md#xplat-004-cross-platform-runner-foundation`
> **Date:** 2026-06-30
> **Questions asked:** 11
> **Stop reason:** natural

## Goals

- Build the Python 3.11+ standard-library runner foundation, not a helper-porting PR.
- Keep real helper behavior out of scope except for runtime-info/preflight and contract smoke fixtures.
- Use a small Python package layout with one module-oriented entrypoint and focused stdlib support modules.
- Preserve the XPLAT-002 JSON envelope, diagnostics, exit-code, path, subprocess, and preflight contract while applying the current XPLAT-003 Python runtime decision.
- Add contract fixture parity for envelopes, validation failures, typed paths, subprocess handling, and preflight behavior.
- Add runner identity, preflight, checksum, and manifest metadata for runner source files.
- Record an accepted two-slice implementation plan inside one XPLAT-004 workflow: Slice 1 for runner/preflight core, Slice 2 for parity harness plus metadata.

## Non-goals

- Porting `generate-spec-index.sh`, scaffold/status/autopilot helpers, install helpers, PR packet helpers, or any other real production helper behavior in XPLAT-004.
- Switching active Claude Code or Codex skills, hooks, generated payloads, or marketplace install behavior to the new runner.
- Copying runner files into `dist/claude/**` or `dist/codex/**` as part of this scaffolded foundation spec.
- Replacing repository-wide Bash test/eval/release gates in this spec.
- Making public native Windows, macOS, or Linux support claims before XPLAT-007.
- Implementing scan automation, release automation, signatures, SBOMs, provenance attestations, reproducible builds, or formal audit.
- Creating child specs or extra branches for the accepted split; XPLAT-004 remains one branch and one workflow with two planned PR slices.

## Design Tree (Q&A log)

### Q1. For XPLAT-004, how much helper behavior should the runner foundation include?

**Branch:** Scope boundary

**Recommended answer:** Preflight only
> The roadmap says XPLAT-004 creates the safe runway and explicitly excludes helper ports except tiny smoke/preflight helpers. The XPLAT-001 inventory maps read-only helpers to XPLAT-005 and mutation helpers to XPLAT-006.

**Alternatives offered:**
- One read-only port: Proves more behavior now, but risks crossing into XPLAT-005.
- Scaffold/status path: Higher user-visible value, but likely too broad and conflicts with the release-gate sequence.

**User's answer:** Preflight only (Recommended)

---

### Q2. What source layout should XPLAT-004 use for the Python runner foundation?

**Branch:** Source layout

**Recommended answer:** Small package
> The roadmap budget is 3-6 production files and the constitution favors simple explicit structure. A small package keeps envelope, path, subprocess, and preflight code testable without creating a framework.

**Alternatives offered:**
- Single file: Smallest file count, but harder to test and extend safely.
- Full package: More future-ready, but likely over-abstracts the foundation slice.

**User's answer:** Small package (Recommended)

---

### Q3. How should skills and tests invoke the runner during XPLAT-004 before active cutover?

**Branch:** Entrypoint and invocation

**Recommended answer:** Python module
> The selected runtime boundary is Python 3.11+ through official Spec Kit / `specify` prerequisites. Module invocation keeps JSON stdin/stdout as the durable contract without introducing shell launchers or direct script-path coupling.

**Alternatives offered:**
- Thin launcher: Closer to install behavior, but risks platform launcher complexity before helper ports.
- Direct script: Simple locally, but weaker for package/module boundaries and installed payload parity.

**User's answer:** Python module (Recommended)

---

### Q4. What should the first parity harness compare in this foundation slice?

**Branch:** Parity harness

**Recommended answer:** Contract fixtures
> XPLAT-004 must make later helper ports consistent and testable. Contract fixtures prove envelopes, errors, typed paths, subprocess handling, and preflight behavior without starting the XPLAT-005/XPLAT-006 helper ports.

**Alternatives offered:**
- Spec-index helper: Useful but starts porting real read-only behavior.
- Multiple helpers: Stronger confidence, but likely too broad for the foundation budget.

**User's answer:** Contract fixtures (Recommended)

---

### Q5. What platform proof should XPLAT-004 require before it is considered complete?

**Branch:** Platform evidence

**Recommended answer:** Local plus runbook
> The roadmap calls out installed-cache launch risk, but XPLAT-007 owns full native platform UAT. XPLAT-004 should prove local execution and leave deterministic Windows/Linux runbook fixtures for downstream validation.

**Alternatives offered:**
- Full native matrix: Strongest proof, but may block the foundation spec on environment access.
- Static only: Faster, but weakens runner-launch confidence.

**User's answer:** Local plus runbook (Recommended)

---

### Q6. Should XPLAT-004 copy runner files into generated Claude/Codex payloads now, or only prepare source metadata for later cutover?

**Branch:** Payload boundary

**Recommended answer:** Source plus metadata
> XPLAT-003 assigns source integrity metadata to the runner foundation and source-to-dist cutover evidence to XPLAT-007. Keeping generated payload propagation out avoids a premature cutover.

**Alternatives offered:**
- Passive dist copies: Closer to install proof, but expands file count.
- Active payload cutover: Conflicts with the roadmap's XPLAT-007 boundary.

**User's answer:** Source plus metadata (Recommended)

---

### Q7. How strict should the Python and `specify` preflight be in XPLAT-004?

**Branch:** Prerequisite handling

**Recommended answer:** Fail closed
> XPLAT-003 requires missing Python 3.11+, `specify`, runner files, or metadata to fail closed with deterministic diagnostics. The runner foundation should prove that behavior now.

**Alternatives offered:**
- Warn only: Easier locally, but weakens the release blocker.
- Python only: Narrower, but misses the official Spec Kit / `specify` prerequisite boundary.

**User's answer:** Fail closed (Recommended)

---

### Q8. Which Python test/eval runner pattern should XPLAT-004 introduce?

**Branch:** Test strategy

**Recommended answer:** Runner tests only
> The roadmap asks XPLAT-004 to introduce Python stdlib test/eval runner patterns, not replace every deterministic shell gate. Runner unit and contract fixture tests are the smallest useful pattern.

**Alternatives offered:**
- Layer 4 mirror: Useful, but may become a broad helper-test migration spec.
- Full test harness: Too broad unless XPLAT-004 is intentionally split.

**User's answer:** Runner tests only (Recommended)

---

### Q9. Which first-release security controls should XPLAT-004 implement directly?

**Branch:** Security controls

**Recommended answer:** Identity checksums manifest
> XPLAT-003 requires runner identity/preflight output plus checksum and manifest metadata for runner files. Scan evidence and public claims are downstream release-readiness concerns.

**Alternatives offered:**
- Add scan evidence: Stronger, but needs tooling decisions outside the runner foundation.
- Checksums only: Smaller, but leaves preflight identity and manifest readiness under-specified.

**User's answer:** Identity checksums manifest (Recommended)

---

### Q10. Should XPLAT-004 stay one constrained foundation spec or split into two thin slices?

**Branch:** Slice sizing

**Recommended answer:** Split into two
> The forward estimator returned `{"estimated_loc":420,"suggested_slices":2,"status":"warn"}` using 3 user stories, 6 files/surfaces, 7 functional requirements, and `new` work. The warning is advisory, but two thin slices reduce review risk.

**Alternatives offered:**
- Keep one spec: Faster sequencing, but reviewability must be watched closely.
- Defer split: Record the warning as an open question for autopilot planning.

**User's answer:** Split into two (Recommended)

---

### Q11. How should the accepted two-slice decision be represented in the XPLAT-004 scaffold?

**Branch:** Split representation

**Recommended answer:** One workflow
> A two-slice plan does not require O5 parent/child topology. One XPLAT-004 workflow can record planned PR slices and let autopilot's atomicity/layer planning produce the review packet.

**Alternatives offered:**
- Two child specs: More explicit, but heavier than needed for two slices.
- First slice only: Keeps this scaffold tiny, but leaves the parity/metadata half outside the ready roadmap item.

**User's answer:** One workflow (Recommended)

## Open Questions

- **What:** Exact module path and package names for the runner files.
  **Why deferred:** The interview selected "small package" and "Python module" but did not need to freeze file names beyond the XPLAT-003 runner-file contract examples.
  **Resolution note:** Resolved during clarification and planning as `speckit-pro/speckit_pro_runner/` with `<python> -m speckit_pro_runner`; avoid `speckit-pro/scripts/` because current payload generation copies that directory into `dist/**`, while generated payload propagation remains XPLAT-007 scope.
- **What:** Exact contract fixture matrix.
  **Why deferred:** The interview selected contract fixtures, but final cases should derive from the XPLAT-002 envelope/diagnostic/exit-code/path/subprocess contract and XPLAT-003 preflight additions.
  **Resolution note:** Resolved in `spec.md`, `plan.md`, `data-model.md`, `contracts/`, and `tasks.md` as invalid JSON, invalid envelope, unsupported schema version, missing fields, typed paths, paths with spaces, Windows separators, traversal-boundary behavior, missing prerequisites, subprocess nonzero, subprocess timeout, stderr-only failure, runtime-info/preflight, checksum, manifest, and metadata-readiness fixtures.

## Recommended Next Step

Setup mode is active. Continue with `$speckit-scaffold-spec XPLAT-004` artifact generation, then run:

```text
$speckit-autopilot docs/ai/specs/.process/XPLAT-004-workflow.md
```

This design concept is the source of truth for scoping decisions captured during scaffolding. Any drift in downstream artifacts from the decisions above is a downstream artifact defect unless an explicit revision note supersedes it.

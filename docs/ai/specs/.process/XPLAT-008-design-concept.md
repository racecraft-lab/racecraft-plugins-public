---
topic: "Claude/Codex cutover and universal install release gate"
slug: "xplat-008-claude-codex-cutover-universal-install-release-gate"
date: "2026-07-05"
mode: "setup"
spec_id: "XPLAT-008"
source_input:
  type: "topic"
  ref: "XPLAT-008 roadmap section in docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md"
question_count: 9
stop_reason: "natural"
---

# Design Concept: Claude/Codex Cutover and Universal Install Release Gate

> **Source:** XPLAT-008 roadmap section in `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
> **Date:** 2026-07-05
> **Questions asked:** 9
> **Stop reason:** natural

## Goals

- Switch active Claude and Codex plugin surfaces to the Python 3.11+
  standard-library runner without relying on Bash, Git Bash, WSL,
  PowerShell-specific command language, `jq`, or Unix-only path assumptions.
- Use one XPLAT-008 workflow with three internal vertical slices:
  active installed-runtime surface cutover; generated payload, release, and
  documentation gates; then native UAT, update, and safe repair evidence.
- Implement active Claude/Codex surface cutover first so payload and
  release-readiness gates validate the same installed runtime path users will
  run.
- Rebuild and gate both generated Claude and Codex payloads from source,
  proving release version, bundled agents, hooks, runner files, and
  XPLAT-003 manifest/checksum metadata are complete.
- Claim native Windows, macOS, and Linux support in public docs only after
  the full Claude and Codex UAT matrix passes.
- Add safe doctor/autoheal behavior that refreshes trusted missing or stale
  install artifacts and prints exact manual remediation for unsafe gaps.

## Non-goals

- Do not create child specs during setup. Record the three-slice strategy and
  let Specify, Plan, Tasks, and the reviewability gates prove whether child
  specs become necessary.
- Do not keep thin shell dispatch wrappers as an installed-runtime transition
  path.
- Do not run a repo-wide purge of every historical Bash or `jq` mention.
  Archive prose, CI dispatch glue, and upstream Spec Kit generated bash helpers
  are outside the active installed-runtime guard.
- Do not publish future-facing or marketing claims before the implementation
  and UAT evidence support them.
- Do not settle for smoke-only or staged UAT if the public native Windows claim
  is part of the release.
- Do not perform broad automatic plugin-cache reinstalls as the repair model.

## Design Tree (Q&A log)

### Q1. How should XPLAT-008 be sliced for reviewability?

**Branch:** Slice strategy

**Recommended answer:** Three slices
> Use one XPLAT-008 workflow with separate slices for active surface cutover,
> payload/release/docs gates, and native UAT/update/autoheal evidence. This
> follows the roadmap warning that the work may be large while keeping one
> coherent release gate.

**Alternatives offered:**
- Child specs now: Reduces PR size earlier but adds setup and coordination
  overhead before autopilot can start.
- Single pass: Fastest to start but highest risk for an oversized review packet.

**User's answer:** Three slices

---

### Q2. Which slice should XPLAT-008 implement first?

**Branch:** Implementation order

**Recommended answer:** Active surfaces
> Cut over Claude/Codex skills, agents, hooks, and install guidance first so
> later payload, release, and UAT gates validate the actual installed runtime
> path rather than a theoretical source-checkout path.

**Alternatives offered:**
- Payload gates first: Stronger guardrails before user-facing changes, but the
  gates may not yet target the final installed path.
- UAT first: Useful for acceptance clarity, but likely blocked until active
  surfaces are switched.

**User's answer:** Active surfaces

---

### Q3. How should installed Claude and Codex plugin surfaces invoke the cross-platform runner after cutover?

**Branch:** Runtime invocation

**Recommended answer:** Direct Python runner
> Use runner-module requests with explicit interpreter discovery and no shell,
> `jq`, or platform-specific command language in active installed-runtime
> guidance. This is the only option aligned with the roadmap's native Windows,
> macOS, and Linux support boundary.

**Alternatives offered:**
- Thin shell dispatch: Simpler on Unix but incompatible with the native Windows
  support goal.
- Docs-only handoff: Reduces code churn but fails the installed-plugin cutover
  objective.

**User's answer:** Direct Python runner

---

### Q4. What should XPLAT-008's no-shell/no-jq guard treat as a failure?

**Branch:** Guard scope

**Recommended answer:** Active runtime only
> Fail active installed-runtime skills, agents, hooks, install docs, payloads,
> and release gates while allowing archive prose, CI dispatch glue, and upstream
> Spec Kit generated bash helpers. This keeps the guard strict where users run
> the plugin without causing noisy historical rewrites.

**Alternatives offered:**
- Repo-wide purge: Maximizes strictness but likely rewrites archive and
  provenance content unrelated to installed runtime behavior.
- Docs advisory: Easier to pass but too weak for a public cross-platform
  release gate.

**User's answer:** Active runtime only

---

### Q5. How should XPLAT-008 handle generated Claude and Codex payloads?

**Branch:** Generated payloads

**Recommended answer:** Rebuild and gate
> Rebuild both generated payloads from source and add gates proving version,
> bundled agents, hooks, runner files, and manifest/checksum metadata are
> complete. The roadmap makes generated release payload publication part of
> XPLAT-008, not a follow-up.

**Alternatives offered:**
- Gate only: Adds checks now but leaves committed dist payload rebuilds for a
  separate release PR.
- Defer payloads: Smaller change but not release-ready.

**User's answer:** Rebuild and gate

---

### Q6. What public support and trust claims should XPLAT-008 allow in docs and release notes?

**Branch:** Public docs and consumer trust

**Recommended answer:** Implemented claims
> Claim native Windows, macOS, and Linux support only after UAT passes, describe
> the XPLAT-003 trust model exactly, and avoid unimplemented cryptographic
> guarantees. This keeps public docs tied to implemented controls rather than
> launch intent.

**Alternatives offered:**
- Release-forward claims: Faster for launch copy but risks overstating support.
- Internal docs only: Smaller review surface but misses the release-readiness
  scope.

**User's answer:** Implemented claims

---

### Q7. What UAT evidence should be required before XPLAT-008 can mark the release gate complete?

**Branch:** Manual UAT

**Recommended answer:** Full matrix
> Require filled Claude and Codex runbooks on native Windows, macOS, and Linux
> covering install, first use, scaffold/status, autopilot dry-run, update, and
> repair. This matches the roadmap's release-reviewable evidence requirement.

**Alternatives offered:**
- Staged matrix: Easier to collect but not enough for native Windows public
  support.
- Smoke only: Fastest but fails the release-reviewable UAT requirement.

**User's answer:** Full matrix

---

### Q8. How aggressive should XPLAT-008's doctor/autoheal behavior be for stale or incomplete installs?

**Branch:** Doctor and repair

**Recommended answer:** Safe autoheal
> Automatically refresh missing or stale bundled agents, hooks, and generated
> payload files when source checksums match, and print exact manual steps for
> unsafe gaps. This satisfies the safe repair goal without turning doctor into
> a broad reinstall tool.

**Alternatives offered:**
- Diagnostics only: Safer but weaker for the safe-repair release requirement.
- Full reinstall: Convenient but too broad for a bounded repair path.

**User's answer:** Safe autoheal

---

### Q9. Given the sizing warning, how should the XPLAT-008 workflow record the split decision?

**Branch:** Slice sizing

**Recommended answer:** Keep three slices
> The estimator returned `{"estimated_loc":505,"suggested_slices":2,"status":"warn"}`.
> Keeping three internal vertical slices is more explicit than the minimum
> two-slice suggestion because the roadmap spans active surfaces,
> payload/release/docs gates, and full installed-plugin UAT.

**Alternatives offered:**
- Use two slices: Follows the estimator minimum but blurs UAT/update/autoheal
  ownership.
- Create child specs: Safest for review size but adds setup work before
  autopilot can start.

**User's answer:** Keep three slices

## Open Questions

- **What:** Exact active installed-runtime inventory.
  **Why deferred:** Specify/Clarify should classify every Claude skill, Codex
  skill, agent, hook, install guide, generated payload file, and release gate
  before implementation.
  **Suggested next step:** During Clarify, produce an inventory that marks each
  item as active runtime, release gate, docs surface, archive/provenance, CI
  dispatch glue, or upstream Spec Kit helper.
- **What:** Interpreter discovery order per platform.
  **Why deferred:** The roadmap requires native Windows/macOS/Linux proof, but
  implementation should confirm the safest installed-cache launch path.
  **Suggested next step:** During Plan, decide the exact order for `py -3.11`,
  `python`, and `python3` discovery and how failures surface to users.
- **What:** Release payload completeness manifest.
  **Why deferred:** The generated payload gate needs a concrete expected-file
  inventory for both Claude and Codex payloads.
  **Suggested next step:** During Plan, define the expected version, bundled
  agents, hooks, runner files, and XPLAT-003 metadata records as a contract.
- **What:** Durable UAT evidence location and ownership.
  **Why deferred:** The roadmap requires filled native UAT runbooks but does
  not assign operators or final artifact paths.
  **Suggested next step:** During Specify/Plan, choose the feature-local
  `.process/` UAT runbook path and required platform/product rows.
- **What:** Autoheal trust boundary.
  **Why deferred:** Safe repair depends on matching source checksums and
  distinguishing safe file refreshes from unsafe install-cache drift.
  **Suggested next step:** During Plan, define which gaps can be autohealed and
  which must print manual remediation only.

## Recommended Next Step

Run setup's generated workflow:

```text
$speckit-autopilot docs/ai/specs/.process/XPLAT-008-workflow.md
```

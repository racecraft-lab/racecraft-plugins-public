# Feature Specification: Verification Coverage

**Feature Branch**: `tacd-004-verification-coverage`

**Created**: 2026-06-19

**Status**: Draft

**Input**: User description: "TACD-004 — Verification Coverage: lock the vendor-neutral capability-discovery contract with deterministic checks plus functional eval coverage, and repair the Claude payload-build defect with a regression check so neither can silently regress."

## User Scenarios & Testing *(mandatory)*

<!--
  User stories are prioritized as independently testable journeys. Each delivers
  standalone verification value: any one shipped alone still tightens the contract.
-->

### User Story 1 - Named-tool regression cannot land unnoticed (Priority: P1) [US1]

As a maintainer, I want a deterministic check that fails when active runtime guidance
reintroduces a hardcoded named optional-tool contract, so the vendor-neutral decision
established by the prior capability-discovery work cannot regress unnoticed.

**Why this priority**: This is the load-bearing guarantee of the whole feature. Without
it, a single future edit to an active agent can quietly reinstate a named-vendor
optional-tool preference and no automated signal would catch it. It directly satisfies
the primary acceptance criterion (AC-4.1).

**Independent Test**: Add a fixture in which an active Claude or Codex agent names a
specific optional vendor tool (e.g., a `mcp__<vendor>__*` preference) outside the
approved category allowlist, run the deterministic suite, and confirm the named-tool
guard FAILS. Revert the fixture and confirm the suite returns to green. Separately,
confirm the guard does NOT fire on allowed content (the generic `mcp` vocabulary and
exact schema/dependency metadata identifiers).

**Acceptance Scenarios**:

1. **Given** active agent guidance that reintroduces a hardcoded named optional-tool
   preference outside the approved category allowlist, **When** the deterministic suite
   runs, **Then** the named-tool guard fails with a message identifying the offending
   file and token.
2. **Given** active agent guidance that uses only the generic `mcp` vocabulary and no
   named vendor tool, **When** the deterministic suite runs, **Then** the named-tool
   guard passes (no false positive).
3. **Given** content that legitimately retains a concrete tool identifier required by
   platform schema or dependency metadata, **When** the deterministic suite runs,
   **Then** the named-tool guard treats it as allowed and does not fail.
4. **Given** the current repository state with the named MCP tool assertions removed
   from the tool-scoping contract, **When** the tool-scoping checks run, **Then** they
   no longer require any specific vendor MCP set by name.

---

### User Story 2 - Directive pointers are proven to exist and resolve (Priority: P1) [US2]

As a maintainer, I want structural checks proving every active agent points to the
shared capability-discovery directive (or an enumerated approved equivalent) and that
the pointer resolves from the installed payload layout, so the directive cannot be
silently orphaned or moved out from under the agents that depend on it.

**Why this priority**: A guard against named tools is only half the contract; the other
half is that agents actually reference the shared directive and that the reference
resolves at the path each runtime loads it from. This satisfies AC-4.2 and protects
consumers who install the built payload, not just the source tree.

**Independent Test**: Run the pointer-coverage checks against the active-agent
inventory and confirm each agent references `capability-discovery.md` or an enumerated
approved equivalent; then break a pointer (rename or remove the directive at a
referenced path inside the built payload) and confirm the target-resolution check
FAILS for both Claude and Codex layouts.

**Acceptance Scenarios**:

1. **Given** the active-agent inventory, **When** the pointer-coverage check runs,
   **Then** every active agent is confirmed to reference `capability-discovery.md` or an
   enumerated approved equivalent.
2. **Given** an active agent that references no directive and no approved equivalent,
   **When** the pointer-coverage check runs, **Then** the check fails and names the
   uncovered agent.
3. **Given** the built payload trees for Claude and Codex, **When** the
   target-resolution check runs, **Then** the referenced directive is confirmed to exist
   at the path each runtime loads it from.
4. **Given** a referenced directive path that does not resolve inside the built Claude
   or Codex payload, **When** the target-resolution check runs, **Then** the check fails
   and identifies the unresolved path.

---

### User Story 3 - Eval expectations enforce vendor-neutral, capability-first answers (Priority: P2) [US3]

As a maintainer, I want the functional eval expectations rewritten so optional-tool
answers are vendor-neutral, asserting both the absence of a preferred named set and an
affirmative capability-first answer, with behavior-observable scenarios that exercise
discovery, fallback, evidence path, citations, and lowered confidence.

**Why this priority**: Deterministic guards lock the static contract; the evals lock the
observable behavior. Rewriting all four eval files and adding behavior scenarios
satisfies AC-4.3 and prevents the evals from re-teaching a named-vendor preference.

**Independent Test**: Inspect each of the four eval files (autopilot and coach, Claude
and Codex) and confirm each optional-tool expected output asserts both the absence of a
preferred named set and an affirmative capability-first answer; confirm the five
behavior-observable scenarios (installed-capability discovery, fallback when named tools
are unavailable, evidence path, citations/local-file references, and lowered confidence
when fallback quality is lower) are present as committed fixtures and validate without a
live model run.

**Acceptance Scenarios**:

1. **Given** any rewritten optional-tool eval expected output, **When** it is evaluated,
   **Then** it asserts BOTH the absence of a preferred named-tool set AND an affirmative
   capability-first answer.
2. **Given** the four eval files, **When** their optional-tool expectations are compared,
   **Then** Claude and Codex are in parity (equivalent expectations for the same
   scenario across both runtimes).
3. **Given** the five behavior-observable scenarios, **When** they are validated against
   committed fixtures, **Then** each scenario validates without requiring a live model
   run, and no live run gates merge.

---

### User Story 4 - Installed skills ship complete bodies (Priority: P1) [US4]

As a consumer, I want every installed skill to ship its full body, with a deterministic
check that fails if the Claude payload truncates a SKILL.md, so that installing or
updating the plugin never delivers an empty-bodied skill.

**Why this priority**: The payload builder currently truncates the Claude SKILL.md body
for every skill whose guard-block terminator phrase is line-wrapped across two source
lines, so most Claude skills install with empty bodies — a consumer-facing defect.
Fixing the builder and adding a regression check satisfies SC-Payload and prevents a
silent recurrence.

**Independent Test**: Rebuild the payload from source and confirm every built Claude
SKILL.md retains its full body (the last non-guard source heading survives, body length
is within tolerance of source-minus-guard); then introduce a deliberately truncated
built SKILL.md and confirm the body-completeness check FAILS.

**Acceptance Scenarios**:

1. **Given** a source SKILL.md whose Codex guard-block terminator phrase is line-wrapped
   across two lines, **When** the payload is rebuilt from source, **Then** the built
   Claude SKILL.md strips only the Codex guard block and retains the full skill body.
2. **Given** the rebuilt payload, **When** the body-completeness check runs, **Then** it
   passes for every built Claude SKILL.md (last non-guard source heading present; body
   within tolerance of source-minus-guard).
3. **Given** a built Claude SKILL.md that is truncated relative to its source minus the
   guard section, **When** the body-completeness check runs, **Then** the check fails and
   identifies the truncated skill.
4. **Given** the default deterministic suite, **When** it runs after the fix and rebuild,
   **Then** it passes without depending on any live AI eval execution.

---

### Edge Cases

- **Guard terminator line-wrap**: When the Codex guard-block terminator phrase is
  line-wrapped across two source lines, the strip MUST still stop at the guard block's
  section boundary (next heading or EOF) and never run to end-of-file.
- **Generic `mcp` vocabulary**: When guidance uses the generic word `mcp` (or
  `MCP`) without naming a specific vendor tool, the named-tool guard MUST treat it as
  allowed.
- **Legitimate concrete identifiers**: When a concrete tool identifier is required by
  platform schema metadata, dependency metadata, an exact file reference, a fixture, or
  historical provenance, the named-tool guard MUST NOT flag it.
- **Approved equivalent pointer**: When an active agent legitimately carries an approved
  runtime-specific equivalent instead of a literal `capability-discovery.md` reference,
  the pointer-coverage check MUST accept it via the enumerated allowlist.
- **Unresolved payload path**: When a referenced directive path is correct in source but
  absent in the built payload, the target-resolution check MUST fail rather than pass on
  source-tree presence alone.
- **Skill with no guard block**: When a source SKILL.md contains no Codex guard block,
  the builder MUST leave the body untouched and the body-completeness check MUST still
  pass.
- **Live eval unavailability**: When no live model runner is available, the default
  deterministic suite MUST still run to completion (no scenario depends on a live run).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The verification suite MUST include a deterministic check (a tool-scoping
  named-tool guard plus a structural check) that FAILS when active Claude or Codex agent
  guidance reintroduces a hardcoded named optional-tool preference outside the approved
  category allowlist, with false-positive guards so that exact schema/dependency metadata
  identifiers and the generic `mcp` vocabulary remain allowed. [US1]
- **FR-002**: The tool-scoping contract MUST be reworked so it no longer requires a
  specific vendor MCP set by name — the named MCP tool assertions are removed entirely
  from the tool-scoping checks. [US1]
- **FR-003**: The verification suite MUST include static pointer-coverage checks proving
  each capability-dependent active agent references `capability-discovery.md` or an
  enumerated approved equivalent. The in-scope set is the agents whose work is governed
  by the directive (research / context-gathering / consensus / gate-remediation agents);
  agents that perform no capability-dependent work (terminal validation or synthesis-only
  workers that gather no external context) are explicitly out of pointer scope and MUST
  be listed in an enumerated exclusion set with a one-line reason each, so "uncovered"
  cannot be confused with "out of scope." The approved-equivalent allowlist MUST be
  enumerated literally and kept minimal: it MUST NOT be widened to silence an in-scope
  agent that simply omits the pointer (see FR-012). [US2]
- **FR-004**: The verification suite MUST include target-resolution checks proving the
  referenced directive resolves and exists at the path each runtime loads it from inside
  the built Claude payload and the built Codex payload. "The path each runtime loads it
  from" is the agent's in-source, repo-root-relative path token (today
  `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`, cited
  verbatim by both the Claude `.md` agents and the Codex `.toml` "equivalent" line)
  re-rooted under each built tree — i.e. the check asserts `dist/claude/<path-token>` AND
  `dist/codex/<path-token>` both exist. Resolution is this prefix re-rooting (the builder
  copies source under `dist/<runtime>/` preserving the `speckit-pro/**` sub-path), NOT a
  runtime-relative `../references/…` walk; no active agent uses a runtime-relative
  reference. The check MUST fail when a path is correct in source but absent in either
  built tree. [US2]
- **FR-005**: The optional-tool eval expected outputs across all four eval files MUST be
  rewritten so each asserts BOTH the absence of a preferred named-tool set AND an
  affirmative capability-first answer. [US3]
- **FR-006**: The eval coverage MUST include behavior-observable scenarios for
  installed-capability discovery, fallback when named tools are unavailable, evidence
  path, citations/local-file references, and lowered confidence when fallback quality is
  lower; these MUST be validated by committed fixtures and MUST NOT require a live model
  run to gate merge. [US3]
- **FR-007**: The payload builder's guard-stripping step MUST be fixed to strip only the
  Codex guard block (to the next heading or end-of-file) instead of truncating to
  end-of-file, and the built payload MUST be regenerated from source via the build script
  so all skill bodies are restored. [US4]
- **FR-008**: The verification suite MUST include a deterministic body-completeness check
  that FAILS if any built Claude SKILL.md is truncated relative to its source minus the
  guard section. The length-tolerance baseline MUST be computed PER SKILL from that
  skill's own guard-section boundary (source line count minus the lines of its stripped
  guard section), never from a single fixed line-count constant shared across skills, so
  the check does not flake across skills of differing size or guard-section length. The
  guard-section boundary used by this check MUST be the same heading-to-next-`##`/EOF
  boundary the builder's guard-stripping step uses (FR-007), so the check and the builder
  cannot disagree on what was stripped. [US4]
- **FR-009**: Every eval and every pointer/resolution check MUST maintain Claude/Codex
  parity (equivalent expectations and coverage across both runtimes). [US2] [US3]
- **FR-010**: The default deterministic suite MUST remain green without depending on live
  AI eval execution. [US1] [US2] [US3] [US4]
- **FR-011**: All new and reworked verification MUST extend the existing deterministic
  test surfaces in place; no new test layer and no broad scanner are introduced. Each new
  Layer 1 validator MUST be REGISTERED in the suite runner (`tests/speckit-pro/run-all.sh`,
  which enumerates Layer 1 validators explicitly) so it actually executes in the default
  run — a validator file that exists but is not registered does not satisfy this
  requirement. [US1] [US2] [US4]
- **FR-012**: Each new deterministic guard MUST be non-vacuous: a deliberate regression
  (a named tool re-added, a missing or unresolved directive pointer, a truncated payload)
  MUST make the corresponding guard fail. Each guard MUST also be fail-closed: if its
  input set is empty or missing (e.g., the active-agent glob matches nothing, a referenced
  `dist/**` target is absent, or a `jq`/file read fails), the guard MUST fail rather than
  silently report success on zero work, so a guard cannot pass vacuously by examining
  nothing. The validators rely on `set -euo pipefail` and explicit empty-set / missing-
  target assertions to enforce this. [US1] [US2] [US4]
- **FR-013**: The built payload MUST be regenerated only from source via the build
  script; built payloads MUST NOT be hand-edited. [US4]

### Reviewability Notes *(if applicable)*

Reviewability-Exception: infra

- This `infra` exception (operator-approved at PR time) covers the **file-count** dimension
  only. The final diff touches 36 files, but that count is inflated by source-derived
  `dist/**` regeneration (9 files, excepted per FR-013) and the SDD process trail (16
  spec/plan/tasks/checklist/MOC/workflow/UAT artifacts). The actual reviewable code surface
  is **10 files / ~4 production LOC (1 production file)** — well within the reviewable-LOC
  and production-file budgets. The change is one cohesive verification-coverage slice
  (atomicity route `one-navigable-PR`); splitting would fragment the contract without
  reducing review risk.
- Generated built payloads under the Claude and Codex payload trees are source-derived
  regeneration and are excepted from reviewable LOC; they are produced solely by re-running
  the build script, never by hand.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: docs/process (spec and workflow process artifacts only;
  no docs-wording changes to shipped guidance)
- **Projected reviewable LOC**: ~292 (extends the roadmap baseline of ~202 by ~90 for the
  guard-stripping fix and the body-completeness validator; generated payload regeneration
  excluded)
- **Projected production files**: 1 (the payload build script)
- **Projected total files**: ~10
- **Budget result**: within budget (under the warn thresholds of 400 reviewable LOC / 6
  production files / 15 total files; the single existing warning is the two primary
  surfaces noted in the setup gate, which is non-blocking)
- **Split decision**: Remains one spec. The named-tool guard, the pointer/resolution
  checks, the eval rewrites, and the bundled payload fix are a single cohesive
  verification-coverage slice that locks one contract; splitting would fragment the
  contract across PRs without reducing review risk. The payload fix is bundled here
  (rather than a separate hotfix branch) per the resolved scope decision.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget,
  traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion (AC-4.1 through
  AC-4.4 and SC-Payload) to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (AC-4.1)**: The deterministic suite fails when active runtime guidance
  reintroduces a hardcoded named-tool contract outside the approved category allowlist,
  and passes when guidance is vendor-neutral — demonstrated by a deliberate regression
  fixture that flips the result. [US1] [FR-001] [FR-002] [FR-012]
- **SC-002 (AC-4.2)**: Structural and tool-scoping checks verify that relevant Claude and
  Codex agents point to the approved capability-discovery directive (or an approved
  equivalent) and that the pointer resolves from the built payload layout — demonstrated
  by a broken-pointer regression that makes the resolution check fail for both runtimes.
  [US2] [FR-003] [FR-004] [FR-009] [FR-012]
- **SC-003 (AC-4.3)**: Functional evals prove SpecKit Pro answers optional-tool questions
  in vendor-neutral terms and describes installed-capability discovery plus fallback
  behavior — every rewritten optional-tool expectation across all four eval files asserts
  both the absence of a named set and an affirmative capability-first answer, validated by
  committed fixtures with no live run gating merge. [US3] [FR-005] [FR-006] [FR-009]
- **SC-004 (AC-4.4)**: The default deterministic suite passes
  (`bash tests/speckit-pro/run-all.sh`) without depending on live AI eval execution.
  [US1] [US2] [US3] [US4] [FR-010] [FR-011]
- **SC-005 (SC-Payload)**: The guard-stripping step strips only the Codex guard block; the
  built payload is rebuilt so all skills retain their bodies; and a deterministic
  body-completeness check fails if any built Claude SKILL.md is truncated relative to its
  source minus the guard section — demonstrated by a truncated-payload regression that
  makes the check fail. [US4] [FR-007] [FR-008] [FR-013] [FR-012]

## Assumptions

- **Approved category allowlist**: The named-tool guard's allowlist of approved tool
  categories is the spike-approved category allowlist established by the earlier
  capability-discovery work; this feature reuses it rather than redefining it.
- **Approved-equivalent allowlist**: The enumerated set of approved runtime-specific
  equivalents to a literal `capability-discovery.md` reference is kept as small as the
  actual capability-dependent agent inventory requires. An entry is LEGITIMATE only when
  the agent demonstrably carries the capability-first guidance in a machine-checkable form
  (for the Codex TOML runtime this is the literal "Capability discovery equivalent:
  mirrors …/capability-discovery.md" line; for Claude it is the literal path reference).
  An agent that carries neither the literal reference nor a real equivalent is NOT
  allowlisted to pass — it either gains the pointer or is recorded in the out-of-scope
  exclusion set with a reason. The allowlist and the exclusion set are both literal
  enumerations in the validator (not heuristics) so they stay auditable, and neither may
  be widened merely to turn a red check green. If every capability-dependent agent
  references the directive directly, the equivalent-allowlist is empty.
- **"Active agent" inventory**: "Active" refers to the agents that ship in the built
  payloads (and their source), excluding archived, historical, or provenance material.
  The pointer-coverage in-scope subset is the capability-dependent agents within that
  inventory; non-capability-dependent agents (e.g., `gate-validator`,
  `consensus-synthesizer`, `phase-executor`, `spec-context-analyst`, `uat-runbook-author`
  on the Claude side, and `phase-executor`, `spec-context-analyst`, `uat-runbook-author`,
  `autopilot-fast-helper` on the Codex side) are out of pointer scope per the directive's
  own applicability rule ("Use this directive whenever research or context gathering
  informs an answer …") and belong in the enumerated exclusion set.
- **Pointer rule**: "Points to the directive" means a literal path match to
  `capability-discovery.md` plus the small enumerated approved-equivalent allowlist above.
- **Target resolution model**: Resolution is verified against the directory layout each
  runtime loads from inside the built Claude and Codex payload trees, not merely the
  source tree.
- **Body-completeness assertion**: Completeness is anchored on a structural invariant (the
  last non-guard source heading is present in the built payload) and a tolerance band for
  body length (within tolerance of source-minus-guard), in preference to a brittle
  absolute line count; the only intended difference between source and built body is the
  stripped guard block.
- **Eval validation mode**: Committed-fixture / replay validation is sufficient for the
  behavior-observable scenarios; no live model run is introduced as a merge gate.
- **Eval parity scope**: Parity covers the four eval files for the autopilot and coach
  skills across Claude and Codex.
- **No behavior, prerequisite, or docs changes**: This feature changes verification and
  the payload build only; it does not change agent decision logic, prerequisite-script
  behavior, or the wording of shipped documentation.
- **Verification commands**: The default deterministic suite is
  `bash tests/speckit-pro/run-all.sh` (the structural, script-unit, and tool-scoping
  layers); the payload is rebuilt with the existing build script. No package-manager,
  build, typecheck, or lint toolchain exists or is added.
- **Generated payloads**: Built payloads are regenerated from source by the build script
  and are never hand-edited.

## Out of Scope

- Live AI eval execution as a merge gate.
- New test layers or broad harness rewrites.
- Rewriting historical/provenance or generated source-derived mentions of named tools.
- A separate hotfix branch for the payload defect (bundled into this feature per the
  resolved scope decision).
- Any change to agent decision logic, prerequisite-script behavior, or shipped
  documentation wording.

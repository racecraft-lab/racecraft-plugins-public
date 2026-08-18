# SpecKit Workflow: ART-004 — Gallery Completion — Design & Prototyping

**Template Version**: 1.0.0
**Created**: 2026-08-17
**Purpose**: Execute ART-004 through the SpecKit planning and implementation workflow.

---

## How to Use This Template

1. Run this workflow only from the dedicated worktree on branch
   "art-004-gallery-completion-design-prototyping".
2. This file is already populated from the ART-004 roadmap entry and its Grill
   Me interview. Do not reopen settled decisions during autonomous execution.
3. ART-004 is currently one combined slice. If the authoritative Plan
   reviewability gate blocks it, stop for a new human-approved split.
4. Track progress in the table below. The scaffold command does not execute any
   phase.

---

## Design Concept

The source of truth for Goals, Non-goals, the complete Q&A log, source
measurements, and Open Questions is:

~~~text
docs/ai/specs/.process/ART-004-design-concept.md
~~~

Re-read it before every phase. Grill Me is human-in-the-loop only and is not
part of autopilot. Clarifications after this point use /speckit-clarify and the
normal consensus protocol.

---

## Scope and Reviewability Decision

The combined slice owns:

- six new single-file gallery ports;
- the six matching manifest status flips;
- ART-020's five existing horizontal-scroll-container fixes across three
  shipped templates;
- the global Layer 4 keyboard-scroll assertion and its negative fixture;
- fill-region and gallery coverage;
- generated payloads, proofs, and reference artifacts; and
- manual file:// interaction and keyboard UAT.

The shared forward estimator used seven capability groups, twelve authored
files or surfaces, fourteen functional requirements, and a net-new
classification. It returned an 865-line estimate, status "warn", and three
suggested slices. The pinned upstream sources total 3,098 lines before the
Racecraft contract is applied.

The user nevertheless selected **one combined slice**. This is not an exception
to the repository gate. Plan MUST:

1. declare every actual file operation;
2. measure the combined shape with the authoritative reviewability gate;
3. record the evidence and threshold class; and
4. stop before Tasks if the result is "block", returning for a human-approved
   split without reducing functional fidelity or reactivating ART-020.

Projected reviewable LOC: 865

---

## Workflow Overview

| Phase | Command | Status | Notes |
|---|---|---|---|
| Specify | /speckit-specify | ✅ Complete | 14 requirements, 3 stories, 0 unresolved markers; G1 passed |
| Clarify | /speckit-clarify | ✅ Complete | 3 sessions, 15 accepted answers, 0 markers, no consensus fan-out; G2 passed |
| Plan | /speckit-plan | 🔄 In Progress | Mandatory declared-file reviewability decision |
| Checklist | /speckit-checklist | ⏳ Pending | UX, accessibility, error handling |
| Tasks | /speckit-tasks | ⏳ Pending | Only after a non-blocking plan |
| Analyze | /speckit-analyze | ⏳ Pending | Cross-check against the design concept |
| Confidence Gate | G6.5 | ⏳ Pending | Composite pre-implementation confidence |
| Implement | /speckit-implement | ⏳ Pending | Outside explicit `--stage plan`; mark skipped at the plan-stage boundary |
| Post | Post-Implementation | ⏳ Pending | Outside explicit `--stage plan`; mark skipped at the plan-stage boundary |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

G6.5 is advisory by default. Record its verdict in Phase 6.5.

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|---|---|---|
| G1 | After Specify | Stories and requirements are measurable; no unresolved markers |
| G2 | After Clarify | Slot, export, and assertion questions are resolved |
| G3 | After Plan | Constitution passes; actual scope is not blocked |
| G4 | After Checklist | Every Gap is resolved or explicitly out of scope |
| G5 | After Tasks | Requirements have ordered, testable task coverage |
| G6 | After Analyze | No critical inconsistency; warnings dispositioned |
| G6.5 | Before Implement | Composite confidence supports autonomous execution |
| G7 | After implementation | Suite and manual UAT pass; generated artifacts agree |

---

## Prerequisites

### Constitution Validation

Before each phase, verify alignment with ".specify/memory/constitution.md":

| Principle | ART-004 requirement | Verification |
|---|---|---|
| I. Plugin Structure Compliance | Gallery source and release payload remain structurally valid | ✅ Layer 1 baseline: 1,447/1,447 |
| II. Cross-Platform Runtime & Script Safety | Offline single-file artifacts; repository tooling stays Python 3.11+ stdlib | ✅ Layer 4 baseline: 5,766/5,766 |
| IV. Test Coverage Before Merge | Global assertion, negative fixture, manifest and fill coverage | ✅ Full baseline: 7,399/7,399 |
| V. Conventional Commits | Lowercase speckit-pro scope and plain-English title | ✅ Phase checkpoint subjects use the repository contract; final PR-title gate remains an implementation-stage task |
| VI. KISS, Simplicity & YAGNI | Functional fidelity with repeated samples compacted; no undeclared affordance | ✅ Scope is roadmap-backed; Plan and later code review re-check complexity |

**Constitution Check:** ✅ Verified before G1 on 2026-08-17.

### Worktree Preflight

- Repository tests need no bootstrap.
- Install docs-site dependencies only before a docs-site command:
  "pnpm --dir docs-site install --frozen-lockfile".
- The generated merge driver must remain configured with driver "exit 0".
- Regenerate generated artifacts from source. Never hand-edit a generated
  payload, installed-cache proof, or generated reference page.
- The upstream revision is pinned to
  "58c305be97f47b26b678f2c07dec01d4242268ec". Retrieve sources read-only into
  session scratch space; do not stage upstream originals.

### Autopilot Preflight Results

- **Stage:** `plan`, resolved from the explicit `--stage plan` argument.
- **Confidence gate:** `advisory` (project default).
- **Execution root:** the registered ART-004 worktree on branch
  `art-004-gallery-completion-design-prototyping`; the worktree was clean.
- **Archive Sweep:** direct extension-contract sweep completed. BRAND-001 is a
  previously merged archive candidate (PR #432); ART-004 was excluded as the
  current target. No cleanup was requested or applied.
- **Agent runtime:** all ten required Codex agents matched the installed
  `gpt-5.5` bundle; dry-run install status was `no_op`.
- **Project commands:** BUILD, TYPECHECK, LINT, and INTEGRATION_TEST are `N/A`;
  UNIT_TEST and FULL_VERIFY are `python3 tests/speckit-pro/run-all.py`.
- **Reviewability:** the repository-level setup gate returned `warn` and passed
  G0. The ART-004 865-LOC forward projection independently crosses the current
  800-LOC block threshold, so it is risk evidence only; Phase 3 must replace it
  with the declared-file Plan verdict and stop before Tasks if that verdict is
  `block`.
- **Capability path:** repository/spec context uses local reads and installed
  analysts; pinned upstream source extraction uses GitHub plus the exact commit;
  library and external-domain questions use installed documentation/web
  capabilities when the phase requires them.

---

## Specification Context

### Basic Information

| Field | Value |
|---|---|
| **Spec ID** | ART-004 |
| **Name** | Gallery Completion — Design & Prototyping |
| **Branch** | art-004-gallery-completion-design-prototyping |
| **Dependencies** | ART-001 |
| **Absorbs** | ART-020, to be marked superseded |
| **Enables** | Gallery completeness |
| **Priority** | P2 |
| **Stage** | plan |

### Success Criteria Summary

- [ ] Six named gallery files exist as self-contained, offline HTML artifacts.
- [ ] Every distinct pinned-upstream section and interaction is preserved;
      repeated sample data may be compacted.
- [ ] Each new artifact embeds both canonical blocks byte for byte and carries
      correct upstream attribution.
- [ ] visual-designs exports one selected direction and rationale as prompt and
      Markdown.
- [ ] component-variants displays all required states and exports one selected
      base variant and rationale as prompt and Markdown.
- [ ] The other four new artifacts expose no export affordance.
- [ ] All horizontal scroll containers are keyboard reachable and accessibly
      named, including ART-020's five existing affected containers.
- [ ] The Layer 4 global assertion fails on its negative fixture and passes for
      every shipped artifact.
- [ ] Exactly six manifest values flip from planned to shipped; no other field
      in those rows changes.
- [ ] Full suite, payload consistency, and manual file:// UAT pass.
- [ ] ART-020 is recorded as superseded by ART-004.

---

## Phase 1: Specify

**When to run:** First. Focus on what readers and maintainers must be able to
do and observe. Output:
"specs/art-004-gallery-completion-design-prototyping/spec.md".

### Specify Prompt

~~~text
/speckit-specify

## Feature: ART-004 Gallery Completion — Design & Prototyping

Read docs/ai/specs/.process/ART-004-design-concept.md first. Treat every recorded
user answer as fixed.

### Problem Statement
The gallery catalog already promises six design and prototyping artifacts, but
their files do not exist. Readers cannot inspect visual directions, a rendered
design system, complete component states, motion timing, a clickable flow, or
an SVG illustration from the plugin. Five horizontal scroll containers in
three shipped artifacts are also unreachable to keyboard-only Safari users, and
there is no global guard stopping the six new ports from repeating the defect.

### Users and user stories
[US1] A keyboard-only reader can focus and horizontally scroll every wide
      region in the shipped gallery, including the five existing affected
      containers, and each focus stop has a meaningful accessible name.
[US2] A reader opens any of the six new files directly from file:// and can use
      every distinct section and interaction from the pinned upstream template,
      fully offline apart from optional typeface substitution.
[US3] A reader chooses one visual direction or one base component variant,
      records a rationale, and copies that live decision as either an actionable
      prompt or Markdown with a selectable fallback if clipboard access fails.

### Fixed product decisions
- Functional fidelity: preserve every distinct section and interaction, but
  compact repeated sample data and rewrite markup as needed. Do not drop a
  behavior or decision surface to fit the budget.
- Pin all six sources to upstream commit
  58c305be97f47b26b678f2c07dec01d4242268ec.
- visual-designs exports exactly one direction plus rationale.
- component-variants shows all states and exports one chosen base variant plus
  rationale.
- design-system, animation-prototype, interaction-prototype, and
  svg-illustrations are read-only and carry no export affordance.
- Absorb all of ART-020 and mark that roadmap entry superseded.
- Keep one combined slice now. If Plan blocks it, stop for a human-approved
  split; do not reduce fidelity and do not drop ART-020.

### Contract constraints
- One HTML file per artifact. No build step, bundler, sibling asset, or runtime
  dependency. It must work directly from file:// and remain readable offline.
- Embed BRAND-KIT and GALLERY-HEAD regions with markers, byte for byte.
- Each port changes exactly one existing catalog value: its status from planned
  to shipped. Identifiers and all other row values are stable.
- Use the exact five-label upstream attribution header and the matching source
  filename from manifest.json.
- Prompt and Markdown exports derive from live state, name the conclusion and
  rationale, include enough context to act without reopening the page, use the
  exact visible labels "Copy as prompt" and "Copy as Markdown", announce their
  result in text, and reveal a selectable fallback on clipboard refusal.
- Every horizontal overflow region is sequentially focusable and specifically
  named. Follow the shipped annotated-diff and flowchart pattern.
- Add a global Layer 4 assertion and a negative fixture; do not create a test
  named after ART-004 or ART-020.
- Regenerate release artifacts from authoritative source.
- Repository tooling stays Python 3.11+ standard library.

### Out of scope
- Workflow-stage routing.
- ART-005's seven ports.
- Vertical scroll containers.
- Any accessibility defect beyond the named horizontal-scroll issue.
- Changes to shared brand blocks, SPA-CONTRACT, signal vocabulary, IDs, stages,
  triggers, sources, when-to-use text, categories, or export declarations.
~~~

### Specify Results

| Metric | Value |
|---|---|
| Functional Requirements | 14 |
| User Stories | 3 |
| Acceptance Criteria | 9 |

### Files Generated

- [x] specs/art-004-gallery-completion-design-prototyping/spec.md

**G1 gate:** ✅ PASS — `spec.md` exists with zero
`[NEEDS CLARIFICATION]` markers.

**After-Specify hook:** The optional project doctor found all five templates,
the Python runner contract, and the constitution. It also reported the legacy
`.specify/init-options.json` Claude command-directory check as unavailable;
the Codex agent dry-run independently passed, so this optional integration
warning does not block the Codex workflow.

---

## Phase 2: Clarify

**When to run:** After Specify. Ask at most five questions per session.

### Session 1: Source structure and fill regions

~~~text
/speckit-clarify

Read the six pinned upstream files at commit
58c305be97f47b26b678f2c07dec01d4242268ec and resolve only:
1. The exact fill-region names and source artifact for each distinct section.
2. Which repeated sample groups may be compacted without losing a behavior.
3. Which elements are state-bearing or list slots under existing gallery tests.
4. The load-bearing IDs/classes required by each interaction.
5. How each port demonstrates functional fidelity in acceptance criteria.

Do not reopen the chosen revision, fidelity rule, export declarations, or
single-slice choice.
~~~

### Session 2: Decision exports

~~~text
/speckit-clarify

Resolve the exact serialization for visual-designs and component-variants:
1. Heading and field order for prompt output.
2. Heading and field order for Markdown output.
3. How the selected direction/base variant and rationale are read from live DOM
   state.
4. What validation and accessible feedback occur before a complete decision.
5. The selectable fallback behavior when clipboard access is refused.

Reuse the shipped code-approaches pattern where it satisfies the fixed
decisions. visual-designs exports one direction; component-variants exports one
base variant while still displaying every state.
~~~

### Session 3: Global keyboard-scroll guard

~~~text
/speckit-clarify

Inspect tests/speckit-pro/unit/test-artifact-gallery.py and neighboring fixtures.
Resolve:
1. How the test identifies every horizontal overflow container without a
   brittle CSS parser.
2. What focusability, role, and accessible-name conditions it asserts.
3. The smallest durable negative fixture proving a missing keyboard route is
   detected.
4. How the existing ART-003 keyboard harness is reused for manual UAT.
5. How the assertion covers all six new ports and the three repaired templates.

Keep the test and fixture named for durable keyboard-scroll behavior, never a
temporary spec ID.
~~~

### Clarify Results

| Session | Focus | Questions | Key outcomes |
|---|---|---|---|
| 1 | Source and fills | 5 | Locked fill/source inventory, compaction boundary, list/state slots, load-bearing selectors, and per-port fidelity evidence; no unresolved consensus items |
| 2 | Exports | 5 | Locked shared field order, format-specific lead lines, persistent live-state selection, accessible validation, focused fallback, and stale-invocation guard; no unresolved consensus items |
| 3 | Keyboard guard | 5 | Locked self-declared scrollers, focus/role/name contract, synthetic RED fixture, ART-003 browser-procedure reuse, and manifest-wide/non-vacuous coverage; no unresolved consensus items |

**G2 gate:** ✅ PASS — zero `[NEEDS CLARIFICATION]` markers remain and
all three sessions are recorded in `spec.md`.

---

## Phase 3: Plan

**When to run:** After Clarify. Output:
"specs/art-004-gallery-completion-design-prototyping/plan.md".

### Plan Prompt

~~~text
/speckit-plan

Read the roadmap, constitution, spec.md, and
docs/ai/specs/.process/ART-004-design-concept.md. Quote the selected interview
answers in the design rationale: "Functional fidelity", "Pin one commit",
"Base variant", "One direction", "Absorb ART-020", "Mark superseded",
"One combined slice", and "Stop and split".

## Tech stack
- Runtime: browser-native HTML, CSS, and JavaScript in one file per artifact.
- State: in-memory DOM state only; no persistence.
- Catalog: existing JSON manifest, with six status-only flips.
- Tests: Python 3.11+ standard-library Layer 1 and Layer 4 suites.
- UAT: direct file:// browser runs for controls, sliders, linked screens,
  clipboard fallback, focus order, and horizontal keyboard scrolling.
- Release: scripts/refresh-release-artifacts.py plus the required generated
  reference command when its tracked inputs change.

## Required architecture
- Treat each new HTML file as a self-contained vertical capability inside the
  one combined delivery slice.
- Copy canonical blocks verbatim; never refactor them into a shared runtime.
- Adapt pinned upstream mechanisms to existing Racecraft tokens and contract.
- Centralize no new production helper: the single-file rule requires local
  behavior, and the global keyboard rule belongs in repository validation.
- Apply the ART-020 repair before using its pattern in new ports.
- Serialize shared manifest, test, payload, proof, and generated-doc integration
  work; do not declare those files parallel-safe.

## Reviewability gate — mandatory stop
- Enumerate every NEW and MODIFIED file in Declared File Operations, including
  generated paths as generated rather than authored.
- Run the authoritative plan gate against plan.md.
- Reconcile its result with the six pinned sources totaling 3,098 lines and the
  forward estimate of 865.
- If blocked, write the evidence into plan.md, mark G3 blocked, stop the run,
  and request a new human-approved split. Do not proceed to Checklist or Tasks.
- Do not claim that the setup helper's full-roadmap result applies to ART-004.

## Verification design
- Red test: today's five existing containers fail the new global assertion.
- Green: all existing and new horizontal overflow containers are focusable and
  named; the negative fixture still proves the guard.
- Per-port manifest/file-presence, attribution, canonical-block, fill-region,
  export-declaration, and offline checks.
- Manual file:// matrix covering both themes, keyboard-only operation, slider
  behavior, linked screens, live selection/rationale exports, clipboard refusal,
  and horizontal arrow-key scrolling.
- Full suite and generated-artifact consistency at completion.

## Constraints
- Preserve all functional sections and interactions; only repeated sample
  volume may shrink.
- No dependency, framework, build step, sibling asset, active Bash, or jq.
- No hand edits to generated outputs.
- No roadmap work beyond ART-004 status/scope and ART-020 supersession.
~~~

### Plan Results

| Artifact | Status | Notes |
|---|---|---|
| plan.md | ⏳ | Must contain a gate verdict |
| research.md | ⏳ | Pinned-source and pattern evidence |
| data-model.md | ⏭️ likely skipped | DOM state only; justify |
| contracts/ | ⏳ | Export payload and gallery contract mapping if useful |
| quickstart.md | ⏳ | Direct file:// and verification instructions |

---

## Phase 4: Domain Checklists

Run only if G3 is non-blocking. Generate all three domains because this change
is interactive UI, has a named keyboard defect, and must degrade safely when
clipboard access is refused.

### UX Checklist

~~~text
/speckit-checklist ux

Focus on ART-004:
- Every distinct upstream section and interaction remains discoverable.
- visual-designs has one unambiguous direction selection and required rationale.
- component-variants displays all states while making the base-variant decision
  clear.
- Sliders and linked screens expose visible current state and reset behavior.
- Read-only artifacts contain no control that implies an unavailable export.
- Manual file:// UAT has observable outcomes for every interaction.
Pay special attention to functional-fidelity drift caused by sample compaction.
~~~

### Accessibility Checklist

~~~text
/speckit-checklist accessibility

Focus on ART-004:
- Every horizontal overflow container is in sequential focus order and named.
- The global guard and negative fixture prove that invariant durably.
- Selection, slider, linked-screen, copy, and fallback controls are keyboard
  operable with visible focus.
- Names, roles, states, labels, live status, reduced motion, and non-color
  meaning are complete.
- Both themes retain WCAG AA pairings supplied by the audited brand kit.
Pay special attention to Safari keyboard reachability and motion controls.
~~~

### Error-Handling Checklist

~~~text
/speckit-checklist error-handling

Focus on ART-004:
- Clipboard refusal reveals the exact live payload in a selectable field.
- Empty selection or rationale produces accessible, actionable validation.
- Offline font failure leaves every artifact readable and functional.
- Invalid or incomplete interactive state never produces a misleading export.
- Generated-artifact and manifest drift fail loudly in validation.
Pay special attention to behavior under file:// security restrictions.
~~~

### Checklist Results

| Checklist | Items | Gaps | Spec references |
|---|---|---|---|
| ux | | | |
| accessibility | | | |
| error-handling | | | |
| **Total** | | | |

Resolve every Gap in spec.md or plan.md and rerun its checklist before G4.

---

## Phase 5: Tasks

**When to run:** Only after all checklist gaps close and G3 remains
non-blocking.

### Tasks Prompt

~~~text
/speckit-tasks

Read spec.md, plan.md, and
docs/ai/specs/.process/ART-004-design-concept.md. Generate small,
dependency-ordered, testable tasks grouped by user story.

## Required TDD ordering
1. [US1] RED: extend the durable Layer 4 keyboard-scroll assertion and add its
   negative fixture so today's five affected containers fail.
2. [US1] GREEN: repair the five containers in code-approaches,
   implementation-plan, and module-map; reuse the existing accessible pattern.
3. [US2] For each read-only port, add failing manifest/fill/contract coverage
   before the minimum functional-fidelity HTML.
4. [US3] For each decision port, add failing export and live-state coverage
   before the minimum implementation.
5. Integration: perform six status-only manifest flips, regenerate authoritative
   artifacts, run the complete suite, and execute the file:// UAT matrix.

## Constraints
- Keep ART-004 one combined branch and delivery slice.
- A task may be [P] only when it touches no shared manifest, shared test literal,
  generated output, payload, proof, or documentation surface.
- Never mark the six HTML ports parallel if their results would concurrently
  edit the same catalog or generated artifact.
- Every functional requirement and user story needs task coverage.
- Use durable capability names for tests and fixtures; never ART-004 or ART-020.
- Include explicit RED, GREEN, REFACTOR, VERIFY checkpoints.
- Include a final task validating the exact prospective PR title against the
  release-readiness gate.
~~~

### Tasks Results

| Metric | Value |
|---|---|
| Total Tasks | |
| Phases | |
| Parallel Opportunities | |
| User Stories Covered | |

---

## Atomicity Route

Autopilot fills this after Tasks by running the read-only classifier against:

~~~text
runner helper atomicity-route specs/art-004-gallery-completion-design-prototyping
~~~

The user selected one combined slice for scaffold. The classifier is evidence,
not permission to override Q8 or Q9.

| Field | Value | Meaning |
|---|---|---|
| **Route** | | Classifier route |
| **Releasable** | | true or false |
| **Signals** | | Decisive structural findings |
| **Warnings** | | Release-safety warnings |

---

## Phase 6: Analyze

### Analyze Prompt

~~~text
/speckit-analyze

Cross-check spec.md, plan.md, tasks.md, and
docs/ai/specs/.process/ART-004-design-concept.md.

Focus on:
1. No artifact, section, or interaction lost from the functional-fidelity rule.
2. Exact traceability for the five ART-020 fixes, global guard, and fixture.
3. Exact traceability for both decision exports and all four read-only entries.
4. Manifest operations limited to six status flips.
5. Shared integration tasks are serialized and generated outputs are regenerated.
6. Accessibility, offline, clipboard-failure, and manual UAT requirements all
   have tasks and observable acceptance evidence.
7. Reviewability evidence is current. If the plan is blocked, report CRITICAL
   and stop rather than rationalizing the combined slice.
8. No design-concept answer was contradicted or silently omitted.
~~~

### Analysis Results

| ID | Severity | Issue | Resolution |
|---|---|---|---|
| | | | |

---

## Phase 6.5: Confidence Gate

| Field | Value |
|---|---|
| Mode | |
| Composite confidence | |
| Verdict | |
| Evidence | |

Do not proceed on a "stop" verdict or while the reviewability decision remains
unresolved.

---

## Phase 7: Implement

### Implement Prompt

~~~text
/speckit-implement

Read tasks.md, plan.md, spec.md, and the ART-004 design concept. Preserve the
reason behind every selected answer, especially functional fidelity, the two
single-decision export shapes, ART-020 ownership, and the fail-closed gate rule.

For every task:
1. RED: add or identify a failing assertion that defines the behavior.
2. GREEN: make the smallest change that passes.
3. REFACTOR: remove duplication only where the single-file contract permits.
4. VERIFY: run the smallest relevant layer and its manual acceptance step.

Pre-implementation:
- Confirm the exact worktree and branch.
- Confirm G0 baseline and that G3/G6.5 permit implementation.
- Retrieve only the six pinned upstream sources into scratch space.
- Preserve unrelated user changes.

Implementation:
- Repair and guard keyboard scrolling first.
- Port functional behavior, not upstream sample volume or brand styling.
- Copy canonical regions verbatim and use only existing brand tokens.
- Implement no export for entries declaring an empty export list.
- Derive both decision exports from live state and exercise clipboard refusal.
- Serialize manifest, shared tests, generation, payload, proof, and docs work.
- Use apply_patch for authored edits; regenerate generated surfaces with their
  authoritative commands.

Final verification:
- python3 tests/speckit-pro/run-all.py
- python3 scripts/refresh-release-artifacts.py when payload inputs changed
- pnpm --dir docs-site reference:generate when its tracked inputs changed
- manual file:// matrix for all six ports and the three repaired artifacts
- release-readiness validation of the exact final PR title
~~~

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|---|---|---|---|
| 1 - Keyboard-scroll guard and repair | | | |
| 2 - Read-only ports | | | |
| 3 - Decision ports | | | |
| 4 - Shared integration and UAT | | | |

---

## Post-Implementation Checklist

| Canonical Item | Status | Evidence |
|---|---|---|
| Post: Doctor Extension Check | ⏭️ Skipped | Outside explicit `--stage plan` |
| Post: Verify Implementation | ⏭️ Skipped | Outside explicit `--stage plan` |
| Post: Verify Tasks Phantom Check | ⏭️ Skipped | Outside explicit `--stage plan` |
| Post: Code Review | ⏭️ Skipped | Outside explicit `--stage plan` |
| Post: Integration Suite | ⏭️ Skipped | Outside explicit `--stage plan` |
| Post: Reviewability Diff Gate | ⏭️ Skipped | Outside explicit `--stage plan` |
| Post: Self-Review | ⏭️ Skipped | Outside explicit `--stage plan` |
| Post: UAT Runbook Generation | ⏭️ Skipped | Outside explicit `--stage plan` |
| Post: Final Reviewability Backstop | ⏭️ Skipped | Outside explicit `--stage plan` |
| Post: PR Packet/Body Generation | ⏭️ Skipped | Outside explicit `--stage plan` |
| Post: PR Body Generation | ⏭️ Skipped | Outside explicit `--stage plan` |
| Post: PR Creation | ⏭️ Skipped | Outside explicit `--stage plan` |
| Post: Review Remediation | ⏭️ Skipped | Outside explicit `--stage plan` |
| Post: Retrospective | ⏭️ Skipped | Outside explicit `--stage plan` |

- [ ] All tasks complete.
- [ ] Layer 1 and Layer 4 pass.
- [ ] Full Python-authoritative suite passes.
- [ ] Generated artifact consistency passes.
- [ ] Manual file:// UAT passes.
- [ ] Exact PR title passes release readiness.
- [ ] ART-004 roadmap and MOC state agree.

---

## Lessons Learned

### What Worked Well

-

### Challenges Encountered

-

### Patterns to Reuse

-

---

## Project Structure Reference

~~~text
speckit-pro/artifact-gallery/
├── SPA-CONTRACT.md
├── brand-kit.css
├── manifest.json
├── theme-toggle.html
└── templates/
tests/speckit-pro/unit/
docs/ai/specs/.process/
specs/art-004-gallery-completion-design-prototyping/
~~~

This file was instantiated from the shared SpecKit workflow template and
enriched with ART-004's roadmap and human-validated design decisions.

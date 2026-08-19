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
3. ART-004 is now three ordered slices. The original combined plan blocked at
   G3, and the user approved the three-slice recovery on 2026-08-17.
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

ART-004 as a whole owns:

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

The original interview selected **one combined slice**. This was not an
exception to the repository gate. The first Plan attempt declared 865
reviewable LOC and 9 production files, so G3 blocked exactly as Q9 required.

On 2026-08-17, the user approved this replacement topology:

| Slice | Scope | Ordering reason |
|---|---|---|
| 1 — Keyboard foundation | ART-020's five container repairs, the global Layer 4 guard, negative fixture, and keyboard UAT | Establishes the accessibility pattern before any port uses it |
| 2 — Read-only ports | `design-system`, `animation-prototype`, `interaction-prototype`, and `svg-illustrations` | Groups the four entries whose manifest export declaration is empty |
| 3 — Decision ports | `visual-designs` and `component-variants`, including live-state prompt/Markdown exports and clipboard fallback | Isolates the two higher-interaction export carriers |

Manifest, shared tests, payload, proof, and generated-doc integration remain
serialized across the ordered slices. This approval changes review topology,
not functional fidelity, ART-020 ownership, or export behavior. The resumed
Plan MUST:

1. declare every actual file operation per slice;
2. produce durable per-slice reviewability inputs and run the authoritative
   gate against all three;
3. record every result and threshold class; and
4. stop before Checklist if any approved slice still returns `block`.

Historical combined projection: 865 reviewable LOC. It is failure evidence,
not authority for any individual approved slice.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|---|---|---|---|
| Specify | /speckit-specify | ✅ Complete | 14 initial requirements, 3 stories, 0 unresolved markers; Checklist remediation raised the current requirement total to 17 |
| Clarify | /speckit-clarify | ✅ Complete | 3 sessions, 15 accepted answers, 0 markers, no consensus fan-out; G2 passed |
| Plan | /speckit-plan | ✅ Complete | G3 passed for three approved slices: 160 pass, 590 warn, 520 warn; no blockers |
| Checklist | /speckit-checklist | ✅ Complete | 111 checks; 16 gaps fixed; 0 remaining; G4 passed |
| Tasks | /speckit-tasks | ✅ Complete | 60 tasks, 17/17 requirements, 3/3 stories, 9 safe parallel tasks; G5 passed |
| Analyze | /speckit-analyze | ✅ Complete | Executor clean, G6 passed, and required clean-pass confidence synthesis completed |
| Confidence Gate | G6.5 | ✅ Complete | Advisory gate passed at 1.00 against the 0.90 threshold |
| Implement | /speckit-implement | ✅ Complete | T001-T060 complete; post-merge suite 7628/7628 and all release/reference/title gates pass |
| Post | Post-Implementation | ✅ Complete | All 14 canonical items are closed; draft PR #450 is open, review remediation is resolved, and the retrospective reports 100% spec adherence |

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
| V. Conventional Commits | Lowercase scope and plain-English title | ✅ `feat(art-004): complete design gallery artifacts` passes both final title gates |
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

- **Stage:** `implement`, resolved from the explicit `--stage implement`
  argument. The recorded `✅ Complete` G6.5 verdict was read and not rerun.
- **Confidence gate:** `advisory` (project default).
- **Execution root:** the registered ART-004 worktree on branch
  `art-004-gallery-completion-design-prototyping`; the worktree was clean.
- **Archive Sweep:** direct extension-contract sweep completed with no archive
  candidates. ART-004 was excluded as the current target. BRAND-001 remains
  active work: PR #432 merged its planning package, while its roadmap still
  records all seven phases as pending. No cleanup was requested or applied.
- **Agent runtime:** all ten required Codex agents matched the installed
  user-level `gpt-5.5` bundle; dry-run install status was `no_op`.
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
- **Tier-2 relocation:** suppressed because ART-004 is the active feature and
  its `SPEC-MOC.md` already declares `structureVersion: 1`.

---

## Specification Context

### Basic Information

| Field | Value |
|---|---|
| **Spec ID** | ART-004 |
| **Name** | Gallery Completion — Design & Prototyping |
| **Branch** | art-004-gallery-completion-design-prototyping |
| **Draft PR** | [#450](https://github.com/racecraft-lab/racecraft-plugins-public/pull/450) |
| **Dependencies** | ART-001 |
| **Absorbs** | ART-020, to be marked superseded |
| **Enables** | Gallery completeness |
| **Priority** | P2 |
| **Stage** | implement |

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
"One combined slice", and "Stop and split". Preserve the first topology as
historical evidence, then record the user's 2026-08-17 recovery decision:
"approve three slices".

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
- Treat each new HTML file as a self-contained vertical capability inside its
  approved ordered slice: keyboard foundation, four read-only ports, then two
  decision/export ports.
- Copy canonical blocks verbatim; never refactor them into a shared runtime.
- Adapt pinned upstream mechanisms to existing Racecraft tokens and contract.
- Centralize no new production helper: the single-file rule requires local
  behavior, and the global keyboard rule belongs in repository validation.
- Apply the ART-020 repair before using its pattern in new ports.
- Serialize shared manifest, test, payload, proof, and generated-doc integration
  work across slice order; do not declare those files parallel-safe.

## Reviewability gate — mandatory stop
- Enumerate every NEW and MODIFIED file per slice in Declared File Operations,
  including generated paths as generated rather than authored.
- Create durable, unambiguous gate input for each approved slice and run the
  authoritative plan gate against all three inputs.
- Reconcile the per-slice results with the six pinned sources totaling 3,098
  lines and the blocked combined estimate of 865.
- If any slice remains blocked, write the evidence into plan.md, mark G3
  blocked, and stop again. Do not proceed to Checklist or Tasks.
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
| plan.md | ✅ Complete | Failed combined topology retained as history; approved three-slice operations and ordering are authoritative |
| research.md | ✅ Complete | Pinned-source and shipped-pattern evidence |
| data-model.md | ✅ Complete | DOM state, manifest state, and keyboard-scroll declaration model |
| contracts/ | ✅ Complete | Gallery, decision-export, keyboard-scroll, and three durable slice-gate contracts |
| `docs/ai/specs/.process/ART-004-manual-uat.md` | ✅ Complete | Ordered slice execution, direct `file://`, suite, UAT, and regeneration instructions |

Plan-phase evidence:

- Structure validation found `plan.md` with zero unresolved markers.
- The advisory estimator returned `status=pass`, `projected=0`, and
  `production=0` for 11 declared authored operations. Its current classifier
  does not recognize this feature's HTML/Python review surface, so that result
  does not override the declared plan inputs.
- The authoritative setup-mode reviewability helper, targeted at `plan.md`,
  returned `status=block`, `pass=false`, `reviewable_loc=865`,
  `production_files=9`, and `total_files=11`, with no honored exception.
- Blockers: reviewable LOC exceeds 800 and production files exceed 8.
- **First G3 verdict: BLOCKED.** Per the recorded `Stop and split` answer, the
  run stopped before Checklist and Tasks and awaited a human-approved split.

Approved-split revalidation after the user's `approve three slices` decision:

| Slice | Durable gate input | Reviewable LOC | Production files | Total files | Result | Blockers |
|---|---|---:|---:|---:|---|---|
| 1 — Keyboard foundation | `contracts/reviewability-slice-1-keyboard-foundation.md` | 160 | 3 | 4 | `pass` | none |
| 2 — Read-only ports | `contracts/reviewability-slice-2-read-only-ports.md` | 590 | 4 | 7 | `warn` | none |
| 3 — Decision ports | `contracts/reviewability-slice-3-decision-ports.md` | 520 | 2 | 5 | `warn` | none |

- All three authoritative helper calls returned `pass=true`; no exception was
  requested or honored.
- The revised advisory estimator still returned `projected=0` because its
  classifier does not count the declared HTML/Python surface. The durable
  per-slice setup-mode results above remain the applicable evidence.
- Structure validation found `plan.md` with zero unresolved markers.
- **G3 gate: PASS.** The approved topology is non-blocking, so Checklist may
  start. Shared integration remains serialized in slice order.

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
| ux | 36 | 0 remaining (3 fixed) | `spec.md`, `plan.md`, `research.md`, `data-model.md`, `docs/ai/specs/.process/ART-004-manual-uat.md`, gallery contract |
| accessibility | 37 | 0 remaining (9 fixed) | keyboard/focus, Safari traversal, semantics/live status, reduced motion, non-color meaning, contrast, UAT evidence |
| error-handling | 38 | 0 remaining (4 fixed) | file:// refusal, stale fallback, font fallback, blocking drift categories |
| **Total** | **111** | **0 remaining (16 fixed)** | All three consensus steps skipped: executors reported zero unresolved items |

Resolve every Gap in spec.md or plan.md and rerun its checklist before G4.

- Authoritative `count-markers` result: `total=0`, `spec=0`, `plan=0`,
  `checklists=0`.
- **G4 gate: PASS.** All three domains completed with zero unresolved items.

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
- Keep ART-004 on one combined branch and delivery, but group implementation
  tasks into the three human-approved ordered review slices: keyboard
  foundation, read-only ports, then decision ports.
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
| Total Tasks | 60 (`T001`-`T060`) |
| Phases | 6 |
| Parallel Opportunities | 9 tasks across 3 disjoint HTML-only sets |
| User Stories Covered | 3/3; functional requirements 17/17; success criteria 9/9 |

- Task mix: 11 RED, 12 GREEN, 5 REFACTOR, and 32 VERIFY.
- **G5 gate: PASS.** The authoritative validator found 60 tasks and the
  marker scan found zero gaps, clarifications, or severity findings.
- Tasks-mode `reviewability-gate` is deferred by the installed runner. The
  fallback chain is non-blocking: G0 setup evidence, the three authoritative
  G3 slice results (`160/pass`, `590/warn`, `520/warn`), and the human-approved
  split all remain valid with no correctness blocker.

### Phase 7 Task Groups

| Group | Task IDs | Plan-stage disposition |
|---|---|---|
| Setup and foundational gates | `T001-T009` | Complete — clean baseline `7399/7399` |
| Slice 1 — keyboard foundation | `T010-T022` | Complete — checkpoint `e15e3a6cc` |
| Slice 2 — read-only ports | `T023-T037` | Complete — checkpoint `01e97ad65` |
| Slice 3 — decision ports | `T038-T052` | In progress |
| Polish and release evidence | `T053-T060` | Pending |

---

## Atomicity Route

Autopilot fills this after Tasks by running the read-only classifier against:

~~~text
runner helper atomicity-route specs/art-004-gallery-completion-design-prototyping
~~~

The scaffold interview originally selected one combined slice. G3 then blocked
that topology, and the user approved the durable three-slice recovery. The
classifier is evidence, not permission to collapse or replace those approved
slices.

| Field | Value | Meaning |
|---|---|---|
| **Route** | `one-navigable-PR` | Classifier route |
| **Releasable** | `true` | One delivery remains releasable |
| **Signals** | `change-shape:modify-heavy` | Decisive structural finding |
| **Warnings** | none | No release-safety warnings |

The classifier is advisory and does not collapse the three approved review
slices. No layer-plan helper is required for `one-navigable-PR`.

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
| A-001 | HIGH | `spec.md` still treated the combined reviewability block as pending | Reframed it as history and made the three approved slice gates current authority |
| A-002 | MEDIUM | Plan and the historical quickstart referenced a sibling-worktree runner | Replaced with the repository-local Python runner invocation; the relocated source is recoverable from merge history |
| A-003 | MEDIUM | T002 omitted the deferred tasks-mode reviewability fallback | Added G0, per-slice G3, and human-approval fallback evidence |

- Rerun result: zero CRITICAL, HIGH, MEDIUM, or LOW findings.
- `T001-T060`, 17/17 requirement traceability, and all nine `[P]` tasks remain
  intact.
- Analyze had zero unresolved findings; the required clean-pass synthesizer is
  still invoked to emit the canonical pre-implementation confidence block.
- **G6 gate: PASS.** The authoritative validator found zero CRITICAL/HIGH
  findings.

The host did not expose the installed `consensus-synthesizer` agent type, so a
read-only default subagent executed the exact clean-pass synthesis rubric and
canonical output contract as the closest callable semantic equivalent.

📊 Confidence: 1.00

- Task understanding: 1.00
- Approach clarity: 1.00
- Requirements alignment: 1.00
- Risk assessment: 1.00
- Completeness: 1.00

---

## Phase 6.5: Confidence Gate

| Field | Value |
|---|---|
| Mode | advisory |
| Composite confidence | 1.00 (threshold 0.90) |
| Verdict | G6.5 PASS — proceed |
| Evidence | Deterministic `confidence-gate` runner exit 0; all five confidence criteria scored 1.00 |

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
| 1 - Keyboard-scroll guard and repair | `T001-T022` | `T001-T022` | Chromium and Safari 26.6.1 file:// UAT passed 11/11 regions after correcting module-map grid sizing; Safari used Tab and Enter for the five source disclosures; suite `7418/7418`, release-artifact `--check`, and docs reference check pass after checkpoint `e15e3a6cc` |
| 2 - Read-only ports | `T023-T037` | `T023-T037` | Complete — checkpoint `01e97ad65`; four ports and exact manifest flips shipped, Chromium/Safari UAT passed, suite `7450/7450`, and release/reference consistency checks passed |
| 3 - Decision ports | `T038-T052` | `T038-T052` | Complete — checkpoint `0a8228a8c`; both decision ports, exact manifest flips, generated payloads, Chromium/WebKit/Safari UAT, suite `7496/7496`, and release/reference consistency checks passed |
| 4 - Shared integration and UAT | `T053-T060` | `T053-T060` | Complete — six status-only manifest flips, nine-target guard, fill inventory, full native-engine UAT matrix, review packet, ART-020 disposition, suite `7496/7496`, release/reference consistency, and exact PR title all pass |

---

## Final PR Review Evidence

### What changed and why

- Repaired keyboard reachability for 11 horizontal regions across
  `code-approaches`, `implementation-plan`, and `module-map`, with a global
  declaration, name, role, focus-order, and overflow-route guard.
- Ported the six remaining design/prototyping artifacts as self-contained
  offline HTML: four read-only ports and two live-state decision-export ports.
- Flipped exactly those six manifest rows to `shipped`, then regenerated Claude,
  Codex, installed-cache, proof, and release-readiness outputs from source.
- This completes ART-004 and discharges the ART-020 accessibility defect under
  the ownership decision recorded during planning.

### Non-goals

- No shared gallery runtime, framework, external asset dependency, persistence,
  network export, or new manifest vocabulary.
- No export-looking controls in read-only ports and no capabilities beyond the
  pinned upstream inventories and approved compaction boundaries.
- No unrelated roadmap, plugin-version, marketplace, or docs-site content work.

### Review order

1. Read the two source contracts in `test-artifact-gallery.py` and
   `test-artifact-fill-regions.py`.
2. Review the three repaired templates, then the four read-only ports, then the
   two decision ports.
3. Confirm the source manifest's six status-only changes.
4. Treat `dist/**`, installed-cache fixtures, and XPLAT proof records as
   generated mirrors; verify them with `refresh-release-artifacts.py --check`
   rather than reviewing copied HTML line by line.
5. Review this workflow, implementation notes, tasks, and final UAT evidence.

### Scope budget and traceability

- Human-approved Slice 1 gate: 160 reviewable LOC, 3 production files, `pass`.
- Human-approved Slice 2 gate: 590 reviewable LOC, 4 production files, `warn`.
- Human-approved Slice 3 gate: 520 reviewable LOC, 2 production files, `warn`.
- Realized post-review diff at checkpoint `d65345e65`: 90 files, including 10
  gallery source paths, 2 test files, generated payload/proof paths, and the
  Verify-Tasks report. Review checkpoints are
  `e15e3a6cc`, `01e97ad65`, and `0a8228a8c`; their bookkeeping checkpoints are
  `be5c90c25`, `caa920d1d`, and `c28eb805d`.
- Tasks T001-T060 trace to all 17 functional requirements, 9 success criteria,
  and the six-row Functional Fidelity Inventory; T053 separately proves the
  final manifest delta against `d67742f10`.

### Verification and known gaps

- Focused gallery: 573/573; fill regions: 70/70; post-merge complete suite: 7628/7628.
- Release payload and docs reference checks pass on the clean post-review
  checkpoint `d65345e65`.
- Both Python-authoritative title gates pass the exact prospective title
  `feat(art-004): complete design gallery artifacts`: release readiness reports
  `blocking=false`, and the PR workflow contract reports `status=passed`.
- Chromium and Safari passed the repaired-region and read-only matrices;
  Chromium, WebKit, and Safari passed the decision matrix. Safari 26.6.1 used
  Option-Tab and moved the component snippet from `scrollLeft=0` to 29.
- No functional gap remains. The installed Playwright MCP profile was already
  in use, so isolated Playwright preserved that session. Headless WebKit did
  not synthesize a generic scroller's browser-default ArrowRight action; real
  Safari supplied the native-engine result for that path.

### Rollback and feature flags

There is no feature flag or data migration: these are static gallery documents
selected by manifest status. Roll back the three feature checkpoints in reverse
order, then rerun `python3 scripts/refresh-release-artifacts.py` and the docs
reference generator. A narrower rollback may set an affected source manifest
row back to `planned`, remove its authored template, and regenerate all mirrors;
generated files must never be hand-reverted independently.

---

## Post-Implementation Checklist

| Canonical Item | Status | Evidence |
|---|---|---|
| Post: Doctor Extension Check | ✅ Complete | 4 checks passed; one unrelated warning remains for the incomplete `brand-001-racecraft-identity-system` planning directory |
| Post: Verify Implementation | ✅ Complete | Verify extension found no implementation defect |
| Post: Verify Tasks Phantom Check | ✅ Complete | 60/60 tasks verified with zero flagged verdicts; privacy-safe report preserved at `docs/ai/specs/.process/ART-004-verify-tasks-report.md` |
| Post: Code Review | ✅ Complete | Independent review findings were repaired with RED/GREEN contracts; final re-review found no blocking or minor issue |
| Post: Integration Suite | ✅ Complete | Post-merge 7628/7628 passed: L1 1468/1468, L4 5968/5968, L5 192/192; privacy 10/10 |
| Post: Reviewability Diff Gate | ✅ Complete | Current committed three-slice evidence remains non-blocking at 160/pass, 590/warn, and 520/warn; review remediation did not change the approved topology |
| Post: Self-Review | ✅ Complete | Mandatory four-question audit below records tests, nine acceptance scenarios, FR/task traceability, and tidiness; no gaps found |
| Post: UAT Runbook Generation | ⏭️ Skipped | `generate-uat-skeleton` is deferred, no committed feature-local skeleton exists, and no UAT validator is registered; `ART-004-manual-uat.md` remains the executable source-derived matrix |
| Post: Final Reviewability Backstop | ✅ Complete | Deferred helper was not invoked; proceeded on current committed slice evidence and clean reviewed checkpoint `d65345e65` |
| Post: PR Packet/Body Generation | ✅ Complete | `pr-packet-output` dry-run/apply emitted the current feature-local packet and body; read-only validation passed with `pr_blocked=false` and `writes_state=false`; clean-tree validation was persisted; both title gates pass |
| Post: PR Body Generation | ✅ Complete | Refined only the sanctioned What Changed and Why It Matters regions, including the required consumer-facing `release-note` fence; protected packet sections and fingerprint remain valid |
| Post: PR Creation | ✅ Complete | Draft PR [#450](https://github.com/racecraft-lab/racecraft-plugins-public/pull/450) opened from the packet-owned base, head, title, and body at head `c7237e9e8` |
| Post: Review Remediation | ✅ Complete | GitHub code quality reported one unused source declaration through two generated-payload threads; removed at source in `37fcc4d4f`, regenerated mirrors/proofs, passed focused and consistency checks, replied with evidence, and resolved both threads; no other live feedback remains, and CI passed at audited head `1861414c3` |
| Post: Retrospective | ✅ Complete | Privacy-safe report preserved at `docs/ai/specs/.process/ART-004-retrospective.md`: 60/60 tasks, 17/17 requirements, 9/9 success criteria, 100% spec adherence, and no proposed spec changes |

### Self-Review — 2026-08-18T21:08:19Z

1. **Tests executed?** `BUILD`, `TYPECHECK`, `LINT`, and
   `INTEGRATION_TEST` are explicitly `N/A` in `PROJECT_COMMANDS`; they were not
   inferred as passing. `UNIT_TEST` and `FULL_VERIFY` are the same configured
   command, `python3 tests/speckit-pro/run-all.py`, and its final run passed
   7628/7628 after integrating current `origin/main`. Focused gallery and fill suites passed 573/573 and 70/70;
   Chromium and WebKit passed 16/16 post-review browser checks; release payload,
   docs reference, privacy, and diff checks pass.
2. **Edge cases?** All nine acceptance scenarios have non-happy-path evidence.
   Repaired-region focus and scrolling are covered at
   `test-artifact-gallery.py:7447` and `ART-004-manual-uat.md:47`; new-region
   coverage is at `test-artifact-gallery.py:7479` and
   `ART-004-manual-uat.md:108`; the missing
   keyboard-route negative is at `test-artifact-gallery.py:7555`. Offline and
   missing-resource failures are covered at `test-artifact-gallery.py:8348`,
   `:8357`, and `:8561`; fidelity and fill replacement are covered by the
   Group M/O inventories and `test-artifact-fill-regions.py:931`; status-only
   manifest drift is rejected at `test-artifact-gallery.py:8314` and `:8527`.
   Both decision payloads and incomplete-input paths are covered by Group O at
   `test-artifact-gallery.py:8799` and its fixtures beginning at `:8860`;
   clipboard refusal, fallback parity, and stale settlement are exercised in
   `ART-004-manual-uat.md:168` and statically guarded by Group O. No
   `[edge-case-gap]` remains.
3. **Requirements matched?** The `tasks.md` traceability matrix maps FR-001
   through FR-017 and SC-001 through SC-009 to checked tasks. Verify-Tasks
   confirms T001-T060 are 60/60 verified with no weak, partial, skipped, or
   missing verdict. Slice checkpoints `e15e3a6cc`, `01e97ad65`, and
   `0a8228a8c`, final integration `37956a78e`, and review remediation
   `d65345e65` provide implementation evidence. There are zero orphan FRs,
   tasks, or acceptance scenarios.
4. **Follow-up and tidiness?** Scans of `spec.md`, `plan.md`, `tasks.md`, commit
   messages, and the changed source found no `[TODO]`, `[DEFERRED]`,
   `[OUT-OF-SCOPE]`, debug logging, breakpoints, commented-out implementations,
   or temporary fixtures. The deferred UAT-skeleton helper is explicitly
   dispositioned above, while the preserved manual UAT record carries the real
   evidence. No silent deferral or leftover scaffolding remains.

- [x] All tasks complete.
- [x] Layer 1 and Layer 4 pass.
- [x] Full Python-authoritative suite passes.
- [x] Generated artifact consistency passes.
- [x] Manual file:// UAT passes.
- [x] Exact PR title passes release readiness and the PR workflow contract.
- [x] ART-004 roadmap and MOC state agree.

---

## Lessons Learned

### What Worked Well

- The fail-closed pre-final audit kept completion honest until every canonical
  Post item was either complete or explicitly skipped.
- The explicit isolated-Playwright and native-Safari fallback preserved browser
  evidence when the installed browser profile was already in use.

### Challenges Encountered

- Codex-native retrospective command exposure was not caught during scaffold
  setup; future setup checks should verify that wiring before Post begins.
- Packet validation did not expose the unused source declaration that the live
  GitHub review found, so packet validation cannot replace a live review audit.

### Patterns to Reuse

- Run the live GitHub review-remediation audit immediately after packet and PR
  creation, even when packet validation is green.
- Cite authored source first and treat generated mirrors as verification output.

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

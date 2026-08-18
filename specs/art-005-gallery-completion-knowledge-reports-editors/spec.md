# Feature Specification: ART-005 - Gallery Completion - Knowledge, Reports & Editors

**Feature Branch**: `art-005-gallery-completion-knowledge-reports-editors`

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "Port seven planned knowledge, report, and editor gallery templates into complete standalone Racecraft artifacts, preserving the accepted one combined slice, resolving semantic export obligations from pinned upstream evidence, and delivering file:// UAT evidence."

## Clarifications

### Session 2026-08-17 - Source, Fidelity, and Fill Regions

- **Pinned identity:** Use
  `anthropics/html-effectiveness@58c305be97f47b26b678f2c07dec01d4242268ec`
  for all seven ports. The commit timestamp is `2026-05-15T16:09:53Z`; the
  evidence was retrieved from the official GitHub repository on `2026-08-17`.
- **Semantic classification:** `slide-deck`, `concept-explainer`,
  `status-report`, and `incident-report` are semantic readers and retain
  `exports: []`. Slide navigation and the concept explainer's transient
  add/remove/reset simulation do not produce a durable user-authored result
  meant to leave the SPA. `triage-board`, `feature-flags`, and `prompt-tuner`
  remain semantic producers with Markdown export.
- **Preservation boundary:** Preserve slide navigation, static report reading,
  the concept explainer's transient visualization controls, and the three
  editors' core editing controls. Intentionally add Racecraft branding,
  canonical embedded blocks, accessibility and fill-region conventions,
  deterministic Markdown exports for the three editors, memory-only state, and
  the contract fallback. Do not add download, import, persistence, URL, or
  server behavior.
- **Contract reconciliation:** No SPA-CONTRACT.md conflict remains after the
  classification above; the shared contract does not change.

| Upstream source | SHA-256 | Semantic role and preserved mechanism |
|---|---|---|
| `09-slide-deck.html` | `e191d49c28569e5f2ae09ed3bc4dc3f8ef25f90f1c842b1458f7b43ef5153291` | Reader; arrow-key/scroll slide navigation |
| `11-status-report.html` | `6468f720bab1d016657a9ed25c1049ec42f1810b230f486a5f3130427614bc7c` | Reader; static status-report reading |
| `12-incident-report.html` | `e787d6a64eca1ccd77fd9fa18849400356895ed2717ceb26dad2638fcc3261a9` | Reader; static incident timeline/report reading |
| `15-research-concept-explainer.html` | `5dd7d3a3866d123fdea1199a3e20d3a31d6305916013b4a2a4a83018765384b3` | Reader; transient consistent-hashing simulation |
| `18-editor-triage-board.html` | `a2a4ba2691c2532dbe67da5bbeb183bbdee5e9027c7006fba6dce18de7347988` | Producer; triage-board editing and Markdown feedback loop |
| `19-editor-feature-flags.html` | `8fd1aa16175614bea196672cd8f9b119b4ddb5b4768bf0bcb4bb05d6588787ab` | Producer; flag editing and Markdown feedback loop |
| `20-editor-prompt-tuner.html` | `b2e1e46643bb908cb01e73600f40a5506a175869a65ad446992f22eacd0b0877` | Producer; prompt editing and Markdown feedback loop |

The required fill-region floors are:

| Artifact | Required fill slots and minimum representative content |
|---|---|
| `slide-deck` | `deck-title`; `slides` list with at least 2 anchored items; `speaker-notes` |
| `concept-explainer` | `concept-title`; `principles`; `worked-example`; `simulation-scenarios` list with at least 2 anchored items |
| `status-report` | `summary`; `landed`, `in-flight`, `blocked`, and `next-actions` lists with at least 2 anchored items each |
| `incident-report` | `summary`; `timeline` list with at least 2 anchored items; `impact`; `root-cause`; `follow-ups` list with at least 2 anchored items |
| `triage-board` | `triage-items` list with at least 2 anchored items; `column-labels` |
| `feature-flags` | `flags` list with at least 2 anchored items; `environment-notes` |
| `prompt-tuner` | `prompt-variants` list with at least 2 anchored items; `evaluation-notes` |

### Session 2026-08-17 - Editor State and Export Contracts

- **Triage ordering:** Serialize columns in `now`, `next`, `later`, `cut`
  order, then tickets in their current visible order within each column. A
  complete export has this shape:

  ```markdown
  # Triage Board Export
  Artifact: triage-board
  Export kind: markdown

  ## Now
  Rationale: Blocking the current release or actively losing user data.
  - `T-101`
    - Title: Fix file:// copy fallback
    - Tag: bug
    - Estimate: S
    - Owner: Ana

  ## Next
  Rationale: High leverage and ready when Now clears.
  - _No tickets._

  ## Later
  Rationale: Valuable work that can wait for a future cycle.
  - `T-102`
    - Title: Unicode check - Zoë / 東京
    - Tag: qa
    - Estimate: M
    - Owner: -

  ## Cut
  Rationale: Close, deduplicate, or return to the requester.
  - `T-103`
    - Title: Remove duplicate export button
    - Tag: scope
    - Estimate: L
    - Owner: Sam
  ```

- **Feature-flag schema:** The Markdown wrapper contains exactly one fenced JSON
  block. Groups and flags stay in declared order. Object fields stay in the
  order shown; `requires` is a string or `null`, and `rollout` is a number or
  `null`, matching the pinned source model.

  ````markdown
  # Feature Flags Export
  Artifact: feature-flags
  Export kind: markdown

  ```json
  {
    "schemaVersion": "artifact-gallery.feature-flags.export.v1",
    "artifactId": "feature-flags",
    "groups": [
      {
        "id": "onboarding",
        "label": "Onboarding",
        "flags": [
          {
            "key": "onboarding.workspace_templates",
            "description": "Offer prebuilt workspace templates during signup.",
            "enabled": true,
            "requires": "onboarding.checklist_v2",
            "rollout": null
          }
        ]
      }
    ],
    "issues": []
  }
  ```
  ````

- **Prompt-tuner schema:** The Markdown wrapper contains exactly one fenced JSON
  block. Slots stay in the pinned order; samples stay in visible order; fields
  stay in slot order; preview text is the live derived value.

  ````markdown
  # Prompt Tuner Export
  Artifact: prompt-tuner
  Export kind: markdown

  ```json
  {
    "schemaVersion": "artifact-gallery.prompt-tuner.export.v1",
    "artifactId": "prompt-tuner",
    "template": "Reply to {{customer_name}} about {{ticket_subject}}.\nTone: {{tone}}",
    "slots": ["customer_name", "plan_tier", "ticket_subject", "ticket_body", "tone"],
    "samples": [
      {
        "id": "sample-1",
        "label": "SAMPLE 1",
        "planClass": "free",
        "fields": {
          "customer_name": "Priya",
          "plan_tier": "Free",
          "ticket_subject": "Missing board",
          "ticket_body": "I cannot find yesterday's board.",
          "tone": "warm and patient"
        },
        "preview": "Reply to Priya about Missing board.\nTone: warm and patient"
      },
      {
        "id": "sample-2",
        "label": "SAMPLE 2",
        "planClass": "team",
        "fields": {
          "customer_name": "Marcus",
          "plan_tier": "Team",
          "ticket_subject": "Sync dropped comments",
          "ticket_body": "Comments disappear between devices.",
          "tone": "direct and apologetic"
        },
        "preview": "Reply to Marcus about Sync dropped comments.\nTone: direct and apologetic"
      },
      {
        "id": "sample-3",
        "label": "SAMPLE 3",
        "planClass": "studio",
        "fields": {
          "customer_name": "Lena",
          "plan_tier": "Studio",
          "ticket_subject": "Billing entity",
          "ticket_body": "Use the new entity on the next invoice.",
          "tone": "brisk and friendly"
        },
        "preview": "Reply to Lena about Billing entity.\nTone: brisk and friendly"
      }
    ],
    "issues": []
  }
  ```
  ````

- **Edge representation:** Preserve empty text as `""`, empty collections as
  `[]`, and absent optional JSON fields as `null`. Preserve duplicate array
  entries in visible order and add a deterministic `issues[]` entry instead of
  deduplicating. Preserve the original raw value for invalid input, use `null`
  for any unavailable normalized value, and add an `issues[]` entry. Preserve
  multiline, Unicode, quotes, backticks, pipes, and other special characters;
  fenced JSON uses `JSON.stringify(value, null, 2)`, while triage field bodies
  use deterministic Markdown escaping and indented continuation lines.
- **Clipboard behavior:** Each editor has exactly one control labeled
  `Copy as Markdown`. On invocation, clear any stale fallback, generate the
  export once from live state, and attempt `navigator.clipboard.writeText()`
  once when available. Success announces `Copied. Markdown is on the
  clipboard.` Failure, rejection, unavailability, or synchronous throw
  announces `Copy failed. The Markdown export is available below for manual
  copy.`, reveals a labeled selectable textarea containing the exact attempted
  string, focuses it, and uses no hidden copy or download path.

### Session 2026-08-17 - Acceptance Evidence and Reviewability

- **Evidence locations:** During active work, keep the plain-English runbook at
  `.process/uat-runbook.md` inside this feature directory. Keep the human-readable
  result summary at `.process/uat-results.md` and the normalized per-check record
  at `.process/uat-results.json`. Post-merge archival preserves them as
  `docs/ai/specs/.process/ART-005-uat-runbook.md`,
  `docs/ai/specs/.process/ART-005-uat-results.md`, and
  `docs/ai/specs/.process/ART-005-uat-results.json`; a committed browser harness,
  if implementation proves one necessary, keeps its detailed JSON under an
  `ART-005-uat-harness/` directory beside those files.
- **Run metadata:** The normalized result record has top-level `featureId`,
  `sourceCommit`, `executedAt`, `environment`, `driver`, and `runbookPath` fields.
  `environment` identifies operating system, browser name/version, `file://`
  scheme, and the network, theme, reduced-motion, and color-mode conditions used.
  `driver` is `manual` or the repository-relative path of the exact harness.
- **Per-check evidence:** Every result row has `artifactId`, `templatePath`,
  `step`, `claim`, `observedResult`, `verdict`, `date`, and `driver`. `verdict` is
  `pass`, `fail`, or `not_applicable`; `not_applicable` still requires an
  observation proving why the check does not apply. The Markdown summary reports
  totals and identifies the exact source commit represented by the JSON rows.
- **Clipboard proof:** Each editor requires one genuine `file://` success in
  which a real clipboard read-back or paste exactly equals the live-state export,
  the success message is present, and the fallback is absent. Separate checks
  force an unavailable clipboard, rejected promise, and synchronous throw, and
  prove that all three reveal and focus the exact fallback text without reporting
  success. The unavailable probe uses
  `Object.defineProperty(navigator,'clipboard',{value:undefined,configurable:true});`;
  `delete navigator.clipboard` is prohibited because the inherited accessor makes
  that expression a no-op and can produce a false pass.
- **Seven-artifact matrix:** Every artifact receives result rows for direct
  `file://` open, complete representative content, offline reload, complete
  keyboard traversal, visible focus, light/dark theme parity, reduced-motion
  behavior, and color-independent meaning. A named keyboard-focusable horizontal
  scroll region is verified wherever one exists; its absence is recorded as
  `not_applicable` with the observed layout. The three editors additionally
  receive live-state serialization, genuine clipboard success, and all three
  forced-fallback checks.
- **Reviewability response:** If any final plan-time projection reaches a block
  threshold, stop with: `STOP: ART-005 combined-slice reviewability block. The
  operator selected one combined slice, and no ratified exception exists. Do not
  split automatically and do not continue to Checklist, Tasks, or Implementation.
  Record the measured projection and wait for an explicit operator topology
  decision.`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand Decks And Concepts (Priority: P1)

A reader opens the Slide Deck or Concept Explainer from the filesystem and can consume complete, representative content without needing a server, setup step, or external workflow.

**Why this priority**: These two entries are part of the planned catalog segment and must become useful standalone reading experiences before the gallery can be considered complete.

**Independent Test**: Open each artifact directly over `file://`, inspect the representative content, navigate any consumption controls, and confirm the experience is understandable without export controls unless the semantic producer/reader check proves otherwise.

**Acceptance Scenarios**:

1. **Given** the `slide-deck` catalog entry is planned and sourced from `09-slide-deck.html`, **When** a reader opens the shipped artifact over `file://`, **Then** the reader can step through a representative Racecraft-branded deck with accessible controls and no missing content.
2. **Given** the `concept-explainer` catalog entry is planned and sourced from `15-research-concept-explainer.html`, **When** a reader opens the shipped artifact over `file://`, **Then** the reader can understand the concept, worked example, and supporting content without any network-dependent behavior.

---

### User Story 2 - Inspect Status And Incident Reports (Priority: P2)

A reader opens a Status Report or Incident Report from the filesystem and can inspect a complete representative report, including status, impact, blockers, timeline, and follow-up information where appropriate.

**Why this priority**: The report entries complete the planned reporting segment and must clearly distinguish read-only reports from any upstream interaction that creates durable user-authored state.

**Independent Test**: Open each report artifact over `file://`, verify the report is complete and readable, and confirm any state-producing upstream behavior has been reconciled with the export contract before implementation proceeds.

**Acceptance Scenarios**:

1. **Given** the `status-report` catalog entry is planned and sourced from `11-status-report.html`, **When** a reader opens the shipped artifact over `file://`, **Then** the reader can inspect current work, in-flight work, blockers, ownership, and next milestones in a complete representative report.
2. **Given** the `incident-report` catalog entry is planned and sourced from `12-incident-report.html`, **When** a reader opens the shipped artifact over `file://`, **Then** the reader can inspect what broke, timeline, impact, response, remediation, and recurrence-prevention information in a complete representative report.

---

### User Story 3 - Export Editor Decisions As Markdown (Priority: P3)

An operator edits a Triage Board, Feature Flag configuration, or Prompt Tuner session, then copies deterministic Markdown derived from the current session state and can recover the same text manually when clipboard access fails.

**Why this priority**: The three editor entries are the only known ART-005 semantic producers and must close the required feedback loop without adding persistence, import-back, or new export kinds.

**Independent Test**: Change each editor's sample state, invoke `Copy as Markdown`, verify the copied or fallback text matches the live state, reload the page, and confirm editor working state resets while existing theme preference behavior is unchanged.

**Acceptance Scenarios**:

1. **Given** an operator has moved or edited items on the `triage-board`, **When** the operator chooses `Copy as Markdown`, **Then** the artifact produces deterministic human-readable Markdown grouped by board column from the current board state.
2. **Given** an operator has changed `feature-flags`, **When** the operator chooses `Copy as Markdown`, **Then** the artifact produces deterministic Markdown containing a fenced JSON block that losslessly represents the current flag state.
3. **Given** an operator has changed the `prompt-tuner`, **When** the operator chooses `Copy as Markdown`, **Then** the artifact produces deterministic Markdown containing a fenced JSON block that losslessly represents the current prompt session state.
4. **Given** clipboard access is unavailable, rejected, or throws synchronously, **When** an operator chooses `Copy as Markdown`, **Then** the artifact announces the failure as text, reveals a labeled manual-copy field containing the exact export text, and moves focus to that field.

---

### Edge Cases

- Clipboard APIs can be unavailable, rejected by the browser, or throw synchronously when opened over `file://`; the operator must still receive the exact export text.
- Reloading an editor after changes must reset editor working state to representative sample content while leaving existing theme preference behavior unchanged.
- The four currently export-free entries may prove to be semantic producers after pinned upstream inspection; implementation must stop and reconcile the contract rather than guessing from the current manifest.
- Partial delivery is invalid: an artifact file without the matching catalog status change, or a catalog status change without the artifact file, does not satisfy the feature.
- Keyboard-only users must be able to reach newly introduced horizontal scroll regions and operate all controls without losing visible focus.
- Reduced-motion users must not be required to tolerate animation, transitions, or smooth scrolling in the new artifacts.
- Color, position, and visual treatment may support meaning but must not be the only way a reader identifies status, priority, or error state.
- Missing upstream source evidence, digest evidence, or plan-time reviewability measurement blocks implementation planning from proceeding silently.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST port exactly these seven existing catalog entries: `slide-deck`, `concept-explainer`, `status-report`, `incident-report`, `triage-board`, `feature-flags`, and `prompt-tuner`.
- **FR-002**: The feature MUST use the immutable upstream commit and seven SHA-256 source identities recorded in Clarifications as the baseline for all seven ports.
- **FR-003**: Each artifact MUST preserve the core upstream content or interaction model while applying Racecraft branding, canonical embedded gallery blocks, the single-file contract, accessibility obligations, and gallery fill-region conventions.
- **FR-004**: Each shipped artifact MUST be delivered atomically with its own catalog entry status changed from `planned` to `shipped`; no other catalog value may change unless required by the resolved export classification.
- **FR-005**: `slide-deck`, `concept-explainer`, `status-report`, and `incident-report` MUST remain semantic readers with `exports: []`; their pinned navigation, static reading, and transient simulation controls do not produce durable user-authored output meant to leave the SPA.
- **FR-006**: Any artifact confirmed as a semantic reader MUST carry no export control and MUST retain an empty export declaration.
- **FR-007**: The three known editor artifacts, `triage-board`, `feature-flags`, and `prompt-tuner`, MUST retain `markdown` as their only export kind and MUST label the export control exactly `Copy as Markdown`.
- **FR-008**: `feature-flags` and `prompt-tuner` exports MUST be deterministic Markdown documents containing lossless structured session state in one fenced JSON block with the exact versioned schemas, field order, collection order, and edge-value rules recorded in Clarifications.
- **FR-009**: `triage-board` exports MUST use the exact human-readable, column-grouped Markdown shape, declared column order, current ticket order, empty-column representation, and escaping rules recorded in Clarifications.
- **FR-010**: Every export MUST be generated from the artifact's live state at the moment the operator invokes it.
- **FR-011**: Each editor MUST implement the one-attempt clipboard success and visible focused fallback behavior recorded in Clarifications; hidden `execCommand` copying and automatic download are prohibited.
- **FR-012**: Editor working state MUST be memory-only and reset on reload; existing gallery theme preference behavior MUST remain unaffected.
- **FR-013**: Every new artifact MUST open directly over `file://`, remain readable with no server or install step, and avoid missing content when the network is unavailable.
- **FR-014**: New horizontal scroll regions MUST be keyboard-focusable and named; all controls MUST have visible focus and accessible names; status MUST be announced as text; reduced motion MUST be respected; color MUST never be the sole carrier of meaning.
- **FR-015**: The feature MUST preserve the tracked plain-English `file://` UAT runbook, Markdown result summary, and normalized per-check JSON record at the active-feature and archival paths, with the mandatory metadata, row fields, verdicts, and seven-artifact coverage recorded in Clarifications.
- **FR-016**: Planning MUST include a file-by-file measurement of the pinned upstream sources and declared operations before implementation starts.
- **FR-017**: If the final projection crosses a reviewability block threshold and no ratified exception exists, planning MUST stop for an operator topology decision instead of splitting automatically or inventing an exception.
- **FR-018**: The feature MUST stay within the selected single combined slice unless an explicit later operator decision changes that topology.
- **FR-019**: The feature MUST NOT add workflow-stage routing, JSON export kinds, automatic downloads, import-back, persistent editor content, shareable URL state, server storage, shared gallery foundation changes, or repairs to already-shipped templates.
- **FR-020**: Each artifact MUST implement the exact fill-slot inventory and minimum anchored sample-content floors recorded in Clarifications; list slots MAY exceed their floor only when the template markers and Layer 4 inventory remain in agreement.

### Reviewability Notes *(if applicable)*

- No ratified reviewability exception exists for this feature.
- The operator selected one combined slice after being shown that both estimates warned and suggested two slices.
- Generated templates, generated zones, process files, PR bodies, and code fences are not valid provenance for a typed reviewability exception.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process (shipped gallery artifacts)
- **Secondary surfaces, if any**: N/A
- **Preset thresholds**: Warn above 400 reviewable LOC, above 6 production files, above 15 total files, or above 1 primary surface. Block above 800 reviewable LOC, above 8 production files, above 25 total files, or above 1 primary surface without a ratified exception.
- **Projected reviewable LOC**: Roadmap estimate 560 LOC; scaffold estimate 555 LOC. Both estimates warn and suggest two slices because they exceed the 400 reviewable LOC warning threshold and remain below the 800 reviewable LOC block threshold.
- **Projected production files**: 7 net-new artifact files, which exceeds the preset warning threshold of 6 production files and remains below the block threshold of 8 production files.
- **Projected total files**: Approximately 9 authored files before generated mirrors, below the total-file warning threshold of 15.
- **Budget result**: Warning accepted by operator for one combined slice; no block is established from current estimates.
- **Split decision**: The feature remains one combined ART-005 spec because the operator selected that topology. Planning must measure pinned source files and declared operations file by file; if the final projection crosses any block threshold, the workflow must stop for an operator topology decision rather than split automatically or invent an exception.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Gallery Artifact**: A standalone catalog template a reader opens from the filesystem; key attributes are identifier, title, category, representative content, interaction model, status, and export affordances.
- **Manifest Entry**: The catalog row that routes and describes an artifact; key attributes are stable id, category, title, guidance, stage, trigger, source, status, and exports.
- **Upstream Source Baseline**: The immutable upstream repository commit and seven source files used as derivative inputs; key attributes are commit identity, file path, retrieval date, and per-file digest or equivalent evidence.
- **Editor Session State**: The in-memory working data for a triage board, feature-flag configuration, or prompt tuning session; key attributes are visible values, ordering, current selections, and reset behavior.
- **Markdown Export**: The deterministic record produced from live editor state; key attributes are artifact name, generated content, stable ordering, and fenced JSON when structured state is required.
- **Manual Copy Recovery**: The fallback path used when clipboard copy fails; key attributes are visible status, labeled selectable field, exact export text, and focus movement.
- **UAT Evidence Record**: The durable acceptance record for `file://` checks; top-level attributes bind the feature, tested commit, execution time, environment, driver, and runbook, while each row binds an artifact and template path to a step, claim, observed result, verdict, date, and driver.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All seven ART-005 catalog entries can be opened directly over `file://` and present complete representative content with no missing artifact content.
- **SC-002**: The manifest and artifact files agree for 100% of the seven entries: each shipped entry has its artifact, and no ART-005 artifact remains planned.
- **SC-003**: For all three known editors, changing visible state before `Copy as Markdown` changes the exported Markdown deterministically to match the current session state.
- **SC-004**: For all three known editors, forced clipboard unavailability, rejection, and synchronous failure each expose a labeled manual-copy field containing the same text the clipboard path would have produced.
- **SC-005**: Keyboard-only UAT covers all seven artifacts and verifies reachable named scroll regions where present, visible focus on controls, and no color-only status or priority meaning.
- **SC-006**: Reduced-motion UAT verifies that all seven artifacts remain usable without required animation, transition, or smooth-scroll behavior.
- **SC-007**: The tracked UAT result record contains a `pass`, `fail`, or evidence-backed `not_applicable` row for every required check across all seven artifacts, including genuine clipboard success and unavailable, rejected, and synchronous-failure fallback paths for each editor.
- **SC-008**: The plan-time reviewability record includes both warned estimates, a file-by-file pinned-source measurement, declared operations, and either a non-blocking projection or an explicit operator topology decision.

## Assumptions

- The target reader or operator opens gallery artifacts from a local filesystem and does not rely on a local server.
- Representative sample content is acceptable for all seven artifacts as long as it preserves the upstream content or interaction model and is complete enough for UAT.
- The immutable upstream commit and file digests are resolved during planning rather than guessed in the specification.
- The existing gallery theme preference behavior remains owned by the shared canonical block and is not redesigned by ART-005.
- Functional fidelity means preserving the recognizable content model and interaction purpose of each upstream file, not pixel-perfect upstream styling.
- Generated payload copies and installed-cache proofs are handled by authoritative repository tooling after source changes; this specification does not authorize hand-editing generated mirrors.

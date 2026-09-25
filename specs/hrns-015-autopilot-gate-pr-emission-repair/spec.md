# Feature Specification: Autopilot, Gate, and PR-Emission Repair

**Feature Branch**: `hrns-015-autopilot-gate-pr-emission-repair`  
**Created**: 2026-09-25  
**Status**: Draft  
**Input**: Repair observed SpecKit Pro autopilot and scaffold defects on Claude Code and Codex in four review slices, each with failing-first fixtures. The complete request is the Phase 1 Detailed Prompt in [HRNS-015-workflow.md](../../docs/ai/specs/.process/HRNS-015-workflow.md).

**Decision source**: [HRNS-015 design concept](../../docs/ai/specs/.process/HRNS-015-design-concept.md), [harness engineering roadmap, HRNS-015 and HRNS-019](../../docs/ai/specs/harness-engineering-uplift-technical-roadmap.md), and [harness engineering PRD §3.16](../../docs/prd-harness-engineering-uplift.md). The design concept's Q1–Q11 decisions govern this specification.

## User Scenarios & Testing *(mandatory)*

The four review slices ship in order A, B, C1, C2. Each story is independently demonstrable on both supported hosts where the behavior is host-facing. Each slice has a failing-first fixture for its acceptance behavior.

### Slice A — PR emission

#### User Story 1 - Release note in the final packet (Priority: P1) [US1]

As an operator, I can supply a release note while preparing a final pull request, and the emitted body passes the host repository's release-note policy without manual body repair.

**Why this priority**: The observed final PR failed the release-note check, and HRNS-016 depends on the packet repair.

**Independent Test**: Build a final packet with a release note and a feature PR title; validate its emitted body against the host policy.

**Acceptance Scenarios**:

1. **Given** a final packet with a release note, **when** its body is emitted, **then** one `## Release note` section follows the eight required headings, contains exactly one nonempty `release-note` fence inside its own editable markers, and leaves the single UAT Runbook heading in its required position.
2. **Given** that emitted body and a `feat` PR title, **when** the host release-note check runs, **then** it passes without a skip label or manual body edit.
3. **Given** a draft PR or a packet without a release note, **when** its body is emitted, **then** no release-note heading, marker field, or fence is invented; drafts retain zero editable fields.

#### User Story 2 - Packet validation in hosts that track untracked files (Priority: P1) [US2]

As an operator, I can validate or refresh a packet when its own generated files are untracked, while unrelated worktree changes still block the operation.

**Why this priority**: A host without packet ignore rules currently blocks on the packet's own files.

**Independent Test**: Run validation and refresh in a host without packet ignore rules, first with only packet files and then with an unrelated file.

**Acceptance Scenarios**:

1. **Given** only this packet's canonical untracked `<id>.json`, `<id>/body.md`, and `<id>/validation.json` files under its validated feature directory, **when** validation or refresh applies, **then** it succeeds without requiring those files to be committed.
2. **Given** another packet, any unrelated changed path, a tracked modification, or unreadable Git status, **when** validation or refresh applies, **then** it blocks without a host ignore-rule workaround.

#### User Story 3 - Confidence visible to reviewers (Priority: P1) [US3]

As a reviewer, I can see the recorded G6.5 confidence verdict in the final PR body.

**Why this priority**: HRNS-025 remains pending, so this repair must carry the verdict into the review artifact.

**Independent Test**: Record a G6.5 verdict and inspect the final emitted body.

**Acceptance Scenarios**:

1. **Given** a recorded G6.5 verdict, **when** the final body is emitted, **then** the verdict is visible and matches the recorded value.
2. **Given** a refreshed final packet, **when** its body is emitted again, **then** a protected line under `## Verification` shows the current Phase 6.5 `Verdict` value rather than stale body text.
3. **Given** no valid recorded Phase 6.5 verdict, **when** final PR emission is attempted, **then** emission blocks instead of inferring a verdict from the overview status or score.

### Slice B — gates and counters

#### User Story 4 - Accurate checklist gap count (Priority: P1) [US4]

As an operator, I receive a G4 count for actual checklist gap tags, regardless of where `Gap` appears among a tag's comma-separated tokens.

**Why this priority**: Live runs reported zero while checklists contained gap tags.

**Independent Test**: Count a checklist containing each supported tag form, two qualifying tags on one line, and quoted examples through G4 and `count-markers gaps/all`.

**Acceptance Scenarios**:

1. **Given** tags with `Gap` as the first or later comma-separated token, including two qualifying tags on one line, **when** G4 and `count-markers gaps/all` count gaps, **then** each real tag counts once and all entry points agree.
2. **Given** Gap tags or clarification markers in inline, fenced, or indented Markdown code, **when** G1, G2, G3, G4, or `count-markers` counts or lists them, **then** code examples are excluded while markers in visible prose are counted.
3. **Given** the operator's gate instructions, **when** they describe counting, **then** they no longer prescribe the literal-only count that misses compound tags.

#### User Story 5 - Spec index freshness in the required artifact check (Priority: P1) [US5]

As a contributor, I see stale spec-index backlinks and home entries fail the required artifact consistency check, and regeneration repairs the drift.

**Why this priority**: The required check currently passes with a stale index.

**Independent Test**: Start from a tracked stale index, run the check, regenerate, and run it again while an untracked file exists.

**Acceptance Scenarios**:

1. **Given** a stale tracked spec index, **when** artifact consistency is checked, **then** `--check` exits nonzero and names the changed index paths.
2. **Given** that stale index, **when** release artifacts are regenerated, **then** the index is refreshed and the check passes.
3. **Given** a candidate absent from the source Git index, including a file inside a tracked spec directory, **when** the index is generated or checked in an isolated copy, **then** neither backlinks nor the roadmap home index include it; staged additions remain eligible.

#### User Story 6 - Reviewability budget for the named spec (Priority: P1) [US6]

As an operator, I can evaluate the named roadmap entry's reviewability budget without another entry's numbers affecting the result.

**Why this priority**: The observed gate read the last roadmap entry instead of HRNS-015.

**Independent Test**: Evaluate two roadmap entries with different budgets and exercise missing fields, typed exceptions, and declared slices.

**Acceptance Scenarios**:

1. **Given** a named spec, **when** setup mode evaluates reviewability, **then** it considers only that spec's section and primary surfaces.
2. **Given** a missing named section or required budget field, **when** setup mode evaluates it, **then** it returns `status: block`, `pass: false`, exit 1, and a blocker naming the spec ID and missing field rather than borrowing another entry's value.
3. **Given** a valid line-anchored typed exception in the selected authored roadmap section, **when** the gate evaluates it, **then** its status is `exception` with the exact accepted class; a pragma in another entry or generated text has no effect.
4. **Given** an over-block-line total, **when** the ordered slice list and budget table have exactly one complete, numeric row per slice and every slice is below each block line, **then** setup reports the aggregate and accepts the split; missing, extra, duplicate, malformed, or over-line rows block.
5. **Given** a greenfield entry, **when** setup evaluates its budget, **then** the documented 1.5x allowance changes LOC thresholds only; production-file, total-file, and surface thresholds retain their ordinary limits.
6. **Given** declared slice budgets, **when** setup evaluates them, **then** it aggregates their LOC and file counts for whole-feature reporting and evaluates each slice against the block lines.

#### User Story 7 - Refactor-aware size estimate (Priority: P2) [US7]

As an operator, I can include required refactor work in the early size estimate so slice planning reflects the expected review burden.

**Why this priority**: The original estimate missed substantial repair work and understated this feature's size.

**Independent Test**: Compare estimates for the same scope with and without a required-refactor signal.

**Acceptance Scenarios**:

1. **Given** required refactor work, **when** size is estimated, **then** the estimate and suggested slice count account for that work.
2. **Given** no required refactor work, **when** size is estimated, **then** the ordinary estimate remains available.

#### User Story 8 - Host-declared quality commands (Priority: P1) [US8]

As an operator, I can declare the host's quality-gate commands, and those commands take precedence over detected defaults.

**Why this priority**: Detection proposed commands that contradicted this repository's documented verification scope.

**Independent Test**: Declare a command for one slot, leave another slot undeclared, and inspect effective commands and their provenance.

**Acceptance Scenarios**:

1. **Given** a valid declared slot, **when** commands are detected, **then** that slot uses the declared command and reports `source: declared`.
2. **Given** an undeclared slot, **when** commands are detected, **then** normal detection remains available for that slot.

### Slice C1 — autopilot Post list and team teardown

#### User Story 9 - One complete Post list on both hosts (Priority: P1) [US9]

As an operator on Claude Code or Codex, I see the same 13 Post steps, including Final Reviewability Backstop and PR Packet/Body Generation.

**Why this priority**: Host lists and their prose counts disagree, weakening resume and completion checks.

**Independent Test**: Compare both host lists and their stated counts to the canonical 13-row list.

**Acceptance Scenarios**:

1. **Given** either host, **when** autopilot presents the Post list, **then** all 13 canonical rows appear once with matching names and counts.
2. **Given** a resumed run, **when** its Post state is reconstructed, **then** the two named resume points retain separate rows.

#### User Story 10 - No premature completion or orphaned team (Priority: P1) [US10]

As an operator, I receive completion only after every Post row is done and every executor-created team has been torn down.

**Why this priority**: Live runs returned with pending Post rows and active teammates.

**Independent Test**: Leave a Post row pending, in progress, or absent; separately form a team and check executor exit behavior on each host.

**Acceptance Scenarios**:

1. **Given** a pending, in-progress, missing, or duplicate canonical Post row in the persisted workflow or state, **when** either host reaches its completion boundary, **then** the shared check fails and identifies every affected row.
2. **Given** every Post row complete, **when** autopilot reaches the boundary, **then** it may report completion.
3. **Given** a team formed by any team-capable executor, **when** that executor reports clean completion, **then** it has collected or stopped every child and confirmed team teardown on both hosts; an unconfirmed child is named in its result.

### Slice C2 — resolve-pr, scaffold, envelopes, and templates

#### User Story 11 - Review-thread resolution after a verified push (Priority: P1) [US11]

As a PR author, I can rely on resolve-pr to consider all review threads and comments and to respond only after the fix is verified on the pushed branch.

**Why this priority**: Current flows can miss later pages and resolve before the fix reaches the remote branch.

**Independent Test**: Provide more than one page of threads and comments; verify event ordering with a failed verification, failed push, and successful confirmed push.

**Acceptance Scenarios**:

1. **Given** multiple pages of threads or nested comments, **when** resolve-pr collects feedback, **then** every connection is exhausted before decisions are made; a failed page or missing continuation cursor blocks replies and resolution.
2. **Given** an unverified fix, failed push, or remote head that does not match the pushed commit, **when** resolve-pr reaches reply handling, **then** it does not reply or resolve.
3. **Given** full verification, a successful push, and a fresh remote PR head SHA matching the intended commit, **when** resolve-pr handles feedback, **then** it replies and resolves serially and confirms each resolved state.

#### User Story 12 - Wait for the scaffold blind-spot analysis (Priority: P1) [US12]

As an operator, I receive the analyst's findings even when its work takes longer than five minutes, or a precise reason why the interview proceeded without them.

**Why this priority**: This feature's analyst returned 11 findings after 18.1 minutes, yet the run recorded the pass as not run.

**Independent Test**: Deliver a late nonempty summary, a dispatch error, an empty return, and an operator abandonment.

**Acceptance Scenarios**:

1. **Given** a dispatched analyst that is still working, **when** five minutes elapse, **then** scaffold continues waiting and later uses its nonempty findings.
2. **Given** a dispatch error, empty return, or explicit operator abandonment, **when** scaffold continues without findings, **then** the Design Concept blind-spot line and operator status show the same specific reason; elapsed time alone never records abandonment.

#### User Story 13 - Complete examples at live helper failure sites (Priority: P2) [US13]

As an operator on either host, I can copy a complete request envelope at each named helper invocation that failed in live use.

**Why this priority**: Bare helper names caused malformed calls; a bounded set of failure sites can be repaired now while the broader sweep remains HRNS-019.

**Independent Test**: Check and execute the examples for status index checking and topology, scaffold reviewability and worktree placement, and phase index writing on both hosts.

**Acceptance Scenarios**:

1. **Given** the named failure sites, **when** an operator follows each example, **then** it supplies the complete request envelope accepted by that helper.
2. **Given** Claude Code and Codex versions of those instructions, **when** examples are compared, **then** equivalent calls are present on both hosts.

#### User Story 14 - Workflow links point to scaffold output (Priority: P2) [US14]

As an operator following a generated roadmap, I can open its workflow links at the location where scaffold writes the files.

**Why this priority**: The template currently links a different path, making generated roadmaps appear broken.

**Independent Test**: Generate a roadmap and follow its workflow links to scaffold-created files.

**Acceptance Scenarios**:

1. **Given** a generated roadmap, **when** its workflow link is followed, **then** it opens the matching file under `docs/ai/specs/.process/`.
2. **Given** the published guidance, **when** it shows the workflow location, **then** it agrees with the generated link and scaffold output.
3. **Given** an existing roadmap with a legacy workflow link, **when** scaffold updates it, **then** a link to a verified existing workflow file is preserved; a broken link is corrected to the actual `.process/<SPEC-ID>-workflow.md` output.

### Edge Cases

- A release note with fence-like text must still yield one valid release-note fence in the final packet; draft output must remain free of that fence.
- Packet exemptions are limited to the packet being validated or refreshed; a second packet's untracked files and any unrelated modification still block.
- Gap-tag matching uses an exact, case-sensitive comma-delimited `Gap` token in a single-line, non-nested bracket tag, not a substring in a larger word. Spaces and tabs around tokens are ignored.
- Gap tags and clarification markers in inline, fenced, or indented Markdown code do not count or appear in marker details; the same text in visible prose does.
- An untracked file that resembles a spec entry cannot become an index backlink or home entry.
- A missing named roadmap section, missing budget field, or undeclared/over-budget slice fails closed; a typed exception is recorded as an exception rather than silently passing.
- Completion is refused for missing rows as well as rows with pending or in-progress state.
- A remote head mismatch after push keeps review replies and resolutions pending.
- A slow, nonempty blind-spot result remains usable; only dispatch error, empty return, or operator abandonment permits proceeding without it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** [US1]: Final packet creation MUST accept an optional release note without requiring a replacement of the full body.
- **FR-002** [US1]: When supplied, the final body MUST render exactly one `## Release note` section after the eight required headings, with its heading and balanced marker lines protected and exactly one nonempty `release-note` fence in its editable body, and pass the host's release-note check for a feature PR title.
- **FR-003** [US1]: Draft bodies and final bodies without a supplied release note MUST NOT acquire a release-note heading, editable field, or fence by default; drafts retain zero editable fields.
- **FR-004** [US2]: `validate-pr-packet-write` and `pr-packet-output` MUST exempt only the current packet's three canonical untracked metadata, body, and validation paths, derived from the validated feature directory and packet ID, from the clean-worktree guard.
- **FR-005** [US2]: The same guard MUST continue to block every unrelated tracked or untracked change, every tracked modification to packet files, and unreadable Git status; both host instructions MUST allow only the current packet's untracked canonical paths without requiring a force-add or ignore rule.
- **FR-006** [US3]: Final PR emission MUST require a valid Phase 6.5 `Verdict` field and show its current value in a protected generated line under `## Verification`, including on refresh; it MUST NOT substitute the Workflow Overview status or infer a missing verdict.
- **FR-007** [US4]: G4 and `count-markers gaps/all` MUST count each real bracket tag with a comma-separated `Gap` token once, including first and later token positions and multiple tags on one line.
- **FR-008** [US4]: G4 gap counting and G1/G2/G3 and `count-markers clarifications/all` clarification counts and details MUST exclude markers in inline, fenced, and indented Markdown code, while preserving counts in visible prose and leaving other marker types unchanged. Operator instructions MUST describe the same rule.
- **FR-009** [US5]: Spec-index generation and isolated checking MUST exclude every candidate absent from the source Git index, including files inside tracked spec directories, from backlinks and the roadmap home index; staged additions remain eligible.
- **FR-010** [US5]: Release-artifact regeneration MUST refresh the spec index; its required `--check` MUST fail on stale tracked index content and name changed index paths.
- **FR-011** [US6]: Setup reviewability evaluation MUST require a spec identifier, match the complete case-sensitive `### <spec_id>:` roadmap entry heading, and consider only that entry through the next peer-level heading and its primary surfaces.
- **FR-012** [US6]: Setup reviewability evaluation MUST return `status: block`, `pass: false`, exit 1, and a blocker naming the spec ID and missing field when the named section or any required budget field is missing.
- **FR-013** [US6]: A valid line-anchored `Reviewability-Exception` with an accepted class in the selected authored roadmap section MUST produce status `exception` with that exact class; other sections, generated text, and new exception classes MUST NOT supply an override.
- **FR-014** [US6]: An over-block-line spec total MUST be acceptable only when the declared ordered slice IDs match unique complete numeric budget rows exactly and every slice is below each block line; the gate MUST report the aggregate of those rows, and missing, extra, duplicate, malformed, or over-line slice budgets MUST block.
- **FR-015** [US7]: Size estimation MUST accept a required-refactor signal and account for it in estimated scope and suggested slice count.
- **FR-016** [US8]: An optional per-slot declared quality command MUST override detection for that slot and identify its source as `declared`; other slots retain normal detection.
- **FR-017** [US9]: Both hosts MUST use one canonical 13-row Post list with separate Final Reviewability Backstop and PR Packet/Body Generation rows; all stated counts MUST agree.
- **FR-018** [US10]: Before Claude or Codex reports successful autopilot completion, it MUST run a completion-boundary check against the persisted workflow and `autopilot-state.json`. The check MUST require each of the 13 canonical Post steps to appear exactly once with status `completed`, name every missing or noncompleted step, and fail when any requirement is unmet.
- **FR-019** [US10]: On both Claude and Codex hosts, each team-capable executor MUST collect the result of every child agent or use a supported stop operation for an unfinished child, request graceful team shutdown, and confirm that no teammate remains active and cleanup has completed before reporting clean completion. Its structured result MUST identify any child result or teardown confirmation that remains unresolved. Codex child lifetime after parent exit remains unverified and is tracked by HRNS-017.
- **FR-020** [US11]: On each host, resolve-pr MUST collect every page of review threads and every page of comments within each thread. A failed request, incomplete connection, or missing continuation cursor MUST block replies and resolution. The implementation MAY reuse the repository’s existing nested pagination pattern; the exact GitHub API route remains a Plan decision.
- **FR-021** [US11]: On each host, resolve-pr MUST apply fixes, verify them, commit, and push before replying to or resolving review threads. It MUST compare the intended local commit SHA with a freshly retrieved remote PR head SHA and block replies and resolution on mismatch. It MUST reply to and resolve threads serially and confirm each thread’s resolved state.
- **FR-022** [US12]: Scaffold MUST wait for a dispatched blind-spot analyst's summary without a fixed five-minute deadline.
- **FR-023** [US12]: Scaffold MAY proceed without findings only for a dispatch error, empty return, or operator abandonment. It MUST record the outcome and specific reason in the Design Concept’s existing `**Blind-spot pass:**` line and show the same reason in its operator status line. A late nonempty result MUST be recorded as `ran` regardless of elapsed time. `operator abandonment` MUST require explicit operator action; elapsed time alone MUST NOT establish abandonment.
- **FR-024** [US13]: Both hosts MUST provide complete, tested request envelopes for status `generate-spec-index-check` and `o5-topology`, scaffold reviewability and worktree placement, and phase index writing; the broader call-site sweep remains HRNS-019.
- **FR-025** [US14]: New roadmap template workflow links and published path guidance MUST resolve to scaffold output under `docs/ai/specs/.process/`; updates to existing roadmaps MUST preserve verified legacy links that resolve to real workflow files and repair broken links to the actual output.
- **FR-026** [US1–US14]: Every changed host-facing behavior MUST have equivalent Claude Code and Codex instructions in the same review slice and failing-first fixture evidence for its acceptance scenarios.
- **FR-027** [US1–US14]: The PRD acceptance criteria AC-16.2, AC-16.5, AC-16.8, and AC-16.10, plus the HRNS-015 and HRNS-019 roadmap entries, MUST reflect the decided scope, four-slice budget, and ownership of deferred work.
- **FR-028** [US6]: The documented 1.5x greenfield allowance MUST apply only to reviewable-LOC thresholds; production-file, total-file, and primary-surface limits MUST retain their ordinary thresholds.
- **FR-029** [US6]: Setup MUST aggregate every declared slice budget for whole-feature reporting and evaluate each complete slice against the block thresholds, without borrowing another roadmap entry's values.

### Reviewability Notes

- Typed reviewability exceptions remain rare, operator-owned overrides. Accepted classes remain `refactor`, `infra`, and `upgrade`; no fourth class is introduced. Generated templates, generated zones, `.process` files, PR bodies, and code fences are not valid provenance.
- Each review slice is one reviewable PR, with both hosts represented for each behavior change. Slice A precedes B, C1, and C2 because HRNS-016 depends on its packet repair.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter.
- **Secondary surfaces**: schema/config and docs/process.
- **Projected reviewable LOC**: approximately 1,442 across all four slices using the design concept's slice estimates: A 282; B 410; C1 335; C2 415. Re-estimate during Plan, including required refactors.
- **Projected production files**: at most 4 in each slice; shared files may recur across slices, so an across-slice unique count is not asserted here.
- **Projected total files**: A about 10, B about 14, C1 about 14, C2 about 16; each slice must remain below 25.
- **Budget result**: split required for the whole feature; each of the four slices is planned below the per-slice block line.
- **Split decision**: A (PR emission), B (gates and counters), C1 (Post list and team teardown), C2 (resolve-pr, scaffold, envelopes, and template links). If a slice exceeds 4 production files or reaches 25 total files, split or rescope before implementation.

### PR Review Packet Requirements *(mandatory)*

- Each slice PR description MUST include what changed, why, non-goals, review order, scope budget, requirement traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and failing-first verification evidence.
- Deferred work MUST name HRNS-019 or another explicit follow-up. The packet repair and its release note MUST be represented in the final validated PR body.
- Review order is A, B, C1, C2. Final PR titles and bodies must pass the host repository's title and release-note policy.

### Key Entities

- **PR packet**: The final review artifact with body, canonical packet files, optional release note, and recorded G6.5 verdict.
- **Gap tag**: A real bracket tag outside code whose comma-separated tokens include `Gap`.
- **Spec index**: Tracked backlinks and roadmap home entries derived only from tracked, nonignored spec content.
- **Reviewability entry and slice budget**: One named roadmap section with required budget fields, primary surfaces, optional typed exception, and complete per-slice budgets.
- **Post row**: One of 13 canonical completion states shared across hosts.
- **Review feedback**: Paginated threads and comments whose reply and resolution state follows a verified push.
- **Blind-spot result**: A nonempty analyst summary or one of three explicit reasons for proceeding without it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In representative final-packet cases with a supplied release note, 100% pass the host release-note check without a manual body edit or skip label.
- **SC-002**: In hosts that do not ignore packets, 100% of packet-only untracked validation and refresh cases succeed, while 100% of cases with another changed path block.
- **SC-003**: In checklist cases covering first-position and later-position gap tokens, multiple tags on one line, and quoted code examples, G4 and `count-markers gaps/all` report the exact real-gap count in 100% of cases.
- **SC-004**: In stale-index cases, the required artifact check fails before regeneration and passes afterward; untracked files appear in zero backlinks or home entries.
- **SC-005**: For the named-spec reviewability scenarios (ordinary, missing field, valid exception, complete split, incomplete split), every gate result matches the declared budget policy without using a neighboring entry.
- **SC-006**: Both hosts present the same 13 Post rows and reject completion in every tested pending, in-progress, or missing-row case; every team-capable executor tears down its team before returning.
- **SC-007**: In multi-page review cases, 100% of pages are considered, and zero replies or resolutions occur before verification, push, and confirmed matching remote head.
- **SC-008**: A slow nonempty blind-spot result is used regardless of crossing five minutes; every permitted no-findings continuation records one specific reason.
- **SC-009**: Operators can execute all five named helper request examples on both hosts without a malformed-envelope error, and generated roadmap workflow links open at the scaffold output path.
- **SC-010**: Each of four PR slices remains at or below 4 production files and below 25 total files, with passing acceptance fixtures and aligned host instructions.
- **SC-011**: Reviewers can find the recorded confidence verdict, release note, changed-scope explanation, and verification evidence in the final PR artifact without reconstructing them from process files.

## Clarifications

### Gap Counting and Estimation

- Gap counting recognizes the exact, case-sensitive token `Gap` within a single-line, non-nested `[...]` tag. Split the tag contents on commas and trim spaces and tabs around each token. Count each qualifying tag once, whether `Gap` is the first or a later token. For example, `[Gap]`, `[Gap, Exception Flow]`, and `[Coverage, Gap]` each count once; `[gap]`, `[Gapless]`, and nested bracket text do not count. This is a new Clarify decision; the prior Q4 decision did not settle these boundaries.
- Gap tags and clarification markers share the Markdown code-visibility rule for G1/G2/G3/G4 and the relevant `count-markers` paths. Counts and reported details agree; other marker types retain their existing behavior. This resolves design concept Open Question 1.
- Required refactor work must affect the size estimate and suggested slice count. Plan defines the input shape and weight, preserves the ordinary estimate when no refactor work is supplied, and preserves spike precedence. Q11 compared scopes with different story, file, and requirement counts, so its 292-to-1,362 LOC change does not establish a refactor weight.

### Reviewability Gate and Spec Index

- A missing `spec_id` input is an invalid request; an existing identifier with no matching roadmap section or an incomplete entry is a reviewability block with a precise diagnostic.
- Release-artifact refresh runs spec-index generation as a named step after metadata, payload, and marketplace refresh. Its isolated `--check` compares against the source index membership and names changed tracked index paths.
- Source Git index membership decides whether a spec-index input is tracked. Untracked files remain excluded even within a tracked spec directory; staged additions count as tracked.
- Reviewability setup matches the complete, case-sensitive `### <spec_id>:` heading and reads only until the next peer-level roadmap entry. This heading grammar is a new Clarify decision; a missing heading blocks without using neighboring values.
- Use an ordered `Slices:` ID list and a `Slice Budgets:` Markdown table with columns `Slice`, `Estimated LOC`, `Production files`, and `Total files`. Each listed ID has exactly one row with three nonnegative integer values. Reject missing, extra, duplicate, malformed, or placeholder rows and any row at or above a block threshold. The roadmap template uses placeholders and no concrete accepted exception pragma. This format creates no new split exception.
- Plan must reconcile Q11's 1,362 LOC aggregate with its 1,442 LOC sum across A, B, C1, and C2, then establish missing production-file projections before recording actual budgets.

### PR Emission

- The optional `## Release note` heading follows the eight required final-body headings. The single `## UAT Runbook` heading stays between `## How To UAT` and `## Verification`. A release note never appears in a draft body.
- A supplied release note is a fourth final-body editable field. Its heading and balanced marker lines are protected; only the enclosed body is elided from the protected fingerprint. Structure validation checks the heading and markers and exactly one nonempty release-note fence. Final packet schema permits four fields; drafts retain zero.
- The packet-only dirty-worktree exemption applies to the current packet's untracked `<id>.json`, `<id>/body.md`, and `<id>/validation.json` under its validated feature directory. A second packet, tracked modification, unrelated path, or Git-status failure still blocks both mutation helpers.
- Claude and Codex Post guidance keeps the packet at canonical local paths, resolves unrelated worktree changes, runs current read-only validation, and then persists validation; it does not require committing the packet or adding ignore rules.
- The Phase 6.5 table `Verdict` field (`proceed`, `remediate`, or `stop`) is the durable decision. The Workflow Overview Confidence Gate row may remain Pending and is not a verdict source. Draft content may show `Not recorded`; final emission blocks until a valid verdict exists. A protected generated line under `## Verification` shows the current value on first emission and refresh, even when a supplied body would otherwise bypass regeneration.

### Workflow Behavior

- The shared completion-boundary rule reads the persisted workflow and `autopilot-state.json` immediately before either host reports successful completion. The current `status-evidence` rule does not establish that all 13 canonical Post rows are completed.
- Team-capable executors report child-result and cleanup confirmation; Codex child lifetime after parent exit remains an HRNS-017 question.
- Resolve-pr exhausts each thread and comment connection before acting, then verifies, commits, pushes, and confirms the fresh remote PR head SHA before serial replies and resolution. Plan selects the exact API route.
- The Design Concept header’s existing `**Blind-spot pass:**` line is the durable scaffold record. A slow nonempty result is `ran`; dispatch error, empty return, and explicit operator abandonment remain distinct reasons.

### Tracked Issue Reproductions

- [#637](https://github.com/racecraft-lab/racecraft-plugins-public/issues/637): A multi-entry roadmap with an oversized first entry and small last entry must evaluate the requested ID only; an `infra` exception in that selected authored section must be honored; missing budget fields must block. Add greenfield LOC-only and complete-slice aggregation fixtures alongside those original reproductions.
- [#638](https://github.com/racecraft-lab/racecraft-plugins-public/issues/638): New roadmap-template links must resolve to `.process/<SPEC-ID>-workflow.md`, matching scaffold output. Preserve a legacy layout only when its existing link target is verified; otherwise repair the broken link. Add generated-template and existing-roadmap fixtures.

## Assumptions

- The design concept's Q1–Q11 answers are ratified scope decisions. Planning may choose the precise placement of the confidence verdict and the required-refactor signal's shape and weight, and must reconcile the slice budget values without changing their observable outcomes.
- The four-slice delivery route (one split-PR run or separate runs) is decided after Tasks; slice order and per-slice budgets hold either way.
- The current cached plugin cannot benefit from its own repairs until released and refreshed. Interim PR-body repair for this run is operational handling, not a product requirement or a change to host policy.
- This feature does not decide whether Codex children outlive their parent; the teardown obligation applies to both hosts regardless, while HRNS-017 investigates host behavior.
- Existing required checks, release-note policy, packet schema fields other than the optional note, and draft-body policy remain in force.
- The historical stale-index example at `b12f1bba1^` is fixture provenance; tests must freeze it under their own fixture tree rather than read a temporary feature-spec path at runtime.

## Delivery and Verification Constraints

- Every behavior change must land on Claude Code and Codex in the same review slice. Each slice has at most 4 production files and fewer than 25 total files.
- Active repository tooling remains Python 3.11+ standard-library code. The repair does not introduce a Bash or `jq` dependency.
- Generated plugin payloads, generated reference pages, and the spec index are regenerated from their sources, never edited by hand.
- Tests must not read a temporary `specs/<feature>/` path at runtime. Any needed historical text, including the pre-fix ART-007 spec-index case from `b12f1bba1^`, is frozen under the test's own fixtures.
- Generated templates must not gain a literal reviewability-exception pragma example; the existing lifecycle contract prohibits it.
- Every acceptance behavior has failing-first fixture evidence before its repair. Required checks include the quick and CI suites, artifact consistency, relevant documentation and lint checks, and each slice PR's title and release-note checks.
- Slice A updates the PRD acceptance criteria AC-16.2, AC-16.5, AC-16.8, and AC-16.10 and the HRNS-015 and HRNS-019 roadmap entries. It removes the stale statement that autopilot wall-clock work from #642 is still in review.

## Out of Scope

- Redesigning the packet schema beyond one optional release-note field or the Post sequence beyond the 13-row unification.
- Changing any host release-note policy, defaulting to a skip label, or inserting a release-note fence into draft PR bodies.
- The remaining 58 bare helper call sites and self-describing malformed-request errors; HRNS-019 owns that sweep.
- Parsing AGENTS.md or CLAUDE.md tables in the runner; operators may seed declared commands from those documents.
- A new typed reviewability-exception class or host-repository ignore-rule changes.
- Removing team-capable tools from open executors or introducing an autopilot wall-clock budget (already removed by #642).
- Unrelated stale prose, duplicate UAT rendering, and other findings deferred by the design concept unless a touched paragraph must be corrected for consistency.

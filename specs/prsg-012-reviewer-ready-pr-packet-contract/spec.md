# Feature Specification: Reviewer-ready PR packet contract

**Feature Branch**: `prsg-012-reviewer-ready-pr-packet-contract`

**Created**: 2026-06-12

**Status**: Draft

**Input**: User description: "Make autopilot-generated PR titles and descriptions deterministic, reviewer-ready, and validated before `gh pr create` for single-PR and split-PR flows."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Specific conventional PR titles (Priority: P1)

As a reviewer, I see a specific conventional PR title that names the visible or operator-visible change before I open the PR body.

**Why this priority**: The PR title is the first review and squash-merge signal. If it is vague, stale, or non-conventional, the final commit history and review queue are degraded before body details can help.

**Independent Test**: Generate packets for a single-PR run and a split-PR run, then inspect only the rendered titles and validation result to confirm each title is specific, conventional, and packet-owned.

**Acceptance Scenarios**:

1. **Given** autopilot prepares a single PR for a visible or operator-visible change, **When** the PR packet is rendered, **Then** the title follows conventional commit form and names the concrete change.
2. **Given** autopilot prepares split PRs for multiple slices, **When** each packet title is rendered, **Then** each title names the slice-specific change rather than a generic batch label.
3. **Given** a rendered title contains stale placeholder text, banned wording, or a generic non-specific label, **When** packet validation runs, **Then** validation blocks and reports exact title evidence to fix.

---

### User Story 2 - Structured reviewer body (Priority: P1)

As a reviewer, I see a neutral structured PR body with Summary, What Changed, Why It Matters, How To Review, How To UAT, Verification, Scope, and Known Gaps.

**Why this priority**: Reviewers need a stable reading order and complete review evidence without depending on manual cleanup after PR creation.

**Independent Test**: Render a valid packet body and confirm the required headings, source markers, UAT compatibility heading, verification evidence, scope evidence, and known-gap language are present in the final text.

**Acceptance Scenarios**:

1. **Given** a valid rendered packet body, **When** a reviewer opens it, **Then** it contains the required reviewer-facing sections in a stable order.
2. **Given** the same packet body, **When** compatibility content is checked, **Then** the literal `## UAT Runbook` heading remains present alongside the reviewer-facing How To UAT section.
3. **Given** a body omits verification evidence, scope evidence, or required source markers, **When** validation runs, **Then** validation blocks before PR creation and names the missing evidence.
4. **Given** a body uses banned labels such as `ELI5` or `Plain-English Summary`, **When** validation runs, **Then** validation rejects the packet even if other sections are present.

---

### User Story 3 - Pre-create validation block (Priority: P1)

As an operator, invalid packets block before PR creation with exact remediation evidence.

**Why this priority**: The failure must happen before `gh pr create` so operators do not need broad post-create repair and reviewers do not receive stale or incomplete PRs.

**Independent Test**: Run packet validation against valid and invalid packet fixtures for every PR creation mode and confirm invalid packets do not reach PR creation.

**Acceptance Scenarios**:

1. **Given** a packet is missing a required heading, **When** validation runs, **Then** it writes a failed validation result and blocks before PR creation.
2. **Given** a packet passes validation, **When** PR creation proceeds, **Then** the PR creation path uses the generated title and generated body file.
3. **Given** split-PR mode renders multiple packets and one packet is invalid, **When** validation runs, **Then** the invalid packet is blocked with packet-specific evidence before its PR is created.

---

### User Story 4 - Safe prose refinement (Priority: P2)

As a maintainer, I can refine sanctioned prose fields without damaging generated governance sections, source markers, UAT content, traceability, scope, or verification evidence.

**Why this priority**: Maintainers need room to improve reviewer-facing language while preserving deterministic governance and reviewability guarantees.

**Independent Test**: Modify only sanctioned prose fields in a rendered packet and confirm validation still passes, then modify protected governance evidence and confirm validation rejects the change.

**Acceptance Scenarios**:

1. **Given** a maintainer edits sanctioned narrative fields, **When** the rendered packet still preserves protected evidence, **Then** validation accepts the packet.
2. **Given** an edit removes or corrupts source markers, UAT content, traceability, scope, or verification evidence, **When** validation runs, **Then** validation rejects the packet and identifies the damaged invariant.
3. **Given** a host PR template safely contributes additional content, **When** the final packet renders, **Then** the required packet-owned sections and validation guarantees remain intact.

---

### Edge Cases

- A single-PR packet and a split-PR packet require different titles, UAT details, and verification evidence for the same feature.
- A host PR template includes legacy headings, template comments, placeholder variables, or example text in the final rendered body.
- Manual UAT is not applicable for a packet, but the reviewer still needs explicit How To UAT and `## UAT Runbook` content explaining that no manual UAT path is required.
- Known Gaps has no open gaps; the body must still say so explicitly rather than omit the section.
- A source marker appears only inside a code fence, HTML comment, generated fixture, or non-rendered area.
- One split packet fails validation while other split packets pass.
- The packet file path is missing, unreadable, points to a directory, contains invalid JSON, or fails the packet schema before a `packet_id` can be trusted.
- A split-PR run has already opened one or more earlier slice PRs when a later packet fails validation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST generate a packet-owned PR title for the single-PR path.
- **FR-002**: The system MUST generate a packet-owned PR title for each split-PR path.
- **FR-003**: Every generated PR title MUST render as `<type>(<scope>): <plain-English description>` and name the visible or operator-visible change. Spec-backed packets MUST derive the scope from the active spec id when available, such as `PRSG-012` or `SPEC-014C`; non-spec plugin packets MAY fall back to `speckit-pro`. Overrides MUST use an allowed conventional commit type and a valid public scope.
- **FR-003A**: The title generator and validator MUST NOT infer the public description from branch names, spec IDs, slice IDs, task IDs, file paths, or free-form PR body text. Spec IDs MAY appear only as the conventional title scope.
- **FR-003B**: The title description after the colon MUST be public-readable plain English and MUST NOT contain internal identifiers or control tokens, including branch refs, slice IDs, PRSG/SPEC/FR/SC/L# tokens, stale placeholders, unexpanded variables, or banned labels. Validation MUST reject any such token in the description, not only descriptions made solely of internal codes.
- **FR-004**: Every PR creation path MUST use the generated title and generated body file as the PR title and body inputs.
- **FR-004A**: Every PR packet MUST include an explicit PR target with `base_branch` and `head_branch` values. PR creation MUST bind that target to `gh pr create --base <base_branch> --head <head_branch> --title <generated-title> --body-file <generated-body>`.
- **FR-005**: A shared deterministic PR packet validator MUST run before every PR creation attempt.
- **FR-006**: The validator MUST evaluate rendered title and body text after packet rendering, not only schema or source data shape.
- **FR-007**: The validator MUST reject stale placeholders, unfilled template comments, unexpanded variables, example text, branch-derived descriptions, slice-id-only descriptions, internal code tokens, and invalid conventional commit prefixes that remain in the rendered packet.
- **FR-008**: The validator MUST reject rendered bodies missing any required reviewer-facing heading: Summary, What Changed, Why It Matters, How To Review, How To UAT, Verification, Scope, or Known Gaps.
- **FR-008A**: The validator MUST compare the packet's `required_headings` list against rendered Markdown `## <heading>` headings in the canonical packet block and reject bodies where those headings are absent, duplicated, out of order, or satisfied only by packet JSON, host template content, code fences, comments, generated fixtures, `.process` files, or generated zones.
- **FR-009**: Rendered bodies MUST keep the literal `## UAT Runbook` compatibility heading while also providing the reviewer-facing How To UAT section.
- **FR-010**: The validator MUST reject rendered packets missing required rendered source/provenance markers for generated packet content and evidence sources. The legacy `speckit-pro-review-packet-source` HTML comment MAY remain for backward compatibility, but MUST NOT satisfy protected source-marker validation.
- **FR-011**: The validator MUST reject rendered packets missing verification evidence or scope evidence.
- **FR-012**: The validator MUST reject banned labels including `ELI5` and `Plain-English Summary`.
- **FR-013**: Validation failures MUST block before PR creation and report remediation evidence that names the failed rule, packet target, affected section or field, and relevant text excerpt or hash evidence when available.
- **FR-014**: Validation results MUST be written as one JSON record per packet under the target feature `.process/pr-packets/<packet_id>/validation.json` path, with status, error class, exit code, deterministic stderr line, packet identity, mode, PR target, title/body paths or values, rule outcomes, failure details, remediation evidence, `pr_blocked`, resume boundary when blocked, and timestamps.
- **FR-015**: Blocking validation failures MUST append a concise workflow event that records the blocked packet and remediation evidence location.
- **FR-015A**: Missing, unreadable, directory-valued, invalid-JSON, or schema-invalid packet inputs MUST be treated as `input_error` failures, exit `2`, make zero `gh pr create` attempts, and emit deterministic diagnostics. When the target feature directory can be derived, the validator MUST write an input-error validation JSON record under `.process/pr-packets/_input-error-<stable-hash>/validation.json`; when it cannot be derived, the validator MUST emit the same `input_error` JSON envelope to stdout and the deterministic stderr line without mutating repository files.
- **FR-015B**: Rendered-content validation failures MUST be distinguished from input errors: validation failures exit `1`, use `error_class: validation_failure`, include packet-specific remediation evidence, and write workflow evidence before stopping; input errors exit `2`, use `error_class: input_error`, and report the bad input path or schema failure without trusting packet-owned fields that did not parse or validate.
- **FR-015C**: Validator stderr MUST be deterministic and fixture-comparable. Each failed run MUST emit one concise line in the form `validate-pr-packet.sh: <error_class>: <packet_or_input_id>: <rule_or_reason>: <validation_result_path_or_no-path>` with no timestamps, absolute paths, random temporary names, or host-specific wording.
- **FR-015D**: Resume after a blocked packet MUST revalidate the current rendered packet and MUST NOT treat stale failed `validation.json` content as authoritative. A passing rerun MUST overwrite or supersede the prior failed result at the packet's validation path, set `pr_blocked: false`, and allow PR creation only from the newly passed result.
- **FR-015E**: In split-PR mode, if a later packet fails after earlier slice PRs were opened, the failure MUST preserve earlier successful PR evidence in `.process/prs.json`, the Spec MOC PRS table, workflow evidence, and `autopilot-state.json`; MUST NOT close, relabel, retarget, or recreate earlier PRs; MUST set the resume boundary to the failed packet or slice; and MUST reconcile existing PR records before retrying so resume cannot create duplicate PRs.
- **FR-015F**: Blocking workflow events MUST be appended to the active workflow file under `docs/ai/specs/.process/<workflow-id>-workflow.md`; for PRSG-012 this is `docs/ai/specs/.process/PRSG-012-workflow.md`. Each event MUST use a deterministic event id derived from packet or input identity, validation result path, and blocked status so retries can supersede the same event instead of creating ambiguous duplicates. The event MUST use repo-relative paths and include packet or input id, mode when known, PR target when known, validation result path or `no-path`, deterministic stderr line, failed rule or reason, remediation summary, resume boundary, `pr_blocked`, and prior successful split PR references when relevant. The validation JSON remains the authoritative machine-readable record; the workflow event is reader-facing process evidence.
- **FR-016**: The packet contract MUST allow sanctioned prose refinements only inside full-line editable HTML comment marker pairs under `Summary`, `What Changed`, and `Why It Matters`. Field IDs MUST use exact markers such as `<!-- speckit-pro-editable:summary:start -->` and `<!-- speckit-pro-editable:summary:end -->`, mirrored in packet JSON.
- **FR-016A**: The packet contract MUST store a normalized protected-body fingerprint with editable blocks elided. The validator MUST reject any non-editable body change when the protected fingerprint no longer matches.
- **FR-016B**: The validator MUST allow only structural editable-boundary comments and the legacy `speckit-pro-review-packet-source` compatibility comment. It MUST reject unknown HTML comments, template placeholder comments, and stale template comments outside code fences.
- **FR-016C**: Host PR template content MAY coexist only after or outside the protected canonical packet block; host content MUST NOT bury, replace, duplicate, or weaken PRSG-012 canonical sections or protected evidence.
- **FR-017**: Host PR template support MAY coexist only when the final rendered packet still satisfies the packet contract.
- **FR-018**: PRSG-012 MUST treat post-create auto-repair of already-open PRs as out of scope.
- **FR-019**: PRSG-012 MUST update Claude Code and Codex autopilot guidance in lockstep for packet generation, validation, and PR creation behavior. The shared validator and packet schema MUST remain single-copy under `speckit-pro/skills/speckit-autopilot/`; Codex-facing guidance references those shared artifacts by path and MUST NOT introduce duplicate validator or schema copies.

### Constraints

- No new runtime dependencies beyond the repository's existing shell and JSON-processing tooling.
- Deterministic packet generation and validation logic belongs in reusable scripts with fixture-backed validation.
- Existing UAT runbook guarantees from SPEC-006a/b must not be weakened.
- Codex-facing mirrored autopilot behavior must preserve parity with the primary autopilot contract. PRSG-012 guidance changes must name both the primary Claude Code surfaces and their Codex mirrors when behavior is mirrored.

### Reviewability Notes *(if applicable)*

- Typed reviewability exceptions are not expected for PRSG-012.
- Generated packet fixtures, generated zones, `.process` files, PR bodies, and code fences must not be treated as valid provenance for protected source markers.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: contracts, docs/process
- **Projected reviewable LOC**: 500-900 excluding generated fixtures and validation result output
- **Projected production/reference files**: 6-8
- **Projected total files**: 20-24
- **Budget result**: within block threshold with a bounded total-file warning from extending existing evidence fixtures
- **Split decision**: Keep as one spec because title generation, body rendering, validation, and PR creation gating share one reviewer packet contract. Fixture and documentation updates can be reviewed in the same vertical slice without splitting the behavior.

### PR Review Packet Requirements *(mandatory)*

- PR descriptions MUST include what changed, why it matters, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.
- Validation evidence for PRSG-012 MUST show both passing packets and blocked packets across single-PR and split-PR flows.
- Validation evidence for PRSG-012 MUST identify required Layer 4 script fixtures, Layer 3 functional eval expectations for Claude Code and Codex, Layer 7 replay/integration fixture expectations, and Layer 8 parity fixture expectations.

### Key Entities *(include if feature involves data)*

- **PR Packet**: A rendered PR title and body for one PR target, including schema version, packet identity, mode, explicit `base_branch`/`head_branch` target, structured generated-title metadata, body file, required sections, UAT content, rendered source/provenance markers, scope evidence with changed files, verification evidence, known-gap language, editable field boundaries, protected-body fingerprint, and validation result path. PRSG-012 uses a shared `pr-packet.schema.json` for both single-PR and split-PR flows; split packets keep `slice-packet.schema.json` as slice evidence/source input and include slice identity or the source slice packet path. Single-PR packets MUST NOT carry split-only `split_slice` evidence.
- **Generated Title Metadata**: Structured title data with final `value`, conventional commit `type`, `scope`, public-readable `description`, source evidence, and rejected candidates. Single-PR title descriptions come from the feature/spec display title normalized into an action phrase. Split-PR title descriptions come from PR marker `source_boundary.section` in marker mode, or the layer-plan increment name in legacy layer-plan mode. Slice IDs remain metadata and are never title description text.
- **Packet Validation Result**: A JSON record describing pass or fail status, error class, exit code, deterministic stderr line, evaluated rules, packet identity or synthetic input-error identity, mode when known, title value or path when available, body file when available, failures, remediation evidence, whether PR creation was blocked, stale-result/resume policy, prior successful split PR references when relevant, and timestamps.
- **Workflow Event**: A concise process log entry appended to the active workflow file when validation blocks a packet before PR creation, including a deterministic event id, blocked packet or input-error identity, validation result path or `no-path`, deterministic stderr line, failed rule or reason, remediation summary, PR blocked status, resume boundary when one exists, and prior successful split PR references when relevant.
- **Sanctioned Prose Field**: A maintainer-editable narrative field bounded by exact full-line `speckit-pro-editable:<field>:start` and `speckit-pro-editable:<field>:end` HTML comment markers, mirrored in packet JSON, and limited to `summary`, `what_changed`, and `why_it_matters`.
- **Protected Body Fingerprint**: A normalized hash of the rendered body with sanctioned editable blocks elided. It detects any change to protected canonical sections, source markers, UAT content, traceability, scope, verification evidence, known gaps, or generated governance content.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of supported PR creation attempts validate a rendered packet before PR creation is attempted.
- **SC-002**: 100% of seeded invalid packet examples for missing headings, stale placeholders, banned labels, missing source markers, missing verification evidence, and missing scope evidence are blocked with at least one exact remediation evidence item.
- **SC-003**: 100% of seeded valid packet examples render a conventional PR title, all required reviewer-facing sections, and the literal `## UAT Runbook` compatibility heading.
- **SC-004**: A reviewer can identify what changed, why it matters, review order, UAT path, verification evidence, scope, and known gaps from a generated PR body in under 2 minutes.
- **SC-005**: 100% of sanctioned prose refinement examples retain protected governance evidence and pass validation.
- **SC-006**: No valid generated packet requires manual cleanup after rendering before PR creation.
- **SC-007**: 100% of seeded missing, unreadable, invalid-JSON, and schema-invalid packet inputs exit `2`, emit deterministic `input_error` stderr, write input-error evidence when a feature directory is known, and make zero PR creation attempts.
- **SC-008**: 100% of seeded split-PR partial-failure examples preserve earlier opened PR records and resume from the failed packet after correction without duplicate `gh pr create` attempts.
- **SC-009**: PRSG-012 implementation evidence names and updates the expected Layer 4 script tests, Layer 3 Claude Code and Codex functional eval fixtures, Layer 7 replay/integration fixtures, and Layer 8 parity fixtures for packet validation before PR creation.

## Assumptions

- Existing SPEC-006a/b UAT runbook wiring remains the source of UAT content for generated packets.
- Generated title metadata stores the final title value plus type, scope, description, source evidence, and rejected candidates. `gh pr create --title` receives only the final rendered title value.
- Packet `body_file` values are repo-relative rendered Markdown paths passed to `gh pr create --body-file`; absolute paths, parent-directory traversal, directories, and non-Markdown paths are invalid packet contract values.
- Packet `scope_evidence.changed_files` records the changed-file scope the reviewer is expected to inspect, using the same declared-file evidence shape as split packets where available.
- Single-PR title descriptions come from the feature/spec display title in the spec, workflow, or roadmap, normalized into a short action phrase. If no public-readable phrase can be produced, validation blocks instead of falling back to branch names or spec codes.
- Split-PR title descriptions come from persisted PR marker `source_boundary.section` values in marker mode, or from layer-plan increment names in legacy layer-plan mode. Slice IDs, branch names, and file paths are metadata only and never title description text.
- A required source marker is an explicit rendered marker outside HTML comments, code fences, generated fixtures, `.process` artifacts, generated zones, and other non-rendered or non-provenance text.
- The legacy HTML comment marker `speckit-pro-review-packet-source` may remain for backward compatibility with existing self-checks, but it does not satisfy PRSG-012 protected source-marker validation.
- Sanctioned prose fields are limited to exact full-line editable marker pairs under `Summary`, `What Changed`, and `Why It Matters`; generated governance and evidence fields remain validator-protected.
- Host PR template content is appended only after or outside the protected canonical packet block and cannot satisfy required canonical sections or protected evidence by itself.
- Validation failures for edits outside sanctioned fields exit `1`, write packet validation JSON with `pr_blocked: true`, and append workflow evidence. Usage or malformed input errors exit `2`.
- Validation failures and input errors use deterministic stderr as a fixture contract; machine-readable JSON remains the authoritative evidence.
- Input-error validation records use a stable synthetic packet id only when packet-owned `packet_id` cannot be trusted.
- Resume always validates current rendered packet content before PR creation; cached failed validation results are evidence, not permission or denial.
- Split-PR resume relies on existing PRSG-009 state surfaces (`.process/prs.json`, Spec MOC PRS table, workflow evidence, and `autopilot-state.json`) to identify already opened PRs before retrying a blocked packet.
- Validation JSON for this feature is written per packet under `specs/prsg-012-reviewer-ready-pr-packet-contract/.process/pr-packets/<packet_id>/validation.json`, with an optional aggregate index for a run.
- PRSG-012 covers generation and validation before PR creation only; repair of already-open PRs is deferred to a later feature if needed.

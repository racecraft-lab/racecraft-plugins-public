# Recorded planning approval security follow-up

PR #1364, finding F1364-4f87a096: planning digest false pass. Workflow
normalization discarded checkbox state even for planning choices under ordinary
headings. The shared runner now preserves checked versus unchecked state and
normalizes only the spelling of a checked marker (`x` versus `X`). Code fences
preserve all input bytes, including execution-row lookalikes. Both hosts ship
the same runner implementation.

The regression tests exercise manifest, record and verify through the public
runner request seam. They cover lowercase and uppercase checks, nested lines,
ordinary headings, checked-marker spelling, execution rows and sections, fenced
checkboxes, and planning-choice text. Each preserved-input case also flips a
planning choice after the excluded region and requires a new digest and refusal
of the old approval. These boundary assertions fail on the pre-fix helper;
the accepted bookkeeping/spelling assertions already passed there.

## Assurance guard follow-up

Finding F1364-e793efeb is a tamper-proof assurance gate false pass. The guard
previously accepted any negation anywhere on the same line as an assurance
term. It now checks each sentence independently and accepts an assurance term
only in a complete, explicit denial: `The approval is not <term>` or
`Nothing may describe it as <term>`. The term may be hyphenated, spaced or
unhyphenated, with case ignored. All other sentences containing the term fail.
An unrelated negation, a qualified negation, or a second positive claim cannot
borrow the exemption from a denial.
Markdown soft line breaks stay inside their sentence, so a wrapped qualifier
or a preceding `The following statement is false:` cannot detach from a denial.

`AssuranceGuardTest` injects document text into the actual public-document
guard. Its named tests cover following and preceding negations; all spellings;
genuine denials followed or preceded by positive claims; double negation and
`not only`; sentence, clause and line boundaries; and each scanned public
surface independently. The scan includes the shared skill/reference, agent
source, Codex descriptor/agent, and both generated host payloads. The existing
runner tests continue to exercise the source and both shipped hosts.

## Declared progress follow-up

### Round 10 writer inventory

The inventory below includes every workflow or feature-map write reached after
approval, including Implement setup, resume, final verification, and Post.
Locations refer to the input revision of this round; `phase-execution.md`,
`post-implementation.md`, and `workflow-file-protocol.md` live in
`speckit-pro/skills/speckit-autopilot/references/`. Code paths below are relative
to `speckit-pro/speckit_pro_runner/`. The protocol was read in full; the phase
and Post write sites were traced to their result and bookkeeping contracts.

| Region | Writer | Source file:line | Progress or planning |
| --- | --- | --- | --- |
| Workflow Overview status | Parent after every phase, including resume | workflow-file-protocol.md:10; phase-execution.md:566,5114 | Progress; reader vocabulary owned by workflow_stage.py:85 |
| Workflow Overview summary notes | Same parent | workflow-file-protocol.md:10; phase-execution.md:5115 | Typed result summary is progress; existing notes and arbitrary added prose are planning |
| Basic Information Stage | Stage resolution and changed plan terminal stage | workflow-file-protocol.md:55; helpers/plan_stage_terminal.py:127 | Closed stage value is progress; any other text is planning |
| Basic Information Draft PR | Successful draft creation, refresh or repair | workflow-file-protocol.md:84; phase-execution.md:2147,3643 | PR identity and numeric artifact-gap count are progress; other text is planning |
| Implement Checklist Gate | Parent once before first Phase 7 dispatch | workflow-file-protocol.md:18; phase-execution.md:3888,3907 | Fixed decision and measured counts are progress; an unknown reason is an evidence reference; arbitrary decision/text changes are planning |
| Implementation Progress | Parent after task/phase results | workflow-file-protocol.md:18; phase-execution.md:566,2280 | Completion counts and typed results are progress; task/phase definitions are planning |
| Files Generated | Parent phase bookkeeping | phase-execution.md:5118 | Tick is progress; generated artifact path is planning |
| Post-Implementation Checklist | Parent synthesizes each canonical Post result | workflow-file-protocol.md:18; post-implementation.md:252,350,404 | Status, result counts and evidence references are progress; requirements and action directives are planning |
| Success Criteria / Success Criteria Summary | Parent ticks completed criteria | workflow-file-protocol.md:18 | Tick is progress; criterion text is planning, including nested criteria |
| Prerequisites baseline results | Implement setup after feedback sweep | phase-execution.md:2343,2354 | Status and test count are progress; command, slot and authorization changes are planning |
| Constitution Validation final result | Parent after Implement | workflow-file-protocol.md:28 | Typed final result is progress; principle, requirement and verification command are planning |
| Quality Gates Final column | Phase 7 final verification and Post Integration Suite | phase-execution.md:4759,4769; post-implementation.md:57 | Result/count/evidence is progress; command, tool, threshold and operator answer are planning |
| Quality Gates Hardener line | Same final verification writer | phase-execution.md:4776,4782; post-implementation.md:57 | Typed status, iterations, scores and evidence are progress; directives remain planning |
| Formal Checkpoints | write_checkpoint, including Final/Post and waiver records | formal/evidence.py:63,71,79 | Owned verdict and canonical result path are progress; row definition and extra evidence prose are planning |
| Lessons Learned and three template subsections | Retrospective parent | workflow-file-protocol.md:3; post-implementation.md:438; workflow-template.md:548 | Result reference is progress; lesson prose is planning-bound rather than discarded |
| Feedback Sweep Log | Sweep bookkeeping after classification/amendment | workflow-file-protocol.md:141; phase-execution.md:3167,3200 | Fixed dispositions and metadata are progress; arbitrary disposition/extra prose is planning |
| Consensus Resolution Log | Sweep adds linked resolution after an amendment | workflow-file-protocol.md:30,178; phase-execution.md:3177,3212 | Closed sweep metadata is progress; accepted requirements, resolutions and changed decisions are planning |
| Phase 7 results: notes-write gaps and review follow-ups | Parent after failed notes create/append or exhausted review allowance | phase-execution.md:3973,4118,4732 | Typed outcome/evidence reference is progress; new instructions are planning |
| Phase 7 results: fallback, deferral, interpretation, deferred_digest | Parent execution-control/finalize-run | phase-execution.md:4280,4421,4549,4557 | Outcome, digest and reference to the already approved decision are progress; a new decision is planning |
| Phase 7 results: plugin drift | Parent after runtime refresh | phase-execution.md:4604,4634 | Version/call result evidence is progress; modified dispatch policy is planning |
| PR Marker Plan evidence/checkpoint | Parent after each marker | workflow-file-protocol.md:241; phase-execution.md:2302 | Checkpoint SHA/status/evidence is progress; task membership, order, ownership and source fingerprint are planning |
| Artifact Review Handoff | Plan terminal, or sweep regeneration following a planning amendment | workflow-file-protocol.md:270; phase-execution.md:1875,3296 | Planning evidence: ordinary Implement progress does not rewrite it; an amendment changes the reviewed artifact and requires renewed approval |
| Post integration, terms lint and UAT outcome | Parent after checks and mandatory runbook attempt | post-implementation.md:570,1043,1056 | Typed counts/status/evidence is progress; any changed requirement is planning |
| Multi-PR emission workflow evidence | Parent after each successful slice PR | post-implementation.md:832,850 | PR/head/verification/resume evidence is progress; planned slice scope/order/base remain bound |
| Feature SPEC-MOC frontmatter status | Parent progress and status readers | helpers/read_only.py:6655,6678 | Recognized status is progress; all other metadata and unknown status prose are planning |
| Feature SPEC-MOC generated PRS and backlinks | generate-spec-index-write at every boundary and PR emission | phase-execution.md:4853; post-implementation.md:832,847; helpers/read_only.py:4058,4257,4440 | Canonical generated navigation is progress; edited generated text and non-generated map content are planning |
| Earlier phase results, consensus repairs, confidence/autonomy and atomicity decisions | Explicit repair or changed plan | workflow-file-protocol.md:11-17,30,37; phase-execution.md:550,1337,1531 | Planning: a new decision requires a new approval; these are not progress exemptions |

### Chosen shape and seam

Shape **(b)**: a single code-owned table declares the progress regions and their
typed fields. A contract test compares the protocol's complete Implement write
list with that table, so naming another write without implementing its contract
fails. The public seam remains `planning_manifest` / record / verify; the
normalizer is a deep module that leaves callers with one revision identity.

The throwaway prototype compared a whole-region allowlist with a typed-value
projection using completion, a directive, and completion followed by a
directive. The allowlist erased both directives; the typed projection retained
both. This rules out shape (a) under the requirement that planning text inside
a progress region remain bound. The trade-off is an explicit progress format:
free prose cannot deterministically be classified as execution rather than a
new instruction. Writers retain planning prose and append typed results or
evidence references; they do not replace planning notes with arbitrary summaries.
Full narrative result details remain in their existing execution records.

Success Criteria are explicit: **text is planning; tick state is progress**.
Other planning-choice checkboxes retain their checked/unchecked distinction.
Status values come from the workflow reader's owner, never a second list.
Formal checkpoint cells use the formal owner's current recorded verdict and
canonical result paths; the planning normalizer does not maintain a second
verdict vocabulary. Unrecognized prose remains bound. Declared heading paths
match beneath document parents, so the sweep's documented sibling placement
works at any heading level without ignoring nested planning content.

The expanded pre-fix run passed 292 of 338 checks: 46 failures reproduced the
missing progress exclusions and hidden planning text, including the actual
spec-index writer. The matrix checks source and both packaged runners.

The round-10 matrix covers 49 progress transitions across all 30 code-owned
write contracts and a planning edit inside each region. It includes the real formal checkpoint writer and the
real spec-index renderer, plus status values from the shared reader owner.
The protocol contract check also rejects a newly named Implement write that has
no code entry or behavioral case. Every positive fixture asserts that its
before/after bytes differ, preventing a preserve test from passing on a no-op.

The earlier Daybreak checkbox and assurance tests remain: ordinary planning
choices still bind checked/unchecked state; explicit Success Criteria now bind
text rather than completion ticks. Blank execution sections no longer suppress
nested planning text. The new tests tighten the previously accepted Stage,
Draft PR, lesson-bullet and whole-section limits instead of extending them.
No new independent Daybreak verdict is claimed here.

## Known limits

- Prior approval digests are not migration tokens. This repair changes their
  projection, so a record made with the older projection may need a fresh plan
  review after upgrading. The new protocol is used for subsequent progress;
  existing free-form notes remain bound. Silently trusting old excluded prose
  would reintroduce the known false pass.
- The verification-record writer stores results in the workflow's
  `.process/verification/` directory (`execution_control.py:evidence_directory`,
  `verification_records.py:execute_verification`); implementation notes use
  `.process/implementation-notes.md`. A top-level `verification-record.json`
  reference is not emitted by either writer and remains bound. This resolves
  the conditional review concern without broadening accepted evidence paths.
- Formal checkpoint results remain live verification evidence, not approved
  planning choices. Their statuses can change `planning_complete` while the
  selected models and planning inputs remain unchanged. Admission must still
  validate current formal evidence; approval never establishes that a checker
  ran or passed. Compact records under `.specify/formal-evidence/` are included
  in `formal/helper.py:check`'s `commit_paths`, including waiver records through
  `formal/lifecycle.py:waive_checkpoint`. `formal-methods.md`'s Commit and resume
  protocol requires those paths to be committed with the workflow.
  A checkout missing them is incomplete and fails closed. Raw ignored formal
  run output is a separate path and is not read by this projection.
- The formal writer rewrites the file with LF and a final newline. CRLF or
  unusual Unicode line endings inside literal code fences, or a path alias,
  can still change bound bytes or the result-path key. Scaffold and the
  documented writer calls use LF and the canonical repository-relative
  workflow path, so these layouts are not produced by those paths.
- Generated navigation is normalized only against the deterministic owner's
  current output. A partially updated PR manifest/map pair may fail closed
  until regeneration finishes. The phase and PR-emission protocols regenerate
  before their checkpoint, so a completed writer does not commit that pair.
- The assurance guard accepts its two explicit denial forms and does not infer
  arbitrary English negation. Obfuscated assurance terms split by HTML,
  entities, punctuation, or look-alike letters are outside its recognition;
  no scanned document uses them. Its existing regression tests remain intact.
- The approval has recorded assurance and does not defend against an agent
  with the operator's file access. Interactive confirmation is exercised through
  its documented JSON contract, not a live question UI in this unattended run.
- Static caller discovery may label unittest methods `test-path-dead`; the
  standard unittest loader executes them. Such rows are reported rather than
  entered into an acknowledgement ledger.
- Linux VM tests do not cover native macOS plugin CI or
  `test_gate_hardening.py::test_pr_test_code_cannot_touch_the_host_under_the_real_sandbox`
  and
  `test_gate_hardening.py::test_pr_test_code_cannot_create_or_modify_any_file_in_the_clone`.
  Those require the orchestrator's macOS host run before merge.
- Native docs browser checks are unavailable in this sandbox: Chromium's macOS
  Mach-port registration is denied. The docs build, link/type/quality checks,
  50 non-browser smoke checks and gallery catalog check pass; 38 smoke browser
  cases and 3 gallery browser cases remain host validation. No docs UI changed
  in this repair; full docs mode was selected by generated reference drift.

## Generated-navigation security repair

Finding `F1364-400139c5` names an **approval-binding false pass**: set membership
discarded missing, duplicated and reordered generated navigation. The renderer's
public progress output now preserves the complete ordered body, including blank
and repeated lines. Approval projects a body only when its complete marker block
matches that output. Projected and raw maps use distinct tagged encodings, so
deleting all generated body text cannot imitate the projected bytes. Marker
bytes, placement and surrounding authored bytes stay bound. A nonmatching or duplicate block keeps the unprojected map (after the
independently declared frontmatter-status normalization).

All tests below live in `tests/speckit-pro/unit/test-planning-approval.py`.
The mutation assertions exercise the public manifest function and the packaged
runner request for both Claude and Codex, with canonical-host baselines checked
before mutation.

| Variant | Regression test |
| --- | --- |
| Omit PRS notice, table header, separator or either required PR row | `NavigationContentTest.test_omitted_prs_header_notice_and_each_row_change_revision` |
| Omit any BACKLINKS row while its artifact exists | `NavigationContentTest.test_omitted_each_backlink_changes_revision` |
| Empty either or both entire bodies while retaining markers; empty BACKLINKS before a PR manifest exists | `NavigationContentTest.test_omitted_entire_body_changes_revision`; `NavigationCompatibilityTest.test_empty_backlinks_with_no_pr_manifest_change_revision` |
| Remove PRS, BACKLINKS or both complete marker pairs and bodies | `NavigationContentTest.test_removed_marker_pairs_change_revision` |
| Duplicate any canonical body row | `NavigationContentTest.test_duplicate_each_canonical_row_changes_revision` |
| Duplicate either marker pair | `NavigationStructureTest.test_duplicate_and_relocated_marker_pairs_change_revision` (`duplicate`) |
| Reorder canonical rows in either zone | `NavigationContentTest.test_reordered_canonical_rows_change_revision` |
| Relocate either complete marker pair across authored content | `NavigationStructureTest.test_duplicate_and_relocated_marker_pairs_change_revision` (`relocated`) |
| Missing individual markers, changed marker spelling, mixed newlines, added prose, fenced blocks and renamed link/scope targets | `NavigationStructureTest.test_noncanonical_markers_and_body_bytes_change_revision` |
| Schema-1 PR rows, legacy markers and CRLF: omitted, duplicated and reordered bodies in both zones | `NavigationCompatibilityTest.test_schema_one_legacy_markers_and_crlf_bind_each_body_edit` |
| Approval apply refreshes its own canonical map; dry-run preserves both files; source and both packaged hosts verify the record | `NavigationApprovalLifecycleTest.test_record_refreshes_canonical_backlinks_and_verifies_on_each_host` |
| Explicitly reviewed noncanonical maps keep their bound bytes during record creation | `NavigationApprovalLifecycleTest.test_record_preserves_explicitly_reviewed_noncanonical_navigation` |

The initial unfixed run reproduced 30 false passes across every reported variant
group (496 of 526 checks passed). The generic progress fixture now models a real
schema-1 PR manifest transition and its complete generated body; its previous
empty-to-partial backlink transition contradicted the canonical-output contract.
The existing real-renderer schema-2 progress test also remains in place.

Independent Standards and Spec review of the first repair found a whole-body
encoding collision and an approval-record backlink lifecycle regression. The
additional omission tests failed before the tagged encoding fix; the record
round-trip test failed before the writer fix. Recording now refreshes only the
feature's already-canonical map through the renderer owner after publishing the
record. Its map write uses the captured content snapshot, preserving concurrent
edits. Verification remains read-only, and runtime backlink rows are still
checked in full. Other runtime writers regenerate navigation before their
checkpoint as required by the phase-boundary protocol; intermediate source/map
states fail closed.

If record publication succeeds but the subsequent map refresh is interrupted,
the helper reports that the record was written and requires regeneration before
verification. The existing record remains audit evidence; a conflicting map is
not overwritten and verification does not gain an exemption.

This changes the shared policy seam and renderer contract, with regenerated
payloads for both hosts. No skill, agent or overlay instruction needs a different
rule. Existing approvals may require renewed review because marker placement and
formerly discarded map bytes now participate in the revision. Daybreak must
re-check the fix commits before the finding can be resolved.

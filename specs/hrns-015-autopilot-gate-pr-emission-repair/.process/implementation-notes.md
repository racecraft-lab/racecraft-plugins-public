# Implementation Notes: HRNS-015

### T001

**Deviations/Edge cases/Surprises:** Current candidate inventory and budgets pass. T001 also requires reconciliation against a first actual implementation checkpoint; T002 and the first source batch depend on T001, so that checkpoint cannot yet exist. The native journal retains an unfinished result while the operator clarifies whether the approved timing applies here. No actual checkpoint evidence or task completion is claimed.

## T001 — scoped resume

Candidate verification completed under the operator-approved timing decision. The native journal retains the earlier unfinished attempt and appends the complete result. Actual diff, LOC and checkpoint reconciliation remains mandatory before PR emission; all eighteen implementation checkpoints remain pending.

## T002

Verified all eighteen candidate budgets, current v1 marker fingerprints, Q11/five-group provenance and #676 reuse. Native guard passed53 rows; completion recorded before checkbox update. Actual emission qualification remains pending.

## T003 — tests ready

Executor supplied six inline test methods. The proposed unittest discovery invocation executed zero tests and is unqualified. Its hyphenated filename is excluded by discovery; the verified registered entrypoint executes the existing file directly and loads199 methods. No production changes occurred. The corrected native RED is in flight; T003 remains unfinished.

## T004 — waiting for RED

No renderer, schema or host instruction edits occurred. The shared unit awaits actual assertion-failure RED from the registered single-file entrypoint. No completion or fabricated TDD evidence is recorded.

## T003 — verified RED and first GREEN

Registered native command executed199 tests. RED failed17 real assertions; source changes brought GREEN to197/199 with two draft subcases still failing. Earlier zero-test discovery is not RED. The bounded FR-003 correction is reserved for diagnosis; no task is marked complete.

## T004 — minimal source ready, closure pending

Executor changed only renderer, schema and both host instructions (32 added lines). The ambiguous insertion guard was refused and the untouched files were completed at a verified anchor. The first native GREEN fails two draft subcases; no GREEN/refactor or marker checkpoint pass is claimed.


## Task Result: T003

**Status:** unfinished — REFACTOR_READY
**TDD unit:** A1a, shared with T004

**TDD Evidence:**

- Tests written: six methods.
- Parent RED: 17 real assertion failures.
- Parent corrected GREEN: 199/199 passed, exit 0.
- REFACTOR: inspection completed; no changes necessary. Distinct parent verification pending.

**Test command:**

```text
python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py
```

**Files modified:** Existing mutation-helper test; unchanged during refactor inspection.

**Errors:** None new. Earlier zero-test invocation and invalid draft setup remain preserved in history.

**Deviations/Edge cases/Surprises:** All meaningful assertions retained. Scoped `git diff --check` passed.

## Task Result: T004

**Status:** unfinished — REFACTOR_READY
**TDD unit:** A1a, shared evidence above.

**TDD Evidence:** Corrected GREEN verified by parent. Refactor is a justified no-op; no tests executed during this turn.

**Test command:** Same registered command above.

**Files modified:**

- `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`
- `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`
- Both host `speckit-autopilot/SKILL.md` files.

**Errors:** None new.

**Deviations/Edge cases/Surprises:** The 12-line runtime change reuses existing validation, newline and fingerprint mechanisms. Both host additions match; no helper extraction or additional behavior is needed. All five owned files remain unchanged. Parent-owned refactor verification, generated outputs, lint and checkpoint gates remain unresolved.

Parent verification: distinct REFACTOR ran 199 tests, all passed, exit 0. Source tasks remain unfinished because independent review found two reproduced release-note fence defects. Original review follows.

## Answer

Two defects found in A1a:

1. **An existing release-note section can be duplicated.** If `inputs.body` already contains a release-note fence and `inputs.release_note` is supplied, the renderer copies the body and unconditionally appends another section. The host parser then sees two fences and rejects the note. This conflicts with FR-002’s exactly-one-fence requirement.

2. **Some fence-breaking line separators bypass validation.** The runtime and schema guard only recognize CR/LF before a fence. The host release-note parser uses `splitlines()`, which also treats Unicode line separators such as U+0085 as line boundaries. A note containing U+0085 before a backtick fence can therefore pass input validation while the host parser sees an early fence and truncates the extracted note. This conflicts with FR-001’s fence-breaking-input rejection.

## Evidence

- **File**: `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` (lines 574–591)
  **Pattern**: A supplied body is retained, then a release-note section and fence are appended without checking whether the body already contains one.

- **File**: `scripts/release_note_policy.py` (lines 165–202)
  **Pattern**: The host parser uses `splitlines()` and requires exactly one extracted release-note fence. A second existing fence makes extraction ambiguous.

- **File**: `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` (lines 541–546)
  **Pattern**: Runtime validation detects fence lines only after `\r` or `\n`.

- **File**: `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json` (lines 50–56)
  **Pattern**: The schema repeats the CR/LF-only fence check, so it has the same line-separator gap.

- **File**: `specs/hrns-015-autopilot-gate-pr-emission-repair/spec.md` (lines 233–235)
  **Pattern**: FR-001 requires rejection of fence-breaking values; FR-003 requires absent-note and draft bodies to remain free of release-note content.

- **File**: `speckit-pro/skills/speckit-autopilot/SKILL.md` and `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`
  **Pattern**: The paired instructions match on optional note handling, the three existing final editable fields, and draft omission. I found no host-parity defect.

**Limits:** This was a read-only source and diff review. I did not rerun tests; A1b’s editable-field work was outside this review.

## Confidence

**Medium**

**Rationale**: The duplicate-fence path follows directly from the renderer and parser code. The Unicode separator finding follows from the mismatch between the runtime/schema checks and the host parser’s line splitting; it was not reproduced by running code.

## Security Relevance

security_relevant: true — caller-controlled content can cross the intended fence boundary or be parsed inconsistently.


## Consensus Result

**Protocol:** installed speckit-autopilot consensus protocol
**Round:** 1
**Routed Categories:** [security]
**Analysts Run:** 3
**Agreement:** 3/3 unanimous
**Confidence:** high

**Answer:**
Reject a supplied body containing a preexisting top-level `release-note` fence when final rendering supplies a new release note. Match the host’s fence recognition, including malformed opening fences it recognizes, using Markdown-aware detection. Permit heading-only bodies and literal fence lines inside other fenced examples. Preserve the supplied body and leave the no-note path unchanged.

The three analysts agree on this boundary. The separate `corrective_run_budget_exhausted` refusal concerns execution approval and does not change their agreement.

**Supporting Analysts:**
- **Codebase analyst:** Append anchor at `pr_emission.py:574–591`; host recognition at `release_note_policy.py:165–202`; requires Markdown-aware detection and preserves the no-note path.
- **Spec context analyst:** FR002 requires exactly one `release-note` fence, not exactly one heading. Existing FR001/FR002/FR003 and T003/T004 cover the correction.
- **Domain researcher:** Supplied specification and parent probe support rejecting recognized existing fences while accepting headings and harmless fenced examples; no independent source fetch was performed.

**Dissent:** None

**Artifact Edit:**
- **File:** `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`
- **Section:** Final release-note append branch, anchor 574–591
- **Action:** Add
- **Content:**
```markdown
Immediately before appending the generated release-note section, within
`if mode != "draft" and release_note is not None`, reject the supplied body
if Markdown-aware recognition finds a preexisting top-level `release-note`
fence opening that the host release-note parser recognizes, whether complete
or malformed.

Match the host recognition contract in `scripts/release_note_policy.py`;
reuse existing runner Markdown fence handling where applicable. Shipped
runner code must not import repository scripts.

Do not reject `## Release note` headings alone or literal release-note fence
lines inside other fenced examples. Preserve the supplied body, retain the
existing append operation for accepted input, and leave rendering without
a supplied release note unchanged.
```

**Artifact Edit:**
- **File:** `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`
- **Section:** PR emission release-note coverage, anchor 8834+
- **Action:** Add
- **Content:**
```markdown
Verify the final renderer's supplied-body boundary with these cases:

- Supplying a new release note with an existing top-level release-note fence
  fails, including malformed opening fences recognized by the host.
- Supplying a new release note with a release-note heading alone succeeds.
- Supplying a new release note with literal release-note fence lines inside
  another fenced example succeeds.
- Omitting the release note preserves the supplied body unchanged.

For accepted note-bearing cases, verify that the host recognizes exactly one
release-note fence and accepts the result for a feature PR title.
```

**Flags:** None


## Consensus Result

**Protocol:** installed speckit-autopilot consensus protocol
**Round:** 1
**Routed Categories:** [security]
**Analysts Run:** 3
**Agreement:** 3/3 unanimous
**Confidence:** high

**Answer:**
Align A1a runtime and schema fence checks with the downstream parser’s `splitlines()` boundaries. Reject parser-visible fence lines while preserving harmless separators and inline fences. This enforces FR001 and supports FR002 verification within existing T003/T004 scope.

**Supporting Analysts:**
- **Codebase Analyst:** Runtime 541–546, schema 50–56, and host parser 165–202 identify the mismatch and support aligned checks.
- **Spec Context Analyst:** FR001 already requires fence-breaking rejection; T003/T004 cover this correction without additional tasks or schema properties.
- **Domain Researcher:** Supplied Python 3.11 documentation and reported local probe support all documented boundaries and the anchored fence rule.

**Dissent:** None.

**Artifact Edit:**
- **File:** speckit-pro/speckit_pro_runner/helpers/pr_emission.py
- **Section:** Release-note validation under `if "release_note" in inputs:`
- **Action:** Replace
- **Content:**
```python
if any(re.match(r"^[ \t]*(?:`{3,}|~{3,})", line) for line in release_note.splitlines()):
```
Preserve the existing `invalid_packet_input` body unchanged.

**Artifact Edit:**
- **File:** speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json
- **Section:** `properties.release_note.not.pattern`
- **Action:** Replace
- **Content:**
```json
"(?:^|[\\u000a\\u000d\\u000b\\u000c\\u001c\\u001d\\u001e\\u0085\\u2028\\u2029])[ \\t]*(?:`{3,}|~{3,})"
```

**Artifact Edit:**
- **File:** tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py
- **Section:** `test_pr_packet_output_release_note_rejects_fenced_or_fence_breaking_strings` and existing valid/absence release-note tests
- **Action:** Add
- **Content:**
```markdown
- Extend malformed cases with each additional separator: VT (`\x0b`), FF (`\x0c`), FS (`\x1c`), GS (`\x1d`), RS (`\x1e`), NEL (`\x85`), LS (`\u2028`), and PS (`\u2029`).
- For every separator, reject `Before<separator>```<separator>After` and `Before<separator>~~~<separator>After` through both runtime validation and the loaded schema validator.
- Preserve existing LF, CR, and CRLF rejection coverage.
- Accept ordinary text containing each separator without a fence line.
- Accept inline triple backticks and inline tilde fences.
- Preserve the existing absent-release-note behavior.
```
These are exact case additions for the existing tests, not executable replacement test code.

**Flags:** None

The earlier human-review flag is withdrawn: all three analysts agree on the security behavior. This proposal was neither applied nor verified. Execution remains separately blocked by `corrective_run_budget_exhausted` (2/2 spent); this synthesis grants no budget exception.


## Consensus Result

**Protocol:** installed speckit-autopilot consensus protocol
**Round:** 1
**Routed Categories:** [security]
**Analysts Run:** 3
**Agreement:** 3/3 unanimous
**Confidence:** high

**Answer:**
Extend the agreed input guard to reject an unclosed enclosing code fence when final rendering supplies a release note. In the candidate’s fence scan, replace the `close_index is None` branch’s `break` with an `invalid_packet_input` return identifying `body`.

Retain rejection of existing top-level release-note fences. Accept heading-only bodies and properly closed code examples. Leave the no-note path unchanged. No specification, task, schema, or checkpoint change is needed.

The actual probe shows renderer/helper exit 0 and host extractor `None`; it does **not** establish a passing host validator result. The budget refusal remains a separate execution constraint; this consensus does not authorize an exception.

**Supporting Analysts:**
- **Codebase analyst:** An unclosed enclosing fence causes host extraction to stop with zero matches; proposes the exact `close_index is None` branch correction and input-error regression.
- **Spec context analyst:** FR002 requires passing the host check; FR001/FR003 preserve the optional-note and no-note behavior. Existing T003/T004 cover this correction.
- **Domain researcher:** Parent-supplied probe and FR002 support rejecting an insertion point inside an unclosed host-recognized code fence, including backtick and tilde fences. No independent retrieval was performed.

**Dissent:** None

**Artifact Edit:**
- **File:** `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`
- **Section:** Candidate supplied-body fence scan before the final release-note append
- **Action:** Replace
- **Content:**
```markdown
Within the supplied-body fence scan executed only when
`mode != "draft" and release_note is not None`, replace the
`close_index is None` branch's `break` with a return of
`invalid_packet_input` identifying `body`.

Reject an enclosing code fence that remains unclosed under the host's fence
recognition rules, because appending the generated section there prevents
the host from extracting the release note.

Retain rejection of existing top-level release-note fences. Accept
heading-only bodies and literal release-note fence lines inside properly
closed code examples. Preserve the supplied body for accepted inputs and
leave the no-note path unchanged.
```

**Artifact Edit:**
- **File:** `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`
- **Section:** PR emission release-note coverage, anchor 8834+
- **Action:** Add
- **Content:**
```markdown
Add regression cases for the final supplied-note input boundary:

- A valid eight-heading body ending with an unclosed backtick code fence,
  with a supplied release note, returns input-error exit code 2 identifying
  `body` and writes no files.
- Repeat with an unclosed tilde code fence recognized by the host.
- Omitting the release note preserves the same unclosed-fence body unchanged.
- A properly closed Python code example accepts the supplied release note,
  and host extraction returns that note.

Retain coverage rejecting preexisting top-level release-note fences and
accepting heading-only bodies and harmless literals inside closed examples.
```

**Flags:** None


## Task Result: T003

**Status:** unfinished — private review candidate ready
**TDD unit:** A1a, shared with T004

**TDD Evidence:**

- Original six tests retained verbatim.
- Four additive regression methods proposed.
- Focused current-source RED: exit 1, 40 assertion failures, zero errors/skips.
- Private candidate GREEN: exit 0, all four methods passed.
- REFACTOR/native completion: unqualified.

**Test commands used:**

```text
python3 private HRNS-015 audit artifact live
python3 private HRNS-015 audit artifact candidate
```

**Files created/modified:** Private test copy, harness, logs and review records under `private HRNS-015 audit artifact`.

**Errors:** Live correction remains unauthorized after `corrective_run_budget_exhausted`.

**Deviations/Edge cases/Surprises:** Tests cover both fence types across all eight separators, harmless separators, inline markers, existing/malformed fences, unclosed enclosing fences, heading-only bodies and closed code examples. No bound-checkout edits.

## Task Result: T004

**Status:** unfinished — private review candidate ready
**TDD unit:** A1a, shared evidence above

**TDD Evidence:** Private candidate checks pass; they do not qualify native TDD, refactor, full suites or A1a completion.

**Test commands used:** Same focused commands above.

**Files created/modified:** Private copies of `pr_emission.py` and `pr-packet.schema.json`.

**Errors:** Native corrective approval remains required before applying source changes.

**Deviations/Edge cases/Surprises:** The proposal preserves supplied content, rejects conflicting or unclosed fences, and uses the portable Unicode separator pattern. Read-only `git apply --check` passed.

The exact [patch](private HRNS-015 audit artifact) is **12,765 bytes**, SHA256:

```text
2681be70efc9fbda1ea2045c5fa39d99c3d6b4a9c04eca9becf42ac849825147
```

Independently captured live base hashes, all rechecked unchanged:

| File | SHA256 |
|---|---|
| `pr_emission.py` | `15e9a981709a58d313870a1ca4b94066d41ece0dd9a2edff576051fe508aa806` |
| `pr-packet.schema.json` | `08724960a7243c0ffa73fcee2cb90ddaa74bae7cc87a034d38a023616e30601f` |
| Mutation-helper test | `9f867ff4ed5e587ccc256a6514bccae30d01c754735683ed0fb5116d72323d17` |

The [README](private HRNS-015 audit artifact) and [manifest](private HRNS-015 audit artifact) contain log digests, preserved earlier revisions and the minimum native validation plan: guarded approval, test-first RED, source/schema GREEN and refactor proof, then parent-owned lint, generated outputs and checkpoint gates.

Parent review: exact candidate hashes and live base hashes verified; git apply --check passed without applying. All current dispatches settled and native checkpoint preserved. Tasks T003 and T004 remain unfinished pending explicit guarded corrective exception approval.


### Approved FR-001 correction: native verification and journal checkpoint

Native RED reproduced 40 assertion failures across 203 tests. GREEN and distinct refactor each passed 203/203. Ruff, mypy (50 files), reference check and docs quality passed. Independent A1a review found no defects. Generated release outputs were refreshed. These are behavioral proofs, not task journal or PR-emission qualification.

#### T003: original source_applied_green_ready result

## Task Result: T003

**Status:** unfinished — SOURCE_APPLIED_GREEN_READY
**TDD unit:** A1a, shared with T004

**TDD Evidence:**

- Parent native RED: 203 tests, 40 assertion failures, zero errors.
- GREEN/REFACTOR: not run during this step.

**Test command:**

```text
python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py
```

**Files modified:** No test changes during this step.

**Test SHA256:** `f9f7cffdad482fae35776a1015dd590720a60c7b129ae17553af1bfea829ecfa`

**Errors:** None.

**Deviations/Edge cases/Surprises:** Test bytes remain unchanged; parent GREEN capture is pending.



#### T004: original source_applied_green_ready result

## Task Result: T004

**Status:** unfinished — SOURCE_APPLIED_GREEN_READY
**TDD unit:** A1a, shared evidence above

**TDD Evidence:** Approved runtime/schema portions applied after native RED. No tests executed.

**Test command:** Same registered command above.

**Files modified and actual SHA256:**

- `pr_emission.py`: `895541f066ab6791d19de143bfa35f8ba8bb7205d2810e84b27c1d5a0d87793b`
- `pr-packet.schema.json`: `30757cc25dde8b04314def2ff07dc4e5154289babf68d8738d7febcff4573d8b`

**Errors:** None.

**Deviations/Edge cases/Surprises:** Fresh native binding passed `resolved/same`. Patch, test and source base hashes matched before writing; resulting sources exactly match the approved candidate. No unrelated edits, bookkeeping, generators or commits.
#### T003: original refactor_ready result

## Task Result: T003

**Status:** unfinished — REFACTOR_READY
**TDD unit:** A1a, shared with T004

**TDD Evidence:**

- Tests written: six original A1a methods plus four regression methods.
- Parent native RED: 203 tests, 40 assertion failures.
- Parent native GREEN: 203/203 passed, exit 0.
- REFACTOR: read-only inspection complete; justified no-op. Separate native proof pending.

**Test command:**

```text
python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py
```

**Files modified:** None during inspection; mutation-helper test retains its approved hash.

**Errors:** None.

**Deviations/Edge cases/Surprises:** Four additive regression methods remain registered. No tests executed during this step.



#### T004: original refactor_ready result

## Task Result: T004

**Status:** unfinished — REFACTOR_READY
**TDD unit:** A1a, shared evidence above

**TDD Evidence:** Approved runtime/schema inspected without changes. Python syntax, schema JSON and scoped `git diff --check` passed.

**Test command:** Same registered command above.

**Files modified:** None during inspection.

**Errors:** None.

**Deviations/Edge cases/Surprises:** All three files still match the approved candidate hashes. The inline scan preserves host fence semantics without adding a helper layer; separator validation matches the portable schema. No necessary cleanup found. Native refactor proof and parent-owned closure gates remain pending.
#### T003: original completed-behavior result

## Task Result: T003

**Status:** completed — authored behavior and TDD; parent journal acceptance pending
**TDD unit:** A1a, shared with T004

**TDD Evidence:**

- Tests written: six initial methods plus four regression methods.
- Parent native RED: 203 tests, 40 assertion failures.
- Parent native GREEN: 203/203 passed, exit 0.
- Parent native REFACTOR: 203/203 passed, exit 0.
- Genuine ordered evidence: [parent observations](private HRNS-015 audit artifact).

**Test command:**

```text
python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py
```

**Files modified:**

- `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`

**Errors:** No remaining behavioral failures. Parent journal acceptance remains blocked by unfinished-report RED reuse handling.

**Deviations/Edge cases/Surprises:** Original tests and failed-attempt history preserved. No task checkbox completion claimed.



#### T004: original completed-behavior result

## Task Result: T004

**Status:** completed — authored behavior and TDD; parent qualification pending
**TDD unit:** A1a, shared evidence above

**TDD Evidence:** Native RED→GREEN→REFACTOR verified by parent. Ruff passed; mypy passed across 50 files. Release/reference generation, reference check and docs quality passed. Independent review reported no A1a defects.

**Test command:** Same registered command above.

**Files modified:**

- `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`
- `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`
- `speckit-pro/skills/speckit-autopilot/SKILL.md`
- `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`

**Errors:** No remaining behavioral defects. Native journal acceptance, checkpoint and PR-emission qualification remain unresolved.

**Deviations/Edge cases/Surprises:** Notes remain protected in A1a; the fourth editable field belongs to A1b. Drafts retain zero editable fields. No whole-feature or Post completion claimed; no new edits performed.

Parent native completion record returned exit 2: `only unchanged completed task observations may be carried forward`. The genuine RED event already appears in an unfinished report; no event IDs, reports, task checkboxes or journal history were rewritten. T001/T002 remain the only completed tasks. Current source checkpoint and PR emission remain pending.

Ripwire working-tree quality delta returned exit 2 (runtime complexity/length and bookkeeping growth); impact check returned exit 4 with eight candidate test files and four untested symbols. These structural diagnostics are retained, not reported as passing checks. The 203-test behavioral proof remains valid. Full suite and final artifact check remain pending.


### A1a 2.38.1 completion reconciliation

The native routing-epoch2 journal accepted T003 and T004 as complete under request `hrns015-a1a-completed-behavior-record-2381`, citing the already retained RED, GREEN and refactor evidence. The prior input error and source test history remain intact. The operator declined a Tasks re-plan. T001–T004 are journal-complete; A1a actual path/LOC accounting and its marker checkpoint remain pending before T005. The first quick-suite run passed 9,456/9,458 checks and exposed two privacy-scan failures; the notes' local paths were redacted, and a narrow scanner fix for this tracked public spec worktree passed the focused privacy test 12/12. The subsequent main merge superseded it with the repository's general worktree-name fix, which retains user, home and Git identity scanning; merged-tree verification is pending. Full quick-suite rerun passed 9,459/9,459, with toolchain preflight passing.

A1a marker checkpoint (2026-09-28T15:10:30Z): post-merge source `5a89c0b706d905760157e1b6d2f7579039c1ee26` passed the quick suite (10,106/10,106), six CI layers, full docs validation (88 smoke, 4 gallery), artifact check, Ruff, mypy (54 files), host parity, and independent critical/high review. Source delta 21 paths, 20 budget-counted, 2 production, 357 authored non-process changed lines. T003/T004 are complete in the original routing-epoch2 journal. Evidence: `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/checkpoints/us1-part1.json` and `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/verification/us1-part1.json`. Exact emitted PR base/head diff and LOC are still required.

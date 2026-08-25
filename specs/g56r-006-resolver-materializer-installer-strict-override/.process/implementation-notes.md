# Implementation Notes: G56R-006

### T001

**Deviations/Edge cases/Surprises:** None

### T002

**Deviations/Edge cases/Surprises:** None

### T003

**Deviations/Edge cases/Surprises:** None

### T004

**Deviations/Edge cases/Surprises:** None

### T005

**Deviations/Edge cases/Surprises:** Baseline static installer validation passed 53/53 tests before route-aware changes.

### T006

**Deviations/Edge cases/Surprises:** Two bounded implementation-executor attempts returned no task result and made no file changes, so the parent authored the deterministic corpus directly. JSON validation and `git diff --check` passed.

### T007

**Deviations/Edge cases/Surprises:** First executor attempt added the planned RED tests but returned before running them, so RED proof and task completion remained pending for a resumed attempt.

### T007

**Deviations/Edge cases/Surprises:** RED produced 10 missing-function errors and one ignored-manifest failure as intended. One test initially recomputed the intentionally bad manifest ID and was corrected before GREEN so the mismatch remained exercised.

### T008

**Deviations/Edge cases/Surprises:** Valid manifests are loaded and validated only; route resolution and routing evidence remain intentionally deferred to later task pairs. Focused validation passed 58/58 and `git diff --check` passed.

### T009

**Deviations/Edge cases/Surprises:** RED produced the three intended adapter-boundary failures: missing capture function, absent route-aware routing block, and an unpatchable static-mode guard.

### T010

**Deviations/Edge cases/Surprises:** One intermediate GREEN missed normalization when a patched adapter returned a raw fixture snapshot; normalization moved to the call site. Focused validation passed 61/61 and static mode still skips capture and omits routing.

### T011

**Deviations/Edge cases/Surprises:** None. Parent safety-net validation passed 61/61.

### T012

**Deviations/Edge cases/Surprises:** RED produced two intended errors because the prior materializer rejected selected route values that differed from source TOML.

### T013

**Deviations/Edge cases/Surprises:** Generated trust metadata refresh is deferred to T041. The executor narrowed one current-source digest assertion to avoid requiring stale generated metadata during this task; parent review will verify that this does not weaken the final consistency gate. Focused tests passed 10/10.

### T014

**Deviations/Edge cases/Surprises:** RED passed 61/63, with both intended errors caused by missing `routing.required_agents` evidence.

### T015

**Deviations/Edge cases/Surprises:** The optional helper source lacks `model_reasoning_effort`; installer-side proof rendering supplies only that selected route field while preserving non-route fields. Focused installer validation passed 63/63 and static mode still omits routing.

### T016

**Deviations/Edge cases/Surprises:** RED passed 63/65; both intended failures were route-aware apply evidence mismatches for missing/stale fake-home destinations.

### T017

**Deviations/Edge cases/Surprises:** None. Route-aware apply now plans all required route-rendered bytes before mutation, verifies exact destination bytes, refreshes recovery evidence, and proves bundled-source immutability. Focused validation passed 65/65.

### T018

**Deviations/Edge cases/Surprises:** None. Parent US1 safety-net validation passed materializer 10/10 and installer 65/65.

### T019

**Deviations/Edge cases/Surprises:** RED passed 65/67; strict mode was intentionally ignored by the pre-T020 implementation in both new cases.

### T020

**Deviations/Edge cases/Surprises:** Helper strict override remains intentionally deferred. Required strict override now evaluates exactly one tuple for each of all 12 agents, suppresses fallback, and fails before mutation. Focused validation passed 67/67.

### T021

**Deviations/Edge cases/Surprises:** RED passed 67/70. The helper-compatible fixture had to make the required roster compatible with the same override model so the required strict gate did not correctly fail first.

### T022

**Deviations/Edge cases/Surprises:** Managed-helper ownership/removal remains deferred to US3. Helper strict evidence, validated no-helper continuation, and unresolved-helper pre-mutation failure are GREEN at 70/70.

### T023

**Deviations/Edge cases/Surprises:** None. Parent US2 safety-net validation passed 70/70.

### T024

**Deviations/Edge cases/Surprises:** RED passed 70/72; both intended errors were missing omitted-helper evidence while the required roster remained resolvable.

### T025

**Deviations/Edge cases/Surprises:** Helper removal and ownership proof remain deferred. An absent helper now records validated no-helper continuation and a not-required ownership proof; focused validation passed 72/72.

### T026

**Deviations/Edge cases/Surprises:** RED passed 72/74; both managed-helper cases still reported omitted instead of removed as intended.

### T027

**Deviations/Edge cases/Surprises:** The known-digest case intentionally uses exact route-rendered helper bytes, not raw source bytes. Post-review hardening removed caller-asserted provenance as an ownership authority; exact trusted rendered bytes now provide the removal path. Focused validation originally passed 74/74.

### T028

**Deviations/Edge cases/Surprises:** One table-driven test produced five intended preservation failures, summarized as 70/75, because all unproven helper states still reported omitted.

### T029

**Deviations/Edge cases/Surprises:** Preservation is proven through fake-home apply. Manual remediation is bounded to one helper-level action, and filename/location/TOML validity/equivalence never widens ownership. Focused validation passed 75/75.

### T030

**Deviations/Edge cases/Surprises:** None. Parent US3 safety-net validation passed 75/75.

### T031

**Deviations/Edge cases/Surprises:** RED passed 75/76; the only failure was the required miss still reporting planned rather than blocked mutation status.

### T032

**Deviations/Edge cases/Surprises:** Required misses now block before mutation and emit explicit no-mutation recovery fields. Probe and rollback behavior remains deferred. Focused validation passed 76/76.

### T033

**Deviations/Edge cases/Surprises:** Two table-driven tests produced four intended failures, summarized as 74/78, because probe evidence was absent and native-unavailable routes still used plain unavailable rejection.

### T034

**Deviations/Edge cases/Surprises:** Probe execution is deterministic through test overrides. When native discovery is unavailable, raw available routes are ignored; only manifest-admitted probe child evidence can establish availability. Focused validation passed 78/78.

### T035

**Deviations/Edge cases/Surprises:** RED passed 78/79; route-aware recovery still reported rollback not required instead of restored after the injected write failure.

### T036

**Deviations/Edge cases/Surprises:** Prior state is captured for the full plan before mutation. Failed route-aware apply now records staged/applied/failed/rolled-back/cleanup actions, matching state identities, restored bytes/modes, and failed verification. Focused validation passed 79/79.

### T037

**Deviations/Edge cases/Surprises:** RED passed 79/80; recovery used the generic partial-failure outcome rather than the required unrestored classification.

### T038

**Deviations/Edge cases/Surprises:** Rollback failure now reports unrestored/uncertain state, exact rollback errors and actions, bounded manual remediation, restart required, and failed verification. Focused validation passed 80/80.

### T039

**Deviations/Edge cases/Surprises:** None. Parent US4 safety-net validation passed 80/80.

### T040

**Deviations/Edge cases/Surprises:** One initial text check had a shell-quoting issue around Markdown backticks; it made no edits and was rerun successfully. Generated mirrors remain deferred to T041.

### T041

**Deviations/Edge cases/Surprises:** Before regeneration, the parent restored the exact materializer source-digest assertion that had been temporarily weakened during T013. Payload mirrors and runner trust metadata regenerated successfully.

### T042

**Deviations/Edge cases/Surprises:** None. The same authoritative refresh regenerated installed-cache mirrors and all proof fixtures; `git diff --check` passed.

### T043

**Deviations/Edge cases/Surprises:** None. Post-refresh exact-digest materializer validation passed 10/10.

### T044

**Deviations/Edge cases/Surprises:** None. Post-refresh installer validation passed 80/80.

### T045

**Deviations/Edge cases/Surprises:** None. Layer 4 passed 12309/12309 with toolchain preflight green.

### T046

**Deviations/Edge cases/Surprises:** None. Layer 5 passed 219/219 with toolchain preflight green.

### T047

**Deviations/Edge cases/Surprises:** None. Layer 1 passed 1511/1511 after payload/trust regeneration.

### T048

**Deviations/Edge cases/Surprises:** The sandboxed install could not resolve registry.npmjs.org. The approved rerun completed from the frozen lockfile/cache with 464 packages and no lockfile mutation.

### T049

**Deviations/Edge cases/Surprises:** None. Reference generation completed for 7 pages.

### T050

**Deviations/Edge cases/Surprises:** None. Reference pages are current.

### T051

**Deviations/Edge cases/Surprises:** None. Full Python-authoritative suite passed 14039/14039: L1 1511, L4 12309, L5 219, with toolchain preflight green.

### T052

**Deviations/Edge cases/Surprises:** The authored implementation added roughly 4170 lines versus the 385-line planning estimate. Release-readiness evidence records this as over plan and routes the decision to mandatory post reviewability/code review rather than claiming it away.

### T053

**Deviations/Edge cases/Surprises:** None. Both the final spec and Design Concept name artifact-author, sweep-analyst, sweep-classifier, consensus-synthesizer, and gate-validator as downstream reconciliation inputs without assigning cohorts.

## Post-Implementation Review Remediation

- Rejected caller-supplied `managed_helper_provenance`; arbitrary bytes with self-asserted fields are preserved, while exact bytes rendered from the trusted current helper source and manifest remain removable.
- Replaced the installer-local renderer and proof identity with calls to the canonical `agent_materialization.py` authority. The canonical materializer now inserts an explicit effort when the original optional-helper source omits that route field.
- Captured file device/inode identity in addition to bytes and mode. Apply revalidates each target before mutation and immediately before replacement/removal; rollback revalidates the installer-written state and refuses to overwrite subsequent external edits.
- Added regression coverage for forged provenance, canonical optional-field insertion, concurrent edits before writes, and concurrent edits before rollback. Post-refresh focused validation passed materializer 11/11 and installer 82/82.
- The post-remediation repository suite passed 14041/14041: L1 1511, L4 12311, and L5 219.
- First independent re-review cleared forged provenance and canonical materializer duplication, then reproduced a return-to-recapture rollback race and found unchecked required-policy non-route contract digests.
- Second remediation makes atomic writes return their captured installed state directly, so rollback never trusts a later path recapture. It also rejects invalid or mismatched non-route contract digests against canonical source materialization. Focused validation remained 11/11 and 82/82; the full suite again passed 14041/14041.
- Second re-review cleared every prior finding and found one final schema bypass: a string-valued `required_capabilities` field skipped compatibility checks. Third remediation closes required-policy objects exactly, validates policy identity, and requires duplicate-free non-empty string capability arrays. Focused tests remained 11/11 and 82/82; the full suite again passed 14041/14041.
- Third re-review cleared all six prior findings and found a truthy-string `no_helper.allowed` bypass. Fourth remediation closes the no-helper record, requires a strict boolean authorization and non-empty reason, and validates adjacent optional-policy identity. Focused tests passed 11/11 and 83/83; the full suite passed 14042/14042.
- Fourth re-review cleared all eight prior findings and exposed two remaining evidence contracts: partial bounded-probe declarations and over-reported rollback/cleanup activity. Fifth remediation closes and binds the documented probe schema, records the exact failed write or removal, reports only applied actions successfully rolled back, and records real cleanup outcomes. Focused tests passed 11/11 and 86/86; the full suite passed 14045/14045.
- Fifth re-review cleared those probe/recovery issues and found three deeper boundaries: a final compare-to-mutate race, route IDs reused for inconsistent tuples, and post-copy verification failures without failed-action evidence. Sixth remediation moves existing targets aside before validation and uses exclusive no-clobber links for install/restore, preserves and reports multi-writer conflicts, rejects inconsistent route-ID tuples, and records verification mismatches as a failed action. Focused tests passed 11/11 and 92/92; the full suite passed 14051/14051.
- Sixth re-review cleared those three boundaries and found that no-clobber collision cleanup could discard the moved prior entry or report success while a concurrent target remained. Seventh remediation retains both entries on collision, reports every preserved path with bounded remediation, and makes temporary-file and backup cleanup failures explicit. Focused installer validation passed 94/94; the pre-merge full suite passed 14053/14053, and the regenerated current-baseline suite passed 14066/14066.
- Seventh re-review cleared the earlier policy, provenance, probe, recovery, and after-move collision findings, then reproduced final backup-cleanup races in write, removal, and rollback restore plus stale evidence after a successful temp-cleanup retry. Eighth remediation recaptures state after destructive cleanup, recreates captured prior bytes and mode under a fresh exclusive conflict path when needed, and reports only paths that remain after cleanup. Focused installer validation passed 98/98; the full suite passed 14070/14070.
- Eighth re-review confirmed direct cleanup-window detection but found rollback preserving installer bytes instead of original pre-batch bytes, dropped nested conflict paths, an unanchored recovery-copy destination, relinquished backup placeholders, and incomplete copies mislabeled as valid. Ninth remediation propagates the original rollback state and structured paths, anchors exclusive recovery copies to the captured directory descriptor, keeps backup placeholders owned through replacement, and separates `recovery_copy_failed` evidence. Focused installer validation passed 102/102; the full suite passed 14074/14074.
- Ninth re-review confirmed rollback composition and pre-call destination checks but found path-based restore, backup-placeholder takeover, post-open moved-directory evidence, phantom pre-create paths, and masking descriptor-close failures. Tenth remediation uses Darwin/Linux native atomic no-replace rename through a verified directory descriptor with no clobbering fallback, anchors restore state/link/unlink operations, revalidates evidence paths, and categorizes creation/close failures after independently attempting every close. Focused installer validation passed 107/107; the full suite passed 14079/14079.

### Post: Review Remediation — Anchored Backend

**Deviations/Edge cases/Surprises:** The exact-head attack review proved that per-helper anchors still reopened mutable paths. The remediation therefore replaces that helper-level design with one long-lived `AnchoredAgentDir` backend across the mutation batch. Ten new regression tests produced a real RED result of 109/117, then GREEN and REFACTOR passed 117/117; materialization passed 11/11 and the canonical materializer passed 17/17. The requested integration-test path did not exist, so the current unit-level materialization entrypoint was used.

### Post: Review Remediation — Windows Anchored Backend

**Deviations/Edge cases/Surprises:** The first anchored implementation failed closed on every Windows apply, which would regress the cross-platform installer contract. Six mocked Win32 contract tests produced a real RED result of 116/122. The follow-up adds a stdlib `ctypes` backend that holds a `CreateFileW` directory handle without `FILE_SHARE_DELETE`, uses `SetFileInformationByHandle(FileRenameInfo)` with `ReplaceIfExists=false`, maps Win32 errors, and closes handles without masking mutation state. GREEN and REFACTOR passed 122/122; materialization remained 11/11 and the canonical materializer 17/17.

### Post: Review Remediation — Owned Cleanup and Win32 Handle Evidence

**Deviations/Edge cases/Surprises:** Independent exact-head review found five remaining concurrency and Win32 contract defects: the Win64 rename filename offset used structure size rather than the native field offset, opened directory handles were not identity-checked, recovery copies reopened share-denied paths, cleanup could unlink a concurrent takeover, and Windows close/directory cleanup evidence was incomplete. Twelve deterministic tests established RED at 118/130, and a final close-evidence case established RED at 130/131. The remediation now uses the native 20-byte rename offset, canonical handle-derived directory identity, already-open exclusive handles for recovery verification, installer-owned state checks before destructive cleanup, identity-safe destination cleanup, and explicit close-handle evidence. GREEN and REFACTOR passed 131/131; materialization remained 11/11 and the canonical materializer 17/17. Native Windows execution remains outside this macOS worktree, so the Win32 contract is verified through mocked API behavior.

### Post: Review Remediation — Final-Instruction Cleanup Safety

**Deviations/Edge cases/Surprises:** The next exact-head review reproduced takeover races at the final pathname unlink and directory removal instructions, found dropped mixed preservation/cleanup evidence, and showed that Windows recovery copies did not retain read-only mode. Five deterministic cases established RED at 130/135. The remediation moves installer-owned entries away from public names before destructive cleanup, preserves anything concurrently recreated at those names, uses move-then-identity-check directory cleanup after the Windows batch anchor closes, propagates cleanup errors when no-clobber conflicts are wrapped, and applies/verifies Windows read-only attributes through the already-open recovery handle. GREEN and REFACTOR passed 135/135; materialization remained 11/11 and the canonical materializer 17/17.

### Post: Review Remediation — OS-Grounded Deletion Contract

**Deviations/Edge cases/Surprises:** Standards review confirmed that POSIX, Linux, macOS, and Python expose only name-based unlink operations, so no compare-before-unlink sequence can bind deletion to an already-open inode against a hostile same-user swap. Windows does expose handle-bound disposition deletion. Seven deterministic cases established RED at 135/142. The remediation therefore fails closed by preserving POSIX quarantine entries with cleanup/manual-remediation evidence, uses handle-bound Windows file disposition, uses no-replace directory quarantine with captured destination and parent identities, records successful-path directory-handle close failures, and clears/restores Windows read-only state through the open handle for rollback cleanup. GREEN and REFACTOR passed 142/142; materialization remained 11/11 and the canonical materializer 17/17.

### Post: Review Remediation — Native Disposition and Verified Mode State

**Deviations/Edge cases/Surprises:** Follow-up attack review found that POSIX still unlinked the private quarantine, Win32 disposition used a four-byte field for native one-byte `BOOLEAN`, read-only restoration could adopt a concurrently replaced pathname, and a Windows cleanup early return dropped close-handle errors. Four new deterministic cases plus eight corrected fail-closed POSIX expectations established RED at 138/146. The remediation now always preserves verified POSIX quarantine residue, validates the one-byte Win32 disposition ABI, applies Windows mode only after verifying the installer-owned handle state, and merges close failures before every cleanup return. GREEN and REFACTOR passed 146/146; materialization remained 11/11 and the canonical materializer 17/17.

### Post: Review Remediation — Structured Cleanup Evidence

**Deviations/Edge cases/Surprises:** The next exact-head review found raw pathname deletion in temp-creation error paths, silent routine POSIX residue, substring-based public/private conflict classification, and optional close-error collectors. Five deterministic cases established RED at 146/151. The remediation removes all pathname unlink/DeleteFile fallbacks, publishes temp files with native no-replace moves so their names are consumed, replaces string classification with structured public-conflict/private-preservation/cleanup-error provenance, and makes close errors mandatory result data at every caller. POSIX retained cleanup residue is now reported as partial failure with manual remediation, and rollback success is not claimed while residue keeps recovery incomplete. GREEN and REFACTOR passed 151/151; materialization remained 11/11 and the canonical materializer 17/17.

### Post: Review Remediation — No-Replace Quarantine and Mandatory Close Results

**Deviations/Edge cases/Surprises:** Exact-head review narrowed the remaining defects to replacing rename into the POSIX private quarantine and lower-level Windows callers that could still omit close evidence. Two deterministic cases established RED at 151/153. The remediation now uses native no-replace rename across directory descriptors for private quarantine collisions and makes every Windows handle close return or raise structured evidence so no caller can silently leak a handle. GREEN and REFACTOR passed 153/153; materialization remained 11/11 and the canonical materializer 17/17.

### Post: Review Remediation — Ownership-Aware Collision Evidence

**Deviations/Edge cases/Surprises:** Exact-head review found that collision evidence labeled a concurrent private victim as installer-owned cleanup residue and that `target_is_safe` could still reduce a Windows close failure to a generic unsafe result. Two deterministic cases established RED at 152/154. The remediation now records installer-owned public residue separately from unknown/private concurrent data, generates manual guidance that explicitly preserves the unknown data, and raises or attaches Windows close evidence without masking a primary error. GREEN and REFACTOR passed 154/154; materialization remained 11/11 and the canonical materializer 17/17.

### Post: Review Remediation — Uniform Cleanup Provenance

**Deviations/Edge cases/Surprises:** Exact-head review found that FileNotFound, generic move failures, and post-move mismatch still inferred private-location ownership. Three deterministic cases established RED at 154/157. The remediation independently classifies public and private leaves, emits `preserved_cleanup_entry` only for exact expected installer state, and treats unverified private leaves as `preserved_concurrent_file` with safe manual guidance. GREEN and REFACTOR passed 157/157; materialization remained 11/11 and the canonical materializer 17/17.

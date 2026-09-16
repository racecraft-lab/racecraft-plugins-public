# Final frozen Layer 4 remainder audit

## Result

This report covers the exact final **262 frozen loaded families** left after the seven earlier Layer 4 audit ledgers (1,153 families) and the disjoint functional worker selection (200 families): **1,153 + 200 + 262 = 1,615**.

- Deep body review completed from exact frozen source, a matching current symbol, or an exact old-to-new patch: **261**
- Behavior-evolved replacement reviewed with exact-frozen-snapshot provenance uncertainty: **1**
- Explicitly unreviewed: **0**
- Dispositions: **250 keep, 10 merge, 2 replace, 0 unreviewed**
- Current new/renamed native methods recorded outside the frozen scope: **37**
- File overlap with the prior ledgers or functional selection: **0**

Loaded methods, runtime counted units, generated subtests, and static assertion sites remain separate measures. This report does not inflate coverage by adding them together.

## Important findings

1. `NativeEvalEntrypointTests.test_execute_is_a_clear_integration_guard` has an evidence-backed **replace** disposition: its exact recovered body and old-to-new patch show that the exit-3 integration-pending stub was explicitly replaced by `test_execute_returns_runtime_status_and_persists_report`. The adapter family's creation-to-rename patch chain supports a separate **replace** disposition: its successor removes the obsolete trigger-unsupported vector now that trigger is supported, retains the other four rejection/preservation vectors, and adds invalid interactive `resource_class` rejection. However, the recovered adapter body has five unittest assertion calls while the frozen inventory records six static assertion sites, and reconstructed creation-time file bytes do not match the frozen whole-file hash. The behavior evolution is reviewed, but the exact frozen adapter snapshot remains uncertain. Public evidence contains only recovered source and cryptographic hashes, not private session provenance.
2. The ten bookkeeping merge dispositions are now implemented as three loaded parameter matrices: `test_authority_pair_classification_matrix` (five vectors), `test_tracked_state_failure_matrix` (two vectors), and `test_isolated_state_invariant_failure_matrix` (three vectors). The file now has **49 loaded methods** and both the functional-worker run and root's independent run report **346/346 counted units**; the worker also detected **3/3 targeted faults**. All ten behavior vectors and their exact criteria remain; the seven-method reduction is maintenance consolidation, not removed execution workload. The remediation is independently verified.
3. The original configured-interpreter feedback-sweep-isolation run passed **111/112** counted units because its Codex launcher confinement family rejected that interpreter's group-writable executable mode. A separate full run under a protected Python **3.11.16** interpreter passed **112/112**, and root independently reproduced the same **112/112** result with that protected interpreter variant. This resolves and independently verifies the local interpreter prerequisite without changing host permissions, regenerating artifacts, or weakening the trust boundary; the original failed result remains recorded separately.
4. Five native files differ from the frozen file hashes. Their 79 matching frozen symbols were reviewed at the recorded current hashes; 37 current new/renamed methods are listed separately and are not counted as frozen coverage.
5. Native/provider-facing tests in this slice use fixtures, mocks, local subprocesses, and temporary files. They are not live provider, Docker, remote Git, or GitHub-mutation proof.

## Focused verification

All nine selected executables were run at the audited hashes. Eight passed under the original configured interpreter; the original exception is the retained 111/112 launcher trust-chain result above. The same full feedback-isolation executable subsequently passed 112/112 under the protected Python 3.11.16 interpreter variant. The other counted outputs were 343/343, 8/8, 257/257, 39/39, 80/80, 22/22, and 30/30; the entrypoint runner emitted `OK` without a counted-unit total.

Eight isolated, non-mutating fault injections were also run. All eight were detected (25 failed assertion/subtest units in total), covering bookkeeping, permission guidance, stage argument rejection, issuer-token scanning, trace parsing, grading, entrypoint validation, and immutable store reservation. Synthetic credential-like fixture literals are deliberately omitted from this report.

## Source freeze and refresh rule

Each file record stores both the frozen inventory hash and the exact current hash used for review. Stable files match the frozen source. Drifted native files are marked `needs_refresh_if_source_changes_after_audited_hash`; this report does not chase concurrent edits indefinitely. The JSON ledger contains every current body hash, source line, assertion preview, fault/state preview, simulation limit, disposition, and replacement obligation.

## Repository-wide caveat

The report integrity and whitespace checks passed, and the post-recovery privacy gate passed **10/10**. Ripwire's whole-worktree quality comparison is not green: it reports 25 pre-existing-symbol major regressions against Git HEAD in the shared concurrent diff. Its whole-worktree test gate also reports 144 suggested tests and 85 untested impacted symbols. Those results are not attributed to these two report-only files, and this bounded read-only lane did not run the prohibited broad suite.

## Scope boundary

This assigns a disposition to every family in the final remainder of the **frozen** Layer 4 baseline, but it does not claim exact frozen-body review for the one adapter family with the provenance/count discrepancy above, and it is not an audit of post-freeze additions. The 37 additions recorded at the audit snapshot remain a separate post-baseline set. No source, product library, generated artifact, provider, Docker, or remote-service mutation was performed by this audit lane.

# Research: Arm The Accidentally-Advisory State Bookkeeping Checks

## Decision: Use `status-evidence`

**Rationale**: The autopilot already invokes `validate-autopilot-phase-coverage.py` with `--rule status-evidence` at phase-transition checkpoints. Adding the three current-run state invariant keys to that existing rule is the smallest behavior change that makes the already-reported diagnostics blocking for the invocation operators actually run.

**Alternatives considered**:
- Create a new state rule. Rejected because it would require changing invocations and parity surfaces beyond ART-017.
- Group every `validate_state` result. Rejected because legacy structural coverage debt must remain visible but nonblocking under `status-evidence`.

## Decision: Keep rule membership and intent verdicts atomic

**Rationale**: `PROBLEM_KEY_INTENT` records whether each emitted key is gated or advisory. The existing consistency test compares `gated` verdicts to `RULE_PROBLEM_KEYS`, so rule membership and verdict changes must move together to avoid an intentionally inconsistent intermediate state.

**Alternatives considered**:
- Separate commits for rule membership and intent verdicts. Rejected because one commit would knowingly misdescribe runtime behavior.
- Derive verdicts from the rule map. Rejected because it broadens ART-017 into a classification-system refactor.

## Decision: Use one shared clean builder with three isolated mutations

**Rationale**: A single clean workflow/state fixture gives every negative control the same baseline. Each mutation can then prove exactly one ART-017 key gates independently while the other two new problem lists remain empty.

**Alternatives considered**:
- Fully separate fixtures. Rejected because they duplicate setup and make fixture drift harder to spot.
- One combined malformed state. Rejected because it cannot prove independent gating per key.

## Decision: Preserve report shape and problem-key names

**Rationale**: The validator already prints the complete JSON report and scopes only the exit code through `--rule`. ART-017 should change authority, not the consumer contract.

**Alternatives considered**:
- Add a new summary field. Rejected because it creates a new output contract outside the repair scope.
- Fail fast. Rejected because operators would lose the full diagnostic report.

## Decision: Cover tracked authority-matched adjacent workflow/state pairs

**Rationale**: ART-017 concerns current-run state invariants, so corpus evidence must cover real tracked workflow/state pairs. A valid pair requires both files to be tracked, in the same directory, with `autopilot-state.json.workflow_file` naming the workflow's repo-relative path exactly.

**Alternatives considered**:
- Directory adjacency alone. Rejected because a nearby state can name another workflow.
- Synthetic state generation for missing states. Rejected because it would not prove the stored corpus.
- Full suite only. Rejected because it would not provide explicit pair-level evidence.

## Decision: Narrow the authored autopilot paragraph only

**Rationale**: The authored skill already contains the explanation of scoped status-evidence behavior. Updating that source paragraph keeps one explanation source, while generated Claude Code and Codex payload, installed-cache, and reference copies can be refreshed through tooling.

**Alternatives considered**:
- Hand-edit every generated mirror and reference. Rejected because generated surfaces are not sources of truth.
- Code and tests only. Rejected because the existing prose would still describe the new blocking behavior incorrectly.

## Decision: Require same-source parity for both supported distributions

**Rationale**: Claude Code and Codex consume separate generated install payloads, but both are derived from the same authored validator and skill guidance. Final release evidence must rebuild and check both payloads and both installed-cache fixture trees so one client cannot remain stale while the other passes.

**Alternatives considered**:
- Verify only the Codex mirror. Rejected because the shared runtime repair also ships to Claude Code.
- Treat a green full suite as implicit distribution evidence. Rejected because explicit release-artifact consistency is the authoritative stale-output check.

## Decision: Rebase then regenerate before ready or merge

**Rationale**: ART-017 authored files are independent from ART-008 during development, but both can touch shared generated payload and documentation surfaces. Final integration must use latest `main`, regenerate both supported distribution payloads and fixtures, run the independent artifact check and docs reference generation/checking, and pass the full suite.

**Alternatives considered**:
- Stack ART-017 on ART-008. Rejected because authored-file independence does not require a branch dependency.
- Merge without regeneration after ART-008. Rejected because generated artifacts are a function of the final source tree.

## Open Questions

None.

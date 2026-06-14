# Quickstart: Optional gh-stack stack manager integration

## Prerequisites

- Run from repository root.
- `jq`, `git`, and `gh` are available.
- `gh stack` is optional. Tests must use fake `gh` fixtures for supported and unsupported cases rather than requiring live GitHub stack support.

## Validation Scenarios

### 1. Supported detection

Use a Layer 4 fake `gh` fixture where:

- `gh extension list` includes `github/gh-stack v0.0.5`
- `gh stack --version` returns `0.0.5`
- `gh stack view --json` returns parseable stack topology matching the PRS/marker plan

Expected:

- `detect-stack-manager.sh` selects `gh-stack`
- `gh_stack.supported=true`
- `gh_stack.reason` explains the passing support proof
- `fallback_allowed=true` before mutation
- command plan includes a mutating `gh stack link` or restack operation as the mutation boundary

### 2. Fallback detection cases

Run matrix fixtures for:

- missing `gh stack`
- unsupported or unparsable version
- private-preview or repository-support failure
- ambiguous `view --json`
- read-only proof failure
- topology mismatch

Expected:

- selected manager is `explicit-gh`
- `gh_stack.supported=false`
- `gh_stack.reason` explains the failed support gate
- fallback reason is specific
- no mutating `gh stack` argv appears

### 3. Supported emission

Use marker-aware emission fixtures with validated PRSG-012 packets and PRSG-013 marker checkpoints.

Expected:

- all packet validations pass before mutation
- explicit `gh pr create/edit --base --head --title --body-file` reconciles PRs first
- `gh stack link --base <base> <pr-number>...` runs only after PR numbers are known
- evidence preserves marker order, branch names, base topology, PR packet paths, and stack-manager decision
- invalid or stale PRSG-012 packets block before any explicit `gh` create/edit, `gh stack` link/sync, or manager switch; they are not treated as a stack-manager fallback cause

### 4. Fallback emission

Use the same PRS/marker fixture with `gh-stack` unsupported.

Expected:

- after packet validation passes, the explicit `gh pr create/edit --base --head --body-file` path is used
- command log records fallback reason
- output state references the stack-manager decision evidence

### 5. Failure classification and partial mutation block

Use fake `gh` fixtures for each failure class:

- clean pre-mutation failure before a topology-changing `gh stack` argv is attempted
- successful mutating command with expected topology evidence
- failed mutating `gh stack link` with observed partial topology changes
- failed mutating `gh stack sync` with ambiguous or unparseable post-failure evidence
- failed mutating `gh stack rebase --upstack <branch>` with ambiguous or unparseable post-failure evidence
- same-manager no-change reconciliation where topology, PR identity, base/head refs, head SHA, and packet identity prove the failed argv left no topology changes

Expected:

- clean pre-mutation failures select explicit `gh` fallback with `fallback_allowed=true` and no mutating `gh stack` argv
- successful mutating commands record `side_effect_class=planned_mutation`
- status is blocked
- `fallback_allowed=false`
- failed mutating commands with observed side effects record `side_effect_class=partial_mutation`
- failed mutating commands with unproven side effects record `side_effect_class=partial_mutation_unknown`
- recoverable block state includes failed action/argv/exit status, side-effect class, stdout/stderr tails, mutation boundary, pre-mutation topology, observed topology when available, prior successful PRs, resume boundary, retry policy, and evidence paths
- decision, proof, command, recovery, and workflow evidence paths are repo-relative `.process` paths with stable operation identities, not absolute paths or timestamped temp files
- no fallback `gh pr edit` or duplicate create command runs after the ambiguous mutation
- same-manager reconciliation is the only automated path that may resume after a mutating `gh stack` failure, and only after proving no topology change occurred

### 6. Duplicate retry reconciliation

Use a fixture where some PRs already exist and match slice ID, head branch, base branch, PR number/URL, head SHA, and packet hash.

Expected:

- existing PRs are reconciled
- no duplicate PRs are created
- stack linking uses reconciled PR numbers
- mismatched PR identity, head SHA, packet hash, or base/head topology blocks before any create, sync, or manager switch

### 7. Supported restack

Use a fake `gh` fixture where `view --json` matches the current PRS order and v0.0.5 help supports `rebase --upstack`.

Expected:

- restack dry run records `gh-stack` decision and command plan
- apply mode runs `gh stack rebase --upstack <first-remaining-branch>` and the proven sync/push step
- evidence records selected manager, command plan, topology, and recovery policy
- any failed or ambiguous mutating rebase/sync step after the boundary emits blocked recovery evidence with `fallback_allowed=false` instead of switching to `restack.sh --apply`

### 8. Fallback restack

Use unsupported or incompatible `gh-stack` fixtures.

Expected:

- `restack.sh --apply` retains explicit `gh pr edit --base` retargeting
- fallback reason is recorded before mutation
- existing restack output compatibility fields remain present

### 9. Layer 7 replay

Run the PRSG-014 replay fixture.

Expected:

- replay proves phase/consensus routing shape
- no `grill-me` invocation appears
- transcript contains operator-facing stack-manager evidence terms only
- no real `gh`, `gh stack`, network PR creation, or live transcript refresh is required

### 10. Layer 8 guidance parity

Run the PRSG-014 parity fixture.

Expected:

- Claude Code and Codex guidance both describe supported, fallback, and blocked stack-manager flows
- both surfaces reference shared scripts/contracts
- no Codex duplicate implementation is introduced

### 11. Blocked stack-manager resume

Use a fake `gh` fixture with an existing blocked recovery record, prior command evidence, a prior blocked workflow event, and current topology variants for:

- same-manager no-change reconciliation
- observed topology drift after the failed command
- stale packet identity
- missing recovery evidence path

Expected:

- resume first reloads the prior decision and recovery evidence from repo-relative `.process` paths
- resume revalidates current topology, PR identity, base/head refs, head SHA, and packet identity before any create, sync, restack, or manager switch
- same-manager no-change reconciliation may resume only when every preflight check matches the safe boundary
- topology drift, stale packet identity, or missing recovery evidence remains blocked with `fallback_allowed=false`
- the blocked workflow event is superseded by the same deterministic event id rather than duplicated
- no explicit-`gh` fallback or duplicate PR creation occurs after a blocked `gh-stack` mutation

### 12. Security injection guards

Use Layer 4 fake-CLI fixtures with:

- branch/base refs containing shell metacharacters, newlines, control characters, or option-looking operands such as `--help`
- PR body paths containing absolute paths, parent traversal, or non-Markdown targets
- stack-manager evidence paths containing parent traversal, absolute host paths, random temp segments, or rendered command strings
- display command text containing shell metacharacters that differs from the stored argv array
- fake CLI override attempts that point outside the test sandbox/fixture tree or provide a shell command string instead of a test-local executable/PATH shim

Expected:

- invalid branch/base refs, body paths, evidence paths, and fake CLI controls block before command capture or mutation
- no `commands.candidate.json`, stack-manager decision, or command execution evidence is persisted for rejected inputs except bounded validation error evidence
- persisted accepted command plans record canonical `["gh", "stack", ...]`, `["gh", "pr", ...]`, `["git", ...]`, or repo-local validator argv shapes
- display command text is never parsed back into argv or executed
- no test fixture requires real `gh`, real `gh stack`, network PR creation, or a shell string executor

## Final Verification Bundle

Use focused commands during implementation:

```bash
bash tests/speckit-pro/run-all.sh --layer 1
bash tests/speckit-pro/run-all.sh --layer 4
bash tests/speckit-pro/run-all.sh --integration
bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run
```

Use the repository default proof before PR handoff:

```bash
bash tests/speckit-pro/run-all.sh
```

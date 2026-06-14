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
- fallback reason is specific
- no mutating `gh stack` argv appears

### 3. Supported emission

Use marker-aware emission fixtures with validated PRSG-012 packets and PRSG-013 marker checkpoints.

Expected:

- all packet validations pass before mutation
- explicit `gh pr create/edit --base --head --title --body-file` reconciles PRs first
- `gh stack link --base <base> <pr-number>...` runs only after PR numbers are known
- evidence preserves marker order, branch names, base topology, PR packet paths, and stack-manager decision

### 4. Fallback emission

Use the same PRS/marker fixture with `gh-stack` unsupported.

Expected:

- explicit `gh pr create/edit --base --head --body-file` path is used
- command log records fallback reason
- output state references the stack-manager decision evidence

### 5. Partial mutation block

Use a fake `gh` fixture where the first mutating `gh stack link` or `gh stack sync` command returns ambiguous failure after possible side effects.

Expected:

- status is blocked
- `fallback_allowed=false`
- recoverable block state includes failed argv, stdout/stderr tails, pre-mutation topology, observed topology when available, prior successful PRs, and resume boundary
- no fallback `gh pr edit` or duplicate create command runs after the ambiguous mutation

### 6. Duplicate retry reconciliation

Use a fixture where some PRs already exist and match slice ID, head branch, base branch, PR number/URL, head SHA, and packet hash.

Expected:

- existing PRs are reconciled
- no duplicate PRs are created
- stack linking uses reconciled PR numbers

### 7. Supported restack

Use a fake `gh` fixture where `view --json` matches the current PRS order and v0.0.5 help supports `rebase --upstack`.

Expected:

- restack dry run records `gh-stack` decision and command plan
- apply mode runs `gh stack rebase --upstack <first-remaining-branch>` and the proven sync/push step
- evidence records selected manager, command plan, topology, and recovery policy

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

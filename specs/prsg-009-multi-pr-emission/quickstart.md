# Quickstart: PRSG-009 multi-PR emission

## Prerequisites

- Run from the repository root.
- `git`, `gh`, and `jq` are on `PATH`.
- A PRSG-008 layer-plan output exists for the completed implementation.
- Full regression verification has completed once before emission.
- `gh-stack` is optional and is never required for PR creation.

## Validation Scenarios

### 1. Structural and parity validation

Command:

```bash
bash tests/speckit-pro/run-all.sh --layer 1
```

Expected result:
- Existing plugin structure remains valid.
- New scripts are executable and structurally visible.
- Claude/Codex mirrored autopilot references stay in parity.
- `.github/workflows/pr-checks.yml` is unchanged by PRSG-009.

### 2. Script unit validation

Command:

```bash
bash tests/speckit-pro/run-all.sh --layer 4
```

Expected result:
- `generate-pr-body.sh` still supports existing positional invocation.
- `generate-pr-body.sh --slice-packet <json-file>` renders slice review fields.
- Invalid `--slice-packet` input exits 2, writes a deterministic
  `generate-pr-body.sh: invalid slice packet:` stderr line, and leaves the
  target PR body absent or unchanged.
- `generate-spec-index.sh` renders PRS schema v1 and v2 rows.
- `multi-pr-emission.sh` stops before PR creation on failed scoped verification.
- `multi-pr-emission.sh` resumes without duplicating existing branches or PRs.
- `restack.sh` defaults to dry-run, emits JSON stdout, and uses distinct exit
  codes for success, conflicts, input errors, dirty worktree, and git/gh
  failures.

### 3. Default deterministic regression

Command:

```bash
bash tests/speckit-pro/run-all.sh
```

Expected result:
- Layers 1, 4, and 5 pass with zero failures.
- Full regression evidence can be referenced by slice packets.

### 4. Three-slice emission fixture

Fixture setup:
- Layer plan contains three ordered slices.
- Scoped verification commands are stubbed to succeed.
- `gh pr create` and `gh pr view` are stubbed to return deterministic PR data.

Expected result:
- Branches are planned as:
  - `prsg-009-multi-pr-emission/01-<slice-id>`
  - `prsg-009-multi-pr-emission/02-<slice-id>`
  - `prsg-009-multi-pr-emission/03-<slice-id>`
- Slice 1 targets the integration base.
- Slice 2 targets slice 1.
- Slice 3 targets slice 2.
- `.process/prs.json`, `SPEC-MOC.md`, workflow evidence, and
  `autopilot-state.json` are updated after each PR before the next slice starts.

### 5. Failed scoped verification fixture

Fixture setup:
- Layer plan contains at least two slices.
- Slice 1 verification succeeds.
- Slice 2 scoped verification fails.

Expected result:
- Slice 1 PR state is durable.
- Slice 2 PR is not opened.
- `multi_pr_emission.failed_slice` records slice identity, command, exit status,
  evidence path, stdout/stderr tail, head SHA, declared tests, and retry policy.
- Resume starts at the failed or next pending slice according to recorded state
  and does not recreate slice 1.

### 6. Restack dry-run fixture

Command shape:

```bash
speckit-pro/skills/speckit-autopilot/scripts/restack.sh \
  --state docs/ai/specs/.process/autopilot-state.json \
  --manifest specs/prsg-009-multi-pr-emission/.process/prs.json \
  --base main \
  --remote origin \
  --start-after prsg-009-multi-pr-emission/01-<slice-id>
```

Expected result:
- No mutation happens without `--apply`.
- JSON stdout lists the remaining branch operations in deterministic order.
- Diagnostics are written to stderr.
- Exit code/status mapping is `0=success`, `1=conflicts`, `2=input_error`,
  `3=dirty_worktree`, and `4=git_gh_failure`.
- Failure diagnostics use `restack.sh: <status>: <message>` with deterministic,
  plain stderr.
- A fresh `bash tests/speckit-pro/run-all.sh` is required after applied restack
  before final/base merge evidence is considered current.

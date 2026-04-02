# Data Model: PR Checks Workflow

**Feature Branch**: `002-pr-checks-workflow`
**Date**: 2026-04-01

## Entities

### Workflow File

**Type**: YAML configuration file
**Location**: `.github/workflows/pr-checks.yml`

| Field | Type | Description |
|-------|------|-------------|
| name | string | Workflow display name: `PR Checks` |
| on.pull_request.types | array | `[opened, reopened, synchronize, edited, ready_for_review]` |
| permissions | object | Top-level: `{}` (empty, no default permissions) |

### Job: detect

**Purpose**: Identify changed plugin directories from the PR diff.

| Output | Type | Description |
|--------|------|-------------|
| plugins | JSON string | Array of plugin directory names, e.g., `["speckit-pro"]` or `[]` |

**State Transitions**:
- Start -> Checkout (fetch-depth: 0)
- Checkout -> Diff (three-dot diff against merge base)
- Diff -> Filter (keep only dirs with `.claude-plugin/plugin.json`)
- Filter -> Output (JSON array of plugin names)

### Job: test

**Purpose**: Run test suite for each changed plugin directory.
**Depends on**: `detect` job
**Condition**: `needs.detect.outputs.plugins != '[]'`

| Input | Type | Source |
|-------|------|--------|
| matrix.plugin | string | `fromJSON(needs.detect.outputs.plugins)` |

**State Transitions**:
- Start -> Checkout (fetch-depth: 0)
- Checkout -> Validate test runner exists (`tests/run-all.sh`)
- Validate -> Execute tests (`bash tests/run-all.sh`)
- Execute -> Report (exit code propagates as job status)

### Job: validate-pr-title

**Purpose**: Validate PR title matches Conventional Commits format.
**Independent**: No dependencies on other jobs.

| Input | Type | Source |
|-------|------|--------|
| PR title | string | `github.event.pull_request.title` |

**Validation Rules**:
- Must match regex: `^(feat|fix|chore|docs|refactor|test)(\(.+\))?!?: .+$`
- Valid types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`
- Scope: optional, any non-empty string in parentheses
- Breaking change indicator: optional `!` before colon
- Description: required, any non-empty string after `: `

**State Transitions**:
- Start -> Read title from github context
- Read -> Regex match
- Match success -> Pass with confirmation message
- Match failure -> Fail with error message (pattern, valid types, example)

## Relationships

```text
Workflow
├── detect (job)
│   └── outputs.plugins → test (job, dynamic matrix)
├── test (job, conditional on detect output)
│   └── matrix.plugin → runs tests/run-all.sh per plugin
└── validate-pr-title (job, independent)
    └── reads github.event.pull_request.title
```

## Validation Rules

| Rule | Source | Implementation |
|------|--------|----------------|
| Plugin detection: `.claude-plugin/plugin.json` exists | Constitution Principle I, FR-002 | `test -f "$dir/.claude-plugin/plugin.json"` |
| Test runner exists | FR-012 | `test -f "$dir/tests/run-all.sh"` with failure on missing |
| PR title format | Constitution Principle V, FR-004 | Bash regex `[[ =~ ]]` |
| Non-draft PR | FR-001 | `if: github.event.pull_request.draft == false` |
| Pinned action versions | FR-008 | SHA-pinned `actions/checkout` |
| Minimal permissions | FR-009 | Top-level `permissions: {}`, job-level `contents: read` |

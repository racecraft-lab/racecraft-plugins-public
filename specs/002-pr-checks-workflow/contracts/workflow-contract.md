# Workflow Contract: PR Checks

**File**: `.github/workflows/pr-checks.yml`

## Trigger Contract

```yaml
on:
  pull_request:
    types: [opened, reopened, synchronize, edited, ready_for_review]
```

All jobs include: `if: github.event.pull_request.draft == false`

## Job Contract: detect

**Outputs**:

| Name | Type | Example |
|------|------|---------|
| `plugins` | JSON string (array) | `["speckit-pro"]` or `[]` |

**Behavior**:
- Checkout with `fetch-depth: 0`
- Three-dot diff: `git diff --name-only origin/${{ github.base_ref }}...HEAD`
- Extract unique top-level directories
- Filter to directories containing `.claude-plugin/plugin.json`
- Log detected plugins or "no plugins changed" message (FR-019)
- Output as JSON array

**Log Output** (FR-019):
- When plugins found: `Changed plugin directories: speckit-pro my-other-plugin`
- When no plugins found: `No plugin directories changed in this PR. Test job will be skipped.`

## Job Contract: test

**Display Name**: `test (${{ matrix.plugin }})` (FR-018 -- plugin name visible in Checks UI)

**Inputs**:

| Name | Type | Source |
|------|------|--------|
| `matrix.plugin` | string | `fromJSON(needs.detect.outputs.plugins)` |

**Condition**: `needs.detect.outputs.plugins != '[]'`

**Behavior**:
- Checkout with `fetch-depth: 0`
- Verify `${{ matrix.plugin }}/tests/run-all.sh` exists (fail if missing per FR-012)
- Execute `bash tests/run-all.sh` from plugin directory
- Exit code propagates as job status

**Exit Codes**:

| Code | Meaning | Error Output |
|------|---------|--------------|
| 0 | All tests passed | (test runner output) |
| 1 | Test failures detected | (test runner output -- already actionable) |
| 2 | Test runner (`tests/run-all.sh`) not found | `::error::` annotation + human-readable message with plugin name and expected path (FR-017) |

## Job Contract: validate-pr-title

**Inputs**:

| Name | Type | Source | Delivery |
|------|------|--------|----------|
| PR title | string | `${{ github.event.pull_request.title }}` | Via `env: TITLE:` (FR-013, script injection prevention) |

**Script Injection Prevention**: The PR title MUST be passed to the inline script via an intermediate environment variable (`env: TITLE: ${{ github.event.pull_request.title }}`), never by direct `${{ }}` interpolation in the script body. The `$TITLE` variable MUST be double-quoted in all uses. See [GitHub Docs - Script Injections](https://docs.github.com/en/actions/concepts/security/script-injections).

**Behavior**:
- Match title against regex: `^(feat|fix|chore|docs|refactor|test)(\(.+\))?!?: .+$`
- On match: exit 0 with success message
- On no match: exit 1 with error message containing:
  - Expected format pattern
  - Valid type prefixes list
  - At least one concrete example

**Error Output Format** (on failure):

```text
::error::PR title does not match Conventional Commits format. See job log for details.

ERROR: PR title does not match Conventional Commits format.

  Your title: "<actual PR title echoed here>"

Expected format: type(scope): description
  - type must be one of: feat, fix, chore, docs, refactor, test
  - scope is optional: type: description is also valid
  - breaking changes: add ! before the colon: type(scope)!: description

Examples:
  feat(speckit-pro): add new coaching command
  fix: resolve session timeout
  docs: update README
  feat!: breaking API change
```

**Success Output Format** (on pass):

```text
PR title is valid: <actual PR title echoed here>
```

## Permissions Contract

```yaml
# Top-level: no default permissions
permissions: {}

# detect job
permissions:
  contents: read

# test job
permissions:
  contents: read

# validate-pr-title job
permissions: {}  # No permissions needed
```

## Action Versions Contract

All actions MUST be pinned to commit SHAs with version comments:

```yaml
- uses: actions/checkout@<SHA>  # vX.Y.Z
```

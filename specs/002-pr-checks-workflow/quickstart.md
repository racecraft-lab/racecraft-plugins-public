# Quickstart: PR Checks Workflow

**Feature Branch**: `002-pr-checks-workflow`

## What This Feature Does

Creates a GitHub Actions workflow (`.github/workflows/pr-checks.yml`) that validates every pull request with:
1. **Scoped plugin tests** -- detects which plugins changed and runs only their test suites
2. **PR title validation** -- enforces Conventional Commits format for release-please compatibility

## Implementation Summary

### Single File Deliverable

```text
.github/workflows/pr-checks.yml
```

### Three Jobs

| Job | Purpose | Depends On |
|-----|---------|------------|
| `detect` | Find changed plugin directories via git diff | None |
| `test` | Run `tests/run-all.sh` per changed plugin (dynamic matrix) | `detect` |
| `validate-pr-title` | Check PR title matches conventional commits regex | None (independent) |

### Key Patterns

**Plugin detection**: Three-dot diff -> extract top-level dirs -> filter by `.claude-plugin/plugin.json` presence

**Dynamic matrix**: `detect` outputs JSON array -> `test` uses `fromJSON()` for parallel jobs per plugin

**Empty matrix guard**: `if: needs.detect.outputs.plugins != '[]'` skips test job when no plugins changed

**Title regex**: `^(feat|fix|chore|docs|refactor|test)(\(.+\))?!?: .+$`

## Testing the Workflow

After implementation, verify with these scenarios:

1. **Plugin change PR**: Modify a file in `speckit-pro/` -> CI should run tests for speckit-pro
2. **Docs-only PR**: Modify only `README.md` -> CI should skip test execution
3. **Valid title**: `feat(speckit-pro): add feature` -> title check passes
4. **Invalid title**: `Update readme` -> title check fails with helpful error message
5. **Draft PR**: Create draft PR -> workflow should not run until marked ready

## Prerequisites

- SPEC-001 complete (test runner and plugin structure exist)
- Repository hosted on GitHub with Actions enabled
- `ubuntu-latest` runner available (default for public repos)

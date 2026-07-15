# Quickstart: Implement And Verify G56R-001

Use this guide when implementing the canonical report from the completed task
list. It assumes the current working directory is the dedicated G56R-001
worktree.

## 1. Confirm Scope

```bash
git rev-parse --abbrev-ref HEAD
git status --short
```

Expected branch:

```text
g56r-001-candidate-route-baseline
```

Only G56R-001 planning files and the canonical report should change.

## 2. Refresh Official Sources

Open the current official OpenAI documentation needed for model, effort,
custom-agent, MCP, app, configuration, non-interactive, telemetry, and prompting
claims. Record each source as an `OfficialSourceLedgerRecord` with direct URL,
retrieval date, source family, documented facts, supported surfaces, claim
bindings, and invalidation triggers.

Do not use repository files, successful local behavior, third-party material,
or remembered facts as platform authority.

## 3. Inventory Project Inputs

Read current project sources as `project_input`:

```bash
find speckit-pro/codex-agents -maxdepth 1 -type f
find speckit-pro/agents -maxdepth 1 -type f
find tests/speckit-pro/layer6-efficiency -maxdepth 3 -type f
```

Use them only for role intent, declared source fields, fixture state, and
historical context.

## 4. Author The Report

Create:

```text
docs/ai/research/codex-agent-route-candidates.md
```

Required sections:

- scope, authority classes, and snapshot metadata
- official-source ledger
- project-input surface inventory
- twelve role contract records
- provisional candidate route manifest
- three-current/nine-missing fixture backlog
- telemetry requirements and G56R-002 capability questions
- traceability matrix
- strict go/no-go decision and invalidation rules

## 5. Run Focused Checks

Marker check the feature directory and canonical report using the current
workflow gate expression. The search should return no unresolved clarification,
gap, critical/high finding, or placeholder markers.

```bash
rg -n "$G56R_MARKER_REGEX" specs/g56r-001-candidate-route-baseline docs/ai/research/codex-agent-route-candidates.md
```

Scope hygiene:

```bash
git diff --check
git diff --name-only
```

Repository gates:

```bash
python3 tests/speckit-pro/run-all.py --layer 1
python3 tests/speckit-pro/run-all.py
```

## 6. Review Counts And Decisions

Confirm the report contains:

- 9 official-source ledger records
- 12 role contract records
- 12 fixture backlog records
- 3 current Codex prompt-emulation fixture records
- 9 missing executable fixture records
- 0 unsupported admitted seed candidates
- explicit `GO` or `NO-GO` for G56R-002 capability discovery
- explicit `NO-GO` for route qualification, installation, and fallback policy

If any official source is unavailable or does not support a required fact, keep
the affected candidate rejected or blocked. Do not weaken the authority rule to
force a `GO`.

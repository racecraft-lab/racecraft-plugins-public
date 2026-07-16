# Quickstart: Implement And Verify G56R-001

Use this guide when implementing or refreshing the canonical report and its
schema-v2 planning companion from the completed task list. It assumes the
current working directory is the dedicated G56R-001 worktree.

## 1. Confirm Scope

```bash
git rev-parse --abbrev-ref HEAD
git status --short
```

Expected branch:

```text
g56r-001-candidate-route-baseline
```

Only G56R-001 planning/process files, the canonical report, its planning
manifest, and the repository validation surface for the evidence paths should
change.

## 2. Refresh Official Sources

Open the current official OpenAI documentation needed for model, effort,
custom-agent, MCP, app, configuration, non-interactive, telemetry, and prompting
claims. Record each source as an `OfficialSourceLedgerRecord` with source
family, retrieval method, requested URL, canonical URL, retrieval timestamp,
HTTP status, response-body hash, page or section locator, short excerpt anchor,
bounded source-fact extracts, extract hashes, documented facts, supported
surfaces, claim bindings, and invalidation triggers.

Do not use repository files, successful local behavior, third-party material,
or remembered facts as platform authority.

## 3. Inventory Project Inputs

Read current project sources as `project_input`:

```bash
find speckit-pro/codex-agents -maxdepth 1 -type f
find speckit-pro/codex-skills -maxdepth 2 -type f
find speckit-pro/skills -maxdepth 2 -type f
find speckit-pro/agents -maxdepth 1 -type f
find tests/speckit-pro/layer6-efficiency -maxdepth 3 -type f
```

Use them only for role intent, declared source fields, fixture state, and
historical context.

## 4. Author The Evidence Package

Create or refresh:

```text
docs/ai/research/codex-agent-route-candidates.md
docs/ai/research/codex-agent-route-candidate-manifest.json
```

Required sections:

- scope, authority classes, and snapshot metadata
- official-source ledger
- project-input surface inventory
- exact source-fact bindings
- bounded source-fact extracts and extract hashes
- twelve role contract records
- all-role instruction/full-file hash validation evidence
- provisional candidate route manifest
- candidate rationale records
- explicit per-candidate effort-surface IDs, effort-surface records, and role
  instruction hashes
- three-current/nine-missing fixture backlog
- telemetry requirements, terminal-state fields, missing-field classification,
  and G56R-002 capability questions
- traceability matrix with stable traceability IDs
- strict go/no-go decision records with stable decision IDs and invalidation rules

The JSON companion must validate against
`docs/ai/research/agent-route-candidate-manifest.schema.json`, preserve legacy
fact dispositions, and use the same shared structure as the CAR-001 manifest.

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
python3 tests/speckit-pro/unit/test-agent-route-research-parity.py
python3 tests/speckit-pro/run-all.py --layer 1
python3 tests/speckit-pro/run-all.py
```

## 6. Review Counts And Decisions

Confirm the preserved v0.1 report retains its historical counts. Confirm the
current schema-v2 manifest contains:

- 21 official-source ledger records
- 5 effort-surface records
- 17 project-input records
- 12 role contract records
- 23 candidate route records
- 12 fixture backlog records
- 24 traceability records
- 5 decision records
- 3 current Codex prompt-emulation fixture records
- 9 missing executable fixture records
- 0 unsupported admitted seed candidates
- explicit `GO` or `NO-GO` for G56R-002 capability discovery
- explicit `NO-GO` for route qualification, installation, and fallback policy

If any official source is unavailable or does not support a required fact, keep
the affected candidate rejected or blocked. Do not weaken the authority rule to
force a `GO`.

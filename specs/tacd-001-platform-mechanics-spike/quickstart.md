# TACD-001 Quickstart

Use this guide to validate the Plan artifacts now and the spike report after
implementation. Commands run from the repository root.

## Prerequisites

- Current branch is `tacd-001-platform-mechanics-spike`.
- Feature directory is `specs/tacd-001-platform-mechanics-spike`.
- No raw runtime inventories or uncommitted probe dumps are required.

## Scenario 1: Validate Plan Artifacts

```bash
test -s specs/tacd-001-platform-mechanics-spike/plan.md
test -s specs/tacd-001-platform-mechanics-spike/research.md
test -s specs/tacd-001-platform-mechanics-spike/data-model.md
test -s specs/tacd-001-platform-mechanics-spike/quickstart.md
test ! -d specs/tacd-001-platform-mechanics-spike/contracts
```

Expected result:

- Plan, research, data model, and quickstart artifacts exist.
- `contracts/` is absent because TACD-001 has no external API or command
  contract.

## Scenario 2: Reproduce Candidate Source Inventory

```bash
rg -n "Tavily|tavily|Context7|context7|RepoPrompt|repoprompt|MCP|mcp" speckit-pro tests/speckit-pro docs -S
rg -n "capability|capabilities|installed tool|app connector|MCP|mcp" speckit-pro tests/speckit-pro docs -S
```

Expected result:

- Commands return candidate references across active agents, Codex agents,
  skills/references, prerequisite scripts, plugin limitation docs, generated
  payloads, evals, and historical/provenance files.
- The implementation report classifies findings by category instead of treating
  the raw `rg` output as the final audit.

## Scenario 3: Validate Report Structure After Implementation

```bash
test -s docs/ai/research/tool-agnostic-capability-discovery-spike.md
rg -n "^## (Audit Inventory|Platform Mechanics|Directive-Home Recommendation|Active-vs-Historical Allowlist|TACD-002 / TACD-003 / TACD-004 Handoff|Probe Appendix|Verification Evidence)" docs/ai/research/tool-agnostic-capability-discovery-spike.md
```

Expected result:

- The canonical report exists.
- Required sections are present for audit inventory, platform mechanics,
  directive-home recommendation, allowlist categories, downstream handoff, probe
  appendix, and verification evidence.

## Scenario 4: Validate Probe Sanitization

```bash
rg -n "session[_ -]?id|request[_ -]?id|access[_ -]?token|api[_ -]?key|full inventory|connector list|usage|quota|cost" docs/ai/research/tool-agnostic-capability-discovery-spike.md
```

Expected result:

- No unsanitized probe details are present.
- If a phrase appears as part of an exclusion rule, it must be clearly labeled as
  data that was excluded, not data that was captured.

## Scenario 5: Validate No Behavior Change

```bash
git diff --name-only
```

Expected result after implementation:

- Expected changed files are Plan artifacts and
  `docs/ai/research/tool-agnostic-capability-discovery-spike.md`.
- No active runtime guidance, prerequisite behavior, docs messaging, generated
  payload semantics, plugin versions, or final enforcement tests changed in
  TACD-001.

If active plugin/spec/test surfaces are unexpectedly touched, run the smallest
relevant deterministic layer:

```bash
bash tests/speckit-pro/run-all.sh --layer 1
bash tests/speckit-pro/run-all.sh --layer 5
```

## Scenario 6: Check Unresolved Markers

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh G3 specs/tacd-001-platform-mechanics-spike
bash speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh all specs/tacd-001-platform-mechanics-spike
```

Expected result:

- No unresolved Plan or report markers remain before G3/G7 validation.
- Any intentionally unresolved platform mechanic in the report is labeled
  `unresolved` in the runtime-by-capability matrix, not as a placeholder marker.

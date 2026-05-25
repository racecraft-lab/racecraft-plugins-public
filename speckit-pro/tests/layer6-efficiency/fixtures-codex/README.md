# Layer 6 — Codex Efficiency Fixtures

This directory holds Codex-specific fixtures for the L6 cost-quality
benchmark. Each subdirectory is named after a Codex agent (matching the
file at `codex-agents/<name>.toml`) and contains:

- `input-prompt.md` — a representative task for that agent, framed as one
  of the agent's enumerated input types (Clarify question / Checklist
  gap / Analyze finding).
- `expected-output.md` — a baseline the quality scorer compares against.
  Authored to be **structurally precise** (the `## Answer / ## Evidence /
  ## Confidence` sections the agent's `developer_instructions` mandate)
  and **content-tolerant** (paraphrase is fine; the scorer checks
  bullet-phrase word overlap, not exact prose).

## How the benchmark uses these

```bash
# Single agent across all 4 effort levels (xhigh / high / medium / low)
bash tests/layer6-efficiency/run-efficiency-benchmarks.sh \
  --codex --agent codebase-analyst --sweep

# All Codex agents at default effort
bash tests/layer6-efficiency/run-efficiency-benchmarks.sh --codex
```

Results land in `../results-codex/`. Per-run timestamped JSONs are
git-ignored; the consolidated baseline (`consolidated-smoke-*.json`) is
the committed reference.

## Authoring a new Codex fixture

1. Create `fixtures-codex/<agent-name>/` (must match `codex-agents/<agent-name>.toml`).
2. Write `input-prompt.md` posing **one** of the input types listed in
   the agent's `developer_instructions`. Don't combine input types in
   one prompt.
3. Write `expected-output.md` following the exact section structure the
   agent's `## Output Format` section prescribes.
4. Smoke-test: `bash run-efficiency-benchmarks.sh --codex --agent <name>`.
   The output should produce 70%+ quality at xhigh — if not, the
   `expected-output.md` is over-specified (too prescriptive about prose)
   rather than the agent being broken.

## What this benchmark does NOT cover

- Tool availability. `codex exec` does not bring MCP tools (tavily,
  context7, RepoPrompt) into the subprocess by default. An agent whose
  `developer_instructions` direct it to use those tools will perform
  worse here than it does in the full Codex CLI, because it has to fall
  back to its training data. This is a real effect — visible in the
  `domain-researcher` fixture, which scores ~65% across all effort
  levels — and a limitation of the bare `codex exec` invocation, not the
  fixture or the agent.

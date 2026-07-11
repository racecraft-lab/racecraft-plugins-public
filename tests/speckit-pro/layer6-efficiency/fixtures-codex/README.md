# Layer 6 — Codex Efficiency Fixtures

This directory holds Codex-specific fixtures for the L6 cost-quality
benchmark. Each subdirectory is named after a Codex agent (matching the
file at `speckit-pro/codex-agents/<name>.toml`) and contains:

- `input-prompt.md` — a representative task for that agent, framed as one
  of the agent's enumerated input types (Clarify question / Checklist
  gap / Analyze finding).
- `expected-output.md` — a baseline the quality scorer compares against.
  Authored to be **structurally precise** (the `## Answer / ## Evidence /
  ## Confidence` sections the agent's `developer_instructions` mandate)
  and **content-tolerant** (paraphrase is fine; the scorer checks
  bullet-phrase word overlap, not exact prose).

## How the benchmark uses these

```console
# Single agent across all 4 effort levels (xhigh / high / medium / low)
python3 tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py \
  --codex --agent codebase-analyst --sweep

# All three current Codex fixtures at ambient/default effort
python3 tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py --codex
```

Results land in `../results-codex/`. Per-run timestamped JSONs are
git-ignored; the consolidated baseline (`consolidated-smoke-*.json`) is
the committed reference.

## Authoring a new Codex fixture

1. Create `tests/speckit-pro/layer6-efficiency/fixtures-codex/<agent-name>/`
   (must match `speckit-pro/codex-agents/<agent-name>.toml`).
2. Write `input-prompt.md` posing **one** of the input types listed in
   the agent's `developer_instructions`. Don't combine input types in
   one prompt.
3. Write `expected-output.md` following the exact section structure the
   agent's `## Output Format` section prescribes.
4. Smoke-test:
   `python3 tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py --codex --agent <name>`.
   Treat the score as non-promotional legacy smoke evidence. Never infer the
   cause of a low score from the score alone.
5. Adjudicate a disputed result blind to the candidate model and effort as one
   of: candidate-quality failure, treatment-delivery failure, invalid fixture,
   invalid scorer, or infrastructure failure. Version and replay every affected
   result after a fixture or scorer change.

## What this benchmark does NOT cover

- Exact treatment delivery. The current runner prepends only
  `developer_instructions` to the fixture and invokes bare `codex exec` while
  inheriting ambient configuration. It neither provisions nor disables the
  TOML model, sandbox, skills, MCP servers, tools, or parent overrides. A
  missing or ambient capability can therefore change the result. Current
  scores—including the historical `domain-researcher` result—cannot support
  routing promotion until replayed with frozen environment and treatment proof.

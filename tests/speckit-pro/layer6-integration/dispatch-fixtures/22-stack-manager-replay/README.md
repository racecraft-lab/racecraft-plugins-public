# Fixture 22 - Stack manager replay

Verifies that a stack-manager scenario routes through the normal autopilot
agents (`analyze-executor`, `implement-executor`), never re-enters
`grill-me`, avoids live `gh` execution, and names the evidence fields of the
shipped contract.

The prompt is a self-contained scenario, like the other dispatch fixtures.
It names the `detect-stack-manager-plan` helper and the
`stack-manager-decision.v1` record (see
`speckit-pro/skills/speckit-autopilot/references/stack-manager.md` and
`contracts/stack-manager-decision.schema.json`). `must_include_terms` lists
names the helper actually returns, including `mutation_boundary`.

In `--replay`, `must_include_terms` are checked against the committed
`parser-fixture.jsonl`, which holds hand-authored dispatch prompts and text.
Replay therefore proves that the parser sees the terms, not that a model
produced them. Only `--live` checks the terms against a fresh transcript.

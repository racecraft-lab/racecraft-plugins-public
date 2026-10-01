# Historical statements in the frozen draft-PR sources

The files under `source/` are byte-exact planning records from the scaffold
workload, pinned by hash in `../manifest.json`. They describe the contract as it
stood when that workload was planned. Do not edit them to match later changes.

Three of them say the PR packet schema allows an uppercase ticket-style scope. That statement is historical. The packet schema now rejects an uppercase
scope: the title pattern in
`speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json` allows
only a lowercase scope, the same shape the release-readiness gate requires.
`test-performance-fixtures.py` checks the schema pattern and checks that these
are the only files that still state the old behavior.

- `source/contracts/draft-packet-mode.md`, section 5 (title contract)
- `source/research.md`, the pre-existing delta rationale
- `source/quickstart.md`, the note after the title check

Read the current schema and the shipped autopilot references for the live rule.

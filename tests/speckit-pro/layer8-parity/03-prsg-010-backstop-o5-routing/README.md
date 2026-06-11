# Parity Fixture 03 - PRSG-010 Backstop, O5, And Routing

Proves the PRSG-010 operator-facing contracts remain equivalent across Agent
Teams and fallback execution paths. The fixture is static guidance parity: it
does not run the final gate, scaffold O5 children, or emit PRs.

## Test scenario

The workflow records the guidance that Claude Code and Codex surfaces must keep
aligned:

- final reviewability backstop stops before PR body generation, `gh pr create`,
  or `multi-pr-emission.sh`
- generated/template exception text is rejected while operator-owned
  `refactor`, `infra`, and `upgrade` classes remain valid only in review-visible
  contract artifacts
- O5 is a fallback after normal PRSG-007/008/009 split planning cannot produce
  reviewable slices; child specs remain flat siblings
- contextual router probes promote only high-confidence evidence and keep weak
  evidence in closed hint tokens

Dry-run mode validates fixture shape and JSON.

## Mode

```bash
bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run --fixture 03-prsg-010-backstop-o5-routing
```

Live mode is optional and token-costly, consistent with Layer 8.

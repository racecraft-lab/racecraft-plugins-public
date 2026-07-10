# Parity Fixture 03 - Reviewability Backstop And Parent-Child Routing

Proves that reviewability-backstop and parent-child routing contracts remain
equivalent across Agent Teams and fallback execution paths. The fixture is
static guidance parity: it does not run the final gate, scaffold child specs,
or emit PRs.

## Test scenario

The workflow records the guidance that Claude Code and Codex surfaces must keep
aligned:

- final reviewability backstop stops before PR body generation, `gh pr create`,
  or `multi-pr-emission.sh`
- generated/template exception text is rejected while operator-owned
  `refactor`, `infra`, and `upgrade` classes remain valid only in review-visible
  contract artifacts
- parent-child decomposition is a fallback after normal split planning cannot
  produce reviewable slices; child specs remain flat siblings
- contextual router probes promote only high-confidence evidence and keep weak
  evidence in closed hint tokens

Dry-run mode validates fixture shape and JSON.

## Mode

```bash
python3 tests/speckit-pro/layer8-parity/run-parity-fixtures.py --dry-run --fixture 03-reviewability-backstop-parent-child-routing
```

Live mode is optional and token-costly, consistent with Layer 8.

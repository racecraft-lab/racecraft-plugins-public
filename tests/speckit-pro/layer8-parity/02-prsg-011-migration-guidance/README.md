# Parity Fixture 02 - PRSG-011 Migration Guidance

Proves that PRSG-011 operator guidance remains equivalent across runtime
surfaces and post-implementation dispatch paths. The fixture focuses on static
text contracts, not script mutation behavior.

## Test scenario

The workflow records the exact repository migration and Tier-2 relocation
guidance that Claude Code and Codex surfaces must expose:

- repository migration dry-run/apply sequence from `speckit-upgrade`
- Tier-2 relocation dry-run/apply suggestion sequence from scaffold/autopilot
- frozen, already-current, no-candidate, and out-of-scope suppression reasons
- no automatic `relocate-process-artifacts.sh` execution

Layer 8 live mode compares the same workflow after Path A and Path B execution.
Dry-run mode validates fixture shape and JSON.

## Mode

Dry-run validates structure today:

```bash
bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run --fixture 02-prsg-011-migration-guidance
```

Live mode is optional and token-costly, consistent with Layer 8.

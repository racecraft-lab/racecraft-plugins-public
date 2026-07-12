# Parity Fixture 02 - Repository Migration Guidance

Proves that repository-migration operator guidance remains equivalent across
runtime surfaces and post-implementation dispatch paths. The fixture focuses
on static text contracts, not script mutation behavior.

## Test scenario

The workflow records the exact Python-runner migration and Tier-2 relocation
guidance that Claude Code and Codex surfaces must expose:

- repository migration dry-run/apply sequence from `speckit-upgrade`
- Tier-2 relocation dry-run/apply suggestion sequence from scaffold/autopilot
- frozen, already-current, no-candidate, and out-of-scope suppression reasons
- a bounded legacy-input example containing retired helper paths, which must
  never be repeated as the current command
- must not invoke the retired `relocate-process-artifacts.sh` path or auto-run
  the runner relocation helper

Layer 8 live mode compares the same workflow after Path A and Path B execution.
Dry-run mode validates fixture shape and JSON.

## Mode

Dry-run validates structure today:

```bash
python3 tests/speckit-pro/layer8-parity/run-parity-fixtures.py --dry-run --fixture 02-repository-migration-guidance
```

Live mode is optional and token-costly, consistent with Layer 8.

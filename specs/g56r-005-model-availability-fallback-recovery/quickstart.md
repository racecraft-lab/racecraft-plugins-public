# Quickstart: G56R-005

This feature is deterministic local simulation only. It must not contact live model services or mutate a real Codex home.

## Focused Verification

```bash
python3 tests/speckit-pro/unit/test-codex-route-fallback-recovery.py
```

## Layer Verification

```bash
python3 tests/speckit-pro/run-all.py --layer 4
```

## Full Verification

```bash
python3 tests/speckit-pro/run-all.py
```

## Expected Evidence

- Route replay emits deterministic ordered plugin diagnostics and exactly one terminal outcome.
- Service reroute attribution is separate from plugin reasons.
- Optional-helper unavailability continues only with explicit independently qualified no-helper evidence.
- Fake-home failure cases prove atomic no-write, rollback, previous-known-good preservation, cleanup disposition, and no host-specific metadata in canonical records.
- The final PR packet states that live availability smoke was not run and that production routing, generated payloads, plugin versions, frozen Claude behavior, and G56R-004 contracts were not modified.

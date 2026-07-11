# Test Suite Guidelines

Repository-only validation lives here, outside the shipped plugin. Python 3.11+ standard library only — no new shell, no `jq`.

## Source of truth

`suite-manifest.json` defines layer membership, dispatch, execution mode, and default selection. `run-all.py` and the shipped suite gate both read it; change the manifest, not hardcoded layer lists.

## Commands

- `python3 tests/speckit-pro/run-all.py` — toolchain preflight plus the default deterministic layers (1, 4, 5).
- `python3 tests/speckit-pro/run-all.py --layer <N>` — a single layer.
- `python3 tests/speckit-pro/run-all.py --integration` — Layer 7 replay fixtures (free); add `--live` only for an intentional live run (`claude -p`, costs tokens).
- Layers 2, 3, and 6 need `claude -p` and are developer-local only. Layer 8 parity: `--dry-run` is free; `--live --budget-usd <N>` is expensive.
- Runner-gate requests live under `unit/fixtures/runner-gates/requests/` and run via `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < <request.json>`.

## Trap: files here regenerate a committed docs page

Any new or changed `.md`, `.py`, or `.sh` file anywhere under `tests/speckit-pro/` (including this file) feeds the generated docs-site tests reference. Run `pnpm --dir docs-site reference:generate` and commit the regenerated `docs-site/src/content/docs/reference/tests.md` in the same PR, or the `validate-docs` CI check fails.

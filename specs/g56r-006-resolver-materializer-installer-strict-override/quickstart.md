# Quickstart: G56R-006 Validation

All G56R-006 validation uses deterministic fixtures and fake homes. Do not run live model calls, do not mutate a real `~/.codex/agents`, and do not qualify downstream production routes.

## 1. Focused Route-aware Installer Tests

Run the mutation-helper unit test after adding the route-aware cases:

```bash
python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py
```

Expected outcomes:

- Static no-manifest cases still install or verify the strict 13-file destination roster and omit `data.routing`.
- Valid route-aware dry-run returns one snapshot, 12 required records, optional helper state, materialization proofs, and zero source TOML mutations.
- Required-route miss cases return complete diagnostics for all 12 required agents, zero planned/applied writes and removals, `writes_state=false`, and `restart_required=false`.
- Strict override cases evaluate exactly one tuple per required agent and never select preferred/fallback routes after an override miss.
- Helper unavailable cases install, omit, remove with proof, or preserve with manual remediation according to ownership evidence.
- Apply failure cases prove rollback restoration or report unrestored actions with restart guidance.

## 2. Structural and Runtime Gates

Run Layer 4 while iterating on Python helper behavior:

```bash
python3 tests/speckit-pro/run-all.py --layer 4
```

Run Layer 1 after generated payload mirrors are refreshed:

```bash
python3 tests/speckit-pro/run-all.py --layer 1
```

Run the full Python-authoritative suite before implementation closeout:

```bash
python3 tests/speckit-pro/run-all.py
```

Expected outcome: zero failures.

## 3. Generated Payload Refresh

After production runner or Codex skill files change, refresh generated release artifacts:

```bash
python3 scripts/refresh-release-artifacts.py
```

Expected outcomes:

- `dist/codex/speckit-pro/...` mirrors changed runner and Codex install skill bytes.
- `dist/claude/speckit-pro/...` mirrors changed shared runner bytes.
- Installed-cache fixture mirrors under `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/` stay consistent with source payloads.

## 4. Docs Reference Refresh

Because the plan modifies a tracked Python unit test under `tests/speckit-pro/`, run docs reference generation and check after installing docs-site dependencies once in this worktree:

```bash
pnpm --dir docs-site install --frozen-lockfile
pnpm --dir docs-site reference:generate
pnpm --dir docs-site reference:check
```

Expected outcomes:

- `docs-site/src/content/docs/reference/tests.md` is current.
- `docs-site/src/content/docs/install/codex.md` documents static compatibility and route-aware manifest activation.

## 5. Contract Review Checklist

Before marking implementation complete, verify:

- Requests with no `route_policy_manifest` omit `data.routing`.
- Requests with an invalid supplied manifest fail route-aware activation rather than silently falling back to static mode.
- Manifest paths outside the repository trusted-file boundary, symlinked manifests, unsupported versions, and manifest or source-roster identity mismatches fail before discovery or mutation.
- Every required policy's non-route contract digest matches canonical materialization of its trusted source TOML.
- Required-policy objects use the exact closed schema and a duplicate-free string array for required capabilities.
- Optional-helper `no_helper` authorization uses a closed record with a strict boolean `allowed` value.
- Every route-aware response has exactly one snapshot ID and all 12 required-agent records cite it.
- Strict override required misses report complete diagnostics and zero writes.
- Optional helper removal has exact known rendered-byte digest proof; caller-asserted provenance is rejected as untrusted.
- Apply and rollback refuse to overwrite a destination changed after its captured snapshot.
- Successful rollback restores bytes and modes or removes newly created files and reports no restart.
- Recovery evidence reports only actions actually applied and rolled back, the exact failed write or removal, and real directory-cleanup outcomes.
- Bounded probes reject partial records, aliases, key/ID mismatches, and candidate routes that do not declare the same probe.
- Reused route IDs must describe one identical normalized route tuple, and write/removal swaps preserve entries created in the final mutation window.
- No-clobber collisions retain both the moved prior entry and the concurrent target, report every preserved path, and fail with manual remediation; temporary or backup cleanup failures are never reported as success.
- Post-copy verification failures identify the verification action and every mismatched target before rollback.
- Rollback uncertainty sets restart guidance and does not claim verification success.
- Fake-home cases use a temporary HOME/USERPROFILE or temporary repository `.codex/agents` destination; they do not add a test-only installer input or touch the operator's real home.

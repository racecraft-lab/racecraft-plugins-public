# XPLAT-010 Count-Parity Ledger

Running record of the `.sh` → `.py` count-parity ports in the XPLAT-010 stack
(FR-013). Each port PR appends **one delta line** proving 1:1 name-and-count
parity against its committed baseline under
`tests/speckit-pro/parity/xplat-010/`. The cumulative roll-up lands in
`docs/ai/specs/.process/XPLAT-010-suite-parity-result.json` (Polish phase).

Columns:

- **PR** — the stack slice (e.g. `PR 3a`).
- **Script** — the ported test module (`.py`), or the swap performed.
- **Mode** — the invocation mode when a script has more than one baseline pair.
- **bash → python** — assertion counts on each side (must be equal).
- **names_equal** — `yes` when the ordered canonical check-name inventory is
  identical (a rename/drop makes this `no` and flags a regression).
- **baseline** — the committed baseline pointer, or `n/a` for a count-neutral swap.

| PR | Script | Mode | bash → python | names_equal | baseline |
|----|--------|------|---------------|-------------|----------|
| PR 13 | port: `test-estimate-spec-size.sh` → `test-estimate-spec-size.py` | default | 33 → 33 | yes | `tests/speckit-pro/parity/xplat-010/test-estimate-spec-size-baseline.txt` |
| PR 2 | wrapper swap: `test-speckit-pro-runner.sh` → `test-speckit-pro-runner.py` | default | 0 → 0 (pure `python3 …` shim; no own assertions) | n/a | n/a |
| PR 2 | wrapper swap: `test-speckit-pro-read-only-helpers.sh` → `test-speckit-pro-read-only-helpers.py` | default | 0 → 0 (pure `python3 …` shim; no own assertions) | n/a | n/a |
| PR 3a | port: `validate-agents.sh` → `validate-agents.py` | default | 104 → 104 | yes | `tests/speckit-pro/parity/xplat-010/validate-agents-baseline.txt` |
| PR 3a | port: `validate-capability-pointer.sh` → `validate-capability-pointer.py` | default | 52 → 52 | yes | `tests/speckit-pro/parity/xplat-010/validate-capability-pointer-baseline.txt` |
| PR 3a | port: `validate-capability-resolution.sh` → `validate-capability-resolution.py` | default | 43 → 43 | yes | `tests/speckit-pro/parity/xplat-010/validate-capability-resolution-baseline.txt` |
| PR 3a | port: `validate-codex-agents.sh` → `validate-codex-agents.py` | default | 148 → 148 | yes | `tests/speckit-pro/parity/xplat-010/validate-codex-agents-baseline.txt` |
| PR 3a | port: `validate-codex-hooks.sh` → `validate-codex-hooks.py` | default | 9 → 9 | yes | `tests/speckit-pro/parity/xplat-010/validate-codex-hooks-baseline.txt` |
| PR 3a | port: `validate-codex-marketplace.sh` → `validate-codex-marketplace.py` | default | 13 → 13 | yes | `tests/speckit-pro/parity/xplat-010/validate-codex-marketplace-baseline.txt` |
| PR 3a | port: `validate-codex-parity.sh` → `validate-codex-parity.py` | default | 81 → 81 | yes | `tests/speckit-pro/parity/xplat-010/validate-codex-parity-baseline.txt` |
| PR 3a | port: `validate-codex-plugin.sh` → `validate-codex-plugin.py` | default | 33 → 33 | yes | `tests/speckit-pro/parity/xplat-010/validate-codex-plugin-baseline.txt` |
| PR 3a | port: `validate-curated-set.sh` → `validate-curated-set.py` | default | 58 → 58 | yes | `tests/speckit-pro/parity/xplat-010/validate-curated-set-baseline.txt` |
| PR 3a | port: `validate-hooks.sh` → `validate-hooks.py` | default | 11 → 11 | yes | `tests/speckit-pro/parity/xplat-010/validate-hooks-baseline.txt` |

**PR 13 note (T121–T130):** The estimator Layer-4 test follows the
Per-Port Protocol against historical predecessor commit
`c9176902d98082415aac88954b2f66fa6c499506`. Six-item dual-run proof:
(1) `VERBOSE=true bash tests/speckit-pro/layer4-scripts/test-estimate-spec-size.sh`
in that historical checkout, parsed by `tests/speckit-pro/lib/capture_baseline.py`;
(2) `python3 tests/speckit-pro/layer4-scripts/test-estimate-spec-size.py`;
(3) committed baseline `tests/speckit-pro/parity/xplat-010/test-estimate-spec-size-baseline.txt`;
(4) ordered-name inventory diff: no differences, 1:1 preserved;
(5) Bash `33` == Python `33`; (6) intentional change: none.

**PR 2 note:** No test-logic ports land in PR 2. The two rows above record the
count-neutral removal of the redundant Bash wrappers — the suite manifest now
lists the `.py` modules they shimmed directly, so the same assertions run with no
count change. The parity tooling (`lib/capture_baseline.py`, `lib/test_result.py`)
and this ledger are established here for the ports in PRs 3a–9.

**PR 3a note (batch 1 of 2, T018–T022):** The first five mechanical Layer-1
validators port with exact 1:1 name-and-count parity against their committed
baselines. Two of them — `validate-capability-pointer` and
`validate-capability-resolution` — had their bash predecessors interpolate the
*absolute* agents-directory / `dist/**` tree paths into a handful of check names
(2 and 4 names respectively). That absolute repo-root prefix is environment noise
(it differs per checkout — CI checks out under a different absolute root), never part of the
check identity, and would violate the repo's privacy hard constraint if committed.
Both the committed baseline and the Python port record the **repo-relative** form
(`speckit-pro/agents`, `dist/claude`, …); the assertion count and the check
identity are preserved, and only the environment-specific prefix is normalized —
so `names_equal` remains `yes` against the committed baseline. The extracted path
tokens (`speckit-pro/skills/...`) are already repo-relative and are recorded
verbatim.

**PR 3a note (batch 2 of 2, T023–T027):** The remaining five mechanical Layer-1
validators port with exact 1:1 name-and-count parity against their committed
baselines (13, 81, 33, 58, 11 → same). Intentional change: `none` for every row.
Unlike batch 1, none of these five interpolate an absolute repo-root prefix into
any check name, so no environment-path normalization was needed — the ports read
live data and reproduce the bash logic directly, and all names are recorded
verbatim. Two data-driven name sources are recorded as baseline regeneration
triggers (count-parity contract §2, rule 4): `validate-codex-parity` interpolates
the shared plugin version (`.claude-plugin`/`.codex-plugin` `plugin.json`) and the
marketplace name (both `marketplace.json` files) into two check names and
enumerates each Codex `SKILL.md`'s `../../skills/**.md` reference links; and
`validate-curated-set` derives its per-entry check names from live
`speckit-pro/scripts/curated-set.json` content. Adding, removing, or reordering
any of those inputs changes the inventory and requires recapturing the affected
baseline. This completes PR 3a — all ten batch-1+batch-2 Layer-1 validators are
ported; ten `.sh` deleted.

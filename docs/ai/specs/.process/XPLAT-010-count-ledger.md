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

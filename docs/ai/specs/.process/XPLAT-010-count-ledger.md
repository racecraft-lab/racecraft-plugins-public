# XPLAT-010 Count-Parity Ledger

Running record of the `.sh` -> `.py` count-parity ports in the XPLAT-010 stack
(FR-013). Each port PR appends one delta line proving 1:1 name-and-count parity
against its committed baseline under `tests/speckit-pro/parity/xplat-010/`.

| PR | Script | Mode | bash -> python | names_equal | baseline |
|----|--------|------|----------------|-------------|----------|
| PR 13 | port: `test-estimate-spec-size.sh` -> `test-estimate-spec-size.py` | default | 33 -> 33 | yes | `tests/speckit-pro/parity/xplat-010/test-estimate-spec-size-baseline.txt` |

**PR 13 note (T121-T130):** The estimator Layer-4 test follows the Per-Port
Protocol against the historical predecessor checkout at commit
`c9176902d98082415aac88954b2f66fa6c499506`. Six-item dual-run proof:

1. Bash capture command: `VERBOSE=true bash tests/speckit-pro/layer4-scripts/test-estimate-spec-size.sh` in the historical checkout, parsed by `tests/speckit-pro/lib/capture_baseline.py`.
2. Port command: `python3 tests/speckit-pro/layer4-scripts/test-estimate-spec-size.py`.
3. Committed baseline: `tests/speckit-pro/parity/xplat-010/test-estimate-spec-size-baseline.txt`.
4. Ordered-name inventory diff: no differences, 1:1 preserved.
5. Count equality: Bash `33` == Python `33`.
6. Intentional change: none.

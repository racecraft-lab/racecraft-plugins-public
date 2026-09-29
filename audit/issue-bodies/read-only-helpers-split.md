Priority: major

## Summary

helpers/read_only.py (about 9,000 lines) holds the sweep comment-export cluster and primitives that core modules need. Core modules reach it through function-local imports, which is the inverted core-to-helpers edge recorded in the architecture baseline and hides a 20-file import cycle. The utf-8 cut helper also exists twice.

## Evidence

- **brokers-and-verification-003** (major): Core modules import shared primitives (resolve_repo_root, is_test_path, trusted_text, write_bytes_atomic, PHASE7_* constants) from helpers/read_only.py and helpers/mutation.py through function-local imports. This is the inverted core-to-helpers edge the arch baseline records, and the local imports hide a 20-file import cycle from static tools. PR 852 raises execution_control's local helper imports from 4 to 7.
  - `speckit-pro/speckit_pro_runner/execution_control.py:387`, `speckit-pro/speckit_pro_runner/execution_control.py:1097`, `speckit-pro/speckit_pro_runner/execution_control.py:1556`, `speckit-pro/speckit_pro_runner/execution_control.py:1726`, `speckit-pro/speckit_pro_runner/task_results.py:20`, `speckit-pro/speckit_pro_runner/task_results.py:76`, `speckit-pro/speckit_pro_runner/task_results.py:319`, `speckit-pro/speckit_pro_runner/sweep_isolation.py:660`, `speckit-pro/speckit_pro_runner/sweep_isolation.py:1564`
- **runner-core-001** (major): helpers/read_only.py (8964 lines) holds 23 sweep_* functions (comment export, redaction, fence handling) that belong with the sweep modules, plus primitives that core modules need. sweep_isolation.py, execution_control.py, task_results.py and gate_preflight_coverage.py import it through function-local imports to dodge the 20-file cycle that ripwire --deps reports.
  - `speckit-pro/speckit_pro_runner/helpers/read_only.py:3391-4267`, `speckit-pro/speckit_pro_runner/sweep_isolation.py:660`, `speckit-pro/speckit_pro_runner/execution_control.py:387`, `speckit-pro/speckit_pro_runner/helpers/gate_preflight_coverage.py:130`
- **brokers-and-verification-005** (minor): _bounded_comment_body and sweep_cut_utf8 are the same UTF-8 boundary cut, defined in two modules.
  - `speckit-pro/speckit_pro_runner/sweep_isolation.py:428-435`, `speckit-pro/speckit_pro_runner/helpers/read_only.py:3396-3404`

## Proposed fix

- brokers-and-verification-003: Move the shared primitives into a core module (path and text utilities, atomic write) that both layers import at module level, then drop the local imports and the baselined edges.
- runner-core-001: Move the sweep_* cluster next to sweep_isolation.py, and move shared primitives (is_test_path, PHASE7_* constants, trusted_open_*, resolve_repo_root) into a lower module so imports can be top-level and the core-to-helpers arrows disappear.
- brokers-and-verification-005: Keep one function in a shared text utility and call it from both.

## Acceptance

- [ ] Sweep functions sit with the sweep modules; shared primitives sit in a lower module imported at module level.
- [ ] No function-local import from helpers/ remains in the core modules listed in the evidence.
- [ ] Runner trust metadata and dist/ are regenerated (refresh-release-artifacts.py), and both suites pass.

## Related

- Overlaps files changed by the open stop-policy stack: #837, #838, #846, #847, #848, #849, #850, #851, #852. Land after that stack merges.
- Overlaps files changed by open PR #685.
- Overlaps files changed by the in-progress fix for #832.

Found by the 2026-09 coherence audit.

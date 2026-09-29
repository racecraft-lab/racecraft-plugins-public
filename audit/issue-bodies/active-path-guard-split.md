Priority: major

## Summary

gates/active_path_guard.py (5,591 lines, 204 functions) carries two parallel guard families, the v1.0 active-path guard and the v2.0 installed-runtime guard, plus two more guards and an AST analyzer. Four function pairs are near duplicates, so a fix to one member can miss the other.

## Evidence

- **runner-core-006** (major): active_path_guard.py (5591 lines, 204 functions) carries two parallel guard families, the v1.0 active-path guard and the v2.0 installed-runtime guard, plus repo-bash-confinement, zero-bash and a Python AST analyzer. Paired near-duplicates: guard_response/active_runtime_guard_response (4156/4186), scan_sources/scan_installed_runtime_sources (4254/4302), classify_raw_finding/classify_installed_runtime_raw_finding (4380/4403), remediation_for/installed_runtime_remediation_for (4951/4969). A fix to one pair member can miss the other.
  - `speckit-pro/speckit_pro_runner/gates/active_path_guard.py:4156`, `speckit-pro/speckit_pro_runner/gates/active_path_guard.py:4186`

## Proposed fix

- runner-core-006: Split by guard (path guard, runtime guard, AST analyzer) and parameterize the paired functions on a small policy object.

## Acceptance

- [ ] The module is split by guard, and the paired functions share one implementation parameterized by a policy object.
- [ ] Existing guard tests pass unchanged; one test exercises each policy through the shared path.
- [ ] Runner trust metadata and dist/ are regenerated.

## Related

- None.

Found by the 2026-09 coherence audit.

Priority: major

## Summary

Small runner primitives exist in several copies: the canonical-JSON encoder lives in agent materialization and is re-implemented in install.py, version parsing exists three times, and three modules carry their own gh or git subprocess wrapper with different timeouts and exception handling.

## Evidence

- **autopilot-and-agents-006** (major): The canonical-JSON byte encoder lives in the agent-materialization module, and task_results, verification_records and failing_checks import it from there for unrelated hashing. install.py re-implements the identical encoder as route_policy_canonical_bytes.
  - `speckit-pro/speckit_pro_runner/agent_materialization.py:53`, `speckit-pro/speckit_pro_runner/helpers/install.py:2453`, `speckit-pro/speckit_pro_runner/task_results.py:11`, `speckit-pro/speckit_pro_runner/verification_records.py:32`, `speckit-pro/speckit_pro_runner/failing_checks.py:18`
- **lifecycle-skills-005** (minor): install.parse_version and runtime.parse_version_tuple are the same function with two names. research_preflight has a third parse_version with a different signature.
  - `speckit-pro/speckit_pro_runner/helpers/install.py:5546-5555`, `speckit-pro/speckit_pro_runner/runtime.py:183-192`, `speckit-pro/speckit_pro_runner/research_preflight.py:189`
- **brokers-and-verification-016** (minor): Three modules each carry their own subprocess wrapper for gh (and git in stack_manager), with the same result shape and different timeouts (30, 20, and sweep_isolation's own).
  - `speckit-pro/speckit_pro_runner/helpers/archive_sweep.py:31`, `speckit-pro/speckit_pro_runner/helpers/stack_manager.py:27`, `speckit-pro/speckit_pro_runner/sweep_isolation.py:438`
- **pr-emission-and-stack-1-008** (minor): stack_manager.probe and archive_sweep.probe are near-duplicate subprocess wrappers (clone similarity 0.81) with different timeouts and different exception handling. The two BRANCH patterns also differ slightly. The stack_manager ValueError for an unknown CLI is raised inside its own try block and is not caught there.
  - `speckit-pro/speckit_pro_runner/helpers/stack_manager.py:14`, `speckit-pro/speckit_pro_runner/helpers/stack_manager.py:27-38`, `speckit-pro/speckit_pro_runner/helpers/archive_sweep.py:27`, `speckit-pro/speckit_pro_runner/helpers/archive_sweep.py:31-54`

## Proposed fix

- autopilot-and-agents-006: Move canonical_bytes to a small shared runner module and reuse it in install.py.
- lifecycle-skills-005: Keep one version parser in a shared module (path_utils or runtime) and import it.
- brokers-and-verification-016: Share one fixed-argv gh/git probe helper that takes the timeout as a parameter.
- pr-emission-and-stack-1-008: Extract one bounded gh/git probe with a per-caller allowlist and share the branch pattern.

## Acceptance

- [ ] One canonical-JSON module, one version parser and one bounded gh/git probe helper, each imported by every caller.
- [ ] Existing tests pass unchanged; a unit test covers the probe helper's timeout and error shape.
- [ ] Runner trust metadata and dist/ are regenerated.

## Related

- Overlaps files changed by the open stop-policy stack: #846, #847, #850, #851, #852. Land after that stack merges.
- Overlaps files changed by the in-progress fix for #832.

Found by the 2026-09 coherence audit.

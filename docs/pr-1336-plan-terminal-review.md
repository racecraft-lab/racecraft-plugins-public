# Plan terminal helper review follow-up

PR #1336 repairs the terminal helper at the full runner dispatcher seam. Its
review reproductions cover the planning gate, confined cleanup, interrupted
authoring, brokered preview evidence, research freshness, and independent
planning-derived page expectations. The shared runner ships to both hosts.

## Known limits

- R1336-0f1bd68e: the original production diff exceeded the ticket's 400-line
  warning target. This is a reviewability warning, not a reachable behavior
  defect or a blocking size tier. This repair keeps each defect in a separate
  commit and adds no unrelated refactor or quality cleanup.
- R1336-d4941850: the existing CLI trust policy rejects user-owned executable
  installations. A consumer must install `gh` through a system-managed,
  trusted installation whose executable and parent directories satisfy
  `cli_probe`. The helper stops at `tool_unavailable` if that installation is
  unavailable. The observed compatibility limit does not authorize bypassing
  the existing executable trust boundary.
- Real GitHub draft creation and interactive preview/question UI are not
  exercised by these deterministic tests. Git uses a disposable bare remote;
  GitHub responses are scripted. UI requests are checked against their
  documented schemas and contracts.
- Linux VM tests do not establish macOS behavior. Before merging, the
  orchestrator must run native macOS coverage, including
  `test_gate_hardening.py::test_pr_test_code_cannot_touch_the_host_under_the_real_sandbox`
  and
  `test_gate_hardening.py::test_pr_test_code_cannot_create_or_modify_any_file_in_the_clone`.

The original reviews are the
[Codex cross-host review](https://github.com/racecraft-lab/racecraft-plugins-public/pull/1336#issuecomment-6137252608)
and the
[Daybreak security review](https://github.com/racecraft-lab/racecraft-plugins-public/pull/1336#issuecomment-6137269198).

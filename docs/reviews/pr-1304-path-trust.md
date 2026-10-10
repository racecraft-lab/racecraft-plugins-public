# PR 1304: PATH ownership coverage

Finding F1304-a2ed4964 is the class **false pass of PATH ownership gate**.
The test fixture previously rejected an owned directory or sibling executable
before it could prove that the requested executable's ownership was checked.

The fixture now installs only the requested CLI in its PATH directory. It models
ownership by inode, independently of write access, so a runner-owned executable
can have protected ancestors. Every assertion runs against the source, Claude
payload and Codex payload, with regular, symlink and hardlink targets.

## Variant coverage

All tests below are in `tests/speckit-pro/unit/test-cli-probe-path-trust.py`.

| Variant | Test |
| --- | --- |
| Host directory ownership masked codex or claude file ownership | `test_runner_owned_executable_is_rejected`, each host CLI |
| Missing non-host executable ownership coverage | `test_runner_owned_executable_is_rejected`, git, gh and docker |
| Selective codex ownership bypass | `test_runner_owned_executable_is_rejected`, codex |
| Selective claude ownership bypass | `test_runner_owned_executable_is_rejected`, claude |
| Selective git bypass masked by a codex sibling | `test_runner_owned_executable_is_rejected`, git alone |
| Selective gh ownership bypass | `test_runner_owned_executable_is_rejected`, gh alone |
| Selective docker ownership bypass | `test_runner_owned_executable_is_rejected`, docker alone |
| Global regular-file ownership rejection removed | `test_runner_owned_executable_is_rejected`, all five CLIs |
| Runner-writable executable rejection | `test_runner_writable_executable_is_rejected`, all five CLIs |
| Host writable-directory rejection | `test_runner_writable_host_path_directory_is_rejected`, both hosts |
| Host owned-directory rejection, including the direct helper assertion | `test_runner_owned_host_path_directory_is_rejected`, both hosts |
| Protected executable acceptance control | `test_root_owned_read_only_executable_is_accepted`, all five CLIs |
| External non-host writable-directory policy | `test_other_cli_path_directory_stays_outside_the_directory_rule`, git, gh and docker |

Each row includes source and both payload copies and all three target layouts.
Each PATH directory holds only the requested name, so there is no second entry
to mask a target-specific bypass. A rename layout was dropped: renaming the
executable away and back keeps the same inode and name, so it repeated the
regular-file layout.

## Known limits

- Non-host writable PATH directories remain accepted by the existing external
  directory policy. A writer already controls replacement names in that external
  namespace. This is an accepted policy limit, not a newly introduced regression;
  the acceptance test pins it for all three non-host CLIs.
- Ownership is modeled by patching `os.stat` and `os.lstat`, which every Python 3.11 to 3.14
  `Path` read reaches, and effective access by patching `os.access` and `os.geteuid`.
  The tests exercise actual filesystem traversal and lookup, but do not require
  privileged ownership changes or claim to simulate concurrent replacement.
- Linux verification does not establish macOS plugin CI coverage. The orchestrator
  must run the macOS suite and the Linux-skipped checks
  `test_gate_hardening.py::test_pr_test_code_cannot_touch_the_host_under_the_real_sandbox`
  and `test_gate_hardening.py::test_pr_test_code_cannot_create_or_modify_any_file_in_the_clone`
  before merging.

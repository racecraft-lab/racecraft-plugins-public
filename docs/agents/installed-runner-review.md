# Installed runner review notes

Issue #1307 fixes import setup at the installed workflow transport seam.
The regression checks the complete argv printed by both rendered skill trees,
then executes a separately constructed launcher argv from an external feature
directory, with no inherited import path. The same
launcher is used by both hosts and keeps the caller's working directory.

## Review fixes

The first Spec review identified contradictory Claude root guidance. The
transport now resolves the loaded skill's literal base directory on Claude
and the loaded skill file on Codex, using the parent of `skills/` on both.
A host-parity test locks that prerequisite down before the first runner call.

Release readiness also caught a dynamically parsed test executable. Daybreak
subsequently found that checking only the interpreter still allowed skill
text to choose executable arguments. The regression now requires the exact
two-element launcher contract before execution and constructs both executable
arguments independently of guidance text. Negative cases exercise the original
coverage test with forged success output across both hosts and all six skills.
The confinement rule and its allowlist are unchanged. Permission-probe fixtures
were updated to match the installed launcher invocation.

Transport comparison validates JSON results, exit codes and stderr, while
allowing only a nonnegative integer `data.duration_ms` to vary between separate
executions. Fifty deterministic timing cases retain failures for changed
results, exit codes, stderr, missing timing and invalid timing.

## Known limits

- A module selected with `-m` could be already importable, but a contributor's
  project module is absent from the empty feature worktree, and `PYTHONPATH`
  is removed. A relative project script is likewise absent. Both argv forms
  are now rejected before subprocess execution, even with forged success output.
- Another absolute plugin script requires control over a runnable plugin
  file. The test rejects alternative scripts, flags and noncanonical launcher
  spellings. Replacing, renaming or linking the canonical launcher itself
  requires changing the trusted runnable installation; guidance text alone
  cannot select such a target. Payload checks cover those runnable files.
- Runner checksum metadata attests the runner package, rather than every
  installed script. The launcher belongs to the trusted installed plugin;
  an attacker-controlled launcher requires compromise of that installation.
  Payload generation and consistency checks include the shipped launcher.
- The executable regression reads the entry-point argv in the shared skills.
  Inline reference commands and agent handoff paragraphs use the same
  launcher, but are not executed as independent shell commands. The current
  diff replaces each bare main-module call in installed workflow guidance.
- The runner's diagnostic replay fields retain their existing module format.
  Read-only helpers dispatch in-process; those fields do not spawn a child.
  Installed agents reuse the resolved launcher argv with each stdin request,
  as prescribed by the transport contract.
- Plugin-owned directories appear on the interpreter's import path. A
  conflicting module in that tree requires a modified trusted installation;
  the feature working directory is not added by the launcher.
- Entry-point argv is repeated at each skill and calling agent so the first
  call and agent handoff are explicit. Root resolution and transport rules
  have one reference; import setup lives in one launcher.
- The permission-probe prefix rule quotes the resolved launcher path. A call
  with different quoting can miss that prefix and prompt or be denied;
  the probe stops before phase work, so this mismatch fails closed.
- A complete live canary and interactive question flows were not exercised.
  Deterministic payload and workflow-binding tests cover this failure seam;
  live canary acceptance remains a separate check.
- Ripwire reports the new unittest methods as dead code despite their
  execution, and increased prose/class length as advisory verbosity. These
  are non-gating rows; no quality acknowledgements were added or changed.

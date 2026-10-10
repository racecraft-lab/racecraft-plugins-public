# Installed runner review notes

Issue #1307 fixes import setup at the installed workflow transport seam.
The regression executes the argv printed by both rendered skill trees from
an external feature directory, with no inherited import path. The same
launcher is used by both hosts and keeps the caller's working directory.

## Review fixes

The first Spec review identified contradictory Claude root guidance. The
transport now resolves the loaded skill's literal base directory on Claude
and the loaded skill file on Codex, using the parent of `skills/` on both.
A host-parity test locks that prerequisite down before the first runner call.

Release readiness also caught a dynamically parsed test executable. The
regression now asserts the documented interpreter and launches the documented
arguments with a statically resolved Python executable. The confinement rule
and its allowlist are unchanged. Permission-probe fixtures were updated to
match the installed launcher invocation.

## Known limits

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

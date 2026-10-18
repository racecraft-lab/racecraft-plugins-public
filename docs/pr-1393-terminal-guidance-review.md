# Terminal guidance gate review follow-up

## False pass in terminal guidance gate

F1393-10142fc4: substring checks accepted inert copies of required instructions
while the operative report, final label, or Codex polling instruction changed.
The gate now binds the complete reviewed rendered reference bytes separately
for Claude and Codex. It reads through the shipped host renderer and compares
independent, committed SHA-256 expectations. It does not search for a section
that an earlier comment, code fence, or shadow heading could conceal.

The reviewed instructions require the completed helper report unchanged,
followed by its final stop label. Codex additionally requires the initial long
yield, empty-input polling with the same session, and the long polling yield
only while the helper is running. Neither host's shipped behavior changes.

The mutation tests stage a changed rendered file in a disposable tree and
invoke the same gate used against the real render. With the old gate they
fail because corrupted instructions pass. With the repaired gate all variants
are rejected, while the actual rendered files pass.

Tests in `tests/speckit-pro/unit/test-plan-stage-terminal.py`:

| Variant | Regression test in `TerminalGuidanceGateMutationTests` |
| --- | --- |
| Claude report omitted or rewritten, original in an HTML comment | `test_claude_rejects_inert_completed_report` |
| Codex report omitted or rewritten, original in an HTML comment | `test_codex_rejects_inert_completed_report` |
| Either host's final stop label omitted or changed | `test_each_host_rejects_missing_or_changed_final_stop_label` |
| Codex long-poll text in a comment with short polling or no operative polling | `test_codex_rejects_inert_long_poll_instructions` |
| Shadow section in a comment, fence, quote, or template | `test_each_host_rejects_shadow_sections_and_other_inert_wrappers` |
| Report mode/field, unchanged-print instruction, final-line position, link, or heading rename | `test_each_host_rejects_other_terminal_fields_and_instruction_links` |
| Each Codex yield, tool, empty input, session binding, or running-state field | `test_codex_rejects_each_poll_field_change` |

## Known limits and pending checks

- The digest deliberately covers the entire reference, including Markdown
  context. Any reference edit requires review of both rendered files and an
  explicit expectation update. A digest is evidence of unchanged reviewed
  instructions, not an interpreter of arbitrary new prose. As with any test,
  changing the gate or its expectations requires code review.
- The spec review notes that guidance in other rendered files is outside
  this gate. This repair changes no instructions in those files, so it
  introduces no reachable path through them; their coverage is not claimed
  by the terminal-reference digest.
- F1393-5495a8f5 is outside this repair and remains unresolved by it. The
  source review records trusted-project overrides as Low because modifying
  that config already requires trusted config access; selected profiles and
  CLI overrides require operator action, and managed policy requires
  administrator control. These paths do not reach the guidance gate repaired
  here. This document does not claim that finding is resolved or accepted.
- R1393-6368ea4f (Low): the completed stop report links each artifact page
  as a CommonMark angle-bracket target (`plan_stage_terminal.py`), which
  cannot hold `<`, `>` or a newline. Unreachable in practice: page ids and
  titles come from the shipped gallery manifest, the feature directory is
  checked against the plan, spec and tasks paths, and the root is a resolved
  checkout. If hit, only the link markup degrades; the plain relative path
  stays readable.
- R1393-c9699449 (Info): on Windows the absolute link target would carry
  backslashes, which CommonMark may read as escapes. Unreachable: the
  autopilot documents no Windows host, and the Windows CI job is advisory
  smoke only.
- No live interactive question or tool execution is added or exercised.
  The existing rendered instructions are reviewed as the contract.
- Linux VM coverage does not establish native macOS plugin CI or the real
  sandbox tests
  `test_gate_hardening.py::test_pr_test_code_cannot_touch_the_host_under_the_real_sandbox`
  and
  `test_gate_hardening.py::test_pr_test_code_cannot_create_or_modify_any_file_in_the_clone`.
  Those remain for the orchestrator before merging.
- Daybreak must re-check the pushed fix and include its full commit SHA in
  the receipt before F1393-10142fc4 can be resolved.

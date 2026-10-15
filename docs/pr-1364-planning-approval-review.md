# Recorded planning approval security follow-up

PR #1364, finding F1364-4f87a096: planning digest false pass. Workflow
normalization discarded checkbox state even for planning choices under ordinary
headings. The shared runner now preserves checked versus unchecked state and
normalizes only the spelling of a checked marker (`x` versus `X`). Code fences
preserve all input bytes, including execution-row lookalikes. Both hosts ship
the same runner implementation.

The regression tests exercise manifest, record and verify through the public
runner request seam. They cover lowercase and uppercase checks, nested lines,
ordinary headings, checked-marker spelling, execution rows and sections, fenced
checkboxes, and planning-choice text. Each preserved-input case also flips a
planning choice after the excluded region and requires a new digest and refusal
of the old approval. These boundary assertions fail on the pre-fix helper;
the accepted bookkeeping/spelling assertions already passed there.

## Known limits

- Unfenced `Stage` and `Draft PR` table rows are declared execution bookkeeping
  and excluded. A planning directive placed in these rows uses a field outside
  its intended purpose; this accepted Low limit is unchanged.
- `Implementation Progress` and `Feedback Sweep Log`, including their nested
  subsections, are declared execution bookkeeping and excluded. Put planning
  decisions under ordinary planning headings. These accepted Info limits are
  unchanged.
- `x` and `X` both represent checked choices. Their spelling alone does not
  change the plan. Fenced spelling and text remain verbatim planning inputs.
- This repair addresses the Daybreak planning-digest false-pass class. It does
  not resolve the separate code-review finding about execution progress that
  unnecessarily invalidates approvals, or reopen prior accepted Low/Info notes.
- Approval assurance remains recorded, without protection against an agent with
  the operator's file access. Interactive confirmation is covered by its JSON
  contract, not a live UI exercise.
- Linux VM evidence does not establish native macOS plugin CI or the two real
  sandbox checks:
  `test_gate_hardening.py::test_pr_test_code_cannot_touch_the_host_under_the_real_sandbox`
  and
  `test_gate_hardening.py::test_pr_test_code_cannot_create_or_modify_any_file_in_the_clone`.
  Those remain orchestrator checks before merge. The finding remains open until
  a later Daybreak re-check includes the fix commits and resolves every variant.

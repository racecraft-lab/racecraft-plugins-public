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

## Assurance guard follow-up

Finding F1364-e793efeb is a tamper-proof assurance gate false pass. The guard
previously accepted any negation anywhere on the same line as an assurance
term. It now checks each sentence independently and accepts an assurance term
only in a complete, explicit denial: `The approval is not <term>` or
`Nothing may describe it as <term>`. The term may be hyphenated, spaced or
unhyphenated, with case ignored. All other sentences containing the term fail.
An unrelated negation, a qualified negation, or a second positive claim cannot
borrow the exemption from a denial.
Markdown soft line breaks stay inside their sentence, so a wrapped qualifier
or a preceding `The following statement is false:` cannot detach from a denial.

`AssuranceGuardTest` injects document text into the actual public-document
guard. Its named tests cover following and preceding negations; all spellings;
genuine denials followed or preceded by positive claims; double negation and
`not only`; sentence, clause and line boundaries; and each scanned public
surface independently. The scan includes the shared skill/reference, agent
source, Codex descriptor/agent, and both generated host payloads. The existing
runner tests continue to exercise the source and both shipped hosts.

## Known limits

- The assurance guard recognizes the two explicit denial forms above, rather
  than inferring arbitrary English negation. Other denial wordings fail closed
  and must use a recognized form or avoid the assurance term. Existing approval
  guidance satisfies this narrow rule. This repository-only guard change does
  not alter runtime policy or either host's generated payload.
- Unfenced `Stage` and `Draft PR` table rows are declared execution bookkeeping
  and excluded. A planning directive placed in these rows uses a field outside
  its intended purpose; this accepted Low limit is unchanged.
- `Implementation Progress` and `Feedback Sweep Log`, including their nested
  subsections, are declared execution bookkeeping and excluded. Put planning
  decisions under ordinary planning headings. These accepted Info limits are
  unchanged.
- `x` and `X` both represent checked choices. Their spelling alone does not
  change the plan. Fenced spelling and text remain verbatim planning inputs.
  This equivalence holds only for `-` bullets; `*`, `+`, numbered and
  blockquoted checkboxes bind the spelling, which fails closed.
- The assurance guard splits sentences at `.`, `!` and `?` before it looks for
  the assurance term. A term joined by one of those marks, split by an inline
  HTML tag such as `<wbr>` or `<em>`, written as an HTML entity, or spelled
  with a look-alike letter from another alphabet is not recognized. No scanned
  document uses such a spelling today, so this Low limit is accepted.
- The execution-section skip ends only at an unindented ATX heading of the same
  or a higher level. An `Implementation Progress` heading followed by planning
  lines under deeper headings, an indented or setext heading after it, or an
  unclosed fence would hide later planning lines. The shipped workflow template
  cannot produce this: `### Implementation Progress` is the last subsection of
  `## Phase 7: Implement` and is closed by the unindented
  `## Post-Implementation Checklist`. No code places `Feedback Sweep Log`; the
  sweep protocol tells the agent where to write it. When the file has a
  `Consensus Resolution Log` heading, the log is written as its sibling at the
  same level, so the next sibling or higher heading closes it. Otherwise the
  agent appends `## Feedback Sweep Log` at the end of the file, and no current
  writer adds planning text after it. Accepted Low.
- These repairs address the Daybreak planning-digest and assurance-guard
  false-pass classes. They do
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

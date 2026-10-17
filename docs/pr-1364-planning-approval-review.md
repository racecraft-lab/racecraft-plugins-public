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

## Declared progress follow-up

R1364-089042f4 and its separator variant R1364-225d0ebf are repaired in the
shared planning-approval owner. Tests start with the shipped workflow and spec
map templates, record approval, make each edit separately, and require both
the same manifest digest and successful verification of the original record.

| Declared progress | Planning input still bound |
| --- | --- |
| Workflow Overview status cells | Phase names, commands, notes and neighboring choices |
| Post-Implementation Checklist status cells | Checklist requirements and evidence |
| Formal Checkpoints result cells and canonical result-record paths | Checkpoint definitions, arbitrary evidence text and formal selection |
| Plain Lessons Learned bullets, directly or in the template's lesson subsections | Prose, checkbox choices, fences and neighboring planning sections |
| Feature SPEC-MOC frontmatter status | Other metadata, body text and status lookalikes outside frontmatter |
| Blank separator before an appended Feedback Sweep Log | Preceding planning content and choices after the excluded section |

Recognized phase and map status values alone are normalized; unexpected cell
contents stay bound. Formal checkpoint rows use the formal owner's row names
and result paths. Their identifier-valued results, canonical result/waiver paths
and template setup gap are progress; arbitrary evidence prose stays bound.
The regression matrix also invokes the actual checkpoint row writer for Final
and Post results, without claiming to run a model checker.
Lessons normalization does not extend into arbitrary subsections or
fenced examples. SPEC-MOC normalization applies only to the feature's own map,
not every file sharing that basename. Trailing blank separator lines outside
fences are normalized so creating the end-of-file sweep log preserves approval.
The earlier checkbox-choice and assurance-claim regression matrices remain in
the same test file. Source and both generated host payloads exercise the new
cases through the public manifest, record and verify request seam.

## Known limits

- Ripwire's static caller graph reports dynamically discovered unittest methods
  as dead code. The focused suite executes them through the standard unittest
  loader, including the shipped-host matrix. These rows are reported in the
  hand-back rather than suppressed in the acknowledgement ledger; a zero exit
  and zero gating rows do not establish zero advisory major rows.
- Other post-approval edits remain bound: Overview summary notes, Post evidence
  and newly added rows, Success Criteria checkbox choices, Constitution text,
  and generated SPEC-MOC blocks. They may contain requirements or approved
  decisions, so this repair does not discard them wholesale. Status spellings
  outside the normalizer's declared vocabulary fail closed, including the
  alternative skipped icons accepted elsewhere by the workflow reader.
- A manually added horizontal rule before Feedback Sweep Log remains bound.
  The no-anchor protocol appends the heading with a blank separator, not a
  horizontal rule; no current writer requires the latter layout.
- The formal row writer rewrites the whole workflow with LF and a final
  newline. CRLF, missing final newlines or unusual Unicode line separators
  may therefore change other bound bytes. A missing checkpoint row can cause
  a new table to be appended; a row under a deeper heading stays bound. The
  shipped template uses LF, a final newline and all four rows directly under
  Formal Checkpoints, so none of these layouts is scaffold-produced.
- A workflow path alias, including a symlink or a leading `./`, can give the
  formal writer a different result-path key from the approval helper's
  canonical path. That result path stays bound and fails closed. Scaffold
  supplies the canonical repository-relative workflow path.
- A blank separator inserted before a mid-file Feedback Sweep Log can remain
  bound. The template has no Consensus Resolution Log anchor, so its sweep
  takes the covered end-of-file path. A later agent-authored anchor and its
  separator layout are not produced by a deterministic writer.
- The host matrix uses the source checkpoint row writer with each packaged
  approval helper. Both packaged writers are byte-identical to source;
  generated-artifact validation enforces that parity. This is not a live
  formal model-checker run on either host.
- The assurance guard recognizes the two explicit denial forms above, rather
  than inferring arbitrary English negation. Other denial wordings fail closed
  and must use a recognized form or avoid the assurance term. Existing approval
  guidance satisfies this narrow rule. This repository-only guard change does
  not alter runtime policy or either host's generated payload.
- Unfenced `Stage` and `Draft PR` table rows are declared execution bookkeeping
  and excluded. A planning directive placed in these rows uses a field outside
  its intended purpose; this accepted Low limit is unchanged.
- Plain bullets directly under `Lessons Learned`, or under its three template
  subsections, are dropped whatever they say. The autopilot writes lessons
  after implementation, and no planning step writes there. A planning
  directive placed in a lesson bullet uses the section outside its purpose,
  like the `Stage` row limit. Accepted Low.
- A Formal Checkpoints status cell is erased for any lowercase identifier when
  its evidence cell is `No selected model` or the owner's result path.
  `checkpoint_signal` reads that live text, so a text-only edit to `pass`
  after approval can change `planning_complete` with the same digest. The
  approval does not vouch for that edit: formal selection stays bound, the
  gate reads the current text, and checker verdicts are not planning inputs.
  Accepted Info; the Daybreak re-check should confirm it.
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
- The declared-progress repair partly addresses the separate code-review
  false-refusal finding. The cross-host review of `00f2fda7` keeps it open
  for writes that a resume can still meet, such as the Implement Checklist
  Gate and the Quality Gates `Hardener` line; it does not accept those writes,
  or the alternative status icons, as limits. Prior accepted Low/Info notes
  remain unchanged;
  this repair does not claim a new independent Daybreak security verdict.
- Approval assurance remains recorded, without protection against an agent with
  the operator's file access. Interactive confirmation is covered by its JSON
  contract, not a live UI exercise.
- Linux VM evidence does not establish native macOS plugin CI or the two real
  sandbox checks:
  `test_gate_hardening.py::test_pr_test_code_cannot_touch_the_host_under_the_real_sandbox`
  and
  `test_gate_hardening.py::test_pr_test_code_cannot_create_or_modify_any_file_in_the_clone`.
  Those remain orchestrator checks before merge. The widened normalization
  still requires the separate Daybreak re-check of this repair.

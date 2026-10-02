# Scaffold proposes the quality-gates file; autopilot runs on unratified defaults without it

Status: accepted

`.specify/quality-gates.json` stays the threshold authority for the COMPLEXITY, MUTATION and DEPENDENCY_RULES slots, the repository's skips, and its opt-in slots. Two things change. Scaffold now writes it, and a missing or invalid file no longer stops autopilot.

**Scaffold measures, proposes and confirms.** Every scaffold checks the file. When it is missing or invalid, scaffold runs the coach's measurement flow: a complexity ceiling that about 90 percent of measured functions pass, the shipped CRAP ceiling (30) and mutation-score floor (60), or the NIST ceiling of 10 when nothing can be measured. It shows the proposal and the files that would fail it today, asks once, and writes the file only on a yes. A decline writes nothing, and the next scaffold offers again; no decline is stored. The coach flow remains the way to change the file later. So any file on disk is one the user confirmed, and the schema needs no ratified field.

**Autopilot runs on unratified defaults.** When G0 finds the file missing or invalid, autopilot uses the shipped defaults (complexity 10, CRAP 30, mutation-score floor 60, no skips, no opt-in slots) in memory and never writes the file. An invalid file is ignored whole, never salvaged section by section. The run records "unratified defaults" (with the first validation problem, if any) in the readiness record and the decisions list, and the PR body and UAT runbook flag it. Agents still never edit the file on their own.

The old rule hard-stopped G0 on a missing or invalid file and only the coach flow could create it. Scaffold never checked, so a clean scaffold reached a G0 stop within a minute. That broke the promise that planning never stops except for a security question.

## Considered Options

- **Scaffold writes the shipped defaults unmeasured, marked unratified.** Rejected: COMPLEXITY and MUTATION judge every function in each changed file, so a ceiling of 10 on an older codebase fails any SPEC that touches a file holding an older complex function, and the retry ladder turns those into blocked-for-UAT tasks.
- **Scaffold points the user to the coach flow.** Rejected: a second interactive skill per SPEC, against the promise that scaffold is the only one.
- **Autopilot measures and writes the file itself.** Rejected: it makes an agent, unconfirmed, a writer of the threshold authority.
- **Keep the G0 hard stop.** Rejected: it stops planning for a non-security reason.
- **Salvage the valid sections of an invalid file.** Rejected: per-section trust rules for a rare case; one predictable fallback is simpler.
- **Store a decline so scaffold stops asking.** Rejected: new state to keep for at most one question per scaffold.

## Consequences

- A run on unratified defaults in an older codebase may block tasks on whole-file complexity; the UAT flag tells the reviewer why and points at the coach flow.
- The readiness record carries the quality-gates source (file, or unratified defaults with the reason); its exact fields belong to the readiness record decision.
- The canary's scaffold answers file must pre-answer this confirmation.

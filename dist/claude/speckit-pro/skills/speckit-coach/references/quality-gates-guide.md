# Quality Gates Guide

Use this reference when autopilot's G0 stops on a missing or invalid
`.specify/quality-gates.json`, or when a user asks what the complexity,
mutation, and dependency gates should be set to. The file is the authority
for the thresholds the `COMPLEXITY`, `MUTATION`, and `DEPENDENCY_RULES` slots
run against and for permanent repository-wide skips. The operator owns it:
agents never edit it, and this flow ends with the operator confirming the
proposed content before it is written.

## What the file holds

```json
{
  "schema_version": "1.0",
  "thresholds": { "complexity": 8, "crap": 30, "mutation_score_floor": 60 },
  "skips": { "MUTATION": { "reason": "no mutation harness yet", "recorded": "2026-09-06" } },
  "basis": { "method": "percentile-90", "measured_functions": 120, "recorded": "2026-09-06" }
}
```

| Field | Meaning |
|---|---|
| `thresholds.complexity` | Maximum cyclomatic complexity per changed function (integer, at least 1). |
| `thresholds.crap` | Maximum CRAP score per changed function (number above 0). CRAP is `cc² × (1 − coverage)³ + cc`, so a well-tested complex function still passes. |
| `thresholds.mutation_score_floor` | Minimum mutation score in percent; the tool receives `100 − floor` as its survival ceiling. |
| `skips` | Permanent skips keyed by slot with a reason. A skipped slot is `N/A` in every workflow without asking. Optional. |
| `basis` | How the thresholds were chosen. Optional, but record it so the next reviewer knows whether the ceiling was measured or guessed. |

The schema lives at `speckit_pro_runner/contracts/quality-gates.schema.json`;
`resolved_python -m speckit_pro_runner.quality_gates validate` checks a file with the
standard library only.

## Recommend a complexity ceiling from the code that exists

Recommend the smallest ceiling that lets about 90 percent of the repository's
existing functions pass. A ceiling below that turns the first implementation
phase into a refactoring project the spec never asked for; a ceiling above it
gates nothing. Measure, do not guess:

1. Confirm the complexity tool is installed (`radon` for Python, `eslint` for
   TypeScript). If it is not, offer the install command from the discovery
   table and, if the operator declines, use the no-code fallback below.
2. Run the shipped CRAP script with lenient ceilings over the whole source
   tree, tests excluded, writing a report. Run the repository's coverage step
   first so the report can join coverage (the slot command in the discovery
   table shows the exact coverage invocation for this stack):

   ```text
   resolved_python <plugin-root>/scripts/crap-score.py --language python \
     --ceiling 1000000 --complexity-ceiling 1000000 \
     --report /tmp/crap-report.json -- <source files>
   ```

3. Turn the report into a proposed file:

   ```text
   resolved_python -m speckit_pro_runner.quality_gates recommend /tmp/crap-report.json
   ```

   The output carries `basis.method: percentile-90` and the measured function
   count. `crap` and `mutation_score_floor` come out at the shipped defaults
   (30 and 60); adjust them only with a reason the operator states.
4. Show the proposed content and the functions that would fail it today.
   Write `.specify/quality-gates.json` only after the operator confirms.

**No-code fallback.** When nothing can be measured (tool declined, empty
repository, greenfield), propose Robert Martin's six as the complexity
ceiling with `basis.method: bobs-six`, and say plainly that it was not
measured. The `recommend` command does this on its own when the report has no
functions.

## Record a permanent skip

When the operator answers "skip this repo" to autopilot's missing-tool
question, the durable record is a `skips` entry in this file, not the
workflow table. Add the slot with a one-line reason and today's date, validate,
and confirm before writing. Remove the entry when the tool arrives; autopilot
re-populates the slot on the next run.

## Recovering from a G0 stop

G0 fails with a message that names `.specify/quality-gates.json` and this
flow. Create the file as above, re-run autopilot, and let Step 0.11 re-read
it. Do not paste thresholds into the workflow file to get past the gate; the
runner reads only this file.

# Quality Gates Guide

Use this reference when autopilot's G0 stops on a missing or invalid
`.specify/quality-gates.json`, or when a user asks what the complexity,
mutation, and dependency gates should be set to. The file is the authority
for the thresholds the `COMPLEXITY`, `MUTATION`, and `DEPENDENCY_RULES` slots
run against, for permanent repository-wide skips, and for which advisory slots
block. The operator owns it:
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
| `thresholds.mutation_score_floor` | Minimum mutation score in percent. cosmic-ray receives `100 − floor` as its survival ceiling; for StrykerJS the slot chains `scripts/mutation-score.py`, which reads `reports/mutation/mutation.json` and fails below the floor, because Stryker's default `thresholds.break` is `null` and never fails a run. |
| `skips` | Permanent skips keyed by slot with a reason. A skipped slot is `N/A` in every workflow without asking. Optional. |
| `enforce` | Advisory slots this repository opts in to blocking on. Only `DEPENDENCY_AUDIT` is advisory today. Optional. |
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
   TypeScript, `oxlint` for a Bun project with a `bun.lock`). If it is not,
   offer the install command from the discovery table and, if the operator
   declines, use the no-code fallback below. Python tools install with
   `pipx install` (or `uv tool install`), never a bare `pip install`, which
   PEP 668 refuses on externally managed interpreters. `coverage` is the
   exception: `coverage run -m pytest` must share pytest's interpreter, so
   add it to the project's own dev dependencies instead. A Bun project passes
   `--complexity-tool oxlint --coverage-lcov coverage/lcov.info` so the report
   joins the lcov that `bun test --coverage` writes; oxlint needs no TypeScript
   compiler API, so it also measures TypeScript 7 code.
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

**The gates judge whole files.** After G0, `COMPLEXITY` and `MUTATION` run
on every changed source file, and they check every function in each one,
not only the changed lines. So a spec that edits one line of a file holding
an older function over the ceiling fails its phase verification until that
function comes under the ceiling. When you show the proposal, name the
files that hold today's failing functions. A spec that touches one of them
must plan the refactor in its tasks.

**No-code fallback.** When nothing can be measured (tool declined, empty
repository, greenfield), propose 10 as the complexity ceiling with
`basis.method: nist-235`, and say plainly that it was not measured.
[NIST SP 500-235](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication500-235.pdf)
(McCabe and Watson, *Structured Testing*, 1996):
"Limit the cyclomatic complexity of modules to 10 wherever possible without
violating other good design principles, and document any exceptions"; it
notes that limits as high as 15 have been used successfully. The `recommend`
command does this on its own when the report has no functions. A file that
still records `bobs-six` from an earlier release stays valid.

**If radon stops working.** radon's last release was 6.0.1 in March 2023, so
a new Python grammar may eventually break it. The fallback analyzer is
[`lizard`](https://github.com/terryyin/lizard), which is actively released
and measures cyclomatic complexity for Python and many other languages. It
does not emit radon's per-function JSON, so the CRAP join in `crap-score.py`
cannot read it yet: use it to measure the ceiling by hand, record
`basis.method: operator`, and raise an issue for the CRAP join.

## The advisory dependency audit

`DEPENDENCY_AUDIT` checks dependencies for known vulnerabilities when the
repository carries the matching signal: `pip-audit` for `requirements.txt` or
`pyproject.toml`, `bun audit`, `pnpm audit`, or `npm audit` at level high for
the matching lockfile, `govulncheck ./...` for `go.mod`, and `cargo audit` for
`Cargo.lock`. It is advisory: autopilot records the result, never blocks on
it, and never asks about a missing tool. To make it block, add
`"enforce": ["DEPENDENCY_AUDIT"]` to this file; it then behaves like
`DEPENDENCY_RULES`. These tools query an online advisory database, so an
enforced audit also fails when the network does. Whether `bun audit` exits
non-zero on a finding at `--audit-level=high` is not verified; check it
before enforcing the slot on a Bun project.

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

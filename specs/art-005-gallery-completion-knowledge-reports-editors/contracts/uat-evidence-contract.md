# Contract: UAT Evidence

ART-005 preserves active UAT evidence during implementation and archives it
after merge.

## Active Paths

```text
specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-runbook.md
specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md
specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.json
```

The files grow serially in slice order. Slice 1 creates them; slices 2 through 7
modify them.

## Archival Paths

```text
docs/ai/specs/.process/ART-005-uat-runbook.md
docs/ai/specs/.process/ART-005-uat-results.md
docs/ai/specs/.process/ART-005-uat-results.json
docs/ai/specs/.process/ART-005-uat-harness/
```

The harness directory is used only if implementation proves a committed browser
harness necessary.

## JSON Run Schema

Top-level fields:

- `featureId`
- `sourceCommit`
- `executedAt`
- `environment`
- `driver`
- `runbookPath`
- `rows`

`environment` includes:

- operating system
- browser name and version
- `file://` scheme
- network condition
- theme condition
- reduced-motion condition
- color-mode condition

`driver` is `manual` or the repository-relative path of the exact harness.

## Row Schema

Every row has:

- `artifactId`
- `templatePath`
- `step`
- `claim`
- `observedResult`
- `verdict`
- `date`
- `driver`

`verdict` is `pass`, `fail`, or `not_applicable`. A `not_applicable` verdict
still includes an observation proving why the check does not apply.

## Required Matrix

Every artifact has rows for:

- direct `file://` open
- complete representative content
- offline reload
- complete keyboard traversal
- visible focus
- light/dark theme parity
- reduced-motion behavior
- color-independent meaning
- named keyboard-focusable horizontal scroll region where present

Every editor additionally has rows for:

- live-state serialization
- genuine clipboard success with read-back or paste equality
- forced unavailable clipboard fallback
- rejected promise fallback
- synchronous throw fallback

The Markdown summary reports totals and identifies the exact source commit
represented by the JSON rows.

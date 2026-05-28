# Quickstart: `generate-uat-skeleton.sh` (standalone)

For maintainers who want to run the UAT skeleton generator by hand — outside the
autopilot loop — to inspect or regenerate a runbook. The autopilot calls this
script automatically during post-implementation; you rarely need to run it
manually, but this is how when you do.

## Prerequisites

- `jq` on PATH (already a hard prerequisite for the autopilot).
- A `spec.md` to parse. Any SpecKit spec works — one with `### User Story`
  headings (story-keyed runbook) or an infrastructure spec with none
  (FR/SC-keyed runbook with a fallback note).

## 1. Minimal run (no env, no workflow file)

From the repository root:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh \
  specs/004-integration-verification/spec.md \
  /tmp/runbook.md
```

What you get:
- A `uat-runbook.md` at `/tmp/runbook.md` with every section header in the fixed
  order (Header, Env Setup, Per-Story Acceptance Tests, FR Coverage Matrix,
  Negative-Path Tests, Self-Review Findings, Sign-off, Rollback).
- Env Setup shows `<unknown — autopilot did not pass PROJECT_COMMANDS>`
  placeholders (no `UAT_PROJECT_COMMANDS` supplied).
- Self-Review Findings shows the stub line
  `**Self-Review:** <not available — workflow file not provided>`
  (no `--workflow-file` supplied).
- The script prints **nothing** to stdout. Diagnostics (if any) go to stderr.

Verify the story count matches the spec (SC-001):

```bash
diff \
  <(grep -c '^### User Story' specs/004-integration-verification/spec.md) \
  <(grep -c '^### User Story' /tmp/runbook.md || true)
```

## 2. Full run (env + workflow file — mimics the autopilot)

```bash
UAT_PROJECT_COMMANDS='{"BUILD":"make","UNIT_TEST":"make test","LINT":"shellcheck"}' \
bash speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh \
  specs/006a-uat-skeleton/spec.md \
  specs/006a-uat-skeleton/uat-runbook.md \
  --workflow-file docs/ai/specs/SPEC-006a-workflow.md
```

What changes vs the minimal run:
- Env Setup renders the build/test/lint commands from the JSON instead of
  placeholders.
- Self-Review Findings echoes the `## Self-Review` block extracted from the
  workflow file (if that heading exists; otherwise the stub line).

## 3. Confirm deterministic overwrite (US3 / FR-007)

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh \
  specs/004-integration-verification/spec.md /tmp/run1.md
bash speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh \
  specs/004-integration-verification/spec.md /tmp/run2.md
diff /tmp/run1.md /tmp/run2.md && echo "byte-identical: deterministic OK"
```

A hand-edit to `/tmp/run1.md` followed by a re-run overwrites it — no merge, no
append, no skip-if-present.

## 4. Exit-code spot checks (FR-006)

```bash
# Usage error (missing argv[2]) -> exit 2
bash .../generate-uat-skeleton.sh specs/004-integration-verification/spec.md; echo "exit=$?"

# Unreadable spec -> exit 1, no partial output
bash .../generate-uat-skeleton.sh /nonexistent/spec.md /tmp/out.md; echo "exit=$?"
test -f /tmp/out.md && echo "BUG: partial output written" || echo "no partial output: OK"
```

## 5. Run the unit test (SC-003)

```bash
cd speckit-pro && bash tests/run-all.sh --layer 4
```

The new `test-generate-uat-skeleton.sh` is auto-discovered. It exercises five
fixtures: the vendored full-spec snapshot
(`tests/layer4-scripts/fixtures/spec-full-snapshot.md`, read from disk, never
the live spec), plus synthetic zero-stories, duplicate-FR, clarification-marker,
and missing-spec cases.

## See also

- CLI contract: [`contracts/generate-uat-skeleton-cli.md`](./contracts/generate-uat-skeleton-cli.md)
- Plan (decisions + FR-013 wiring): [`plan.md`](./plan.md)
- Design concept (locked decisions Q1-Q4): `docs/ai/specs/SPEC-006a-design-concept.md`

# Gate Validation Reference

Programmatic gate checks performed after each SDD phase. The autopilot validates each gate automatically and attempts auto-fix if validation fails (max 2 attempts before escalating to human).

## Gate Definitions

### G0 — Prerequisites (Before Specify)

**Check:** Constitution principles validated against the current codebase.

```
1. TYPECHECK command → must pass (0 errors)
2. UNIT_TEST + INTEGRATION_TEST commands → must pass (record count as baseline)
3. BUILD command → must pass
4. LINT command → must pass
(use PROJECT_COMMANDS discovered in Step 0.10)
5. Architecture patterns verified (e.g., definitions/primitives split exists)
6. Workflow file's Prerequisites table filled with baselines
7. Constitution Check summary line set to "✅ Verified"
```

**Auto-Fix:** Not applicable — if the codebase doesn't pass typecheck/test/build, the user must fix it before starting a new spec workflow. These are foundational health checks.

**Failure Escalation:** Immediate STOP. Report which checks failed with output. The user must resolve codebase issues before autopilot can proceed.

### G1 — After Specify

**Check:** Determine if clarification is needed.

```
Search spec.md for "[NEEDS CLARIFICATION]" markers.
- If markers found → Proceed to Clarify phase
- If no markers → Skip Clarify, proceed to Plan
```

This is a routing decision, not a pass/fail gate. The presence of markers is expected and normal.

### G2 — After Clarify

**Check:** All ambiguities resolved, no human review flags.

```
1. grep -c "NEEDS CLARIFICATION" spec.md → must be 0
2. grep -c "HUMAN REVIEW NEEDED" spec.md → must be 0
3. Clarifications section exists in spec.md with documented decisions
```

**Auto-Fix:** Re-run clarify focused on remaining markers. Spawn consensus agents for each unresolved question.

**Failure Escalation:** If markers remain after 2 clarify attempts, STOP. Present remaining ambiguities to human with all 3 agent perspectives.

### G3 — After Plan

**Check:** Required artifacts exist and constitution gates pass.

```
1. Verify plan.md exists and is non-empty
2. Verify research.md exists (may be brief for simple specs)
3. Verify data-model.md exists (if spec has data entities)
4. Search plan.md for "FAIL" in constitutional gate sections
5. Verify no unresolved "[TODO]" markers in plan.md
```

**Auto-Fix:** Re-run plan with gate failure as additional context. If a specific constitutional gate failed, include the principle text and ask the planner to address it.

**Failure Escalation:** If constitutional gates continue to fail after 2 attempts, STOP. Present the gate failure with the specific principle and proposed architecture for human review.

### G4 — After Checklist

**Check:** All gap markers resolved across all checklist files.

```
1. Find all checklist files: specs/<feature>/checklists/*.md
2. Count [Gap] markers across ALL files: grep -c "\[Gap\]" checklists/*.md
3. Total must be 0
```

**Auto-Fix:** This is the **Checklist Gap Remediation Loop**.
Runs after each domain subagent returns (not batched — see
SKILL.md Rule 6).

```text
For EACH [Gap] marker found after a domain subagent:

Step 1: Research the gap using multiple tools:
  a. context_builder(response_type: "question") — ask
     "How should we close this gap?" with the gap text,
     spec.md excerpt, and plan.md excerpt as context.
     RepoPrompt explores the codebase for established
     patterns and proposes an evidence-grounded fix.
  b. Tavily search (mcp__tavily-mcp__tavily-search) —
     search for API docs, standards, or best practices
     relevant to the gap (e.g., OmniJS behavior, MCP
     patterns, error handling standards)
  c. Read constitution + prior specs — check if project
     principles or precedent decisions address the gap

Step 2: Determine the fix:
  - Which artifact to edit (spec.md, plan.md, or both)
  - What exact text to add or modify
  - Where in the artifact the edit goes (section name)

Step 3: Apply the fix to the relevant artifact(s)

Step 4: Re-run the domain checklist to verify the gap
  is closed
  - If new gaps appear → remediate (max 2 total loops
    per domain)
  - If 0 gaps → domain complete, proceed to next domain

Step 5: If gaps remain after 2 loops → STOP, present
  to human with the gap description, research findings,
  and attempted fixes
```

**Why research + consensus:** Gaps often require understanding
both what the codebase already does (context_builder) AND what
the API/standard requires (Tavily). Using multiple research
sources produces higher-quality fixes than guessing.

**Critical:** Run gap remediation sequentially (one gap at a
time) to prevent conflicting spec edits.

### G5 — After Tasks

**Check:** Every functional requirement has at least one task.

```
1. Extract all FR-XXX markers from spec.md
2. For each FR-XXX, verify it appears in tasks.md
3. Verify task dependency ordering makes sense (no forward references)
4. Verify [P] markers are only on genuinely parallel-safe tasks
```

**Auto-Fix:** For each unmapped FR:
- Generate a task that covers the requirement
- Place it in the appropriate user story phase
- Ensure it has the correct FR reference marker

**Failure Escalation:** If coverage gaps persist after 2 attempts, STOP. Present the unmapped FRs with the relevant spec sections.

### G6 — After Analyze

**Check:** All findings remediated at every severity level.

```
1. Run /speckit.analyze and capture output
2. Count findings by severity (CRITICAL, HIGH, MEDIUM, LOW)
3. ALL findings must be remediated — none left unresolved
```

**Auto-Fix:** This is the **Analyze Remediation Loop**. Uses
the same research + consensus workflow as Checklist Gap
Remediation.

```text
Step 1: Run /speckit.analyze (via phase-executor subagent)
Step 2: Parse ALL findings by severity

Step 3: For EACH finding (CRITICAL, HIGH, MEDIUM, LOW):

  a. Research the finding using multiple tools:
     - context_builder(response_type: "question") — ask
       "How should we fix this finding?" with the finding
       text, spec.md/plan.md/tasks.md excerpts as context.
       RepoPrompt explores the codebase for established
       patterns and proposes an evidence-grounded fix.
     - Tavily search (mcp__tavily-mcp__tavily-search) —
       search for API docs, standards, or best practices
       relevant to the finding
     - Read constitution + prior specs — check if project
       principles or precedent decisions inform the fix

  b. Determine the fix:
     - Which artifact to edit (tasks.md, spec.md, plan.md)
     - What exact change to make (add task, amend task,
       edit requirement, fix coverage gap, remove stale
       marker, etc.)
     - Cite the research source supporting the fix

  c. Apply the fix to the relevant artifact(s)

Step 4: Re-run analyze to verify all findings resolved
  - If new findings appear → remediate (max 2 total loops)
  - If 0 findings → G6 PASS

Step 5: If findings remain after 2 loops → STOP, present
  to human with all remaining findings, research results,
  and attempted fixes
```

**Why remediate everything:** The autopilot runs unattended.
Leaving MEDIUM/LOW issues for "post-hoc review" means they
never get fixed. Fixing all findings produces cleaner
artifacts and prevents issues from compounding during
implementation.

### G7 — After Implement

**Check:** Full verification suite passes, TDD was followed,
and no placeholder tests exist.

```
1. Run BUILD command → must pass
2. Run TYPECHECK command → must pass (skip if N/A)
3. Run LINT command → must pass
4. Run UNIT_TEST command → must pass
5. Run INTEGRATION_TEST command separately → must pass.
   Many projects exclude integration tests from the default
   test command — you MUST run both.
(use PROJECT_COMMANDS discovered in Step 0.10)
6. Verify spec-specific integration tests exist:
   Glob("tests/integration/*<spec-name>*") → must find files
7. Verify test count increased from G0 baseline
8. Verify NO placeholder tests in new files:
   Grep("it\.todo\(|test\.todo\(|it\.skip\(|xit\(|xtest\(|xit\(",
        path: "specs/<number>-<name>/") → must be 0
   Grep("it\.todo\(|test\.todo\(|it\.skip\(|xit\(",
        path: "tests/integration/*<spec-name>*") → must be 0
9. ALL must pass for G7 to pass
```

**Placeholder Test Check:** `it.todo()`, `it.skip()`,
`xit()`, `test.todo()`, and empty test bodies are NOT real
tests. They don't fail during RED and don't verify behavior
during GREEN. If ANY are found in spec-related files, G7
FAILS. The implement-executor must replace them with real
assertions.

**TDD Verification:** The implement-executor's summary
includes RED→GREEN evidence for each task. If the summary
shows implementation without RED phase verification (real
assertion failures, not "skipped" or "todo"), the gate
FAILS — re-run the Implement phase.

**Integration Test Requirement:** Spec-specific integration
tests MUST exist with real assertions. If missing or all
placeholders, spawn implement-executor to create/fix them
before G7 can pass.

**Auto-Fix:**
- Build failures: Check for syntax errors, missing imports
- Type errors: Fix type mismatches, add missing types
- Lint errors: Run LINT_FIX command
- Test failures: Fix failing tests or implementation bugs
- Missing integration tests: Spawn implement-executor

**After G7 passes:** Run full integration suite (Step 3.1),
then push branch and create PR via `gh pr create`.

**Failure Escalation:** If verification suite fails after 2 fix attempts, STOP. Present the specific failures to human.

## Gate Summary Table

| Gate | After | Check | Auto-Fix Strategy | Max Attempts |
|------|-------|-------|-------------------|--------------|
| G1 | Specify | NEEDS CLARIFICATION markers | N/A (routing) | N/A |
| G2 | Clarify | 0 markers remain | Re-run clarify | 2 |
| G3 | Plan | Artifacts exist, gates pass | Re-run plan | 2 |
| G4 | Checklist | 0 [Gap] markers | context_builder remediation | 2 |
| G5 | Tasks | All FRs mapped to tasks | Generate missing tasks | 2 |
| G6 | Analyze | 0 findings (all severities) | context_builder remediation | 2 |
| G7 | Implement | Build+type+lint+test pass, integration tests exist, 0 placeholders, TDD evidence | Fix errors, replace placeholders, create real tests | 2 |

## Optional: Extension Verification at G7

If the `verify` extension is installed, the autopilot can
run `speckit.verify` as additional validation alongside
the standard G7 checks. This validates the implementation
against spec artifacts from the extension's perspective.

If the `verify-tasks` extension is installed, it can
complement G5 by detecting phantom completions — tasks
marked `[X]` that have no real implementation behind them.

These are additive checks, not replacements for gates.

## Failure Escalation Protocol

When auto-fix fails after max attempts:

1. **STOP** execution — do not proceed to the next phase
2. **Present context** to human:
   - Which gate failed
   - What the specific failure is
   - What auto-fix attempts were made
   - Research findings from context_builder and Tavily (for G4/G6)
3. **Wait for guidance** — the human can:
   - Provide a fix and resume: "Fix X, then continue"
   - Skip the gate: "Proceed anyway" (logged as a deliberate override)
   - Abort: "Stop the autopilot"
4. **Resume** from the failed phase after human intervention

# Gate Validation Reference

Programmatic gate checks performed after each SDD phase. The autopilot validates each gate automatically and attempts auto-fix if validation fails (max 2 attempts before escalating to human).

## Gate Definitions

### G0 — Prerequisites (Before Specify)

**Check:** Constitution principles validated against the current codebase.

```
1. pnpm typecheck → must pass (0 errors)
2. pnpm test → must pass (record count as baseline)
3. pnpm build → must pass
4. pnpm lint → must pass
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

**Auto-Fix:** This is the **Checklist Remediation Loop**:

```
Step 1: Run all checklist prompts from the workflow file
Step 2: Parse all [Gap] markers across all checklists/*.md
Step 3: For EACH gap:
  a. Spawn 3 consensus agents in parallel with gap description + spec/plan context
  b. Apply consensus rules → produce proposed edit
  c. Auto-edit spec.md or plan.md with the remediation
Step 4: Re-run ALL checklists to verify gaps closed
  - If new gaps appear → remediate (max 2 total loops)
  - If 0 gaps → G4 PASS
Step 5: If gaps remain after 2 loops → STOP, present to human
```

**Critical:** Run gap remediation sequentially (one gap at a time), even though checklist execution is parallel. This prevents conflicting spec edits.

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

**Auto-Fix:** This is the **Analyze Remediation Loop**:

```
Step 1: Run /speckit.analyze (via phase-executor subagent)
Step 2: Parse ALL findings by severity
Step 3: For EACH finding (CRITICAL, HIGH, MEDIUM, LOW):
  a. Use context_builder(response_type: "question") to
     investigate the finding with codebase context
  b. Determine the fix: add task, amend task, edit spec,
     edit plan, remove stale marker, etc.
  c. Apply the fix to the relevant artifact
Step 4: Re-run analyze to verify all findings resolved
  - If new findings appear → remediate (max 2 total loops)
  - If 0 findings → G6 PASS
Step 5: If findings remain after 2 loops → STOP, present
  to human with all remaining findings and attempted fixes
```

**Why remediate everything:** The autopilot runs unattended.
Leaving MEDIUM/LOW issues for "post-hoc review" means they
never get fixed. Fixing all findings produces cleaner
artifacts and prevents issues from compounding during
implementation.

### G7 — After Implement

**Check:** Full verification suite passes.

```
1. Run build command (e.g., pnpm build) → must pass
2. Run typecheck (e.g., pnpm typecheck) → must pass
3. Run lint (e.g., pnpm lint) → must pass
4. Run tests (e.g., pnpm test) → must pass (unit + contract + integration)
5. ALL must pass for G7 to pass
```

**Auto-Fix:**
- Build failures: Check for syntax errors, missing imports
- Type errors: Fix type mismatches, add missing types
- Lint errors: Run auto-fix (e.g., `pnpm lint:fix`)
- Test failures: Fix failing tests or implementation bugs

**After G7 passes:** Push branch and create PR via `gh pr create`.

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
| G7 | Implement | Build+type+lint+test pass | Fix errors | 2 |

## Failure Escalation Protocol

When auto-fix fails after max attempts:

1. **STOP** execution — do not proceed to the next phase
2. **Present context** to human:
   - Which gate failed
   - What the specific failure is
   - What auto-fix attempts were made
   - The 3 consensus agent perspectives (for G4/G6)
3. **Wait for guidance** — the human can:
   - Provide a fix and resume: "Fix X, then continue"
   - Skip the gate: "Proceed anyway" (logged as a deliberate override)
   - Abort: "Stop the autopilot"
4. **Resume** from the failed phase after human intervention

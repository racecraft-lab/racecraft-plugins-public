# Consensus Protocol Reference

The consensus protocol is the core autonomy mechanism used by 3 phases: Clarify, Checklist, and Analyze. Each phase presents a different type of "question" to resolve, but the resolution mechanism is the same.

## The 3 Perspective Agents

| Agent | Perspective | Primary Tools | Strength |
|-------|------------|---------------|----------|
| `codebase-analyst` | What does the existing code show? | RepoPrompt context_builder, file_search, get_code_structure | Finding established patterns, types, naming conventions, error handling |
| `spec-context-analyst` | What do project decisions say? | Read (constitution, master plan, prior specs, CLAUDE.md) | Grounding answers in established principles and prior decisions |
| `domain-researcher` | What do best practices recommend? | Tavily search, Context7 docs | External evidence — API docs, standards, community patterns |

## Consensus Rules

### Moderate Mode (Default)

| Scenario | Action |
|----------|--------|
| **2/3 agree** | Use the majority answer. Log the dissenting perspective for context. |
| **3/3 agree** | Use the answer with high confidence. |
| **All 3 disagree** | Flag as `[HUMAN REVIEW NEEDED]` with all 3 perspectives. STOP autopilot. |
| **Security/data-integrity keyword detected** | Always flag for human regardless of consensus. |

### Conservative Mode

Same as moderate, but:
- Requires 3/3 agreement for auto-answer
- 2/3 agreement flags for human with recommendation
- Any disagreement stops for human review

### Aggressive Mode

Same as moderate, but:
- 2/3 agreement auto-answers (same as moderate)
- Even all-disagree attempts to synthesize best answer and proceed
- Only security keywords stop for human review

## Security Keywords

These keywords in the question, gap, or finding text trigger **mandatory human review** regardless of consensus mode:

```
auth, token, secret, encryption, PII, credential, permission, password,
authentication, authorization, session, cookie, jwt, api-key, access-control
```

When a security keyword is detected:
1. Still spawn all 3 agents to gather perspectives
2. Present all 3 answers to the human
3. Let the human decide which answer to use
4. Resume autopilot after human decision

## Phase-Specific Consensus Flows

### Clarify Consensus

The clarify phase surfaces questions about the specification. For each question:

```
/speckit.clarify surfaces Question Q
    │
    ├── Spawn 3 agents IN PARALLEL (background):
    │   ├── codebase-analyst: "Given this spec and question Q, what's the right answer?"
    │   ├── spec-context-analyst: "Given this spec and question Q, what's the right answer?"
    │   └── domain-researcher: "Given this spec and question Q, what's the right answer?"
    │
    ├── Wait for all 3 to complete
    │
    ├── Compare answers:
    │   ├── Check for security keywords in Q → if found, flag for human
    │   ├── 2/3 or 3/3 agree → use consensus answer
    │   └── All disagree → flag for human
    │
    ├── If consensus reached:
    │   └── Respond to clarify with "recommended" + the consensus answer
    │       (This integrates the answer into spec.md automatically)
    │
    └── If no consensus:
        └── Respond to clarify with "done" to end the session
            Flag the question as [HUMAN REVIEW NEEDED] in the workflow file
```

**Prompt template for consensus agents during Clarify:**

```
You are participating in a consensus resolution for a SpecKit clarification question.

## Specification Context
[Insert relevant spec.md excerpt]

## Question
[Insert the clarify question]

## Your Task
Propose the best answer to this question from your perspective. Be specific and actionable.
Follow your agent instructions for output format (Answer, Evidence/References/Citations, Confidence).
```

### Checklist Gap Remediation

When a checklist identifies `[Gap]` markers, each gap becomes a "question" for consensus:

```
Checklist produces [Gap]: "No requirement specifies array index behavior for batch results"
    │
    ├── Spawn 3 agents IN PARALLEL (background):
    │   ├── codebase-analyst: "How should we close this gap? Propose a spec/plan edit."
    │   ├── spec-context-analyst: "How should we close this gap? Propose a spec/plan edit."
    │   └── domain-researcher: "How should we close this gap? Propose a spec/plan edit."
    │
    ├── Wait for all 3 to complete
    │
    ├── Compare proposed edits:
    │   ├── Check for security keywords → if found, flag for human
    │   ├── 2/3 or 3/3 agree on approach → use consensus edit
    │   └── All disagree → flag for human
    │
    ├── If consensus reached:
    │   ├── Apply the edit to spec.md or plan.md
    │   └── Log the edit with rationale in the workflow file
    │
    └── If no consensus:
        └── Flag as [HUMAN REVIEW NEEDED] in the workflow file
```

**Prompt template for consensus agents during Gap Remediation:**

```
You are participating in a consensus resolution for a SpecKit checklist gap.

## Specification Context
[Insert relevant spec.md and plan.md excerpts]

## Gap Description
[Insert the [Gap] marker text and surrounding checklist context]

## Your Task
Propose how to close this gap. Specifically:
1. Which artifact should be edited? (spec.md, plan.md, or both)
2. What exact text should be added or modified?
3. Where in the artifact should the edit go? (section name)

Follow your agent instructions for output format.
```

### Analyze Finding Remediation

When analyze produces CRITICAL/HIGH findings, each finding is resolved via consensus:

```
Analyze finding C1 (MEDIUM): "Plan references tests/integration/ but no task creates it"
    │
    ├── Spawn 3 agents IN PARALLEL (background):
    │   ├── codebase-analyst: "How should we fix this finding? Propose artifact edits."
    │   ├── spec-context-analyst: "How should we fix this finding? Propose artifact edits."
    │   └── domain-researcher: "How should we fix this finding? Propose artifact edits."
    │
    ├── Wait for all 3 to complete
    │
    ├── Compare proposed fixes:
    │   ├── Check for security keywords → if found, flag for human
    │   ├── 2/3 or 3/3 agree → apply fix
    │   └── All disagree → flag for human
    │
    ├── If consensus reached:
    │   ├── Apply the fix to tasks.md, spec.md, or plan.md
    │   └── Log the fix with rationale in the workflow file
    │
    └── If no consensus:
        └── Flag as [HUMAN REVIEW NEEDED] in the workflow file
```

**Prompt template for consensus agents during Finding Remediation:**

```
You are participating in a consensus resolution for a SpecKit analysis finding.

## Artifact Context
[Insert relevant excerpts from spec.md, plan.md, and tasks.md]

## Finding
Severity: [CRITICAL/HIGH]
Description: [Insert finding text]

## Your Task
Propose how to fix this finding. Specifically:
1. Which artifact(s) should be edited? (tasks.md, spec.md, plan.md)
2. What exact changes should be made?
3. Does this fix introduce any new concerns?

Follow your agent instructions for output format.
```

## Determining Agreement

Two agents "agree" when their proposed answers converge on the same approach, even if worded differently. Evaluate agreement based on:

1. **Same conclusion** — both recommend the same action (add task, edit spec section, use specific API)
2. **Compatible evidence** — evidence from different sources pointing to the same answer
3. **No contradiction** — answers don't conflict in their recommendations

Two agents "disagree" when:
1. **Different conclusions** — they recommend incompatible actions
2. **Contradictory evidence** — their evidence points in different directions
3. **Different scope** — one says "add to spec" while another says "not needed"

When evaluating agreement, consider the **substance** of the answer, not the exact wording. A codebase-analyst saying "use the existing BatchResult pattern" and a spec-context-analyst saying "follow the Phase 5 batch pattern" are agreeing if they point to the same pattern.

## Logging

After each consensus resolution, log the result in the workflow file:

```markdown
### Consensus Resolution Log

| # | Type | Question/Gap/Finding | Agents Agree | Resolution | Agent Used |
|---|------|---------------------|--------------|------------|------------|
| 1 | Clarify | Session token format? | 3/3 | JWT with 24h expiry | domain-researcher |
| 2 | Gap | Rate limit thresholds | 2/3 | Added to spec §4.2 | codebase-analyst, domain-researcher |
| 3 | Finding | Missing integration tests | 3/3 | Added task T050 | All |
```

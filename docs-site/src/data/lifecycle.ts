/**
 * Single source for the lifecycle phase and gate tables. LifecycleFlow.astro
 * renders the phases as a flow; LifecycleTable.astro renders the same rows as
 * the static tables in spec-kit-lifecycle.mdx. Edit the wording here only.
 * Backticked spans render as inline code.
 */
export interface LifecycleStep {
  id: string;
  stage: string;
  purpose: string;
  output: string;
  gate: string;
  next: string;
  badge: string;
}

export interface LifecycleGate {
  gate: string;
  checks: string;
  ifFails: string;
}

export const lifecycleSteps: readonly LifecycleStep[] = [
  {
    id: 'idea',
    stage: 'Idea',
    purpose: 'Capture the problem or opportunity in plain language.',
    output: 'Notes, transcript, or scoping answers.',
    gate: 'The idea is specific enough to write a PRD.',
    next: 'Run `grill-me` or move to PRD creation.',
    badge: 'Input',
  },
  {
    id: 'prd',
    stage: 'PRD',
    purpose: 'Convert the idea into product requirements and acceptance criteria.',
    output: 'PRD and SPEC catalog.',
    gate: 'A SPEC-ID is visible.',
    next: 'Add or confirm the roadmap entry.',
    badge: 'Product artifact',
  },
  {
    id: 'roadmap',
    stage: 'Roadmap',
    purpose: 'Put the SPEC-ID in technical order with dependencies and status.',
    output: '`docs/ai/specs/*.md` roadmap row.',
    gate: 'The roadmap marks the SPEC ready or explains the blocker.',
    next: 'Scaffold the SPEC.',
    badge: 'Planning artifact',
  },
  {
    id: 'scaffold',
    stage: 'Scaffold',
    purpose: 'Prepare one worktree, workflow file, spec folder, and MOC.',
    output: 'Design concept, workflow, `SPEC-MOC.md`, and initial `spec.md`.',
    gate: 'Setup gates pass and the target feature directory exists.',
    next: 'Start autopilot.',
    badge: 'Setup gate',
  },
  {
    id: 'specify',
    stage: 'Specify',
    purpose: 'Turn the request into user stories and functional requirements.',
    output: '`spec.md`.',
    gate: 'G1: spec exists and clarification markers are addressed.',
    next: 'Clarify remaining decisions.',
    badge: 'G1',
  },
  {
    id: 'clarify',
    stage: 'Clarify',
    purpose: 'Resolve ambiguity before planning.',
    output: 'Updated `spec.md` and clarification notes.',
    gate: 'G2: no unresolved clarification markers remain.',
    next: 'Plan implementation.',
    badge: 'G2',
  },
  {
    id: 'plan',
    stage: 'Plan',
    purpose: 'Choose the architecture, files, validation, and constraints.',
    output: '`plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`.',
    gate: 'G3: plan exists with no unresolved markers.',
    next: 'Generate checklists.',
    badge: 'G3',
  },
  {
    id: 'checklist',
    stage: 'Checklist',
    purpose: 'Audit UX, accessibility, integration, and error-handling gaps.',
    output: '`checklists/*.md`.',
    gate: 'G4: checklist gaps are fixed or explicitly deferred.',
    next: 'Generate tasks.',
    badge: 'G4',
  },
  {
    id: 'tasks',
    stage: 'Tasks',
    purpose: 'Break work into reviewable tasks by user story.',
    output: '`tasks.md` and reviewability evidence.',
    gate: 'G5: tasks cover every requirement and carry valid execution metadata.',
    next: 'Analyze drift before implementation.',
    badge: 'G5',
  },
  {
    id: 'analyze',
    stage: 'Analyze',
    purpose: 'Check cross-artifact consistency.',
    output: 'Analysis results in the workflow file.',
    gate: 'G6: no Critical or High findings remain.',
    next: 'Pass the confidence gate.',
    badge: 'G6',
  },
  {
    id: 'confidence',
    stage: 'Confidence gate',
    purpose: 'Score confidence in the plan before any code changes.',
    output: 'Confidence score and criterion breakdown.',
    gate: 'G6.5: confidence is at or above 0.90 (advisory by default, strict when the project opts in).',
    next: 'Implement the tasks.',
    badge: 'G6.5',
  },
  {
    id: 'implement',
    stage: 'Implement',
    purpose: 'Apply the tasks and record validation evidence.',
    output: 'Changed files, task checkoffs, validation output, and the PR packet.',
    gate: 'G7: build, type-check, lint, and tests pass, with TDD evidence and no placeholder tests.',
    next: 'Open the pull request.',
    badge: 'G7',
  },
  {
    id: 'pull-request',
    stage: 'Pull request',
    purpose: 'Package the change for review.',
    output: 'PR packet, UAT runbook, and the pull request body.',
    gate: 'Every required check is green at each PR head. Only human UAT may stay deferred.',
    next: 'Review and merge the PR yourself. Autopilot never merges.',
    badge: 'Review',
  },
];

export const lifecycleGates: readonly LifecycleGate[] = [
  {
    gate: 'G1',
    checks: '`spec.md` exists and the basic request is captured.',
    ifFails: 'Inspect the specify output and update the spec evidence.',
  },
  {
    gate: 'G2',
    checks: 'Clarification markers are resolved.',
    ifFails: 'Return to the unanswered decision before planning.',
  },
  {
    gate: 'G3',
    checks: 'The plan has concrete files, validation, and constraints.',
    ifFails: 'Inspect `plan.md` and the research or contract artifact it references.',
  },
  {
    gate: 'G4',
    checks: 'Checklist gaps are resolved or intentionally deferred.',
    ifFails: 'Review the checklist item and update the owning artifact.',
  },
  {
    gate: 'G5',
    checks: '`tasks.md` covers every requirement with valid execution metadata, and no gate task waits on its own dependents.',
    ifFails: 'Inspect task grouping, dependencies, and reviewability evidence.',
  },
  {
    gate: 'G6',
    checks: 'Analyze has no open Critical or High drift findings.',
    ifFails: 'Resolve the finding recorded in the workflow file.',
  },
  {
    gate: 'G6.5',
    checks: 'The pre-implement confidence score is at or above 0.90 (advisory by default, strict when the project opts in).',
    ifFails: 'Re-route consensus on the lowest-scoring criterion, then re-emit the confidence score.',
  },
  {
    gate: 'G7',
    checks: 'Build, type-check, lint, unit tests, and integration tests pass, TDD evidence is present, and no placeholder tests remain.',
    ifFails: 'Fix the failing command or placeholder test, then inspect `tasks.md` and the PR packet evidence.',
  },
];

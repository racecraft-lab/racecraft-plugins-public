---
name: speckit-coach
description: Coach developers through Spec-Driven Development and SpecKit Pro. Use for SDD methodology, SpecKit command and gate guidance, technical-roadmap and workflow design, roadmap-MOC guidance, checklist selection, SpecKit project repair, selective formal-methods guidance and model/checker selection, SpecKit consensus protocol and voting rules, or SpecKit preset and extension discovery and configuration. Not for running autopilot, conducting grill-me, or unrelated coding (including MCP tool implementation). Formal-check execution and autopilot resume belong to speckit-autopilot.
---

# SpecKit Coach

Coach the user through the official SpecKit CLI and complementary SpecKit Pro workflows. This skill provides guidance and bounded project repair; it does not run an autonomous workflow itself. In Codex, use `$skill-name` syntax for plugin skills rather than legacy custom slash-command syntax.

## Start with the project that exists

- Use `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` for capability selection and `speckit-pro/skills/speckit-autopilot/references/grounding.md` for external-fact grounding.
- Discover the session's available tools and skills before recommending an external action. Ground external claims in an observed result; say when the available evidence is insufficient.
- Inspect `.specify/presets/*/preset.yml` and `.specify/extensions/*/extension.yml` when present. Read the installed configuration before advising, so the advice reflects the project's actual constraints.
- Treat mutable actions as user-controlled. Explain the intended change and request confirmation before installing, removing, enabling, disabling, or configuring extensions.

## Route the request

Use the smallest relevant reference; do not load the whole library.

| User goal | Read or do |
|---|---|
| Learn SDD, start a project, recover from a failed phase, or assess artifacts | [Getting started](references/getting-started.md) and [SDD methodology](references/sdd-methodology.md) as needed. |
| Use an installed official Spec Kit command | [Command guide](references/command-guide.md) for inputs, artifacts, mistakes, and recovery. Inspect the active installed command definition for version-specific mechanics. For gate questions, read the [live autopilot contract](../speckit-autopilot/SKILL.md) as a reference only; do not execute or invoke it. |
| Choose or author checklists | [Checklist domains](references/checklist-domains-guide.md). Read the feature's `spec.md` and `plan.md`, rank the relevant risks, and offer enriched prompts for two to four domains. |
| Decide whether a behavior needs formal verification, choose a checker, or learn a first model | [Selective formal methods](references/formal-methods-guide.md). Assess risk and simpler checks first; record explicit selection and adapt coaching to experience. |
| Model a difficult rule in Quint, or look up Quint language, modeling, or witness guidance | [Optional Quint modeling](references/quint-guide.md). Read only the sections the model needs; SpecKit still owns selection, bounds, and gate decisions. |
| Design a constitution | [Constitution guide](references/constitution-guide.md). |
| Create or repair `.specify/quality-gates.json`, pick gate thresholds, or record a permanent gate skip | [Quality gates guide](references/quality-gates-guide.md). Measure the existing code before proposing a ceiling; write the file only after the operator confirms. |
| Design a multi-spec roadmap or split a feature | Read the complete [technical-roadmap template](templates/technical-roadmap-template.md) and [slicing heuristics](references/slicing-heuristics.md), then instantiate the template without dropping required sections. `## Progress Tracking` is mandatory: scaffold and status use it as the shared lifecycle record. Derive independently executable vertical slices with observable outcomes and explicit real dependencies; review the graph before writing. |
| Create a PRD and roadmap from an unformed idea | Route to `$speckit-prd`; use its PRD and roadmap templates. |
| Track one spec through phases or understand scaffold-created workflow files | [Workflow template](templates/workflow-template.md). For scaffold creation, population, inputs, or output locations, also read the [live scaffold skill](../speckit-scaffold-spec/SKILL.md) as a reference only; do not execute or invoke it. Keep artifacts, gates, and decisions current. |
| Explain the roadmap home note | [Roadmap-MOC guide](references/roadmap-moc-guide.md). The curated zone is author-owned; the generated index is regenerated, not hand-edited. |
| Explain or configure presets, extensions, hooks, catalogs, or upgrade recovery | [Presets and extensions guide](references/presets-extensions-guide.md). Discover and inspect first; confirm before any mutation. |
| Explain autonomous execution, consensus, remediation, review loops, or configuration | Read [the live autopilot skill](../speckit-autopilot/SKILL.md) as a reference only; explain its current contract without executing or invoking it. When the user asks to run an existing workflow, use the bounded autopilot hand-off below. |
| Scope a raw brief interactively | Route to `$grill-me`; do not conduct its interview here. |
| Scaffold a roadmap item, inspect status, resolve a review, or repair Codex agents | Route respectively to `$speckit-scaffold-spec`, `$speckit-status`, `$speckit-resolve-pr`, or the SpecKit Pro `install` skill. |
| Archive merged-spec records or clean up archived specs | Route to `$speckit-archive-cleanup`; do not copy or execute its cleanup workflow here. |

## Keep adjacent contracts distinct

- Scaffold owns roadmap lookup, branch/worktree placement, the canonical
  Design Concept and workflow artifacts, and the explicit hand-off to
  autopilot. Grill Me owns the interactive interview that supplies the Design
  Concept. Grill Me never creates a branch, worktree, workflow, or roadmap
  status update, and scaffold must not synthesize interview answers when a
  human interaction surface is unavailable.
- Canonical scaffold artifacts are
  `docs/ai/specs/.process/SPEC-<ID>-design-concept.md`,
  `docs/ai/specs/.process/SPEC-<ID>-workflow.md`, and
  `specs/<branch-name>/SPEC-MOC.md`. The workflow's `Branch` field records the
  actual dedicated spec branch returned and verified by scaffold; it is never
  `main` and is never guessed from the spec title alone.
- A declared extension command is not evidence that a hook runs
  automatically. Inspect installed presence, host command registration, and
  enabled hook wiring separately. Report an empty declaration as empty and an
  unavailable registration or wiring check as unverified; never describe a
  command declaration as a hook.

## Essential SDD guidance

The normal flow is `constitution → specify → clarify (as needed) → plan → checklist (as needed) → tasks → analyze (as needed) → implement`. Preserve the traceability markers in the artifacts: user stories, functional requirements, clarifications, parallel-safe tasks, and checklist gaps. Do not advance past a failed gate; explain the artifact or evidence that must change first.

For roadmap decomposition, prefer delivery slices over technical layers when a slice can be independently verified. Keep cross-spec dependencies explicit, minimize them, and use mocks only when the handoff contract is defined.

## Bounded autopilot hand-off

Coach never executes or invokes autopilot. When the user asks to run a workflow
and supplies its path, return one explicit Codex command bounded to the
requested stage:

```text
$speckit-autopilot <workflow-file> --stage plan|implement|full
```

Use `--stage full` only when the user asks for the full workflow; use
`--stage plan` or `--stage implement` only for that requested boundary. Preserve
the supplied workflow path exactly, do not invent a path or broaden the stage,
and state briefly that the autopilot owns its own preflight, phase gates,
durable state, and fail-closed stops. If no workflow path exists, route to
`$speckit-scaffold-spec`; if the path or requested stage is ambiguous, ask for
that missing input instead of executing anything.

## Project fixup

For a request to repair an existing SpecKit Pro project:

1. Confirm the target root and inspect `git status`; preserve unrelated changes.
2. Inspect presets and resolve each affected core template with `specify preset resolve`. Move durable local customizations into a project preset rather than modifying core templates.
3. Restore a core template only from a reviewed source (version control, verified backup, or official template); never reconstruct it by guesswork.
4. Preserve any host PR template and run the relevant project checks before reporting the resolved template paths, restored files, and remaining manual follow-up.

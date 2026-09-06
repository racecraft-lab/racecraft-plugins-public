---
name: speckit-coach
description: Coach developers through Spec-Driven Development and SpecKit Pro. Use for SDD methodology, SpecKit command and gate guidance, technical-roadmap and workflow design, roadmap-MOC guidance, checklist selection, SpecKit project repair, or SpecKit preset and extension discovery and configuration. Not for running autopilot, conducting grill-me, or unrelated coding (including MCP tool implementation).
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
| Learn SDD, start a project, recover from a failed phase, or assess artifacts | [Getting started](../../skills/speckit-coach/references/getting-started.md) and [SDD methodology](../../skills/speckit-coach/references/sdd-methodology.md) as needed. |
| Use an installed official Spec Kit command | [Command guide](../../skills/speckit-coach/references/command-guide.md) for inputs, artifacts, mistakes, and recovery. Inspect the active installed command definition for version-specific mechanics. For gate questions, read the [live autopilot contract](../speckit-autopilot/SKILL.md) as a reference only; do not execute or invoke it. |
| Choose or author checklists | [Checklist domains](../../skills/speckit-coach/references/checklist-domains-guide.md). Read the feature's `spec.md` and `plan.md`, rank the relevant risks, and offer enriched prompts for two to four domains. |
| Design a constitution | [Constitution guide](../../skills/speckit-coach/references/constitution-guide.md). |
| Create or repair `.specify/quality-gates.json`, pick gate thresholds, or record a permanent gate skip | [Quality gates guide](../../skills/speckit-coach/references/quality-gates-guide.md). Measure the existing code before proposing a ceiling; write the file only after the operator confirms. |
| Design a multi-spec roadmap or split a feature | [Technical-roadmap template](../../skills/speckit-coach/templates/technical-roadmap-template.md) and [slicing heuristics](../../skills/speckit-coach/references/slicing-heuristics.md). Derive independently executable vertical slices with observable outcomes and explicit real dependencies; review the graph before writing. |
| Create a PRD and roadmap from an unformed idea | Route to `$speckit-prd`; use its PRD and roadmap templates. |
| Track one spec through phases | [Workflow template](../../skills/speckit-coach/templates/workflow-template.md). Keep artifacts, gates, and decisions current. |
| Explain the roadmap home note | [Roadmap-MOC guide](../../skills/speckit-coach/references/roadmap-moc-guide.md). The curated zone is author-owned; the generated index is regenerated, not hand-edited. |
| Explain or configure presets, extensions, hooks, catalogs, or upgrade recovery | [Presets and extensions guide](../../skills/speckit-coach/references/presets-extensions-guide.md). Discover and inspect first; confirm before any mutation. |
| Explain autonomous execution, consensus, remediation, review loops, or configuration | Read [the live autopilot skill](../speckit-autopilot/SKILL.md) as a reference only; explain its current contract without executing or invoking it. |
| Scope a raw brief interactively | Route to `$grill-me`; do not conduct its interview here. |
| Scaffold a roadmap item, inspect status, resolve a review, or repair Codex agents | Route respectively to `$speckit-scaffold-spec`, `$speckit-status`, `$speckit-resolve-pr`, or the SpecKit Pro `install` skill. |
| Archive merged-spec records or clean up archived specs | Route to `$speckit-archive-cleanup`; do not copy or execute its cleanup workflow here. |

## Essential SDD guidance

The normal flow is `constitution → specify → clarify (as needed) → plan → checklist (as needed) → tasks → analyze (as needed) → implement`. Preserve the traceability markers in the artifacts: user stories, functional requirements, clarifications, parallel-safe tasks, and checklist gaps. Do not advance past a failed gate; explain the artifact or evidence that must change first.

For roadmap decomposition, prefer delivery slices over technical layers when a slice can be independently verified. Keep cross-spec dependencies explicit, minimize them, and use mocks only when the handoff contract is defined.

## Project fixup

For a request to repair an existing SpecKit Pro project:

1. Confirm the target root and inspect `git status`; preserve unrelated changes.
2. Inspect presets and resolve each affected core template with `specify preset resolve`. Move durable local customizations into a project preset rather than modifying core templates.
3. Restore a core template only from a reviewed source (version control, verified backup, or official template); never reconstruct it by guesswork.
4. Preserve any host PR template and run the relevant project checks before reporting the resolved template paths, restored files, and remaining manual follow-up.

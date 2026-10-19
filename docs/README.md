# Project docs

This folder holds the design record for this repository: why things are built
the way they are, and how each feature was planned. To install or use the
plugins, start with the [root README](../README.md) instead.

## Where to start

| You want to | Read |
| --- | --- |
| Understand a design decision | [Architecture decision records](adr/README.md) |
| Understand how a part of the runner works | [`architecture/`](architecture/) |
| See how a feature was planned | A PRD below, then its roadmap and map |
| Work on this repo as a coding agent | [`AGENTS.md`](../AGENTS.md), then the [agent runbook](agent-runbook.md) |

## How planning works here

This repository plans its own features with speckit-pro, so its planning files
follow the layout the plugin teaches:

1. A **PRD** (`docs/prd-<name>.md`) states the problem and goals.
2. A **technical roadmap** (`docs/ai/specs/<name>-technical-roadmap.md`) breaks
   the PRD into numbered specs, such as `ART-001`.
3. A **roadmap map** (`docs/ai/specs/<name>-roadmap-MOC.md`) links the PRD,
   the roadmap and every spec.
4. Each spec gets a folder, `specs/<id>-<name>/`, with `spec.md`, `plan.md`
   and `tasks.md`. After a spec merges, its folder is archived.
5. `docs/ai/specs/.process/` holds the workflow file and design notes of work
   that is still running.

Files from finished work were removed from the tree. The git tag
`docs-pre-cleanup-2026-10` keeps all of them.

## Initiatives

| Initiative | Status | PRD | Roadmap | Map |
| --- | --- | --- | --- | --- |
| Cross-platform plugin runtime | Done | [PRD](prd-cross-platform-plugin-runtime.md) | [Roadmap](ai/specs/cross-platform-plugin-runtime-technical-roadmap.md) | [Map](ai/specs/cross-platform-plugin-runtime-roadmap-MOC.md) |
| PR-size governance | Done | [PRD](prd-pr-size-governance.md) | [Roadmap](ai/specs/pr-size-governance-technical-roadmap.md) | None |
| Tool-agnostic capability discovery | Done | [PRD](prd-tool-agnostic-capability-discovery.md) | [Roadmap](ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md) | [Map](ai/specs/tool-agnostic-capability-discovery-roadmap-MOC.md) |
| CI/CD and release pipeline | Done | None | [Roadmap](ai/specs/cicd-release-pipeline-technical-roadmap.md) | None |
| Reviewer experience | Done | None | [Roadmap](ai/specs/reviewer-experience-technical-roadmap.md) | None |
| Interactive documentation | Active | [PRD](prd-interactive-documentation.md) | [Roadmap](ai/specs/interactive-documentation-technical-roadmap.md) | [Map](ai/specs/interactive-documentation-roadmap-MOC.md) |
| Harness engineering uplift | Paused | [PRD](prd-harness-engineering-uplift.md) | [Roadmap](ai/specs/harness-engineering-uplift-technical-roadmap.md) | [Map](ai/specs/harness-engineering-uplift-roadmap-MOC.md) |
| HTML artifacts | Paused, partly built | [PRD](prd-html-artifacts.md) | [Roadmap](ai/specs/html-artifacts-technical-roadmap.md) | [Map](ai/specs/html-artifacts-roadmap-MOC.md) |
| Racecraft identity system | Paused, not started | [PRD](prd-racecraft-identity-system.md) | [Roadmap](ai/specs/racecraft-identity-system-technical-roadmap.md) | [Map](ai/specs/racecraft-identity-system-roadmap-MOC.md) |
| Selective formal methods | In progress | None | [Decision record](ai/specs/formal-check-decision.md) | [Spec map](../specs/formal-001-selective-formal-methods/SPEC-MOC.md) |

"Paused" means the roadmap marks its open specs as frozen while the speckit-pro
health work comes first.

## Folders

| Folder | What it holds |
| --- | --- |
| [`adr/`](adr/README.md) | Architecture decision records, one decision each |
| [`architecture/`](architecture/) | How specific runner parts work |
| [`ai/specs/`](ai/specs/) | Roadmaps, roadmap maps, design contracts and decision records |
| [`ai/research/`](ai/research/) | Research spikes that informed a PRD or roadmap |
| [`agents/`](agents/) | Settings that coding-agent skills read: issue tracker, triage labels, domain docs |

New top-level files and folders here must be added to the allowlist in
`tests/speckit-pro/layer1-structural/validate-docs-layout.py`.

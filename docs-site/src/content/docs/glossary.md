---
title: "Glossary"
description: "Definitions for the SpecKit Pro terms that recur across install, troubleshooting, generated reference, and release guidance — marketplace, payload, source tree, skill, agent, hook, cache, and more."
---

Use this route to orient users, support responders, and reviewers to the terms
that recur across install, troubleshooting, generated reference, and release
workflow guidance.

## Route Shell

- **Audience:** All users
- **Purpose:** Define marketplace, payload, source tree, skill, agent, hook, cache, constitution, lifecycle, generated reference, and source-update terms.
- **Shell owner DOC:** DOC-002
- **Full-content owner DOC:** DOC-010
- **Success criterion:** Support answers can link to exact definitions.
- **Useful now:** Link to the stable term anchors below when answering install,
  recovery, reference, or release workflow questions.

## Marketplace

A marketplace is the platform-facing catalog that tells Claude Code or Codex
where to find SpecKit Pro. For install decisions, start with the
[support link map](/racecraft-plugins-public/choose-your-path/#support-link-map),
then use the platform install guide that matches the user environment.

## Payload

A payload is the generated plugin directory a platform installs from. Keep the
Claude payload under `dist/claude/speckit-pro/` and the Codex payload under
`dist/codex/speckit-pro/` separate from the authoring source tree.

## Source Tree

The source tree is the editable repository content that owns plugin behavior,
docs, validation scripts, and generated-reference inputs. Do not treat generated
payloads, generated reference pages, or installed runtime state as the source
tree.

## Skill

A skill is an instruction surface shipped by SpecKit Pro. Use the generated
[skills reference](/racecraft-plugins-public/reference/skills/) for source-cited
skill names, runtime mappings, prerequisites, and expected artifacts.

## Agent

An agent is a runtime-specific helper definition. Claude Code plugin agents and
Codex custom-agent TOML files are parallel surfaces, so compare them through the
generated [agents reference](/racecraft-plugins-public/reference/agents/)
instead of assuming one runtime copied the other.

## Hook

A hook is platform configuration that can observe or respond to supported
runtime events. Hook behavior remains governed by the selected platform, local
settings, managed policy, sandboxing, and approval prompts.

## Cache

A cache is installed runtime state owned by the platform. Use cache-specific
recovery only after checking marketplace source, payload, installed state,
reload or restart status, and custom-agent registration. Start from
[recovery cases](/racecraft-plugins-public/update-and-rollback/#recovery-cases)
before choosing a manual action.

## Constitution

The constitution is project-level governance for SpecKit work. It describes
constraints and review expectations that implementation plans and workflow
evidence must respect.

## Lifecycle

The lifecycle is the path from idea, clarification, PRD, spec planning,
implementation, validation, review, merge, and archive. Use the
[Spec Kit lifecycle](/racecraft-plugins-public/spec-kit-lifecycle/) page when a
support answer needs process orientation.

## Generated Reference

A generated reference is committed Markdown output from
`docs-site/scripts/generate-reference-pages.mjs`. Generated reference pages are
checked with `pnpm --dir docs-site reference:check`, and source updates belong
in the generator inputs rather than direct edits to generated pages. Use the
[Install record](/racecraft-plugins-public/reference/skills/#install) for a
representative generated skill anchor.

## Source Update Guidance

When an external platform claim about Claude Code, Codex, marketplace behavior,
search behavior, PR Checks, or release tooling changes, make a source update in
the owning page or generator input. Keep shared support links aligned with
`docs-site/scripts/validate-docs-quality.mjs`, the
[change type matrix](/racecraft-plugins-public/contribute-and-release/#change-type-matrix),
and the relevant generated reference or recovery page.

## Source Evidence

- [docs/prd-interactive-documentation.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs/prd-interactive-documentation.md)
- [docs/roadmap-interactive-documentation.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs/roadmap-interactive-documentation.md)

## Next Step

[Review the choose-your-path support map](/racecraft-plugins-public/choose-your-path/#support-link-map)
for install, recovery, glossary, reference, and release workflow handoffs.

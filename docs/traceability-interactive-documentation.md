# Traceability Matrix: Racecraft Interactive Documentation

**Date:** 2026-06-12  
**Source PRD:** [docs/prd-interactive-documentation.md](prd-interactive-documentation.md)  
**Roadmap:** [docs/roadmap-interactive-documentation.md](roadmap-interactive-documentation.md)  
**Status:** DOC-002 ready for SPEC decomposition

Every PRD feature maps to exactly one roadmap SPEC. Every roadmap SPEC maps back to exactly one PRD feature. Acceptance criteria are not shared across features.

| PRD feature ID | PRD feature name | Roadmap SPEC ID | Acceptance criteria IDs | Primary user | Source evidence | Validation method | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| DOC-FR-001 | Static docs framework and IA spike | DOC-001 | AC-1.1, AC-1.2, AC-1.3, AC-1.4 | Maintainer | Astro/Starlight docs, Starlight community plugin evidence, GitHub Pages docs, Docusaurus fallback evidence, Diataxis, repo absence of site config | Research artifact review; no product code changes | Completed | DOC-001 selected Astro/Starlight, kept Docusaurus/MDX as fallback, and was archived after PR #163 merged. |
| DOC-FR-002 | Unified landing page and IA shell | DOC-002 | AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5 | First-time user | README, `speckit-pro/README.md`, Diataxis, DOC-001 decision record | Static site build; nav inspection; local link check | Ready | DOC-001 dependency is satisfied; DOC-002 owns Astro/Starlight scaffolding and concrete site config. |
| DOC-FR-003 | Claude Code marketplace installation path | DOC-003 | AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5 | Claude Code user | Claude plugin/marketplace/settings docs; `.claude-plugin/marketplace.json`; `speckit-pro/.claude-plugin/plugin.json` | Link check; command review; source file existence check | Pending | Must clarify current skill-first packaging. |
| DOC-FR-004 | Codex marketplace installation path | DOC-004 | AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | Codex user | OpenAI Codex plugin/skills/subagents/security docs; `.agents/plugins/marketplace.json`; `speckit-pro/.codex-plugin/plugin.json`; generated Codex payload manifest path | Link check; command review; source file existence check | Pending | Must validate personal marketplace path wording. |
| DOC-FR-005 | First successful `speckit-pro` workflow tutorial and lifecycle explainer | DOC-005 | AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | New plugin user | GitHub Spec Kit README; `speckit-pro/README.md`; skill files | Tutorial walkthrough review; platform command labels; static fallback diagram | Pending | First-run path should minimize destructive operations. |
| DOC-FR-006 | Safe interactive platform/path selector and validation aids | DOC-006 | AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | New and returning users | Official platform docs; manifests; build script; W3C WAI | Site build; keyboard smoke test; metadata fixture review | Pending | No browser-executed local shell commands. |
| DOC-FR-007 | Command, workflow, manifest, and file-layout reference | DOC-007 | AC-7.1, AC-7.2, AC-7.3, AC-7.4, AC-7.5, AC-7.6 | Users, agents, maintainers | README, skill files, agents, hooks, manifests, tests | Local link check; referenced-file existence check | Pending | Shared reference for later troubleshooting docs. |
| DOC-FR-008 | Troubleshooting, security, trust, update, and rollback model | DOC-008 | AC-8.1, AC-8.2, AC-8.3, AC-8.4, AC-8.5, AC-8.6 | Security/platform evaluator | OpenAI security docs; Claude settings/marketplace docs; repo hooks/manifests | Source-fact review; symptom matrix coverage | Pending | Keep guarantees narrow and source-backed. |
| DOC-FR-009 | Maintainer and contributor release workflow | DOC-009 | AC-9.1, AC-9.2, AC-9.3, AC-9.4, AC-9.5, AC-9.6 | Maintainer/contributor | AGENTS.md, CLAUDE.md, CI workflows, scripts, tests | Command existence check; optional layer-1 test after docs edits | Pending | Should not duplicate all CLAUDE.md internals. |
| DOC-FR-010 | Search, accessibility, deep links, responsive UX, and docs validation | DOC-010 | AC-10.1, AC-10.2, AC-10.3, AC-10.4, AC-10.5, AC-10.6, AC-10.7 | All users | W3C WAI, selected docs framework docs, existing validation scripts | Site build; markdown lint; link check; accessibility/responsive smoke tests | Pending | Final hardening after content and interactions exist. |

## Traceability Checks

- **PRD feature count:** 10
- **Roadmap SPEC count:** 10
- **Mapping status:** 1:1; DOC-001 complete and archived, DOC-002 is next.
- **Acceptance criteria ownership:** Each AC-N.* belongs only to DOC-FR-00N.
- **Shared dependencies:** Allowed where platform pages feed first-run/reference/troubleshooting pages.
- **Untraced items:** None.

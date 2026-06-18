# Research: Troubleshooting, Security, Trust, Update, And Rollback

## Decision 1: Keep Three User-Facing Pages

**Decision**: Expand `troubleshooting.md` and `security-and-trust.md`, and add `docs-site/src/content/docs/update-and-rollback.md` as a top-level route.

**Rationale**: The design concept selected three separate pages so diagnostic support, evaluator trust review, and recovery procedures can each be scanned independently. Existing `docs-site/astro.config.mjs` already has a How-to group for troubleshooting and an Explanation group for security/trust, so the new route can join How-to without a new navigation pattern.

**Alternatives considered**:

- One combined page: lower IA cost, but support rows and evaluator trust claims would compete for attention.
- Update/rollback inside install pages: keeps platform commands nearby, but duplicates shared source/payload/cache guidance across Claude Code and Codex.

## Decision 2: Use A Symptom Matrix With Strict Inspection Boundaries

**Decision**: Troubleshooting content will use matrix rows with symptom, platform label, likely cause, read-only inspect command/file, recommended fix, and follow-up link.

**Rationale**: The spec requires every row to be support-linkable and safe in browser-rendered docs. A table shape makes missing fields obvious and preserves stable anchors for support replies. Inspect cells must stay read-only; mutating repair commands belong only in recommended fixes or linked recovery guidance with side effects stated first.

**Alternatives considered**:

- Narrative troubleshooting: easier prose, but harder to verify field completeness.
- Decision tree only: useful for first triage, but too weak for source-backed commands and files.

## Decision 3: Separate Evidence Types On Security & Trust

**Decision**: Security and trust claims are grouped as official vendor behavior, checked-in repository facts, or recommended practice.

**Rationale**: DOC-008 is user documentation, not a security audit or certification. Separating evidence type prevents overclaiming and lets evaluators distinguish platform guarantees from Racecraft-specific file inventory and derived guidance.

**Alternatives considered**:

- Control checklist: would look evaluator-friendly but risks implying an attestation.
- Threat model lite: useful for security readers but outside the DOC-008 documentation scope.

## Decision 4: Use Recovery Cases Instead Of A New Diagnostic Command

**Decision**: The update/rollback page defines update, refresh, reinstall, remove, rollback, stale payload, stale cache, and version-sync cases. Each case includes read-only checkpoint, manual operator action, expected side effect, reload/restart need, and source citation.

**Rationale**: The design concept and spec forbid a live diagnostic command, browser execution, local repair automation, CI workflow changes, or plugin behavior changes. Recovery docs can explain safe operator actions without changing runtime behavior.

**Alternatives considered**:

- Doctor command: better automation, but explicitly out of scope.
- Full maintainer playbook: too broad and overlaps DOC-009 release/contributor workflow.

## Decision 5: Prefer Generated DOC-007 References For Racecraft Facts

**Decision**: Racecraft source, manifest, skill, agent, hook, script, test, and source-vs-dist claims should link to generated DOC-007 reference pages when those pages cover the claim; otherwise cite checked-in source files directly.

**Rationale**: Generated reference pages already consolidate source facts for manifests, skills, agents, hooks, scripts, tests, and source-vs-dist responsibility. Linking to them avoids duplicating reference tables and keeps DOC-008 focused on user diagnosis and recovery.

**Alternatives considered**:

- Duplicate full reference tables: too much maintenance and drift risk.
- Link only raw source files: precise, but weaker for user-facing source-vs-dist explanation where generated references already summarize the facts.

## Decision 6: Official Platform Docs Verified During Plan

**Decision**: Current official vendor documentation was checked on 2026-06-18 and must be cited narrowly during implementation for platform behavior claims.

**Rationale**: Platform command names, plugin behavior, settings, environment variables, sandboxing, approvals, managed configuration, and cache behavior are temporally unstable. The implementation must cite the narrowest official page for each platform claim and must not cite vendor docs for Racecraft source or generated payload facts.

**Claude Code official docs checked**:

- [Discover and install prebuilt plugins](https://code.claude.com/docs/en/discover-plugins)
- [Create plugins](https://code.claude.com/docs/en/plugins)
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Settings](https://code.claude.com/docs/en/settings)
- [Environment variables](https://code.claude.com/docs/en/env-vars)
- [Permissions](https://code.claude.com/docs/en/permissions)
- [Sandbox environments](https://code.claude.com/docs/en/sandbox-environments)
- [Security](https://code.claude.com/docs/en/security)
- [Hooks](https://code.claude.com/docs/en/hooks)
- [Subagents](https://code.claude.com/docs/en/sub-agents)
- [Managed MCP](https://code.claude.com/docs/en/managed-mcp)

**OpenAI Codex official docs checked**:

- [Plugins](https://developers.openai.com/codex/plugins)
- [Build plugins](https://developers.openai.com/codex/plugins/build)
- [Agent Skills](https://developers.openai.com/codex/skills)
- [Subagents](https://developers.openai.com/codex/subagents)
- [Hooks](https://developers.openai.com/codex/hooks)
- [MCP](https://developers.openai.com/codex/mcp)
- [Config basics](https://developers.openai.com/codex/config-basic)
- [Config reference](https://developers.openai.com/codex/config-reference)
- [Environment variables](https://developers.openai.com/codex/environment-variables)
- [CLI reference](https://developers.openai.com/codex/cli/reference)
- [Sandbox](https://developers.openai.com/codex/concepts/sandboxing)
- [Permissions](https://developers.openai.com/codex/permissions)
- [Agent approvals & security](https://developers.openai.com/codex/agent-approvals-security)
- [Managed configuration](https://developers.openai.com/codex/enterprise/managed-configuration)
- [AGENTS.md](https://developers.openai.com/codex/guides/agents-md)

**Alternatives considered**:

- Use only links already listed in `spec.md`: lower effort, but does not satisfy current-doc verification.
- Avoid platform claims: safest, but the spec requires evaluator guidance for platform behavior.

## Decision 7: Validation Stays In Existing Docs-Site Commands

**Decision**: Verification uses `pnpm --dir docs-site reference:check`, `pnpm --dir docs-site validate`, `pnpm --dir docs-site validate:links`, and the combined full verification command. Plugin Layer 1 is conditional only if implementation touches plugin/spec surfaces, manifests, scripts, hooks, or generated payload paths.

**Rationale**: DOC-008 changes user-facing docs content and docs navigation only. Existing docs-site scripts already cover generated reference freshness, Astro content/type checks, production build, and link validation.

**Alternatives considered**:

- Full plugin suite: unnecessary for docs-only content unless implementation expands into plugin surfaces.
- Manual review only: insufficient for generated reference and link correctness.

# Phase 0 Research: Verification Coverage (TACD-004)

All NEEDS CLARIFICATION items were resolved in the spec via the pre-workflow Grill Me
interview (Q1–Q8) and encoded as functional requirements; this document records the
resulting design decisions, grounded in the actual repository state inspected during
planning. No open clarifications remain.

---

## Decision 1 — Named-tool guard placement and shape (FR-001, FR-002)

**Decision**: Host the named-tool regression guard in **Layer 5**
(`validate-tool-scoping.sh`) and remove the named-MCP requirement from Layer 5
**entirely**. The structural pointer/resolution checks live in **Layer 1** (Decisions
2–3). The guard scans active Claude agent source (`speckit-pro/agents/*.md`) and
active Codex agent source (`speckit-pro/codex-agents/*.toml`) for a hardcoded named
optional-tool preference outside the spike-approved category allowlist.

**Rationale**:
- The Layer 5 contract today is what encodes the named-vendor set. Lines 243–248 of
  `validate-tool-scoping.sh` REQUIRE `implement-executor` to carry
  `mcp__tavily-mcp__tavily-search`, `mcp__context7__resolve-library-id`,
  `mcp__context7__get-library-docs`, `mcp__RepoPrompt__file_search`, and
  `mcp__RepoPrompt__context_builder`. `implement-executor` is the **only** agent with a
  named-MCP requirement; every other agent already uses `assert_no_mcp`. Per Q4/FR-002,
  remove the five `mcp__*` lines from that loop and keep `WebSearch WebFetch` (the
  generic research capability). This is the surgical change the maintainability
  checklist calls for — it must not disturb the other Layer 5 expectations.
- The new guard belongs in the same file because tool/agent-capability scoping is
  Layer 5's domain; adding a second scanner elsewhere would violate the
  no-broad-scanner constraint.

**Allowlist (false-positive guards)** — the guard MUST NOT fire on:
- the **generic `mcp` / `MCP` vocabulary** (no vendor token attached);
- **exact schema/dependency metadata identifiers** that legitimately retain a concrete
  tool ID (platform schema, dependency metadata, exact file references, fixtures,
  historical provenance);
- the **spike-approved category allowlist** from the TACD-001 capability-discovery
  work (reused, not redefined — see `docs/ai/research/tool-agnostic-capability-discovery-spike.md`).

**Detection shape**: match a vendor-qualified pattern such as `mcp__<vendor>__<tool>`
where `<vendor>` is a specific named server (e.g., `tavily-mcp`, `context7`,
`RepoPrompt`), then subtract the allowlist above. A bare `mcp`/`MCP` word with no
`__<vendor>__` qualifier is allowed by construction.

**Non-vacuity (FR-012)**: a fixture in which an active agent names a specific
`mcp__<vendor>__*` tool outside the allowlist MUST make the guard FAIL; reverting it
returns the suite to green; generic-`mcp`-only content and schema/dependency IDs do
NOT trip it (spec US1 acceptance scenarios 1–3).

**Alternatives considered**:
- *A brand-new Layer for contract scanning* — rejected (violates "no new test layer").
- *A repo-wide grep scanner over all markdown* — rejected (violates "no broad
  scanner"; would flood on historical/provenance mentions the spec explicitly keeps).
- *Keeping the named set but marking it optional* — rejected; Q4 is an explicit full
  removal so the scoping contract no longer names a vendor set at all.

---

## Decision 2 — Pointer-coverage rule (FR-003)

**Decision**: "Points to the directive" = a **literal path match to
`capability-discovery.md`** in the agent's source body, PLUS a **small enumerated
approved-equivalent allowlist** built from the actual active-agent inventory. A
Layer 1 validator (`validate-capability-pointer.sh`) iterates the active-agent
inventory and asserts each agent either references `capability-discovery.md` by path
or appears in the enumerated approved-equivalent allowlist.

**Active-agent inventory** (the agents that ship in the built payloads and their
source; excludes archived/historical/provenance material per the spec assumption):
- Claude: `speckit-pro/agents/*.md` (e.g., `phase-executor`, `implement-executor`,
  `analyze-executor`, `checklist-executor`, `clarify-executor`, `codebase-analyst`,
  `consensus-synthesizer`, `domain-researcher`, `gate-validator`,
  `spec-context-analyst`, `uat-runbook-author`).
- Codex: `speckit-pro/codex-agents/*.toml` (the TOML agent templates, plus
  `autopilot-fast-helper`).

**Approved-equivalent allowlist policy**: kept as small as the inventory requires. If
every active agent references the directive directly, the allowlist is **empty**
(the spec's stated default). Plan does not pre-enumerate equivalents; the implement
phase fills the allowlist only with agents that legitimately carry a runtime-specific
equivalent (e.g., an agent that inlines the capability-first guidance rather than
linking the shared file). The allowlist is a literal, enumerated set in the validator
— not a heuristic — so it stays auditable.

**Non-vacuity (FR-012)**: an active agent that references neither
`capability-discovery.md` nor an enumerated equivalent MUST make pointer-coverage FAIL
and name the uncovered agent (spec US2 acceptance scenario 2).

**Rationale**: A literal path match is machine-checkable and unambiguous; an
enumerated allowlist (vs. a fuzzy "mentions capability discovery" heuristic) keeps the
check deterministic and prevents silent drift. Existing Layer 1 validators
(`validate-codex-parity.sh`) already iterate `AGENTS_DIR`/`CODEX_AGENTS_DIR`, so this
reuses an established discovery pattern.

**Alternatives considered**:
- *Semantic/keyword match for "capability discovery"* — rejected (non-deterministic,
  false positives/negatives).
- *Requiring the literal file reference with no allowlist* — rejected; the spec
  explicitly permits an enumerated approved equivalent for agents that carry one.

---

## Decision 3 — Target-resolution model against dist/** (FR-004)

**Decision**: Verify resolution against the **built payload layout**, not the source
tree. A Layer 1 validator (`validate-capability-resolution.sh`) confirms the directive
file exists at the path each runtime loads it from inside `dist/claude/speckit-pro/**`
and `dist/codex/speckit-pro/**`.

**Resolution targets confirmed present in the current build**:
- `dist/claude/speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`
- `dist/codex/speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`

**Resolution semantics**: Each pointer found in Decision 2 references the directive by
its **repo-root-relative source path** — verified across the current inventory, every
Claude `.md` agent cites
`` `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` `` and every
covered Codex `.toml` agent cites the same path inside its "Capability discovery
equivalent: mirrors speckit-pro/skills/…/capability-discovery.md …" line. There is **no**
runtime-relative (`../references/…`) reference in any active agent. Resolution is
therefore a **prefix re-rooting**, not a relative-path walk: extract the in-source path
token verbatim and assert the same token resolves under BOTH built trees — i.e.
`dist/claude/<source-path-token>` and `dist/codex/<source-path-token>` both exist (both
currently resolve to
`dist/<runtime>/speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`).
The check fails on a referenced path that is correct in source but absent in the built
payload — it must NOT pass on source-tree presence alone (spec edge case "Unresolved
payload path"; US2 acceptance scenarios 3–4). The check and the builder agree on the
re-rooting because the builder copies source under `dist/<runtime>/` preserving the
`speckit-pro/**` sub-path.

**Build dependency**: `validate-plugin-payload.sh` already rebuilds `dist/**` via the
builder and runs `git diff --exit-code -- dist` to prove the committed payload matches
source. The resolution check is the natural sibling: it asserts the *directive target*
resolves inside the rebuilt tree. It assumes `dist/**` is committed in sync (which the
payload-completeness check and the existing payload validator both enforce).

**Non-vacuity (FR-012)**: renaming/removing the directive at a referenced path inside
the built payload MUST make target-resolution FAIL for both Claude and Codex layouts.

**Alternatives considered**:
- *Resolve against source `speckit-pro/**` only* — rejected; the whole point (Q3) is to
  protect consumers who install the built payload, not just the source tree.

---

## Decision 4 — Payload-build fix shape: strip_codex_guard (FR-007)

**Decision**: Replace the single-line magic-terminator scan with a **section-boundary
scan**. Strip from the `## Codex Skill-Selection Guard` heading to the **next `## `
heading or EOF**, then regenerate `dist/**` from source via the builder.

**Root cause (confirmed by inspection)**: In
`scripts/build-plugin-payloads.sh`, `strip_codex_guard` (lines 71–94) finds the guard
heading (`lines[i] == "## Codex Skill-Selection Guard"`, line 77) then advances until a
line satisfies `"fallback guard was triggered." in line` (line 82). That terminator
phrase is **line-wrapped** in source — e.g., `speckit-autopilot/SKILL.md` lines 24–25
read `...report that the` / `fallback guard was triggered.` The substring check on a
single line never matches the split phrase, so the inner `while` consumes to EOF and
the strip truncates the entire body.

**Observed blast radius (current `dist/claude` vs source line counts)**:

| Skill | Source | dist (current) | Status |
|-------|-------:|----------------:|--------|
| grill-me | 386 | 11 | truncated |
| speckit-coach | 382 | 10 | truncated |
| speckit-install | 215 | 11 | truncated |
| speckit-prd | 365 | 11 | truncated |
| speckit-resolve-pr | 242 | 11 | truncated |
| speckit-scaffold-spec | 442 | 11 | truncated |
| speckit-status | 297 | 11 | truncated |
| speckit-upgrade | 351 | 11 | truncated |
| speckit-archive-cleanup | 150 | 141 | intact |
| speckit-autopilot | 698 | 683 | intact |

8 of 10 Claude skills currently install with empty bodies — a consumer-facing defect.
The two intact skills have a guard-block layout where the existing terminator scan
happens to stop correctly; the section-boundary scan handles both uniformly.

**Fix shape**: from the guard heading, skip the heading line, then consume lines until
the next line that `startswith("## ")` (the next section) OR EOF; do not emit the
consumed range. This removes only the guard section and is independent of the
terminator phrase's wrapping. The trailing special-case block (lines 86–90, "The Codex
variant must...") collapses into the same boundary logic. Edge case "Skill with no
guard block": a SKILL.md without the guard heading is left untouched (the `while` never
enters the strip branch).

**Regeneration (FR-013)**: after the fix, run `bash scripts/build-plugin-payloads.sh`
to regenerate all `dist/**` bodies. Payloads are NEVER hand-edited; the only
source→built difference is the stripped guard section.

**Alternatives considered**:
- *Un-wrap the terminator phrase in every source SKILL.md so the single-line check
  matches* — rejected; brittle (any future re-wrap reintroduces the bug) and touches
  shipped guidance wording, which is out of scope.
- *Match the terminator across joined lines* — rejected; still couples the strip to a
  magic phrase. A heading-to-heading boundary is the structural invariant.

---

## Decision 5 — Body-completeness assertion design (FR-008)

**Decision**: A Layer 1 validator (`validate-payload-completeness.sh`) asserts, for
every built Claude `SKILL.md`, a **structural invariant** plus a **tolerance band**,
in preference to a brittle absolute line count:

1. **Structural anchor**: the **last non-guard `##` heading** present in the source
   `SKILL.md` is also present in the built `dist/claude/**/SKILL.md`. (If the body were
   truncated to EOF, that trailing heading would be missing.)
2. **Length tolerance**: the built body length is **within tolerance of
   source-minus-guard** (source line count minus the stripped guard section, within a
   small slack). The only intended difference between source and built body is the
   stripped guard block.

**Rationale**: The structural anchor directly detects the failure mode (strip-to-EOF
drops the trailing real content). An absolute line count is brittle across skills of
different sizes and across legitimate guard-block size differences; anchoring on "the
last real heading survives" is deterministic and not flaky (reliability checklist
concern). The tolerance band is a secondary guard against a partial mid-body
truncation that happened to preserve the final heading.

**Computing source-minus-guard**: reuse the same section-boundary definition as the
fixed `strip_codex_guard` (heading → next `## ` heading/EOF) so the check and the
builder agree on what "the guard section" is. This keeps the assertion coupled to the
fix's invariant rather than to a hardcoded number.

**Scope**: the check targets the **Claude** payload (`dist/claude/**`), which is where
the defect occurs (the Codex variant is the guard's fallback target and is built
differently). Codex parity for the *pointer/resolution* checks is covered by Decisions
2–3; FR-009 parity for evals is Decision 6.

**Non-vacuity (FR-012)**: a deliberately truncated built `SKILL.md` (trailing heading
removed / body cut) MUST make the check FAIL and identify the truncated skill (spec US4
acceptance scenario 3).

**Determinism (FR-010)**: runs in the default Layer 1 suite; no live model run.

**Alternatives considered**:
- *Absolute line-count equality* — rejected (brittle/flaky across skills).
- *Byte-identical source==built* — rejected; the guard section is legitimately
  stripped, so they are never byte-identical.

---

## Decision 6 — Eval rewrite + behavior scenarios (FR-005, FR-006, FR-009)

**Decision**: Rewrite the optional-tool expectations in all four eval files so each
asserts BOTH (a) the **absence** of a preferred named-tool set AND (b) an
**affirmative capability-first** answer; add **five behavior-observable scenarios** as
committed replay fixtures; hold **Claude/Codex parity** across the four files. No live
`claude -p` run gates merge.

**Eval file schema (confirmed)**: each file is
`{ "skill_name": <str>, "evals": [ { "id", "prompt", "expected_output",
"expectations": [<str>, ...] } ] }`. All four files
(`evals/speckit-autopilot-evals.json`, `evals/speckit-coach-evals.json`, and the
`codex-evals/` counterparts) currently contain named-tool mentions
(Tavily/Context7/RepoPrompt) and must be rewritten.

**Rewrite rule (FR-005)** for each optional-tool `expected_output`/`expectations`:
- **Absence arm**: assert the answer does NOT prescribe a specific named-tool set
  (no Tavily/Context7/RepoPrompt preference).
- **Affirmative arm**: assert the answer describes installed-capability discovery and
  vendor-neutral fallback behavior (capability-first).

**Five behavior-observable scenarios (FR-006)** added as fixtures:
1. installed-capability discovery,
2. fallback when named tools are unavailable,
3. evidence path,
4. citations / local-file references,
5. lowered confidence when fallback quality is lower.

Each validates against committed fixtures with no live model run (Q7); the spec is
explicit that no scenario depends on a live runner.

**Parity (FR-009)**: the same scenario has equivalent expectations across Claude and
Codex for both the autopilot and coach skills. The implement phase mirrors each edit
across the `evals/` and `codex-evals/` pair.

**Validation mode**: these are Layer 3 functional eval fixtures consumed by the
replay/committed-fixture path; the **default deterministic suite (Layers 1/4/5) stays
green without them** (FR-010). The eval rewrites are JSON-content changes — the JSON
must remain valid and the existing eval runners must continue to parse it.

**Alternatives considered**:
- *Absence-only assertions* — rejected; Q8/FR-005 require BOTH absence and an
  affirmative capability-first answer so the evals can't drift back to teaching a
  named preference while still "passing" by omission.
- *A live `claude -p` gate for the five scenarios* — rejected (Q7); replay/committed
  fixtures are sufficient and no live run gates merge.

---

## Cross-cutting constraints (carried into Tasks)

- **Extend in place**: all new checks land in Layers 1 and 5; `run-all.sh` is updated
  only to register the new Layer 1 validators. No new layer, no broad scanner (FR-011).
- **TDD / non-vacuity**: each guard starts from a failing regression fixture, then the
  check is implemented to pass (FR-012).
- **dist from source only**: regenerate via the builder; never hand-edit (FR-013).
- **No scope drift**: no agent decision-logic, prerequisite-script, or docs-wording
  changes (spec Out of Scope).

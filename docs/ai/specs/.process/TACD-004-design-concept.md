---
topic: "TACD-004 Verification Coverage"
slug: "tacd-004-verification-coverage"
date: "2026-06-19"
mode: "setup"
spec_id: "TACD-004"
source_input:
  type: "file"
  ref: "docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md"
question_count: 8
stop_reason: "natural"
---

# Design Concept: TACD-004 Verification Coverage

> **Source:** docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md
> **Date:** 2026-06-19
> **Questions asked:** 8
> **Stop reason:** natural

## Goals

- Add deterministic checks that FAIL when active runtime guidance reintroduces a hardcoded named optional-tool contract outside the TACD-001 category allowlist, so the vendor-neutral contract from TACD-002/TACD-003 cannot silently regress.
- Host the named-tool regression guard in Layer 5 (tool scoping) and the directive pointer-coverage / structural checks in Layer 1, matching each layer's existing purpose.
- Prove every active Claude and Codex agent points to the shared `capability-discovery.md` directive or an approved runtime-specific equivalent, using a path/string match plus a small enumerated allowlist for legitimate exceptions.
- Prove those directive pointers actually resolve from the installed runtime layout by checking the referenced file exists at the path each agent loads it from inside `dist/claude/**` and `dist/codex/**`.
- Rework the Layer 5 block that currently REQUIRES `mcp__tavily-mcp__*`, `mcp__context7__*`, and `mcp__RepoPrompt__*` by name so those named-tool assertions are removed entirely from the scoping contract.
- Rewrite the optional-tool eval expected outputs across all four eval files (autopilot + coach, Claude + Codex) so answers assert BOTH the absence of a preferred Tavily/Context7/RepoPrompt set AND an affirmative capability-first discovery answer.
- Add behavior-observable eval scenarios for installed-capability discovery, fallback when named tools are unavailable, evidence path, citations/local-file references, and lowered confidence when fallback quality is lower — validated against committed fixtures (replay), with no live `claude -p` gating the merge.
- **Fix the Claude payload-build defect and lock it with verification:** repair `strip_codex_guard` in `scripts/build-plugin-payloads.sh` so it strips only the Codex guard block (to the next heading) instead of truncating to end-of-file, rebuild `dist/`, and add a deterministic body-completeness check so a truncated Claude SKILL.md can never ship silently again.
- Keep the default deterministic suite (`bash tests/speckit-pro/run-all.sh`, Layers 1/4/5) green; do not depend on live AI eval execution for the slice to be considered verified.

## Non-goals

- Live AI eval execution as a merge gate — answered in Q7 (Eval proof bar): replay/committed-fixture validation is sufficient; the implementation PR may optionally run the slower local suite.
- New test layers or broad harness rewrites — the work extends Layers 1/4/5 in place.
- Behavior changes outside the directive and messaging already implemented by TACD-002 and TACD-003 (no agent decision-logic changes, no prerequisite-script behavior changes, no docs-wording changes).
- Keeping the formerly-named MCP tools as REQUIRED assertions — answered in Q4 (Layer-5 MCPs): the named-tool assertions are removed entirely, not retained as optional.
- Deleting or rewriting historical/provenance mentions (PRD, roadmap, changelog, archives, intentionally-historical fixtures) merely because they contain older named tools.
- Hand-editing generated `dist/**` payload copies as a source of truth; generated source-derived duplicates are regenerated from source by the build script.
- A separate hotfix branch for the payload bug — answered in Q5 (Sequencing): the fix, the `dist/` rebuild, and the regression check are bundled into TACD-004 rather than fast-tracked.

## Design Tree (Q&A log)

### Q1. Which test layer(s) should host the named-tool regression guard and the directive pointer-coverage checks?

**Branch:** Verification layering

**Recommended answer:** Split: Layer 5 + Layer 1
> The named-tool contract already lives in Layer 5 (`validate-tool-scoping.sh`), and file/structure existence checks already live in Layer 1. Hosting each concern in its established layer avoids overloading tool-scoping with structural logic.

**Alternatives offered:**
- Layer 5 only: Extend `validate-tool-scoping.sh` for both concerns; one file to touch but overloads tool scoping with structural checks.
- New Layer 1 validator only: One fresh structural validator; clean separation but leaves the stale named-MCP assertions in Layer 5 unaddressed.

**User's answer:** Split: Layer 5 + Layer 1

---

### Q2. What is the machine-checkable definition of an agent "pointing to the shared directive or an approved runtime-specific equivalent"?

**Branch:** Pointer contract

**Recommended answer:** Path match + approved-equivalent allowlist
> Require a literal reference to `references/capability-discovery.md`; for agents that legitimately cannot (e.g. a runtime-specific surface), maintain a small enumerated allowlist of approved equivalents. Flexible, explicit, and auditable without forcing frontmatter churn.

**Alternatives offered:**
- Strict path/string match only: Every active agent must contain the literal path; simplest to check but brittle for runtime-specific agents.
- Frontmatter field: Require a dedicated frontmatter key on each agent; most structured but requires editing every agent's frontmatter.

**User's answer:** Path match + approved-equivalent allowlist

---

### Q3. How should "target resolution from the installed runtime context" be tested deterministically without a live runtime?

**Branch:** Resolution testing

**Recommended answer:** Resolve against dist/** payload layout
> Verify the referenced directive file actually exists at the path each agent would load it from inside `dist/claude/**` and `dist/codex/**` — the artifacts consumers install. Proves real install-time reachability, not just source-tree presence.

**Alternatives offered:**
- Resolve against source tree only: Check the path exists relative to `speckit-pro/`; simpler but does not prove the generated payload is correct.
- Live runtime probe: Spin up each runtime and confirm the directive loads; most faithful but non-deterministic and effectively out of scope.

**User's answer:** Resolve against dist/** payload layout

---

### Q4. After TACD-004, how should the formerly-required named MCP tools be treated in the Layer 5 contract?

**Branch:** Tool-scoping contract

**Recommended answer:** Allowed, not required
> Dropping the named tools as REQUIRED assertions while keeping them permitted preserves backward-compatible best-available behavior and removes vendor lock-in from the contract.

**Alternatives offered:**
- Remove named-tool assertions entirely: Strip all references to the specific MCP tool names from the scoping contract; cleanest vendor-neutrality but loses the explicit record that those tools are acceptable.

**User's answer:** Remove named-tool assertions entirely
> The user chose full removal over allowed-not-required: the scoping contract should carry no specific vendor MCP tool names at all, so vendor neutrality is enforced at the contract level rather than relying on an "optional but named" list.

---

### Q5. The Claude payload-build defect ships now (8 of 10 skills install with empty bodies). How should the fix be sequenced against TACD-004?

**Branch:** Payload bug scope

**Recommended answer:** Hotfix now + regression check in TACD-004
> An immediate `fix(speckit-pro):` PR would restore the 8 skills for current users today, while TACD-004 adds the deterministic regression check — fastest user relief and keeps TACD-004 a clean verification spec.

**Alternatives offered:**
- Hotfix only, skip the check: Fix + rebuild now with no regression test; smallest change but nothing prevents recurrence.

**User's answer:** Bundle everything into TACD-004
> The user chose to fold the build-script fix, the `dist/` rebuild, and the body-completeness regression check all into the TACD-004 PR. Tradeoff acknowledged during the interview: the 8 skills remain broken in the installed plugin until TACD-004 merges. This makes the payload-build correctness fix in-scope for this spec, alongside the vendor-neutrality verification work.

---

### Q6. What should the new deterministic payload check assert so the truncation can never silently recur?

**Branch:** Payload verification

**Recommended answer:** Body-completeness vs source
> Assert every `dist/claude` SKILL.md retains its source body minus only the Codex guard section — e.g. the last source `##` heading still appears and the body line-count is within tolerance of source-minus-guard. Catches truncation directly, including partial truncation.

**Alternatives offered:**
- Non-trivial floor: Assert each payload SKILL.md body exceeds a minimum size; simple but coarse, misses partial mid-file truncation.
- Round-trip on the function: Re-run `strip_codex_guard` in-test and assert only the guard block is removed; most precise but couples the test to the implementation.

**User's answer:** Body-completeness vs source

---

### Q7. Is committed-fixture/replay validation enough for the behavior-observable eval scenarios, or must a live `claude -p` pass be captured before merge?

**Branch:** Eval proof bar

**Recommended answer:** Replay-only fixtures acceptable
> The roadmap scope-out lists live AI eval as optional, and Layers 2/3/6 are developer-local only. Validating the five behavior scenarios against committed fixtures keeps the default suite deterministic while still proving the expected behavior shape.

**Alternatives offered:**
- Require one live `claude -p`: Capture at least one live pass before merge; stronger behavioral proof but adds a non-deterministic, developer-local gating step.

**User's answer:** Replay-only fixtures acceptable

---

### Q8. How should the rewritten eval expected outputs express vendor-neutrality across the four eval files?

**Branch:** Eval wording

**Recommended answer:** Absence + affirmative
> Assert BOTH that no preferred Tavily/Context7/RepoPrompt set is named AND that the answer affirmatively describes capability-first discovery (referencing the capability categories). Catches regressions in either direction — a vague non-answer and a re-introduced vendor list both fail.

**Alternatives offered:**
- Assert absence only: Only check the vendor names are absent; simpler but a vague non-answer could pass.
- Affirmatively name categories: Require enumerating the capability categories; most prescriptive but brittle if the category list evolves.

**User's answer:** Absence + affirmative

## Open Questions

- **What:** The exact tolerance and anchor for the body-completeness check (e.g. "last source `##` heading present" vs. a line-count delta threshold).
  **Why deferred:** The implementation should derive the most robust, least-flaky assertion from the real source-vs-payload diff after `strip_codex_guard` is fixed.
  **Suggested next step:** Resolve during Plan/Implement; prefer a structural anchor (last non-guard heading survives) over a brittle absolute line count.

- **What:** The precise contents of the approved runtime-specific-equivalent allowlist for the pointer-coverage check (which agents, if any, legitimately cannot reference `capability-discovery.md` directly).
  **Why deferred:** Requires enumerating the current active Claude and Codex agents during Plan and confirming which need an equivalent.
  **Suggested next step:** Build the allowlist from the actual agent inventory during Plan; keep it as small as the evidence requires.

- **What:** The exact vendor-neutral phrasing for the rewritten eval `expected_outputs` across the four files.
  **Why deferred:** Final copy should be derived from the existing eval JSON shape and the `capability-discovery.md` category language.
  **Suggested next step:** Resolve during Implement; keep each expected output both absence-asserting and affirmatively capability-first.

## Recommended Next Step

Continue `/speckit-pro:speckit-scaffold-spec TACD-004` by generating the setup workflow file and SPEC-MOC marker, then run `/speckit-pro:speckit-autopilot docs/ai/specs/.process/TACD-004-workflow.md`. TACD-004 is the final spec in the roadmap; its scope now also includes the Claude payload-build fix and its regression check.

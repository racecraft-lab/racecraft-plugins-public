---
topic: "Reviewer-ready PR packet contract"
slug: "prsg-012-reviewer-ready-pr-packet-contract"
date: "2026-06-11"
mode: "setup"
spec_id: "PRSG-012"
source_input:
  type: "file"
  ref: "docs/ai/specs/pr-size-governance-technical-roadmap.md (PRSG-012 section)"
question_count: 8
stop_reason: "natural"
---

# Design Concept: Reviewer-ready PR packet contract

> **Source:** `docs/ai/specs/pr-size-governance-technical-roadmap.md` (PRSG-012 section)
> **Date:** 2026-06-11
> **Questions asked:** 8
> **Stop reason:** natural

## Goals

- Enforce reviewer-ready PR titles and bodies before any `gh pr create` path runs.
- Use one shared deterministic validator for both single-PR and split-PR emission.
- Make each generated PR packet own its title, body file, evidence, scope, UAT content, and validation result.
- Generate canonical, neutral reviewer sections that explain what changed, why it matters, how to review, how to UAT, verification, scope, and known gaps.
- Preserve the existing literal `## UAT Runbook` heading while adding a clearer `How To UAT` section for reviewers.
- Allow refinement only inside explicit editable prose fields while preserving generated governance sections and source markers.
- Record validation failures as deterministic JSON plus a concise workflow event so the run can resume without creating an invalid PR.
- Keep PRSG-012 as a single slice. The advisory estimator returned `{"estimated_loc":245,"suggested_slices":1,"status":"ok"}`.

## Non-goals

- Broad post-create PR title/body repair is out of scope for PRSG-012; it is recorded as a follow-up idea.
- Agent-authored first drafts are out of scope; scripts own the first draft from deterministic evidence.
- Replacing the existing `## UAT Runbook` compatibility heading is out of scope.
- Treating host PR templates as the primary packet contract is out of scope; canonical generated sections own the contract.
- Advisory-only validation is out of scope; invalid packets must block before PR creation.

## Design Tree (Q&A log)

### Q1. Where should PRSG-012 put the pre-create PR packet validation logic?

**Branch:** Validation architecture

**Recommended answer:** Shared script
> Add one deterministic validator script that both single-PR and split-PR paths invoke before any `gh pr create` call. This matches the repo's scripts-first rule and keeps behavior testable in Layer 4.

**Alternatives offered:**
- Inline checks: Smaller now, but risks drift between `generate-pr-body.sh` and `multi-pr-emission.sh`.
- Schema only: Validates JSON shape but leaves rendered title/body placeholders and wording issues less protected.

**User's answer:** Shared script (Recommended)

---

### Q2. How should PRSG-012 generate PR titles for both single-PR and split-PR paths?

**Branch:** Title ownership

**Recommended answer:** Packet-owned title
> Add an explicit generated title field to the PR packet or slice packet and require `gh pr create --title` to consume that field. This makes the title part of the validated packet, not an ad hoc create-time choice.

**Alternatives offered:**
- Derive at create: Avoids a field but duplicates logic across PR paths.
- Human edits title: Preserves flexibility but weakens determinism.

**User's answer:** Packet-owned title (Recommended)

---

### Q3. What should the generated PR body structure be after PRSG-012?

**Branch:** Body contract

**Recommended answer:** Canonical sections
> Generate the required reviewer sections directly and validate exact headings. Host-template content can be preserved only when it does not weaken the contract.

**Alternatives offered:**
- Template plus fills: Less disruptive, but harder to validate consistently.
- Append contract: Preserves compatibility, but can bury the useful content.

**User's answer:** Canonical sections (Recommended)

---

### Q4. How should PRSG-012 handle the existing UAT Runbook heading while adding the new How To UAT section?

**Branch:** UAT compatibility

**Recommended answer:** Keep both
> Make `How To UAT` the reviewer-facing section and keep a literal `## UAT Runbook` subsection or sibling heading for compatibility with existing checks and SPEC-006a/b guarantees.

**Alternatives offered:**
- Replace heading: Cleaner, but requires coordinated updates to prior guarantees and evals.
- Link only: Compact, but less useful for reviewers in the PR view.

**User's answer:** Keep both (Recommended)

---

### Q5. How should PRSG-012 allow human or agent refinement of generated PR body prose?

**Branch:** Safe prose refinement

**Recommended answer:** Editable fields only
> Use explicit editable prose blocks for Summary and reviewer notes. The validator rejects edits that remove source markers, UAT, traceability, verification, or scope sections.

**Alternatives offered:**
- Any prose section: Easier to use, but can accidentally damage governance content.
- No edits: Most deterministic, but likely produces less useful reviewer prose.

**User's answer:** Editable fields only (Recommended)

---

### Q6. When PR packet validation fails, what evidence should PRSG-012 write before stopping?

**Branch:** Failure evidence

**Recommended answer:** JSON plus log
> Write a deterministic validation JSON under the feature `.process` directory and append a concise workflow event with exact remediation. This supports resume and fixture testing.

**Alternatives offered:**
- Log only: Simpler, but weaker for resume and test fixtures.
- Body comments: May help local repair, but risks stale invalid packets being reused.

**User's answer:** JSON plus log (Recommended)

---

### Q7. Should PRSG-012 include any post-create repair behavior after a PR has already been opened?

**Branch:** Post-create scope

**Recommended answer:** Pre-create only
> Block invalid packets before PR creation and leave existing post-create review remediation behavior unchanged. This matches the roadmap's pre-create contract.

**Alternatives offered:**
- Auto-repair PRs: Broader and riskier; it adds post-create mutation semantics.
- Advisory audit: Helpful for diagnosis, but does not enforce the contract.

**User's answer:** Auto-repair PRs

**Notes:** This answer expanded scope beyond the roadmap and triggered a follow-up.

---

### Q8. How should the workflow handle auto-repair without blowing up PRSG-012 scope?

**Branch:** Post-create scope correction

**Recommended answer:** Follow-up only
> Record post-create auto-repair as a future follow-up; PRSG-012 enforces the pre-create contract only.

**Alternatives offered:**
- Current spec narrow: Include auto-repair only for PRs created in the same run when validation metadata proves the generated fields are safe to edit.
- Current spec broad: Include repair for any existing PR title/body, which is much larger and harder to validate safely.

**User's answer:** Follow-up only (Recommended)

## Open Questions

- **What:** Exact JSON schema name and fields for the validated PR packet.
  **Why deferred:** The design choice is settled at the architecture level; the precise field list belongs in Plan.
  **Suggested next step:** During Plan, decide whether to extend `slice-packet.schema.json` directly or introduce a dedicated `pr-packet.schema.json` consumed by both paths.
- **What:** Exact title wording algorithm.
  **Why deferred:** The packet owns the title, but the final conventional-commit mapping should be derived from the generated spec and implementation plan.
  **Suggested next step:** During Plan, define title sources for single PRs and slice PRs, then pin them with Layer 4 fixtures.
- **What:** Post-create auto-repair behavior.
  **Why deferred:** It is useful but outside PRSG-012's pre-create contract and budget.
  **Suggested next step:** Track as a follow-up roadmap item after PRSG-012 proves the packet metadata is stable.

## Recommended Next Step

Run setup-mode autopilot from the PRSG-012 worktree with:

```bash
$speckit-autopilot docs/ai/specs/.process/PRSG-012-workflow.md
```

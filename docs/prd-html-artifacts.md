# PRD: HTML Artifacts & Staged Review Workflow

**Status**: Active — not yet implemented
**Source**: Anthropic field guide ("A Field Guide to Claude Fable: Finding Your Unknowns"), "The Unreasonable Effectiveness of HTML" (claude.com/blog), the HTML-effectiveness template gallery (thariqs.github.io/html-effectiveness, github.com/anthropics/html-effectiveness), and the 2026-07-28 speckit-prd interview
**Created**: 2026-07-28
**Last updated**: 2026-07-28
**Target window**: Next speckit-pro minor-release train; no external deadline

---

## 1. Problem

> "As a SpecKit-Pro operator, I approve an implementation I have never really *seen* — dense markdown specs go in, a finished PR comes out, and my first genuine review moment is after the code is already written."

Today the chain runs scaffold (interactive grill-me) → autopilot (all 7 SDD
phases plus PR creation) in one autonomous stretch. The operator's
understanding of *what is about to be built* rests on reading `spec.md`,
`plan.md`, and `tasks.md` — long markdown documents the research shows people
skim rather than absorb. There is no deliberate human checkpoint between
"planning finished" and "implementation started", and the delivered PR explains
itself through a markdown UAT runbook with the same readability ceiling. The
field guide's thesis is that work quality is bottlenecked by clarifying
unknowns *before* they get expensive; the HTML-effectiveness research shows
dense, visual, interactive single-file artifacts are the cheapest way to make a
human genuinely understand — and react to — an agent's plan. SpecKit-Pro
currently uses neither.

## 2. Goals & Non-goals

### 2.1 Goals

- Operators fully understand what is about to be implemented **before**
  implementation runs: the planning stage ends at a **draft PR** carrying
  branded, interactive HTML artifacts (implementation plan, spec explainer,
  and conditional companions).
- The workflow gains a real human checkpoint: feedback left on the draft PR is
  ingested, resolved through the existing consensus machinery, and re-presented
  for review before any code is written; a clean draft PR flows straight into
  implementation.
- Final PRs explain themselves: a PR writeup, an interactive UAT walkthrough
  (replacing the markdown UAT runbook), and conditional companions ship with
  every completed spec.
- All 20 upstream HTML-effectiveness templates are available inside the plugin
  as Racecraft-branded, self-contained single-file SPA templates with routing
  metadata, leverageable by the staged workflow and ad hoc.
- Two Field Guide unknown-finding techniques join the workflow: a **blind-spot
  pass** before grill-me and **implementation-notes capture** during the
  implement stage.
- Claude Code and Codex CLI operators run the same staged workflow (parity
  woven into every SPEC).

### 2.2 Non-goals (out of scope)

- **Artifact hosting infrastructure** (GitHub Pages, htmlpreview/raw.githack
  links, claude.ai artifact publishing) — artifacts render locally over
  `file://`; hosting is a possible future PRD.
- **Comprehension-quiz artifact** — deferred; revisit after the core artifact
  set proves out.
- **Retro-fitting legacy specs** — merged specs, existing UAT runbooks, and
  in-flight worktrees keep their current artifacts; no migration.
- **Changes to grill-me's core interview machinery** — the blind-spot pass
  feeds it; it does not change it.
- **Live-data / server-backed artifacts** — static single-file SPAs only.
- **Embedded font payloads** — Google Fonts `<link>` with system-stack
  fallbacks; no woff2 embedding.
- **Automated upstream re-sync of the template gallery** — the port is a
  one-time branded derivation with provenance headers.
- **Rewrites of the consensus protocol, gate semantics, TDD protocol, or PRSG
  marker-split internals** — this effort wires into them; it does not redesign
  them.

## 3. Acceptance Criteria

### 3.1 Artifact Brand Kit & Gallery Foundation *(→ ART-001)*

- **AC-1.1**: A plugin-shipped brand kit exists: a CSS custom-property token
  block (70-20-10 palette — warm-neutral scale, brand red `#dc143c` as
  punctuation, brand blue `#3c89c6` accents — plus GTO90 dark-mode set),
  typography stacks (Space Grotesk headings, Geist body, Fira Code mono via
  Google Fonts `<link>` with `font-display: swap` and system fallbacks), a
  brand-voice cheat-sheet, and accessibility rules (AA contrast, visible focus
  ring, reduced-motion guard). Provenance headers cite the sources
  (racecraft-lab/racecraft `docs/brand/*` and this repo's
  `docs-site/src/styles/brand.css`).
- **AC-1.2**: A gallery routing manifest (JSON) enumerates every template with
  id, category, title, when-to-use, consuming workflow stage
  (`draft-pr` | `final-pr` | `ad-hoc`), and conditional trigger; Layer-1
  structural validation covers the manifest.
- **AC-1.3**: A single-file-SPA contract document states the constraints (all
  behavior and data inline; `fonts.googleapis.com`/`fonts.gstatic.com` are the
  only permitted external references; must render over `file://` with no
  console errors), and an automated repo test verifies every gallery template
  against the external-reference rule.
- **AC-1.4**: The kit, manifest, and contract live in a platform-neutral
  plugin path consumed identically by `skills/` and `codex-skills/` variants.

### 3.2 Draft-PR Template Set *(→ ART-002)*

- **AC-2.1**: Branded derivatives of upstream templates 16 (implementation
  plan), 14 (feature/spec explainer), 01 (code-approaches comparison), and 04
  (module map) exist in the gallery, each a self-contained single-file SPA
  using the brand kit.
- **AC-2.2**: Each template documents its fill regions (the slots an authoring
  agent populates from `spec.md`, `plan.md`, `tasks.md`, and the design
  concept).
- **AC-2.3**: Each passes the AC-1.3 external-reference test and renders over
  `file://` without console errors.
- **AC-2.4**: Manifest routing: implementation plan and spec explainer are
  `draft-pr`/always; code-approaches is `draft-pr`/conditional (plan recorded
  competing approaches); module map is `draft-pr`/conditional (brownfield spec
  touching existing modules).

### 3.3 Final-PR Template Set *(→ ART-003)*

- **AC-3.1**: Branded derivatives of upstream templates 17 (PR writeup), 03
  (annotated diff), and 13 (flowchart) exist under the same SPA constraints.
- **AC-3.2**: The PR-writeup template carries a dedicated implementation-notes
  section slot (fed by ART-012).
- **AC-3.3**: The annotated-diff template renders a unified diff with margin
  annotations, severity tags, and jump links.
- **AC-3.4**: Manifest routing: PR writeup is `final-pr`/always; annotated
  diff and flowchart are `final-pr`/conditional.

### 3.4 Gallery Completion: Design & Prototyping *(→ ART-004)*

- **AC-4.1**: Branded derivatives of upstream templates 02 (visual designs),
  05 (design system), 06 (component variants), 07 (animation prototype), 08
  (interaction prototype), and 10 (SVG illustrations) exist and pass the
  AC-1.3 test.
- **AC-4.2**: Manifest lists all six as `ad-hoc` with when-to-use guidance.

### 3.5 Gallery Completion: Knowledge, Reports & Editors *(→ ART-005)*

- **AC-5.1**: Branded derivatives of upstream templates 09 (slide deck), 15
  (concept explainer), 11 (status report), 12 (incident report), 18 (triage
  board), 19 (feature flags), and 20 (prompt tuner) exist and pass the AC-1.3
  test; the three editors keep working export-back buttons (copy as
  markdown/JSON).
- **AC-5.2**: Manifest lists all seven as `ad-hoc` with when-to-use guidance.

### 3.6 Autopilot Staging *(→ ART-006)*

- **AC-6.1**: Autopilot accepts `--stage plan|implement|full`: `plan` runs
  specify → clarify → plan → checklist → tasks → analyze; `implement` runs
  implement → post-implementation; `full` preserves today's single-run
  behavior.
- **AC-6.2**: A bare invocation auto-detects the stage: phases 1–6 complete
  plus an existing draft PR → `implement`; otherwise `plan` from the first
  pending phase. The workflow file is the authoritative signal; the PR state
  is corroboration.
- **AC-6.3**: The workflow file records stage state durably; `--from-phase`
  continues to resume within a stage; gate semantics (G0–G7, G6.5) are
  unchanged.
- **AC-6.4**: The scaffold → autopilot chain contract is documented and
  implemented on both platforms.

### 3.7 Draft-PR Emission *(→ ART-007)*

- **AC-7.1**: The plan stage's terminal step generates the draft artifact set
  per manifest routing into `specs/<branch>/artifacts/` and commits it.
- **AC-7.2**: A **draft** PR opens through the packet machinery with a
  gate-valid title and a body carrying an Artifacts index table (artifact,
  purpose, copy-paste open command).
- **AC-7.3**: Artifact generation is fail-open: on generation failure the
  draft PR still opens and the gap is logged in the workflow file.
- **AC-7.4**: The plan stage ends with a stop report: draft-PR URL, artifact
  index, and the resume instruction (review, leave feedback or run autopilot).

### 3.8 Feedback Sweep *(→ ART-008)*

- **AC-8.1**: The implement stage opens with a feedback sweep reading
  unresolved draft-PR comments via `gh`; zero unresolved feedback proceeds
  directly to implementation.
- **AC-8.2**: Substantive feedback routes through the existing consensus
  machinery to amend `spec.md`/`plan.md`/`tasks.md`; affected artifacts
  regenerate; changes are committed and pushed.
- **AC-8.3**: When amendments occurred, the run STOPS with a re-review report
  and does not implement; a subsequent clean run proceeds.
- **AC-8.4**: Sweep decisions land as Consensus Resolution Log rows in the
  workflow file.

### 3.9 UAT Walkthrough Replacement *(→ ART-009)*

- **AC-9.1**: A repo-authored UAT-walkthrough template exists in the gallery:
  an interactive checklist SPA with numbered steps and observable expected
  results per user story, env-setup prose, an FR coverage matrix, per-step
  pass/fail toggles, and a copy-results-as-markdown export button.
- **AC-9.2**: `uat-runbook-author` is replaced by `uat-artifact-author` on
  both platforms; the post-implementation task list references the artifact
  step.
- **AC-9.3**: The markdown UAT-runbook path is retired from the
  post-implementation flow; fail-open behavior is preserved (artifact failure
  never blocks the PR).
- **AC-9.4**: Exported UAT results follow a fixed markdown schema the review
  loop can parse from a PR comment.

### 3.10 Final-PR Writeup, Companions & Ready Flip *(→ ART-010)*

- **AC-10.1**: Post-implementation generates the PR writeup (always), its
  implementation-notes section populated from the ART-012 record.
- **AC-10.2**: The annotated diff is emitted when self-review recorded
  findings or the diff is large; the flowchart is emitted when the spec
  changed an operational flow.
- **AC-10.3**: The existing draft PR is updated in place (body artifact index
  refreshed) and flipped to ready-for-review; no duplicate PR is created.
- **AC-10.4**: The final reviewability gate and packet validation still
  govern PR readiness; the marker-split interaction follows the OQ-1
  resolution.

### 3.11 Scaffold Integration *(→ ART-011)*

- **AC-11.1**: Scaffold runs a read-only blind-spot pass over the roadmap
  scope and affected code area before grill-me; findings are shown to the
  operator and seeded into the interview and the design concept's Open
  Questions.
- **AC-11.2**: After the workflow-file commit, scaffold chains into the
  autopilot plan stage in-session; the operator can decline the chain at an
  explicit confirmation.
- **AC-11.3**: The scaffold closing report shows the draft-PR URL, the
  artifact index, and the next step (review, then run autopilot).
- **AC-11.4**: Both platform variants implement the same flow.

### 3.12 Implementation-Notes Capture *(→ ART-012)*

- **AC-12.1**: Implement-phase dispatch instructs every implementation
  executor to report deviations from plan, discovered edge cases, and
  surprises; the orchestrator appends them to a notes record under the
  feature's `.process/` directory.
- **AC-12.2**: The notes record feeds the PR writeup (AC-10.1) and the
  retrospective extension when installed.
- **AC-12.3**: An implement stage with no deviations records an explicit
  "no deviations" entry rather than an absent file.

### 3.13 Documentation *(→ ART-013)*

- **AC-13.1**: A docs-site gallery page documents every template (purpose,
  when-to-use, stage routing).
- **AC-13.2**: Operator-facing workflow documentation (docs-site + plugin
  README) describes the staged scaffold → draft PR → autopilot flow.
- **AC-13.3**: `pnpm --dir docs-site validate` passes.

## 4. Migration Path (phased — one phase per tier)

- **Phase 1 (ART-001) — Foundation**: brand kit, manifest schema, SPA
  contract; everything downstream consumes it.
- **Phase 2 (ART-002…005 ∥ ART-006) — Gallery + staging**: template ports
  proceed in parallel with the autopilot staging refactor; neither depends on
  the other.
- **Phase 3 (ART-007) — Draft PR**: the plan stage terminal step; needs the
  draft-PR template set and staging.
- **Phase 4 (ART-008, ART-009, ART-011, ART-012) — Review loop & delivery
  inputs**: feedback sweep, UAT walkthrough, scaffold chain, notes capture;
  parallel after Phase 3.
- **Phase 5 (ART-010) — Final PR**: writeup, companions, ready flip;
  integrates Phases 3–4.
- **Phase 6 (ART-013) — Docs**: lands last, documents shipped behavior.

## 5. Constraints

- **Constitution** (`.specify/memory/constitution.md` v1.2.0): plugin
  structure compliance (Layer 1), Python 3.11+ stdlib-only tooling with no new
  active Bash/`jq` dependencies (Layer 4), semver via release-please,
  Layer 1/4/5 test coverage before merge, conventional-commit PR titles,
  KISS/YAGNI.
- **Generated-artifact contract**: every shipped-byte change (templates, brand
  kit, skill files, agents) must account for the payload/proof regeneration
  ritual before merge.
- **Reviewability contract**: each SPEC fits the review budget; ART-004
  (est. 480 LOC) and ART-005 (est. 560 LOC) carry recorded estimator warns
  under the 1.5× greenfield allowance (net-new files only, warn threshold
  600).
- **Single-file SPA rule**: artifacts and templates inline all behavior and
  data; Google Fonts is the sole permitted external reference; must render
  over `file://`.
- **Brand sources**: racecraft-lab/racecraft `docs/brand/color-system.md`,
  `docs/brand/typography-system.md`, `.claude/rules/brand.md`,
  `.claude/rules/content.md` (voice), and this repo's
  `docs-site/src/styles/brand.css`; the private repo is unreachable at plugin
  runtime, so tokens are copied with provenance, not referenced.
- **Accessibility**: AA contrast, visible focus rings, reduced-motion guard —
  matching the established `brand.css` patterns.
- **Platform parity**: every behavior SPEC updates `skills/` and
  `codex-skills/` (and both agent sets) in the same slice; Codex's 32KiB
  AGENTS.md ceiling bounds skill-file growth.
- **Artifacts are review-visible**: committed under
  `specs/<branch>/artifacts/` (CONTRACT tier), not `.process/` exhaust —
  operators and reviewers consume them.

## 6. Open Questions

- **OQ-1 (ART-007/ART-010):** How does the early draft PR interact with
  marker-split multi-PR emission when final reviewability requires a split?
  Recommendation: the draft PR becomes the first slice PR of the stack (or is
  superseded with an explanatory comment); resolve during ART-007 clarify.
- **OQ-2 (ART-002…005):** Do branded template files count toward reviewable
  production LOC, or classify as the docs/process surface? Recommendation:
  docs/process surface — templates are shipped content, not logic.
- **OQ-3 (ART-001):** Brand-token drift between the private racecraft repo
  and this public plugin. Recommendation: copy with provenance headers and a
  recorded source commit; accept drift until BRAND-001 lands a canonical
  public token source.
- **OQ-4 (ART-006):** Exact auto-detect corroboration when the workflow file
  and `gh` disagree (e.g., draft PR closed manually). Recommendation: workflow
  file wins; log the discrepancy and surface it in the stage report.
- **OQ-5 (ART-009):** The fixed markdown schema for exported UAT results.
  Recommendation: fixed headings + one checkbox row per step ID so the review
  loop can parse pass/fail mechanically.

## 7. SPEC Catalog Crosswalk

| Feature (§3) | Acceptance Criteria | SPEC | Depends on | Priority |
|---|---|---|---|---|
| Artifact Brand Kit & Gallery Foundation | AC-1.* | ART-001 | — | P1 |
| Draft-PR Template Set | AC-2.* | ART-002 | ART-001 | P1 |
| Final-PR Template Set | AC-3.* | ART-003 | ART-001 | P1 |
| Gallery Completion: Design & Prototyping | AC-4.* | ART-004 | ART-001 | P2 |
| Gallery Completion: Knowledge, Reports & Editors | AC-5.* | ART-005 | ART-001 | P2 |
| Autopilot Staging | AC-6.* | ART-006 | — | P1 |
| Draft-PR Emission | AC-7.* | ART-007 | ART-002, ART-006 | P1 |
| Feedback Sweep | AC-8.* | ART-008 | ART-007 | P1 |
| UAT Walkthrough Replacement | AC-9.* | ART-009 | ART-001, ART-006 | P1 |
| Final-PR Writeup, Companions & Ready Flip | AC-10.* | ART-010 | ART-003, ART-007, ART-012 | P1 |
| Scaffold Integration | AC-11.* | ART-011 | ART-006 | P1 |
| Implementation-Notes Capture | AC-12.* | ART-012 | ART-006 | P2 |
| Documentation | AC-13.* | ART-013 | ART-001…012 | P2 |

## 8. Success Criteria

1. All acceptance criteria AC-1.1 … AC-13.3 pass; each SPEC merges within its
   recorded reviewability budget (greenfield warns honored for ART-004/005).
2. A spec scaffolded after this ships runs: grill-me → plan stage → draft PR
   with rendered artifacts → (feedback sweep loop) → implement stage → final
   PR with writeup + UAT walkthrough — on both Claude Code and Codex CLI.
3. The §1 question is answered in-product: an operator can open the draft-PR
   artifacts in a browser and state what will be built, why, and how it will
   be verified — before implementation starts.

## 9. References

- **Technical roadmap:** `docs/ai/specs/html-artifacts-technical-roadmap.md`
- **Roadmap MOC:** `docs/ai/specs/html-artifacts-roadmap-MOC.md`
- **Constitution:** `.specify/memory/constitution.md`
- **Project standards:** `AGENTS.md`, `speckit-pro/AGENTS.md`, `REVIEW.md`
- **Research sources:** claude.com/blog "A Field Guide to Claude Fable:
  Finding Your Unknowns"; claude.com/blog "The Unreasonable Effectiveness of
  HTML"; thariqs.github.io/html-effectiveness (template gallery);
  github.com/anthropics/html-effectiveness (source)
- **Brand sources:** racecraft-lab/racecraft `docs/brand/`,
  `.claude/rules/brand.md`, `.claude/rules/content.md`;
  `docs-site/src/styles/brand.css` (DOC-013)

---

## Appendix — Staged Workflow Overview

```text
/speckit-pro:speckit-scaffold-spec ART-NNN
  ├─ worktree + branch
  ├─ blind-spot pass (read-only unknown-unknowns scan)      [ART-011]
  ├─ grill-me interview → design concept
  ├─ workflow file
  └─ chains into ──► autopilot --stage plan                 [ART-006]
                       ├─ specify → clarify → plan →
                       │  checklist → tasks → analyze
                       ├─ generate draft artifacts           [ART-002/007]
                       │    implementation-plan.html (always)
                       │    spec-explainer.html      (always)
                       │    code-approaches.html     (conditional)
                       │    module-map.html          (conditional)
                       └─ DRAFT PR + artifact index → STOP for human review

operator reviews artifacts (file:// in browser)
  ├─ feedback? → comment on draft PR ─┐
  └─ satisfied? ──────────────────────┤
                                      ▼
/speckit-pro:speckit-autopilot (auto-detects --stage implement)
  ├─ feedback sweep: comments → consensus → amend + regen   [ART-008]
  │    amendments made? → push + STOP for re-review
  ├─ implement (TDD, per-task dispatch)
  │    └─ implementation-notes capture                      [ART-012]
  └─ post-implementation
       ├─ integration suite + self-review (unchanged)
       ├─ pr-writeup.html (always, with impl notes)         [ART-003/010]
       ├─ uat-walkthrough.html (always, replaces runbook)   [ART-009]
       ├─ annotated-diff.html / flowchart.html (conditional)
       └─ update draft PR → flip READY + review loop
```

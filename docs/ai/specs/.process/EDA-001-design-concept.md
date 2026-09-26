---
topic: "Attribution foundation for adopting mattpocock/skills into SpecKit Pro"
slug: "eda-001-attribution-foundation"
date: "2026-09-25"
mode: "setup"
spec_id: "EDA-001"
source_input:
  type: "file"
  ref: "docs/ai/specs/engineering-discipline-adoption-technical-roadmap.md#eda-001-attribution-foundation"
question_count: 8
stop_reason: "natural"
---

# Design Concept: Attribution foundation for adopting mattpocock/skills into SpecKit Pro

> **Source:** docs/ai/specs/engineering-discipline-adoption-technical-roadmap.md (EDA-001)
> **Date:** 2026-09-25
> **Questions asked:** 8
> **Stop reason:** natural
> **Blind-spot pass:** did not run — wait deadline expired

The blind-spot analyst replied about 16 minutes after dispatch, past the
5-minute deadline, so the recorded outcome is "did not run". Its late leads were
treated as unverified input: each one used below was re-checked against the
repository or the upstream repositories before it shaped a question.

## Superseding provenance and license clarification

The operator answered `MIT` during EDA-001 Clarify Session 1. The upstream `pr` skill credits `humanlayer/skills/plugins/show-me/skills/show-me/SKILL.md`, present at commit `bba9d13ab34f0a87f1cc33df4dd196372393ddfc`; that repository's pinned `LICENSE` is MIT, Copyright (c) 2026 HumanLayer. Keep the Q2 decision to ship two notices now, but use a separate HumanLayer MIT notice. Earlier Apache-2.0 descriptions, the `humanlayer/humanlayer` license reference, and the repository-head fallback in the historical interview below are superseded for this copied source. The original Q&A is retained as the decision record.

## Goals

- Publish Matt Pocock's MIT notice (text verbatim from the fork at tag
  `speckit-pro-baseline`, SHA `c55ee46073ed923f86ce59a5eb3b6d895095d1b7`,
  header "MIT License / Copyright (c) 2026 Matt Pocock") under
  `speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/`, so
  both payloads ship it without a `payloads.py` change.
- Record all 38 upstream skills in a machine-readable `ledger.json` beside the
  notice (Q1), with every ABSORB and NEW row starting `planned`.
- Publish a second notice for the Apache-2.0 text that upstream `pr` copies from
  Dex Horthy's `show-me` (humanlayer/humanlayer), and link it from the ledger
  through a `transitive_sources` field (Q2).
- Enforce the notices and ledger with a test that cannot pass on nothing, even
  while 0 rows are `landed` (Q3).
- Define one file-level credit header format for derivative files, plus the
  `metadata.credits` frontmatter shape for SKILL.md files (Q4).
- Record partial absorption with a required `not_ported` note on the ask-matt,
  wayfinder, and triage rows (Q7).
- Deliver in two vertical slices, each its own PR in the EDA stack (Q8):
  - **Slice 1:** MIT notice, `ledger.json`, attribution test and fixtures,
    suite registration, README acknowledgement, and regenerated artifacts.
  - **Slice 2:** the `show-me` source search, the humanlayer Apache notice, and
    enforcement of `transitive_sources`.

## Non-goals

- Any derivative content: EDA-002 onward owns every ABSORB and NEW destination
  (roadmap Out of Scope).
- Edits in the `racecraft-lab/skills` fork, which stays a provenance anchor only
  (roadmap Key Decision).
- Section-level credit markers inside existing files: credits are file-level
  only (Q4).
- A fourth disposition value: the set stays ABSORB, NEW, IGNORE (Q7).
- Routing the ledger through the `merge=generated` driver. That driver keeps
  "ours" verbatim (`.gitattributes:32`) and would silently drop another branch's
  status flips (evidence: `.gitattributes`).
- Fixing the reviewability budget lines of other roadmap entries (Open Question).

## Module and Interface Deltas

- `speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/UPSTREAM-NOTICE.md`:
  new. It carries:
  - the MIT text verbatim;
  - the upstream URL, fork URL, and pinned SHA;
  - a statement that the files the ledger lists as `landed` are modified
    derivatives;
  - a pointer to `ledger.json`.

  (Evidence: roadmap Scope; Q1.)
- `speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/ledger.json`:
  new interface consumed by the test and by every later EDA spec. There is one
  object per upstream skill, ordered by upstream path and pretty-printed with
  one key per line, so status flips on different rows merge cleanly (Q1).

  | Field | Rule |
  | ----- | ---- |
  | `upstream_path` | required |
  | `bucket` | required |
  | `disposition` | ABSORB, NEW, or IGNORE |
  | `destination` | null for IGNORE |
  | `owner_spec` | the EDA spec that flips this row |
  | `status` | `planned` or `landed`; absent for IGNORE |
  | `ignore_reason` | required on IGNORE |
  | `not_ported` | required on exactly ask-matt, wayfinder, and triage (Q7) |
  | `transitive_sources` | list of {project, license, holder, notice_path}; present on `pr` (Q2) |
- `speckit-pro/skills/speckit-coach/references/upstream/humanlayer-show-me/UPSTREAM-NOTICE.md`:
  new in slice 2. It holds humanlayer's LICENSE verbatim (a 15-line Apache-2.0
  header, "Copyright (c) 2024, humanlayer Authors") and a pin to the located
  `show-me` source commit and path. If the source cannot be found, it pins
  humanlayer's head with the gap disclosed (Q2, Q5, Q6).
- Credit header (interface for EDA-002 to EDA-011): one file-level header per
  derivative file, not per section (Q4).
  - Fields: upstream skill paths, pinned SHA, "Modified derivative: yes", and
    the repo-relative notice path.
  - Syntax per file type: an HTML comment in Markdown, `#` comments in TOML and
    Python.
  - Placement: where the file has frontmatter, directly after the frontmatter
    closes, so loaders still see frontmatter first.
  - SKILL.md files also carry `metadata.credits` in frontmatter.
    `validate-skill-contracts.py:28` already allows `metadata` and validates only
    top-level keys.
- `tests/speckit-pro/unit/test-upstream-skill-attribution.py`: new. It is named
  for durable behavior, not the spec ID (AGENTS.md Editing Boundaries).
- `tests/speckit-pro/unit/fixtures/upstream-skill-attribution/`: new fixtures:
  - the frozen MIT text;
  - the frozen humanlayer LICENSE (slice 2);
  - the frozen 38-path upstream list taken from the pinned SHA;
  - a credit-header pass fixture and a credit-header fail fixture (Q3).
- `tests/speckit-pro/suite-manifest.json`: changed, registering the new test.
- `speckit-pro/README.md`: changed, adding an acknowledgements line that links
  the MIT notice.
- Generated outputs: changed by regeneration only, never by hand edits:
  - `dist/` payloads;
  - `docs-site/src/content/docs/reference/tests.md` (a new test `.py`, per
    `tests/speckit-pro/AGENTS.md:12`);
  - the Plugin Authoring Source reference page, which reads
    `speckit-pro/README.md` (`docs-site/scripts/generate-reference-pages.mjs:590`).
- Unchanged grey box: `payloads.py`, the skill contract validators, and every
  skill's behavior.

## Terms

| Term | Meaning in this spec | Differs from codebase usage? | Source (Q<n> or evidence) |
| ---- | -------------------- | ---------------------------- | ------------------------- |
| ABSORB / NEW / IGNORE | Ledger disposition: merged into an existing surface, a new skill, or not ported | yes: new terms, no prior codebase usage | roadmap Disposition Summary |
| planned / landed | Ledger status: destination not yet written, or written with its credit header | yes: new terms | roadmap Scope |
| modified derivative | A repository file adapted from upstream text, carrying a credit header | no: same sense as the Quint and gallery notices | `speckit-pro/skills/speckit-coach/references/quint/UPSTREAM-NOTICE.md` |
| transitive source | A third-party work that upstream itself copied, with its own license and holder | yes: new term | Q2 |
| not_ported | The part of an absorbed upstream skill deliberately left out | yes: new term | Q7 |

No `docs/ai/specs/ubiquitous-language.md` exists to reconcile against.

## Verification Gates

- Attribution test: `python3 tests/speckit-pro/unit/test-upstream-skill-attribution.py`
  passes. It fails if:
  - the MIT block differs by any byte from the frozen copy;
  - the ledger's upstream-path set is not exactly the frozen 38;
  - an IGNORE row lacks `ignore_reason`;
  - `not_ported` is missing from ask-matt, wayfinder, or triage, or appears on
    any other row;
  - the credit checker accepts the fail fixture or rejects the pass fixture;
  - any `landed` row's destination is missing or lacks a credit header;
  - in slice 2, a `transitive_sources` notice path is missing or its license
    text differs from its frozen copy.

  The checks that count rows assert a non-zero count before they pass (Q3;
  precedent `tests/speckit-pro/unit/test-quint-reference-attribution.py:239`).
- Quick suite: `python3 tests/speckit-pro/run-all.py` passes (AGENTS.md
  Commands).
- CI suite: the `run-default-suite.json` runner command from AGENTS.md passes.
- Generated artifacts: run `python3 scripts/refresh-release-artifacts.py`,
  commit, then `python3 scripts/refresh-release-artifacts.py --check` exits 0.
  Both `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/` contain the
  notice and `ledger.json` (roadmap Scope).
- Docs reference: `pnpm --dir docs-site reference:generate`, then
  `pnpm --dir docs-site reference:check` and `pnpm --dir docs-site validate:quality`
  pass (`tests/speckit-pro/AGENTS.md:12`; AGENTS.md Commands).
- Privacy scan: `tests/speckit-pro/unit/test-privacy-scan.py` passes. The notices
  hold only public names, URLs, and SHAs (AGENTS.md Gotchas).
- Shipped prose contains no `bash`, `jq`, or `$(` instructions
  (`active_path_guard.py`; AGENTS.md Gotchas).
- PR title and release-note gates pass before each slice's PR is marked ready.
- Formal methods: none. The spec adds static files and a deterministic
  data-shape test, with no state machine or concurrency to model (evidence:
  roadmap Scope).

## Design Tree (Q&A log)

### Q1. Where should the 38-row disposition ledger live, and in what format?
**Branch:** data / interface
**Recommended answer:** JSON sidecar
> Quint's `provenance.json` is the local precedent for machine-read attribution
> data. A JSON object per row keeps each `status` line several lines from its
> neighbours, so parallel EDA branches that flip different rows merge without
> conflicts. Markdown table rows are adjacent lines and conflict.
**Alternatives offered:** a table in the notice (one file, but parsing and
adjacent-row conflicts); a sibling LEDGER.md (same costs).
**User's answer:** JSON sidecar (Recommended)

### Q2. How should EDA-001 handle the second license from `show-me`?
**Branch:** licensing / scope
**Recommended answer:** Schema now, notice later
> Verified: upstream `skills/in-progress/pr/CREDITS.md` says the "shape of the
> change" section is Dex Horthy's `show-me`, "reproduced almost word for word".
> humanlayer/humanlayer's LICENSE is Apache-2.0, "Copyright (c) 2024, humanlayer
> Authors". The repo precedent is one notice per license holder (the Quint
> notice). Nothing from `show-me` ships before EDA-008.
**Alternatives offered:** both notices now (complete up front, but a notice for
content that has not shipped yet); require EDA-008 to rewrite the section in
original words.
**User's answer:** Both notices now

### Q3. How should the attribution test stay meaningful while 0 rows are `landed`?
**Branch:** verification
**Recommended answer:** Frozen set plus fixture proof
> AGENTS.md Code Review Rules treat "a check that passes on nothing" as
> blocking. The Quint attribution test already fixed this class of bug (commit
> 4427bae5f) and asserts `seen > 0` with "refusing to pass vacuously". The
> gallery test checks MIT text only by substring (`test-artifact-gallery.py:144`),
> which is weaker than the frozen-copy check this scope requires.
**Alternatives offered:** defer the landed-destination check to EDA-002.
**User's answer:** Frozen set + fixture proof (Recommended)

### Q4. What form should each credit block take?
**Branch:** interface
**Recommended answer:** Section comment
> Most derivative content lands as a section in an existing file. Section-scoped
> comments would say exactly which parts are derived.
**Alternatives offered:** a visible blockquote (costs context tokens on every
load); a file header only (simplest, but cannot say which sections are derived).
**User's answer:** File header only

### Q5. With both notices shipping now, what should the humanlayer notice pin?
**Branch:** licensing / provenance
**Recommended answer:** Repo head plus a disclosed gap
> `pr/CREDITS.md` links only the humanlayer repository root. A tree listing of
> humanlayer `main` (head `99abe673498cf8bdcd5f989aebe9406a27185b3b`) shows no
> `show-me` path, and a GitHub code search for "shape of the change" did not find
> it. The LICENSE applies to the whole repository.
**Alternatives offered:** find the exact source first; move the notice to EDA-008.
**User's answer:** Find exact source first

### Q6. If the `show-me` source cannot be found, what should EDA-001 do?
**Branch:** licensing / error path
**Recommended answer:** Fall back to the repo-head pin
> Keeps EDA-001 from stalling on a search that may come up empty, while
> disclosing the gap in the notice.
**Alternatives offered:** defer the notice to EDA-008; pause autopilot for the
operator.
**User's answer:** Fall back to repo-head pin (Recommended)

### Q7. How should the ledger record partial absorption?
**Branch:** data
**Recommended answer:** Required `not_ported` field
> The roadmap's Disposition Summary says ask-matt, wayfinder, and triage are
> absorbed only in part, with their tracker-workflow parts not ported. Only the
> roadmap prose records this, and nothing checks it.
**Alternatives offered:** a new PARTIAL disposition; an optional notes field.
**User's answer:** Required not_ported field (Recommended)

### Q8. How should EDA-001 be sliced?
**Branch:** slice sizing
**Recommended answer:** Two vertical slices
> `estimate-spec-size` (3 stories, 10 files, 10 FRs) returned
> `{"estimated_loc":625,"suggested_slices":2,"status":"warn"}`. The `show-me`
> search is the one uncertain step, and isolating it keeps the core foundation
> unblocked.
**Alternatives offered:** one slice, accepting the warning.
**User's answer:** Two vertical slices (Recommended)

## Open Questions

- **What:** The exact commit and path of Dex Horthy's `show-me` skill.
  **Why deferred:** The operator chose to search before pinning (Q5). The fallback
  is the humanlayer head pin with the gap disclosed (Q6).
  **Suggested next step:** Clarify, slice 2: search humanlayer/humanlayer history
  (commits touching `.claude/` or `commands/`, and the "shape of the change"
  wording) and any Dex Horthy repository linked from humanlayer.
- **What:** The roadmap's "within budget" lines for prose-only specs cannot be
  reproduced by `estimate-reviewable-loc`.
  **Why deferred:** It counts only code suffixes
  (`speckit_pro_runner/helpers/read_only.py:8420`) and returns `not_estimated`
  for Markdown and JSON layouts. `phase-execution.md:409` says never to treat
  that as a within-budget pass. Correcting other entries is outside EDA-001.
  **Suggested next step:** Record EDA-001's budget as the `estimate-spec-size`
  result (625 LOC, warn, split into 2 slices). Raise a roadmap wording fix
  separately.
- **What:** Ledger row ownership when Tier 2 specs run in parallel.
  **Why deferred:** The JSON layout (Q1) removes adjacent-line conflicts, but
  stacked PRs that touch one file still go `dirty` when a lower branch changes.
  **Suggested next step:** Clarify: decide whether `owner_spec` stays
  informational (each EDA spec flips only its own rows by convention) or whether
  the test enforces it in some checkable form.

## Recommended Next Step

Scaffold writes the EDA-001 workflow from this record. Autopilot then runs the
plan stage, with slice 1 as the first PR stacked on the roadmap PR.

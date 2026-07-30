---

description: "Task list for ART-001 — Artifact Brand Kit & Gallery Foundation"
---

# Tasks: Artifact Brand Kit & Gallery Foundation

**Input**: Design documents from `specs/art-001-brand-kit-gallery-foundation/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/gallery-validation-contract.md`, `contracts/routing-catalog-contract.md`,
`quickstart.md`

**Tests**: Test tasks are included and are **first-class**, not optional. The
feature's single deliverable of record is a test —
`tests/speckit-pro/unit/test-artifact-gallery.py` — implementing all 71 checks in
`contracts/gallery-validation-contract.md`. Each check group is written RED against
the contract before the asset that satisfies it exists, then turned GREEN.

**Reviewability**: Task generation adds no file and no surface beyond the plan's
Declared File Operations — 9 authored files, 24 total, 1 primary surface
(seed/config). The binding figures are the ones `spec.md` declares and the
setup-mode gate scrapes: **62 reviewable LOC, 2 production files, 24 total
files**, one primary surface. The gate returns **warn** on exactly one dimension
— total files 24 against a warn of 15 — and **no block**. The plan's broader
hand estimate (7 files of any character, ~580 logic LOC) is disclosure, not the
gate's input, and must not be compared against the gate thresholds. T009 is the
explicit pre-implementation reviewability checkpoint the template requires at
that level.

**Organization**: Tasks are grouped by user story so each can be implemented and
tested independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel — touches no file another `[P]` task in the same
  phase touches
- **[Story]**: `US1` / `US2` / `US3`, matching `spec.md`
- Every description carries its exact repository-relative file path

## Path Conventions

All paths are repository-relative and are run from the repository root.

- **Shipped plugin payload**: `speckit-pro/artifact-gallery/`
- **Repository-only validation**: `tests/speckit-pro/unit/`
- **Generated, never hand-edited**: `dist/`,
  `speckit-pro/speckit_pro_runner/speckit-pro-runner.{manifest.json,sha256}`,
  `docs-site/src/content/docs/reference/tests.md`

## Project Commands

| Purpose | Command |
|---|---|
| Single-file test (the fast loop) | `python3 tests/speckit-pro/unit/test-artifact-gallery.py` |
| Unit layer | `python3 tests/speckit-pro/run-all.py --layer 4` |
| Structural layer | `python3 tests/speckit-pro/run-all.py --layer 1` |
| Full verify | `python3 tests/speckit-pro/run-all.py` |

There is no build, typecheck, or lint surface in this feature.

## Conventions fixed before any file is written

These are decisions the artifacts already settle. They are restated here because
each one is cheap now and expensive after a port lands.

1. **Canonical marker names.** `brand-kit.css` uses
   `/* BRAND-KIT:START */` … `/* BRAND-KIT:END */`, unchanged. The second block's
   pair is **renamed** from `THEME-TOGGLE:*` to
   `<!-- GALLERY-HEAD:START -->` … `<!-- GALLERY-HEAD:END -->`, per FR-027: the
   block carries the policy declaration, the font request, pre-first-paint theme
   application, and `color-scheme` selection, so its name must describe the head
   region it is rather than the toggle alone. FR-027 requires this rename, and it
   is already carried through every downstream artifact — `data-model.md`,
   `research.md`, `plan.md`, and check A2 in the validation contract all spell
   `GALLERY-HEAD`. The only remaining mention of the old literal in this feature's
   artifacts is the description of the rename itself, immediately above. The
   **file name** `theme-toggle.html` is unchanged — the
   plan's Declared File Operations and the payload declarations depend on it, and
   FR-027 constrains only the marker pair.
2. **No third canonical block, and no third canonical file.** FR-027 places the
   policy declaration inside the existing head block precisely because a third
   block would add a third marker pair, a third per-artifact presence check, a
   third canonical-file check, and one authored file plus two regenerated copies —
   taking declared total files from 24 to 27, past the block threshold of 25.
3. **`speckit-pro/artifact-gallery/templates/` is not created by this feature.**
   D5 makes an absent directory a vacuous pass, and D4 rejects any non-`.html`
   file — so a placeholder is both unnecessary and a failure. A port creates the
   directory with its first artifact.
4. **The gallery ships no `.sh`, `.bash`, or shell-shebang file.** The zero-Bash
   guard's scan roots include the whole `speckit-pro` source tree.
5. **Method names carry no live spec ID.** `test-unit-layout.py` fails any
   `test_*` method name matching `<family>[-_]\d{3}`, and `art` is a live family.
   No method may be named `test_art_001_*`. Methods are behavior-named.

---

## Phase 1: Setup

**Purpose**: Establish a clean baseline and the one worktree dependency, so any
later red is attributable to this feature.

- [X] T001 [P] Record the pre-change baseline by running `python3 tests/speckit-pro/run-all.py` from the repository root and noting the result in the PR working notes
- [X] T002 [P] Install the docs-site dependencies once for this worktree with `pnpm --dir docs-site install --frozen-lockfile`, required before the `docs-site/` reference regeneration in T032

**Checkpoint**: Baseline recorded, `docs-site/` buildable.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The payload allowlist edit, the test harness, and the shipped
contract document. Nothing downstream is safe without these.

**⚠️ CRITICAL**: No user story work begins until this phase completes.

**⚠️ T003 is the single highest-risk item in the feature.** Without it the whole
feature builds green and ships nothing.

- [X] T003 [P] Add `"artifact-gallery"` to **both** per-platform copy lists in `speckit-pro/speckit_pro_runner/gates/payloads.py` — the Claude list (alongside `.claude-plugin`, `agents`, `commands`, `hooks`, `skills`, `scripts`, `speckit_pro_runner`, `README.md`, `CHANGELOG.md`) and the Codex list (alongside `.codex-plugin`, `codex-agents`, `codex-hooks.json`, `scripts`, `speckit_pro_runner`, `README.md`, `CHANGELOG.md`). Satisfies FR-018's edit half. The copy helper is fail-silent, so an unnamed directory produces no error and no output — a green build is not evidence the gallery shipped. This edit MUST land before the first payload regeneration (T031)
- [X] T004 [P] Create `tests/speckit-pro/unit/test-artifact-gallery.py` with the house entrypoint shape only — `from __future__ import annotations`, standard library only, `REPO_ROOT = Path(__file__).resolve().parents[3]`, `run_counted` from `tests/speckit-pro/lib/test_result.py`, `build_suite()` → `main()` → `raise SystemExit(main())`, no argv parsing (Layer 4 never receives `--live`), and a final `test-artifact-gallery: <passed>/<total> passed` line. **Every check function MUST take the gallery root as a parameter** rather than closing over a module constant — this is what lets groups A, D, E, G, and J be exercised against synthetic fixtures built in a temporary directory, without which roughly half the 71 checks would be vacuous in a feature that ships zero artifacts (FR-014)
- [X] T005 [P] Create `speckit-pro/artifact-gallery/SPA-CONTRACT.md` carrying the core contract (FR-010): all behavior, styling, and data inline in one file; correct `file://` rendering with no reported errors; the routing catalog's top-level and per-entry shape with each field's meaning; both trigger forms and the two-step stage-then-trigger routing rule (FR-016); the identifier stability guarantee and the single value a port may change — a port embeds two blocks and flips exactly one `status` from `planned` to `shipped`, editing no shared foundation file (FR-007; SC-004); **all five signals named exactly as `signals` carries them, each with its meaning and its named workflow evidence source** (FR-015, and one leg of check C8's three-way closure); the explicit statement that the **validated** shape is normative and this document is its explanatory statement; the two canonical marker names fixed in Conventions above; and the F5 authoring rule that no gallery file may carry a `../skills/`-style relative reference the Codex payload rewriter would match — written in backticks so the document does not trip the check that records it
- [X] T006 [P] Create `speckit-pro/artifact-gallery/UPSTREAM-NOTICE.md` by downloading the `anthropics/html-effectiveness` MIT license text verbatim and never retyping it, preserving `Copyright (c) 2026 Anthropic PBC` exactly (FR-020). The file MUST NOT be named `LICENSE` — the payload builder special-cases that exact relative path and maps it to this repository's own root license
- [X] T007 Register the test as the last entry in the Layer 4 `scripts` array of `tests/speckit-pro/suite-manifest.json` as `{ "path": "tests/speckit-pro/unit/test-artifact-gallery.py", "label": "test-artifact-gallery", "baseline": null }`, adding a comma to the current last line — the array is append-ordered, not sorted (FR-014). Depends on T004; must never be committed without it
- [X] T008 Extend `speckit-pro/artifact-gallery/SPA-CONTRACT.md` with the inherited obligations (FR-010, FR-027, SC-012): the accessibility duties — audited and **prohibited** token pairings with their named replacements (FR-005), the use-of-color rule stated as a rule distinct from the punctuation-level reservation (FR-021), the theme-control keyboard/name/role/state obligations (FR-022), focus visibility and reduced-motion behavior (FR-023), typography loading and fallback rules (FR-024); the security duties — the six prohibited constructs and the in-document policy declaration (FR-027); and the untrusted-input rule for **generated** artifacts naming the four contexts an interpolated value may never enter (script bodies, style bodies, URL-valued attributes, event-handler attributes) plus the explicit statement that FR-011's external-reference guarantee covers the gallery's own source files and **not** artifacts generated at run time. Depends on T005 (same file)
- [X] T009 Verify the reviewability budget against this task list before implementation and record the result in `specs/art-001-brand-kit-gallery-foundation/plan.md` working notes. Record the **binding** figures — the ones `spec.md` declares and the setup-mode gate scrapes: 1 primary surface, 62 reviewable LOC, 2 production files, 24 total files, which the gate returns as **warn on total files only** (24 against a warn of 15) with no block dimension crossed. Record the plan's broader hand estimate (9 authored files, 7 files of any character, ~580 logic LOC, ~1,570 authored lines) separately and explicitly as disclosure, never as a second gate reading — reporting it in the gate's threshold columns is the error the plan's budget section already had to correct once. Confirm task generation introduced no new file or surface, and that the recorded split decision still stands or invoke the plan's fallback cut

**Checkpoint**: The gallery reaches both payload allowlists, the test runs and
reports 0/0, the contract document exists. User story work can begin.

---

## Phase 3: User Story 1 - Adopt shared branding with drift caught automatically (Priority: P1) 🎯 MVP

**Goal**: A canonical, marker-delimited brand token set and a canonical
marker-delimited head block, both embeddable verbatim with no build step, with a
byte-exact drift check that names the offending file and block.

**Independent Test**: Take a copy of a gallery file, alter one character inside
the delimited brand block, and confirm the check fails naming both the file and
the block; restore it and confirm it passes. Because this feature ships zero
artifacts, run it against a synthetic fixture rather than a tracked file.

### Tests for User Story 1 (write FIRST, confirm they FAIL) ⚠️

- [X] T010 [US1] Implement check group A (A1–A5) in `tests/speckit-pro/unit/test-artifact-gallery.py` — A1 `brand-kit.css` holds exactly one well-ordered `BRAND-KIT:START`/`END` pair; A2 `theme-toggle.html` holds exactly one well-ordered `GALLERY-HEAD:START`/`END` pair; A3 every gallery HTML artifact's marker pairs appear exactly once each with matching ends; A4 each embedded region equals the canonical **inner** region byte for byte, with the failure message naming artifact **and** block; A5 every `shipped` entry's artifact embeds the brand block, so absence is never a pass. Comparison is limited to the delimited region so template-specific styling outside it never fails. Exercise A3–A5 against synthetic fixtures (FR-002, FR-003, FR-006; SC-002)
- [X] T011 [US1] Implement check group I (I1–I6) in `tests/speckit-pro/unit/test-artifact-gallery.py` — I1 the `brand-kit.css` marked region contains a `prefers-reduced-motion: reduce` at-rule; I2 it contains a `:focus-visible` rule; I3 it sets `color-scheme` under **both** `[data-theme="dark"]` and `[data-theme="light"]`; I4 the `theme-toggle.html` marked region contains a `button` element carrying both an accessible-name source and a state attribute; I5 the marked region validates the stored override against the closed set of theme names before applying it and writes a literal from that set rather than the string read back; I6 the storage key in the marked region is namespaced to this gallery. Every one asserts the construct is **inside** the copied region — a rule above the start marker looks correct and reaches no artifact (FR-004, FR-022, FR-023)

### Implementation for User Story 1

- [X] T012 [P] [US1] Create `speckit-pro/artifact-gallery/brand-kit.css`. **Above** the start marker: the FR-012 provenance header naming `racecraft-lab/racecraft` `docs/brand/*` at commit `30237cceaeb398e9fc08d8570714f24ff661c867` captured 2026-07-04 and the in-repo `docs-site/src/styles/brand.css` source, by repository/path/revision/date only with no prose reproduced; plus the audited contrast table transcribed from `data-model.md` with every ratio unrounded to two decimals and the four prohibition rules each naming its replacement token. The table MUST be **complete and symmetric** — every token measured against **all four** surfaces in **both** themes, every token it names defined in both themes so each ratio is independently reproducible, and every sub-threshold pairing carrying a prohibition rule rather than being omitted, since absence of a row is a defect and not an implied pass (SC-007). The two token classes MUST be distinguished at their point of definition: a **functional token** is re-valued when it misses its floor, while a **brand primitive** is not — its unservable need is routed to a named functional sibling defined alongside it (FR-025). **Inside** `BRAND-KIT:START`/`END`: the four surface tokens, both border tokens, the three text tokens, `--rc-accent`, `--rc-brand-red`, `--rc-danger-text`, the three font-stack tokens with distinguishable fallbacks per role, the `:focus-visible` treatment using `--rc-link`, the `prefers-reduced-motion: reduce` block covering the cross-theme transition, dark values under both `@media (prefers-color-scheme: dark)` and `:root[data-theme="dark"]` with `:root[data-theme="light"]` forcing light back on, and `color-scheme` set under each of the two `data-theme` selectors. Anything left above the start marker ships to no artifact (FR-001, FR-005, FR-012, FR-021, FR-023, FR-024, FR-025)
- [X] T013 [P] [US1] Create `speckit-pro/artifact-gallery/theme-toggle.html` as a single contiguous **head** region delimited by `GALLERY-HEAD:START`/`END`. The region opens with the FR-027 in-document policy declaration — so it is a direct child of `<head>` (J7) and only a character-encoding declaration may precede it (J8) — restricting base URI, form submission, embedded objects, nested documents, and outbound connections, naming `'none'` for each and never `'self'` (J9), and naming none of the reporting-endpoint, frame-ancestry, or sandbox directives (J10). Then the `fonts.googleapis.com` stylesheet request carrying the swap-behavior parameter (FR-024, E4). Then the inline behavior: read the gallery-namespaced storage key, validate the value against the closed two-member set of theme names and discard anything else in favor of the operating-system signal, apply `data-theme` to `:root` **before first paint** as a literal from that closed set rather than the string read back, set the matching `color-scheme`, and write the override inside `try`/`catch` so a browser refusing storage for local files still switches for the session with no error surfaced — the `try`/`catch` MUST NOT be what satisfies the read-side validation. The control is emitted from inside the same region as a real `button` element with a stable accessible name that does not depend on an icon glyph and a state attribute that changes between theme positions, so one marker pair covers head-only content while still satisfying I4 (FR-003, FR-004, FR-022, FR-024, FR-027)
- [X] T014 [P] [US1] Create `speckit-pro/artifact-gallery/brand-voice.md` covering only the artifact-relevant subset of the upstream content rules — voice and tone, banned and preferred vocabulary, answer-first summary structure, and call-to-action and button labeling. Website-only concerns (structured-data markup, question-and-answer section minimums, site navigation chrome) MUST be excluded so they cannot mislead an authoring agent (FR-013)

### Verification for User Story 1

- [X] T015 [US1] Run `python3 tests/speckit-pro/unit/test-artifact-gallery.py` and confirm groups A and I are GREEN, then discharge Story 1's Independent Test by adding a fixture-driven drift proof to `tests/speckit-pro/unit/test-artifact-gallery.py`: build a synthetic artifact embedding the canonical block, mutate one character inside the marked region, assert the check fails and the message names **both** artifact and block, restore it, assert it passes. Build the fixture in a temporary directory, never as a tracked file — a fixture under `speckit-pro/artifact-gallery/templates/` would fail D4 and be required in both payloads by F1/F2 (SC-002)

**Checkpoint**: The brand kit and the head block exist, drift is provably caught,
and the shared-block invariants are asserted inside the copied regions. User
Story 1 is independently functional.

---

## Phase 4: User Story 2 - Route against a complete template catalog (Priority: P2)

**Goal**: A machine-readable routing catalog seeded with all 21 planned templates
and a closed five-signal vocabulary declared as data, validated for shape,
closure, and artifact correspondence.

**Independent Test**: Read `speckit-pro/artifact-gallery/manifest.json` with no
other part of the feature in place and confirm every planned template is listed
with all eight fields, and that `planned` entries cause no failure for files that
do not exist.

### Tests for User Story 2 (write FIRST, confirm they FAIL) ⚠️

- [X] T016 [US2] Implement check group B (B1–B12) in `tests/speckit-pro/unit/test-artifact-gallery.py` — B1 exactly the three top-level keys `schema_version`, `signals`, `templates`; B2 `schema_version == "1.0"`; B3 21 entries; B4 exactly the eight documented keys per entry; B5 `stage` in the three-member set; B6 `category` in the nine-member set; B7 `status` in `planned`/`shipped`; B8 `title` and `when_to_use` non-empty strings; B9 `id` unique **and** filename-safe kebab-case with no path separator, `..` segment, whitespace, or dot; B10 `source` matching one of two forms with `origin` closed to `upstream`/`repository`, `upstream` carrying a non-empty `file` and `repository` carrying none; B11 `source.file` unique across the catalog; B12 the catalog's identifier set equals the seeded identifier set **pinned as a literal in the validation**. Entries are named by `id` in failure messages **except** where the id is itself missing, duplicated, or malformed — those are named by array position, since naming by identifier is circular exactly there — and **every** offending entry is reported, not just the first (FR-007, FR-019, FR-026; SC-003)
- [X] T017 [US2] Implement check group C (C1–C8) in `tests/speckit-pro/unit/test-artifact-gallery.py` — C1 asserts the integer `5` and the test holds **no copy of the five names**, because a list edited in the same change as the catalog is not an independent check; C2 `signals` entries unique and flat `snake_case`; C3 every trigger exactly `{"always": true}` or `{"any_of": [...]}`; C4 every `any_of` array non-empty; C5 every signal named by a trigger is a member; C6 every member is named by at least one trigger; C7 every entry carries a `trigger`, `ad-hoc` entries included; C8 the set of names in `signals` equals the set of signals documented in `speckit-pro/artifact-gallery/SPA-CONTRACT.md` — closure between two shipped artifacts, not a duplicate list, and the only check that makes a coordinated rename visible (FR-008, FR-015, FR-016, FR-017)
- [X] T018 [US2] Implement check group D (D1–D5) in `tests/speckit-pro/unit/test-artifact-gallery.py` — D1 for `shipped`, `templates/<id>.html` exists; D2 for `planned`, it **does not** exist — the biconditional that stops an artifact shipping under a `planned` entry and skipping A5 entirely, and the only thing that makes SC-004's "changes exactly one catalog value" enforceable rather than aspirational, since adding a file without flipping its status would otherwise pass; D3 every `.html` file under `templates/` is claimed by exactly one entry; D4 `templates/` contains no non-`.html` file, reported as disallowed rather than as an unclaimable orphan; D5 an **absent** `templates/` directory counts as zero artifacts and passes, which is this feature's actual shipped state. Both D1 and D3 resolve the path from the identifier relative to the manifest's own directory and never from a stored field, and resolution is rejected if it would leave the artifact directory. Exercise D1–D4 against synthetic fixtures, since the real gallery exercises only D5 (FR-009)

### Implementation for User Story 2

- [X] T019 [US2] Create `speckit-pro/artifact-gallery/manifest.json` with exactly three top-level keys in order — `schema_version: "1.0"`, `signals` as the five names in FR-015 order (`competing_approaches`, `brownfield_change`, `self_review_findings`, `large_diff`, `operational_flow_change`), and `templates` with all 21 entries transcribed from the seeded catalog table in `data-model.md`. Each entry carries the eight keys in FR-007's declaration order with no path key. All 21 ship `status: "planned"`. The counts that must hold: 20 `upstream` + 1 `repository`; 4 `draft-pr` + 4 `final-pr` + 13 `ad-hoc`; four staged always-applies (`implementation-plan`, `spec-explainer`, `pr-writeup`, `uat-walkthrough`) and four staged conditional (`code-approaches`, `module-map`, `annotated-diff`, `flowchart`); all 13 ad-hoc entries always-applies; every signal consumed at least once; all nine category members exercised; the 20 `source.file` values distinct and carrying numeric prefixes `01`–`20` exactly once each. Do **not** create `speckit-pro/artifact-gallery/templates/` (FR-007, FR-008, FR-015, FR-017, FR-019, FR-026)

### Verification for User Story 2

- [X] T020 [US2] Run `python3 tests/speckit-pro/unit/test-artifact-gallery.py` and confirm groups B, C, and D are GREEN against `speckit-pro/artifact-gallery/manifest.json`, and confirm each negative case fires against its synthetic fixture — a duplicate id, an id composing a path outside `templates/`, an unknown signal, an empty `any_of`, an unrecognized `origin`, a `shipped` entry with no file, a `planned` entry with a file, an orphaned `.html`, and a non-`.html` file (SC-003)

**Checkpoint**: A routing consumer can answer "which artifacts belong at this
stage?" from one read of the catalog. User Stories 1 and 2 both work
independently.

---

## Phase 5: User Story 3 - Open an artifact locally and read it in either theme (Priority: P3)

**Goal**: The guarantees that make an artifact safe and readable from the
filesystem — nothing loads from a host other than the two font hosts, no
construct is present that would make that scan unenforceable, and the theme and
offline behavior is verified where the suite cannot reach.

**Independent Test**: Open a gallery artifact directly from the filesystem with
the network disabled, in both a light-set and a dark-set operating system, and
confirm it renders correctly, reports no errors, and its theme control works.
Because this feature ships zero artifacts, run it against a scratch harness page
composed from the two canonical files.

### Tests for User Story 3 (write FIRST, confirm they FAIL) ⚠️

- [X] T021 [US3] Implement group E's position collector in `tests/speckit-pro/unit/test-artifact-gallery.py` as **default-deny over every URL-valued attribute in the document**, parsed with `html.parser`, carrying a **closed exemption list** — `href` on an anchor, addresses inside parser-recognized comments, and visible text — and failing any unrecognized attribute carrying a URL-shaped value. An enumeration of positions is a denylist and is explicitly rejected: it omitted `source`, `video`, `audio`, `track`, `object`, `embed`, image-typed inputs, SVG `image`/`use`, `form action`, `a ping`, `meta refresh`, and `base`. On `link`, treat `stylesheet`, `preload`, `modulepreload`, `prefetch`, `icon`, `manifest`, `preconnect`, and `dns-prefetch` as scanned. Add E9 (both `@import` forms — the URL-token form **and** the bare-string form) and E11 (`srcset` split by the documented algorithm, each candidate's URL a run up to the next whitespace so an embedded comma is not a separator, with **every** candidate scanned). Also scan `fetch(...)`, `XMLHttpRequest.open(...)`, `new WebSocket(...)`, `navigator.sendBeacon(...)`, `new Worker(...)`, `new EventSource(...)`, `importScripts(...)`, and dynamic `import(...)` string literals anywhere in the document text including attribute values. Make the `url()` pattern case-insensitive and tolerant of whitespace, newlines, and optional quotes. **Group E scans every file under the gallery directory, not only `templates/`** — `brand-kit.css` and `theme-toggle.html` are embedded verbatim into all 21 artifacts, so this is the only part of group E that can fire here and it guards the highest-leverage surface (FR-011; SC-008)
- [X] T022 [US3] Implement group E's host, scheme, and fail-closed rules in `tests/speckit-pro/unit/test-artifact-gallery.py` — E1 every resolved host is `fonts.googleapis.com` or `fonts.gstatic.com` by **exact case-folded equality**, never containment or prefix, with a trailing root dot failing closed deliberately; E5 the host is obtained with a structured URL parser, userinfo and port absent and the parse round-tripping to the original string, **reusing** the conjunction in `tests/speckit-pro/layer6-efficiency/lib/codex_capability_contract.py` rather than reimplementing it; E6 every reference is rejected **before parsing** if it contains a backslash, whitespace, a control character, or a character outside the unreserved URL grammar, **reusing** the pre-parse rejection in `scripts/release_note_policy.py` — this is what closes the scanner-versus-browser differential where `https://evil.example\@fonts.googleapis.com/x.css` parses to the allowed host here and loads from `evil.example` in a browser; E7 in a resource-loading position the scheme is `https` or the reference is same-document relative, **reusing** the unsafe-scheme corpus in `tests/speckit-pro/unit/test-release-note-policy.py` rather than assembling a second one; E8 a reference that cannot be parsed or yields no host **fails**; E10 any escape sequence inside a style `url()` or `@import` reference **fails** rather than being decoded; E12 no scheme-relative `//host/…` reference in any scanned position (FR-011; SC-008)
- [X] T023 [US3] Implement group E's negative controls and the font-request check in `tests/speckit-pro/unit/test-artifact-gallery.py` — E2 anchor `href` passes for `https:`, `mailto:`, and fragment schemes only and **must fail** on `javascript:`, `data:`, `vbscript:`, and `blob:` in that same position; E3 URLs in **parser-recognized** comments and in visible text pass, where "comment" means a construct the parser classifies as one, because content inside a `script` element is raw text even when written to look like a comment and a pattern-stripping implementation would blind itself to live script; E4 every `fonts.googleapis.com` stylesheet request carries the swap-behavior parameter, since the provider's default is a blocking behavior with an invisible-text period and no other check would notice its absence. E2 and E3 are asserted explicitly as negative controls — a scanner that fails them would reject the provenance and attribution links FR-012 and FR-020 require. Record in the module docstring that the style and network-call positions are regex-matched rather than parsed, a deliberate constitution deviation, and must not be presented as carrying the same strength as a parsed position (FR-011, FR-024; SC-008, SC-011)
- [X] T024 [US3] Implement check group J (J1–J10) in `tests/speckit-pro/unit/test-artifact-gallery.py` — J1 no `base` element, the one construct that defeats group E completely because it carries no disallowed host and instead redefines what every relative reference resolves to; J2 no scheme-relative reference anywhere; J3 no `on*` event-handler attribute; J4 no `srcdoc` attribute; J5 no `form` element with an `action` and no `ping` attribute on any element; J6 every artifact carries an in-document policy declaration restricting base URI, form submission, embedded objects, nested documents, and outbound connections; J7 the declaration is a **direct child of the head element**; J8 no content-bearing element precedes it, only a character-encoding declaration may; J9 it names `'none'` for each restricted directive and never `'self'`; J10 it names none of the reporting-endpoint, frame-ancestry, or sandbox directives. All ten are vacuous against the real gallery, which ships no artifact — exercise every one against synthetic fixtures so the contract ART-002…005 inherit is proven rather than declared (FR-027)

### Verification for User Story 3

- [X] T025 [US3] Run `python3 tests/speckit-pro/unit/test-artifact-gallery.py` and confirm groups E and J are GREEN, that group E fires non-vacuously against `speckit-pro/artifact-gallery/brand-kit.css` and `speckit-pro/artifact-gallery/theme-toggle.html`, and that each negative case fails against its synthetic fixture — a lookalike host, a userinfo-bearing URL, a backslash authority, a bare-string `@import`, a hex-escaped URL, a multi-candidate `srcset`, a scheme-relative reference, a `base` element, a `srcdoc`, an `on*` attribute, a `ping`, a missing font swap parameter, and each of the four ways the policy declaration silently voids (SC-008)
- [ ] T026 [US3] Compose a scratch harness page **outside the repository working tree** from `speckit-pro/artifact-gallery/theme-toggle.html` and `speckit-pro/artifact-gallery/brand-kit.css`, then run manual scenarios M1–M6 from `specs/art-001-brand-kit-gallery-foundation/quickstart.md` and capture the evidence for the PR: dark-OS first paint with no flash of light, light-OS render, theme-control switch and persistence, the storage-refused path switching for the session with no error surfaced, offline reload with typeface substitution as the only difference, and a provenance link navigating normally. **Manual — the suite drives no browser** (SC-001, SC-005, SC-006)
- [ ] T027 [US3] Run manual scenarios M7–M12 from `specs/art-001-brand-kit-gallery-foundation/quickstart.md` against the same scratch harness and capture the evidence: keyboard-only reach and activation with a visible focus indicator; the control's reported name and state inspected in **both** theme positions with the state changing between them; reduced-motion suppressing the cross-theme transition; a dark-OS reviewer forcing light and seeing form controls and scrollbars follow the **chosen** theme; no invisible-text period during font loading; and heading versus body remaining distinguishable with the brand faces unavailable. Also seed the storage key with an arbitrary out-of-set string and confirm the artifact renders in the operating-system theme and reports no error. **Manual** (FR-004, FR-022, FR-023, FR-024; SC-010, SC-011)

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: The obligations that serve no single story — upstream attribution,
payload reach, suite integration, and the generated-artifact contract.

- [X] T028 Implement check group G (G1–G7) in `tests/speckit-pro/unit/test-artifact-gallery.py` — G1 the upstream notice file exists and is **not** named `LICENSE`; G2 it reproduces the permission notice verbatim including `Copyright (c) 2026 Anthropic PBC`; G3 for each `upstream` entry whose artifact exists, the artifact carries an attribution header containing upstream repository, upstream file, verbatim copyright line, license identifier, link to the full license text, and an explicit modified-derivative statement; G4 for each `repository` entry whose artifact exists, the artifact carries **no upstream attribution element at all**, not merely no copyright line, so both branches test the same claim from opposite directions; G5 every entry takes exactly **one** of the G3/G4 branches, so an unrecognized `origin` fails rather than falling through — a licensing gate that silently declines to run is worse than no gate, because green is read as evidence the attribution was checked; G6 the upstream **file** named in an artifact's header equals its entry's `source.file`; G7 the upstream **repository** named there equals `anthropics/html-effectiveness`. G3–G7 are vacuous against the real gallery — exercise each against synthetic fixtures, including a header copy-pasted from a neighbouring entry (FR-020)
- [X] T029 Implement check group F (F1–F5) in `tests/speckit-pro/unit/test-artifact-gallery.py` and confirm it fails RED before regeneration — F1 the set of paths under `speckit-pro/artifact-gallery/` equals the set under `dist/claude/speckit-pro/artifact-gallery/`; F2 the same holds for `dist/codex/speckit-pro/artifact-gallery/`; F3 each source file is byte-identical to its Claude payload copy; F4 each source file is byte-identical to its **Codex** payload copy, which is safe only because F5 holds; F5 no source gallery file contains a reference the Codex rewriter would match, defined by `REL_SKILL_PATH_XPLAT008` itself rather than by a substring search — a substring check for `../skills/` would fail `SPA-CONTRACT.md` for documenting its own rule. Scope F1/F2 to `artifact-gallery/` only; a generalized "every source file must ship" check would immediately fail on `speckit-pro/AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`, which are shipped by neither payload by design. **This is the check half of FR-018** — the existing payload gates compare a fresh build against committed `dist/`, so a directory absent from both sides is self-consistently absent and passes (FR-018)
- [X] T030 Implement check H1 in `tests/speckit-pro/unit/test-artifact-gallery.py` asserting the test's own registration in the Layer 4 `scripts` array of `tests/speckit-pro/suite-manifest.json`, so an unregistered test the suite never runs fails loudly (FR-014)
- [X] T031 Regenerate the shipped payload and its proofs by running `python3 tests/speckit-pro/check-toolchain.py --mode tests` then `PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py`, confirm both `dist/claude/speckit-pro/artifact-gallery/` and `dist/codex/speckit-pro/artifact-gallery/` list all six gallery files, re-run `python3 tests/speckit-pro/unit/test-artifact-gallery.py` and confirm group F flips to GREEN, then run `python3 tests/speckit-pro/run-all.py --layer 1`. Hand-editing any regenerated file is forbidden. **The build exits 0 even when the gallery is absent from the payload** — an empty or missing `dist/` gallery directory means T003 did not land (FR-018)
- [X] T032 Regenerate the docs-site test reference with `pnpm --dir docs-site reference:generate` and commit the resulting `docs-site/src/content/docs/reference/tests.md` diff — the generator enumerates every `.md`, `.py`, and `.sh` under `tests/speckit-pro`, so the new unit test staleness-fails the committed page, which passes locally and fails clean CI if skipped
- [X] T033 Run full verification from the repository root — `python3 tests/speckit-pro/run-all.py`, `python3 tests/speckit-pro/check-toolchain.py --mode docs`, `pnpm --dir docs-site reference:check`, and `PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py --check` — and confirm all 71 checks in `specs/art-001-brand-kit-gallery-foundation/contracts/gallery-validation-contract.md` are implemented and passing, with the test reporting `test-artifact-gallery: <N>/<N> passed`. Then confirm the deliverable set is complete enough for ART-002…005 to begin with no further foundation decisions required of them — both canonical blocks, the seeded catalog, the contract document, the voice reference, and the upstream notice all present and shipped to both payloads (SC-009)
- [x] T034 Generate the PR review packet per the PR Review Packet Requirements in `specs/art-001-brand-kit-gallery-foundation/spec.md` — what changed, why, non-goals, review order (token set → head block → routing catalog → contract and voice references → validation), scope budget, traceability mapping each requirement to changed files and evidence, verification evidence including the automated suite result **and** the manually captured `file://` evidence from T026 and T027, known gaps, and rollback notes. Restate the accepted budget warning and the plan's replacement composition-and-indivisibility rationale, and disclose the ~1,570 raw authored lines alongside the ~580 logic lines the contract's metric counts

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup — **blocks all user stories**
- **User Story 1 (Phase 3)**: depends on Phase 2
- **User Story 2 (Phase 4)**: depends on Phase 2; C8 additionally depends on
  T005/T008 (`SPA-CONTRACT.md` documents the five signals)
- **User Story 3 (Phase 5)**: depends on Phase 2; group E's non-vacuous coverage
  additionally depends on T012 and T013 existing
- **Polish (Phase 6)**: depends on all three stories; T031 depends on T003 and on
  every gallery file existing; T032 depends on T002 and T004; T033 depends on
  everything

### User Story Dependencies

- **US1 (P1)**: independent. Delivers the two canonical files and their drift
  check — the MVP.
- **US2 (P2)**: independent of US1's files. C8 reads `SPA-CONTRACT.md`, a
  Foundational deliverable, not a US1 one.
- **US3 (P3)**: its checks are file-independent, but its non-vacuous coverage and
  its manual scenarios both read US1's two canonical files, so it is sequenced
  last as the spec records.

### Within Each User Story

- Check-group tasks are written RED before the asset that satisfies them
- Canonical files before the catalog that references them
- Story complete before moving to the next priority

### Critical path

T003 → (T012, T013, T014, T019, T005/T008, T006) → T029 → T031 → T033.
T003 is on the critical path of the whole feature: without it T031 silently
produces nothing and T029 stays red for a reason no other check explains.

### Parallel Opportunities

- **Phase 1**: T001 and T002 together — different toolchains, no shared file
- **Phase 2**: T003, T004, T005, T006 together — `payloads.py`,
  `test-artifact-gallery.py`, `SPA-CONTRACT.md`, `UPSTREAM-NOTICE.md` are four
  distinct files. T007 and T008 are **not** parallel-safe: T007 must follow T004
  or the suite points at a missing file, and T008 writes the same file as T005
- **Phase 3**: T012, T013, T014 together — `brand-kit.css`, `theme-toggle.html`,
  `brand-voice.md` are three distinct files
- **Phases 4–6**: **no parallel opportunities.** Every remaining task writes
  `tests/speckit-pro/unit/test-artifact-gallery.py`, which is one file by design
  (`research.md` R10 — splitting it was considered and rejected). Marking any two
  of them `[P]` would cause write contention, so none is marked

---

## Parallel Example: Phase 2 Foundational

```bash
# Four distinct files, no ordering between them:
Task: "Add artifact-gallery to both copy lists in speckit-pro/speckit_pro_runner/gates/payloads.py"
Task: "Create the test harness in tests/speckit-pro/unit/test-artifact-gallery.py"
Task: "Create speckit-pro/artifact-gallery/SPA-CONTRACT.md core contract"
Task: "Create speckit-pro/artifact-gallery/UPSTREAM-NOTICE.md from the verbatim upstream license"
```

## Parallel Example: User Story 1

```bash
# Three distinct gallery files, all after their RED checks land:
Task: "Create speckit-pro/artifact-gallery/brand-kit.css"
Task: "Create speckit-pro/artifact-gallery/theme-toggle.html"
Task: "Create speckit-pro/artifact-gallery/brand-voice.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup
2. Phase 2 Foundational — **T003 first; it is the item that silently voids the
   whole feature**
3. Phase 3 User Story 1
4. **STOP and VALIDATE**: run `python3 tests/speckit-pro/unit/test-artifact-gallery.py`
   and discharge Story 1's Independent Test (T015)

At this point the brand kit is usable and enforced even though the catalog and
the contract's later sections do not yet exist — which is exactly the standalone
value the spec claims for P1.

### Incremental Delivery

1. Setup + Foundational → the gallery reaches both payloads and the test runs
2. US1 → drift caught → validate independently
3. US2 → the catalog routes → validate independently
4. US3 → the external-reference and prohibited-construct guarantees hold →
   validate independently
5. Polish → attribution, payload reach, suite registration, regeneration

### Notes on the size decision

The plan records a reviewability **warning**, accepted on composition and
indivisibility rather than on the dead greenfield allowance. T009 re-verifies it
against this finished task list. Task generation added no file and no surface, so
the recorded decision stands. If a reviewer rejects the composition argument, the
plan's fallback cut is 1a (brand kit, head block, notice, `payloads.py`, groups
A/E/F/G1/G2 **and** group H) and 1b (catalog, contract, voice, groups B/C/D,
G3–G7) — with A5 moved to 1b or explicitly scoped to the vacuous case, because it
reads the catalog.

---

## Notes

- `[P]` = different files, no dependency on an incomplete task. The validation is
  one file by design, so `[P]` is scarce here and its scarcity is correct.
- The gallery ships **zero** artifacts. Roughly half the 71 checks are vacuous
  against the real tree, which is why T004 parameterizes every check by gallery
  root and why each check group carries a synthetic-fixture task. A check that is
  vacuous **and** unexercised is a check that was never proven.
- Do not create `speckit-pro/artifact-gallery/templates/`. D5 passes on an absent
  directory and D4 rejects any placeholder.
- Do not hand-edit anything under `dist/`, the runner manifest or sha256, or
  `docs-site/src/content/docs/reference/tests.md`. Regenerate them (T031, T032).
- Reuse, do not reinvent, the three URL-safety components FR-011 names:
  the round-trip conjunction in
  `tests/speckit-pro/layer6-efficiency/lib/codex_capability_contract.py`, the
  pre-parse character rejection in `scripts/release_note_policy.py`, and the
  unsafe-scheme corpus in `tests/speckit-pro/unit/test-release-note-policy.py`.
  Assembling a second implementation of any of them is how they drift apart.
- Out of scope, per the design concept's Non-goals: any template port; workflow
  wiring; a trigger-expression DSL or evaluator; automated cross-repository drift
  checking and the docs-site palette overlap test; a marker-block sync script;
  banning navigation anchors or text/comment URLs; structured-data markup, FAQ
  minimums, and site navigation chrome in the voice sheet; embedded font files.

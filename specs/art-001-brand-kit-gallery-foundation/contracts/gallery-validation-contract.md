# Contract: Gallery Validation Check Inventory

**Feature**: ART-001 | Implemented by `tests/speckit-pro/unit/test-artifact-gallery.py`

Every check the single Layer 4 test performs, with the requirement it satisfies
and the failure message it must produce. Failure messages must name the offending
file/entry and the offending block/field — a bare assertion failure does not
satisfy FR-006, FR-008, or FR-019.

**Scan scope**: source only — `speckit-pro/artifact-gallery/`. The built copies
under `dist/` are never scanned as gallery artifacts; they are only compared
against source by group F.

## Group A — Marker-block drift (FR-002, FR-003, FR-006; SC-002)

| # | Check | Fails when |
|---|-------|-----------|
| A1 | `brand-kit.css` contains exactly one `BRAND-KIT:START` and one `BRAND-KIT:END`, start before end | canonical file malformed |
| A2 | `theme-toggle.html` contains exactly one `THEME-TOGGLE:START` / `THEME-TOGGLE:END` pair, ordered | canonical file malformed |
| A3 | For every gallery HTML artifact: each marker pair it uses appears exactly once, with a matching end | duplicated or unbalanced markers |
| A4 | For every gallery HTML artifact embedding a block: the region between its markers equals the canonical region **byte for byte** | any single-character drift; message names artifact + block |
| A5 | Every `shipped` entry's artifact embeds the brand block | shipped artifact omits the block (no pass-by-absence) |

Only the delimited region is compared, so template-specific styling outside the
markers never fails (Story 1 scenario 4).

The canonical comparison uses `brand-kit.css`'s **inner** region, not the whole
file, so the provenance header and the audited contrast table can sit above the
start marker without every artifact having to embed them.

## Group B — Catalog shape (FR-007, FR-019; SC-003)

| # | Check | Fails when |
|---|-------|-----------|
| B1 | Top level has exactly the keys `schema_version`, `signals`, `templates` | extra or missing top-level key |
| B2 | `schema_version == "1.0"` | version drift |
| B3 | `templates` has 21 entries | catalog seeded wrong |
| B4 | Each entry has exactly the eight documented keys | missing/extra key; names entry + key |
| B5 | `stage` ∈ {`draft-pr`,`final-pr`,`ad-hoc`} | unrecognized stage; names entry + value |
| B6 | `category` ∈ the nine-member enum | unrecognized category; names entry + value |
| B7 | `status` ∈ {`planned`,`shipped`} | unrecognized status |
| B8 | `title` and `when_to_use` are non-empty strings | empty required field; names entry + field |
| B9 | `id` is kebab-case and unique across the catalog | duplicate id (Story 2 scenario 5) |
| B10 | `source` matches one of its two forms exactly, discriminated by `origin`; `upstream` carries a non-empty `file`, `repository` carries no `file` | malformed attribution |

## Group C — Triggers and signal closure (FR-008, FR-015, FR-016, FR-017)

| # | Check | Fails when |
|---|-------|-----------|
| C1 | `len(signals) == 5` | a signal was invented, or one was removed to disguise an addition |
| C2 | `signals` entries are unique, flat `snake_case` strings | malformed vocabulary |
| C3 | Every trigger is exactly `{"always": true}` or `{"any_of": [...]}` | unrecognized form; names entry |
| C4 | Every `any_of` array is **non-empty** | empty signal set — the failure that stops a deleted last signal from silently disabling routing |
| C5 | Every signal named by any trigger ∈ `signals` | entry names an unknown signal; names entry + signal (Story 2 scenario 2) |
| C6 | Every member of `signals` is named by ≥ 1 trigger | vocabulary carries an unused signal |
| C7 | Every entry has a `trigger`, including `ad-hoc` entries | uniform shape broken |

**C1 is the FR-017 mechanism and must not be replaced by a literal list.** The
test hard-codes the integer `5` and never holds a copy of the five names: a copy
edited in the same commit as the manifest is not an independent check. C1 catches
invention (count rises); C5/C6 catch the disguise (removing a real member orphans
its consumers).

## Group D — Artifact existence and orphans (FR-009)

| # | Check | Fails when |
|---|-------|-----------|
| D1 | For `status: "shipped"`, `templates/<id>.html` exists | missing or misnamed artifact |
| D2 | For `status: "planned"`, existence is **not** required | — (must not fail; all 21 are planned in ART-001) |
| D3 | Every file in `templates/` is claimed by exactly one entry | orphaned artifact accumulating |

Both D1 and D3 resolve the path from the identifier relative to the manifest's
own directory — never from a stored path field.

## Group E — External references (FR-011; SC-008)

Positions scanned, and **only** these:

- `src` on `script`, `img`, `iframe`
- `srcset`
- `href` on `link` where `rel` is a stylesheet or preconnect relation
- CSS `url()` and `@import`
- `fetch(...)`, `XMLHttpRequest.open(...)`, `new WebSocket(...)` string literals

| # | Check | Fails when |
|---|-------|-----------|
| E1 | Every host in a scanned position ∈ {`fonts.googleapis.com`, `fonts.gstatic.com`} | any other external host; names file + reference |
| E2 | Navigation `<a href>` to any host passes | — (must not fail) |
| E3 | URLs in comments or visible text pass | — (must not fail) |
| E4 | Every `fonts.googleapis.com` stylesheet request carries the swap-behavior parameter | the request would otherwise be served with the provider's blocking default, producing an invisible-text period; names file + reference |

**On E4 (FR-024).** This is a host-allowlist scanner extended by one property of
the request, because the allowlist alone cannot see the defect. The font
provider's stylesheet only carries a swap descriptor when the request asks for
it. Verified directly against the live endpoint: a `css2` request **without**
the display parameter returns a stylesheet containing **zero** `font-display`
declarations, which leaves the descriptor at its initial value — a blocking
behavior with an invisible-text period in the major engines. The same request
**with** the parameter returns `font-display: swap` on every `@font-face`. The
spec's edge case ("never invisible while waiting") therefore depends on a single
query parameter that no other check would notice, and that a port author can
drop while still passing E1.

E2 and E3 are **negative controls** and are asserted explicitly, because a scanner
that fails them would reject the provenance and attribution links FR-012 and
FR-020 require. Element positions are parsed with `html.parser`; the CSS and
network-call positions use targeted regular expressions, since the standard
library has no parser for them.

## Group F — Payload reach (FR-018) — BLOCKING

| # | Check | Fails when |
|---|-------|-----------|
| F1 | The set of paths under `speckit-pro/artifact-gallery/` equals the set under `dist/claude/speckit-pro/artifact-gallery/` | gallery missing from, or stale in, the Claude payload |
| F2 | The same set equality holds for `dist/codex/speckit-pro/artifact-gallery/` | gallery missing from, or stale in, the Codex payload |
| F3 | Each source gallery file is byte-identical to its Claude payload copy | truncated or stale copy |

**Why this group exists.** `build_xplat008_payloads` copies a fixed list of
top-level names per platform (`payloads.py:298-308` Claude, `:316-324` Codex) via
`copy_optional_xplat008`, which is fail-silent: a name that is absent produces no
error and no output. No existing check closes this. The standing proof is that
`speckit-pro/AGENTS.md`, `speckit-pro/CLAUDE.md`, and `speckit-pro/GEMINI.md`
exist in source, appear in neither payload, and the suite is green.

The existing payload gates compare a **fresh build against committed `dist/`** —
both sides come from `scan_payload_files` over payload roots, and `source_root`
is used only to label each file. A directory absent from both sides is
self-consistently absent and passes.

**Scope discipline**: F1/F2 are deliberately scoped to `artifact-gallery/`. A
generalized "every source file must ship" check would immediately fail on the
agent-instruction files above, which are intentionally not shipped.

**F3 is Claude-only by design.** The Codex build runs
`rewrite_payload_skill_paths_xplat008` over every file in its payload, rewriting
any literal matching `(../)+(skills|codex-skills)/...`. Gallery files contain no
such literal, but pinning byte-equality against a text-rewriting build would be
brittle. `SPA-CONTRACT.md` records the corresponding authoring rule: gallery files
must not contain a `../skills/` or `../codex-skills/` literal.

## Group G — Upstream attribution (FR-020)

| # | Check | Fails when |
|---|-------|-----------|
| G1 | The upstream notice file exists and is **not** named `LICENSE` | a file named `LICENSE` would be mistaken for this repository's own license |
| G2 | The notice reproduces the upstream permission notice verbatim, including `Copyright (c) 2026 Anthropic PBC` | notice altered or truncated |
| G3 | For each entry with `source.origin == "upstream"` whose artifact exists: the artifact carries an attribution header containing upstream repository, upstream file, verbatim copyright line, license identifier, link to full license text, and an explicit modified-derivative statement | any required element missing; names artifact + element |
| G4 | For each entry with `source.origin == "repository"` whose artifact exists: the artifact carries **no** upstream copyright line | misattributed repository-authored file |

**On G1**: `infer_payload_source_path` special-cases the exact relative path
`LICENSE` and maps it to the repository root (`payloads.py:631-632`), and
`payload_file_kind` classifies the exact path `LICENSE` as version metadata
(`:652`). A gallery file at `artifact-gallery/LICENSE` would not match those exact
comparisons today, but the spec forbids the name outright and the check enforces
it, so the gallery never depends on that exact-match detail holding.

G3 and G4 are **vacuously true in ART-001**, which ships no artifact. They are
written now because they are the contract ART-002…005 inherit, and because
writing them later means each port spec re-litigates the rule.

## Group I — Shared-block accessibility invariants (FR-004, FR-022, FR-023)

Presence checks on the **canonical** blocks only, not on artifacts. Each asserts
that a construct the accessibility requirements depend on is actually inside the
marked region — which is what makes it reach all 21 artifacts. These are cheap
static assertions, not a conformance audit; the behavioral outcomes stay with
the manual scenarios.

| # | Check | Fails when |
|---|-------|-----------|
| I1 | The `brand-kit.css` marked region contains a `prefers-reduced-motion: reduce` at-rule | reduced-motion handling absent or left outside the copied region (FR-023) |
| I2 | The marked region contains a `:focus-visible` rule | focus treatment absent or outside the copied region (FR-023) |
| I3 | The marked region sets `color-scheme` under **both** `[data-theme="dark"]` and `[data-theme="light"]` | only the `light dark` declaration is present, so native UI would follow the OS rather than the override (FR-004) |
| I4 | The `theme-toggle.html` marked region contains a `button` element carrying both an accessible-name source and a state attribute | control unnamed or stateless (FR-022) |

**Why these are automated at all**, given that browser behavior is not: the
failure mode here is *omission from the copied region*, which is a static
property of two files. A token defined above the start marker looks correct in
the canonical file and silently reaches no artifact — the same
inside-vs-outside-the-marker distinction group A already depends on. I1–I4 cost
a few assertions and close the one gap where "it is in `brand-kit.css`" is not
the same as "every artifact has it".

**What these do NOT claim.** Presence is not conformance. That the region
contains a `:focus-visible` rule does not prove every interactive element is
reachable, and that a `button` carries a state attribute does not prove the
state is correct in both positions. Those remain manual (M7, M8).

## Group H — Suite integration (FR-014)

| # | Check | Fails when |
|---|-------|-----------|
| H1 | The test is registered in the Layer 4 `scripts` array of `tests/speckit-pro/suite-manifest.json` | test not discoverable by a plain suite run |

Registration entry, appended last (the array is append-ordered, not sorted):

```json
{ "path": "tests/speckit-pro/unit/test-artifact-gallery.py", "label": "test-artifact-gallery", "baseline": null }
```

## Not validated by the automated suite

Per FR-014's standard-runtime constraint and the spec's assumptions, the suite
drives no browser. These are verified manually and recorded as acceptance
evidence (SC-001, SC-005, SC-006):

- `file://` rendering with no console errors
- First-paint theme correctness with no flash of light theme
- Theme-toggle behavior and persistence, including the storage-refused path
- Offline readability with system-typeface fallback
- Keyboard reachability and activation of the theme control, and the name and
  state it reports in **both** theme positions (FR-022, SC-010)
- Reduced-motion behavior, including the cross-theme transition (FR-023)
- Native form controls and scrollbars following a **manual** theme override
  rather than the operating-system preference (FR-004)
- Absence of an invisible-text period during font loading (FR-024, SC-011) —
  E4 proves the request is correct, not that the rendering is

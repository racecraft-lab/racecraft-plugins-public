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
| B9 | `id` is unique across the catalog **and** matches filename-safe kebab-case — lowercase alphanumerics in hyphen-separated segments, no leading/trailing/repeated hyphen, no path separator, parent-directory segment, whitespace, or dot | duplicate id (Story 2 scenario 5); an id that would compose a path outside `templates/` (FR-019) |
| B10 | `source` matches one of its two forms exactly; `source.origin` ∈ {`upstream`,`repository`}; `upstream` carries a non-empty `file`, `repository` carries no `file` | malformed attribution; an unrecognized `origin` — which must fail here rather than fall through group G |
| B11 | `source.file` is unique across the catalog | two entries claiming one upstream file, which FR-020's per-artifact attribution cannot express |
| B12 | the catalog's identifier set equals the seeded identifier set pinned in the validation | a later spec renaming an identifier — which every other check misses, because renaming the derived file alongside it leaves the catalog and the artifact directory agreeing with each other |

**On B9 and the derived path.** FR-019 no longer asks whether the id "equals the
referenced file stem": with the path composed as `templates/<id>.html` that
comparison is true by construction and can never fail. The format rule replaces it
because that is what the composition actually depends on — the id is
concatenated into a path, so its character set is the only thing keeping the
resolution inside the gallery. **Entries are named by `id` in failure messages,
except where the id is itself missing, duplicated, or malformed — those are named
by array position**, since naming by identifier is circular exactly there. All
offending entries are reported, not just the first.

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
| C8 | The set of names in `signals` equals the set of signals documented in `SPA-CONTRACT.md` | a member is undocumented, or the document describes a name the vocabulary does not carry — the check that makes a coordinated rename visible (FR-015, FR-017) |

**C1 is the FR-017 mechanism and must not be replaced by a literal list.** The
test hard-codes the integer `5` and never holds a copy of the five names: a copy
edited in the same commit as the manifest is not an independent check. C1 catches
invention (count rises); C5/C6 catch the disguise (removing a real member orphans
its consumers).

**Why C8 is needed, and why it is not a second copy.** C1 plus C5/C6 do not close
the space. A signal renamed in `signals` **and** in its consuming trigger within
one change keeps the count at five and keeps closure intact in both directions, so
C1, C5, and C6 all pass while the vocabulary changes underneath ART-007/009/010;
an addition paired with an equal-sized removal behaves the same way. C8 closes
that by asserting the vocabulary against the per-signal documentation FR-015
already requires. This is closure between two shipped artifacts — the same shape
as C5/C6, which close `signals` against the triggers — not a list held inside the
test, so FR-017's prohibition is untouched. The residual limit is stated in
FR-017: a rename carried through the catalog, the trigger, and the documented
meaning together still passes, and that is the recorded-amendment path the
stability guarantee prescribes.

## Group D — Artifact existence and orphans (FR-009)

| # | Check | Fails when |
|---|-------|-----------|
| D1 | For `status: "shipped"`, `templates/<id>.html` exists | missing or misnamed artifact |
| D2 | For `status: "planned"`, `templates/<id>.html` **does not** exist | an artifact shipped under a `planned` entry — see below (all 21 are planned in ART-001, and no artifact exists, so this passes) |
| D3 | Every `.html` file in `templates/` is claimed by exactly one entry | orphaned artifact accumulating |
| D4 | `templates/` contains no non-`.html` file | a file the derivation can never name, reported as disallowed rather than as an unclaimable orphan |
| D5 | An **absent** `templates/` directory counts as zero artifacts | — (must not fail; this is ART-001's actual shipped state) |

Both D1 and D3 resolve the path from the identifier relative to the manifest's
own directory — never from a stored path field.

**D2 is a biconditional, not a waiver (FR-009).** The earlier formulation only
said existence was *not required* for `planned`, which left a real artifact
legally present under a `planned` entry. That mattered because A5 keys the
brand-block comparison on `shipped` status: such a file would ship without its
embedded block ever being compared, making `status` an opt-out from the drift
check. It also left SC-004 unenforceable — adding an artifact without flipping its
status would pass, when "changes exactly one catalog value" is the whole claim.
Tying existence to status in both directions closes both.

**D4 and D5 bound the sweep.** The derived path is always `<id>.html`, so a
non-HTML file in `templates/` is unclaimable by construction; without D4 it would
be a permanent, unfixable D3 failure instead of an actionable message. D5 covers
the state this feature actually ships: no artifact is ported, and version control
does not preserve an empty directory, so `templates/` is absent at merge and group
D must pass vacuously rather than error on a missing path.

**D5 is what makes D4 safe, and the two must land together.** Because an absent
directory passes, there is no reason to track `templates/` with a placeholder
file — and D4 would reject one, since a placeholder is not an `.html` artifact.
Shipping D4 without D5 would push an author toward exactly the placeholder D4
forbids. The rule for a port author is therefore: create `templates/` when you add
the first artifact to it, never before.

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
| F4 | Each source gallery file is byte-identical to its **Codex** payload copy | truncated, stale, or rewritten copy |
| F5 | No source gallery file contains a **reference the Codex rewriter would match** — that is, `REL_SKILL_PATH_XPLAT008` finds nothing in it | the authoring rule F4 depends on, now enforced rather than only documented |

**F5 must be defined by the rewriter's pattern, not by a substring search.** The
rewriter requires at least one character after the `skills/` segment drawn from
`[^\s`)"']` (`payloads.py:401`). A prose mention written in backticks — which is
exactly how `SPA-CONTRACT.md` records this rule for authors — therefore does
**not** match, because the next character is a backtick. Verified against the live
pattern: `` `../skills/` `` and a bare `../skills/` followed by a space both fail
to match, while `../skills/a/SKILL.md`, `../../codex-skills/foo/SKILL.md`, and a
markdown link target all match. A substring check for `../skills/` would fail
`SPA-CONTRACT.md` for documenting its own rule, and would fail it in a way F4
could not explain. Reuse the rewriter's pattern so the check and the build agree
by construction.

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

**Content equality now covers both platforms (FR-018).** F1/F2 compare path sets
only, and a path set cannot see a copy that arrived truncated, stale, or
rewritten — least of all `manifest.json`, whose silent divergence would have a
consumer routing against a different catalog than the repository declares.

An earlier revision scoped byte-equality to Claude, on the grounds that pinning it
against a text-rewriting build would be brittle: the Codex build runs
`rewrite_payload_skill_paths_xplat008` over every file in its payload. Reading
that rewriter settles the question rather than leaving it to judgment. It
substitutes on `REL_SKILL_PATH_XPLAT008 = (?:\.\./)+(?:skills|codex-skills)/…`
(`payloads.py:401`) and writes the file back **only if the substitution changed
it** (`:430-431`). So on a file containing no such literal the Codex build is a
verified no-op, and F4 is exactly as stable as F3.

That makes the authoring rule load-bearing rather than advisory, which is why F5
enforces it. `SPA-CONTRACT.md` still records it for authors, but a rule that only
a document carries is one a port author can break while every check stays green —
and breaking it is precisely what would make F4 fail confusingly instead of
failing at the real cause.

## Group G — Upstream attribution (FR-020)

| # | Check | Fails when |
|---|-------|-----------|
| G1 | The upstream notice file exists and is **not** named `LICENSE` | a file named `LICENSE` would be mistaken for this repository's own license |
| G2 | The notice reproduces the upstream permission notice verbatim, including `Copyright (c) 2026 Anthropic PBC` | notice altered or truncated |
| G3 | For each entry with `source.origin == "upstream"` whose artifact exists: the artifact carries an attribution header containing upstream repository, upstream file, verbatim copyright line, license identifier, link to full license text, and an explicit modified-derivative statement | any required element missing; names artifact + element |
| G4 | For each entry with `source.origin == "repository"` whose artifact exists: the artifact carries **no** upstream copyright line | misattributed repository-authored file |
| G5 | Every entry takes exactly one of the G3/G4 branches | an `origin` matching neither — the fail-open case (FR-020) |

**On G5 — the discriminator must be exhaustive, not merely present.** G3 and G4
as written are two independent conditionals. An entry whose `origin` is neither
literal matches neither branch, so an upstream-derived artifact would ship with no
attribution header, no misattribution check, and a green suite. B10 now rejects an
unrecognized `origin` at the shape layer and G5 asserts branch exhaustiveness at
the attribution layer; either alone would leave the gate readable as passing when
it never ran. A licensing gate that silently declines to run is worse than no gate,
because green is read as evidence the attribution was checked.

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

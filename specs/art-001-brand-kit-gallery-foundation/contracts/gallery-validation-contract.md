# Contract: Gallery Validation Check Inventory

**Feature**: ART-001 | Implemented by `tests/speckit-pro/unit/test-artifact-gallery.py`

Every check the single Layer 4 test performs, with the requirement it satisfies
and the failure message it must produce. Failure messages must name the offending
file/entry and the offending block/field — a bare assertion failure does not
satisfy FR-006, FR-008, or FR-019.

**Scan scope**: source only — `speckit-pro/artifact-gallery/`. The built copies
under `dist/` are never scanned as gallery artifacts; they are only compared
against source by group F.

**Artifacts generated at run time are outside every check in this document, and
that limit is load-bearing.** Nothing here scans what a later spec's authoring
agent emits, and nothing in this feature ever will. It is stated in the contract
because SC-008's reach ("across the gallery") is otherwise readable as covering
generated output, and a workflow-spec author who reads it that way would be relying
on a guarantee that was never made. What governs generated artifacts is the
untrusted-input obligation FR-027 places in `SPA-CONTRACT.md` — the four contexts
an interpolated value may never enter, and context-correct escaping for the rest.
That obligation exists precisely because group E cannot reach that far.

## Group A — Marker-block drift (FR-002, FR-003, FR-006; SC-002)

| # | Check | Fails when |
|---|-------|-----------|
| A1 | `brand-kit.css` contains exactly one `BRAND-KIT:START` and one `BRAND-KIT:END`, start before end | canonical file malformed |
| A2 | `theme-toggle.html` contains exactly one `GALLERY-HEAD:START` / `GALLERY-HEAD:END` pair, ordered | canonical file malformed |
| A3 | For every gallery HTML artifact: each marker pair it uses appears exactly once, with a matching end | duplicated or unbalanced markers |
| A4 | For every gallery HTML artifact embedding a block: the region between its markers equals the canonical region **byte for byte** | any single-character drift; message names artifact + block |
| A5 | Every `shipped` entry's artifact embeds **both** canonical blocks | shipped artifact omits either block — A3 skips a file using neither pair and A4 skips one embedding neither, so an artifact omitting the head block was invisible to all of group A while hand-writing its own policy |

**The head block's marker pair is named for the region, not the control.** It carries
the policy declaration, the pre-first-paint theme application, the colour-scheme
selection, and the theme control's behaviour — so naming it after the toggle alone
mislabels it. The rename is done now, while zero artifacts exist; after the ports land
it would cost 21 files. The canonical **filename** is unchanged, because the plan's
declared file operations and both payload declarations depend on it.

**Why the block emits its control from script rather than containing markup for it.**
J7 and J8 require the policy declaration to be a direct child of the head element with
no content-bearing element before it, while I4 requires the theme control's accessible
name and state to live inside the same marked region. Those cannot both be satisfied by
a region containing a `button` element: the head element admits only metadata content,
so a parser encountering a `button` there closes the head and opens the body, which
silently relocates the region and voids J7 for every artifact that embeds it. The region
therefore stays entirely within the head and creates the control at run time. The
consequence is deliberate and consistent with FR-004: with scripting unavailable the
reader still gets their operating-system theme through the media query, and loses only
the ability to override it — the same degradation the storage-unavailable path already
accepts.

Only the delimited region is compared, so template-specific styling outside the
markers never fails (Story 1 scenario 4).

The canonical comparison uses `brand-kit.css`'s **inner** region, not the whole
file, so the provenance header and the audited contrast table can sit above the
start marker without every artifact having to embed them.

## Group B — Catalog shape (FR-007, FR-019; SC-003)

| # | Check | Fails when |
|---|-------|-----------|
| B1 | Top level has exactly the keys `schema_version`, `signals`, `export_kinds`, `templates` | extra or missing top-level key |
| B2 | `schema_version == "1.0"` | version drift |
| B3 | `templates` has 21 entries | catalog seeded wrong |
| B4 | Each entry has exactly the nine documented keys | missing/extra key; names entry + key |
| B5 | `stage` ∈ {`draft-pr`,`final-pr`,`ad-hoc`} | unrecognized stage; names entry + value |
| B6 | `category` ∈ the nine-member enum | unrecognized category; names entry + value |
| B7 | `status` ∈ {`planned`,`shipped`} | unrecognized status |
| B8 | `title` and `when_to_use` are non-empty strings | empty required field; names entry + field |
| B9 | `id` is unique across the catalog **and** matches filename-safe kebab-case — lowercase alphanumerics in hyphen-separated segments, no leading/trailing/repeated hyphen, no path separator, parent-directory segment, whitespace, or dot | duplicate id (Story 2 scenario 5); an id that would compose a path outside `templates/` (FR-019) |
| B10 | `source` matches one of its two forms exactly; `source.origin` ∈ {`upstream`,`repository`}; `upstream` carries a non-empty `file`, `repository` carries no `file` | malformed attribution; an unrecognized `origin` — which must fail here rather than fall through group G |
| B11 | `source.file` is unique across the catalog | two entries claiming one upstream file, which FR-020's per-artifact attribution cannot express |
| B12 | the catalog's identifier set equals the seeded identifier set pinned in the validation | a later spec renaming an identifier — which every other check misses, because renaming the derived file alongside it leaves the catalog and the artifact directory agreeing with each other |
| B13 | every entry's `exports` is an array whose members are declared in `export_kinds`, with no repeat | an artifact left silent about whether its reader can carry a conclusion out — an absent key cannot be told apart from a deliberate read-only artifact, which is the ambiguity the key exists to close |
| B14 | the export vocabulary closes in both directions: every declared kind is carried, every carried kind is declared | dead vocabulary a later author has to guess the meaning of, and a kind no consumer can resolve — the catalog-wide half B13 cannot see, because it reads one entry at a time |

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

**Positions scanned: every URL-valued attribute, by default.** The earlier
formulation enumerated five position families and said "and **only** these",
which made the scan a denylist — anything unenumerated was permitted by
construction. Re-derived against the parser, that enumeration omitted `source`
(`src` and `srcset`), `video` (`src`, `poster`), `audio`, `track`, `object`
(`data`), `embed`, `input type="image"`, SVG `image`/`use` (`href`), `form`
(`action`), `a` (`ping`), and `meta http-equiv="refresh"` — and omitted `base`
(`href`) entirely, which is not a missing case but a total bypass (group J). On
`link` it named two relations, which are not the fetching set: `stylesheet`,
`preload`, `modulepreload`, `prefetch`, `icon`, and `manifest` each fetch, and
`preload`/`modulepreload` fetch **and execute**. `preconnect` and `dns-prefetch`
fetch nothing but do contact the host — which is why `preconnect` was in the
original list and why a fetch-only reading would not serve the privacy property
FR-011 protects.

**Which files group E scans, and why this is not vacuous in ART-001.** FR-011 says
"every gallery artifact", and an artifact (data-model Entity 8) is a self-contained
HTML file under `templates/` — of which this feature ships **zero**. Read that way
the whole group would be vacuous at merge. It is not, and must not be: group E
scans **every file under the gallery directory**, including the canonical
`brand-kit.css` and `theme-toggle.html`. That is the reading the propagation
argument demands — those two files are embedded **verbatim into all 21 artifacts**,
so a bad `@import` or a foreign `src` in a canonical block reaches every artifact
and is fixable in none of them. Scanning them is the only part of group E that can
fire in ART-001, and it is the part guarding the highest-leverage surface.

The scan is therefore **default-deny with a closed exemption list**:

- **Exempt**: `href` on `a`; addresses inside parser-recognized comments; visible
  text.
- **Scanned**: every other URL-valued attribute, plus style `url()` and both
  `@import` forms, plus `fetch(...)`, `XMLHttpRequest.open(...)`,
  `new WebSocket(...)`, `navigator.sendBeacon(...)`, `new Worker(...)`,
  `new EventSource(...)`, `importScripts(...)`, and dynamic `import(...)` string
  literals **anywhere in the document text, including attribute values** — which is
  what catches a network destination hidden in an event-handler attribute whose
  element's own `src` is innocuous.
- **Unrecognized attribute carrying a URL-shaped value**: fails. A position nobody
  anticipated is reported rather than admitted.

| # | Check | Fails when |
|---|-------|-----------|
| E1 | Every host resolved from a scanned position ∈ {`fonts.googleapis.com`, `fonts.gstatic.com`}, by **exact case-folded equality**; a trailing root dot fails | any other host; a substring or prefix match that would admit `fonts.googleapis.com.evil.example`; `fonts.googleapis.com.` (fails closed, deliberately — see below); names file + reference |

**E1 is only safe because E6 runs first — this was found by executing it, not by
reading it.** Case folding is a lossy many-to-one mapping. A host carrying the Latin
small letter long s folds onto an allowlisted host exactly: it compares **equal** to
`fonts.gstatic.com` under `casefold`, while resolving to a domain an attacker controls.
Executed against the checks as first written, that reference was admitted by E1 (it
compares equal), admitted by E5 (it round-trips, carries no userinfo and no port), and
admitted by E6 until E6's repertoire was closed. Lowercasing would not have collided —
folding is what creates the hole, and folding is what the requirement asks for, so the
repertoire restriction is the half that makes it correct.

E6 therefore rejects on a closed grammar repertoire and refuses every non-ASCII
character **before** any host comparison happens. The test asserts both halves — that
E1 and E5 alone still admit the folded host, and that E6 rejects it — so the reason
this clause exists cannot be refactored away by someone who reads E6 as redundant
tidying.
| E2 | Navigation `<a href>` passes **for `https:`, `mailto:`, and fragment schemes only** | — (must not fail on those); **must** fail on `javascript:`, `data:`, `vbscript:`, `blob:` in the same position |
| E3 | URLs in **parser-recognized** comments or visible text pass | — (must not fail) |
| E4 | Every `fonts.googleapis.com` stylesheet request carries the swap-behavior parameter | the request would otherwise be served with the provider's blocking default, producing an invisible-text period; names file + reference |
| E5 | Host is obtained with a structured URL parser; userinfo and port are absent, and the parse round-trips to the original string | a reference carrying a userinfo segment that reads as an allowlisted host while the real host is an attacker's; `https://fonts.googleapis.com:8443/`; any non-canonical parse |

**On writing these examples down.** The userinfo case is deliberately described rather
than written as a literal. A literal `userinfo@host` string is indistinguishable from an
email address to a pattern matcher, and the repository's tree-wide privacy scan flags it
as a leaked address — which is exactly what happened when this contract first stated the
example verbatim. The attack is unchanged and the rule is unchanged; only the notation
avoids tripping a scanner that is right to be suspicious of that shape.
| E6 | Every reference in a scanned position is rejected **before parsing** if it contains a backslash, whitespace, a control character, or a character outside the unreserved URL grammar | the scanner-vs-browser differential: `https://evil.example\@fonts.googleapis.com/x.css` parses to host `fonts.googleapis.com` here and loads from `evil.example` in a browser |
| E7 | In a resource-loading position, scheme ∈ {`https`} or the reference is same-document relative | `javascript:`, `data:`, `blob:`, `vbscript:`, `file:` — none of which expose a host to compare |
| E8 | A reference in a scanned position that cannot be parsed, or that yields no host, **fails** | fail-open on precisely the set an evader controls |
| E9 | Both `@import` forms are recognized — the URL-token form and the **bare string** form | `@import "https://evil.example/a.css";` matches no pattern written for `@import url(...)` |
| E10 | Any escape sequence inside a style `url()` or `@import` reference **fails** | `@import "\68 ttps://evil.example/a.css";` — no host appears in the text at all, and the browser decodes and fetches it |
| E11 | `srcset` is split by the documented algorithm — each candidate's URL is a run up to the next whitespace, so an embedded comma is **not** a separator — and **every** candidate is scanned | scanning only the first candidate; or naive comma splitting, which fragments `https://h/x,y.png 1x` into tokens matching no real candidate |
| E12 | No scheme-relative (`//host/…`) reference in any scanned position | invisible to any pattern keyed on an explicit scheme, and resolves against `file:` rather than a network scheme (group J) |

**On E1/E5/E6 — reuse, do not reinvent.** This repository already owns the
hardened form of this comparison, and the requirement (FR-011) directs validation
to reuse it. `_openai_url` in
`tests/speckit-pro/layer6-efficiency/lib/codex_capability_contract.py` asserts a
conjunction that includes `parsed.geturl() == value` (canonical round-trip),
`username is None`, `password is None`, `port is None`, and
`parsed.netloc.lower() == host` — which is E5 exactly. `_validated_http_url` in
`scripts/release_note_policy.py` rejects control, whitespace, and delimiter
characters *before* `urlsplit`, which is E6 exactly. Neither was written for this
feature; both were written for the same class of problem.

**On the style positions' scan scope and surface forms.** The `url()` and
`@import` patterns run over the **whole document text**, not only within a `style`
element or attribute — which is what makes E10's escape prohibition and E12's
scheme-relative ban prohibitions rather than parses, since neither has a
standard-library parser to be scoped by. Two consequences are recorded so neither
reads as an oversight. A URL written inside a **CSS** comment is scanned and will
fail; this is over-strict rather than unsafe, and an author needing a prose URL
writes it in an HTML comment, which E3 exempts. And `@namespace "https://…"` is
matched while initiating no fetch — a false positive in the same direction. On
surface forms, the `url()` pattern MUST be case-insensitive and MUST tolerate
whitespace and newlines between the token and its argument, with or without
quotes: executed against a straightforward case-insensitive pattern, the quoted,
unquoted, uppercase `URL(`, internal-whitespace, and embedded-newline forms are all
matched, so this is a statement of what the pattern must be rather than a defect
found — but it is stated because a pattern written without those tolerances would
silently miss ordinary CSS.

**On E11 — stated as a correctness rule, not as a closed bypass.** Naive comma
splitting was executed and does fragment comma-bearing and `data:` URLs, but in the
cases tried it still surfaced the foreign host rather than hiding it. The defect it
demonstrates is an unreliable candidate list in a position that can carry several
references, which is why the rule fixes the algorithm and requires every candidate
be scanned rather than claiming an evasion that was not reproduced.

**On E7 — the negative corpus already exists.**
`tests/speckit-pro/unit/test-release-note-policy.py` maintains a table-driven
corpus of unsafe destinations covering `javascript:`, mixed-case `JaVaScRiPt:`,
`data:text/html`, `vbscript:`, the scheme-relative form, and the backslash form.
Reuse it rather than assembling a second one that will drift from it.

**On E2 and E3 — the exemptions are the attack surface.** They remain
**negative controls** and are still asserted explicitly, because a scanner that
fails them would reject the provenance and attribution links FR-012 and FR-020
require. But E2 is now bounded by scheme: "navigation to any host" taken literally
exempted `javascript:` and `data:`, which are not navigation to a host at all.
And E3's "comment" means a construct **the parser classifies** as a comment. That
distinction is load-bearing in both directions — content inside a `script` element
is raw text rather than a comment even when written as `<!-- … -->`, so an
implementation that strips comment-shaped regions with a pattern *before* parsing
would blind itself to live script, while a parser-driven one does not.

**Parsing strength is not uniform, and the contract says so.** Element positions
are parsed with `html.parser`, which satisfies the constitution's structured-parser
requirement and — verified by execution — decodes character references in attribute
values, so `<img src="&#104;ttps://evil.example/x">` yields a fully decoded URL and
entity encoding is **not** an evasion there. The style and network-call positions
have no standard-library parser and are matched by targeted expressions: a recorded
deviation, which is why E10 and E12 constrain those positions by **prohibition**
rather than by decoding. A regex-scanned position must not be presented as carrying
the same strength as a parsed one.

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
| G4 | For each entry with `source.origin == "repository"` whose artifact exists: the artifact carries **no upstream attribution element at all** — not merely no copyright line | misattributed repository-authored file, including one carrying a complete header that happens to omit the copyright line |
| G5 | Every entry takes exactly one of the G3/G4 branches | an `origin` matching neither — the fail-open case (FR-020) |
| G6 | The upstream **file** named in an artifact's header equals its entry's `source.file` | a header asserting a different provenance than the catalog declares — what a header copy-pasted from a neighbouring artifact produces |
| G7 | The upstream **repository** named in an artifact's header equals the single repository this contract names | a header asserting an upstream this gallery does not derive from |
| G8 | the header's licence identifier is the upstream licence, compared not merely present | an artifact claiming any licence it likes — G3 asks only that a value follow the label, and the reference scan exempts comments, so `License: WTFPL-2.0` satisfied every other check |
| G9 | the header's licence-text reference is the notice shipped in this gallery | a reader sent anywhere for "the full license text"; also the pairing that revealed the pinned literal contradicted the path the contract prescribes |

**On G6/G7 — presence is not provenance.** G3 checks each required element for
presence and nothing more, so a header naming a different upstream file than its
own entry satisfies it exactly. The catalog and the header are the only two places
provenance is asserted and nothing joined them, which means the attribution header
— a licensing claim a downstream reader relies on — could be well-formed and false
at the same time. B11 already makes `source.file` unique across the catalog, so
once G6 holds, each artifact's asserted provenance is unique and catalog-backed.

**On G4 — test the claim, not one symptom of it.** The earlier formulation failed
only on an upstream *copyright line*, which let a repository-authored artifact
carry an otherwise complete and convincing attribution header — repository,
filename, license identifier, license link — and still pass by avoiding that one
line. G3 and G4 now test the same claim from opposite directions instead of
testing a claim on one side and a symptom on the other.

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
| I5 | The marked region validates the stored override against the closed set of theme names before applying it, and the value written to `data-theme` is a literal from that set rather than the string read back | an unvalidated persisted value reaching all 21 artifacts (FR-004) |
| I6 | The storage key in the marked region is namespaced to this gallery | an unnamespaced key such as `theme`, which collides in both directions with any other local document sharing the storage partition (FR-004) |

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

I5 and I6 are the same *kind* of assertion applied to the storage path: whether
the closed-set validation and the namespaced key sit **inside the copied region**.
A validation written above the start marker looks correct in `theme-toggle.html`
and reaches no artifact — the identical failure mode I1–I4 exist to catch.

## Group J — Prohibited constructs (FR-027)

Artifact-level prohibitions. These are checks on the **artifact**, not on the
scanner, because each names a construct that changes what the scanner is reading
or that gives the document reach it has no reason to have. All are vacuously true
in ART-001, which ships no artifact; they are the contract ART-002…005 inherit.

| # | Check | Fails when |
|---|-------|-----------|
| J1 | No `base` element | the one construct that defeats group E **completely** — every reference relative, one `<base href="https://attacker.example/">`, and no foreign host in any scanned position while the browser loads everything from that host |
| J2 | No scheme-relative (`//host/…`) reference anywhere | resolves against `file:` rather than a network scheme, composing a Windows network-share path and an authenticated connection to an attacker-named host; also invisible to any explicit-scheme pattern |
| J3 | No `on*` event-handler attribute | executable content in a position no resource-load scan reads; can hold a network destination while the element's own `src` stays innocuous |
| J4 | No `srcdoc` attribute | a complete nested document, with its own script, carried in an attribute value |
| J5 | No `form` element with an `action`, and no `ping` attribute on any element | both send rather than fetch; `ping` is the sharper case because it rides the `a` element E2 exempts |
| J6 | Every artifact carries an in-document policy declaration restricting at minimum base URI, form submission, embedded objects, nested documents, and outbound connections | the only control covering the positions a static scan provably cannot see is absent |
| J7 | The declaration is a **direct child of the head element** | the whole policy is discarded at parse and the artifact looks protected while carrying nothing |
| J8 | **No content-bearing element precedes it** — only a character-encoding declaration may | content before the declaration is outside its coverage, so the artifact is partly unprotected in a way nothing else reveals |
| J9 | The declaration names **`'none'`** for each restricted directive and never `'self'` | a filesystem-opened document has an implementation-defined, usually opaque origin, so `'self'` resolves inconsistently across engines |
| J10 | The declaration names **none of** the reporting-endpoint, frame-ancestry, or sandbox directives | those three are silently stripped from an in-document declaration; their presence marks an author relying on protection that was removed |

**J7–J10 exist because a declaration's realistic failure mode is an authoring
mistake, not a browser refusing it.** Each of those four conditions produces an
artifact that reads as protected and is not, with no visible symptom — a console
message at most. They are all statically checkable, so the uncertainty that would
otherwise attach to this control is moved from run time to build time.

**Enforcement over the local-file scheme was researched to source level, not
assumed.** The in-document delivery algorithm strips exactly three directives —
reporting endpoint, frame ancestry, and sandbox — and none of the five this contract
requires is among them. None of the three major engines gates in-document policy
ingestion on the document's scheme, and the base-URI restriction in particular is
enforced through a path that bypasses the one scheme-based exemption that exists.
This is confirmed against shipping engine source rather than executed in a browser,
so a single manual three-engine check remains a verification item the first port spec
discharges — it cannot run here, where no artifact exists.

**Why J1 is separated from group E rather than added to it.** Group E asks "is
this host allowed". A base element carries no disallowed host — it changes what
every *other* reference resolves to. No amount of host checking sees it, so it has
to be a prohibition on the construct.

**Why J6 is narrow, and what it does not buy.** Because the artifacts run with no
server, no response header reaches them and an in-document declaration is the only
policy channel available. That channel cannot carry the framing, sandbox, or
reporting directives a header can — those are specified as ignored when delivered
in-document — and the artifacts' own inline behavior means it cannot
meaningfully restrict script without a per-artifact digest — which the
embed-verbatim model does not admit, since each template adds its own inline
behavior on top of the shared snippet. The directive set is therefore restricted to
the five above, all of which the gallery legitimately needs none of, so nothing
breaks. It is **defense in depth layered behind group E**, not a replacement for
it: J1–J5 and E1–E12 each fail independently, so neither being weakened silently
disarms the other.

## Group H — Suite integration (FR-014)

| # | Check | Fails when |
|---|-------|-----------|
| H1 | The test is registered in the Layer 4 `scripts` array of `tests/speckit-pro/suite-manifest.json` | test not discoverable by a plain suite run |

Registration entry, appended last (the array is append-ordered, not sorted):

```json
{ "path": "tests/speckit-pro/unit/test-artifact-gallery.py", "label": "test-artifact-gallery", "baseline": null }
```

## Group K — Canonical-block cross-file agreement (FR-022, FR-024)

Closure between the **two canonical files**, the same shape as C8 closing the
catalog's signal vocabulary against the contract document's prose. Each row names
a value one file writes and the other consumes, extracted from each file and
compared — never held as a literal in the test, which would make the test a third
copy to keep in step rather than a check on the other two.

| # | Check | Fails when |
|---|-------|-----------|
| K1 | The class `theme-toggle.html`'s marked region sets on the control it builds is a class `brand-kit.css`'s marked region carries a rule for, and every other class the region sets is styled there too | the control carries no class at all (which I4 passes), the class is renamed in one file alone, or the rule sits above the brand start marker and so reaches no artifact; names both files and the class |
| K2 | The set of families named **first** in `brand-kit.css`'s typeface stacks equals the set of families in `theme-toggle.html`'s font request | a face added to the kit and not to the request, or renamed in one file alone — every artifact then falls through to the next face in the stack while E4 still passes; names both files and the family |

**Why this is its own group rather than rows added to I and E.** Group A catches
drift between a canonical region and an artifact's copy of it. Group I catches a
construct omitted from a copied region. Neither can see two regions that are each
internally correct and disagree **with each other**, which is a third failure mode
— and the one that has actually shipped: the theme control went out unstyled and
was caught in a browser screenshot, because I4 asks for a button carrying a name
and a state and says nothing about the class the kit styles it by. E4 has the
same blind spot for K2: the request it validates is well formed, so a family
missing from it produces a plausible-looking render rather than a failure.

**K1 asserts one direction, K2 asserts both.** A class the kit styles and the head
block never sets is not a defect — the kit legitimately carries rules a template
opts into — while a class the head block sets and the kit never styles is the
unstyled ship. Both one-sided renames are caught by that one direction, since each
leaves the head block naming a class no rule matches. K2's two sides are closed
against each other in both directions, because an unrequested face falls through
to a fallback and an unused request costs every artifact a fetch.

**K2 compares families only, by decision.** An unrequested axis value is
synthesised by the engine; an unrequested family is not served at all. Comparing
the weight lists as well would make the check fail on every ordinary weight change
and teach a reader to edit it rather than read it. Weight coverage stays with the
manual typography scenario.

**Neither row holds a copy of the agreed value.** What the test holds is a
*locator* for each side — how a class is set, how a typeface stack is spelled,
which query parameter names a family — which is the distinction C8 already records
for naming a section heading without restating the vocabulary under it. The
fixtures use synthetic class names and synthetic typeface names throughout, so a
check that had quietly grown a shipped literal would fail every one of them.

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
- Theme-override **behavior** when the stored value is outside the closed set
  (FR-004) — I5 proves the validation is inside the copied region, not that the
  artifact falls back correctly when a hostile value is present. Seed the storage
  key with an arbitrary string and confirm the artifact renders in the
  operating-system theme and reports no error.
- That the in-document policy declaration (FR-027, J6) is **enforced** and does not
  break any legitimate gallery behavior — J6 proves the declaration is present with
  the required directives, not that a browser honors it over the local-file scheme
  nor that the artifact still works under it. Both halves are manual, and the
  enforcement half is the one carrying real uncertainty: in-document delivery is
  specified without a scheme restriction, but that is an inference from the
  processing model rather than a stated guarantee for local files. Confirm in each
  target browser that fonts still load, the theme control still operates, and a
  deliberately-added violating reference is actually blocked — a policy that is
  present but unenforced is the failure this item exists to catch.
- Absence of an invisible-text period during font loading (FR-024, SC-011) —
  E4 proves the request is correct, not that the rendering is

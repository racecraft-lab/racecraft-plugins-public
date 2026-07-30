# Contract: Routing Catalog Interface

**Feature**: ART-001 | Consumers: routing design in ART-007/009/010, template
ports ART-002…005

This is the machine-readable interface `speckit-pro/artifact-gallery/manifest.json`
exposes. The shipped, human-facing statement of the same contract lives in
`speckit-pro/artifact-gallery/SPA-CONTRACT.md`, because JSON cannot carry
explanatory notes (FR-010).

The catalog ships inside the plugin payload and is read from a version-scoped
install cache. Consumers therefore resolve paths **relative to the manifest's own
directory** — repository-relative paths would not resolve at read time.

**Which statement of the shape governs.** The shape is written down twice: as
prose here and in `SPA-CONTRACT.md`, and as assertions in the Layer 4 validation.
Per FR-010 the **validated** shape is normative and the prose is its explanatory
statement. A port author who finds the two disagreeing follows the validation and
reports the disagreement as a defect. Only the signal vocabulary is closed between
prose and data automatically (C8); the rest is held true by review.

## Document shape

```
{
  "schema_version": "1.0",     // string, first key
  "signals":        [...],      // 5 strings, the closed vocabulary
  "templates":      [...]       // 21 entry objects
}
```

Exactly three top-level keys, in that order. No `$schema`, no `description`.

`schema_version` follows the repository's two hand-authored version-carrying
manifests — `tests/speckit-pro/suite-manifest.json` and
`speckit-pro/speckit_pro_runner/install_inventory.json` — both of which use a
`snake_case` key with the string value `"1.0"`.

**Correction to the original justification.** This field was first justified by
install-cache lag — that a consumer might read an older shape than current
validation expects. That channel does not actually exist: the catalog and every
consumer that reads it ship in the *same* version-scoped payload, so they cannot
skew relative to each other, and the repository's own validation only ever reads
the source tree. The field is kept because it matches house form and costs one
line, not because a live skew channel requires it.

**Failure posture (stated; migration semantics deliberately not stated).** A
consumer that reads a `schema_version` it does not recognize, or one whose major
version is newer than it understands, MUST refuse to route and MUST report the
unrecognized value rather than interpreting the document. A version it recognizes
at the same major MUST NOT be treated as a fault. This is the repository's
existing posture rather than a new rule: the suite-manifest loader rejects any
value other than `"1.0"` through the same error path it uses for a missing or
corrupt file, and the runner request envelope answers an unrecognized version with
a named `unsupported_schema_version` error.

The directionality matters and is not decorative. The conventional rule across
Terraform, npm, and the Model Context Protocol is *reject newer, tolerate older* —
a flat "fail closed on any mismatch" would break every already-installed copy the
moment this version is bumped, which is the opposite of what a version field is
for.

**What is deliberately not specified**: any transformation between versions. No
migration is defined; a version bump requires a coordinated payload release. That
rule belongs to the first spec that reads this catalog programmatically, and is
written when a second shape actually exists — the same way this repository's
marker-plan contract widened its version set only when its second version shipped.

**Where this is enforced**: at the load and validate boundary, not by the reader.
An agent consuming this file as context does not branch on a version field, so a
rule addressed to that consumer would not execute. The obligation binds the
programmatic validator.

## Entry shape

Eight keys, no more, no fewer:

| Key | Type | Contract |
|-----|------|----------|
| `id` | string | unique; filename-safe kebab-case — lowercase alphanumerics in hyphen-separated segments, no leading/trailing/repeated hyphen, no path separator, `..`, whitespace, or dot |
| `category` | string | one of nine members |
| `title` | string | non-empty |
| `when_to_use` | string | non-empty |
| `stage` | string | `draft-pr` \| `final-pr` \| `ad-hoc` |
| `trigger` | object | `{"always": true}` or `{"any_of": [...]}` |
| `source` | object | `{"origin":"upstream","file":"..."}` or `{"origin":"repository"}`; `origin` is a closed two-member set |
| `status` | string | `planned` \| `shipped`; an artifact file exists **iff** the value is `shipped` |

### Artifact path resolution

There is **no path key**. A consumer resolves:

```
<directory containing manifest.json>/templates/<id>.html
```

Deriving rather than storing makes identifier/filename drift impossible and keeps
the catalog portable across the repository checkout and the install cache.

Because the path is **composed** from `id`, the identifier's format is what keeps
the resolution inside the gallery — an id carrying a path separator or a `..`
segment composes a path outside `templates/`, and both the existence check and the
orphan check would follow it. That is why `id` is validated for filename-safe form
rather than for equality with the file stem: with the path derived, the stem *is*
the id by construction, so the equality that earlier revisions asserted is a
tautology and can never fail.

## Routing algorithm — two ordered, independent steps

```
1. candidates = [e for e in templates if e.stage == stage_being_routed]
2. selected   = [e for e in candidates if trigger_matches(e.trigger, present_signals)]
```

```
trigger_matches({"always": true},  S) -> True
trigger_matches({"any_of": [...]}, S) -> any(sig in S for sig in any_of)
```

Consequences a consumer must honor:

- "Always applies" means **always within its own stage**, never across stages.
- `ad-hoc` entries are never in any stage's candidate set, so their triggers are
  never evaluated. They still carry a mandatory trigger so all 21 entries have
  one uniform, validated shape.
- `category` is a browsing axis. **No routing consumer reads it.**

## Signal vocabulary

`signals` is the single authority for membership. The five members carry
membership only — no descriptions — because FR-017 puts each signal's meaning and
evidence source in `SPA-CONTRACT.md`, and a name-to-description map here would
create a second editable home for the same prose.

Membership is closed in three directions, not two. Beyond the count and the
closure against entries' triggers, the vocabulary is also closed against the
per-signal documentation in `SPA-CONTRACT.md` (check C8). Without that third leg a
signal renamed in the catalog **and** its consuming trigger in one change keeps the
count at five and keeps trigger-closure intact, so it passes silently while every
routing consumer's join key moves. The documentation is the leg that cannot be
renamed without a human writing new prose.

Names are flat `snake_case`. The repository's one prior in-repo routing
vocabulary, `speckit-pro/skills/speckit-autopilot/contracts/routing-decision.schema.json`,
uses namespaced `family:value` tokens because that classifier groups signals into
families (`hard-atomic:`, `releasability:`, `change-shape:`, `context:`). This
vocabulary has five flat members and no families, so namespacing would add
structure carrying no information.

Signals are **names, not computed predicates**. ART-001 validates only that every
trigger uses a recognized form and recognized names. Deciding whether a signal
holds for a given change belongs to the emitting workflow in a later spec — which
is why no expression language, operator, or evaluator appears anywhere.

## Stability guarantees

- Entry `id` values are stable; ports never rename. This is enforced, not merely
  asserted: validation pins the seeded identifier set and compares it against the
  catalog (check B12), so a rename fails loudly rather than passing every internal
  check by renaming the derived file alongside it. The guarantee is also stated in
  the shipped contract document, because that is the only artifact a port author
  actually reads — leaving it here alone would put it somewhere no port ever opens.
  The pinned set is not the duplicate list FR-017 prohibits: that rule is scoped to a
  copy edited in the same change as the catalog, whereas this one is defeated only by
  a later spec editing a validation file outside its own declared scope. The same
  shape already exists in this repository for another shipped manifest's identifiers.
- `signals` reserves no slack. A member is added only by recorded amendment
  naming its consuming entry. Members are not renamed or removed.
- `category` reserves no slack and adds no member for repository authorship —
  origin is already carried by `source`.
- Porting a template changes exactly one value: `status`, `planned` → `shipped`
  (SC-004). No other catalog edit, and no shared-foundation edit, is permitted.

## Attribution obligation carried by `source`

`source.origin` is the discriminator that makes FR-020 mechanically checkable:

- `origin: "upstream"` → the artifact MUST carry the attribution header, and the
  upstream **file** and **repository** it names MUST equal `source.file` and the
  single repository this contract names. Presence of the required elements is not
  the same as agreement with the entry: a header naming a different upstream file
  than its own entry is well-formed and false at once, which is exactly what a
  header copy-pasted from a neighbouring artifact produces. `source.file` is
  already unique across the catalog (B11), so once the header agrees with the
  entry, each artifact's asserted provenance is unique and catalog-backed.
- `origin: "repository"` → the artifact MUST NOT carry **any** upstream
  attribution element — not merely no copyright line. Failing on the copyright
  line alone would let a repository-authored artifact carry an otherwise complete
  and convincing header and still pass.

ART-001 ships no artifact, so no header is validated yet. The rule and its
enforcement are ART-001's deliverable; ART-002…005 inherit the obligation.

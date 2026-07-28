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
`snake_case` key with the string value `"1.0"`. It earns its place because the
install cache can lag the repository, so a consumer may read an older shape than
current validation expects.

## Entry shape

Eight keys, no more, no fewer:

| Key | Type | Contract |
|-----|------|----------|
| `id` | string | kebab-case, unique, equals the artifact file stem |
| `category` | string | one of nine members |
| `title` | string | non-empty |
| `when_to_use` | string | non-empty |
| `stage` | string | `draft-pr` \| `final-pr` \| `ad-hoc` |
| `trigger` | object | `{"always": true}` or `{"any_of": [...]}` |
| `source` | object | `{"origin":"upstream","file":"..."}` or `{"origin":"repository"}` |
| `status` | string | `planned` \| `shipped` |

### Artifact path resolution

There is **no path key**. A consumer resolves:

```
<directory containing manifest.json>/templates/<id>.html
```

Deriving rather than storing makes identifier/filename drift impossible and keeps
the catalog portable across the repository checkout and the install cache.

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

- Entry `id` values are stable; ports never rename.
- `signals` reserves no slack. A member is added only by recorded amendment
  naming its consuming entry. Members are not renamed or removed.
- `category` reserves no slack and adds no member for repository authorship —
  origin is already carried by `source`.
- Porting a template changes exactly one value: `status`, `planned` → `shipped`
  (SC-004). No other catalog edit, and no shared-foundation edit, is permitted.

## Attribution obligation carried by `source`

`source.origin` is the discriminator that makes FR-020 mechanically checkable:

- `origin: "upstream"` → the artifact MUST carry the attribution header.
- `origin: "repository"` → the artifact MUST NOT carry an upstream copyright
  line.

ART-001 ships no artifact, so no header is validated yet. The rule and its
enforcement are ART-001's deliverable; ART-002…005 inherit the obligation.

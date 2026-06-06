# Contract: Namespace-aware ID normalization grammar

The grammar the shared normalizer implements and that the `spec_id` check (FR-019) uses to join a doc ID to a directory name. Owned by FR-017 / FR-018 / FR-019. Implemented once in `speckit-pro/tests/lib/moc-id-normalize.sh` and sourced by both lints + the Layer-4 unit test.

## Normalization: value -> (namespace, number-suffix)

1. **Lowercase** the value.
2. **Split** the lowercased value on `-`.
3. If the **first** dash-delimited segment is **all-alpha** (`^[a-z]+$`): `namespace` = that segment, `number-suffix` = the **next** segment.
4. Else: `namespace = "spec"`, `number-suffix` = the **first** segment.

**Totality**: the grammar yields a defined `(namespace, number-suffix)` pair for ANY input. When the selected number-suffix segment is missing or empty (an all-alpha value like `prsg`, a trailing-dash value like `prsg-`, an empty value, or a lone `-`), `number-suffix` is the empty string. An empty number-suffix can never byte-equal a well-formed directory's number-suffix, so a degenerate value never yields a false match.

## Comparison: match requires BOTH parts

- `namespace` equality (byte-equal lowercased strings), AND
- `number-suffix` equality by **exact, opaque whole-segment** comparison (byte-equal the entire segment).

**Forbidden**: sub-parsing the number-suffix into digits + trailing letters (no `[0-9]+[a-z]*` capture). The whole segment is compared as-is, so `013a1` is NOT truncated to `013a`.

## Canonical examples (these are the test fixtures)

| Input | Normalized | Notes |
|-------|------------|-------|
| `prsg-002-moc-templates` | `(prsg, 002)` | directory; alpha first segment `prsg` is the namespace |
| `PRSG-002` | `(prsg, 002)` | bare id; lowercases to `prsg`; **matches** `prsg-002-moc-templates` |
| `002-pr-checks-workflow` | `(spec, 002)` | no alpha prefix → `spec`; does NOT match `(prsg, 002)` |
| `SPEC-002` | `(spec, 002)` | alpha first segment `spec`; does NOT match `(prsg, 002)` |
| `006a-uat-skeleton` | `(spec, 006a)` | no alpha prefix; number-suffix `006a` |
| `013a` | `(spec, 013a)` | whole-segment; does NOT match `013a1` |
| `013a1` | `(spec, 013a1)` | whole-segment; does NOT match `013a` |

## Match-decision summary

- `PRSG-002` ↔ `prsg-002-moc-templates` → **MATCH** `(prsg,002)==(prsg,002)`
- `PRSG-002` ↔ `SPEC-002` → **NO MATCH** (different namespace)
- `PRSG-002` ↔ `002-pr-checks-workflow` → **NO MATCH** (different namespace)
- `013a` ↔ `013a1` → **NO MATCH** (different number-suffix segment)

## Usage in the `spec_id` check (FR-019)

For a version-gated `SPEC-MOC.md`: `normalize(frontmatter spec_id)` MUST equal `normalize(name of the containing directory)`. A mismatch is a violation. This is the check that actually validates the headline ID-join feature. Both sides are reduced with the SAME grammar before comparison (symmetric — neither side is compared raw). An ABSENT or EMPTY `spec_id` in a version-gated marker is itself a violation (a marker with no join key cannot satisfy the join), distinct from a present-but-mismatched value.

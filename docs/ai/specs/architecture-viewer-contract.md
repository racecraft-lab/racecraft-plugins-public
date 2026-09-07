# Architecture viewer data contract

Date: 2026-09-06. Status: contract and template stub only; fail-open. No
producer, no viewer page, and no autopilot reference change lands with this
record. The gallery manifest carries the entry as `planned`, which per the
single-file artifact contract means no template file exists yet and the
artifact author skips it.

This is the "Quality Gauntlet" memo's item 10. It fixes three things so the
producer and the page can be built independently:

1. The graph JSON the viewer consumes.
2. The artifact-gallery manifest entry that routes the page.
3. The touched-plus-one-hop rule for per-PR pages, with whole-repository on
   demand.

## 1. Graph JSON

Schema: `speckit_pro_runner/contracts/architecture-graph.schema.json`.
Validator: `speckit_pro_runner/architecture_graph.py` (standard library,
`python3 -m speckit_pro_runner.architecture_graph graph.json`, exit 0 or 1
with one violation per line). The validator also enforces the two rules a
schema cannot state: every edge endpoint is a node id, and a `pr`-scoped
graph holds only touched nodes and their one-hop neighbours.

```json
{
  "schema_version": "1.0",
  "scope": { "kind": "pr", "base": "origin/main", "touched": ["src/queue/api.py"] },
  "language": "python",
  "tool": "pydeps",
  "nodes": [
    { "id": "src/queue/api.py", "path": "src/queue/api.py", "touched": true,
      "delta": { "kind": "changed", "summary": "Queue.drain(limit) added to the public API" } },
    { "id": "src/queue/store.py", "path": "src/queue/store.py" }
  ],
  "edges": [
    { "from": "src/queue/api.py", "to": "src/queue/store.py" },
    { "from": "src/cli/main.py", "to": "src/queue/api.py", "valid": false, "rule": "cli-must-not-import-queue" }
  ]
}
```

- `nodes[].id` is the repository-relative module path and the single join
  key for `edges`, `scope.touched`, and the plan's Module and Interface
  Deltas.
- `nodes[].delta` carries the plan line for that module: `kind` is `new`,
  `changed`, or `removed`; `summary` is the one-line delta for callers. A
  node without a plan line has no `delta`.
- `edges[].valid` is false when the DEPENDENCY_RULES tool flagged the edge,
  with `rule` naming the violated rule or contract. The viewer draws such an
  edge red. A valid edge carries neither field.
- `tool` names the producer so a reader knows which graph shape it was
  derived from.

### Sources, per language

The graph is derived from the DEPENDENCY_RULES tool the gate tooling
decision record picked, joined with the plan's deltas. No new analysis tool.

| Language | Raw source | Mapping |
| --- | --- | --- |
| TypeScript | `depcruise --output-type json` (the same cruise the gate runs, with `--output-type json` instead of `err`) | `modules[].source` is a node; each `modules[].dependencies[]` entry is an edge `source` to `resolved`; an entry with `valid: false` copies the first `rules[].name`. `summary.violations[]` gives the same edges by `from`, `to`, and `rule.name`. `--affected <base>` or `--include-only` scopes the cruise to the PR. |
| Python | `pydeps <pkg> --no-output --show-deps` | Each key is a module; its `path` is the node path; each name in `imports` is an edge to that module's path. import-linter emits no JSON, so violations come from parsing its text report or from re-running with `--contract <id>` per touched module; until that parser exists Python edges carry no `valid` field and the page shows the rules result as a whole. |

The producer writes `specs/<feature>/artifacts/architecture-graph.json`
next to the pages, validates it with the module above, and on any failure
writes nothing. The artifact author then reports the viewer page as a gap,
which is the gallery's existing fail-open path. A missing DEPENDENCY_RULES
slot means no graph and no page, never an empty page.

## 2. Manifest entry

`speckit-pro/artifact-gallery/manifest.json` gains one entry:

| Field | Value |
| --- | --- |
| `id` | `architecture-viewer` |
| `category` | `code-review` |
| `stage` | `draft-pr` |
| `trigger` | `{"any_of": ["brownfield_change"]}` |
| `source` | `{"origin": "repository"}` |
| `status` | `planned` |
| `exports` | `["markdown"]` |

A greenfield change has no callers to show, so the page rides the existing
`brownfield_change` signal rather than a new one. The whole-repository view
is not a second entry: it is the same page with `scope.kind` set to
`repository`, selected explicitly like any ad-hoc artifact. The markdown
export is the adjacency list, one line per edge, so a reviewer can paste
the graph into a comment.

## 3. Scope rule

- **Per-PR page:** `scope.kind` is `pr`. `scope.touched` is the set of
  modules the PR changed (from `git diff --name-only <base>...HEAD`, filtered
  to the detected language, tests excluded, the same list the quality-gate
  slots use). The graph holds every touched module plus every module one
  edge away in either direction, and nothing else. The validator rejects a
  node two hops out, so a producer cannot silently ship the whole tree
  under a `pr` scope.
- **Whole repository on demand:** `scope.kind` is `repository`, no `base`,
  no `touched`, every module the tool reports. Produced only when an
  operator asks, because on a large tree it is slow and the page is not
  reviewable at a glance.
- **Both** carry `delta` on any node the plan names, so a reviewer sees the
  intended interface change beside the actual edges.

## Template stub

The page will be `speckit-pro/artifact-gallery/templates/architecture-viewer.html`
under the single-file artifact contract: one file, the canonical head and
brand blocks, the CSP the gallery test locks, a leading slot inventory,
and ordered `FILL` marker pairs. Its slot inventory, fixed now so the fill
step can be written against it:

```text
Slot: document-title | Fills: the browser title using the artifact kind, feature identifier, and feature name | Source: spec.md
Slot: feature-header | Fills: the feature identifier, its name, and the scope line (per-PR against <base>, or whole repository); keep id="feature-id" and id="feature-name" | Source: spec.md, architecture-graph.json scope
Slot: graph-data | Fills: the architecture-graph.json document inline in a <script type="application/json" id="graph-data"> element; the page reads nodes and edges from it and never fetches | Source: architecture-graph.json
Slot: delta-list | Fills: one row per node with a delta: module, kind, summary; keep id="delta-list" because the markdown export reads it | Source: plan.md Module and Interface Deltas via the graph
Slot: violation-list | Fills: one row per edge with valid=false: from, to, rule; keep id="violation-list"; empty state text "No rule violations on the touched modules" | Source: architecture-graph.json
```

Rendering is the page's own concern: an inline layout of touched nodes in
the centre and one-hop neighbours around them, no external script or
stylesheet, per the CSP. The template lands when the producer exists; then
the manifest row's status flips to `shipped` and nothing else in the row
changes.

## Unverified

- Whether `depcruise --affected <base>` returns exactly the touched set plus
  dependents, or dependents only; the producer must add the touched
  modules' own dependencies to reach one hop in both directions.
- pydeps' handling of namespace packages and `src/` layouts; an `ast` walk
  of `Import` and `ImportFrom` is the fallback the gate tooling record
  already names.

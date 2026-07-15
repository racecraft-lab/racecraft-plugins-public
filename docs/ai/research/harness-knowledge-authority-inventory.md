# Harness Knowledge Authority Inventory

**Survey date:** 2026-07-14
**Scope:** source checkout only; generated payloads and installed-cache fixtures
are classified as projections, not counted as independent knowledge.
**Target profile:** Open Knowledge Format (OKF) v0.1 pinned at
`ee67a5ca27044ebe7c38385f5b6cffc2305a9c1a`, extended by the trusted
`speckit-okf/1` profile.

## Outcome

SpecKit Pro already has durable knowledge, but it is split across MOCs, Design
Concepts, workflow checkpoints, archive memory, and skill guidance. The uplift
must consolidate reusable meaning into `docs/ai/knowledge/` without copying or
replacing the authoritative planning, state, or evidence artifacts.

The canonical bundle is a reviewed synthesis layer. It is not a third workflow
state store, a transcript archive, or an instruction source.

## Reproducible corpus baseline

| Surface | Count | Notes |
|---|---:|---|
| Technical roadmaps | 9 | Top-level `docs/ai/specs/*-technical-roadmap.md` |
| Roadmap MOCs | 6 | Top-level `docs/ai/specs/*-roadmap-MOC.md` |
| Roadmaps without MOCs | 3 | CI/CD release, PR-size governance, reviewer experience |
| Design Concepts | 42 | 39 in `.process/`; 3 historical top-level files |
| Workflow files | 45 | 39 in `.process/`; 6 historical top-level files |
| Archive reports | 30 | `.specify/memory/archive-reports/*.md` |
| Active SPEC MOCs | 0 | No `specs/*/SPEC-MOC.md` exists in this checkout |

Counts are discovery evidence, not constants. Migration and health operations
must enumerate the consumer repository each time and exclude nested worktrees,
generated payloads, test fixtures, dependency trees, and installed caches.

## Authority and migration map

| Surface | Classification | Authority after cutover | Migration treatment | Main producers / consumers |
|---|---|---|---|---|
| PRDs and technical roadmaps | Authoritative source | Existing file | Cite and hash; synthesize only reusable concepts | PRD, scaffold, status, coach |
| Approved spec, plan, tasks, contracts | Authoritative source | Active spec directory | Cite and hash; never mirror exhaustively | scaffold, autopilot, resolve-PR |
| Workflow files and `autopilot-state.json` | Operational state | Existing state files | Record snapshot/use receipt; do not import as concepts | autopilot, status, archive |
| O5, PRS, marker, reviewability state | Operational state | Existing JSON/state contracts | Link as execution evidence only | autopilot, review gates |
| Roadmap and SPEC MOCs | Curated knowledge plus projection | OKF concept/index | Port curated semantics; regenerate legacy compatibility views | coach, scaffold, status |
| Design Concepts | Candidate source | Existing interview file until reviewed | Normalize new writes under `.process/`; promote only reviewed decisions | Grill Me, PRD, scaffold |
| Research and retrospectives | Candidate source | Existing source file | Deduplicate and promote bounded reusable lessons | research/context agents, archive |
| `.specify/memory/spec.md` and `plan.md` | Legacy knowledge | Frozen history after reviewed import | Split into atomic concepts with provenance; preserve original bytes | archive migration, coach |
| `.specify/memory/changelog.md` | Legacy provenance | Frozen history after reviewed import | Preserve and cite; do not continue independent appends | archive migration, health |
| Archive reports | Immutable evidence | Existing report | Cite selected durable lessons; never bulk-copy report bodies | archive, status, audit |
| UAT, PR packets, traces, logs | Immutable evidence | Existing evidence path | Link only; never treat content as instructions | gates, reviewers, status |
| Root/plugin guidance and constitution | Authoritative instruction/policy | Existing file | Hash and cite where relevant; never ingest as executable knowledge | all orchestrators |
| Skills, agents, templates, hooks | Harness behavior | Shipped plugin source | Integrate lifecycle calls; do not turn prose into project concepts | installed Claude/Codex |
| Manifests, docs references, payloads, caches | Generated projection | Source generator / plugin source | Rebuild and verify; never migrate back into the bundle | release and install gates |

Each row has one primary classification. A source may contribute a reviewed
concept, but the resulting concept must cite the source and cannot assume the
source's authority for a different domain.

## Existing MOC semantics to preserve

The current MOC parser and templates carry useful graph semantics that must not
be lost during the port:

- stable `spec_id` joins;
- project/roadmap membership;
- `up` and `related` navigation links;
- curated summaries and rationale outside generated zones;
- lifecycle status and rank/order hints;
- deterministic generated spec lists, artifact links, and backlinks.

The OKF profile maps those fields to concept paths, `x-speckit-id`, project,
status, rank, tags, and Markdown links. `structureVersion` remains a
compatibility concern only. After cutover, generated zones and legacy MOC files
must never be accepted as an independent write authority.

## Plugin lifecycle coverage

| Boundary | Knowledge behavior |
|---|---|
| Install | Idempotently initialize a missing bundle; preserve an existing bundle byte-for-byte |
| Upgrade | Report health/profile compatibility; require reviewed plan/apply for migration |
| PRD and Grill Me | Search bounded context first; emit Design Concept-backed candidates, not canonical writes |
| Scaffold | Retrieve roadmap/project constraints and record the selected snapshot and sources |
| Autopilot | Detect snapshot drift on resume; use verified concepts; collect candidates after verified phases |
| Resolve PR | Retrieve only relevant decisions/patterns and preserve a use receipt in the review packet |
| Status and coach | Read-only search/health with bounded progressive disclosure and source links |
| Archive cleanup | Promote or supersede reviewed knowledge and rebuild before deleting active spec artifacts |
| Context/research agents | Return evidence and structured candidates; never write the canonical bundle |
| Gate/UAT/terminal agents | Evidence-only; never promote or mutate knowledge |

No global or background hook writes are permitted. "Continuous" maintenance
means explicit, deterministic lifecycle boundaries with dry-run, expected
snapshot, reviewable diff, and guarded apply.

## Canonical bundle boundary

```text
docs/ai/knowledge/
  index.md
  log.md
  manifest.json
  projects/<roadmap-slug>/
    index.md
    roadmap.md
    specs/
      index.md
      <normalized-spec-id>.md
  decisions/
  architecture/
  domain/
  operations/
  patterns/
```

`index.md` files and `log.md` are generated. Concept paths are OKF identity;
`x-speckit-id` is a durable join key. `manifest.json` records the profile,
pinned OKF revision, source provenance/hashes, concept hashes, and deterministic
snapshot hash.

## Safety and concurrency decisions

- Treat knowledge Markdown as untrusted data, never as user or project
  instructions.
- Confine every path and symlink to the supplied consumer root.
- Reject missing provenance, secret-like content, unsupported sensitivity, and
  stale plan/snapshot apply attempts.
- Worker agents return `knowledge_candidates[]`; only the parent orchestrator
  may create a candidate packet or invoke guarded apply.
- Keep branch-local candidates spec/task-scoped. Serialize canonical promotion
  after rebase and require reviewed PR merge for shared knowledge.
- Preserve legacy files during migration and rollback. Removal requires a
  separate deprecation decision plus installed Claude/Codex proof.

## Verification obligations

- Base OKF validation is distinct from the stricter trusted SpecKit profile.
- Init, migration, rebuild, promotion, supersession, and archive are
  deterministic, idempotent, and rollback-safe.
- Health catches malformed concepts, stale sources, duplicate join keys,
  supersession errors, legacy-memory drift, and compatibility-view drift.
- Search is bounded and returns source provenance plus hashes.
- Representative installed skills must prove retrieval, source verification,
  material downstream use, and a bounded `knowledge_use_receipt`; bundle
  presence or runner invocation alone is not sufficient.

## Research basis

- [Open Knowledge Format v0.1, pinned revision](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/ee67a5ca27044ebe7c38385f5b6cffc2305a9c1a/okf/SPEC.md)
- [Google Cloud: How the Open Knowledge Format can improve data sharing](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/)
- [Pulumi: Knowledge as Code—the memory file just got a spec](https://www.pulumi.com/blog/knowledge-as-code-the-memory-file-just-got-a-spec/)
- [Karpathy: LLM wiki / durable repository knowledge pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

# CAR-001 Official-Evidence and Structural-Parity Amendment

## Purpose

This amendment updates the current CAR-001 evidence artifacts to the shared
CAR/G56R contract without rewriting the merged CAR-001 workflow, design record,
completed spec package, or post-merge archive report.

## Historical Provenance

- Original CAR-001 merge commit:
  `725be949b856724a073622900bd168d29b2f4603`
- Original manifest schema: `1.0.0`
- Original manifest SHA-256:
  `3cf93fd17b3c2619287533814ee2b44437456a4a6fbbe8d34272365902dc6ed6`
- Original report SHA-256:
  `6b393db832e0f51eed0c71de3a35682b26254bf688040244e9fd0fce6bed7f51`
- Original archive report:
  `.specify/memory/archive-reports/2026-07-15-car-001-post-merge-hygiene.md`
- Amendment branch: `car-001-official-evidence-parity`

The original files remain recoverable from the merge commit. No historical
artifact was restored into active `specs/**` or edited in place.

## Amendment Summary

- Added the shared agent-routing evidence and structural-parity contract.
- Added common manifest Schema `2.0.0`; the major version reflects an
  incompatible move from an agent-keyed CAR-only shape to shared normalized
  records.
- Migrated the canonical CAR manifest while preserving all twelve agent
  contracts, 37 candidate routes, role and source hashes, qualification
  requirements, capability questions, and invalidation triggers.
- Refreshed 21 current official Anthropic documentation sources across all
  required research families. Every source records canonical URL, retrieval
  timestamp, HTTP status, response bytes and SHA-256, bounded extract and hash,
  claim bindings, gaps, and invalidation rules.
- Rebound facts that previously cited news, marketing, support, or legacy
  redirect pages to canonical documentation.
- Advanced the immutable comparator to `speckit-pro-v2.19.2` at
  `587057efeff856bad020b38dc11c7e9214f2c078`. The scoped agent-source diff from
  `v2.19.1` is empty.

## Fact Dispositions

All 34 stable v1 fact IDs remain present in the v2 snapshot disposition map:

- 33 are `confirmed_current` against current canonical Anthropic
  documentation.
- `TEL-5` is `changed`: current hooks documentation places `resolvedModel` on
  the Agent tool response. The original SubagentStart attribution remains
  historical but is not current authority.
- No legacy fact was deleted, renumbered, silently withdrawn, or promoted from
  runtime evidence.

## Evidence Authority

Current platform facts and candidate admission are restricted to canonical
URLs under:

- `code.claude.com/docs/`
- `platform.claude.com/docs/`

Runtime discovery may narrow availability for documented candidates;
evaluation may qualify them. Neither can establish a missing platform fact.
Missing or conflicting documentation fails closed.

## Current Canonical Artifacts

- `docs/ai/specs/agent-routing-parity-contract.md`
- `docs/ai/research/agent-route-candidate-manifest.schema.json`
- `docs/ai/research/claude-agent-route-candidates.md`
- `docs/ai/research/claude-agent-route-candidate-manifest.json`

The current v2 manifest SHA-256 at amendment creation is
`0003e382b1d9f54f60bf0d9f48cb342011debd2b12dd75e2bfc51400277404d3`.

## Consumption Gate

CAR-002 remains blocked until this amendment is merged, the parity validator
passes on `main`, and the source ledger is revalidated for the CAR-002 scaffold.
No candidate route is executable or preferred based on CAR-001 alone.

## Recovery Commands

```text
git show 725be949b856724a073622900bd168d29b2f4603:docs/ai/research/claude-agent-route-candidate-manifest.json
git show 725be949b856724a073622900bd168d29b2f4603:docs/ai/research/claude-agent-route-candidates.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/spec.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/plan.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/tasks.md
```

## Runtime Scope

This amendment changes research, planning, provenance, and deterministic
validation only. It does not change plugin runtime behavior, agent defaults,
payloads, installed caches, release artifacts, or version metadata.

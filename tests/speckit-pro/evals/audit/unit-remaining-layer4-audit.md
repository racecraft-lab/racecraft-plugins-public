# Remaining Layer 4 Audit — 200-Family Stable Slice

> Status: **bounded complete**. This is a substantive audit of 200 frozen Layer 4 families, not full Layer 4 or live-provider qualification.

## Result

- **Disposition:** keep 200; merge 0; replace 0; remove 0.
- **Focused execution:** all 19 selected files passed.
- **Negative controls:** 7/7 targeted in-memory faults were detected.
- **Source integrity:** all selected files match their frozen inventory hashes.
- **Remainder:** 262 frozen Layer 4 families.

## Exact accounting

| Population | Families |
|---|---:|
| Frozen Layer 4 inventory | 1,615 |
| Prior six substantive ledgers | 961 |
| Whole mutation-helper ledger | 192 |
| Unreviewed before this slice | 462 |
| This disjoint slice | 200 |
| Unreviewed after this slice | **262** |

The intersection with all seven earlier ledgers is zero. Counts are loaded
unittest methods; house-counted checks and generated subtests are not
substituted for families.

## Selected files

| File | Families | Frozen/current SHA-256 |
|---|---:|---|
| `tests/speckit-pro/test-run-all.py` | 22 | `45fb9305b8780df5c0d296787378dc2cf9c78076fab0a9bef82f23253edab618` |
| `tests/speckit-pro/unit/test-autopilot-phase-coverage.py` | 39 | `d084455fbd51b28b80e3e1c2aa44c2d90aa3750434417799c6e7499d53633d4f` |
| `tests/speckit-pro/unit/test-check-toolchain.py` | 1 | `918c5bd443b955e16d9cc5d1c5500acc3197b462a7a550fa052eb2ab4c90ff12` |
| `tests/speckit-pro/unit/test-post-implementation-reference.py` | 1 | `bd4051c6ec75c9ed26578c6405d2b13b2a47cb432a51f559a93db178f6130b55` |
| `tests/speckit-pro/unit/test-reviewability-marker-guidance.py` | 5 | `762d3d8cf3089843a6d0842967ddf310f546f8df8469c8d640b44ad78cb959f4` |
| `tests/speckit-pro/unit/test-native-eval-pool.py` | 11 | `00f32dcff8b011ee1e5761d9d43d769fbb375f98097242bd931cd102d73dd09b` |
| `tests/speckit-pro/unit/test-native-eval-judge.py` | 7 | `5374dbb8824ea62a10a8d5c2b143e5fb0e15a33d244db03e171fd7d28a1e0229` |
| `tests/speckit-pro/unit/test-ubiquitous-language-lint.py` | 1 | `df43384a37174e4edd87a37468306f7b0481cc31b9d734f6f9a5fa5af08f00cf` |
| `tests/speckit-pro/unit/test-generate-spec-index.py` | 20 | `63c7e5d1160328dbb00556cc6b4cbc1c2335f4e415dc510e3fdc9fe4427a659c` |
| `tests/speckit-pro/unit/test-agent-materialization.py` | 12 | `4cba3aada729c2d1a0ace2494cc9b9cf6bd2f356f5c4c043bf4324c29ee1bbc0` |
| `tests/speckit-pro/unit/test-moc-lint-exit-codes.py` | 1 | `8691b03fd7818ef717d4f7a4d27bf4fc5b0efd11da8ee8d40e8fc248595dfb02` |
| `tests/speckit-pro/unit/test-artifact-gallery.py` | 5 | `d6f44bd02f94bb96f457d2f2e5cd3a60df2990e1c39f407c4a5e207e75c58e85` |
| `tests/speckit-pro/unit/test-artifact-review.py` | 28 | `36780eb534bfb85368ba34a5aaee1b7f29e4dcc161257a5ecbd9d73052b6fd5f` |
| `tests/speckit-pro/unit/test-architecture-graph.py` | 1 | `b18a401854a1d5758cc3d60531fe88e7fc08846f84d60e6c2380b6e98b6eb8f3` |
| `tests/speckit-pro/unit/test-artifact-fill-regions.py` | 4 | `ff6348081384f71baa068fb21d05bf347e67c3585674a21408bcec0e7251b44e` |
| `tests/speckit-pro/unit/test-implementation-notes-record.py` | 3 | `bdfbde4966cc322fd15d6ae51e303715269109630dc5f94d47eea9b5a2f599a1` |
| `tests/speckit-pro/unit/test-consensus-analyst-shared-prose.py` | 9 | `a76b728779e8bf1c02d89743ba52e5d158ce6b2920ed83f6ed7c9f19f6228f18` |
| `tests/speckit-pro/unit/test-feedback-sweep-parse.py` | 22 | `9e1dfab74979566f93f621459b92cf398465f117ebd74da4b8dea47d2313b1ca` |
| `tests/speckit-pro/unit/test-artifact-freshness.py` | 8 | `ae1db628295578b2e0a190ba52824bec51355ff72113d1cd336608551650afee` |

## Focused execution

All selected files passed their direct Python entry point. The observed results
ranged from 7 loaded unittest methods in the judge contract suite to 360/360
house-counted checks in the feedback-sweep parser suite. The exact command and
result for every file are frozen in the JSON ledger.

No selected failure was attributable to stale generated hashes. That statement
does not cover excluded or concurrently edited files.

## Targeted fault injections

The audit injected and detected these seven faults in memory without editing
repository sources:

1. An empty runner layer falsely reported success.
2. Judge-response validation accepted every reply.
3. Artifact filling returned the original unfilled template.
4. Artifact review accepted an invalid observation.
5. Feedback-sweep parsing accepted a malformed envelope.
6. One consensus analyst grounding note diverged.
7. Spec-index target-chain validation admitted an unsafe target.

The combined injection harness detected the first six, then hit an audit-harness
setup error because the spec-index helper was referenced through the wrong
namespace. A corrected isolated rerun injected the seventh fault and the suite
rejected it. The setup error is not a product failure.

## Substantive review

- Every exact body was reconciled to its frozen requirement, assertion route,
  and focused result.
- Exact normalized-AST comparison found no duplicate body. No loaded body was
  empty or pass-only.
- Cases without direct assertion calls route through named, same-file assertion
  helpers recorded in the JSON ledger.
- Direct inspection covered fail-closed runner dispatch, malformed workflow
  state, pool bounds, strict judge validation, unsafe index targets, invalid
  artifact observations, malformed sweep envelopes, and template fill markers.
- The JSON ledger records every exact family ID, body hash, line, requirement,
  coverage type, evidence, disposition, and replacement field.

## Evidence boundary

Mocks, fake launchers, synthetic observations, temporary repositories, and
local filesystem fixtures prove only their unit or harness contracts. They do
**not** prove provider behavior, live agent behavior, semantic-judge
sensitivity, client installation, human visual acceptance, or complete Layer 4
qualification.

The frozen inventory marks one selected family with a platform-conditional
skip decorator: the descriptor-relative directory-swap defense. Its condition
was available in this focused run, so the family executed and passed rather
than being credited while skipped. Three additional static `skipTest` call
sites are environment-fallback branches; no selected focused suite reported a
runtime skip.

Seven selected names contain `preview`, all in the artifact-review state
machine. They assert preview invalidation, preservation, and resume behavior;
they are not dry-run-only substitutes for file evidence. This audit does not
turn those unit-state assertions into a claim that rendered artifacts were
visually accepted.

## Narrow remediation candidate

No reviewed family needs replacement on the available evidence. A separate
audit-maintenance change could add a read-only integrity validator for duplicate
family IDs, IDs absent from the frozen inventory, and source-hash mismatches
across ledgers. That would protect audit accounting; it would not replace live
qualification.

## Remaining scope

The 262-family remainder includes deliberately excluded native-eval files whose
current bodies drift from the frozen snapshot and belong to another active
architecture lane, plus other unselected files. They require separate,
non-overlapping review.

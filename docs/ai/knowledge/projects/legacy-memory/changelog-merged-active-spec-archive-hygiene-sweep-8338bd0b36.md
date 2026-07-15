---
type: "speckit-legacy-memory-record"
title: "Merged Active-Spec Archive Hygiene Sweep"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-8338bd0b366f3d40"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Merged Active-Spec Archive Hygiene Sweep

[Source: .specify/memory/archive-reports/2026-06-13-merged-specs-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-13
- **Cleanup branch**: `codex/archive-merged-specs-hygiene`
- **Cleanup command**: `git rm -r specs/001-repository-foundation specs/002-pr-checks-workflow specs/003-release-automation specs/004-integration-verification specs/006a-uat-skeleton specs/prsg-002-moc-templates specs/prsg-003-spec-index specs/prsg-004-roadmap-moc-home-note specs/prsg-006-reviewability-budget specs/prsg-012-reviewer-ready-pr-packet-contract`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/001-repository-foundation`, `specs/002-pr-checks-workflow`, `specs/003-release-automation`, `specs/004-integration-verification`, `specs/006a-uat-skeleton`, `specs/prsg-002-moc-templates`, `specs/prsg-003-spec-index`, `specs/prsg-004-roadmap-moc-home-note`, `specs/prsg-006-reviewability-budget`, `specs/prsg-012-reviewer-ready-pr-packet-contract`

### Provenance

| Spec | PR | Merge commit | Tree reference | Task completion |
|------|----|--------------|----------------|-----------------|
| `specs/001-repository-foundation` | #1 | `b10d40f0d5c54ccc4a3d29ebe776a1bd74bae4c2` | `0bc6ef47bf24f37f63a8a3effec2b533ca93c2ef` | 30 / 30 |
| `specs/002-pr-checks-workflow` | #2 | `030c47a6ae7f032d96a158883b4b6bfde2f5ef19` | `2143519cda2908838e8e1b3f5689b4233c9eccea` | 16 / 16 |
| `specs/003-release-automation` | #3 | `5a52abebf05941eca0905e2ba61b0b9e66b374c1` | `2468efe7e9d400080acdf38fb4fd1af62b40322e` | 11 / 11 |
| `specs/004-integration-verification` | #5 | `c11d9291a13b984cfca467a3418ac482e566c49b` | `acd61703cfd47e129c43d7895a848cf11e36623b` | 0 / 31 recorded; merged PR is authoritative |
| `specs/006a-uat-skeleton` | #99 | `dcd1208a57780abbb9c9d204b3c096be3a7da188` | `df5f8a07aae0005185f82e557994e592edd3872d` | 28 / 28 |
| `specs/prsg-002-moc-templates` | #116 | `3e4be3e9901c466040809a211af8aa0ec0c6935b` | `c6cc7c63dabce308d1a15552872ca7958564f25d` | 24 / 24 |
| `specs/prsg-003-spec-index` | #121 | `339fbaadc299f3593392937cf563b33e5d44627a` | `6cbdf0e7279c39641d9249524cb209a44d41e2df` | 25 / 25 |
| `specs/prsg-004-roadmap-moc-home-note` | #129 | `60018313eb768b8339cf60737e9b9965cc9465b8` | `1bf3942b2c88fdb959cf6c54001b82c1c402feef` | 23 / 24; remaining PR packet task was not a merge blocker |
| `specs/prsg-006-reviewability-budget` | #119 | `9d4b94867d2ad9e47a3b64b7551fa6d86ce8cf53` | `8f0058ff12832c0c08529cdf97295eba20cd9954` | 35 / 35 |
| `specs/prsg-012-reviewer-ready-pr-packet-contract` | #164-#168 | `896ab42f443e330d095f1c08be681cc8c9bca995` | `4c50790bf3009149c07eeba92771f5b2a501995d` | 56 / 56 |

### PRSG-012 PR Stack

| PR | Merge commit | Scope |
|----|--------------|-------|
| #164 | `b57e2992b8e304b0e649398b86f7b495aada3252` | Add reviewer packet validation contract |
| #165 | `7580f08fc78877f21a71c72ff4a6a2781c9017ce` | Generate packet-owned conventional PR titles |
| #166 | `d6685c44ae706370ec91977831d3d1149c299b65` | Render plain-English reviewer PR body evidence |
| #167 | `302d73a884d7fbe10964839f17460aec91f04dc1` | Block invalid PR packets before creation |
| #168 | `896ab42f443e330d095f1c08be681cc8c9bca995` | Protect editable PR body prose |

### Recovery Commands

```text
git checkout b10d40f0d5c54ccc4a3d29ebe776a1bd74bae4c2 -- specs/001-repository-foundation
git checkout 030c47a6ae7f032d96a158883b4b6bfde2f5ef19 -- specs/002-pr-checks-workflow
git checkout 5a52abebf05941eca0905e2ba61b0b9e66b374c1 -- specs/003-release-automation
git checkout c11d9291a13b984cfca467a3418ac482e566c49b -- specs/004-integration-verification
git checkout dcd1208a57780abbb9c9d204b3c096be3a7da188 -- specs/006a-uat-skeleton
git checkout 3e4be3e9901c466040809a211af8aa0ec0c6935b -- specs/prsg-002-moc-templates
git checkout 339fbaadc299f3593392937cf563b33e5d44627a -- specs/prsg-003-spec-index
git checkout 60018313eb768b8339cf60737e9b9965cc9465b8 -- specs/prsg-004-roadmap-moc-home-note
git checkout 9d4b94867d2ad9e47a3b64b7551fa6d86ce8cf53 -- specs/prsg-006-reviewability-budget
git checkout 896ab42f443e330d095f1c08be681cc8c9bca995 -- specs/prsg-012-reviewer-ready-pr-packet-contract
```

The detailed per-file `git show` recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-13-merged-specs-post-merge-hygiene.md`.

### Fixture Decoupling

- PRSG-012 PR body generation now reads a committed feature fixture under
  `tests/speckit-pro/unit/fixtures/pr-packet-feature/`.
- PRSG-012 marker-emission regression now reads committed marker-plan fixtures
  under `tests/speckit-pro/unit/fixtures/marker-plan/`.
- MOC orphan/stale-index lints now use committed MOC fixtures for former
  PRSG-002 dogfood assertions.

### Verification

- Pre-cleanup focused tests passed: `test-generate-pr-body.sh` `85/85`,
  `test-multi-pr-emission.sh` `156/156`, MOC stale-index `11/11`, MOC orphan
  `29/29`.
- Post-cleanup `bash tests/speckit-pro/run-all.sh` passed `2915/2915`
  (Layer 1 structural `549/549`, Codex structural `430/430`, Layer 4 script
  unit `1746/1746`, Layer 5 tool scoping `190/190`).

---

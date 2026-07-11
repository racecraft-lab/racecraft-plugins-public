# XPLAT-010 PR Stack Review Guide

<!-- speckit-pro-review-packet-source: docs/ai/specs/.process/XPLAT-010-pr-packet.json -->

## Summary

XPLAT-010 is published as 18 dependent pull requests, #311 through #328. A live
GitHub query at `2026-07-11T05:42:15Z` confirmed all 18 are open and non-draft.
The packet set was reconciled at `2026-07-11T05:40:56Z`; every adjacent packet
validation reports `passed`, with none blocked.

The stack replaces repository-owned Bash test and helper execution with the
Python 3.11+ runner, confines the remaining vendored and workflow Bash surface,
adds hosted Linux/Windows preflight contracts, and adds deterministic release
note validation and composition.

## Snapshot Semantics

- Implementation snapshot: PR #328's frozen adjacent implementation head is
  `a7b2d27b12fdc5051dfa4829c94f92752e2f5146`, with tree
  `a1c42735d35619bbd0a4a90a42c57ab9e578848e`.
- Metadata publication: no publication head is asserted here. A later bounded
  metadata-only commit may advance the live top branch; the finalizer must
  resolve that future head through
  `specs/xplat-010-repository-bash-confinement/.process/publication-tail.json`.
  The 18 packet boundaries remain frozen to their implementation snapshots.

## Review Order

| Order | PR | Slice | Purpose | Base slice | Implementation snapshot | Artifacts |
|---:|---|---|---|---|---|---|
| 1 | [#311](https://github.com/racecraft-lab/racecraft-plugins-public/pull/311) | `00-process` | Record confinement design and process evidence | `main` | `da15f705d9` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/00-process/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/00-process/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/00-process/validation.json) |
| 2 | [#312](https://github.com/racecraft-lab/racecraft-plugins-public/pull/312) | `01-foundation` | Remove orphaned Bash test scripts | `00-process` | `1304d5a1fd` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/01-foundation/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/01-foundation/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/01-foundation/validation.json) |
| 3 | [#313](https://github.com/racecraft-lab/racecraft-plugins-public/pull/313) | `02-us14` | Restore spec-size estimation | `01-foundation` | `c2d3b0c7bd` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/02-us14/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/02-us14/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/02-us14/validation.json) |
| 4 | [#314](https://github.com/racecraft-lab/racecraft-plugins-public/pull/314) | `03-us1` | Replace Bash suite orchestration with Python | `02-us14` | `9f9684fa6f` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/03-us1/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/03-us1/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/03-us1/validation.json) |
| 5 | [#315](https://github.com/racecraft-lab/racecraft-plugins-public/pull/315) | `04-us2` | Port structural validator batch one | `03-us1` | `7d6a6d115b` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/04-us2/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/04-us2/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/04-us2/validation.json) |
| 6 | [#316](https://github.com/racecraft-lab/racecraft-plugins-public/pull/316) | `05-us3` | Port structural validator batch two | `04-us2` | `9b249ddd0e` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/05-us3/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/05-us3/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/05-us3/validation.json) |
| 7 | [#317](https://github.com/racecraft-lab/racecraft-plugins-public/pull/317) | `06-us4` | Port remaining structural checks | `05-us3` | `cf352fbc35` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/06-us4/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/06-us4/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/06-us4/validation.json) |
| 8 | [#318](https://github.com/racecraft-lab/racecraft-plugins-public/pull/318) | `07-us5` | Port toolchain and Layer 5 dispatch | `06-us4` | `c1d5e51c8a` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/07-us5/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/07-us5/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/07-us5/validation.json) |
| 9 | [#319](https://github.com/racecraft-lab/racecraft-plugins-public/pull/319) | `08-us6` | Port repository helpers and hooks | `07-us5` | `790b9e230d` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/08-us6/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/08-us6/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/08-us6/validation.json) |
| 10 | [#320](https://github.com/racecraft-lab/racecraft-plugins-public/pull/320) | `09-us7` | Port transcript helpers and tools | `08-us6` | `7584c468cb` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/09-us7/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/09-us7/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/09-us7/validation.json) |
| 11 | [#321](https://github.com/racecraft-lab/racecraft-plugins-public/pull/321) | `10-us7b` | Port Layer 7 replay runners | `09-us7` | `511746913f` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/10-us7b/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/10-us7b/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/10-us7b/validation.json) |
| 12 | [#322](https://github.com/racecraft-lab/racecraft-plugins-public/pull/322) | `11-us8` | Port Layer 8 parity harness | `10-us7b` | `15fac7807d` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/11-us8/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/11-us8/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/11-us8/validation.json) |
| 13 | [#323](https://github.com/racecraft-lab/racecraft-plugins-public/pull/323) | `12-us9` | Port live evaluation runners | `11-us8` | `3348aa4fbb` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/12-us9/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/12-us9/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/12-us9/validation.json) |
| 14 | [#324](https://github.com/racecraft-lab/racecraft-plugins-public/pull/324) | `13-us10` | Enforce repository Bash confinement | `12-us9` | `93aaddd09d` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/13-us10/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/13-us10/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/13-us10/validation.json) |
| 15 | [#325](https://github.com/racecraft-lab/racecraft-plugins-public/pull/325) | `14-us11` | Add Linux and Windows runner checks | `13-us10` | `c6b47a6d85` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/14-us11/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/14-us11/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/14-us11/validation.json) |
| 16 | [#326](https://github.com/racecraft-lab/racecraft-plugins-public/pull/326) | `15-release-contract` | Validate consumer release-note blocks | `14-us11` | `b3c81e25fa` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/15-release-contract/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/15-release-contract/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/15-release-contract/validation.json) |
| 17 | [#327](https://github.com/racecraft-lab/racecraft-plugins-public/pull/327) | `16-release-composition` | Compose consumer-facing release highlights | `15-release-contract` | `b5ab3cac69` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/16-release-composition/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/16-release-composition/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/16-release-composition/validation.json) |
| 18 | [#328](https://github.com/racecraft-lab/racecraft-plugins-public/pull/328) | `17-polish` | Finalize integrated verification evidence | `16-release-composition` | `a7b2d27b12` | [packet](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/17-polish/packet.json) · [body](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/17-polish/body.md) · [validation](../../../../specs/xplat-010-repository-bash-confinement/.process/pr-packets/17-polish/validation.json) |

## Verification

- 18 of 18 packet validations report `passed`; none is blocked. Live GitHub
  state confirms 18 open and 0 draft pull requests.
- The 18 contiguous adjacent ranges contain 101 commits and 0 merge commits.
- Their per-slice metric sums are 2,101 changed-path observations, 149,201
  insertions, 132,605 deletions, 54 production-file observations, and 5,635
  reviewable LOC. Path and production-file values are observations, not unique
  full-stack counts.
- Reviewability results are 13 `within_budget`, 2 `exception`, and 3 `warning`.

## Known Gaps

- `T108` remains open. Hosted pull-request checks cover only the pre-merge path.
  After the workflow exists on `main`, an operator must run `workflow_dispatch`
  and record Linux, advisory Windows, ARM64-disabled, sentinel, and artifact
  results.
- `T117` remains open. Branch protection does not currently require
  `validate-release-note`; after the workflow lands, a repository administrator
  must add that exact check and record the resulting configuration evidence.
- No packet or this aggregate guide claims a merge, release publication,
  post-merge dispatch, or completion of hosted-only acceptance.

## Rollback

Reverse the stack from #328 toward #311, one adjacent slice at a time. Do not
restore deleted Bash runtime paths without also reverting their Python
replacement, manifest registration, parity evidence, generated proof, and
confinement contract.

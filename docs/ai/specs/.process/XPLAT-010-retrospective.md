# XPLAT-010 Retrospective

## Outcome

XPLAT-010 produced an 18-PR linear stack, #311 through #328. The generated
packet/body/validation triplets cover every adjacent branch boundary and all 18
validations report `passed`. Its frozen implementation head is
`a7b2d27b12fdc5051dfa4829c94f92752e2f5146`, with tree
`a1c42735d35619bbd0a4a90a42c57ab9e578848e`. The final neutral-PATH deterministic
suite passed 2512/2512 checks (Layer 1 1373, Layer 4 953, Layer 5 186). The
stack remains open; this retrospective does not claim merge, release
publication, branch-protection configuration, or completion of hosted-only
acceptance.

## What Worked

- The work split safely across isolated worktrees and refs for CI diagnosis,
  lower-stack repairs, upper-stack reconstruction, review-thread auditing, and
  closeout analysis. Shared branch heads, generated release artifacts, state
  files, and force-push order remained serialized at integration points.
- Rebuilding from fixed marker checkpoints made the 18 adjacent diffs explicit.
  Packet validation then proved topology, actual Git diff metrics, task mapping,
  and rollback scope independently for each PR.
- Canonical artifact regeneration was treated as part of every shipped-runner or
  release-contract boundary, with a second run used to prove idempotence.
- The Windows helper's actual execution path was kept direct and portable:
  Windows dispatches to the Python module, which iterates privacy-safe fixtures.
  The completed local helper evidence is 33/33, and the final source-head
  Windows x64 advisory jobs passed. Windows ARM64 remained deliberately disabled;
  neither result substitutes for the post-merge evidence still required by T108.

## What Needed Correction

- The first repaired lower stack carried one shared CI failure from #314 through
  #324. #314 expected `source_payload_tree_hash` in a partial-root diagnostic
  after #313 had refreshed that hash, so the actual categories were only
  `installed_root` and `source_payload_root`. Fixing the earliest affected layer
  and restacking its dependents removed the duplicated failure family.
- Generated proof drift recurred when source changes and release metadata moved
  without the matching payload/proof refresh. #326 exposed both missing generated
  artifacts and two runtime-sensitive wording findings. The repair sequence was
  source-first replay, runtime-neutral wording, canonical refresh, proof-hash
  refresh, and idempotence verification before replaying later layers.
- Purpose-based renames had a wider blast radius than directory moves alone.
  `tests/speckit-pro/layer4-scripts` became `tests/speckit-pro/unit`,
  `parity/xplat-010` became `parity/bash-to-python`, and the XPLAT-009 fixture
  root became `plugin-bash-confinement`. Embedded fixture IDs, packet inventories,
  generated references, and layout assertions also had to change. A stronger
  layout test now catches opaque spec-coded IDs as well as legacy paths.
- The clean-head Linux ARM64 exact pinned-container overlay initially failed
  because the publication tail did not hydrate `tasks.md`. Hydrating publication
  tasks fixed that planner path and the overlay passed 42/42; this is local
  clean-head evidence and does not overstate current remote CI before the
  workflow is published.
- Publication metadata is self-referential: committing a packet that names its
  own commit would change that commit. The run therefore freezes implementation
  checkpoint SHAs, generates and validates packet triplets against those exact
  adjacent boundaries, and writes aggregate body, packet, PR map, MOC, and this
  retrospective as a publication tail. Schema-v2 PR rows explicitly describe
  open-PR SHAs as evidence snapshots, so later metadata commits do not pretend to
  be a fixed point or rewrite the implementation boundaries.

## Follow-Up Boundaries

- `T108` remains open until hosted evidence covers all declared PR triggers,
  relevant and docs-only paths, Linux failure propagation and sentinels, Windows
  advisory behavior, ARM64-disabled evidence, artifact uploads, and post-merge
  `workflow_dispatch` after the workflow exists on `main`.
- `T117` remains open because branch protection does not yet require
  `validate-release-note`. The #326 packet/body already contains the required
  callout; a repository administrator must still configure that exact required
  check and record the resulting rule state. The callout is not configuration
  evidence.

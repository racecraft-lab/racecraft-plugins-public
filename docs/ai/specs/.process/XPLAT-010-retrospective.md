# XPLAT-010 Retrospective

## Outcome

XPLAT-010 produced and merged an 18-PR no-gap stack, #311 through #328. The
generated packet/body/validation triplets cover every adjacent review boundary
and all 18 validations report `passed`. Its frozen implementation head is
`a7b2d27b12fdc5051dfa4829c94f92752e2f5146`, with tree
`a1c42735d35619bbd0a4a90a42c57ab9e578848e`; final `main` merge commit
`ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29` has tree
`0d5a46bfa28efbca13d7f49539369705bd58d76f`, byte-identical to the verified
published stack tip. The final neutral-PATH deterministic suite passed 2512/2512 checks
(Layer 1 1373, Layer 4 953, Layer 5 186). All 18 review branches were deleted.
T108 hosted preflight evidence and T117 branch-protection configuration are
complete. Release publication and XPLAT-008 native operator UAT remain separate
boundaries.

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
  hosted follow-up then proved ARM64 available-but-disabled/no-queue behavior
  and advisory Windows failure handling. None of this preflight evidence
  substitutes for XPLAT-008 native installed-plugin UAT.

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
- Squash-merging #311-#313 discarded stack ancestry and made each next
  dependent PR conflict. Exact restacks repaired those heads. A temporary,
  operator-approved merge-commit window for #314-#328 then preserved each
  reviewed head as the exact second parent; the repository's normal squash-only
  policy was restored after the stack merged.

## Follow-Up Boundaries

- `T108` is complete. Manual `main` run `29161090549` succeeded at
  `ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29` with all eight artifacts, both
  Linux heavy jobs and sentinels passing, Windows x64 passing, and Windows ARM64
  available but disabled and not queued. Relevant run `29159969108`, docs-only
  run `29161055742`, and intentional failure run `29159559914` prove heavy,
  no-op sentinel, and failure-propagation behavior. PR #331 canaries prove
  `opened`, `synchronize`, `ready_for_review`, and `reopened` triggers.
- `T117` is complete. Non-strict `main` protection requires exactly five GitHub
  Actions checks: `validate-plugins`, `validate-pr-title`,
  `validate-release-note`, `container-preflight-linux-amd64`, and
  `container-preflight-linux-arm64`.
- The separate constitution amendment completed through PR #331 at
  `b537e3b43ca20d8f6e8b6e9430d797444462f2e9` before archive cleanup. The index-tooling
  defect is repaired in a separate isolated branch before archive.
- The first real release Highlights rewrite remains release-publication
  evidence, and public native-platform claims remain blocked by XPLAT-008 UAT.

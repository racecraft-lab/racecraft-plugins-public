# PR 1371: failure-path seam review record

## Known limits

The structural test in `test-failure-path-seam.py` detects direct handler
names, imports and attribute references within the runner package. It does
not detect string-based lookups through `getattr`, `globals` or `__dict__`,
references outside that package, or references within a second annotated
`FAILURE_PATH_ACTIONS` assignment.

These accepted informational limits require a future contributor source edit.
None occurs in the reviewed runner, so no current request reaches a bypass;
the contributor already controls the source. They are not runtime security
boundaries. The prior size-budget note was closed by compacting the epoch
fixture without changing its parsed JSON or its 23 ordered steps.

## CI recovery

At head `80d11bbe8`, the plugin test job and both Linux heavy-preflight jobs
were cancelled. Their required result checks failed closed on that cancelled
state. The logs show cancellation, without a test assertion failure. This is
not evidence of a test flake or a runner defect; the cause of the cancellation
is not established by those logs.

The recovery merges current main, preserves every registered test from both
parents, and regenerates the conflicted test-reference page from its sources.
No failure-path behavior changes are introduced by the recovery.

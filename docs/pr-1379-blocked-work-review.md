# PR 1379: blocked-work review limits

The Standards and Spec follow-up axes reviewed source at `ed8b9e4a`. Both axes
confirmed closure of the four original Medium findings and the overlapping-owner
and blocked-escalation follow-ups. The Spec axis retained the two Low notes below.
They are accepted limits, not demonstrated failing paths in this PR.

## Known limits

### S1379-ladder-after-skip: check ownership before block time

`reserve_retry_rung` receives a command digest and refuses a cause already marked
blocked. The check's owning tasks are first supplied to `block-exhausted-check`;
there is no earlier check-to-owner binding for admission to consult.

A hypothetical caller could associate a new check with an already dependency-blocked
task and request its ladder. The review did not demonstrate an orchestration path
that makes that association and dispatches those attempts. The runner cannot infer
that unstated ownership from the digest. A future ownership-binding change must
preserve the rule that blocked tasks receive no further attempts in the same run.

### S1379-cause-attribution: own and inherited causes for future renderers

An entry that owns an exhausted check can also depend on another blocked owner.
Its `causes` list preserves both checks, while `roots` retains its upstream links.
Each cause keeps its evidence once; the entry's `attempted` flag does not credit it
with the upstream check's attempts.

A future consumer that sums all linked causes as the entry's own attempts would
misattribute upstream attempts. No current PR-body or UAT renderer consumes this
record; ADR 0012 explicitly leaves those renderers unbuilt. This makes the proposed
consumer failure unreachable today. The renderer implementation must distinguish
own evidence from inherited evidence rather than summing `causes` indiscriminately,
and can add explicit ownership attribution if needed at that seam.

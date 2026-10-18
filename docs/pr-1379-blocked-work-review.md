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

## Cross-host re-review notes (head 4b34e934)

The Claude cross-host re-review confirmed the four original Medium findings closed
and found no blocking issue. It retained the Low notes below as accepted limits.

### C1379-unbound-requests: requests that name no unit or gate

`reserve` refuses a request when the units, gate or check it names meet the blocked
scope. A `failure_family` or `failure_class` escalation, a family-scoped retry or
continuation, and an implementation reserve without `tdd_units` name no unit, so the
guard has nothing to compare. For those escalation kinds the guard adds a key with
no subject that can never match.

None of these requests binds to a task unit, and the guidance requires `tdd_units`
on every implementation reserve, so no demonstrated path redispatches a blocked task
through them. A change that lets them carry a unit must add it to the blocked-scope
comparison.

### C1379-co-owner-roots: co-owners of one check carry no root link to each other

When one check names `owner_tasks=["T001", "T002"]` and T002 depends on T001, both
entries are attempted roots of the same cause and T002 gets `roots=[]`. The shared
cause already links them; no current code reads `roots`.

### C1379-dependent-retained-work: dependents copy their root's retained work

A dependency skip records the cause's `retained_work` and `unblock` note although it
was never attempted. A root that later gains a second cause keeps its first cause's
values on the entry; each cause record keeps its own. No renderer reads these fields
yet; the renderer must take retained work and unblock notes from each cause.

### C1379-gate-name: the ownerless gate name is free text

`block-exhausted-check` checks only that `gate` is non-empty text. A misspelled gate
records a block that matches no remediation request for the real gate. The caller is
the runner's own orchestration, which names gates from the workflow; whether gates
outside `REMEDIATION_GATES` can own a check is a design question for the builder.

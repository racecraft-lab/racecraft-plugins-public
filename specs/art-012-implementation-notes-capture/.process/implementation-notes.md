# Implementation Notes: ART-012

### T001

**Deviations/Edge cases/Surprises:** None

### T002

**Deviations/Edge cases/Surprises:** None

### T014

**Deviations/Edge cases/Surprises:** The Use site 3 pseudocode line could not be
left byte-identical as instructed. It read `Lead waits for all to complete,
merges results into COMPLETED_TASKS`, fusing a legitimate barrier with the
batched-arrival framing this task exists to remove; leaving it would have left
the wrong claim standing in the most-copied part of the section. Split into a
per-arrival append line plus `Lead merges results into COMPLETED_TASKS once the
whole run is in`. Barrier semantics preserved, wording changed. Swept for a
fourth batched-arrival site and found none: six candidates surfaced and all six
are legitimate, four describing where results merge rather than when they
arrive, two being chosen barriers at consensus use sites. Design Principle #2's
clarification was written into the file rather than only into this report, on
the grounds that a note reaching only the orchestrator reaches nobody reading
the document.

### T003+T004

**Deviations/Edge cases/Surprises:** The Layer 4 test's section extractor
terminates on any heading at or shallower than the section's own level when
that heading sits outside a code fence. The record's own literals
`# Implementation Notes: <SPEC_ID>` and `### <TASK_ID>` are exactly that shape,
so writing either at line start unfenced truncates the Phase 7 section and
fails every check after it, with no error naming the cause. Both had to go
inside fences; this nearly cost about 25 checks silently. The lifecycle heading
is `#### Phase 7 Setup:` rather than a Phase 7 "Step 0" because the document
already owns a global `Step 0.x` namespace and a live cross-reference to
`Step 0.9` sits inside Phase 7's own pseudocode, which a second Step 0 would
have collided with. Two checks forced unbroken clauses because the regex
gap-fillers are `[^.]` and no period may fall inside an asserted span. The
FR-006 instruction went into the Path A block rather than the shared Step 3c
template, appended after the existing anchor line so the anchor text survives
verbatim for the mirroring task. No batched-delivery contradiction exists
inside this file; the stale claim lived only in agent-teams-integration.md.

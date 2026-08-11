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

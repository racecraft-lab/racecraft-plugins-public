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

### T003

**Deviations/Edge cases/Surprises:** The Layer 4 test's section extractor terminates on any heading at or shallower than the section's own level when that heading sits outside a code fence. The record's own literals `# Implementation Notes: <SPEC_ID>` and `### <TASK_ID>` are exactly that shape, so writing either at line start unfenced truncates the Phase 7 section and fails every check after it, with no error naming the cause. Both had to go inside fences; this nearly cost about 25 checks silently. The lifecycle heading is `#### Phase 7 Setup:` rather than a Phase 7 "Step 0" because the document already owns a global `Step 0.x` namespace and a live cross-reference to `Step 0.9` sits inside Phase 7's own pseudocode, which a second Step 0 would have collided with.

### T004

**Deviations/Edge cases/Surprises:** Two checks forced unbroken clauses because the regex gap-fillers are `[^.]` and no period may fall inside an asserted span. The FR-006 instruction went into the Path A block rather than the shared Step 3c template, because Path B subagents and foreground singletons already return their output to the orchestrator directly, so a send-to-the-lead obligation would be meaningless there. It was appended after the existing anchor line so the anchor text survives verbatim for the mirroring task. The append instruction was placed at both `Wait` lines individually rather than only at the safety-net convergence, because an instruction sitting at the convergence reads as "wait for the barrier, then append", which is the batching FR-003 forbids. No batched-delivery contradiction exists inside this file; the stale claim lived only in agent-teams-integration.md.

### T005

**Deviations/Edge cases/Surprises:** The Codex platform turned out to already
run the per-arrival model natively, which is stronger corroboration than
research R10 predicted. Its bounded `wait_agent` loop consumes one worker's
actual summary at a time and already states that a status update or a timeout
alone is not the result, and the Codex SKILL.md implement row already says to
record each result as it arrives and then start the next parallel task. So the
cadence was written as riding that existing loop rather than as a change to it,
and the never-append-on-idle rule was anchored to this document's own
vocabulary of status updates and `wait_agent` timeouts rather than to Claude's
teammate-idle framing. B25 and B26 were verified before writing: the Codex
`domain-researcher.toml` agent exists and the Codex SKILL.md routing table
already names both `domain-researcher` and `orchestrator-direct`, so naming
them in Phase 7 restates this platform's own routing rather than importing the
Claude side. No FR-006 clause and no Agent Teams section were added, because
Codex workers already return their summaries through the harvest loop. The
`# Implementation Notes: <SPEC_ID>` literal had to stay fenced, since as a
shallower heading in raw text it would have truncated the section scope.

### T006

**Deviations/Edge cases/Surprises:** The tree-wide match count for contract
item 4 is 12, not the 7 the dispatch predicted, and the twelfth is the contract
file itself, whose "Resulting block" example prints the heading at column 0.
That match is the argument for scoping in to `speckit-pro/` rather than
excluding known generated directories: an exclusion list built from `dist/` and
the fixture path would have missed the contract document and reported four.
Scoping could not be narrowed to the Task Result block itself, because that
block sits inside a fence in all three files and the section helper
deliberately ignores fenced headings, returning empty; `## Summary Format`
occurs exactly once per file and was used instead. Item 2 needed no new check
kind and not even the `before` kind: two regexes built with `re.escape` from
the contract's own literals assert adjacency and last-ness, where `before`
would have proven only ordering. Item 4 could not take the four-tuple shape the
other checks use, because it asserts over a set of files rather than a document
body, so it is a separate method reporting under the same group label. Item 4
is also green from birth by design, being an invariant guard against a future
fourth copy rather than a red-first assertion, so the RED evidence covers items
1 through 3 only. Satisfiability was proven rather than assumed by simulating
the intended edit against all four targets and confirming 10 of 10 turn green.

### T010

**Deviations/Edge cases/Surprises:** None

### T011

**Deviations/Edge cases/Surprises:** None

### T007

**Deviations/Edge cases/Surprises:** None

### T008

**Deviations/Edge cases/Surprises:** None

### T009

**Deviations/Edge cases/Surprises:** None

### T012

**Deviations/Edge cases/Surprises:** None

### T013

**Deviations/Edge cases/Surprises:** None

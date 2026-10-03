# Every SPEC declares one value unit; outgrowing it is recorded, never a stop

Status: accepted

A SPEC's scope is fixed by its **value unit**: one actor, one observable outcome, one primary surface, and one headline acceptance step that a non-engineer runs from the UAT runbook. The UAT runbook leads with that step; per-story acceptance tests stay as supporting steps. This holds on Claude Code and Codex alike.

**Every SPEC has one.** There is no exemption class. Refactor, infra, upgrade and spike SPECs name a developer or operator as the actor, and their acceptance step is still something a non-engineer can run and read ("run X, see Y"). Without that, the promise that a SPEC is the smallest unit of value a user can see, review and accept would have a hole.

**The roadmap entry is the source of truth.** speckit-prd writes a Value unit block on each roadmap SPEC entry. Scaffold reads it, lets the user confirm or sharpen it, and writes the confirmed version back to the roadmap and into the Design Concept. spec.md and the UAT runbook copy from it. A roadmap without the block (any written before this decision) gets it elicited in scaffold's interview.

**Scaffold checks it structurally and cannot finish without it.** A runner helper checks that all four fields are present, non-placeholder and singular, with the surface taken from the fixed primary-surface list. The user then confirms it. Scaffold is the interactive skill, so this is not a run stop.

**One per SPEC, not per slice.** Declared slices (ADR 0006) stay review partitions with no value unit of their own. The reviewability budget's own Primary surface field is removed; the reviewability report reads the surface from the value unit, and its multi-surface warning stays advisory.

**Autopilot detects drift deterministically.** Each spec.md user story names its actor and primary surface. After Specify and again after Plan, a runner helper compares them with the value unit and names the first story that differs. Missing or malformed tags climb the retry ladder (ADR 0004) like any other evidence.

**Outgrowing the value unit never stops a run.** Autopilot records "recommend split at story X" with the reason in the decisions list, the review artifacts and the draft PR body, then builds the full approved plan. It also appends a Split recommended note (story, reason, run link) to the SPEC's roadmap entry without changing the catalog. The next scaffold on that roadmap shows open notes and asks whether to add a SPEC. Only scaffold changes the catalog.

## Considered Options

- **Allow several actors per SPEC.** Rejected: an author-and-reviewer SPEC is two outcomes in one PR, and the pilot that grew to 71 tasks across 3 layers is the result.
- **Accept the outcome when every per-story step passes, with no headline step.** Rejected: the reviewer needs one step that proves the value; per-story steps check parts of it.
- **Keep the value unit only in the Design Concept.** Rejected: a roadmap could then catalog SPECs that never had one, and drift notes would have nowhere durable to land.
- **Put it on the PRD's acceptance-criteria groups.** Rejected: the PRD is meant to stay lean, and the roadmap already maps 1:1 to those groups.
- **Add an agent judgment of outcome fit or step runnability.** Rejected: not deterministic across hosts, which host parity (ADR 0003) requires. The user's confirmation at scaffold covers judgment.
- **Typed exemptions for refactor, infra, upgrade or spike SPECs.** Rejected: an exemption path reopens SPECs that no one can accept.
- **Defer stories outside the value unit instead of building them.** Rejected: that changes the plan the user approved during implement.
- **Leave the split recommendation in the PR only.** Rejected: the human would have to carry it to the next scaffold by hand.

## Consequences

- The roadmap template, speckit-prd's authoring protocol, scaffold, grill-me's slice-sizing branch, the spec template's user stories and the UAT runbook template all change. The block's exact layout is an implementation detail.
- The roadmap template's typed block exceptions (`refactor`, `infra`, `upgrade`) go away with ADR 0006's advisory reviewability; nothing replaces them here.
- Autopilot gains a write to the roadmap, limited to appending Split recommended notes.
- Validation must cover missing, placeholder and plural fields, legacy roadmaps, untagged stories, a second actor and a second surface after Specify and after Plan, and identical results on both hosts.
- This records the planning decision for [Value unit: actor, outcome, acceptance step, surface](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1025); no runner behavior exists for it yet.

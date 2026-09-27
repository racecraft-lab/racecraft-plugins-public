# Research: HRNS-015 Planning Decisions

**Updated**: 2026-09-26. This Plan research pass used the bound project-local skill, native setup once, and three read-only research roles; the domain role received a bounded documentation follow-up. Actual results were consumed. Decisions below distinguish supplied owner authority, local artifact evidence, design choices and unqualified runtime behavior.

## Evidence and Capability Status

- Native setup returned the existing feature/Plan paths and branch with exit0; it retained the existing Plan instead of overwriting it from the template. The reviewability preset Plan/spec/tasks templates and constitution 2.0.0 were loaded directly.
- Local mandatory context: current spec, design concept Q&A/Open Questions, six existing Plan artifacts and four checklists. A narrow inventory parser counted candidate unions; these are not actual base/head diffs.
- Domain research: four broker research_search calls returned search_unavailable, followed by three docs_query calls (Python, JSON Schema, GitHub) returning fetch_failed/rate_limited. Every result reported screening_mode=jev, no chunks, no dropped results and no source URLs. No official-source factual claim was obtained.
- Independent repository/spec research: the cloud read was denied for private-context transmission; the explicitly selected local read failed before files were read. No alternate cloud route was used. Independent source-behavior and checklist audits therefore remain unavailable.
- Bounded child local evidence identified registered packet/read-only, phase-coverage, spec-index, scaffold and lifecycle tests; HEAD 7a994ba01 / origin/main 09c4c5ada checkout state is evidence of history, not proof of each behavior.

**Fallback disclosure**: No installed official-documentation capability was usable; used the supplied workflow decisions and local contract/artifact evidence. Confidence is medium for the local design and low for unverified external API/schema/runtime behavior. No installed independent repository-reading capability was usable; used mandatory Plan context and narrow local metadata searches, with medium confidence in artifact consistency and low confidence in complete shipped-versus-remaining behavior coverage.

**Capability path**: requirements/context → bound spec/design/preset/constitution reads; candidate sizing → local inventory metadata parser; official docs → research broker unavailable; independent code/spec audit → local delegation unavailable. Evidence: [spec](spec.md), [design concept](../../docs/ai/specs/.process/HRNS-015-design-concept.md), [inventory](.process/slice-inventory.md), native setup result and consumed research-agent summaries. Runtime correctness still requires failing-first acceptance fixtures.

## R1 — Approved Delivery and Current Proposal

**Decision**: Retain owner-approved A → B → C1a → C1b → C2. Present eighteen candidate increments only as the owner-review alternative after B2a leaves scope. Do not convert the instruction to resolve blockers into approval of eighteen PRs.

**Rationale**: The inventory's five union counts are A 4 production / 39 total, B 3 / 36, C1a 1 / 29, C1b 4 / 29 and C2 0 / 40; removing shipped link-only README/template paths makes C2 34. Every approved group exceeds 24 candidate paths. These conservative candidates may not all change in the actual diff and the source/generated fan-out still needs review; none is a qualified changed-file minimum.

**Alternatives considered**: Silently keeping four slices contradicts the explicit C1 split; silently adopting eighteen PRs fabricates ratification; excluding generated/process paths or waiving strict caps contradicts scope policy. Explicit owner rescope is the alternative to ratifying the candidate split.

Historical Q11 signals differ: 1,362 whole-feature versus 1,442 sum (282+410+335+415); later estimates are also not current diff proof. No refactor weight is inferred from their differences. Current per-slice LOC remains not estimated. See [Plan budget](plan.md#five-approved-slices-and-budget-evidence).

## R2 — Refactor Estimate

**Decision**: Retain optional required_refactor_files as additional distinct existing-file work absent from files. Use the existing 40 LOC file weight after the ordinary modify discount, preserving the existing base result and spike precedence. Invalid/absent signals use the existing normalization policy rather than a new exception path.

**Rationale**: The spec delegates shape/weight to Plan; extending the existing signal is simpler than introducing a second estimator. This is a design contract, not a fresh proof that the current implementation supports it.

**Alternatives considered**: A boolean has no scope measure; a global multiplier distorts unrelated estimates; historical292→1,362 or80LOC drift cannot establish a measured weight.

## R3 — Scoped Baseline, Split Syntax and Greenfield

**Decision**: Preserve #694's named-entry/pragma/missing-budget baseline. Remaining changes are ordered complete slice aggregation and LOC-only 1.5x greenfield allowance. Exactly one nonnegative integer row per declared ID; reject missing/extra/duplicate/placeholder/nonnumeric/at-block rows and report ordered slice_results plus aggregate existing count fields. Ordinary file/surface limits and typed classes refactor/infra/upgrade remain.

**Design Concept Open Question 3 — slice-budget syntax**: Ordered Slices IDs and a Slice Budgets Markdown table with columns Slice, Estimated LOC, Production files, Total files. No literal accepted exception pragma in generated templates.

**Rationale**: Q6 settles per-slice policy; Open Question 3 leaves syntax to Plan. FR-011–FR-013 are explicitly removed by the current rescope; shipped baseline fixtures must stay green, not be claimed as new red-first repairs.

**Alternatives considered**: Last-match values or zero defaults hide missing evidence; a new split exception bypasses actual budgets; applying greenfield to file/surface limits changes the agreed allowance.

## R4 — Tracked Spec Index and Required Refresh

**Decision**: Source Git-index membership decides inputs, including staged additions and excluding every untracked candidate, even within a tracked directory. Existing generator joins release-artifact refresh; isolated check names stale tracked output paths. Preserve source membership in isolated validation.

**Rationale**: Q10 chooses the existing required artifact job; no new workflow job or optional-only docs gate. Generated historical formal-001 text belongs in test-owned fixtures, not a runtime read of this active feature.

**Alternatives considered**: Filesystem-only scanning can create local-only links; manual generated edits and a separate optional gate do not meet the required check contract.

## R5 — Marker Visibility and Quality Commands

**Decision**: Each visible single-line non-nested bracket tag counts once if comma-separated, whitespace-trimmed tokens contain exact case-sensitive Gap. Gap and clarification count/detail paths share exclusion of inline/fenced/indented code. Other marker types stay unchanged.

Quality commands are an optional validated map of the four existing quality slots. Declarations override only their slot; effective commands remain strings, with additive command_sources and quality-gate source=declared. Invalid object/key/value fails G0 with a named diagnostic; absent/undeclared slots retain detection. Preserve approved thresholds/basis.

**Rationale**: Q4/Q5 and clarified boundaries define real markers; Q9 chooses explicit config rather than parsing arbitrary agent prose. General detected mypy/ruff commands do not authorize executing them outside the repository's pinned lint environment.

**Alternatives considered**: Prefix/raw-line matching misses real compound tags or counts examples; parsing arbitrary AGENTS tables adds a fragile convention; fallback on invalid declarations hides config failure.

## R6 — Packet Rendering and Confidence Placement

**Decision**: One optional nonblank unfenced release_note adds exactly one final Release note heading after the eight required headings and one renderer-created release-note fence in a fourth editable field. Reject explicit wrong-type/blank/fence-breaking inputs. Heading and balanced marker lines are protected; only enclosed note content is editable. No absent-note or draft default is invented.

**Design Concept Open Question 8 — verdict placement**: Render the current Phase 6.5 table Verdict as a protected generated line under Verification, including refresh with a supplied body. Missing/invalid verdict blocks final emission; overview status/score is not a substitute. Retain the single UAT Runbook heading between How To UAT and Verification.

**Rationale**: Q3 chooses an optional packet input; Open Question 8 leaves the location to Plan. These are distinct from Open Question 3 and Q8's envelope scope.

**Alternatives considered**: Hand-writing an entire body or post-packet edit breaks provenance; a new standalone verdict section adds an unnecessary heading; stale supplied body text is not current evidence.

## R7 — Packet Guard, Post and Executor Return

**Decision**: Exempt only this validated packet's three canonical untracked paths; unrelated changes, tracked modifications, another packet or unreadable status still block. Derive the requested 13 Post names from POST_STEPS and enforce full completion against both persisted records. Unique exact-name legacy progress survives; missing/renamed rows start pending. Only identical verified absent-extension reason-coded skips for optional canonical extension rows qualify at full-run success; staged returns do not claim full completion.

Team-capable executor clean return requires actual child results or supported stops and genuine teardown/no-active-child/cleanup confirmation. Missing capability/evidence stays unresolved in the result; HRNS-017 owns separate lifetime observations.

**Rationale**: Q1/Q7 and FR-018/019 choose these outcomes. Historical list counts are not assertions about current 2.37.0; the requested 13-row invariant must be tested. Ordinary status-evidence validation and an advisory confidence score are separate contracts.

**Alternatives considered**: Broad untracked exemptions, inferred progress by row position, or assumed host cleanup fabricate evidence. No host-policy ignore or force-add workaround is designed.

## R8 — Review Feedback API and Ordering

**Decision**: Reuse the existing gh api graphql pattern. Independently traverse reviewThreads and each thread's comments via pageInfo.hasNextPage/endCursor; a missing cursor or failed/inconsistent page blocks mutation. A thread-node query handles nested continuation. Fix, fully verify, commit, push, query fresh PR headRefOid, compare intended commit, then serially reply/resolve/read back each resolved state.

**Rationale**: The local prior design records this integration shape; no fresh official schema/documentation result was returned. Exact query/mutation field behavior is therefore a validation obligation, not an externally verified fact. Failed verification prevents push; failed push/query/mismatch leaves local commits and review threads pending.

**Alternatives considered**: One-page collection truncates feedback; replying before remote-head match races publication; a second API route adds a pattern without evidence of need.

## R9 — Analyst Results and Explicit Abandonment

**Decision**: No fixed blind-spot or whole-workflow wall-clock limit. Await the actual summary. Late nonempty result is ran; only dispatch error, empty return or explicit operator abandonment permits continuation without findings. Record the same specific reason in the existing Blind-spot pass header and operator status. Silence/time is not abandonment; an entire-workflow stop means stop.

**Rationale**: Q2 removed the deadline and #642 already removed the autopilot wall-clock budget. The stale Tasks two-hour instruction is a workflow reconciliation defect, not a new owner-imposed cap.

**Alternatives considered**: A larger timeout can still discard findings; inferring abandonment invents intent; a new state/UI field is unnecessary.

## R10 — Bounded Envelopes and Existing Links

**Decision**: Q8 remains failure sites now, rest to HRNS-019. Both hosts get complete tested registry envelopes for status index-check/topology, scaffold reviewability/worktree placement and phase index-writing only. No broad sweep or self-describing-error redesign.

For existing roadmaps, resolve a legacy target relative to its containing document; preserve only a real verified workflow file, otherwise repair to actual .process output. The new-template/README link fix is baseline from #698 and is not a new operation in C2.

**Rationale**: This preserves Q8 and the surviving half of FR-025 without duplicating shipped scope.

**Alternatives considered**: All 58 bare sites expand into HRNS-019; unconditional legacy rewrite breaks working links; unconditional preservation keeps broken links.

## Research Completion Limits

Plan choices delegated by the clarified requirements are recorded; Open Questions3/8 are explicitly answered. Actual owner delivery ratification is still pending. Official API/schema/runtime facts and an independent full source audit were unavailable. Source rescope assertions come from the exact workflow/spec inputs, with no claim of fresh behavior qualification. Tasks/Analyze must reconcile remaining inventory/state/checklists and run current gates. Nothing here claims implementation, G3/G6, actual LOC or valid marker emission.

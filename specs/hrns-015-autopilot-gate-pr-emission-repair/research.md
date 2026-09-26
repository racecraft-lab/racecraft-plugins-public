# Research: HRNS-015 Planning Decisions

This record resolves design choices left to Plan by the clarified [spec](spec.md) and the design concept's Q1–Q11 log. It does not change those decisions. External documentation lookup through the SpecKit research broker was attempted on 2026-09-25: web search was unavailable without a Tavily key and documentation lookup was provider-rate-limited. The GitHub route below is grounded in the existing repository GraphQL pattern and must pass failing-first fixtures before release; the unavailable lookup is not treated as verification.

## R1 — Four review slices and estimate reconciliation

**Decision:** Ship A → B → C1 → C2. Use the conservative 1,442-LOC sum of A 282, B 410, C1 335, and C2 415 for current aggregate planning. Recalculate actual diff and file counts at each PR boundary.

**Rationale:** Q11's 1,362-LOC value was a separate whole-feature estimate with different signals before C was split. The four slice values sum to 1,442; neither number may silently replace the other. The 80-LOC difference is an estimator artifact to investigate, not a measured refactor size. C1's host and executor inventory brings its file projection to 24, leaving one-file headroom under the strict less-than-25 limit.

**Alternatives considered:** Three slices leaves C above the file limit; five slices is unnecessary without measured overage. Treating the 1,362 aggregate as the sum would be arithmetically false.

## R2 — Required-refactor estimator signal

**Decision:** Add optional `required_refactor_files` to `estimate-spec-size`. It is a nonnegative integer count of additional existing files whose required refactor work is not already included in `files`. The existing baseline remains unchanged; add 40 LOC per such file **after** the existing modify discount. The 400-LOC ceiling and ceil-based suggested slice count then use the new total. `spike` still returns its fixed result first. Missing/invalid values normalize to zero through the existing size-signal policy.

**Rationale:** The existing estimator gives a 40-LOC file weight. Using that weight for distinct required refactor files is the smallest explainable extension and ensures mandatory refactor work survives the generic modify discount. The caller must avoid double counting by supplying only files excluded from `files`. Q11's 292-to-1,362 drift involved different stories, files, and FRs and does not justify an inferred weight.

**Alternatives considered:** A boolean surcharge has no scope measure; multiplying every estimate would distort unaffected calls; deriving 80 LOC from Q11 would assert causation not in the evidence.

## R3 — Reviewability gate and issue #637

**Decision:** `reviewability-gate` setup requires `inputs.spec_id`. Match exactly one case-sensitive `### <spec_id>:` authored roadmap heading, ending at the next peer-level entry. Read all required budget fields and primary surfaces only from that section. A missing input is an invalid request; missing section or field is `status: block`, `pass: false`, exit 1, with the spec ID and field in the blocker. Honor only a line-anchored accepted `Reviewability-Exception` in that selected authored section; keep accepted classes `refactor`, `infra`, `upgrade`. Reject malformed, mis-cased, placeholder, or unsupported selected-section candidates with a named `exceptions.rejected` reason and ordinary budget evaluation; an over-block budget remains blocked. For a split, use ordered `Slices:` IDs and `Slice Budgets:` table columns `Slice`, `Estimated LOC`, `Production files`, `Total files`; require a unique complete nonnegative-integer row for each ID and no other rows. Report sum across rows and judge each row below block thresholds. The 1.5x greenfield multiplier changes LOC warn/block only.

**Rationale:** This directly covers issue #637's oversized first/small last entry, selected `infra` pragma, and missing-budget reproduction. It prevents a neighboring entry or generated text from changing the named result and preserves the existing typed override vocabulary.

**Alternatives considered:** Last-match regex repeats the bug; defaulting a missing field to zero is false evidence; a new `split` exception avoids checking slice budgets; multiplying file/surface thresholds for greenfield exceeds the documented allowance.

## R4 — Spec index in required artifact check

**Decision:** Determine candidate membership from the source Git index, including staged additions but excluding all untracked files even inside a tracked directory. The refresh script calls the existing spec-index generator as a named step after metadata, payload, and marketplace generation. Plain refresh writes; `--check` compares in an isolated copy and names stale tracked index paths.

**Rationale:** The required artifact-consistency job already runs that script. This makes stale backlinks and roadmap home entries fail without a new CI workflow step.

**Alternatives considered:** A separate optional docs gate leaves required CI green; filesystem-only scanning includes untracked files and can yield a local-only backlink.

## R5 — Marker visibility and command precedence

**Decision:** Tokenize a single-line non-nested bracket tag by comma, trim spaces/tabs, and count one exact case-sensitive `Gap` token per qualifying tag. Use one Markdown visibility filter for gap and clarification count/detail paths that excludes inline, fenced, and indented code. Keep other marker types' behavior. In quality-gates config, an optional per-slot command overrides detection for that slot and reports `source: declared`; undeclared slots follow existing detection.

**Rationale:** This covers both checklist forms and quoted examples while avoiding a separate rule in each gate. A slot map follows the existing detector's output shape without parsing host AGENTS documents.

**Alternatives considered:** Prefix matching misses later-token Gap; raw-line matching counts examples; parsing arbitrary prose command tables makes the runner depend on host documentation structure.

## R6 — Packet and Post contracts

**Design Concept Open Question 3 — optional release_note:** Adopt one optional `release_note` packet input and a fourth final-body editable field, as Q3 decided; do not rely on a full-body override or post-packet manual edit.

**Decision:** A final packet may carry one optional release-note field after the eight required headings, with one editable body and protected heading/markers; draft packets never gain it. The generated Phase 6.5 Verdict line sits under Verification, is protected, and is recomputed on refresh from the workflow table. The packet dirty guard ignores only the current packet's canonical untracked JSON/body/validation paths. Make `POST_STEPS` the 13-row source for a **new completion-boundary rule** that reads persisted workflow and state and rejects missing, duplicate, pending, or in-progress rows. Both hosts invoke it immediately before success. Existing `status-evidence` remains an audit, not this gate.

**Rationale:** Q1, Q3, and Q7 explicitly decided these observable behaviors. The current phase-coverage guard has only 11 Post names and its `status-evidence` rule does not prove every row completed.

**Alternatives considered:** Hand editing PR body breaks packet provenance; treating overview Confidence Gate status as Verdict is wrong; broad untracked exemptions admit unrelated changes; re-invoking `status-evidence` without a new rule misses the defect.

## R7 — Team completion evidence

**Decision:** Each team-capable executor on both hosts reports clean completion only after it has collected each child result or used a supported stop operation for an unfinished child, requested graceful shutdown, and confirmed no active child plus cleanup complete. Its structured result names any unresolved child or teardown confirmation. Do not infer Codex child lifetime from Claude behavior; HRNS-017 retains that host observation.

**Rationale:** The requirement is about evidence at executor return, independent of whether a host would auto-clean children on parent exit.

**Alternatives considered:** Disabling team tools conflicts with existing tool scope; assuming host auto-cleanup would make the result unverifiable.

## R8 — Resolve-pr GitHub API route and ordering

**Decision:** Reuse `gh api graphql`, already used by the Claude resolve-pr skill for `repository.pullRequest.reviewThreads(first: 100)`. Traverse the review-thread connection through `pageInfo.hasNextPage/endCursor` and each thread's comments connection independently through its own cursor, never relying on the first ten comments. For a nested continuation, query that thread by its GraphQL node ID; treat missing cursor or any failed page as incomplete feedback and stop. After all fixes and full verification, commit and push; then make a fresh GraphQL query for the PR's `headRefOid` (the field is already used in `scripts/validate-release-pr-integrity.py`) and compare it with the intended local commit SHA. Only a match permits serial reply, resolve, and confirmed resolved-state readback. Failed verification prevents push and leaves any earlier local fix commits identified in the failure report; failed push/query/mismatch leaves the commit local and threads pending. Retry requires full verification, push, and a new matching remote-head query.

**Rationale:** One GraphQL API route provides thread IDs, comment pagination, and PR-head identity. The fresh post-push query prevents a locally verified but unpublished fix from being treated as available to reviewers. General GitHub cursor pagination and the repository's existing route support the shape; exact schema/CLI behavior is acceptance-fixture work because the broker could not fetch new documentation during Plan.

**Alternatives considered:** The existing single-page query truncates feedback; reply before push races publication; a separate REST ref route adds a second API pattern without an identified need.

## R9 — Blind-spot completion and explicit abandonment

**Decision:** Remove the fixed five-minute wait. A nonempty late analyst result records `ran` in the Design Concept header's existing `**Blind-spot pass:**` line. A no-findings continuation records exactly one of `dispatch error: <message>`, `empty return`, or `operator abandonment: <instruction reference>` there and uses the same reason in the operator status line. “Operator abandonment” is accepted only from an explicit operator instruction to proceed without those findings, visible in the active conversation; elapsed time, a silent child, or parent exit is not that signal. A request to stop the entire workflow stops it rather than continuing.

**Rationale:** This is an auditable signal without a new timer, state store, or guessed host lifecycle. It preserves the record location found in the current scaffold/design concept.

**Alternatives considered:** A longer fixed deadline can still discard valid late results; interpreting timeout as abandonment fabricates operator intent; a new UI field is outside this slice.

## R10 — Full request examples and issue #638 links

**Design Concept Open Question 8 — bounded inline envelopes:** Repair only the named live failure sites on both hosts with complete registered request envelopes; HRNS-019 owns the remaining broad sweep.

**Decision:** Replace bare names only at the five named live failure sites with complete existing runner envelopes, on both hosts. New roadmap template links point under `docs/ai/specs/.process/<SPEC-ID>-workflow.md`. When scaffold updates an existing roadmap, it resolves a legacy link against its containing document; preserve it only when its target exists, otherwise write the actual new output location.

**Rationale:** This fixes observed malformed calls and issue #638's broken generated link while leaving the full call-site sweep to HRNS-019. The target-existence rule avoids breaking legitimate legacy layouts.

**Alternatives considered:** Rewriting every bare call expands scope into HRNS-019; always rewriting legacy links changes working documents; preserving every legacy link retains broken output.

## Research status

All Plan-level choices are recorded. The exact external GitHub schema was not freshly fetched because the research broker was unavailable/rate-limited; the route is based on existing repository usage and requires failing-first fixture validation. The operational decision between a single split-PR run and separate runs belongs to the Atomicity Route after Tasks. Codex child survival after parent exit belongs to HRNS-017; neither item blocks this design.

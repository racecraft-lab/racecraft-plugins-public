# API Contracts Checklist: Autopilot Staging

**Purpose**: Unit tests for the requirements themselves — is `--stage` specified
precisely enough that six downstream specifications can build against it, and
that the two distributions cannot silently diverge again? The argv contracts have
*already* diverged once without detection (the Claude synopsis omits the
confidence-mode flags the Codex side advertises, FR-002). Nothing in CI diffs the
two `SKILL.md` bodies, so every item below asks whether a rule is pinned by
something executable or survives only as prose.

**Created**: 2026-08-04

**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md) · [contracts/stage-invocation.md](../contracts/stage-invocation.md) · [contracts/scaffold-autopilot-chain.md](../contracts/scaffold-autopilot-chain.md)

**Depth**: Standard · **Audience**: Reviewer (PR) · **Domain**: api-contracts

Focus areas, verbatim from the Phase 4 domain prompt: the argv surface specified
identically for both distributions including flag names, values, precedence
against `--from-phase`, and error text; the stage vocabulary closed and stated
once rather than per platform; the scaffold → autopilot chain contract precise
enough for ART-011 and documentation-only; the out-of-stage marker using
`skipped:` under all four FR-011 constraints; and above all anything specified
only in prose.

Domain 1 (`state-management.md`) and domain 2 (`error-handling.md`) resolved 14
items between them. None is re-raised here. Domain 2 in particular split the
invocation contract's exit codes along the *unreadable-versus-absent* axis;
CHK023 below is a different split on a different axis and is noted as such.

## Requirement Completeness — Argv Surface, Both Distributions

- [x] CHK001 Is the argument name specified as one literal shared by both distributions, rather than described as "a stage argument" each side may spell its own way? [Completeness, Spec §FR-002, contracts/stage-invocation.md §1]
- [x] CHK002 Is the full accepted argv surface enumerated for each distribution, rather than only the newly added flag? [Completeness, contracts/stage-invocation.md §1]
- [x] CHK003 Is the pre-existing synopsis divergence — the confidence-mode flags the Claude side omits — named as a defect this change repairs, rather than left as an undocumented difference? [Completeness, Spec §FR-002]
- [x] CHK004 Is the repair scoped as documentation catching up to shipped behaviour, with the evidence that the capability already exists, so a reviewer can tell it changes no gate outcome? [Completeness, Spec §FR-002, §SC-008]
- [x] CHK005 Is argument *order* explicitly declared non-normative, given the two synopses list the flags in different orders? [Completeness, contracts/stage-invocation.md §1]
- [x] CHK006 Does the contract account for every visible difference between its rendering of the Claude line and the shipped line, rather than naming only some of them? [Resolved, contracts/stage-invocation.md §1]
- [x] CHK007 Is the request shape for the shared operation specified field by field, with types and required/optional status, rather than by example alone? [Completeness, contracts/stage-invocation.md §3]
- [x] CHK008 Is the response envelope specified field by field, including the type of each field and the meaning of its null case? [Completeness, contracts/stage-invocation.md §3]
- [x] CHK009 Is the choice of a structured JSON response over the bare token the sibling resolver returns justified, so the shape is a decision rather than an accident? [Completeness, contracts/stage-invocation.md §3]

## Requirement Clarity — Vocabulary and Value Sets

- [x] CHK010 Is the stage vocabulary declared closed, with the exact number of members fixed, rather than described as "the stage names"? [Clarity, Spec §FR-001, §Key Entities]
- [x] CHK011 Are casing and spelling fixed as literal tokens, so a value differing only by case is unambiguously rejected? [Clarity, Spec §FR-001]
- [x] CHK012 Is the same vocabulary required for both the invocation argument value and the recorded durable entry, so the two cannot drift into separate dialects? [Clarity, Spec §FR-001]
- [x] CHK013 Is the vocabulary genuinely stated once, or does the document asserting that also restate it — and if copies exist, is each identified as a copy rather than a peer source? [Resolved, contracts/stage-invocation.md §Stage vocabulary]
- [x] CHK014 Are the vocabulary copies pinned by something executable, given that prose cannot be golden-fixtured and nothing compares the two skill bodies? [Resolved, contracts/stage-invocation.md §Stage vocabulary, plan.md §6]
- [x] CHK015 Is the terminal-status vocabulary the chain contract hands ART-011 identified as owned by a shipped source, rather than presented as six literals to copy? [Resolved, contracts/scaffold-autopilot-chain.md §4]
- [x] CHK016 Is the reason the vocabulary must be a cross-spec contract recorded, rather than the tokens simply being asserted? [Clarity, Spec §FR-001]

## Requirement Consistency — Precedence and the Operation Contract

- [x] CHK017 Is precedence between an explicit stage and auto-detection stated as a ranked order rather than as prose a reader must infer an order from? [Consistency, contracts/stage-invocation.md §2, Spec §FR-006]
- [x] CHK018 Is `--from-phase` positioned relative to `--stage` as a non-competing input, with its effect bounded to within the resolved stage? [Consistency, contracts/stage-invocation.md §2]
- [x] CHK019 Is the string-pinned Codex sentence that constrains `--from-phase` identified, so an edit cannot break a structural assertion unknowingly? [Consistency, contracts/stage-invocation.md §2, Spec §FR-013]
- [x] CHK020 Is the absence of a recorded stage placed unambiguously within the precedence order, rather than being a fourth outcome outside it? [Consistency, contracts/stage-invocation.md §2, Spec §FR-008a]
- [x] CHK021 Is the operation identifier fixed, along with its mode and both registration sites, so the two distributions cannot reach two different implementations? [Consistency, Spec §FR-012, contracts/stage-invocation.md §3]
- [x] CHK022 Do the named invocation sites for the two distributions actually exist in the files named, and does each sit early enough for a pre-flight rejection to precede phase work? [Resolved, contracts/stage-invocation.md §3, plan.md §4]
- [x] CHK023 Does the exit-code table distinguish the runner's request-validation diagnostics from the operation's own process exit codes, rather than folding both into one column? [Resolved, contracts/stage-invocation.md §Exit codes]
- [x] CHK024 Is every documented error string specified verbatim, so a test can assert on it rather than on a paraphrase? [Consistency, contracts/stage-invocation.md §Response — exit 2]
- [x] CHK025 Are the error strings consistent with the vocabulary they enumerate, so a rejection message cannot advertise a value set the resolver does not accept? [Consistency, contracts/stage-invocation.md §Response — exit 2]

## Scenario Coverage — The Scaffold → Autopilot Chain

- [x] CHK026 Is the handoff artifact reduced to a single named token, with an explicit statement of what does *not* cross the boundary? [Coverage, Spec §FR-016, contracts/scaffold-autopilot-chain.md §1]
- [x] CHK027 Is everything the autopilot derives from that one token enumerated, so ART-011 can confirm it need pass nothing else? [Coverage, contracts/scaffold-autopilot-chain.md §1]
- [x] CHK028 Is the entry precondition stated as a checkable property of the scaffold's own output, rather than as an assumption about scaffold behaviour? [Coverage, contracts/scaffold-autopilot-chain.md §2]
- [x] CHK029 Is the per-platform invocation form given for both distributions, and does it agree with the full argv surface it defers to? [Coverage, contracts/scaffold-autopilot-chain.md §3]
- [x] CHK030 Is the completion signal observable from the workflow file alone, without a live session or the state file, as ART-011 requires? [Coverage, contracts/scaffold-autopilot-chain.md §4]
- [x] CHK031 Is the distinction between a corroborating signal and the completion test itself made explicit, so ART-011 cannot read the recorded stage as "planning finished"? [Coverage, contracts/scaffold-autopilot-chain.md §4, Spec §FR-008a]
- [x] CHK032 Is the documentation-only boundary stated with an enumerated list of what is *not* shipped, rather than as a general disclaimer? [Coverage, Spec §FR-016, contracts/scaffold-autopilot-chain.md §5]
- [x] CHK033 Is the deferral of the draft-pull-request limb attributed to a named downstream specification with the reason it cannot be exercised here? [Coverage, Spec §Out of Scope, contracts/scaffold-autopilot-chain.md §5]

## Edge Case Coverage — The Out-of-Stage Task Marker

- [x] CHK034 Is the marker's status token fixed as a literal, and is the field it occupies named, rather than "mark them skipped"? [Edge Case, Spec §FR-011]
- [x] CHK035 Is the requirement that the entry name stay byte-identical stated with the consequence of violating it, given the guard matches post-implementation checkpoints by exact equality? [Edge Case, Spec §FR-011]
- [x] CHK036 Is the prohibition on the substring `pending` stated with its casing rule, matching the case-insensitive check that enforces it? [Edge Case, Spec §FR-011]
- [x] CHK037 Is the reuse of the established `skipped: <reason>` shape justified by an existing precedent rather than invented for this feature? [Edge Case, Spec §FR-011]
- [x] CHK038 Is the marked set scoped to include every post-implementation entry, not only the implementation phase, since that family is where the audit blocks? [Edge Case, Spec §FR-011]
- [x] CHK039 Is the audit that tolerates the marker identified as belonging to one distribution or to both, given the constraint is written as though it were shared? [Resolved, Spec §FR-011]
- [x] CHK040 Is the canonical list required to stay untruncated, so the marker is an annotation rather than a deletion? [Edge Case, Spec §FR-011, §Out of Scope]

## Non-Functional — Prose-Only Specification, the Divergence Vector

- [x] CHK041 Is the absence of any CI comparison between the two skill bodies recorded as a stated constraint, rather than assumed known? [Traceability, Spec §Assumptions, contracts/stage-invocation.md preamble]
- [x] CHK042 Is parity required to come from shared executable logic rather than from a prose comparison, with the reason the latter cannot work? [Traceability, Spec §FR-012, contracts/stage-invocation.md §5]
- [x] CHK043 Is the parity assertion assigned to a named test file, and is the surface it must *not* be added to named with the reason? [Traceability, Spec §FR-015a, contracts/stage-invocation.md §5]
- [x] CHK044 Is the Codex constraint set — pinned sentences, additive-only edits, word cap — stated concretely enough that an edit can be checked against it before it lands? [Traceability, Spec §FR-013]
- [x] CHK045 Does the word-cap budget account for every edit the plan directs into the capped body, rather than for a subset? [Resolved, plan.md §4]
- [x] CHK046 Is the reporting obligation specified as an observable output with named content, so "reports the resolution" is testable? [Traceability, Spec §FR-006, contracts/stage-invocation.md §4]

## Acceptance Criteria Quality — Measurability

- [x] CHK047 Is the cross-distribution identical-resolution criterion measurable by execution across a defined fixture set rather than by inspection? [Measurability, Spec §SC-007]
- [x] CHK048 Is the auto-detection criterion tied to an enumerated fixture set covering both the planning-incomplete and planning-complete conditions? [Measurability, Spec §SC-004]
- [x] CHK049 Is the rejection criterion measurable against a closed case set, so "every invalid argument" is bounded? [Measurability, Spec §SC-005, plan.md §6]
- [x] CHK050 Is the no-gate-behaviour-change criterion falsifiable, given this change edits a gate's stop guidance and a synopsis line? [Measurability, Spec §SC-008]

## Dependencies & Assumptions

- [x] CHK051 Is the assumption that both orchestrators can execute the shared resolver stated, since a fail-fast argv rejection is unreachable on a platform that cannot run it? [Assumption, Spec §Assumptions]
- [x] CHK052 Is the downstream consumer set identified, so a change to this surface has a known blast radius? [Dependency, Spec §Dependencies, contracts/stage-invocation.md preamble]
- [x] CHK053 Is the dependency on regenerated distribution mirrors and installed-cache proofs stated, given both distributions' skill bodies are edited? [Dependency, Spec §Assumptions, §Reviewability Notes]

## Notes

**All 53 items evaluated; 53 marked complete. 45 passed as-written, 8 were
remediated. 0 outstanding.**

Those 8 remediated items cover **6 distinct defects** — CHK013 and CHK014 are two
readings of one vocabulary defect, and CHK022 and CHK045 are the contract and
plan halves of one mis-sited step. Every defect was raised against requirement or
contract *text* that was wrong, incomplete, or self-contradicting — none against
the design. Each carries a `Resolved` tag naming the artifact that closes it:

| Item(s) | Defect | Closed by |
|---|---|---|
| CHK022, CHK045 | The contract sited the Codex resolver step in `references/phase-execution-codex.md`, which opens at the main execution loop and has **no opening-preparation section**. Step 0.6b — the step it claims to match — is in the Codex skill body. A rejection sited as written would run *after* phase work began, satisfying neither FR-007 nor SC-005. The plan's word-cap budget also counted only two edits into the capped body. | contracts/stage-invocation.md §3 (correct site + the reason it cannot be a reference file); plan.md §4 (third edit declared, budget restated ≈54 of 329) |
| CHK023 | The exit-code table folded a path outside the trust boundary into exit 2. That condition is a request-layer `unsupported_path` diagnostic that never reaches the helper and has no exit-code entry at all; exit 2 maps to `invalid_input`. Golden fixtures written to the table would assert a code the runner never emits. | contracts/stage-invocation.md §Exit codes (request-layer diagnostics split from process exit codes) |
| CHK013, CHK014 | "Stated once… not restated per platform" was contradicted by the same document, which restates the vocabulary in both synopsis blocks and both rejection messages, as does the chain contract. No copy was identified as a copy, and nothing tied them to the source. | contracts/stage-invocation.md §Stage vocabulary (normative source named; copies marked as copies; pinned to the FR-015a rejection-case coverage and the status-evidence literal assertion) |
| CHK006 | The contract's Claude block carried a third difference from the shipped line — the `/speckit-pro:speckit-autopilot` command token — while declaring "two additions". Three renderings of the Claude invocation existed across two contracts and the skill body. | contracts/stage-invocation.md §1 (argv-received versus user-facing invocation distinguished; parity scoped to the flag set) |
| CHK039 | FR-011's premise cites "the existing pre-final audit" as though shared. That audit is Codex-only; the Claude distribution ships no completion audit, so the justification was vacuous on one of the two platforms it governs. | Spec §FR-011 (audit attributed to Codex; constraints (a) and (b) identified as the cross-distribution ones, since both derive from the shared guard) |
| CHK015 | The chain contract handed ART-011 six terminal-status literals to build against, a fourth uncontrolled copy of a vocabulary the shipped guard owns. | contracts/scaffold-autopilot-chain.md §4 (set attributed to `WORKFLOW_TERMINAL_STATUSES`; ART-011 directed to read the shipped set) |

The remaining 47 were evaluated and found already satisfied. They are checked
because they were *evaluated and passed* — an unchecked box would read as "not
verified" and understate the coverage.

**Prose-only probe result.** The domain prompt asked specifically for rules that
exist only as prose on both sides. Four of the six gaps are that class, and they
share a shape worth naming: the contract document written to *be* the single
source of truth had itself accumulated per-platform copies (CHK013), a
mis-sited platform-specific step (CHK022), an unnamed platform-specific
rendering difference (CHK006), and a platform-specific justification presented
as shared (CHK039). The divergence vector this specification exists to close was
reproducing inside the artifact meant to close it. Three of the four are now
pinned to something executable — the FR-015a rejection cases, the status-evidence
literal assertion, and the shared phase-coverage guard — rather than to review.

**Verification provenance.** Every behavioural claim behind the six gaps was
confirmed by reading shipped source, not by inference: the runner's exit-code map
and `unsupported_path` diagnostic (`read_only.py`), the guard's exact-name
matcher and its case-insensitive `pending` check
(`validate-autopilot-phase-coverage.py`), the Codex Step 0.6b site and the
heading structure of `phase-execution-codex.md`, the absence of a Claude-side
completion audit, and the `skipped:` precedent in `task-list-canonical.md`.
`file:line` citations for each appear in the executor's summary.

**Scope impact.** **+6 reviewable LOC (453 → 459)**, no new file, no new surface,
no new requirement. Four of the six fixes cost nothing to implement: the
vocabulary pinning (CHK013/CHK014) points at coverage plan.md §6 already
declares, the Claude argv clarification (CHK006) and the FR-011 attribution
(CHK039) only prevent wrong edits, and the terminal-status ownership note
(CHK015) directs ART-011, which is out of this slice. Two carry lines: the Codex
Step 0.6c bullet relocating into the capped skill body (≈4 lines of skill-body
markdown at a site the plan had not counted as a distinct edit), and the two
request-layer diagnostics the unit test must now assert separately from exit 2
(≈2 in fixtures). Budget posture unchanged: warn on LOC (459 against 400 warn /
800 block) and on file count, block on neither. Recorded at plan.md
§Reviewability governance.

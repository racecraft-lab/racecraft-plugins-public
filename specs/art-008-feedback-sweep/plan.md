# Implementation Plan: Feedback Sweep, slice 1 of 2 — the checkpoint

**Branch**: `art-008-feedback-sweep` | **Date**: 2026-08-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/art-008-feedback-sweep/spec.md`

## Summary

The implement stage opens with a feedback sweep. Before any task work it reads
the draft pull request the plan stage left behind, keeps only comments from
write-capable authors, recognizes artifact-exported blocks by registered lead
sentences, gives each comment exactly one class, routes only `amended` through
a sweep-local consensus sequence, records every handled comment in a Feedback
Sweep Log, replies once per comment, and then stops for re-review or proceeds.

The technical approach splits along the line the repository already uses for
`resolve-autopilot-stage`: **the orchestrator observes, one read-only runner
helper classifies, and the orchestrator decides.** The helper takes the raw
`gh` observation as data, applies the author-association allowlist, matches the
export registry, and returns a closed-vocabulary envelope. It never runs `gh`,
never touches the network, and never assigns a class. That keeps the security
boundary and the determinism guarantee inside a fixture-pinned Python surface
while leaving consensus routing, commits, and replies where they can only be
orchestrator work.

**Assigning the class is no longer one of them.** The orchestrator holds
`Bash`, and the rule this slice now enforces is that no agent holding `Bash` or
the network reads reviewer text. Classification therefore moves out of the
orchestrator entirely, into `sweep-classifier`, a harness-scoped agent that
receives one sanitized, delimited block and returns a structured record. The
three amendment perspectives and their synthesis move to `sweep-analyst`,
scoped the same way. Both ship on both platforms and are used only by this
sweep. What the orchestrator handles afterwards is an enum, a target, a
byte-capped reason, and a structured edit — never a body.

## Trust Boundary Enforcement

This feature carries public pull-request text into agents that edit the planning
artifacts, so the trust boundary is the design, not a caveat on it. Seven
mechanisms implement it. Each names where it runs, because "enforced in the
helper" and "expected of the orchestrator" are different guarantees and the
distinction is the point.

**1. The allowlist runs in the helper, ahead of everything.** `sweep-pr-feedback`
applies the FR-005 author-association filter itself and returns `candidates` and
`excluded`. The candidate records carry id, surface, author, association,
truncation flag, and export metadata — and **no body**. An untrusted comment's
text is therefore absent from the helper's output by construction, not by an
orchestrator remembering to drop it. This is the placement the spec's own
security posture requires: the filter is a fixture-pinned Python surface, so it
is provable, while orchestrator judgment is not.

**2. Classification consumes the candidate list and nothing else.** The
orchestrator holds the full observation it captured, untrusted bodies included,
so the helper's filter is only as good as what the orchestrator does next. The
rule: the classification loop iterates `candidates`, and a body is read out of
the captured observation **only for an id present in that array**. No path
enumerates the observation directly. Without this, mechanism 1 filters an
envelope while the orchestrator reads around it — the filter would be real and
bypassed at the same time.

**Amended by the consumer-scoping pass: the orchestrator no longer reads a
body at all.** The `gh` read is piped straight into the runner —
`gh ... | python3 -m speckit_pro_runner`, with the orchestrator supplying only
the wrapping envelope — so the unredacted observation never lands on disk and
never enters the orchestrator's context. Because the runner is stateless and
that invocation is the only place a raw body exists, the analyst-payload leg
runs **inside** it, once per dispatched candidate, and its response carries the
bodiless candidate records, each candidate's shaped block, and each candidate's
shaping report together. The orchestrator is a **conduit** for a block: it
hands each one to `sweep-classifier` unchanged, and for an amended item to the
analysts, and no path asks it to read one. The rule above therefore no longer
bounds which body the orchestrator reads. It bounds which ids get a sanitized
block at all: the leg runs only for an id present in `candidates`, and no other
id produces one. **This is construction, not enforcement.** The orchestrator
still holds `Bash` and could run `gh` for itself; nothing in the harness stops
it. What the design guarantees is that no path it is told to take puts a body
in front of it, and item 7 carries that residual rather than dissolving it.

**3. The recognized-export payload (FR-007e).** For a recognized comment the
consensus payload is the helper's export record plus the body with every matched
registered line removed. The remainder is delimited and labelled as
reviewer-supplied data rather than concatenated as instruction. That labelling
is a model-layer control — the strongest thing available inside a prompt, and
still probabilistic — and nothing deterministic stands behind it on this path.
Mechanism 1 classifies deterministically; mechanism 2, which decides what is
forwarded, is orchestrator prose checked against FR-008b's second fixture. There
is no deterministic boundary on the forward path, and FR-007e says so rather
than letting the allowlist be read as one. Tagging without removal does not
satisfy FR-007c; that reading is available from FR-007c's wording and is the one
this plan forecloses.

The labelling half is new work, not an existing guarantee this slice inherits.
The shipped Gap Remediation prompt template in `consensus-protocol.md` is a bare
`## Gap Description` heading over an inserted-text placeholder, with no
delimiter and no "treat this as data" instruction, and the three analyst
definitions describe their input as "the relevant context" — trusted framing.
The analysts' `disallowedTools` frontmatter denies the built-in write tools but
says nothing about `Bash` or about the input, and the grounding note governs
their **output**; what that frontmatter does and does not bound is item 7. So a
sweep that hands a reviewer body to that template inherits raw interpolation.
The sweep supplies its own delimiting rather than assuming the protocol does it.

**The consumer is now scoped, which is a deterministic control on the reader
even though the labelling stays probabilistic.** The delimited block is read by
`sweep-classifier` and `sweep-analyst`, whose Claude frontmatter pins
`tools: Read` and `tools: Read, Grep, Glob` and whose Codex definitions pin
`sandbox_mode = "read-only"`. A model that ignores the frame still cannot shell
out, fetch a URL, spawn a sub-agent, or write a file, because those tools do
not resolve for it. That does not make the labelling stronger; it bounds what
follows from the labelling failing, which is a different guarantee and the one
item 7 previously said this design did not have.

**Shaping applies to every forwarded body, not only a recognized one, and it
is code (FR-007g).** FR-007e specifies the payload for a recognized comment,
and the common case is the opposite: only `amended` reaches consensus, and most
`amended` comments match no registered sentence. Every body therefore passes
through the **analyst-payload leg of the redaction surface** — the second named
surface of `sweep-pr-feedback`, beside the checks T004 settles — before an
analyst sees it. The surface takes the capture-truncated body as captured, the
comment id, and the parse's own `truncated` flag and `matched_lines` for that
comment, and returns one delimited block plus a report. Inside it the order is
fixed: normalize line endings; bound at the 8192-byte budget `data-model.md`
fixes, a no-op on a conforming input; replace matched registered lines in
place; one left-to-right span scan in which the earliest opener wins, spans do
not nest, and an unclosed opener runs to the end of the body; then frame and
label with the comment id. Placeholders stand inside the frame and are
bounded, the info-string echo at 32 bytes. The report and the statement line
both carry the truncation and the count of spans withheld, so the analyst
knows it is reading a reduced body and the disposition can say so to the
reviewer. The orchestrator's whole part is the call and the two-part assembly
— block beside the export record for a recognized comment, block alone for an
ordinary one — which is what the two phase-execution references document.

This does not disturb mechanism 1. FR-008b's first assertion is about the
parse envelope, and candidate records still carry no body; the surface is
networkless and write-less, receives one body at a time, and only ever for an
id the orchestrator was entitled to read under mechanism 2. Registration stays
one operation, and production files stayed seven through this pass —
superseded by the consumer-scoping pass, whose count lives in the superseding
note under Reviewability below and in `spec.md`'s second Reviewability Budget
superseding note. What the surface proves is the
payload's shape. It does not decide whether a body is forwarded — that is
mechanism 2's orchestrator prose, and nothing deterministic stands on the
forward path — and it does not make the analyst honour the frame, which is a
model property. The earlier claim that shaping "adds no Python" is withdrawn:
a rule nothing executes has no fixture that can fail, which is the defect the
producer exists to close.

**4. The edit surface is an allowlist, checked twice, and what crosses it is
redacted once (FR-012b, FR-012f).** At classification, a requested change
outside `spec.md`, `plan.md`, and `tasks.md` in the feature directory takes
`deferred` with the refused target named in the disposition and the reply. At
the write, the resolved target path is validated against the same three-entry
set in code before any write; a violation stops the run. That stop reports like
the others this feature defines: it names the refused target path, the comment
id it came from, and the resume path, so the operator can tell a mis-routed
amendment from a broken tool. FR-017 and FR-019 both fix a report shape for
their stops, and a stop without one would be the only silent halt in the sweep.
The two checks catch different failures — prose a mis-routed item walks past,
and a defect that would otherwise write outside the surface — so neither
replaces the other. The redaction pass is a third thing, not a third check: the
two checks bound **where** an amendment goes and it bounds **what** the sweep
carries outward. It runs in the helper as a named surface of
`sweep-pr-feedback`, it takes one body and a comment id and returns the
transformed text with a report, and it never refuses a write. Every line an
amendment adds, every Feedback Sweep Log cell, and every reply body goes
through it before it is written, a deny-set hit is replaced in place by a
placeholder naming the rule class, and the event is recorded in the run report
every run produces (FR-018a). The row is always written and the commit always
taken, which is what keeps FR-006c's convergence invariant intact: a refusal
here would discard the row, leave the comment in the work set, and regenerate
the same hit on every re-run. A run that fired any event then stops once every
write has landed, under FR-012f, in FR-017's report shape: the redacted text
is already public, and the stop puts a human in front of the report before
task work. The next run finds the rows and replies in place, fires no event,
and proceeds, so the stop costs no convergence.

This fills a repo-wide hole rather than restating a local rule. The consensus
synthesizer's output contract accepts a free-form `File: <path>` and nothing
downstream validates it, and the three-artifact enumeration in
`consensus-protocol.md` is justified there by **write contention** — serializing
concurrent edits — not by scope safety. No allowlist, no "only these three
files" guard, and no rejection of an out-of-scope edit target exists anywhere in
the repository today. The shape to copy is
`speckit-pro/artifact-gallery/SPA-CONTRACT.md`, which already names
pull-request-derived values untrusted and answers the escaping question with
"the value goes somewhere else" rather than with a quoting rule. That contract
is scoped to generated HTML; this is the same discipline applied to an edit
target.

**Staging, and the `git add -A` hazard.** Each amendment commit stages exactly
the one artifact path it amended, never a directory. The precedent is the
`Draft PR` bookkeeping commit in `phase-execution.md`, which stages the workflow
file alone because the directory "also holds untracked run byproducts that a
directory-wide add would sweep in". The hazard is specific and easy to miss: the
sweep is a **Phase 7 setup step**, and Phase 7 is the one phase whose existing
commit path uses `git add -A`. An amendment commit that inherits that pattern
would stage the entire worktree, which defeats the edit-surface allowlist at the
last step — the check would pass on the target path while the commit carried
everything else. Amendment and bookkeeping commits here follow the enumerated
single-path form, not the Phase 7 form.

The hazard has a second face the single-path rule does not cover. Phase 7's
own `git add -A` runs **after** the sweep, over whatever the sweep left in the
worktree, and the sweep leaves files. It leaves fewer than it did: the helper
request is **piped** rather than written, so the document carrying every
observed body no longer exists as a file at all, which is a stronger control
than ignoring it and is why the pipe is specified rather than left to the
implementation. What remains is the reply body files FR-004b forces onto disk,
the outbound-leg request files, and the captured commands. FR-004d is the
control. Every such file lives
under `specs/<feature>/.process/feedback-sweep/`, and the sweep's first write
into that directory is a `.gitignore` of its own containing `*`, so the
directory ignores itself in whatever repository the worktree belongs to and
`git add -A` cannot stage it. That placement matters because the sweep ships
in `phase-execution.md` and runs in consumer repositories whose root
`.gitignore` knows nothing of this directory; a control that lived only in
this repository's configuration would protect only this repository. This
repository's root `.gitignore` carries the entry as well, as belt and braces.
The sweep removes the directory before it proceeds or stops. The precedent is
the pull-request packet directory, excluded today through `.git/info/exclude`,
which a fresh clone does not carry; that is prior art for the shape and not
for the mechanism. Four fixtures pin it: a scratch repository with no root
ignore in which `git add -A --dry-run` stages nothing under the directory,
this repository's `.gitignore` line present, every byproduct path in every
captured command under the directory, and the run report naming the directory
as removed.

No check reads the staged diff back for a second path. Single-path staging is
a convention rule 2 does not verify at the commit, so an inherited `git add -A`
is warned about here rather than caught, and FR-012f's redaction pass does not
change that: it transforms the lines an amendment adds, not the paths a commit
touches.

**5. `self_login` is derived, then validated.** The orchestrator reads it from
the live authenticated session at call time rather than from configuration, the
way FR-004a requires the author-association field be read fresh. The helper then
requires it to be a non-empty string after stripping surrounding whitespace;
absent, empty, or whitespace-only returns `invalid_input` rather than
proceeding. The helper cannot go further than presence, because its contract
forbids it from reaching the network, so it has no second independently sourced
value to compare against — verification is provenance, not checking.

What an empty value actually breaks, stated correctly: comparison is exact, so
an empty account matches **no** real comment author. The author condition is
permanently false, the conjunction is therefore always false, and **no comment
is ever excluded as a self-reply**, including the sweep's own. That reaches the
same non-convergence FR-006a describes, but by disabling the rule rather than by
narrowing it to the marker half. The distinction matters because the two
failures have opposite shapes and a reader expecting the wrong one would test
for the wrong thing.

**6. The shell boundary is verified in both directions.** FR-004b covers reads
and writes, so the captured-command fixture SC-009 rests on captures the **read**
argv as well as the reply writes. Quickstart Scenario 4 pins the reply half;
without the read half, "every command the sweep issues" is asserted against a
fixture that inspects some of them. The helper never runs `gh` at all, and the
request reaches it as one JSON document on stdin, so no field of it is ever a
shell argument.

**7. Every agent that reads reviewer text now carries a closed read-only
allowlist; the orchestrator does not, and is never handed a body.** This one
runs in the agent harness rather than in this repository's code, and this slice
sets it rather than inheriting it. Two agents read reviewer-derived text and
nothing else does:

- **`sweep-classifier`** receives one sanitized, delimited block — the FR-007g
  output, handed over unchanged by an orchestrator that never reads it — plus
  the closed class vocabulary, and returns `{class, target, reason}`: the class
  from the four-value vocabulary, the target from the three-file allowlist or
  `null`, and a reason bounded at 512 bytes. Claude frontmatter pins
  `tools: Read`, which is the narrowest allowlist a subagent can carry, because
  the runtime refuses a subagent that resolves zero tools; the implementation
  task verifies whether an explicitly empty list is accepted and tightens to it
  if so. `disallowedTools` names `Agent`, `TeamCreate`, `SendMessage`, and
  `Skill`. Codex pins `sandbox_mode = "read-only"`.
- **`sweep-analyst`** pins `tools: Read, Grep, Glob` and the same denials, with
  the same Codex sandbox. It is dispatched three times per amended item with
  the perspective — codebase, spec-context, domain — supplied **in the
  prompt**, and once more in a synthesis prompt, and returns a structured edit
  `{file, anchor, replacement}` whose `file` is one of the three artifacts and
  whose `replacement` is byte-capped.

Both structured returns cross the FR-012f redaction surface before any use: the
classifier's `reason` before the orchestrator acts on it or writes it, the
analyst's `replacement` before the write. So what leaves an untrusted-text
reader is an enum, a path from a closed set, and bounded text that a
fixture-pinned Python surface has already transformed.

**Synthesis is performed by `sweep-analyst`, not by `consensus-synthesizer`.**
The synthesizer declares no `tools:` allowlist and inherits `Bash`, so routing
sweep synthesis to it would reopen F-1 one hop downstream, on text three
analysts have just concatenated. Naming this is the point: the natural reuse is
the wrong one.

**What the Codex side can and cannot claim.** The loader reads exactly two
fields — `name`, which must equal the filename stem, and `model`
(`speckit-pro/speckit_pro_runner/helpers/install.py:319-338`) — and copies the
rest byte-for-byte. Layer 1 `validate-codex-agents.py:132-134` forbids the
Claude-only keys outright, so a Codex agent definition **cannot** carry `tools`
or `disallowedTools`; `sandbox_mode` is the only lever. No `network` field
exists anywhere: not in the loader, not in a shipped definition, not in the
Layer 1 or Layer 5 validators. The corpus manifest's `"network":"restricted"`
is a descriptor of a qualification run, read back from nothing. The Codex claim
is therefore exactly **"read-only filesystem; network per Codex defaults"**,
and nothing stronger. `speckit-pro/codex-skills/install/SKILL.md:53-62` adds
the limit that matters: `sandbox_mode = "read-only"` does not sandbox MCP
server processes, so a write-capable MCP server must be curated out at the
profile or config level, which is operator territory this plan does not reach.

**The Layer 5 policy change, and why it is scoped to two names.**
`tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py:163-178`
asserts that **every** Claude agent definition carries no `tools:` line, with a
message reading "pins a tools: allowlist - availability is operator-owned; use
disallowedTools for role denials only". That rule is right for an agent acting
on trusted input, where the operator owns availability, and wrong for an agent
reading attacker-controllable text, where availability is the exposure. The
validator gains one tuple,
`UNTRUSTED_INPUT_CONSUMERS = ("sweep-classifier", "sweep-analyst")`, and three
assertions: members are exempt from the no-allowlist rule; each member pins
**exactly** its stated allowlist, so adding a tool fails; and the tuple's
membership is asserted exactly, so adding an open executor to it fails.
Members also deny the orchestration set and `Skill`, asserted in the
`READ_ONLY_ROLES` style. The rationale goes in the module docstring, because a
carve-out whose reason lives only in a spec is a carve-out the next reader
widens. **This is the only policy change**, and it changes no existing agent
definition: the twelve governed Layer 6 roles are untouched, so the digest
chain does not restale.

**What this does not fix, stated as a residual.** The orchestrator remains a
model with `Bash`, the network, and every installed MCP server. It is never
handed a body — the read is piped, the shaped blocks pass through it unread,
and the classifier returns an enum — but that is a property of the path it is
told to take, not a capability it lacks. A divergent orchestrator can run `gh`
for itself. **This slice moves the untrusted-text reader inside a closed
allowlist and leaves the untrusted-text router outside one.** That residual is
smaller than the one this item previously recorded, and it is not zero. The
earlier prerequisite sentence is withdrawn as taken: the policy reversal is the
carve-out above, taken deliberately at the Layer 5 test, and the Layer 6 corpus
is deferred rather than reversed (see the Non-Goals entry the spec adds).
**FR-005 relaxation is still blocking.** The author-association allowlist is
what keeps this text to text a write-capable account posted; admitting
`CONTRIBUTOR` would put anonymous text in front of these agents, scoped or not.

**Where the sweep's dispatch sits, and what it leaves untouched.** The sweep
carries its own dispatch inside its own Phase 7 setup block, in
`speckit-pro/skills/speckit-autopilot/references/phase-execution.md` ahead of
"Phase 7 Setup: Open the Implementation-Notes Record", and in
`speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`
ahead of "Open the implementation-notes record before the first task is
dispatched." That block names `sweep-classifier` once per candidate and
`sweep-analyst` three times plus once for synthesis per amended item, by name.
It never emits a category-tagged "Unresolved for consensus" item, so
**`consensus-protocol.md`'s Category-Routed Dispatch routing table is never
consulted and is not edited** — and note the precision: the routing table is
untouched, while `consensus-protocol.md` itself stays MODIFIED in the block
below for the `Sweep` `Type` value alone. Clarify, Checklist, and Analyze keep
routing through that table to the three shared analysts with synthesis by
`consensus-synthesizer`, unchanged in behavior and unchanged in file. The seam
is the dispatch site, not the protocol.

**What these do not claim.** None of the seven inspects a trusted body for
adversarial content, and none is a permissions check. FR-012f is not a
counterexample: it transforms what the three outbound legs carry, not what a
comment carried in, and it names five secret shapes and an over-bound line
rather than judging intent. The trust unit is the comment, recorded in the
spec's Assumptions: a write-capable author who quotes untrusted text is treated
as endorsing it, and quoting is the expected route for untrusted text rather
than an edge case. The number to reason with is the adaptive one: published
injection-resistance figures sit near a tenth of a percent against a single
attempt and rise to five or six percent against roughly a hundred adaptive
ones, and a public pull request is an unbounded retry surface. Relayed text is
how attempts arrive — a bug report, an issue, a support thread that a
maintainer pastes into a review comment as ordinary triage — so each relay is
an attempt, and nothing in this design counts or limits them. Mechanism 3
keeps a known imperative out of an analyst prompt, and mechanism 4 bounds what
an analyst outcome can reach through the orchestrator; item 7 now bounds what
the reader of that text holds, so an attempt that survives the frame reaches an
agent with three read tools rather than a shell. What it does not bound is the
orchestrator that routes the text, and that residual stands as a residual: this
plan does not call it tolerable.

**Budget note.** These add an estimated 15 to 30 reviewable lines over the table
below: the path check and `self_login` validation are small, and the rest is
reference prose. The high end moves from 745 toward roughly 775 against the 800
block. That margin is thinner than the table states and is recorded here rather
than absorbed silently. Superseded: the live figure's one home is `spec.md`'s
Reviewability Budget superseding note.

FR-012f and FR-007g add more than the item-7 line above, and what they add is
code: the two share one named surface of `sweep-pr-feedback` that takes one
body and a comment id and returns the transformed text with a report. The
line-item derivation — the deny-set and replacement loop, the span scan and
delimiter, the surface's validation and dispatch, and the orchestrator prose in
both phase-execution files — lives in `spec.md`'s Reviewability Budget
superseding note at **110 to 170 reviewable lines**, none of it fixture or test.

**Item 7 no longer adds zero.** It was disclosure of frontmatter this
repository did not set; it is now two agent definitions on two platforms, an
inventory line in the Codex installer, the dispatch wiring in both
phase-execution references, and the Layer 5 carve-out. That is **415 to 640**
reviewable lines and **five** more production files, derived line by line in
`spec.md`'s second superseding note and summarized under "The consumer-scoping
pass moves this again" below. **Production files move from 7 to 12, which
crosses the 8-file block.** Both crossings are size-family and both are
operator-accepted; neither is restated here.

## Failure Paths

The sweep reads a live pull request, edits artifacts, commits, pushes, and
writes back to a reviewer, so it has five places to fail partway. Two design
decisions cover all five, and both are placement decisions rather than new
mechanism.

**One report builder, not one per stop.** FR-020 fixes a single contract —
condition, what landed, resume path — and every stop calls it. This is the
consolidation the spec needed anyway: nine stop conditions have accumulated with
their reports described one requirement at a time. Building the report once, from
the run state the orchestrator already holds, is fewer lines than nine
hand-written wordings and is the only way the what-landed part stays accurate,
since no individual stop knows what the ones before it did.

**Reads are one transaction; writes are ordered so that stopping is safe.** All
reads precede all writes, so FR-004c's discard-on-failure needs no unwind path —
there is nothing to unwind. The write side is ordered at two levels, and keeping
them apart is what makes the failure states exact. **Per amendment**, FR-012a's
existing ordering does the work: amendment commit, push, then bookkeeping
commit, repeated once for each amendment the run makes. **Replies are not part
of that cycle.** FR-015c fixes them at one point per run — after every
bookkeeping commit the run takes has landed — so the sequence is the whole
commit cycle first, replies once at the end. A stop between any two writes
leaves a state the next run reaches by a route the spec already reasons about,
so no failure needs a repair rule of its own; and because the reply point sits
after the entire commit cycle, a run that aborts inside that cycle has posted
zero replies rather than some, which is what makes the composed interrupt case
a single determinate outcome instead of two.

The one exception is the reply, which lands after the row that would otherwise
suppress it. FR-015b closes that with the marker already required by FR-015 and
already matched by FR-006 — it now carries the answered comment's id — so the
pull request itself witnesses which replies exist. No log column, no state file,
and the FR-006 anchor is unchanged because the id follows the fixed prefix.

**Budget note.** These add an estimated 35 to 55 reviewable lines: the report
builder and the reconciliation read are the substantial parts, and the remaining
stops are two or three lines each once the builder exists. Against the 775 high
end recorded above, the high end now reaches roughly **810 to 830, which crosses
the 800 block**, while the midpoint stays under it. That is a threshold crossing
rather than a thinner margin, and it is flagged for the operator rather than
absorbed: the levers are the serialization-family deferral already described
under the split option, accepting the block explicitly, or re-slicing. This plan
does not choose among them.

**Superseding note: the live figure lives in the spec.** The 810-to-830 figure
above is left as written because it records what was true when this paragraph
was. Three later passes moved it: the artifact verification repair recorded in
the workflow file, for **595 to 910**; the trust-boundary remediation, which
made FR-012f and FR-007g into helper code, for **705 to 1080**; and the
consumer-scoping pass, which ships `sweep-classifier` and `sweep-analyst` on
both platforms and carves them out of the Layer 5 no-allowlist rule.
`spec.md`'s Reviewability Budget superseding notes derive both deltas line item
by line item — **110 to 170** and **415 to 640** reviewable lines — for a live
figure of **1120 to 1720, midpoint near 1420**. Those notes are the figure's
only home; this paragraph repeats them and does not re-derive them.
**Production files move from 7 to 12**: the redaction surface still lands
inside paths the Declared File Operations block already named, but the two
agent definitions, their two Codex mirrors, and the Codex installer's closed
inventory line are five new production paths. **The midpoint crosses the 800
LOC block and the count crosses the 8-file block.** Both are size-only, both
are recorded as operator-accepted, and T014's lever decision is taken against
this figure.

## Technical Context

**Language/Version**: Python 3.11+ standard library (runner helper); Markdown
(skill references). No new dependencies.

**Primary Dependencies**: `speckit_pro_runner` helper framework; the existing
consensus protocol's round structure, run here with the sweep's own scoped
analyst rather than through the category-routed table; `gh` CLI at the
orchestrator boundary only.

**Storage**: The workflow file is the sole store. No state-file mirror (FR-013).

**Testing**: `python3 tests/speckit-pro/run-all.py`. Layer 4 golden fixtures for
the helper; Layer 1 structural and Codex-parity validation for the references
and the two sweep agent definitions; Layer 5 tool-scoping validation for the
`UNTRUSTED_INPUT_CONSUMERS` carve-out.

**Target Platform**: Claude Code (`speckit-pro/skills/`) and Codex CLI
(`speckit-pro/codex-skills/`), identical behavior (FR-003, SC-007).

**Project Type**: Plugin source — a read-only runner helper plus skill
reference documentation. No application tier.

**Performance Goals**: N/A. The sweep is a once-per-stage setup step bounded by
pull-request size, not a throughput surface.

**Constraints**: No new Bash and no `jq` (constitution II). `shell=False` and
argument arrays throughout. No comment text may reach a shell argument in
either direction (FR-004b, SC-009). Each comment body truncates at a fixed byte
budget below the runner's 32 KiB bounded-input limit, because that limit
rejects the whole request rather than the offending string (FR-008).

**Scale/Scope**: One new read-only helper operation, two new agent definitions
shipped on both platforms, twelve modified or new production files, nine test
and fixture files, and one repository-configuration line in `.gitignore`. Two
platform variants.

**Reviewability Budget**: harness/adapter (single primary surface);
**hand-derived 515 to 830 reviewable LOC, midpoint near 630, at the time this
line was written, since superseded twice** — the live figure has one home,
`spec.md`'s Reviewability Budget superseding notes, repeated in the Failure
Paths superseding note above, and it reads **1120 to 1720, midpoint near
1420**, crossing the 800 block at the midpoint; **12 production files**,
crossing the 8-file block; **22 authored files total**, over the warn of 15 and
under the block of 25; **block on production files, block on reviewable LOC,
warn on authored files, both blocks size-only and operator-accepted.** Derived
by hand from the Declared File Operations block below, because the estimator
cannot measure this slice. See "Reviewability Budget, derived by hand".

## Declared File Operations

The plan-phase reviewability estimator (`estimate-reviewable-loc.sh`) parses this
block to project the slice's production-LOC footprint before `tasks.md` exists.
List one entry per file on its own line, each starting with a `- ` list marker:
`- NEW <repo-relative-path>` for a new file or `- MODIFIED <repo-relative-path>`
for an existing one.

Production surface (authored, reviewable):

- MODIFIED speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED speckit-pro/skills/speckit-autopilot/references/phase-execution.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/workflow-file-protocol-codex.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md
- NEW speckit-pro/agents/sweep-classifier.md
- NEW speckit-pro/agents/sweep-analyst.md
- NEW speckit-pro/codex-agents/sweep-classifier.toml
- NEW speckit-pro/codex-agents/sweep-analyst.toml
- MODIFIED speckit-pro/speckit_pro_runner/helpers/install.py

Test and fixture surface (authored, verification):

- MODIFIED tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py
- MODIFIED tests/speckit-pro/unit/fixtures/read-only-helpers/fixture-manifest.json
- NEW tests/speckit-pro/unit/fixtures/read-only-helpers/requests/sweep-pr-feedback.json
- NEW tests/speckit-pro/unit/test-feedback-sweep-parse.py
- NEW tests/speckit-pro/unit/fixtures/feedback-sweep/comment-corpus.json
- NEW tests/speckit-pro/unit/fixtures/feedback-sweep/expected-envelopes.json
- MODIFIED tests/speckit-pro/suite-manifest.json
- MODIFIED tests/speckit-pro/unit/test-artifact-gallery.py
- MODIFIED tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py

Repository configuration (authored, not production):

- MODIFIED .gitignore

Generated surface (regenerate, never hand-edit, not counted as reviewable):

- MODIFIED dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED dist/claude/speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED dist/codex/speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py
- NEW dist/claude/speckit-pro/agents/sweep-classifier.md
- NEW dist/claude/speckit-pro/agents/sweep-analyst.md
- NEW dist/codex/speckit-pro/codex-agents/sweep-classifier.toml
- NEW dist/codex/speckit-pro/codex-agents/sweep-analyst.toml
- MODIFIED dist/claude/speckit-pro/speckit_pro_runner/helpers/install.py
- MODIFIED dist/codex/speckit-pro/speckit_pro_runner/helpers/install.py
- NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/agents/sweep-classifier.md
- NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/agents/sweep-analyst.md
- NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/codex-agents/sweep-classifier.toml
- NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/codex-agents/sweep-analyst.toml
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/helpers/install.py
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/helpers/install.py
- MODIFIED docs-site/src/content/docs/reference/agents.md

The `dist/` and installed-cache entries are byte-identical copies produced by
`python3 scripts/refresh-release-artifacts.py`. The spec's Assumptions section
already records that adding a read-only helper restales them and that
regenerating is required rather than optional. The reference `.md` files ship
into both distributions too and regenerate through the same script.

The five production entries the consumer-scoping pass adds are the two agent
definitions, their two Codex mirrors, and one line in the Codex installer.
`install.py` is not optional: `REQUIRED_CODEX_AGENT_NAMES`
(`speckit-pro/speckit_pro_runner/helpers/install.py:31-45`) is a **closed**
inventory, and a Codex agent definition that is present but unlisted returns
the `incomplete_agent_bundle` diagnostic with the file under `unexpected_files`
(`:302-311`), pinned by
`tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:424-441`. The
`artifact-author` agent is the precedent and the ripple map: it landed with a
one-line `install.py` edit and regenerated exactly the thirteen generated paths
listed above, including `docs-site/src/content/docs/reference/agents.md`. The
Claude side needs no registry edit — `validate-agents.py`'s `AGENTS` tuple is
closed at ten names and excludes `artifact-author` too — but Layer 1
`validate-capability-pointer.py:75-100` requires every non-excluded agent on
**both** runtimes to carry `capability-discovery.md`, `grounding.md`, and a
`Capability path:` line, and Layer 5's `test_session_shape_metadata` requires a
positive `maxTurns` and a non-empty `effort`. Both apply to the two new
definitions and both are implementation-task obligations, named here so they
are not discovered by failing.

The `.gitignore` entry is FR-004d's one line, `specs/*/.process/feedback-sweep/`,
which ignores the directory the sweep writes its transport files to. It is
authored and reviewed, so it counts toward the twenty-two authored files, and
it is not production, so it does not count toward the twelve.

### Two files deliberately absent from this block

`speckit-pro/skills/speckit-autopilot/SKILL.md` and
`speckit-pro/codex-skills/speckit-autopilot/SKILL.md` are **not** modified. The
spec's Reviewability Budget projected "8 or 9" production files partly because
"both `SKILL.md` files carry helper names today". Measured against the shipped
cap, that line cannot be taken:

- Layer 1 `validate-codex-skills.py` and `validate-skills.py` both assert a
  skill body of 500 to 8000 words.
- Measured with the validator's own `_body` helper, the Codex autopilot skill
  body is **7997 words — three words of headroom.** Any added line fails Layer 1.
- The Claude body is 6857 words and has room, but no test requires either
  `SKILL.md` to enumerate helpers. The Claude file's helper index is
  documentation, and the Codex file names `resolve-autopilot-stage` only in
  running prose.

Adding the helper to the Claude index alone would also put the two platform
documents out of step for no behavioral gain. The sweep is documented in the
phase-execution references, which is where the sequence lives. This removes two
files from the projected surface, which is why production files landed at 7
rather than 9 at plan time. They land at **12** now, and neither `SKILL.md` is
among them: the two agent definitions, their Codex mirrors, and the installer's
inventory line are new paths, not `SKILL.md` lines, and the Codex skill body
still sits at 7997 of its 8000 words. The two files stay absent for exactly the
reason recorded above.

## Reviewability Budget, derived by hand

### The estimator's verdict is an absent measurement, not a pass

`estimate-reviewable-loc` projects from production files only, and counts a file
as production only when its path sits under `src/`, `app/`, `lib/`, or
`scripts/`, or when it ends in a JavaScript, TypeScript, or SQL extension. Every
path in the block above fails both tests: the runner helpers sit under
`speckit-pro/speckit_pro_runner/`, and every reference is Markdown.

This was run against this plan rather than predicted. Verbatim output:

```json
{"tool":"estimate-reviewable-loc","status":"pass","projected":0,
 "declared_files":{"production":0,"new":4,"modified":20,"total_entries":24},
 "greenfield":false,
 "thresholds":{"warn":400,"block":800,"greenfield_multiplier":1.5,
               "base_warn":400,"base_block":800}}
```

Read it closely. The block parsed correctly — all **24** entries were seen, 4
new and 20 modified — and **`production` is 0**. The helper is not failing to
read the plan; it is reading it correctly and finding nothing it recognizes as
production code. `projected` is therefore 0, and `status` is `pass` against a
warn line of 400 it never had a chance to cross.

**That `pass` is an absent measurement and MUST NOT be cited as evidence the
slice is within budget.** The figures below are the measurement.

### Per-file derivation, anchored to shipped analogues

| File | Low | High | Basis |
|---|---:|---:|---|
| `read_only.py` — parse and report cluster | 200 | 250 | The nearest shipped analogue is the corroboration cluster at `read_only.py` lines 1292–1453: **162 lines** for a six-outcome classification over one supplied observation. This slice's parse does strictly more — CRLF normalization, per-comment byte truncation with a flag, whole-line matching across a ten-line window, an eight-value association filter, the anchored-marker-plus-author self-reply test, and a reasoned exclusion list. |
| `read_only.py` — export lead registry | 40 | 55 | 14 lead sentences (7 note-payload templates × 2 kinds), 6 distinct empty-export sentences, and header identities for the 3 serialization-family templates, each entry carrying template id and kind. The sentences are long literals that wrap in this file's style. |
| `read_only.py` — registration touch points | 5 | 8 | Allowed-inputs map entry (near line 256), argument-derivation branch (the `resolve-autopilot-stage` branch near line 341 is 10 lines), dispatch-table entry (near line 4466). |
| `registry.py` | 8 | 10 | One `HelperEntry`, matching the `resolve-autopilot-stage` shape at lines 181–188. |
| `phase-execution.md` | 110 | 170 | The Phase 7 Setup block this precedes is **34 lines**; the corroboration-status explainer it reuses is **57 lines**. The sweep sequence carries the substance of both, plus stop-or-proceed, per-amendment commit and push, two log writes, replies, and four-cause stop reporting. |
| `phase-execution-codex.md` | 90 | 150 | Codex references run roughly 70% of their Claude counterparts (59,990 against 84,310 bytes). |
| `workflow-file-protocol.md` | 40 | 60 | The nearest analogue is the `Draft PR` entry at lines 62–120: **58 lines** of grammar, examples, and rules for one workflow-file entry. The Feedback Sweep Log entry adds an eight-column table, pipe and newline escaping, and the unresolvable-author rule. |
| `workflow-file-protocol-codex.md` | 15 | 30 | The entire Codex protocol file is 90 lines, so its entries are far more compressed. |
| `consensus-protocol.md` | 5 | 12 | The fourth `Type` value in the row schema at line 617, plus the sweep-row escape-rate note. |
| **Total** | **513** | **745** | Midpoint **≈ 630** |

Stated as **515 to 745, midpoint near 630** — the low column sums to 513 and
was carried forward rounded to 515, the figure the other documents' plan-time
bullets still carry as history.
This is the derivation as it stood when the plan was written. Later passes have
moved it; the live figure has one home, `spec.md`'s Reviewability Budget
superseding note, repeated in the Failure Paths superseding note above.

### Corroborate or correct: this corrects the spec

The spec projected **325 to 485, midpoint near 400**. That range is **too low,
and this plan corrects it upward.** Two anchors in the spec's own bottom-up
derivation were measured against the wrong shipped precedent:

1. The spec anchored the parse at "the corroboration classifier is 35 lines".
   35 lines is the body of `corroborate_draft_pr` alone. The behavior it
   actually compares against — the closed vocabulary, the record builder, the
   three observation validators, and the classifier — is **162 lines** in this
   file's comment-dense house style. Anchoring on the function body alone
   undercounted by roughly a factor of four.
2. The spec allowed "15 to 25" for the workflow-file protocol entry. The
   `Draft PR` entry, the only comparable entry in that file, is **58 lines**.

The two phase-execution figures (70 to 110 each) are also low against a 34-line
setup block plus a 57-line status explainer for a sequence that carries more
than both, but that one is a judgment rather than a measurement error.

The spec's **production-file** count of "8 or 9" is corrected **downward to 7**,
for the `SKILL.md` cap reason recorded above. Superseded: the consumer-scoping
pass takes it to 12, derived in the subsection below.

### Budget result against the constitution thresholds

| Dimension | Value | Warn | Block | Result |
|---|---:|---:|---:|---|
| Reviewable LOC | ~1420 (1120–1720); ~630 (515–830) at plan time | 400 | 800 | **BLOCK at the live midpoint, size-only, operator-accepted** |
| Production files | 12 (7 at plan time) | 6 | 8 | **BLOCK, size-only, operator-accepted** |
| Total authored files | 22 (15 at plan time) | 15 | 25 | **WARN** |
| Primary surfaces | 1 | >1 | >1 | pass |

**Two size-only blocks and one warn now, two warns and no blocks at plan time.
The table above is the live position; the derivation tables earlier in this
section are the plan-time record.** Twenty-two authored files is seven over the
warn line, because the gate warns strictly above 15 (`reviewability-gate` in
`read_only.py` tests `total > 15`) and blocks only above 25. Twelve production
files is four over the 8-file block, which fires strictly above 8. The primary
surface stays one: the two agent definitions are authored role prose rather
than a second executable surface, and they are recorded under secondary
surfaces in the Constitution Check below so that judgment is visible rather
than assumed.

The live figure has one home, `spec.md`'s Reviewability Budget superseding
notes, repeated in this plan's Failure Paths superseding note and in the
subsection below: it crosses the 800 block at the midpoint and the 8-file block
at the count. Read those, not the plan-time tables, for the live figure.

The reason the margin matters is unchanged: the implementation must hold the
references to the sequence rather than restating the spec's rationale in them.

### The consumer-scoping pass moves this again

The operator chose to mitigate F-1 and F-2 inside this slice rather than
accept them as disclosed or defer them, recorded as Q13 in the design concept
and as an amendment in the workflow file. That decision is what put the two
scoped agents in the Declared File Operations block. Its delta is **415 to 640
reviewable lines** and **five** production files, derived line item by line
item in `spec.md`'s second Reviewability Budget superseding note, which is the
figure's one home. Summarized, not re-derived: the two Claude agent
definitions and their two Codex mirrors, anchored on the shipped agent files at
the measured 90% mirror ratio rather than the 70% reference ratio, are the bulk
of it; the installer's closed-inventory line is two to four; the dispatch
wiring in both phase-execution references is stated net of the
classification-loop prose and the category-routed dispatch instruction it
displaces; the classifier's reason crossing the FR-012f surface is five to
fifteen inside a file already declared.

Three things in this pass are authored and count **zero** reviewable LOC, named
so they read as counted-and-excluded rather than forgotten: the new planning
contract `specs/art-008-feedback-sweep/contracts/sweep-classifier-output.md`,
which follows ART-007's `artifact-author-agent` contract in
appearing in no count; the Layer 5 carve-out in
`tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py`; and the
captured-call fixture extensions. The plan's derivation table counts production
paths only, and this pass is counted the same way.

The live figure is **1120 to 1720, midpoint near 1420**, over **12** production
files and **22** authored files. Two blocks, both size-only, both
operator-accepted: the trust boundary is not separable from the feature, and
`docs/ai/specs/.process/PRSG-013-workflow.md:570` is the precedent for a
recorded size-only block whose run continued — `status=block,
is_size_only=true, reviewable_loc=1800, total_files=78`, 2.25 times over its
threshold, carried into marker planning. Read `spec.md`'s note, not this
summary, for the derivation.

**Every MUST in the carve-out has a fixture that can fail, named.** In
`tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py`:
`test_untrusted_input_consumers_pin_scoped_allowlists` reads `tools:` with the
existing `_yaml_field` helper and compares the comma-split value to `("Read",)`
for the classifier and `("Read", "Grep", "Glob")` for the analyst, so adding a
tool fails; `test_untrusted_input_consumers_membership_is_closed` asserts
`UNTRUSTED_INPUT_CONSUMERS == ("sweep-classifier", "sweep-analyst")` and that
the tuple shares no member with `OPEN_EXECUTORS`, so adding an open executor
fails; `test_untrusted_input_consumers_deny_orchestration_and_skill` asserts
the denials in the `READ_ONLY_ROLES` style; and
`test_untrusted_input_consumers_codex_sandbox_read_only` asserts
`sandbox_mode == "read-only"` on both Codex definitions. That last one is
deliberately **not** membership in `CODEX_READ_ONLY_ROLES`, which would drag in
that test's `gpt-5.5` and effort assertions this design never specified. Each
new method MUST be appended to `TEST_METHOD_ORDER` (`:49-59`), because
`build_suite` (`:357-361`) iterates only that tuple and a method absent from it
never runs — which is the failure mode of a carve-out that looks tested and is
not.

### The split option, if the operator chooses to re-slice

The warn is accepted rather than re-sliced, and the reasoning is stated so the
operator can overrule it.

**The one clean lever available** is deferring the serialization-family registry
rows — `feature-flags`, `prompt-tuner`, and `triage-board`, whose exports carry
no reviewer objections and no imperative addressed to an agent. Deferring them
saves an estimated **15 to 30 lines**. It does not reach 400, and it costs
FR-007b's "every shipped template that declares an export".

**No split reaches 400 while shipping a checkpoint that works.** The drivers are
the parse helper (245–313) and the two phase-execution references (200–320).
Those are the feature's irreducible core: a sweep without the helper cannot
classify, and a sweep without the references cannot run on either platform.

**The split that would technically fit is rejected on merit.** Slicing the read
path and the records into 1a while deferring consensus amendment, replies, and
stop-or-proceed into 1b would produce a checkpoint that reads feedback, records
it, and then walks into task work having acted on none of it. That is precisely
the "feedback becomes decoration" outcome this feature exists to remove, one
layer down. If the operator wants a smaller slice, the serialization-family
deferral above is the recommended lever; this one is not.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution version 1.2.0.

| Principle | Assessment | Gate |
|---|---|---|
| I. Plugin Structure Compliance | PASS. No new plugin component types. The helper joins the existing `speckit_pro_runner` surface; all new tests live under `tests/speckit-pro/`, outside the install-facing directory. | `run-all.py --layer 1` |
| II. Cross-Platform Runtime & Script Safety | PASS, and this slice tightens it. Python 3.11+ stdlib only, no new Bash, no `jq`, structured JSON parsing, `shell=False`, argument arrays. FR-004b forbids comment text in a shell argument in either direction, which is a **correction** to the nearest shipped precedent rather than a restatement of it. | `run-all.py --layer 4` |
| III. Semantic Versioning | PASS. No manual version edit; release-please owns the bump. | Layer 1 `validate-plugin` |
| IV. Test Coverage Before Merge | PASS. The new helper carries Layer 4 unit coverage, the golden-fixture corpus FR-008a pins, and a `suite-manifest.json` membership entry. | `run-all.py` |
| V. Conventional Commits | PASS. Amendment commits and the `chore:` bookkeeping commits FR-012a requires both follow `type(scope): description`. | CI `validate-pr-title` |
| VI. KISS, Simplicity & YAGNI | PASS with one judgment recorded below. | Plan and code review |

**Reviewability, per the preset's added obligations:**

- **Primary surface**: harness/adapter — the deterministic comment parse and its
  unit coverage. **Secondary surfaces**: docs/process — both phase-execution
  references, both workflow-file-protocol files, `consensus-protocol.md`, and
  the two sweep agent definitions on both platforms. The agent definitions are
  classified secondary deliberately: they are authored role prose that the
  harness reads, not a second executable surface, and recording the judgment
  keeps the primary-surface count at one honest rather than convenient.
- **Within budget?** No, and two of the three crossings are blocks. Block on
  production files (12 against a block of 8), block on reviewable LOC at the
  live midpoint (~1420 against 800), and warn on authored files (22 against 15,
  under the block of 25). Both blocks are size-only and both are
  **operator-accepted**: the trust boundary is not separable from the feature,
  because F-1 and F-2 are properties of the agents this feature dispatches, so
  a slice that ships the sweep without the scoped consumers ships the disclosed
  exposure and defers the fix behind the thing that creates it. The precedent
  for continuing past a recorded size-only block is
  `docs/ai/specs/.process/PRSG-013-workflow.md:570`, which recorded
  `status=block, is_size_only=true, reviewable_loc=1800, total_files=78` and
  continued with the crossing captured as marker-planning input; 1420 is under
  that 1800. Carried into marker planning under the spec's size-crossing rule,
  with the rejected split recorded above.
- **Split decision**: ART-008 is two stacked vertical slices along a Path seam.
  This is slice 1. Slice 2 (artifact freshness) is specified separately on a
  branch stacked on this one and owns page regeneration, stale-page detection,
  and the draft-description refresh.
- **PR review packet source**: `spec.md`'s PR Review Packet Requirements
  section, plus the traceability table in `quickstart.md`.

**The one KISS judgment worth recording.** One helper is registered rather than
two. Reading and recognizing could plausibly split into a read normalizer and a
registry matcher, but they share the ten-line window, the truncation budget, and
the normalization rules, and splitting them would put that shared state in a
third place. Three similar lines beat a premature abstraction; one operation is
the simpler shape. No Complexity Tracking entry is required.

**Post-design re-check.** Re-evaluated after Phase 1. The design artifacts
introduced no new violation: the helper stays Python 3.11+ stdlib and read-only,
truncation moved to the orchestrator without adding a Bash or `jq` dependency,
and no new plugin component type appeared. The production-file warn stands as
recorded above; the reviewable-LOC warn became a size-only block at the live
midpoint after the design closed, which continues into marker planning rather
than stopping the run.

## Slice Topology

ART-008 ships as two stacked vertical slices along a Path seam. Both cut end to
end through the Claude and Codex variants.

| Slice | Branch | Scope | Status |
|---|---|---|---|
| 1 — the checkpoint | `art-008-feedback-sweep` | The comment-driven path: read, trust-filter, recognize, classify, amend through consensus, record, reply, stop or proceed. | This spec |
| 2 — artifact freshness | stacked on slice 1 | Regenerating the draft page set after amendments, detecting stale pages from git history on a clean sweep, and refreshing the draft pull-request description including the Resume block. | Specified separately |

### The hooks slice 1 leaves for slice 2

Slice 2 is stacked on this branch, so these are an interface, not an internal
detail. Changing either after slice 2 starts is a breaking change to it.

1. **The Feedback Sweep Log row shape.** Header
   `| # | Comment ID | Surface | Author | Class | Disposition | Commit | CRL # |`
   under its own `### Feedback Sweep Log` heading, immediately after
   `### Consensus Resolution Log` (FR-013). Slice 2 reads this table to learn
   which amendments landed and therefore which pages are stale. The `Commit`
   column is the join key for that read: it is what lets slice 2 diff the
   artifact tree against the amendment commits rather than guessing from
   timestamps. Placement is additive-safe — the phase-coverage guard's table
   reader is heading-anchored and breaks on any line starting with `#`.
2. **The stop-report regeneration sentence.** Slice 1's stop report states that
   draft pages regenerate once slice 2 lands (FR-017). Slice 2 replaces that
   sentence with the real regeneration outcome. Until it does, the sentence is
   the only thing telling a reviewer why the pages they are looking at are
   older than the amendments.
3. **SC-008's standing constraint on slice 2.** After an amendment run stops, a
   reviewer can tell what changed and where from the pull request alone, and
   that rests entirely on the FR-015 replies, because a draft description is
   fully fingerprint-protected with no editable region. Slice 2 owns the
   description refresh and **MUST NOT** weaken the replies on the assumption
   that the description now carries this.

## Project Structure

### Documentation (this feature)

```text
specs/art-008-feedback-sweep/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── sweep-pr-feedback.md
├── checklists/
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
speckit-pro/
├── speckit_pro_runner/
│   └── helpers/
│       ├── read_only.py          # + sweep_pr_feedback(), the redaction surface, registry, 3 registration points
│       └── registry.py           # + one HelperEntry
├── skills/speckit-autopilot/references/
│   ├── phase-execution.md        # + Phase 7 setup sweep sequence, ahead of the notes record
│   ├── workflow-file-protocol.md # + the Feedback Sweep Log entry
│   └── consensus-protocol.md     # + the `Sweep` Type value
└── codex-skills/speckit-autopilot/references/
    ├── phase-execution-codex.md        # mirror of the sweep sequence
    └── workflow-file-protocol-codex.md # mirror of the log entry

tests/speckit-pro/
├── suite-manifest.json
└── unit/
    ├── test-speckit-pro-read-only-helpers.py   # EXPECTED_HELPERS, NO_BASH_ANCESTOR
    ├── test-feedback-sweep-parse.py            # golden fixtures + manifest-derived registry test
    └── fixtures/
        ├── feedback-sweep/                     # comment corpus + expected envelopes
        └── read-only-helpers/
            ├── fixture-manifest.json           # order-sensitive; append to match EXPECTED_HELPERS
            └── requests/sweep-pr-feedback.json
```

**Structure Decision**: No new directories under plugin source. The helper joins
`speckit_pro_runner/helpers/read_only.py` beside `resolve_autopilot_stage`,
which is the operation this one is modeled on: both take an orchestrator-supplied
observation, classify it offline, and report without deciding. One new fixture
directory, `tests/speckit-pro/unit/fixtures/feedback-sweep/`, holds the golden
corpus, named for the durable behavior rather than for the spec id.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations. The reviewability warns are not a constitution
violation: the preset's thresholds warn above 400 reviewable LOC, 6 production
files, and 15 authored files, and block above 800, 8, and 25. At the live
figure this slice crosses **two** blocks, both size-only: the reviewable-LOC
block at its midpoint, and the **production-file block at 12 against 8**, which
the consumer-scoping pass introduced with the four sweep agent definitions and
the `install.py` inventory edit. Authored files sit at 22, a warn under the 25
block. **Both crossings are operator-accepted at T014**, on the ground that the
trust boundary is not separable from the feature; the precedent for continuing
past a recorded size-only block is PRSG-013. Recorded, not hidden.
The warn, its derivation, its acceptance, and the split option that was
considered and rejected are recorded in "Reviewability Budget, derived by hand".

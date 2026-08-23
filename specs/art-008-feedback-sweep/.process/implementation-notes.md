# Implementation Notes: ART-008

Appended by the orchestrator as each Phase 7 task returns. One entry per task
that reported something; a task that reported nothing gets no entry.

### T001

**Deviations/Edge cases/Surprises:** One deviation, accepted. The task scoped
`anchors_dropped` to the Response block; the worker also named the field in the
new Recognition prose, because a drop-and-count rule is meaningless without
saying where the count lands. The field's shape stays declared in the Response
block alone.

Two edge cases, both worth carrying forward. First, FR-007e specifies two
different anchor representations that differ by one character, and conflating
them breaks the parse in either direction. The grammar `#[a-z0-9-]{1,64}`
includes the leading `#` and validates the parenthesised value as pasted,
`(#phase-2)`. The record stores the run after the `#`, `["phase-2"]`. Validating
the stored form against the grammar drops every conforming anchor; storing the
validated form breaks the fixture. Whoever implements the anchor parse (T031,
T032) and whoever fixtures it (T021) must read the contract's Recognition
paragraph rather than infer the shape. Second, sixty-four appears twice with
different meanings, the maximum anchor length and the maximum anchor count.
Both are in the contract and distinctly worded, but they read as one rule when
skimmed.

### T002

**Deviations/Edge cases/Surprises:** One cosmetic deviation: an em dash was
written and then removed to match the repository writing style.

One edge case, since acted on. FR-007e also fixes *which* sixty-four anchors
survive the cap, "the first sixty-four in body order", and T021 asserts exactly
that. The worker encoded the grammar and the count only, correctly scoping
itself to the task text, and flagged the rest. The orchestrator added the
body-order clause to `data-model.md`; the contract needs the same clause.

The worker also flagged that CHK049 in `checklists/security.md` still read as an
open conflict quoting the superseded singular `matched_line`, and that no task
in the T001-T006/T094 setup block owned closing it. The orchestrator reached the
same conclusion independently and closed it. See the entry below.

### T005

**Deviations/Edge cases/Surprises:** Report not returned; the worker went idle
before sending one. The edit was verified by the orchestrator against the task
acceptance and the sibling manifest entry. Nothing anomalous observed.

The red state this task creates is expected and must not be papered over: the
manifest now names `tests/speckit-pro/unit/test-feedback-sweep-parse.py`, which
T015 has not yet created, so the suite stays red until US1 tests land.

### T006

**Deviations/Edge cases/Surprises:** Report not returned; the worker went idle
before sending one, twice, including after an explicit request.

One deviation the orchestrator corrected. The worker produced
`{"schema_version": "1.0"}` for both fixture files, matching the sibling's
version key but supplying no container. The task called for skeletons "keyed by
case name", and tasks T015 through T093 fill them, so each would have invented
its own container. Both files now carry `cases: {}`.

### CHK049 (orchestrator, not a task)

**Deviations/Edge cases/Surprises:** CHK049 was recorded during the security
checklist as deliberately *not* closed, on the stated ground that resolving it
changes either a requirement or the helper contract and the contract sat outside
that remediation's edit surface. T001 owns the contract, so the deferral expired
when T001 landed. The orchestrator ticked the item, retagged it `[Resolved,
Contract §Recognition]`, and rewrote the deferral note to record where and why it
actually closed. The Remediation Record table was left alone, because CHK049 was
never one of the nine items that table counts.

### T003

**Deviations/Edge cases/Surprises:** No deviations.

One edge case, checked and closed by the orchestrator. FR-006b's validation half
continues into a paragraph stating that the input error stops the run, and stops
it with the FR-020 report (`spec.md:611-622`). The worker deliberately did not
mirror that into the contract and grepped to justify it: the contract carries no
run-stop, FR-020, or halt language for any diagnostic, so adding it for one row
would invent a shape, and the stop is orchestrator behavior rather than
something the helper validates. The obligation is owned downstream, by T052 (the
write-point stop reporting under the FR-020 contract) and T071 (consolidating
every stop onto one report builder). No gap.

The worker also confirmed its two hunks are disjoint from T001's, hunk by hunk,
with nothing reverted or restyled. That was the concurrency risk on this file.

### T004

**Deviations/Edge cases/Surprises:** Four deviations, all justified and declared.
(1) The `check_target` surface received full Request, Response, and Diagnostics
blocks though the task named only the redaction surface, because the Known
Interface Gap says T004 settles "the request and response shape of that check at
the write" and the narrower reading would leave T051 with prose. (2) Registration
row 2 was updated to the four-input entry and a "seven rows" note added, because
T011's acceptance names that entry and leaving row 2 at three would make T011
contradict the contract it cites. (3) A transport-cut paragraph on the `lines`
rule, without which the 8192-byte bound and the runner's 32 KiB per-string limit
read as unreconciled and T084's 33 KiB case has no stated cause. (4) One
diagnostic beyond the four listed: an outbound field sent on the analyst-payload
leg, or the reverse, is `invalid_input`, derived from FR-012f's "anything else
returns `invalid_input`".

Three edge cases.

First, **this contract sits inside the blast radius of its own examples.**
`spec.md:1144-1148` names seven feature documents, the contract among them, that
FR-008a's corpus-scan case sends through the `amendment` leg asserting zero
redaction events. A realistic `bearer <token>` example in any of them fires
`bearer_token` and turns that fixture red. The worker elided the value and said
so in the document so a later editor does not innocently restore it. T084's
author needs this: the same constraint binds `spec.md`, `plan.md`, `tasks.md`,
`data-model.md`, `quickstart.md`, and `research.md`.

Second, **the spec's own node-id example was one character short of its own
stated floor.** FR-012f (`spec.md:2205-2208`) called `IC_kwDOKQ7tDs5vXkZ9` a
token-shaped run of "twenty-plus characters"; the literal was nineteen. The
marker-line negative case still asserted zero events, but for a different reason
than stated, "not a run at all" rather than "a run with no trigger before it".
The orchestrator fixed the literal rather than weakening the case: the id is now
`IC_kwDOKQ7tDs5vXkZ9Aq`, twenty-one characters, replaced across `spec.md` (1),
`tasks.md` (2), and the contract (9). Zero occurrences of the short form remain.

Third, **em dashes.** The file's existing prose uses them heavily, so "match
local style" and the repository's no-em-dash rule pull opposite ways. The worker
checked the diff, found T001 and T003 had added zero, and followed that
precedent. The result is a visible inconsistency between the new sections' bullet
lead-ins and the neighbouring ones. Deliberate.

### Stray artifact (orchestrator, not a task)

**Deviations/Edge cases/Surprises:** T004 flagged an untracked
`tests/speckit-pro/unit/fixtures/read-only-helpers/tmpl81hwyb5/unknown-mode.json`
as a stray temp directory rather than intended output. Confirmed and removed. An
untracked path under a scanned tree is not harmless here: the spec-index
generator walks the filesystem rather than the git index, so a stray file can
become a committed dangling backlink that passes locally and fails on a clean
checkout.

### T007

**Deviations/Edge cases/Surprises:** No deviations. Red state captured cleanly:
76/76 before, 73/76 after, `FAILED (failures=2, errors=1)`.

**One finding changed the task plan.** A third failure fired that no acceptance
criterion named and no task owned. `test_helper_python_authoritative_records`
iterates `filtered_helpers()` and indexes `HELPER_CASES[helper_id]` at line 2161,
skipping only `helper-registry-dispatch`, so appending the id to
`EXPECTED_HELPERS` raises `KeyError` on every run until a `HELPER_CASES` entry
exists. Phase 2 could not have reached green. The worker correctly refused to add
it out of scope and flagged it. T012 found the same gap independently. The
orchestrator added it to `tasks.md` as **T110**, depending on T010 and T011,
because the assertions after the lookup read a real dispatch response rather than
an `unknown_helper` envelope. Task count 109 to 110.

The index question is settled with evidence: index 18, the last element, with the
manifest holding exactly 18 records in matching order, so appending renumbers
nothing. The failure output confirms it independently ("First extra element 18").
`bash-reference-manifest.json` stays at 16 comparisons and needs no new record.

Left deliberately: the comment block at lines 79-82 rationalizes each
`NO_BASH_ANCESTOR` member individually and now has three members with two
rationales. Flagged rather than silently drifted.

### T009

**Deviations/Edge cases/Surprises:** One deviation, and the worker was right.
**The task prompt's premise was wrong.** It said to match
`requests/resolve-autopilot-stage.json` "including how `pr_observation` is
structured there"; that fixture carries no `pr_observation` at all, because the
input is optional for that helper and only the test file constructs one. The
worker took the payload from the authoritative contract instead and corroborated
the underlying convention twice: the `ok`-must-be-JSON-literal-`true` rule at
`read_only.py:1345`, and the sibling observation built in-test at
`test-autopilot-stage-resolution.py:1455`. Same `ok` convention, different
payload key, because ART-008's is `comments`.

One choice worth keeping. `self_login` is `speckit-pro-bot`, deliberately not
`octocat`: `octocat` authors the canonical candidate comment, so a matching
`self_login` would flip it to a `self_reply` exclusion under FR-006 and silently
invalidate the contract's own Response example of observed 2, candidates 1,
excluded 1.

Its acceptance proof exceeded what was asked. Three differential probes
established that envelope validation runs before `request_id` is copied onto the
response, so an echoed `request_id` proves `schema_version`, `mode`, `helper_id`,
and `inputs` all validated and the request died at the registry lookup.
`unknown_helper` with `fixture-sweep-pr-feedback` echoed is therefore exactly the
pre-T010 state, not a malformed envelope.

Minor: the report credited the `EXPECTED_HELPERS` edit to T012. It was T007.

### T012

**Deviations/Edge cases/Surprises:** Independently found the same unowned
`HELPER_CASES` gap T007 found, and established the set difference precisely:
`sweep-pr-feedback` is the only member of `EXPECTED_HELPERS` missing from
`HELPER_CASES` besides the deliberately skipped `helper-registry-dispatch`. It
also confirmed the contract's seven-row registration checklist is incomplete by
one touch point, since `HELPER_CASES` appears nowhere in `tasks.md` or the
contract.

**One deviation is a process hazard worth recording.** The worker ran two
path-scoped `git stash push` / `git stash pop` round trips to build counterfactual
evidence. The evidence was genuinely good: it showed the edit removed exactly one
failure, the one the task names, and that the other two never read the registry.
But the stash stack is shared with the main checkout and every other worktree, and
concurrent sessions push and pop it, so a `pop` can take an entry that is not
yours. No amount of care by the worker closes that race. It came out clean, the
stack holds only its 11 pre-existing entries and `registry.py` compiles. The
orchestrator has since added an explicit `git stash` prohibition to every
remaining worker prompt, with scratchpad copies named as the substitute.

Also recorded: the line-238 mismatch resolving from the ACTUAL side confirms the
harness executes worktree source rather than the installed plugin cache.

### T010

**Deviations/Edge cases/Surprises:** Four declared deviations, all sequencing
rather than substance: two module-level constants encoding the contract's closed
surface set; an interim carry-all where the skeleton yields 2 candidates and 0
excluded against the finished parse's 1 and 1, recorded in the docstring so no
reader mistakes sequencing for policy; `check_target` and `redact` refused with
exit 2 until T051 and T083; and runner-manifest staleness owned by T074/T075/T108.

**The verification was a proof, not a code read.** A `sys.addaudithook` was armed
before the call, watching `subprocess.Popen`, `os.system/exec/spawn/fork`,
`socket.*`, `urllib.Request`, any `open` whose mode carried `w`, `a`, `x`, or `+`,
and `os.remove/rename/mkdir`. Zero events on both the no-network and no-write
invariants. Determinism was shown by two calls on independent deep copies
compared byte for byte, and no-class-assigned by asserting none of the four
vocabulary values appears in the serialized output. 25/25 checks.

**One design decision prevents a tautology.** `observed` is counted from the
observation, not from `len(candidates) + len(excluded)`. Had it been derived,
T034's invariant could never fail. Same failure mode the checklist caught
elsewhere in this spec.

**One contract gap, since closed.** The contract said absence of `named_surface`
means `parse` but said nothing about an explicit JSON `null`, and `.get()` cannot
tell them apart. The orchestrator wrote the rule into the contract: explicit null
reads as absence and routes to `parse`, while the empty string is a value outside
the three and therefore `invalid_input`. The distinction is stated because the
natural idiom `inputs.get("named_surface") or "parse"` silently routes `""` into
the parse. The worker tested `is None`.

### T008 and T013

**Deviations/Edge cases/Surprises:** One deviation, a correctness improvement.
`failure_classes` is `["invalid_input", "unsupported_path"]` rather than a copy of
the sibling's four-value list, because all three Diagnostics tables in the
contract emit only `invalid_input` and explicitly fold "missing required field"
and "unreadable `workflow_file`" into it. Copying the sibling would have recorded
failure classes the contract rejects, and nothing asserts that field's contents,
so it would never have been caught.

The worker also checked `.sh`, which the same test gates on at line 386 and which
the prompt did not mention. No hit for either substring.

**One masking effect worth knowing when reading a run.** At 75/76, no
missing-helper failure appeared for T010 or T011, but they were masked rather
than absent: the `HELPER_CASES` lookup raises before any dispatch reaches the
helper. The dispatch path was not proven until T110 landed.

Insertion was textual rather than a JSON round-trip, so all 18 existing records
keep their bytes.

### T011 and T110

**Deviations/Edge cases/Surprises:** No deviations in the code. Phase 2 reached
**76/76**. T110's counterfactual used a scratchpad `cp` restore rather than
`git stash`, per the prohibition added after T012.

**The most consequential finding of the phase.** The contract's "allowed-inputs
entry" is not an allowlist, and no such map exists in the runner. Row 2 actually
names `path_keys_by_helper` at `read_only.py:247`, and every key it lists is run
through `request_path_display`, whose `normalize_path_input` is
`str(raw).replace("\\", "/")`. A listed key is rewritten: backslashes become
forward slashes, then the value is resolved as a path and re-rendered
repo-relative.

The hazard is T083, not T011. T083's instruction said it would add "the
allowed-inputs entry for the surface's fields", and those fields include `text`,
a raw reviewer comment body, and `lines`, an array of them. Either behind that
map silently rewrites every backslash a reviewer typed, before the deny-set ever
runs, corrupting the exact bytes FR-007g's golden envelope pins. The fixture
would then pin corrupted bytes as correct.

The worker flagged it rather than fixing it out of scope, and verified the two
non-path keys already named were inert rather than trusting the trace:
`pr_observation` is skipped by the `isinstance(value, str)` guard, and
`self_login` round-trips unchanged on every shape that matters including the
FR-006b whitespace-only case. The orchestrator applied the rule in both places it
has to live: contract row 2 now reads `path_keys_by_helper` with real path inputs
only, `{workflow_file, feature_dir}`, and T083's instruction in `tasks.md` now
forbids `text` and `lines` with the reason attached.

**One sequencing item carried forward.** The test-file edit restales the
docs-site test reference page; `tests/speckit-pro/AGENTS.md` requires
`pnpm --dir docs-site reference:generate` after a tracked `.py` change under that
tree. T076 owns it. Correctly not run mid-phase with other workers in the tree.

### T095

**Deviations/Edge cases/Surprises:** Three deviations, all justified.

(1) **No Codex TOML existence assertion.** The task said to assert each member's
file exists; the worker implemented it for the Claude `.md` only. The TOMLs land
at T099 and T105, one task after their `.md`, so asserting TOML existence here
would make T098's and T104's stated acceptance unmeetable, since each creates
only the `.md`. The Codex half instead uses the guard idiom already in the file
at `test_codex_agent_sandbox_mode_scoping`, so the `read-only` pin arms the
moment T099 and T105 land.

(2) **The task's line numbers were stale**: it cites 29, 49, and 187 where the
actual pre-edit values were 30-49, 50, and 187. Placement followed the real
structure.

(3) **One assertion beyond the literal three.** `UNTRUSTED_INPUT_ALLOWLISTS` plus
a membership subtest asserting its keys equal the tuple. Without it, a member
added to the tuple with no allowlist entry would be exempted from the
no-allowlist rule and pinned by nothing, which is the same door assertion 3
exists to close.

**Count proof, which the task required because a method left off
`TEST_METHOD_ORDER` never runs**: 192/192 before, 195/197 after. Total moved by
+5, so the method dispatches. The two reds are the Claude-definition existence
assertions, the written-red state T095 names.

**Eleven counterfactuals, run against a temp fixture tree with `AGENTS_DIR` and
`CODEX_AGENTS_DIR` redirected, nothing written into the repository.** The two
that matter most: a bare `tools:` key (YAML null) goes RED against the pinned
floor, and a non-member pinning `tools: Read` goes RED on the unchanged
no-allowlist rule while members skip it. Together those show the pin is
bidirectional and the exemption is by membership rather than by pattern. The
forbidden tightening was not written: no assertion moves toward an empty `tools:`
list.

**One stated mechanism in the task is wrong, and the worker checked rather than
assumed.** The task says `_disallowed_tools` raises on an absent path, and gives
that as the reason for the existence assertion. It does not raise: `_read`
returns `""` for a non-file and `frontmatter([])` returns `""`, so the call
returns `[]`. The existence assertion is still correct, because it converts a
cascade of confusing "denies Agent" failures on a nonexistent file into one
legible pending-work red per platform. The reason is different from the one
recorded.

### T015-T024, T082, T096, T097 (US1 test harness and corpus)

**Deviations/Edge cases/Surprises:** No deviations from the task text. 971-line
harness, 112 corpus cases, **139 failures and 0 errors**, every one a real
assertion against live runner output rather than a harness crash.

**Three assertions were rewritten mid-task because they could not fail.** As
first written, `test_counts_agree_with_the_two_lists`,
`test_every_exclusion_reason_is_in_the_closed_set`, and
`test_anchors_conform_to_the_grammar_the_record_stores` compared the expectation
to itself. They now read the live response. Two are vacuously green today,
because the skeleton emits no exclusions and no exports, and each goes red
against a wrong implementation. The worker classified them honestly as
"vacuously green now, falsifiable later" rather than counting them as coverage.

**No golden is typed by hand.** The 30 shaping cases carry `capture_pending:
true` with a null golden plus independent per-case assertions, and the refresh
mode refuses on a non-ok response. That is what keeps T081's acceptance real: a
test comparing a typed string to itself executes nothing.

**Two design decisions the spec left open**, both recorded in the affected case's
`purpose` string so a later implementer meets a decision rather than an
accident: the serialization family's registered line is `Artifact:
<template-id>`, grounded in `research.md:68-77`; and when a body matches both a
markdown and a prompt lead, the export record's `kind` is the first matched
line's kind in body order, because nothing fixes it and one record carries one
kind.

**A third independent confirmation of the `path_keys_by_helper` hazard.** The
worker probed `read_only.py:257` and found the four-key entry still contradicted
the contract's corrected row 2. It verified the two non-path keys were inert
today rather than assuming, and flagged the extension risk. The orchestrator
narrowed the code entry to `{"workflow_file", "feature_dir"}` with the reason in
a comment. Three workers found this independently.

**`run-all.py` discovers a Layer 4 test without a manifest row.** The new file
ran as `FAIL test-feedback-sweep-parse (exit 1, no summary)` and counted as one
failed unit. Layer 4 discovery is not manifest-gated; the manifest row supplies a
label and baseline, not selection. Worth knowing when reading a red count.

**Ambient suite state**, so a later reader does not misattribute it: 7907/7918
with 11 failures, of which 7 are `test-speckit-pro-gates`, 1 is the runner
`.sha256` mismatch stale against the source change, 2 are the Layer 5 carve-out
awaiting T098 and T104, and 1 is this file's designed red. The 8 payload failures
are the standard shipped-source-changed-artifacts-not-regenerated state that
T074, T075, and T108 close.

**T081 remains open, deliberately.** Its acceptance requires the expected blocks
to be the redaction surface's own committed output, and that surface lands at
T083. The corpus request cases are authored; the expected side cannot be
produced yet. Marking it complete now would require hand-typing the goldens,
which is exactly the tautology its acceptance forbids.

### T088

**Deviations/Edge cases/Surprises:** Both tests green; the 139 ambient failures
unchanged in count and confined to the six earlier classes. Test count moved
22 to 24.

**One finding changed the test and is worth carrying.** A user-level ignore at
`$XDG_CONFIG_HOME/git/ignore` silently masks this red. The worker proved it
empirically: with `XDG_CONFIG_HOME` pointed at a directory holding `git/ignore`
containing `feedback-sweep/`, `git add -A --dry-run` staged nothing even with no
self-ignore write present; pointed at an empty directory, the same repository
staged the byproduct. So the env isolation in the scratch-repo helper is
load-bearing rather than decoration, and the red proof is honest only because of
it. `GIT_CONFIG_NOSYSTEM`, `GIT_CONFIG_GLOBAL`, and `GIT_CONFIG_SYSTEM` alone do
not cover it, because git reads that default path with no config naming it.

The scratch-repo test also carries a positive control, asserting `README.md` is
named, so a dry run that named nothing at all cannot pass vacuously.

The second test's red proof needed care: with `REPO_ROOT` resolving into the
scratch copy, an absent root `.gitignore` raises `FileNotFoundError`, which is an
error rather than a clean red. The worker planted a root ignore carrying other
entries and not this one, proving the test keys on the line rather than on the
file's presence.

Parity verified by a scripted check over fourteen load-bearing facts, zero
present on one side only. The Codex block was scanned for Claude-only runtime
terms, which matters because `validate-codex-skills` concatenates every
reference file onto the SKILL.md before scanning.

One deliberate omission: the `.git/info/exclude` contrast the acceptance names
was left out of the shipped prose as repository history rather than sweep
behavior, with the operative half kept.

### T098 and T099

**Deviations/Edge cases/Surprises:** Four deviations, three findings that needed
routing.

Layer 5 moved 195/197 to **207/208**, one failure left, the `sweep-analyst`
existence subtest that T104 closes. The predicted 196/197 was unreachable and the
worker explained why rather than forcing it: the denominator grows because the
carve-out subtests only exist once the files do, +9 from the classifier and +2
from the TOML. FR-008c anticipates this ("the subtest count moves, and that is
fine"). The real invariant is one failure, and which one.

**Deviations.** (1) Amended `capability-discovery.md`, outside the stated file
list, because T098 names it explicitly and no concurrent worker claimed it; the
edit narrows the falsified claim to agents acting on trusted input and names the
two untrusted-input consumers as the exception. (2) Bumped two counts in
`test-speckit-pro-mutation-helpers.py`, 11 to 12, on the decisive precedent that
`artifact-author.toml` bumped the same two 10 to 11 in its own commit; **T105
takes them to 13**. (3) `disallowedTools` carries T098's four names rather than
FR-010a's eight, because FR-008c is the normative pin and the other four are
denied by the equality-pinned `tools: Read` allowlist itself. (4) The Codex
mirror of the capability-discovery amendment has no legal target: that reference
tree has no `capability-discovery.md`, and the nearest Codex statement sits in
the SKILL.md at the 8000-word cap. Routed to the orchestrator, unresolved.

**Layer 6 did not restale**, verified empirically rather than inferred: the
twelve governed roles are a closed tuple and `sweep-classifier` sits outside it
exactly as `artifact-author` does.

**The finding that needed a new task.** `test-codex-route-fallback-recovery` is
red and no shipped task owned it. Its roster is derived by globbing
`speckit-pro/codex-agents/*.toml` and digesting every one, so any new TOML
restales it. Causation was proved rather than assumed: deriving the roster while
excluding `sweep-classifier.toml` reproduces the reviewed fixture exactly. The
worker deliberately did not fix it, because the library raises
`RosterDriftError("bundled Codex source roster drifted; fixture re-review
required")` with no regeneration script, which makes it a fail-closed
human-review control that regenerating-to-green would disarm. Added as **T111**,
after T105, with the re-review framed as a stated judgment rather than a refresh.

**The binding probe did not run, and the worker refused to fabricate it.** Its
dispatch forbade spawning agents, so T098's stop condition is unmet rather than
passed. The orchestrator then attempted it directly and could not: plugin agents
load from the versioned plugin cache, not worktree source, so the runtime reports
`Agent type 'speckit-pro:sweep-classifier' not found`. Staging the definition
into the cache was refused by the permission classifier, correctly, since that is
agent-config self-modification and a control proved only after editing the
control's own configuration would be worth little. Recorded durably in the
workflow file as UNRUN, with the discharge path after release and cache refresh.
The stop condition is not triggered, because it fires on a reachable tool and
none was observed; it is also not discharged.

**Two concurrency observations.** A sibling's `git add -A` commit swept this
worker's source files into `a36d12af7` before it finished, so its later
mutation-helpers bump is working-tree-only. And someone ran the payload build
mid-task, creating the two `dist/` agent copies while leaving the runner
`.manifest.json` and `.sha256` stale, so T074 is still required.

### T035-T043, T100, T101 (US1 reference documentation)

**Deviations/Edge cases/Surprises:** Three forced deviations, four findings.

**The orchestrator's parity scan was half wrong, and the worker proved it.** Two
of four reported gaps were probe artifacts of a line-based grep: `reviewThreads`
is symmetric and deliberately unprescribed, since FR-004b says reads pass their
query by file or structured argument; `self_login` was present on both, and the
Codex hit was missed because the phrase wraps across two lines. One gap was real,
a `convergence` clause dropped in a Codex compression pass, and restored. The
fourth, `gh api` 3 vs 0, belonged to unrelated pre-existing prose in the
resolve-pr flow outside the sweep block, and the worker correctly refused to
mirror another feature's flow into the Codex reference. Final parity: **58 facts,
58 on both sides, zero on one side only.**

**Deviations.** (1) No FR or SC ids in the shipped prose: neither reference cites
this spec's requirements, and the only two FR citations in those files belong to
an unrelated spec whose own FR-004 and FR-005 would collide. (2) `resolved_python`
rather than the task text's literal `python3`, because the hardcoded interpreter
failed `validate-installed-interpreter-contract` under the Installed Runtime
Contract. (3) T043's fixture writes to its own temp directory rather than the
shared scratch, for the reason below.

**A concurrency hazard in the test file itself, found by being bitten.** The
worker's fixture was flaky at 42, then 33, then 9, then 0 failures across
consecutive runs. Cause: another worker's suite run calls
`shutil.rmtree(WORKFLOW_SCRATCH)` in `main()`, deleting the workflow file
mid-case. Fixed for the new fixture with an owned `tempfile.mkdtemp`, self-cleaning
in a `finally`. **The pre-existing `materialized_workflow` path still carries this
hazard** for any two concurrent runs of this file, and is worth closing later.

**The Codex SKILL.md word cap has ZERO headroom, not three words.** Measured with
the validator's own `_body()` helper rather than `wc -w`, because the cap is
computed after frontmatter is stripped:
`speckit-pro/codex-skills/speckit-autopilot/SKILL.md` is at **exactly 8000 of
8000**. The next-largest is `speckit-scaffold-spec` at 7453 and everything else is
under 4300, so the cap binds on one file. The standing project note recording
7997 came from task prose rather than a measurement and has been corrected.

**T040 versus T100 was written once, as T100's version.** T040's per-candidate
body read never appears, because T100 replaces it: the orchestrator is a conduit
and reads no body on any path. The worker also corrected T040's three-field
shorthand to the contract's four fields, matching the landed fixture.

Verification: Layer 1 **1490/1490**, `validate-codex-skills` 163/163,
`validate-codex-parity` 85/85, parse test delta against the 9 baseline **zero**.

### T051 and T086

**Deviations/Edge cases/Surprises:** Three deviations, each a decision inside a
contract silence and commented in code so T084's author reads intent rather than
accident. (1) **Rule-major intra-line event order**, because `spec.md:2093` says
the deny-set is applied "in this order", so on a line with a bearer hit left of an
AWS hit the events come rule-major. Output text is identical either way; only
event order differs. (2) An over-bound line inside a PEM span takes the span
placeholder and **both** events are kept; both placeholders carry zero reviewer
bytes and the fixpoint holds either way. (3) The END line is strip-compared,
mirroring the header rule's own surrounding-whitespace allowance, so a PEM block
indented inside a fence still closes.

**The trap-2 clearance is empirical, not argued.** All 15 `.md` files under the
feature directory were fed through the `amendment` leg: **zero events,
byte-identical output, line count preserved on every one.** That is the evidence
FR-008a's corpus-scan case needs, and it also clears the two grammar judgment
calls. The worker additionally kept its own code out of the blast radius by
assembling the PEM constants as `"-" * 5 + "BEGIN "`, so no committed line in the
implementation is itself a header.

**One real defect found and closed after its first pass.** A NUL byte in `target`
raised `ValueError` out of `Path.resolve` instead of returning a diagnostic.
`target` is deliberately absent from `path_keys_by_helper`, so nothing upstream
validates it, and the contract reserves `invalid_input` for a malformed request.
Guarded for both `feature_dir` and `target`.

**Two ordering details that are load-bearing rather than stylistic.** In the
write-point check, each directory is tested for `is_symlink()` **before** the walk
asks whether it is the stop point, because a link inside the feature directory
pointing back at it resolves onto an allowed path: membership passes, and a walk
that broke before testing where it stopped would let it through. And the
candidate is kept both resolved and unresolved, because resolving destroys
exactly what the link tests read. `contracts/../plan.md` resolving to allowed is
the proof the comparison is over resolved paths.

**Its RED was honest about being a probe bug.** The first run's three failures
were all in the probe, and the detail is worth keeping: the boundary vector used a
30-character run, where the 24-byte placeholder *shrinks* the line. The spec's
named vector needs a 20-character run, where the placeholder grows it by 4 and
8189 crosses the bound. Fixing the probe is what exercised the boundary math.

### T048-T050, T052-T054, T087 (US2 consensus and commit documentation)

**Deviations/Edge cases/Surprises:** Two rendering substitutions forced by the
standing rules, one deliberate partial overlap left rather than rewriting
committed US1 prose, and three findings.

**144 fact probes, 144 on both sides, zero on one side only.** Nine probes missed
on a first exact pass and resolved case-insensitively or on a word-order variant,
which is the same false-gap effect that made the orchestrator's own earlier
parity scan wrong. Whitespace-normalized comparison is the reliable method here.

**The finding that mattered: a phantom completion the orchestrator created.**
T051 and T086 were both marked `[x]` on the strength of their code halves, but
each also owes documentation in both references, and neither had landed. The
orchestrator's own dispatch caused it, by telling the code worker "the
documentation half is NOT yours" and then marking the whole task complete.
Verified independently before acting: `8193`, T086's transport-cut figure, appears
zero times in either reference, and the only "refused target" hits are T052's
write-point stop under rule 2 rather than T051's rule-1 classification wording.
**Both marks were reverted to open.** This is exactly the class of defect the
post-implementation phantom-completion check exists to catch, found early instead.

T051's outstanding half is rule 1: an out-of-scope request takes `deferred` with
the refused target named in the disposition and the reply, worded as recorded and
not acted on, with no implication of future action. T086's is the amendment-leg
call point beside the commit protocol: the introduced text through the surface
before the write, the caller writing back what the surface returned, and the
8192-byte transport cut at the first character boundary at or past byte 8193.
Both are assigned to the next references wave, which writes the same two files.

**Both stated baselines had drifted upward mid-run**, Layer 1 to 1511/1511 from
1490 and `validate-codex-parity` to 87/87 from 85, consistent with a concurrent
worker adding assertions. The worker reported the drift rather than normalizing
it, which is the right instinct: a silently normalized baseline hides whether the
delta was yours.

**A preflight worth copying.** This worker asserted its constraints
programmatically BEFORE splicing, blocking on failure: zero lines over 80
columns, zero em dashes, zero hardcoded interpreter literals. It also verified
after the write that the Codex-only runtime regex finds zero hits in the whole
Codex reference, and that the bare literal `Bash` does not appear in it at all,
since the Codex text names "a shell, web fetch, web search, and every installed
MCP server" where the Claude text names the tools.

### T055-T058 (Feedback Sweep Log protocol)

**Deviations/Edge cases/Surprises:** Five deviations, four findings. 47 facts,
zero on one side only. Three initially read as Codex-only misses and were line-wrap
artifacts, the same false-gap effect seen twice before; normalizing whitespace
resolved all three.

**Deviation 1 was correct and the orchestrator's brief was wrong.** The dispatch
allowed two files; T058 names `consensus-protocol.md:617` explicitly, and the
worker verified the Consensus Resolution Log row schema exists there and nowhere
else, with the two workflow-file-protocol files only summarizing the column set
and deferring to it as canonical. Satisfying T058 inside the allowed two would
have created drift against the canonical schema. It wrote the correct file and
flagged the conflict rather than silently obeying or silently disobeying.

**Two omissions that improve the shipped prose.** It cut a `Stage` navigational
contrast it had first written, because the Codex file has no `Stage` entry, so
mirroring would dangle and keeping it would put one fact on one side only. And it
omitted "including this feature's own" from the corpus statistic on both sides, on
the ground that a fact about an in-flight feature does not belong in protocol
prose that outlives the feature.

**A false stale worth knowing about, and now in project memory.** `cmp` flags the
Codex `dist/` copy as differing from source, but the diff is three link-prefix
rewrites: the payload generator strips `../../skills/speckit-autopilot/references/`
because in the packaged layout the Codex reference sits beside the Claude ones.
`validate-codex-parity.py:172` calls `removeprefix("../../")` and resolves against
the plugin root, so `../../` is the enforced convention even though it does not
resolve as a filesystem path. A future agent would reasonably try to "fix" those
links and would break both mechanisms.

**One inference flagged rather than presented as fact.** The example row leaves
`Commit` and `CRL #` empty for a non-amended comment. FR-013 does not say what
those cells hold; the worker inferred it from T059 (only an `amended` reply names
a commit) and FR-014 (only an amendment produces a consensus row), and labelled it
an illustration rather than a normative claim.

**Baselines were stale again**, measured at 1509/1509 before the worker touched
anything against the 1490 the dispatch stated, and it proved its edits could not
have moved `validate-codex-parity` by reading that validator's scan scope. Third
worker in a row to report drift rather than normalize it.

### T104 and T105 (sweep-analyst agent)

**Deviations/Edge cases/Surprises:** Four deviations, all unpinned choices
declared rather than hidden. Layer 5 went 207/208 to **219/219, zero failures**,
closing the carve-out on both agents. The denominator moved as FR-008c predicts,
and the worker verified zero failures rather than forcing a predicted total.

**Deviations.** `model: sonnet` and `color: pink` are unpinned; nothing binds
either and it mirrored the classifier for shape. `maxTurns: 20` rather than the
classifier's 10, reasoned rather than copied: the analyst must read a target file
and verify anchor uniqueness before returning, which the classifier never does.
The "What you receive" input table is an extrapolation, since the contract fixes
the classifier's inputs explicitly but names the analyst's only in prose. And it
left pre-existing gitignored `__pycache__` directories alone rather than racing
concurrent test runs for no benefit.

**Two design points in the agent body worth keeping.** First, it states plainly
that the three tools are **permission-scoped, never path-scoped**, and that
nothing in the body should be read as confining the agent to this repository. It
then greps for the four claims that would have said otherwise and reports zero
hits. An agent definition that overclaims its own containment is worse than one
that states the real boundary, which here is the absent shell, the absent network
tool, the redaction over `replacement`, and the human checkpoint.

Second, it explains why **synthesis is `sweep-analyst` and never
`consensus-synthesizer`**: that role declares no allowlist, so it inherits the
operator's whole surface, and handing it reviewer-derived findings would reopen
one hop downstream exactly what the allowlist closes. "A boundary that holds for
three calls and fails on the fourth is not a boundary, and the fourth call is the
one that composes the edit."

**The route-fallback restale was left alone, correctly, and with a precise
attribution.** The core-count assertion was **already red at 11** from T099's
TOML, so this TOML moved an already-red assertion rather than breaking a green
one. T111 owns it.

**It disproved a plausible false attribution.** The runner manifest failure could
have been blamed on its own `install.py` edit. It checked: the manifest records a
digest matching neither the pre-edit content nor the current content, so the entry
was already stale before it touched the file.

### T044-T047, T084, T085, T090-T093, T102, T103 (US2 tests and captures)

**Deviations/Edge cases/Surprises:** 25 tests with 9 failures became **72 tests
with 0 failures**, 154 corpus cases, four capture blocks at 94 runs each, zero
pending goldens.

**It ran falsification probes rather than asserting green.** Dropping one
`log_row` call from the captures turns the per-leg count test red; rewriting one
report disposition to the un-redacted string turns the identity test red. The
fixture was restored by file copy and the suite re-run green. That is the
difference between a passing test and a test that can fail.

**It added a case specifically to stop a tautology.** T046's shipped cases would
have made T092's identity assertion compare two copies of an unchanged string, so
it added a disposition carrying a credential-shaped run, and a guard test that
keeps at least one `log_row` call actually changing its cell.

**Four assertions flagged as currently unfalsifiable, declared rather than
counted as coverage.** One escapes text inside the test rather than observing
output; one ends on a constant comparison because the filled Author cell is not
captured anywhere; one greps for a sentence no worker has written yet, so it
passes vacuously until the references land; and one is true by construction, but
carries a `discriminating > 0` guard proving at least one captured amendment
differs between request and response.

**Three deviations that are judgment, not shortfall.** T091 scans in size-bounded
line chunks because the runner truncates stdout near 16 KiB and six of the eight
documents come back unparseable whole; splitting on line boundaries can only add
events, never hide one, so zero over the runs implies zero over the file. T084's
33 KiB transport case was omitted because **no transport cut exists in the
runner** and a 33 KiB line is accepted, so writing the `invalid_input` assertion
the task names would be a false test; this is consistent with the contract, which
puts the cut on the caller. And it partitioned the case-name helpers rather than
appending blindly, because 27 new outbound cases would otherwise have flowed into
the shaping tests and raised `KeyError` on a missing `text` key, reddening
green tests.

**Two runtime facts worth carrying.** The runner caps stdout near 16 KiB and drops
`stdout_json` when it trips, which any future whole-file surface test will hit.
And `check_target` answers `status: ok` with `allowed` and a `reason`, never a
diagnostic, so a test asserting a non-ok status passes for the wrong reason on an
allowed path and fails on a refused one.

**Eight em dashes in the expectations file are captured bytes**, pulled in as edit
anchors from this feature's own document headings, not authored prose.

### T051/T086 doc halves, T059-T065, T089, T106, T107

**Deviations/Edge cases/Surprises:** **103 facts, zero on one side only.** All four
gates post-edit equal the measured pre-edit baseline: Layer 1 1511/1511,
codex-skills 163/163, codex-parity 87/87, interpreter-contract 6/6. Hygiene over
367 added lines: zero em dashes, zero lines over 80 columns, zero FR or SC ids,
zero absolute paths, zero banned Claude-only runtime terms in the Codex half.

**The two outstanding halves closed, and the worker reconciled them against prose
already in the file rather than just appending.** For T051 it found two conflicts:
the malformed-record rule forty lines above stops the run on a record whose
`target` is outside the three artifacts, so the refused path had to ride the
bounded reason and never the `target` field; and the vocabulary paragraph says
class-choosing rules live once in the classifier's definition, so what this
sequence fixes is only what a `deferred` reached this way must carry. It also
stated the rule-1 versus rule-2 distinction explicitly, since rule 1 alone is
prose a mis-routed item walks past and rule 2 alone turns an ordinary
out-of-scope request into a stopped run. The figure `8193` now appears on both
sides, where it appeared zero times before.

**A tension in the task text, surfaced rather than smoothed over.** T089's
mandated causal wording, that the parse filters over those bodies so the request
file has to carry them, sits against the pipe paragraph already in the file
saying no unredacted body is written to disk at any point. They reconcile through
that paragraph's own "where a byproduct file is unavoidable" clause, which is why
the worker hooked the enumeration onto it rather than editing either sentence.
**The tension is in the task text, not introduced by the implementation, and it is
worth a reviewer's eye.**

**Two more tasks were mostly already done, the same shape as T051 and T086.**
T106 and T089 were each roughly two thirds documented by the earlier sweep-sequence
commits; their genuine deltas were four sentences and two paragraphs. A task whose
code half lands with a partial documentation half is a recurring pattern in this
tasks.md, and it is why the phantom-completion check earns its place.

**One vocabulary judgment left deliberate.** `slice 2` is spec-internal language now
in shipped prose. T064 mandates it as report content, the follow-on sentence marks
it as a temporary interface the same slice replaces, and the section already used
slice vocabulary, so it was kept verbatim rather than paraphrased.

### T066-T070 (US3 corroboration gate)

**Deviations/Edge cases/Surprises:** 72 tests to **80, 0 failures**. 39 facts, zero
on one side only. All four other gates unchanged from measured baseline.

**Two falsification probes, both restored.** Neutralizing the gate in the modeled
walk produced 21 real subtest failures across four methods, and flipping one
declared status from `pr_closed` to `match` failed the classifier-link test with
`'pr_closed' != 'match'`. The three links are independently falsifiable: the
vocabulary is read from the shipped `AUTOPILOT_CORROBORATION_STATUSES`, each
declared status is recomputed by the shipped `corroborate_draft_pr` from the
case's own row and observation, and the mapping is walked into the capture and
compared against the declared outcome.

**One assertion flagged as currently unfalsifiable rather than counted.** The test
that the sweep never writes the `Draft PR` row passes trivially, because nothing
in the walk writes it today. It is a tripwire for the day someone adds a repair
step to a stop that had just failed to corroborate the record, and its own comment
says so.

**Two existing tests were narrowed rather than left alone**, to branch on whether
the gate admitted the run, each falsifiable in both directions: a blocked run now
asserts zero parse calls and an admitted run asserts one.

**A convention followed rather than changed.** Its first pass left
`consensus_comments` empty for an `answered` item and `SurfaceCallTest` failed on
an `analyst_payload` count mismatch, because the walk shapes a block for every
dispatched candidate rather than only amended ones. It checked the three existing
`answered` cases, found all three list the shaped candidate, and followed that
convention rather than changing the derivation, so no existing test's meaning
moved.

**It proved which step dirties `dist/`.** `validate-codex-skills` leaves it
untouched; `run-all.py --layer 1` refreshes the payload as a side effect. That
explains the `dist/` churn seen throughout this run without any worker
hand-editing a generated path.

**T070 closed a pre-existing platform gap**: the Claude side already carried the
resume sentence and the Codex side did not. Both now carry it.

**`__pycache__` cleanup is blocked** by the Bash safety gate for both `rm -rf` and
`find -delete`. The directories are gitignored and regenerated by every suite run,
so this is cosmetic; the new import sets `sys.dont_write_bytecode = True` so it
adds none of its own.

### T071 and T080

**Deviations/Edge cases/Surprises:** 80 tests to **84, 0 failures**. 41 facts, zero
on one side only. Three read as gaps on a first pass and were case-only false
gaps; two more wrapped across lines. Sixth worker to hit that trap, and the
whitespace-normalized pass is the authoritative one.

**What the consolidation actually removed.** Three competing names for one report
collapsed into one: "the standard stop report's three parts", "the plan-stage
stop report's shape", and "the re-review report's shape". The gate's inline
definition of the three parts is gone while its values remain, the whole separate
run-report section was folded into the builder, and the redaction section's
restatement of leg/rule/count went with it while its prohibition on the matched
line stays. Nine stop sites now supply only their own values.

**Both preserved distinctions verified intact rather than assumed.** The `skipped`
paragraph still reads "Those three stops observed something and this one observed
nothing", and the mid-read failure still opens "not the gate stop, and must not
read like it" and still requires naming that reading had begun and which surface
failed. Only its re-enumeration of the three parts was replaced by a pointer.

**A falsification probe with a stronger result than usual.** Two mutations, drop a
log row from the clean case and add one to the lost-bookkeeping case, turned all
four new tests red. After restoring and re-capturing, the regenerated expectations
file was **byte-identical** to the pre-probe backup, which also demonstrates
`--capture-runs` is byte-reproducible and that adding two cases churns no other
case's captured block.

**One assertion's provenance flagged honestly.** In the clean case the
"already replied" half enters through declared input rather than executed reply
reconciliation. The zero-rows and zero-replies conclusions still failed under the
probe by way of the executed skip key, so nothing is unfalsifiable, but the worker
named which half is declared rather than letting it read as executed.

**Three deviations, all declared.** The condition list includes a malformed
classifier or analyst record, which the brief required and T071's own enumeration
omits; it consolidates an already-documented stop, so no behavior changed. One
heading disappeared from the Claude sweep sequence, verified against every
reference in both skill trees before removal. And the human-review stop's two
operator actions are now stated once in the builder rather than at the site,
which is the consolidation working as asked.

**A shell trap worth carrying:** an unquoted `--include=*.py` died on a zsh glob
and returned a shell error rather than "no matches". A grep that errors looks
exactly like a grep that found nothing, which would have made a prose removal
look safe.

### Post-implementation code review: three blocking findings, all fixed

An independent read-only review found three blocking defects after the feature
was green at 7983/7983. **Each was reproduced by the orchestrator before being
accepted**, and each fix is proven by the reviewer's own scenario.

**One correction to my own verification first.** My first reproduction attempt
returned `input_error` for both the bug case and its control, which would have
read as "the finding is wrong". The cause was mine: I pointed `PYTHONPATH` at the
installed plugin cache rather than the worktree source, so the helper was
unregistered. That is exactly the trap every worker prompt in this run warned
about. Re-run against `PYTHONPATH=speckit-pro`, the finding reproduced exactly as
reported.

**Blocking 1: an array entry with an embedded newline bypassed the entire
deny-set.** Every rule tests a whole entry, the key-header rule using `fullmatch`
with no `MULTILINE`, and no entry was ever split. A whole private key packed into
one entry returned `redactions: []` with the key verbatim; the identical key split
one entry per physical line was fully redacted. The bytes on the `amendment` leg
are the analyst's replacement text and the push is part of the amendment step, so
they reach a public remote before any human checkpoint. Enforcement had rested on
an unenforced caller convention. Fixed by rejecting any entry containing a line
break, with the reason in a comment.

**Blocking 2: a symlink at an allowlist name approved a fourth file.**
`allowed_paths` was built by resolving the three names, so the allowed set was
"whatever those names point at". With `spec.md` a link to `evil.md`, the indirect
route was refused as `symlink_target` while a request naming `evil.md` directly
was **approved**. Fixed by requiring the candidate's unresolved form to be one of
the three names as well as its resolved form to be in the resolved set, so a link
can neither launder a file in nor be followed.

**Blocking 3: an oversized envelope reported success with no data.** The runner
captures stdout at 16 KiB and drops `stdout_json` when the truncated JSON will not
parse, leaving `status: ok`, `exit_code: 0`, and no diagnostics. Reproduced at
16759 bytes. Reachable without an attacker: four trusted comments each pasting a
conforming export, or one quote-heavy body whose JSON escaping doubles every
quote. A caller told to iterate `candidates` and nothing else cannot distinguish
that from a clean sweep, so the busiest pull requests would look empty. Fixed by
measuring the envelope against the capture limit and failing closed.

**Two minors, both actioned.** The NUL-byte comment overstated its own necessity:
`target` is in `PATH_KEYS`, so `validate_bounded_inputs` already checks it before
the helper is entered. Comment corrected to say defence in depth and unreachable
through registered dispatch. The Layer 5 Codex assertion is skip-on-missing, which
`install.py`'s required-names list covers from the other side; left as the
reviewer characterised it, a shape note.

**Six regression tests added**, because two of the three holes shipped with no
coverage at all and `symlink_target` and `symlink_parent` had no test anywhere.
Each carries a positive control so a fix cannot pass by refusing everything.

**What the review did not cover, stated so it is not mistaken for cleared:** the
full `run-all.py` did not finish inside the reviewer's window, so the Layer 6
Codex qualification digest chain is unverified by it. The orchestrator re-ran the
full gate after these fixes.

### The suite count was wrong all run, and the fix found it

**`test-feedback-sweep-parse.py` contributed zero units to the suite total.** It
used bare `unittest.main` rather than the house `run_counted`, so it printed no
summary line and `run-all.py` reported
`PASS test-feedback-sweep-parse (no summary)`, counting nothing from it.

This was invisible for the whole run because the number kept moving for other
reasons. It surfaced only when adding six regression tests did not change the
total at all: 7983 before, 7983 after. That is the tell.

**What was actually at risk.** Not failure detection: a nonzero exit is a `FAIL`
whatever the summary says, so a broken test would always have failed the gate.
What was broken was the measurement. G7's contract is that the count increases
against the G0 baseline of 7659, and it did, to 7983, but **none of that increase
came from this feature**. Its entire test surface, 6028 counted units across 90
tests, was absent from the number that exists to prove the feature was tested.

A test file that runs, gates correctly, and reports zero is the same defect class
this spec caught three times internally: coverage that looks present and measures
nothing. It is worse here, because the thing it fooled was the gate.

Wired to `run_counted`. A named class or method still routes through plain
unittest, so iterating on one test stays cheap, and the reason sits in a comment
so it is not reverted as noise. **True total: 14011/14011**, L4 6253 to 12281.

An earlier worker had already noticed the adjacent half of this, that Layer 4
discovery is not manifest-gated, so the file ran without its manifest row. The
manifest row supplies the label and baseline; `run_counted` supplies the count.
Both are needed and neither implies the other.

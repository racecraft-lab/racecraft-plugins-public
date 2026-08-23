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

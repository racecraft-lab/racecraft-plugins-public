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

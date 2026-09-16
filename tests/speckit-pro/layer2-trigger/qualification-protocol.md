# Trigger qualification and scoped feedback

The provider-free planner and comparator do not establish native qualification.
An accepted PR-core result covers only its declared selection. Unknown or global
impact expands the selection to the full corpus. Keep historical evidence intact;
missing parser context makes an old run diagnostic, not retrospectively eligible.

## Frozen coverage

The reviewed inventory accounts for all 438 original occurrences and retains all
14 protected identities. Its revised 23 host/skill corpora contain 217 cases:
105 Claude and 112 Codex. Three trials in each of two behavior arms require 1,302
native launches, a 50.46% reduction from 2,628. The minimum reduction target is
met; the 200-case stretch target is not. This is launch arithmetic, not a measured
token, billing, latency, or behavior result.

Semantic review approved the inventory with SHA-256
`0dfbf5670912e7806c7b588394c7ffd25d1ab8dc01acca1a9263f9df2151bdf1`.
Any edit invalidates that approval. Do not prune cases after observing outcomes.

## Controlled comparison

For the closure experiment, both arms use the same final runner, parser, corpus,
inventory, fixtures, and skill catalog. Only the `no-speckit-skill` description
changes. The baseline description is recovered from the parent of public commit
`6ef717ed` (PR #572); the candidate is that commit's approved description, still
present in baseline commit `42f4afe5bd2a319f81ea4b28799ec13bfa8e6107`.
The exact strings and source paths are in `controlled-descriptions.json`.
This trigger baseline differs from the **autopilot performance** baseline, which
uses the unchanged installed harness at the latter full commit.

Freeze a `trigger-experiment/v1` only after integration and artifact generation.
Review its exact roster, raw inventory digest, parser/catalog/fixture identities,
model and CLI versions, trial settings, scope, and controlled description digests.
The manifest must include positive integer `trial_timeout_seconds`. The campaign
call's `--timeout` must equal that value; both native runners retain it in report
metadata and independent replay rejects a missing or different value. Changing
the timeout requires a newly reviewed manifest and invalidates prior concurrency
qualification. Historical reports without this evidence remain diagnostic.
Do not substitute a current runner with the historical runner: that would vary
more than the approved behavior difference. Do not treat placeholder pins or an
approval-shaped JSON object as a user's authorization.

Preserve the existing host model-evidence policy. Codex's exact requested model
and CLI argument binding may qualify under its existing `requested-only` policy
when the native stream omits a resolved model identifier; report the resolved
identifier as null, not as an observed backend identity. Compare resolved model
identifiers when present, reject contradictions and cross-arm policy changes,
and retain the existing Claude resolved-model requirements. The official
[Codex non-interactive guide](https://learn.chatgpt.com/docs/non-interactive-mode)
does not promise a model identifier on every JSONL event. This limitation is not
permission to substitute a model or relax other trial-eligibility checks.

## Launch authorization and isolation

Every campaign needs exact retained authorization for its manifest and launch
budget under one of the versioned contracts below. V1/v2 require a
transaction-specific user message or adjacent reply; the narrow v3 contract
permits only its bounded standing-grant exercise. Reserve identities before
launching; unknown outcomes consume budget. There are no automatic retries.
Recover owned processes and artifacts before requesting subsequent
authorization. Keep credential material outside evidence.

`trigger-campaign-approval/v1` retains its exact source-message contract.
`trigger-campaign-approval/v2` additionally permits a prospective contextual
reply only when the trusted recorder preserves the exact canonical assistant
request and following user response as an explicitly adjacent pair in one
retained session. Both observations retain their genuine message identity,
role, timestamp, source ordinal, exact content hash, and complete source-line
hash. This is recorder-observed user-visible adjacency, not a fabricated native
`reply_to` relationship. The entire v2 record remains part of the immutable
ledger authorization hash, and its manifest and budget must still equal the
launch request exactly.

V2 decision parsing is a finite whole-response grammar, not sentiment analysis:
case-insensitive `approved`, `yes`, `authorized`, or `I approve`, with only
whitespace/punctuation and an optional `please proceed`, `please finish the
goal`, or `finish the goal` continuation. Quotes, questions, arbitrary prose,
conditions, denials, hypotheticals, and later reversals fail closed. A response
for an older manifest cannot authorize the changed observer bytes or a newly
hashed campaign; present the final manifest and budget again and retain a fresh
adjacent response.

`trigger-campaign-approval/v3` is a one-shot exercise of the retained standing
grant for the already approved issue-573 full-trigger goal; it does not weaken
or reinterpret v1/v2 adjacency. The ledger-hashed record must preserve genuine
user observations for the narrowly parsed standing grant and existing-quota
directive, plus an independent no-revocation review through the latest retained
user message before source freeze. It must
embed the exact reviewed manifest and bind the approved plan, frozen source and
observer, continuity assessment, terminal predecessor, new output directory,
and a 1,302-launch budget for exactly 217 cases, three trials, two arms, and one
serial worker. Runtime validation rechecks the live manifest, identities,
inventory, descriptions, output, budget arithmetic, and serial worker before
any output, ledger, lease, or provider action.

V3 authorizes one new campaign using available quota only. It cannot transfer
an old approval or ledger, retry or regrade old work, refund charged launches,
reset quota, redeem credits, or purchase quota. Unknown outcomes remain charged.
Any changed experiment, source binding, manifest, budget, predecessor,
continuity result, later revocation, or extra field requires a different valid
authorization record; campaign-specific evidence stays in that record rather
than in repository code.

### Prospective case-level carry-forward

The versioned `trigger-case-carry-forward/v1` component and
`trigger-campaign-approval/v4` authorization are a separate prospective path.
V4 extends the retained standing-authority and independent-review provenance;
it does not invent a new exact user-confirmation sentence. Its review binds the
new manifest, exact source component, terminal predecessor manifest and
approval, frozen ledger bytes, terminal interrupted-ledger JSON, terminal
evidence and cleanup review, canonical roots, source-stability review, exact
cohort, both parser closures, narrow compatibility decision, and accounting.
Legacy V1-V3 dispatch and rejection remain unchanged.

The SQLite ledger is hashed as inert bytes and is never opened as a database.
All row identities are derived instead from the frozen terminal interrupted-
ledger snapshot. Admission takes all and only baseline cases with exactly
trials 1, 2, and 3 complete, ordered by the full predecessor roster: 137 cases
and 411 trials, including both behavior failures and excluding the partial
invalid case as a whole. The retained partial experiment is independently
derived by filtering that roster, changing only `qualification_scope` to
`pr-core`, and recomputing `corpus_sha256`; its canonical digest must be
`959b2740ff161e155f5d1f5d645944a7f603d614479a92b3c056c29bafb96f51`.

Every external file is opened once through a bounded, no-follow descriptor
walk retained from the trusted filesystem root through every absolute-root
ancestor and then every relative artifact component. The walk permits only
appropriately owned and protected system ancestors, requires the declared
external root to be owned by the current user without group/world write, and
revalidates the whole retained descriptor/path chain after the read. It binds
owner, mode, regular-file type, all ancestor identities, descriptor identity,
size, and the exact bytes that are hashed and parsed.
Live SQLite sidecars, path traversal, links, replacement, growth, or a second-
read swap fail before output, ledger, lease, reservation, workspace, or native
process mutation. An immutable reviewed dual-replay artifact binds distinct
old/current module namespaces, closure roots and file maps, loaded `__file__`
paths, identical raw/context hashes, and exact typed 411-trial projections.
Each isolated verifier must itself accept `valid` and `trial_valid` and
recompute the execution and cleanup checks; retained Boolean assertions cannot
substitute for that computation. Loaded closure bytes are hashed both before
and after replay. The isolated import mechanism executes only the securely read
and digest-verified byte map; neither initial modules nor lazy imports reopen a
pathname. Extracted closure directories are never placed on `sys.path`, every
approved sibling or lazy import is served from that map, and non-approved
imports may resolve only through identity-checked standard-library roots.
Thus an unapproved sibling cannot shadow even a standard-library module, and
every executed closure byte string appears in the consumed-byte record.

The new manifest keeps the full 217-case roster, three trials, both arms, pins,
timeout, descriptions, catalog, fixtures, and serial-only execution. The
compatibility record retains the exact old/new SHA-256 pair for every changed
closure file and limits the transition to the approved canonical complete
Codex relative-path `sed` read plus its enumerated carry-forward generator,
CLI, validation, scheduler, and comparison bookkeeping paths. The new ledger
authorizes and contains only the
891-identity complement; carried cases create no row and no provider call. A
source-aware final index references old evidence under its old labels instead
of copying or retagging it. Final comparison revalidates the full V4 approval,
requires an exact deterministic fresh submanifest and an immutable completed
fresh ledger containing exactly the approved 891-row complement, then requires
the exact disjoint, ordered 411+891=1,302 identity union. Old 414 charged
attempts remain separate, for a maximum historical-plus-new accounting of
1,305. Carry-forward is serial, non-contiguous, both-arm, full-scope, and never
qualifies timing, pilot concurrency, retries, refunds, resets, or regrading.

Before creating output, a request, or a fresh SQLite ledger, admission performs
a read-only cleanup check and confirms that the global lease is absent or an
unlocked idle state. Inspection errors and unknown lease/process state fail
closed. Exact retained runner and child process/group ownership fingerprints
must be absent; unrelated later reuse of an old numeric PID or PGID is not
treated as predecessor ownership. This check verifies the signed complete file
tree for all 137 carried cases plus the terminal partial case, including all
138 runner command/start fingerprints, 410 distinct carried child groups, the
terminal groups, and every recorded workspace, against one fail-closed current
process snapshot. An existing V4 output root is admitted read-only before the
global lease: an empty or partial publication, changed immutable request,
unsafe file, live SQLite sidecar, malformed authorization, incomplete case
reservation, or non-complete retained row is rejected without touching the
lease. Admission validates every allowed saved artifact rather than accepting
its name alone: the serial tree must have safe containment, types, modes, and
no links; `serial.start.json`, timing, baseline/candidate indexes, `ledger.json`,
and interrupted snapshots must have their exact schemas, manifest and schedule
bindings, source-aware lineage, timestamps, authorization, completeness, and
state progression. Artifacts that cannot validly exist for the current ledger
state are rejected. A valid resume set and the complete lineage are checked
again under the acquired lease. The lineage guard then runs inside the
per-case failure boundary immediately before every fresh reservation, so drift
between cases stops queued work without another reservation or provider call.
Legacy V1-V3 campaigns retain their pre-dispatch interrupted-ledger snapshot
contract; the zero-new-reservation suppression applies only to V4 carry-forward.

### Reviewed multi-generation continuation

`trigger-campaign-approval/v5` and `trigger-case-carry-forward/v2` add a
separate dispatch without changing V1-V4 or carry-forward V1. V5 reuses the
retained standing authority, but its independent review binds the exact fresh
request, full logical dual-arm manifest, ordered flat history list, observer
replays, accounting, and policy. It does not fabricate an exact user
confirmation or transfer a predecessor campaign's approval or budget.

Each history is a distinct physical generation identified by its canonical
output root and exact ledger bytes. Its own manifest, approval, inventory,
terminal ledger snapshot, evidence indexes, nested reviewed component,
ownership inventory, source commit/tree, and review digest are validated under
their original labels. Terminal history admission is read-only and permits
complete and invalid or unknown charged rows; it is deliberately separate from
V4 destination-resume admission, which still accepts only complete rows. Every
reserved case-arm pair must have one review-digest-bound case-tree descriptor.
The validator derives the exact runner, child-group, and removed-workspace
inventory from those strongly read launch, execution, replay-context, cleanup,
and trial bytes. The host-specific replay workspace must exactly equal the
cleanup workspace and be absent;
caller-supplied empty or incomplete ownership lists do not establish absence,
including for a charge-only generation with zero valid coverage. Every
charged row counts by generation, ledger, arm, case, and trial. Reusable
coverage counts only disjoint semantic `(arm, case, trial)` identities from
three-trial, all-complete case-arm pairs, including behavior failures. Partial,
invalid, and unknown pairs are excluded atomically and are never refunded,
regraded, reset, or automatically retried. A separately reviewed new
generation may re-execute an excluded invalid identity while retaining its
historical charge; it may never re-execute carried-valid evidence.

An interrupted generation with complete pairs but no published final arm index
uses the closed `reviewed-partial` descriptor. Only the exact-hash partial index
JSON is read from its separately reviewed root, which must not overlap the new
destination or any historical output tree. Every inventory, description,
cleanup, report, record, stdout, and stderr reference inside that index remains
rooted in the immutable historical output and is read through the bounded,
owner-and-mode checked, no-follow descriptor path. Complete case IDs are
derived from terminal ledger rows in manifest order, not accepted from the
descriptor. Index bytes are re-read after parser replay, and final comparison
performs the same history admission again; path replacement, hard links,
symlinks, forged same-name artifacts, and post-admission drift fail closed.

The V2 observer set is deliberately closed to the original retained observer,
the exact successor observers established by reviewed nested V1 lineages, and
the final current observer. Every contributing `(generation, arm)` source is
listed once. A source already produced by the final observer has `replay: null`;
every older source binds an exact-hash `trigger-observer-replay/v1` artifact in
its review root. That artifact covers the source index's exact trial set and
securely rereads every retained stdout stream, executes the loaded and
source-verified final parser with its bound replay context, recomputes typed
validity checks, and requires that result to equal both the immutable record
projection and reviewed historical projection. A third observer or a missing,
duplicated, relabeled, stale, parser-rejected, or
unreviewed transition is rejected. Nested V1 validation checks its retained
historical successor closure without relabeling it as live current; ordinary
V1-V4 admission remains pinned to the live observer exactly as before.

The exact fresh request must equal the full logical manifest minus all carried
valid identities. This permits a candidate-only 217-pair request when all 217
baseline pairs are already valid. `trigger-evidence-index/v3` publishes each
logical arm from its reviewed historical sources plus an optional fresh source;
the no-fresh-baseline case has no empty or synthetic fresh-baseline manifest.
`trigger-carry-forward-lineage/v2` and the published logical manifest bind the
physical histories, semantic union, and cumulative ceiling. Final comparison
re-admits every history and its observer transition, verifies the completed
fresh ledger, and requires the exact ordered 217-baseline plus 217-candidate
union before qualification. All multi-generation timing remains
non-contiguous and ineligible.

For the reviewed recovery scenario, the three physical histories contain
414 + 3 + 243 = 660 charged launches: 651 complete baseline trials and nine
invalid charges. The fresh candidate request is exactly 651 launches, giving
the full 1,302 valid-trial comparison and a maximum cumulative charge of 1,311.
The V5 destination must be absent and must not equal, contain, or be contained
by any historical output; historical outputs are also pairwise non-overlapping.
Every history binds the exact same global lease path that execution acquires.
Historical bytes, cleanup, derived process absence, and the unlocked idle lease
are checked before any output, ledger, lease activation, reservation, or
provider call, then byte/evidence lineage is
rechecked immediately before every reservation while the new campaign owns the
same global lease. That exact path binding is what permits the under-lock replay
to skip trying to acquire its own lease a second time.

First run the 48-launch pilot: four reviewed cases per host, three trials, one
fixed behavior arm, under serial and two-worker schedules. Keep trials within a
case sequential. Both schedules must have valid complete evidence, unchanged
behavior, disjoint workspace/config/temp/output ownership, and confirmed cleanup.
Two workers qualify only when elapsed time is at least 25% below serial. Retain
all raw start/end observations; never report missing or invalid work as faster.
Full campaigns default to serial until this pilot qualifies a global ceiling of
two workers. More workers require another approved experiment.

The pilot is **additional**: 48 pilot launches plus 1,302 full-matrix launches
equals 1,350 planned launches, before any separately approved campaign. A failed
pilot does not authorize a replacement run or a larger budget.

## Evidence and acceptance

Retain immutable per-trial stdout, execution metadata, parser replay context,
Codex witness bodies, cleanup evidence, and artifact digests. Publish the evidence
index only after those artifacts are complete. Independently replay the native
parsers and join by stable case/trial identities, never report order.

Report completeness, execution validity, candidate acceptance, regressions, and
qualification separately. Positive target hits falling from 3 to 2 and negative
hits increasing from 0 to 1 are regressions even if Boolean grades pass. Positive
0 to 1 remains below the unchanged 0.5 acceptance threshold. Comparator exits are
0 accepted, 1 valid behavioral failure, and 2 invalid or incomplete evidence.

Artifact hashes establish byte integrity, not independent provider authorship.
Keep the trusted orchestrator's actual execution and approval observations with
the campaign record; worker assertions or copied messages are not that authority.

Do not close the public issue until all eight criteria and a complete eligible
dual-host matrix are satisfied. The broader performance program additionally
requires matched completed autopilot benchmarks, under-two-hour full workflows,
and at least 50% lower per-host median runtime. PR feedback under 15 minutes is
measured only for the declared feedback scope. Human UAT is pending until done.

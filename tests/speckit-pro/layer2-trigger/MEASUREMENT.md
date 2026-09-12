# Trigger measurement prerequisite

The Layer 2 trigger measurement prerequisite is **qualified** for the pinned
host interfaces and observation scopes in
[`measurement-capabilities.json`](measurement-capabilities.json). Qualification
allows a frozen baseline/candidate matrix to run. It does not itself authorize
corpus pruning or satisfy the broader taxonomy and comparator work in
[issue #573](https://github.com/racecraft-lab/racecraft-plugins-public/issues/573).

Qualification is fail-closed. A run is eligible only when it uses the canonical
model, reasoning, trial-count, and threshold parameters; passes the pinned CLI
and isolation preflights; records the no-retry launch contract; completes every
requested trial; and produces only valid observations in the declared scope.
A passing noncanonical or diagnostic run remains ineligible.

## Qualified observation scopes

### Claude: `claude-native-skill-tool`

Claude selection is observed through a completed, linked, model-initiated
`Skill` tool call. The observer validates the exact staged target or sibling
identifier, tool-use/result linkage, ordering, successful completion, terminal
result, and reported model identity. A target nonce is optional corroboration;
when emitted, it must appear in exactly one assistant text block as the first
nonblank line after the target selection. A nonce without its native target selection, or multiple,
unknown, malformed, or conflicting selections, is invalid. A sibling selection
is a valid target nonselection.

The runner pins Claude Code 2.1.269 and `claude-sonnet-5`. It launches with an
empty `--setting-sources` list, strict empty MCP configuration, a curated
environment, and `CLAUDE_CODE_MAX_RETRIES=0`. Qualification is limited to macOS
or Linux after the runner verifies the documented managed-settings locations
and the pinned `claude doctor` account-policy state. Any managed settings,
managed MCP, managed instructions, managed preference payload, version drift,
or reported retry invalidates preflight or the stream.

### Codex: `codex-body-read-attestation`

Codex 0.153.3 does not expose a native skill-selection event in its public exec
JSON. The qualified Codex scope therefore uses a behavioral attestation and
names that limitation rather than claiming native observation.

Every staged target and sibling retains its exact source description and gets a
minimal body containing a unique randomized 128-bit marker. A selection
requires both:

1. one command that proves access to the exact staged `SKILL.md` body, either
   through completed exact output from a qualified path-bound or bare read,
   completed leading output from a qualified `sed -n '1,<N>p' <exact-path>`
   first shell segment whose canonical numeric endpoint covers the complete
   staged body, or the private marker in a later completed agent message after
   that exact leading command starts; and
2. that skill's marker as the first nonblank line of one completed agent message.

The catalog preflight proves the exact source locator for every staged target
and sibling. When the pinned CLI renders an `rN/<skill>/SKILL.md` locator, the
harness derives that alias from the catalog, binds it inside the disposable
workspace to the relative `.agents/skills` root, and re-attests the link and
every resolved witness immediately before each trial. A collision, malformed
locator, different skill path, or changed link fails closed before launch.

The pinned public exec JSON omits the internal command working directory even
though Codex uses it while executing a skill read. The observer therefore also
accepts a bare `sed -n '1,<N>p' SKILL.md` command with a canonical numeric
endpoint that covers the complete staged body, but only when its completed
output byte-for-byte matches exactly one staged body and the command contains
no staged path or marker. Other bare commands, malformed or undersized ranges,
and additional shell segments remain invalid.

For the leading compound form, the parser requires the body at byte zero and
rejects a tail that names another staged skill path or emits any staged body or
selection marker; a successful tail may be silent. The post-start form also
rejects a command that contains any marker or a second staged path; it is valid
only when the marker appears after the command start. It applies both when the JSON stream omits command completion
and when a successful completion's retained output omits the leading body. When
retained output exists, any displaced staged body or marker still makes that
form invalid. This accounts for the official `codex exec --json` sample, which
shows a command start followed by an agent message and completed turn without a
matching command-completion event, without treating `aggregated_output` as a
documented complete stdout transcript. Outer exit, error, isolation, and
cleanup checks still apply at the trial layer.

Each accepted witness records `read_mode` as `exact-output`,
`leading-compound-output`, or `post-start-marker`. An exact body read without a
marker is a valid consultation/nonselection. A marker without its matching
read, an unknown or repeated marker, multiple body reads, a command without one
of those proofs, a reported failed command, or connected-tool activity is
invalid. A sibling's read-plus-marker is a valid target nonselection. This
makes the behaviorally selected staged-skill set observable within the declared
scope, while preserving the distinction from a native activation event.

The runner pins Codex 0.153.3, `gpt-5.6-sol`, and low reasoning. It uses strict
configuration isolation, disables unrelated features, and installs a dedicated
ChatGPT-auth provider with request and stream retries set to zero, WebSockets
disabled, and unbounded connection retries disabled. The existing Codex login
root remains available to the CLI through the public
`CODEX_HOME` variable, while command execution receives a disposable `HOME`
and `TMPDIR` inside the fixture. The named permission profile keeps the staged
repository read-only and grants write access only to that scratch directory, so
routine inspection has a writable cache location without exposing the real home
or granting shared temporary-directory writes. Network access remains disabled.
The per-trial launch contract attests each of these environment boundaries. On
qualified POSIX hosts, fd 0 is a fresh pseudo-terminal so the positional query
is the only prompt input. This bypasses Codex's documented non-terminal stdin
append path, whose
status output would otherwise invalidate the JSONL stream. The public JSON
stream does not attest backend model identity, so Codex records the requested
model and labels model evidence `requested-only`; it never upgrades that to a
resolved backend identity.

## Evidence and validity

Each evidence directory contains exact `case-NNN-trial-NN.jsonl` and
`.stderr.log` files, plus a `trigger-trial/v2` `.trial.json` record with their
paths and SHA-256 hashes. Files are created exclusively. Existing evidence
directories and report files are never reused.

The trial record contains stable logical case identity, case/trial ordinals,
the exact query and its hash, expected label, parser observations, the declared
observation scope, the launch contract, and typed supervision observations.
`provider_exit_code` is the observed child return code, or null if unobserved.
The legacy `exit_code` alias contains the same value; a timeout sentinel is not
an observed provider exit. Timeouts and interruptions have separate fields.

`stream_valid` records parser validity. `trial_valid` (and its legacy `valid`
alias) is the conjunction of execution-record completeness, process outcome,
stream structure, model evidence, selection evidence, no-retry/configuration
launch checks, bounded cleanup, process-group absence, and descendant checks.
`qualification_eligible` is true only when the trial is valid, its parser
completed a qualified observation, and the batch used canonical parameters.

Counts come only from canonically valid trials. `status: not_run` has null
counts and no observations. An incomplete or invalid case has a null trigger
rate, explicit executed and unexecuted counts, and cannot pass. Report-level
qualification additionally requires every case and trial to complete and remain
eligible.

`trial-stop.json` identifies the first invalid trial. Supervision exceptions
also retain a `.failure.json` diagnostic. `isolation-stop.json` preserves a
Codex isolation diagnostic when applicable. No report is synthesized for a
failure before provider launch; a missing report blocks comparison.

`arm-cleanup.json` is written after workspace removal and records the actual
runner exit, cleanup error, and whether the workspace is absent. A report is
preliminary until that receipt is checked. Runner exits are:

| Exit | Meaning |
| --- | --- |
| 0 | Cases passed; workspace cleanup still requires its receipt |
| 1 | Behavioral failure, invalid evidence, or preflight/runtime error; inspect the report and receipt |
| 2 | Workspace cleanup or cleanup-receipt retention failed |
| 128 + signal | Interrupted runner, unless workspace cleanup failure superseded it |

A comparator must independently validate raw hashes, containment, record
identities, parser replay, typed execution checks, summary agreement, runner
exit, qualification status, canonical parameters, and the cleanup receipt. It
must reject missing or ineligible evidence. Replaying historical JSONL cannot
reconstruct an unrecorded process exit or launch contract.

## Scope boundaries and remaining work

Layer 2 measures implicit model selection, not forced slash-command expansion.
Claude's documented `UserPromptExpansion` hook and Codex direct invocation are
therefore outside this qualification scope. They must be separately specified
and qualified before evidence from those paths is accepted.

The owned POSIX process group and staged workspace are the cleanup proof scope;
unrelated processes are not observed or claimed. Windows descendant cleanup is
not qualified. Provider-side behavior invisible to the pinned public interfaces
cannot be reconstructed; qualification relies on the explicit no-retry controls
and rejects every reported retry or error event.

One bounded provider canary per host validated each qualified selection path;
one earlier Codex transport probe validated the dedicated no-retry provider.
The full frozen baseline/candidate matrices, comparator validation, corpus
dispositions, independent pruning review, and issue #573's broader work remain
separate gates.

Sources: [Claude hooks](https://code.claude.com/docs/en/hooks#userpromptexpansion),
[Claude tools](https://code.claude.com/docs/en/tools-reference),
[Claude CLI](https://code.claude.com/docs/en/cli-reference),
[Claude settings](https://code.claude.com/docs/en/settings),
[Claude model configuration](https://code.claude.com/docs/en/model-config#model-aliases),
[Codex pinned event schema](https://raw.githubusercontent.com/openai/codex/rust-v0.153.3/codex-rs/exec/src/exec_events.rs),
[Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode#make-output-machine-readable),
and [Codex skills](https://learn.chatgpt.com/docs/build-skills#how-chatgpt-and-codex-use-skills).

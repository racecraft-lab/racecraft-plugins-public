# TLC: finite states and progress rules

Use TLC when the selected behavior has a manageable finite state space or needs
native TLA+ fairness. Start from the design question and existing selection. A
TLC installation does not enroll a feature.

## A small progress example

The counter starts at zero, increases to two, and stays there. We check two rules:
it stays between zero and two, and it eventually reaches two. The second rule
needs an explicit scheduling assumption: an increment that stays possible will
eventually run. Without that assumption, the specification permits waiting
forever at zero. This is a useful counterexample, not a checker failure.

After authorized installation, copy `examples/formal/counter-tlc/CounterTLC.tla`
and `.cfg` from this skill into `formal/counter-tlc/`. Merge the example
`catalog.json` into `.specify/formal-methods.json`, preserving unrelated entries.
Explicitly select `counter-tlc` in the workflow, with a rationale and `model`
evidence. Follow the shared formal checkpoint procedure to preview and run it.

The initial model passes. In a separate learning copy, remove
`/\ WF_count(Next)` from `Spec` and rerun: TLC finds a behavior that never reaches
the limit. Explain the waiting loop before restoring the learning copy. In real
work, a changed fairness assumption needs the approved design decision; never
add fairness merely to turn a failed requirement green.

## Version and configuration

The integration targets the official [TLC 1.7.4 release](https://github.com/tlaplus/tlaplus/releases/tag/v1.7.4).
Its JAR reports TLC 2.19 internally; the release is identified by `X-Git-Tag:
v1.7.4` and the pinned artifact, not by guessing from that banner. The downloaded
JAR matches the release's published SHA1 and has SHA256
`936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88`.
Use a dedicated directory without optional `CommunityModules.jar` sidecars.
Declare every local imported model input.

TLC requires Java 11 or newer in this integration. The catalog explicitly sets
the Java command, maximum heap, timeout, output budget, and `max_set_size`.
The adapter uses one worker, breadth-first exploration, a fixed fingerprint
polynomial/seed, and isolated metadata and temporary directories. A sandbox may
need to permit TLC's local RMI socket; a denied run remains inconclusive.

- Use `mode: finite` for invariants, or `mode: temporal` when the catalog includes
  temporal properties. These modes require `bounds.max_set_size`.
- Use either catalog `init`/`next` matching native INIT/NEXT, or catalog
  `specification` matching native SPECIFICATION. The latter preserves native
  fairness and stuttering. Do not supply both forms.
- Native INVARIANT/PROPERTY lists must exactly match the catalog's complete
  property-to-requirement mapping. The checker receives the original config.
- State/action constraints and constants delimit the checked model. Describe
  them as assumptions. Temporal checking with symmetry is outside this profile.
- Simulation, an interrupted search, zero explored initial states, and missing
  properties never satisfy a formal checkpoint.

## What a pass establishes

TLC explores the reachable states of the configured finite model. A completed
temporal run checks its behaviors under the recorded assumptions. Report the
finite domain, constraints, fairness, and TLC's fingerprint-collision estimate.
This is evidence about that model; arbitrary larger systems and application
executions need separate justification or selected trace validation.

See the official [TLC command guide](https://docs.tlapl.us/using:tlc:start) and the
pinned [result-code implementation](https://github.com/tlaplus/tlaplus/blob/v1.7.4/tlatools/org.lamport.tlatools/src/tlc2/output/EC.java).
Never use a nightly-only flag with the qualified release. Installation remains
an explicit authorized operation; `formal-doctor` and `formal-check` install
nothing. Current execution evidence and profile limits live in the qualification
record; do not infer compatibility for an untested OS, JVM, or container image.

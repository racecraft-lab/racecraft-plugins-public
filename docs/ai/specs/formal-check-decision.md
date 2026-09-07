# Formal check decision record

Date: 2026-09-06. Status: decided; decision record only. No autopilot
reference, agent, runner helper, discovery-table, or workflow change lands
with this record. The `FORMAL_CHECK` slot, the Formal Model plan section, and
the grill-me branch are specified here so the wiring layer has a contract to
implement.

This record answers the three questions the "Quality Gauntlet" memo's item 9
spike asks:

1. Which toolchain runs the check, and where.
2. How a model maps to implementation tests so the check is not decorative.
3. How grill-me decides that a spec needs a model at all.

Every command, flag, exit code, and version requirement below was read from
the tool's official documentation or source on 2026-09-06. Anything the docs
did not settle is listed under **Unverified**.

## Summary of decisions

| Question | Decision |
| --- | --- |
| Model checker | TLC from `tla2tools.jar` (tlaplus/tlaplus release v1.7.4 or the 1.8.0 nightly), explicit-state, bounded by the `.cfg`. Apalache is opt-in per model, not a default. |
| Runtime | Java 11+ for TLC. Apalache needs Java 21+. One JDK 21 satisfies both. |
| Where it runs | GitHub-hosted `ubuntu-latest` with `actions/setup-java` by default. HAL's fireactions pool (`hal-linux`, ephemeral Firecracker microVMs, 6 vCPU and 4.5 GB each) is the option for a model that needs a longer run, for any racecraft-lab repository the runner group admits. |
| Not decorative | Every model ships with a trace-validation harness: the implementation emits a JSON trace of the modelled actions and TLC checks that trace against the spec. A model with no trace harness is `advisory`, never `populated`. |
| grill-me | A hybrid branch: the skill scans the spec and surrounding code for concurrency signals, presents the evidence, and the operator confirms, corrects, or extends. A confirmed signal set adds a Formal Model section to the plan and populates `FORMAL_CHECK`. |
| Slot | `FORMAL_CHECK` joins the closed `slot` enum in the discovery table when the wiring layer lands. Its signal file is `specs/<feature>/model/<Name>.cfg`. It runs at final verification only. |

## 1. Toolchain

### TLC (default)

- **Artifact:** `tla2tools.jar` from the tlaplus/tlaplus releases page.
  v1.7.4 is the current versioned release; every commit to master is also
  built into the `v1.8.0` pre-release. Pin the versioned release and record
  its sha256 in the consumer repository's `.specify/quality-gates.json`
  `formal_check.tla2tools_sha256` field once the wiring layer adds it.
- **Runtime:** "The TLA⁺ tools require Java 11+ to run." (repository
  `USE.md`). `java -jar tla2tools.jar` is aliased to `tlc2.TLC`; with the
  jar on the classpath, `java tlc2.TLC` and `java tla2sany.SANY` run the
  checker and the parser.
- **Command (gate form):**

  ```text
  java -XX:+UseParallelGC -jar {plugin_root}/vendor/tla2tools.jar \
    -config {rules_path} -workers auto -cleanup -noTE -tool \
    -metadir {metadir} {spec}
  ```

  `-config` names the `.cfg` ("defaults to SPEC.cfg"). `-workers auto`
  uses one thread per core. `-cleanup` removes the states directory.
  `-noTE` skips generating a trace-exploration spec on a violation, which
  keeps the run write-free apart from `-metadir`. `-tool` surrounds output
  with message codes so the runner can parse it. Deadlock checking stays on;
  `-deadlock` would turn it off and a model whose author wants that sets it
  in the plan section's `tlc_flags`.
- **Exit codes** (`tlc2.output.EC.ExitStatus`): `0` success; `10`
  assumption violation; `11` deadlock; `12` safety violation; `13` liveness
  violation; `14` assertion; `75`, `76`, `77` evaluation failures; `150`
  spec parse error; `151` config parse error; `152` state space too large;
  `153` system error; `255` generic error. The gate treats `0` as pass,
  `10` through `14` as a red gate with the trace attached, `150` and `151`
  as a blocking authoring error, and `152`, `153`, `255` as a tool failure
  (exit 2 semantics in the Quality Gates table, which blocks like a missing
  tool).
- **Trace dump:** `-dumpTrace json <file>` writes a counterexample as JSON;
  `-loadTrace json <file>` reads one back. Both exist in the current tools
  and are the format the trace-validation harness uses.
- **Liveness with workers:** v1.7.4's release note fixes "Running liveness
  checking with multiple workers can cause unsoundness". Pin v1.7.4 or
  newer; never an older jar.

### Apalache (opt-in)

- **Why not default:** Apalache is a symbolic bounded checker over an SMT
  solver. It handles unbounded integers and large constants TLC cannot
  enumerate, but it checks up to `--length` steps only and needs "at least
  4GB of memory". A team that does not already know why they need it
  should not be offered it by default.
- **Runtime:** "Java 25, using the Eclipse Temurin or Zulu builds of
  OpenJDK. Released artifacts maintain bytecode compatibility with Java 21
  and should run on Java 21 or newer" (installation docs). Hence JDK 21 as
  the single runner JDK.
- **Command:**

  ```text
  apalache-mc check --config={cfg} --inv={Inv1,...} --length={n} \
    --out-dir={metadir} {spec}
  ```

  Output lands under `--out-dir` (default `./_apalache-out`, one
  subdirectory per run keyed by the spec file name).
- **Unverified:** Apalache's documented CLI does not state exit codes for
  violation versus error. The wiring layer must read them from the source
  before Apalache can populate the slot; until then Apalache runs are
  `advisory`.

### Where it runs

- **Default: GitHub-hosted `ubuntu-latest`.** Every workflow in this
  repository already targets hosted runners. `actions/setup-java` with
  `distribution: temurin` and `java-version: 21` covers both tools. The jar
  is cached with `actions/cache` keyed on its sha256.
- **HAL, verified over SSH on 2026-09-06.** Host: x86_64 with AMD-V, 32
  cores, 62 GB RAM, Ubuntu 24.04.4 LTS. It runs fireactions v2.0.4 as a
  systemd service: an orchestrator that serves GitHub Actions jobs from
  Firecracker microVMs, where "each virtual machine is created from scratch
  and destroyed after the job is finished, no state is preserved between
  jobs, just like with GitHub hosted runners" (fireactions README). One
  pool, `hal-linux`: ten replicas, runner labels `self-hosted`, `Linux`,
  `X64`, `hal-linux`, registered to the racecraft-lab organization under a
  runner group through a GitHub App, each VM 6 vCPU and 4608 MiB from the
  image `ghcr.io/racecraft-lab/hal-linux-runner`. So "HAL runners" in the
  memo means that pool, and a job there sees 6 vCPU, not 32 cores.
- **Public repository rule.** GitHub's hardening guide states: "Self-hosted
  runners should almost never be used for public repositories on GitHub,
  because any user can open pull requests against the repository and
  compromise the environment", and asks that a reused host give a JIT
  runner "a clean environment". fireactions' destroy-after-job VMs are
  that clean environment, and the org runner group's repository access
  list decides which repositories may target the pool. This repository
  keeps `FORMAL_CHECK` on hosted runners unless the operator admits it to
  the group; the record does not make that call.
- **Sizing on HAL.** `-workers auto` gives TLC 6 threads per job. Apalache's
  "at least 4GB" recommendation nearly fills the 4608 MiB VM, so an
  Apalache job on HAL needs a larger pool (a second `pools:` entry with a
  bigger `machine_config`) rather than the default one. Target the pool
  with `runs-on: [self-hosted, Linux, X64, hal-linux]`.

## 2. Mapping a model to implementation tests

A TLC run that only checks a hand-written `.tla` proves the model, not the
code. The check is decorative unless something ties the two together. The
decision is **trace validation**, the approach described in "Validating
Traces of Distributed Programs Against TLA+ Specifications" (Cirstea, Kuppe,
Loillier, Merz, 2024, arXiv 2404.16075): the implementation is instrumented
to record the events that correspond to the spec's actions, and the trace is
checked as a constrained model-checking problem with TLC.

Concretely, a Formal Model is four files under `specs/<feature>/model/`:

| File | Owner | Purpose |
| --- | --- | --- |
| `<Name>.tla` | plan author | The model: variables, `Init`, `Next`, the invariants and temporal properties the spec's rules require. |
| `<Name>.cfg` | plan author | `SPECIFICATION`, `INVARIANTS`, `PROPERTIES`, and `CONSTANTS` bounds small enough to finish on a hosted runner. This file is the `FORMAL_CHECK` signal. |
| `<Name>Trace.tla` | plan author | A refinement module that reads `trace.json`, constrains `Next` to the recorded steps, and asserts the same invariants. TLC checks it with the same jar. |
| `trace.json` | a test | Written by one implementation test per modelled action set: the test drives the real code through a scenario and appends one JSON entry per action with the variable updates the spec names. |

Rules that make the tie real:

- **Action map.** The plan's Formal Model section lists each spec action
  next to the implementation function that emits its trace entry. A
  reviewer can see that `Enqueue` is `queue.push` in one line. An action
  with no emitter is a plan gap, not a passing gate.
- **Two runs, both required.** `FORMAL_CHECK` runs the model (`<Name>.cfg`)
  and then the trace refinement (`<Name>Trace.cfg`) against the
  `trace.json` the test suite just produced. Either exiting nonzero fails
  the slot. A model that passes while its trace refinement fails is the
  interesting result: the code diverged from the model.
- **The trace test is a normal test.** It lives in the project's test tree,
  runs under `UNIT_TEST` or `INTEGRATION_TEST`, and is subject to the same
  mutation floor as any other test. That is what stops the harness from
  being a fixture that always writes the same file.
- **Advisory without a trace.** A model with a `.cfg` but no `Trace` module
  or no test that writes `trace.json` is recorded as `advisory` in the
  Quality Gates table and never blocks. The workflow file says why, so the
  gap is visible at review.
- **Bounded on purpose.** The `.cfg` constants stay small enough for the
  run to finish in a few minutes on a hosted runner. A model that needs
  more is the private-runner case above, and the plan section records the
  expected run time.

## 3. The grill-me branch

The memo asks for a hybrid: the tool finds the evidence, the operator
decides. The branch joins the three branches the interview protocol already
resolves before synthesis (module and interface deltas, terms, verification
gates) as a fourth, conditional one.

### Scan

Before asking, grill-me scans the spec text and the code the module deltas
name for concurrency signals. A signal is a durable pattern, not a keyword
hit:

| Signal | Evidence looked for |
| --- | --- |
| Shared mutable state across actors | Two or more writers to one store, queue, file, or row named in the spec or the touched modules. |
| Ordering or retry protocol | Words of protocol in the spec (`retry`, `ack`, `lease`, `lock`, `idempotent`, `exactly once`, `at least once`) or a state machine in the deltas. |
| Distributed participants | More than one process, service, worker, or hook that must agree on an outcome. |
| Invariant stated as a rule | A spec rule of the form "never", "always", "at most one", or "eventually" over system state. |
| Existing model | A `specs/*/model/*.cfg` in the repository, or a `.tla` anywhere in the tree. |

### Present

The branch presents the findings as evidence, one line per signal with its
file and line or spec section, plus the recommendation:

- No signal: recommend "no model"; record the branch as resolved from
  evidence with the scan summary, so a skipped branch is never mistaken for
  an unscanned one.
- One or more signals: recommend a model, name the candidate invariants in
  the spec's own words, and ask one decision question: confirm, correct
  (drop or reword a signal), or extend (add one the scan missed).

### Record

The operator's answer lands in the Design Concept's Verification Gates
section as a `FORMAL_CHECK` line. Downstream:

- `/speckit-plan` adds a **Formal Model** section to the plan when the line
  is present: the action map, the invariants, the bounded constants, the
  expected run time, and the checker (`tlc` or `apalache`). The plan
  template gains the section in the wiring layer, in the same way the
  Module and Interface Deltas section landed.
- `detect-commands` populates `FORMAL_CHECK` when `specs/<feature>/model/
  <Name>.cfg` exists. The table row's `probe` is `java`; the jar ships
  under the plugin's `vendor/` directory or is fetched by the workflow, a
  choice the wiring layer makes.
- The slot runs at final verification only, after `MUTATION`, because its
  trace input comes from the test suite. It is never run at G0 or at a
  phase group; the Quality Gates table records `deferred` there, matching
  the mutation rule.

## Unverified

- Whether the `hal-linux-runner` image carries a JDK. The host's OpenJDK
  26.0.1 is not visible inside a microVM, so the job must run
  `actions/setup-java` or the image must be rebuilt with Temurin 21.
- Whether the `hal-linux` runner group admits this public repository. Read
  it from the organization's runner-group settings before routing any job
  here.
- Apalache exit codes on violation versus error.
- Whether the `-dumpTrace json` shape and the trace-validation paper's
  `trace.json` shape are the same document; the wiring layer fixes one
  schema and documents it under `speckit_pro_runner/contracts/`.
- Wall time of a hosted-runner TLC run at the bounded constants a typical
  plan will choose. Measure on the first real model before setting a
  timeout default.

## First-install checklist

1. Download `tla2tools.jar` v1.7.4, record its sha256, and vendor or cache
   it.
2. `actions/setup-java` with Temurin 21 in the consumer workflow; confirm
   `java -jar tla2tools.jar -h` prints the TLC usage.
3. Write one model with a trace refinement against an existing feature and
   run both `.cfg` files locally; record the wall time.
4. Add `FORMAL_CHECK` to the discovery table enum, schema, and validator
   test, with the `.cfg` signal and `java` probe.
5. Add the Formal Model section to the reviewability preset's plan template
   and its Layer 1 lock.
6. Add the grill-me scan and question to `interview-protocol.md` on both
   platforms, with a Layer 3 eval that feeds a spec containing a retry
   protocol and expects the signal presented.
7. To use HAL: confirm the runner group admits the repository, confirm the
   runner image has a JDK or add `actions/setup-java` to the job, and target
   `runs-on: [self-hosted, Linux, X64, hal-linux]`. For Apalache, add a
   larger fireactions pool first.

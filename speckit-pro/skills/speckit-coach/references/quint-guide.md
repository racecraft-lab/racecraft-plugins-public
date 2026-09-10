# Optional Quint modeling

Quint is useful when a small executable model would clarify a difficult rule and
its syntax is more approachable for the team than TLA+. Start from the same
plain-English question in [formal-methods-guide.md](formal-methods-guide.md).
Recommend ordinary tests when they adequately address the risk. An installed
Quint plugin, a TypeScript project, or an existing model does not select a feature.

Quint describes a model; it does not translate an application's Python,
TypeScript, or Swift source into a verified implementation. Apalache checks the
selected model. Optional observed implementation traces use a reviewed action
and state projection, described in [implementation-traces.md](implementation-traces.md).
Generating test inputs from a model or replaying a counterexample is useful but
does not establish implementation conformance.

## Use the upstream guidance on demand

Reuse the official Quint team's language and modeling skills as references:

- [Quint language guidance](https://github.com/quint-co/quint/blob/6fb2924e00707cef6dbc5e30db606d555c447123/skills/quint-lang/SKILL.md)
- [Quint modeling guidance](https://github.com/quint-co/quint/blob/6fb2924e00707cef6dbc5e30db606d555c447123/skills/quint-modeling/SKILL.md)
- [Quint LLM Kit's lightweight plugin](https://github.com/quint-co/quint-llm-kit/tree/cc75369f741af7d490936f82002c2d28e3b3d78d/quint-llm-kit-plugin)

The first two references are the preferred reusable authoring guidance. The
parent supplies only the relevant sections and examples to `formal-model-author`.
Read referenced guidelines from that same pinned revision. Both repositories use
Apache-2.0; these links preserve upstream ownership and avoid a second maintained
copy of the language manual. The reviewed revisions' skill trees passed the
repository's skill security scan without findings.

SpecKit owns selection, approved requirements, phase order, allowed output paths,
and gate decisions. Upstream advice that ordinary modeling needs only simulation
does not satisfy a selected Apalache gate. The LLM Kit's `quint-execute-spec`
orchestrator is a useful reference for model-based implementation, but its own
Research/Plan/Implement loop and model-as-authority rule are not activated inside
SpecKit. Do not install its full Docker/MCP environment as a workflow prerequisite.

## Start with the working counter

Use `examples/formal/counter-quint/Counter.qnt` and its native configuration.
The rule is: start at zero, increment by exactly one until two, then hold. The
`Bounded` property says the count stays between zero and two. After the first
successful check, temporarily change `count <= 2` to `count < 2`: the checker
must report a violation at two. Explain that state in plain English, then restore
the approved rule and recheck. Experts may proceed directly to the catalog.

Select the model in the workflow exactly as for TLA+, using `origin: new` or
`existing` and the chosen evidence level. Set these catalog fields:

```json
{
  "language": "quint",
  "checker": "apalache",
  "module": "formal/counter/Counter.qnt",
  "config": "formal/counter/Counter.cfg",
  "inputs": ["formal/counter/Counter.qnt", "formal/counter/Counter.cfg"],
  "main": "Counter",
  "init": "init",
  "next": "step",
  "mode": "bounded",
  "bounds": {"length": 5}
}
```

This is a partial model entry: also declare properties, requirements, assumptions,
implementation inputs, and budgets required by the catalog schema. Declare every
import. The native configuration uses matching `INIT init` and `NEXT step`.
Quint supports the integration's bounded and bounded temporal profiles; induction
and TLC execution of Quint models require separate qualification and are rejected.

## Pinned compiler and checking boundary

The executed profile is Quint **0.32.0**, Node.js **24.11.1**, Apalache **0.62.2**,
and Java **26.0.1**, on macOS arm64. These exact local executions establish the
reported compatibility; additional OS/runtime combinations need their own tests.
Installation is an explicit operator action. The catalog's `tools.quint` records
`version`, installation `root`, `tree_sha256`, and `node`. The full tree digest
includes the installed compiler, dependencies, and package lockfile; doctor
rejects drift. Preserve a lockfile and verify registry integrity before computing
that approved digest. Use the release's installation/qualification guidance.

The runner executes the pinned Node CLI with `compile --target=json --flatten=true`.
The pinned Apalache process then checks that JSON directly. It never calls Quint
`verify` or `compile --target=tlaplus`: Quint 0.32.0's managed backend can download
and start its own Apalache when connection fails. Node's permission mode limits
filesystem access to the installed compiler and snapshot and denies subprocess
launching; this is not a network isolation guarantee. Use a network-disabled
consumer CI check job when reproducible offline execution is required.

Compilation/typechecking success is only an intermediate result. Bounded
verification, temporal checking, and observed trace conformance retain their
separate meanings. Each checkpoint includes the compiler identity and original
Quint inputs in its freshness calculation. Converted JSON/TLA+ lives in ignored
run directories and is not a second authoring source.

For trace queries only, Apalache renders the compiled JSON to native TLA+ and
parses the complete query back into its documented IR. The runner replaces only
native assignment/UNCHANGED nodes with their documented equalities, preserving
literal data, annotations, and all constraints. Apalache documents `v' := e` as
evaluating to `v' = e`, and `UNCHANGED e` as `e' = e`. This permits conjunction
of the original Next relation and the recorded action without duplicate mandatory
assignments. Native positive and defective implementation tests qualify this
conversion; no property or transition is removed.

Sources: [Quint 0.32.0](https://github.com/quint-co/quint/releases/tag/v0.32.0),
[pinned backend management](https://github.com/quint-co/quint/blob/fd77260/quint/src/apalache.ts),
[Apalache assignment semantics](https://apalache-mc.org/docs/lang/apalache-operators.html#assignment),
and [ITF interchange format](https://apalache-mc.org/docs/adr/015adr-trace.html).

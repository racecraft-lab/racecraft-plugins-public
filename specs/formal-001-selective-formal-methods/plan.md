# FORMAL-001 implementation plan

Use Python 3.11+ standard library and the existing runner request/response and
helper registries. Keep selection, checker execution, freshness, and traces in
small modules under `speckit_pro_runner/formal/`. Reuse existing workflow binding,
stage resolution, PR packets, and agent distribution tooling.

The workflow's `## Formal Methods` JSON block is authoritative selection. The
catalog describes reusable models and does not enroll features. Compact run
records are distinct from authoring inputs. All paths resolve from the verified
workflow root, including parent-checkout invocation and resume.

Authoring is a conditional checkpoint after the normal Plan command, preserving
the seven phases and the phase executor's single-command contract. The parent
dispatches a bounded author agent with approved inputs and allowed output paths.
The formal checkpoint blocks stage entry independently of generic quality slots.

Checker adapters own exact supported command lines and conservative result
classification. External tools are optional. Local execution and pinned hosted
CI profiles require actual qualification; unsupported profiles remain unverified.

Trace validation binds producing tests, adapter and implementation inputs to the
current model. A valid state sequence also needs legal action transitions; replay
of a model counterexample alone does not establish implementation conformance.

PR management selects a manager before stack mutation. The packet path owns PR
titles and bodies. Optional gh-stack links verified existing PR URLs in declared
order and owns recovery once it has mutated the stack.

## Delivery ownership

See [tasks](tasks.md) for the six branch layers. Each layer includes its relevant
tests, documentation and regenerated payloads. Generated artifacts are rebuilt
from source. The final layer records full-suite, checker qualification, installed
parity and manual-UAT status against the exact pushed revision.

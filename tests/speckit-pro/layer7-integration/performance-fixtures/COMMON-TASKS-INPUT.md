# Common Tasks-production input

This is a prepared prompt supplement, not generated Tasks output, a qualified
benchmark, or launch authorization. Apply these identical bytes to both arms'
Tasks-production prompt without replacing the original workflow or the scenario
kickoff's approved scope. Run the actual Tasks phase through the installed native
autopilot. Generate the plan, tasks, and metadata from the approved requirements;
**never seed** the historical reference plan/tasks or an evaluator-authored
metadata sidecar into the active feature directory.

## Tasks output contract

Preserve every functional requirement, safety boundary, verification obligation,
and exclusion in the scenario kickoff and frozen approved specification. The
14 / 54 / 40 reference obligations are coverage inventories, not required new
task counts. ART-012 includes FR-006/T014. ART-007 T052 remains operator-only
and pending; its automated scenarios 1–4 and all other obligations still apply.

Alongside freshly generated `tasks.md`, the Tasks producer must write
`.process/task-execution.json` in the active feature directory. Its JSON object
contains exactly `schema_version`, `fingerprints`, and `tasks`:

- `schema_version` is `task-execution.v1`.
- `fingerprints` contains exactly `spec_sha256`, `plan_sha256`, and
  `tasks_sha256`, calculated from the freshly generated active files, never
  copied from references or guessed. Read each file as UTF-8 text with universal
  newline handling. Hash the UTF-8 encoding of spec and plan text unchanged.
  For tasks only, normalize checkbox completion with the Python expression
  below before hashing. Recalculate after any definition change.
- `tasks` is an object keyed by exactly every unique task ID in `tasks.md`.
  Each entry contains exactly `capability_group`, `depends_on`, `owns`, and
  `tdd_unit`. Capability and TDD-unit names are stable identifiers matching
  `[a-z][a-z0-9-]*`. Dependencies are unique preceding task IDs; order
  prerequisites first and preserve real dependencies rather than inventing
  parallelism. Ownership is a nonempty unique list of bounded canonical
  repository-relative paths covering every explicit file reference and all
  shared/generated writes. Do not use absolute paths, parent escapes, globs,
  repository-root ownership, symlink trees, or hard-link aliases.
- A TDD unit groups a complete test/implementation behavior, spans at most four
  adjacent tasks, and stays within one phase, routed agent, and capability.
  Distinct units may overlap ownership and must then execute sequentially.
  Do not split an inseparable TDD unit merely to meet a batching count; if it
  cannot fit safely, report the compatibility blocker. Start all generated
  tasks unchecked; completion requires actual reconciled results and effects.

The fingerprint algorithm uses only Python's standard library. It does not
require a candidate-only helper, installed candidate module, or reference output:

```python
definitions = re.sub(r"(?m)^(\s*-\s+\[)[ xX](\]\s+T[0-9]{3,})", r"\1 \2", tasks_text)
fingerprints = {key: hashlib.sha256(text.encode("utf-8")).hexdigest() for key, text in (
    ("spec_sha256", spec_text), ("plan_sha256", plan_text), ("tasks_sha256", definitions)
)}
```

Import `re` and `hashlib`; the three text variables are the active generated
files read as described above. This snippet computes digests only: it supplies
no task IDs, ownership, grouping decisions, or metadata output in advance.

## Evidence boundary

Both arms must actually generate this sidecar and preserve its bytes/digest in
the campaign evidence. Use each arm's installed dispatch policy, not a shared
replacement scheduler. When the installed arm supports required metadata, the
orchestrator must request `task_execution_required=true` and validate generated
metadata after Tasks and after every subsequent definition change, before
partitioning. Missing, stale, or invalid metadata blocks that optimized run;
silently falling back to legacy dispatch is not a batching benchmark.

The baseline must demonstrate that it can process this prompt and run its own
native workflow without a missing candidate-only helper. A source inspection or
unit fixture does not establish that producer compatibility. Until real native
evidence exists for both arms, metadata-input qualification remains pending.

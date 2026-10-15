# Plan terminal helper review follow-up

PR #1336 repairs the terminal helper at the full runner dispatcher seam. Its
review reproductions cover the planning gate, confined cleanup, interrupted
authoring, brokered preview evidence, research freshness, and independent
planning-derived page expectations. The shared runner ships to both hosts.

## Hidden-content evidence repair

F1336-8430c586: hidden artifact content counted as feature evidence. The
terminal helper now binds every fill to the independently rendered planning
bytes, masking only the text of paragraphs emitted by the narrative owner.
Only escaped narrative text may change. This keeps the existing plain-text
authoring contract and prevents a hidden copy, an attribute, a class, or an
unbalanced wrapper from certifying a different visible feature. Static template
provenance and active-content checks remain mandatory before publication.

Tests exercise the public terminal dispatcher with both host inputs and rerun
the same hidden-content cases against each shipped runner. Coverage includes
hidden, display:none, visibility:hidden, opacity:0, template, closed details,
aria-hidden, script, comments, CSS variants, nested hiding, attribute-only
text, hidden structured anchors, and wrappers across fill boundaries. Scripts
and comments already stopped on the reviewed head; their new red assertions
require rejection at the planning-markup boundary before the later provenance
check. Successful plain-text narrative edits remain covered.

R1336-7dcb2dec closes the mixed-region exception: `feature-header` also holds
the feature id, name, and eyebrow; `module-graph` holds directory/file-count
rows beside its narrative caption. `Page.prose` marks only its own paragraph,
so every neighboring byte remains bound to the planning render. Dispatcher
tests rewrite each field, repeat the shared header attacks on every page,
and exercise both shipped runners with both host inputs. Plain escaped edits
to the lede and module caption still publish. Existing concealment, active
content, nested wrapper, and cross-region wrapper cases remain mandatory.

## Canary CLI termination

The copied receipt-CLI harness previously inherited the parent input stream
and had no child deadline. Eighteen call sites now share one invocation owner
that supplies EOF and a five-second timeout. Deterministic regressions cover an
open parent request stream and a CLI that does not return; both failed before
the lifecycle fix. Existing API/CLI corruption matrices retain every case.
The original long VM hang was not reproduced by the isolated matrices, so
this repair establishes bounded child waits without claiming its precise
external trigger was identified.

## Known limits

- R1336-0f1bd68e: the original production diff exceeded the ticket's 400-line
  warning target. R1336-a155648d also records the warn tier on the other
  two axes: six production source files and eighteen authored files at the
  reviewed head, with about 528 added production lines. Subsequent focused
  repairs retain that accepted size warning. The confidence-gate repair adds
  `read_only.py`, so the production set is seven files with about 560 added
  lines against the merged main. This is a reviewability warning,
  not a reachable behavior
  defect or a blocking size tier. This repair keeps each defect in a separate
  commit and adds no unrelated refactor or quality cleanup.
- R1336-d4941850: the existing CLI trust policy rejects user-owned executable
  installations. A consumer must install `gh` through a system-managed,
  trusted installation whose executable and parent directories satisfy
  `cli_probe`. The helper stops at `tool_unavailable` if that installation is
  unavailable. The observed compatibility limit does not authorize bypassing
  the existing executable trust boundary. Issue #1355 later lifted this limit
  for `git` and `gh` only: `cli_probe.OPERATOR_CLIS` accepts an install the
  operator owns with no group or other write bit, when no worktree name
  reaches it or its lookup chain.
- R1336-624c09eb: quoted, commented, or repeated `confidence_threshold`
  values are rejected by the strict configuration grammar. No tracked config
  or documentation uses these forms; they yield an input error or stop,
  never a confidence-gate pass. This accepted compatibility limit remains.
- Real GitHub draft creation and interactive preview/question UI are not
  exercised by these deterministic tests. Git uses a disposable bare remote;
  GitHub responses are scripted. UI requests are checked against their
  documented schemas and contracts.
- Linux VM tests do not establish macOS behavior. Before merging, the
  orchestrator must run native macOS coverage, including
  `test_gate_hardening.py::test_pr_test_code_cannot_touch_the_host_under_the_real_sandbox`
  and
  `test_gate_hardening.py::test_pr_test_code_cannot_create_or_modify_any_file_in_the_clone`.

Additional read-only review questions were checked against the owners:

- A retained denial with an old artifact digest remains pending after
  regeneration. The preview contract requires matching digests for a verified
  observation; a denied observation records refused access and cannot verify
  the new page. No authorization is inferred from regenerated bytes.
- `confidence-gate` dispatch returns a runner data object. A hypothetical
  `data: null` injected by a test double is outside that helper's dispatcher
  contract, so it does not reach this consumer on real dispatcher responses.
- If execution stops before its first handoff record and inputs subsequently
  change, existing pages can fail the independent content check. This is a
  fail-closed recovery limit: authored files remain intact, and the caller can
  rerender them through `fill-artifact-page` before retrying publication.
- Planning records with no usable structured feature passage fail the
  content check. This was not reproduced on the supplied real planning
  templates and is a non-blocking sparse-input limit, not evidence that the
  reviewed fixtures lose or falsely certify content.

The original reviews are the
[Codex cross-host review](https://github.com/racecraft-lab/racecraft-plugins-public/pull/1336#issuecomment-6137252608)
and the
[Daybreak security review](https://github.com/racecraft-lab/racecraft-plugins-public/pull/1336#issuecomment-6137269198).

# Contract: Scaffold → Autopilot Chain

**Documentation only.** This specification ships **no** scaffold-side code. The
scaffold-side implementation belongs to ART-011, which the roadmap places out of
ART-006's scope explicitly
(`docs/ai/specs/html-artifacts-technical-roadmap.md:462`, `:466-468`) and which is
blocked on ART-006 for exactly the reason this document exists: the chain needs a
stable contract before it can be built against (`:66`).

FR-016 enumerates five things ART-011 cannot derive on its own. Each is fixed
here.

## 1. Handoff artifact

**The workflow file path is the sole handoff token.**

```text
docs/ai/specs/.process/<SPEC-ID>-workflow.md
```

Nothing else crosses the boundary. Not a state file, not a branch name, not a
feature directory, not an environment variable. Everything the autopilot needs it
reads from, or derives from, that one path:

- the state file, as `<workflow-dir>/autopilot-state.json`
- the specification identity, branch, and feature directory, from
  `### Basic Information`
- the phase completion picture, from `## Workflow Overview`
- the stage, from the `Stage` row — or its absence

This is what makes the boundary survivable. A scaffold run and an autopilot run
in different sessions, different working copies, or on opposite sides of an
archive sweep agree because they agree about one path.

## 2. Entry precondition

**At scaffold time the `Stage` entry is absent, and absence means "no run yet".**

The scaffold writes no `Stage` row, and
`speckit-pro/skills/speckit-coach/templates/workflow-template.md` carries none —
its `### Basic Information` table ends at `Priority` (`:109-118`). A workflow file
handed to the autopilot for the first time therefore resolves through ordinary
auto-detection, which reads the phase status table and answers `plan` because the
planning phases are not yet complete.

Three consequences ART-011 may rely on:

- Absence is **never** an error and is **never** reported as one.
- Absence is **not** a fourth stage value; the vocabulary stays closed at three.
- A scaffold does not need to know the stage vocabulary at all. It hands over a
  path; the autopilot decides.

This is the common case rather than the exception: of the workflow files in this
repository today, all but one carry no `Stage` entry (spec.md:139-143).

## 3. Invocation form and stage vocabulary

Per-platform invocation, full argv surface in
[stage-invocation.md](./stage-invocation.md):

| Platform | Chain-into-plan-stage invocation |
|---|---|
| Claude Code | `/speckit-pro:speckit-autopilot <workflow-file> --stage plan` |
| Codex CLI | `<workflow-file> --stage plan` |

**Closed stage vocabulary**: `plan`, `implement`, `full`. Literal lowercase
tokens, identical for the argument value and the recorded entry. No aliases, no
alternate casing, no long-form spellings. ART-011 chains into `plan`; a caller
that omits `--stage` entirely gets the same answer by auto-detection on a
freshly scaffolded file, so passing it is explicitness rather than necessity.

## 4. Completion signal — observable in the workflow file

ART-011 must be able to tell that the planning stage finished **by reading the
workflow file**, without a live session and without the state file. Three
conditions, all in the one artifact:

1. Every planning-phase row in `## Workflow Overview` — Specify, Clarify, Plan,
   Checklist, Tasks, Analyze — carries a terminal status
   (`Complete`, `✅ Complete`, `Skipped`, `✅ Skipped`, `⏭ Skipped`, `⏭️ Skipped`).
2. A `G6.5` confidence-gate verdict is recorded in the file.
3. The `Stage` row reads `plan` — the last *resolved* stage of the most recent
   run.

Point 3 is a corroborating signal, not the completion test. The `Stage` entry
records what was resolved, not what completed (FR-008a), so within-stage progress
comes from points 1 and 2. A file showing `Stage: plan` with Tasks still pending
is a run in flight, not a finished one — and a file that shows both a `G6.5` PASS
and a non-terminal planning row is a contradiction that the tree-wide CI gate
fails (`tests/speckit-pro/layer1-structural/validate-workflow-status-evidence.py:297-298`).

The boundary is also a **commit**, not working-tree state: the planning stage
closes with its own terminal commit, taken after the gate resolves and carrying a
message that names the stage boundary rather than a phase (FR-009). ART-011 can
therefore locate the checkpoint in version history as well as in the file.

## 5. Out of scope here

ART-006 ships no scaffold-side code. Specifically not in this slice:

- Any change to `speckit-pro/skills/speckit-scaffold-spec/`
- Any change to `speckit-pro/skills/speckit-coach/templates/workflow-template.md`
- Any automatic hand-off, chaining, or invocation of the autopilot from a
  scaffold run
- Draft-pull-request creation and the auto-detection corroboration limb that
  would read it — both deferred to ART-007, which is the specification that
  creates the draft PRs there would be anything to corroborate against
  (`html-artifacts-technical-roadmap.md:451-460`)

What ART-006 does ship is the contract above plus the resolver that honours it.

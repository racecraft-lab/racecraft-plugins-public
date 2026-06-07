# Contract: `reviewability-gate.sh` output (reworked, US2)

The end-stage detective gate. Its `setup`/`tasks`/`diff` mode topology is UNCHANGED (FR-007).
The reworked internals: production-only LOC metric (FR-008), 1.5× greenfield allowance
(FR-009), surface-count as warning not blocker (FR-010), and a single shared typed-exception
matcher replacing the legacy keyword at all three modes (FR-011/012/013).

## Invocation (unchanged)

```bash
reviewability-gate.sh setup <roadmap-or-workflow-file>
reviewability-gate.sh tasks <feature-dir>
reviewability-gate.sh diff  [git-range]      # default origin/main...HEAD
```

## Exit codes (unchanged)

| Code | Meaning |
|------|---------|
| 0 | within budget (`status` ∈ `pass`, `warn`, `exception`) |
| 1 | block threshold exceeded and not excepted (`status = block`) |
| 2 | usage or unreadable input |

## Status values (unchanged set; surface no longer contributes to `block`)

`pass` → `warn` → `block`, with `block` flippable to `exception` by a valid typed pragma.
After FR-010, a primary-surface count > 1 produces only a `warn` (never a `block`).

## JSON shape (target — changes from current marked)

```json
{
  "mode": "diff",
  "status": "warn",
  "pass": true,
  "reviewable_loc": 380,
  "production_files": 5,
  "total_files": 12,
  "primary_surface_count": 2,
  "primary_surfaces": ["UI", "harness/adapter"],
  "greenfield": false,
  "thresholds": {
    "warn":  { "reviewable_loc": 400, "production_files": 6, "total_files": 15, "primary_surfaces": 1 },
    "block": { "reviewable_loc": 800, "production_files": 8, "total_files": 25, "primary_surfaces": 1 }
  },
  "exception_honored": false,
  "exception_class": null,
  "warnings": ["primary surfaces 2 exceeds warn threshold 1"],
  "blockers": []
}
```

### Field changes from the current gate output

| Field | Current | Reworked |
|-------|---------|----------|
| `reviewable_loc` | sum of ALL non-excluded additions (`reviewable_loc_from_numstat`) | sum over **production** files only — `is_production_file` & not `is_excluded_generated` (FR-008). Applies in `diff` mode (and the estimator) consistently. |
| `primary_surface_count > 1` | adds BOTH a warning AND a blocker | adds a **warning only**; the blocker line is removed (FR-010). `primary_surface_count` + `primary_surfaces` still reported (downstream consumers — PRSG-007). |
| `greenfield` | (absent) | NEW boolean. True iff every non-excluded changed path is git add-status `A` (`--no-renames` pinned). When true, **only the `reviewable_loc` thresholds** scale ×1.5 (warn 400→600, block 800→1200) — FR-009. |
| `thresholds` | static 400/6/15/1 & 800/8/25/1 | greenfield scales **`thresholds.warn.reviewable_loc` and `thresholds.block.reviewable_loc` ONLY**. The `production_files`, `total_files`, and `primary_surfaces` thresholds are UNCHANGED by greenfield (FR-009 grants a LOC allowance only). Concretely: of the eight literals at current `reviewability-gate.sh:130-131`, only the two `reviewable_loc` values (400, 800) become greenfield-variable; the other six stay fixed. |
| `transition_exception` (boolean) | legacy key reflecting the 3-phrase keyword | **replaced** by `exception_honored` (boolean) + `exception_class` (matched class \| null). The legacy keyword is honored by no mode (FR-013). Whether to rename or add-alongside is a tasks-phase call; L4 assertions on the old key update in lockstep. |

## Typed exception (FR-011/012/013) — single shared matcher

One function `match_exception_pragma`, POSIX ERE via `grep -E`, reused by all three modes:

```text
^[[:space:]]*Reviewability-Exception:[[:space:]]+(refactor|infra|upgrade)[[:space:]]*$
```

- Line-anchored, **case-sensitive**, exact closed enum `{refactor, infra, upgrade}`, no trailing
  content. All three classes flip a `block` equally in v1 (class recorded for audit, not for a
  different budget). `exception_class` = the matched class; `exception_honored` = true only when a
  `block` is flipped by a valid pragma.
- **Fail-closed (FR-012):** a class outside the set, a mis-cased class, or a missing pragma leaves
  `status = block`. No free-form prose is honored.
- **`diff` mode reads added lines of committed Markdown only (FR-012):**
  `git diff "$range" -- '*.md' | grep '^+' | grep -v '^+++' | sed 's/^+//'` then apply the matcher.
  This isolates added (`+`) content so the `+++ b/<file>` header cannot self-satisfy the matcher;
  a pragma on a context/removed line does NOT flip. Over `merge-base..HEAD`, a pragma the branch
  introduced is an added line (honored); a base-branch pragma is a context line (not honored).
  NEVER read from the PR description or commit messages (mutable, not the durable governance
  artifact).
- **Legacy phrases** (`split exception`, `transition exception`, `ratified exception`) are honored
  by NO mode — new-specs-only break (FR-013), documented for PRSG-011.

## Known limitation (recorded; deferred to PRSG-010)

The matcher is line-scoped, not Markdown-aware: a syntactically valid pragma inside a fenced code
block or inline-code span in a committed `.md` WOULD flip a `block`. Scoping the scan to a
designated governance section/artifact is PRSG-010 ("harden the hatch"); the L4 fixtures record
this residual rather than asserting it away.

## Template consistency (FR-014 / SC-007)

The roadmap template's `## Reviewability Contract` is updated to advertise the production-LOC
thresholds, the surface-count-as-warning wording, and the `Reviewability-Exception: <class>`
pragma. `setup` mode parses that template, so an L1 assertion verifies template vocabulary
matches what the gate honors (no parse failure against the new contract).

**Keep the template's pragma as the literal placeholder `Reviewability-Exception: <class>`** — do
NOT substitute a concrete class (e.g. `refactor`) into the template. `<class>` is deliberately not
a member of the closed enum, so the documentation example fails `match_exception_pragma` and
setup-mode parsing of the template never honors the example as a live exception. This is the
correct, fail-closed behavior for a template that the gate reads (FR-012 + FR-014).

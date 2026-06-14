# Research: Optional gh-stack stack manager integration

## Decision 1: Treat `gh stack` as optional and fail closed

**Decision**: Runtime support detection must select `gh-stack` only when local command availability, version, repository support, read-only topology proof, and PRS/marker topology compatibility all pass.

**Rationale**: Local evidence shows `gh stack` is installed as `github/gh-stack v0.0.5`, and official project documentation identifies Stacked PRs as private preview. A repository can have the extension installed while the GitHub feature is unavailable, so installation alone is insufficient.

**Alternatives considered**:

- Select `gh-stack` when the extension is installed. Rejected because private-preview repository enablement and topology compatibility are separate from installation.
- Try a mutating dry run. Rejected because `gh stack link`, `submit`, `sync`, and `rebase` can push branches, create or edit PRs, or rewrite local history.

## Decision 2: Use `gh stack view --json` as the read-only proof

**Decision**: `detect-stack-manager.sh` must use `gh stack view --json` as the only `gh stack` read-only topology proof. Missing, nonzero, unparseable, ambiguous, or topology-incompatible output selects explicit `gh` fallback before mutation.

**Rationale**: Local v0.0.5 help exposes `view --json` as machine-readable stack data. This can be compared against PRS/marker order before any topology-changing command runs.

**Alternatives considered**:

- Parse human `gh stack view` output. Rejected because human output is not a stable contract.
- Infer support from `.git/gh-stack`. Rejected because local metadata is not enough to prove repository enablement or PR topology.

## Decision 3: Keep PRSG-012 packets authoritative

**Decision**: Emission creates or reconciles PRs through explicit `gh pr create/edit --base --head --title --body-file` using validated packets first. Only after every planned packet is valid may `gh stack link` run.

**Rationale**: `gh stack submit` can prompt or auto-generate titles and bodies, and `gh stack link` with branch argv can create PRs. PRSG-012 requires packet-owned title/body generation and validation before PR creation or sync. Therefore stack manager use must be downstream of validated packet state.

**Alternatives considered**:

- Use `gh stack submit --auto` for initial PR creation. Rejected because it bypasses packet-owned PR bodies and generates titles.
- Use `gh stack link` with branch names before PR creation. Rejected because branch argv can push branches, create PRs, and correct base branches itself.

## Decision 4: Prefer PR numbers for stack linking

**Decision**: Supported emission should call `gh stack link --base <base> <pr-number>...` after explicit PR reconciliation when PR numbers are known. Branch argv is allowed only if the plan explicitly proves it cannot create duplicate PRs and every packet/topology precondition is satisfied.

**Rationale**: Local help states `gh stack link` accepts branch names or PR numbers. PR numbers let existing packet-created PRs remain authoritative while still linking them into a GitHub stack.

**Alternatives considered**:

- Always pass branch names. Rejected because branch arguments can push and create or update PRs as part of the stack command.
- Never use `link`. Rejected because `link` is the documented command for users who manage branches with other tools and want GitHub stack linking without local tracking.

## Decision 5: Restack through `gh stack` only with exact topology proof

**Decision**: Supported restack uses `gh stack rebase --upstack <first-remaining-branch>` plus a proven sync/push step only when local `view --json` topology matches PRS/marker order and v0.0.5 help confirms exact scoped upstack support. Otherwise `restack.sh --apply` keeps the existing `gh pr edit --base` fallback before mutation.

**Rationale**: Local v0.0.5 help supports `rebase [branch] --upstack` and `sync --remote`. Both mutate branch/PR state, and `sync` operates on the current stack. The existing fallback is deterministic and scoped to PR base retargeting.

**Alternatives considered**:

- Always use `gh stack sync` after squash merge. Rejected because it operates on a current stack and can fetch, rebase, push, and sync PR state outside the desired scope when local tracking is absent or ambiguous.
- Use only `gh pr edit --base`. Rejected because PRSG-014 explicitly adds optional stack-manager support when safely available.

## Decision 6: Shared decision contract, not per-caller ad hoc fields

**Decision**: Add a shared `stack-manager-decision.schema.json` and have emission/restack evidence reference or embed the same decision object.

**Rationale**: Emission and restack share availability, compatibility, fallback, command plan, mutation boundary, and recovery semantics. A single contract reduces drift and keeps Claude Code/Codex guidance aligned.

**Alternatives considered**:

- Add separate emission and restack decision shapes. Rejected because it duplicates support semantics.
- Store informal text in command logs. Rejected because reviewers need deterministic schema-backed evidence.

## Decision 7: Bound command evidence

**Decision**: Each command execution record captures argv, exit status, started/finished timestamps, mutation classification, and stdout/stderr tails bounded to 120 lines and 16 KiB per stream.

**Rationale**: Reviewers need enough evidence to diagnose failures without unbounded logs. The limits are large enough for `gh` diagnostics and small enough for stable artifacts.

**Alternatives considered**:

- Capture full command output. Rejected because it can bloat evidence and leak unrelated terminal content.
- Capture only exit status. Rejected because recoverable blocks need actionable error context.

## Evidence Sources

- Local CLI: `gh extension list` reported `gh stack github/gh-stack v0.0.5`.
- Local CLI: `gh stack --version` reported `gh stack version 0.0.5`.
- Local CLI help: `gh stack view --help`, `link --help`, `submit --help`, `sync --help`, and `rebase --help`.
- Project docs: `https://github.com/github/gh-stack` README, including private-preview status, local tracking notes, command list, `link`, `submit`, `sync`, `rebase`, and exit-code documentation.

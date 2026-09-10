# FORMAL-001: Selective formal methods

Status: implementation in progress. Baseline: `371e4217877e6f2bd599fdc6ec997620611abfed` (2.31.0).

## Purpose

Help developers answer a specific design question with a small formal model when
ordinary tests, contracts, or database constraints leave material risk. Selection
is per behavior or subsystem, reusable across stories, and always explicit.

## User stories

- US1: A beginner receives a justified no-model recommendation or completes a
  guided passing check and understands an intentionally failing property.
- US2: A model author selects Apalache or TLC for the required evidence and
  receives version-correct setup guidance and bounded, honest results.
- US3: A SpecKit operator can scaffold, author, check, commit, and resume a
  selected model without bypassing an incomplete or stale checkpoint.
- US4: An implementer can validate observed action/state traces against the
  selected model and expose an implementation defect.
- US5: A maintainer can reproduce checks from a clean checkout, upgrade tooling,
  and deliver reviewable PRs with the available PR manager.

## Requirements

- FR1: Coach from the design question, consequences, alternatives, and modeling
  cost. Adapt to beginner, intermediate, and expert needs without forcing an
  interview in autopilot. Keywords and installed tools never activate checks.
- FR2: The workflow owns `none`, `deferred`, or `enabled` selection, rationale,
  model IDs, behavior, new/existing origin, evidence level, and checkpoints. A
  missing legacy selection is disabled. Malformed selection fails closed.
- FR3: A versioned `.specify/formal-methods.json` catalogs durable models,
  properties, assumptions, native configurations, inputs, budgets, and adapters.
  New models live in `formal/<model>/`; archive cleanup must not remove them.
- FR4: `formal-doctor` is read-only. `formal-check` previews or executes selected
  checks through the runner envelope. Execution is independent of app-language
  discovery and never installs a runtime implicitly.
- FR5: Qualify Apalache 0.62.2 and TLC 1.7.4 by actual execution before claiming
  compatibility. Distinguish violations, invalid models, unsupported features,
  missing tools, timeouts, mismatches, and inconclusive checks. Type checking is
  not model checking; all configured induction obligations must complete.
- FR6: After normal Plan execution, a bounded `formal-model-author` creates the
  selected model contract. G3 stays incomplete until selected checks pass. Never
  silently weaken properties, assumptions, bounds, or coverage to obtain a pass.
- FR7: Fingerprint spec, plan, selection, model/config/import inputs, and checker
  identity; store results outside those inputs. Reconcile after planning/review
  edits and renew checks before Tasks, implementation entry, and closeout.
- FR8: All resume forms enforce the same formal prerequisites against
  `WORKFLOW_ROOT`. Confidence flags and generic skips cannot bypass them. An
  explicit operator waiver is separate evidence, never a passing check.
- FR9: Planning commits include declared model/configuration changes and compact
  evidence; raw output stays ignored. Final and Post verification recheck models.
- FR10: Trace validation follows real producing tests, uses an explicit tested
  action/state projection, rejects illegal transitions even when invariants
  hold, and cannot pass with missing, stale, malformed, or mismatched traces.
- FR11: Prefer gh-stack only with usable CLI, available skill, repository support,
  compatible topology, and no operator fallback preference. Preserve validated
  PR metadata, identities, ownership, recovery state, and partial-mutation rules.
- FR12: Preserve disabled-workflow behavior and Claude/Codex parity. Hosted CI is
  default; optional organization runners retain admission and resource checks.
- FR13: Support Python, TypeScript, and Swift implementations through a shared
  trace contract and explicit language-specific emitters/test integration. Verify
  serialization, numeric and concurrency semantics from official documentation;
  execute valid and deliberately defective implementations in each language.
  Language detection never activates formal methods or replaces model selection.
- FR14: Evaluate and qualify Quint as an optional modeling front end for Apalache,
  with version-pinned tooling and ITF trace interoperability. Keep model-based
  test generation and validation of observed implementation traces distinct.
  No Quint command may silently acquire a checker during an ordinary workflow.

## Non-goals

Automatic enrollment, proof of all implementation behavior from model success,
unbounded guarantees from bounded checks, new upstream SpecKit command forks,
automatic runtime installation, automatic verification/translation of arbitrary
application source, or TLAPS execution. Quint's optional front end is now in the
research and qualification scope following the operator's update.

## Acceptance

The single [acceptance record](acceptance.md) owns evidence and limitations for
all six delivery PRs. Manual onboarding UAT is recorded separately from tests.

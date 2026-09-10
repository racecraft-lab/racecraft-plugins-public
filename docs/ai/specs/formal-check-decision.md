# Formal check decision record

Date: 2026-09-10. Status: approved design; implementation and qualification in
progress under [FORMAL-001](../../../specs/formal-001-selective-formal-methods/spec.md).
The [acceptance record](../../../specs/formal-001-selective-formal-methods/acceptance.md)
distinguishes delivered behavior, automated evidence, and manual onboarding UAT.
This supersedes the 2026-09-06 spike, including its automatic discovery,
mandatory trace, archive-prone paths, final-only timing, and mixed-version flags.

## Selection and coaching

Select formal verification explicitly for behaviors or subsystems when the
design question, failure consequences, and modeling cost warrant it beyond
ordinary tests, contracts, and database constraints. Recommend no model, a
focused model, or deeper verification. Tools, catalog entries, and concurrency
keywords do not enroll features or stories. Reuse maintained models.

Beginners start with plain-English rules and a small passing example, then an
intentional violation and an explained counterexample. Intermediate users adapt
models and diagnose failures. Experts can configure properties, assumptions,
types, bounds, fairness, and all induction obligations directly.

## Toolchain and evidence

Qualification targets are Apalache 0.62.2 and TLC 1.7.4. Choose from model needs:
Apalache's documented bounded, inductive, and temporal capabilities within
compatibility limits, or TLC's suitable finite-state and temporal checking.
Actual execution is required before advertising a profile. Never combine TLC
release flags with nightly flags.

`formal-doctor` inspects readiness without mutation; `formal-check` previews or
executes selected checks through the existing runner envelope, independently of
application-language discovery. Distinguish violations, invalid/type-invalid
models, unsupported features, absent tools, timeouts, inconclusive results, and
version/configuration mismatches. Type checking alone cannot satisfy a gate.

Prefer Apalache's official distribution with checksum-pinned downloads; offer
digest-pinned containers after qualifying them. Current Apalache installation
guidance recommends Java 25, retains Java 21 bytecode compatibility, and
recommends at least 4 GB of memory. Installation needs operator authorization;
ordinary workflows acquire no Java or Docker requirement.

## Lifecycle

The workflow owns selection (`none`, `deferred`, `enabled`), rationale, selected
IDs and behaviors, new/existing origin, evidence level, and checkpoint results.
The versioned `.specify/formal-methods.json` catalog does not activate checking.
Missing legacy selection is disabled; malformed explicit selection fails closed.

Resolve from `WORKFLOW_ROOT`. A new model may await authoring; a missing selected
existing model blocks setup. After normal Plan execution, the parent dispatches
bounded `formal-model-author`, shipped for Claude and Codex. G3 requires selected
checks. Preserve upstream commands and the phase executor's single-command rule.

Fingerprint spec, plan, selection, model/configuration/import inputs, and checker
identity. Keep results outside authoring inputs. Checklist, Analyze, and review
edits require reconciliation and renewed checks. Every resume form enforces this;
confidence flags and generic skips cannot bypass it. An explicit operator waiver
is separate evidence and never a passing check.

New models live in `formal/<model>/`, beyond feature archival. Planning commits
explicitly stage declared model/configuration changes and compact evidence. Raw
output stays ignored. Final verification and Post integration recheck models;
a clean checkout of pushed planning work must reproduce the checks.

Model evidence can block before implementation. Optional `model_and_trace`
evidence follows real producing tests with an explicit, tested action/state
projection. Reject illegal transitions even when individual states satisfy
invariants. Missing, stale, malformed, or mismatched traces cannot pass.
Counterexample replay alone does not establish implementation conformance.

## Delivery and PR management

One spec and acceptance record own six PR layers: coaching/selection; Apalache and
the complete planning checkpoint; TLC; full lifecycle and optional manager;
implementation traces; reproducible CI, recovery, and onboarding qualification.

Prefer gh-stack only when both its CLI and skill are available and compatible
with the repository and topology, unless the operator chooses current management.
Record capability evidence and ownership before mutation. PR packets retain
validated titles, bodies, identities, and release checks; link verified existing
PR URLs through gh-stack in declared order. Recover partial mutations through the
selected manager before switching. Implement and qualify the formerly disabled
selection helper before invoking it.

Hosted CI remains default. Organization runners require explicit repository
admission and adequate VM resources; neither is inferred here. Quint and TLAPS
may receive coaching references but no execution integrations.

## Official grounding

- [Apalache capabilities](https://apalache-mc.org/docs/apalache/features.html),
  [configuration](https://apalache-mc.org/docs/apalache/config.html), and
  [installation](https://apalache-mc.org/docs/apalache/installation/index.html)
- [Apalache JVM requirements](https://apalache-mc.org/docs/apalache/installation/jvm.html)
- [TLC 1.7.4 release](https://github.com/tlaplus/tlaplus/releases/tag/v1.7.4)
- [Trace-validation research](https://arxiv.org/abs/2404.16075)
- [gh-stack existing-PR linking](https://github.com/github/gh-stack#gh-stack-link)

Project-owned choices above are workflow contracts, not claims made by those
sources. Qualification gaps remain explicit in the acceptance record.

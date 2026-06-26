# Cross-Platform Runtime Inventory

Status: XPLAT-001 implementation report

Date: 2026-06-25

Feature branch: `codex/xplat-001-runtime-inventory-constraints`

Source spec: `specs/xplat-001-runtime-inventory-constraints/spec.md`

## Summary

XPLAT-001 inventories Bash, `.sh`, `jq`, shell quoting, Unix path,
`chmod`, and line-ending assumptions across the tracked repository input set.
It does not port helpers to a new runtime, change Claude or Codex invocation
paths, select a runtime, or select supply-chain controls. A post-PR review
remediation narrowed the existing spec-index generator's roadmap-MOC ownership
logic and synchronized its generated Claude/Codex payload copies; that scoped
helper correction is not a cross-platform runtime port.

The active installed-runtime surface is real: source skills, hooks, agents, and
helper scripts contain 3,739 represented source-reference scan hits, and
generated payload mirrors contain 6,966 represented generated active scan hits.
Those active rows split into XPLAT-005 read-only helper work, XPLAT-006
mutation/install/PR-emission helper work, and XPLAT-007 generated-payload
cutover guidance.

Review order:

1. Scan boundary and command set.
2. Inventory row schema and aggregate rows.
3. Runtime rubric for XPLAT-002.
4. Supply-chain rubric for XPLAT-003.
5. Verification and PR packet notes.

## Scope and Non-Goals

In scope:

- Whole-repo tracked-text scan input, including hidden tracked paths,
  `dist/**`, public docs, tests, fixtures, specs, and archive reports.
- Static caller-to-callee trace review for active installed-runtime rows.
- Markdown-only inventory and rubric output.
- Roadmap handoff to XPLAT-002, XPLAT-003, XPLAT-005, XPLAT-006, and XPLAT-007.

Out of scope:

- Runtime candidate scoring, ranking, or selection.
- Supply-chain model or control-set selection.
- Helper ports to a replacement runtime, runner implementation, broad generated
  payload rebuilds, and public native Windows support claims.
- Native Windows, macOS, or Linux runtime probes.

## Reviewability Decision

The accepted `speckit-pro-reviewability` warning remains valid. Planning
recorded one report-focused docs/process spike with no runtime behavior change.
The task reviewability gate reported a size/scope block for the generated task
plan, but `atomicity-route.sh` classified the work as `one-navigable-PR`.

This report keeps the split decision: XPLAT-001 is inventory and rubric only.
Implementation, runner choice, security-control choice, helper ports, generated
payload cutover, and release UAT remain in later XPLAT specs.

## Scan Boundary

Input universe:

| Metric | Count | Command |
|---|---:|---|
| Tracked files, excluding this generated report | 1,262 | `git ls-files ':!docs/ai/research/cross-platform-runtime-inventory.md' \| wc -l` |
| Tracked text/non-empty files searched by `git grep -I`, excluding this generated report | 1,248 | `git grep -I -l -e '' -- . ':(exclude)docs/ai/research/cross-platform-runtime-inventory.md' \| wc -l` |

The scan commands below intentionally exclude this report path,
`docs/ai/research/cross-platform-runtime-inventory.md`, after the report exists.
The report is the generated inventory output, not an input runtime assumption;
excluding it prevents self-referential matches from changing the inventory every
time the report text is edited.

Explicit exclusions:

| Exclusion | Reason | Expiry or removal condition |
|---|---|---|
| `.git/` internals | Not tracked source input and not part of installed plugin payloads. | Never part of this inventory unless a later spec inventories repository metadata. |
| Untracked files | Not durable review input. | Add to Git before they can affect runtime inventory. |
| Vendor caches and dependency caches | Not source of truth for installed plugin behavior. | Inventory only if a later spec intentionally vendors runtime artifacts. |
| Binary and non-text inputs skipped by `git grep -I` | Text search cannot produce source evidence or invocation rationale for binary payloads. | Add a text manifest or checksum policy in XPLAT-003 if binary artifacts become runtime inputs. |
| `docs/ai/research/cross-platform-runtime-inventory.md` | Generated output would recursively match the terms it documents. | Remove only if a future automated inventory format separates source input from report text. |

## Scan Commands

All scan commands run from the repository root. Each command searches tracked
text via Git and excludes this generated report path.

```bash
git grep -n -I -E '(bash|/bin/(ba)?sh|#!/usr/bin/env (ba)?sh|set -euo pipefail)' -- . ':(exclude)docs/ai/research/cross-platform-runtime-inventory.md'
```

```bash
git grep -n -I -E '\.sh([^A-Za-z0-9_/-]|$)' -- . ':(exclude)docs/ai/research/cross-platform-runtime-inventory.md'
```

```bash
git grep -n -I -E '(^|[^A-Za-z0-9_-])jq([^A-Za-z0-9_-]|$)' -- . ':(exclude)docs/ai/research/cross-platform-runtime-inventory.md'
```

```bash
git grep -n -I -E '(set -euo pipefail|shell quoting|shell-quoting|quote|quoted|xargs|printf %q|mktemp|trap |\$\(|\$\{|&&|\|\||\| tee|2>|>/dev/null|<<)' -- . ':(exclude)docs/ai/research/cross-platform-runtime-inventory.md'
```

```bash
git grep -n -I -E '(/usr/bin/env|/bin/bash|/bin/sh|/tmp|/private/tmp|/dev/null|/Users/|~/|\.git/)' -- . ':(exclude)docs/ai/research/cross-platform-runtime-inventory.md'
```

```bash
git grep -n -I -E '(^|[^A-Za-z0-9_-])chmod([^A-Za-z0-9_-]|$)' -- . ':(exclude)docs/ai/research/cross-platform-runtime-inventory.md'
```

```bash
git grep -n -I -E '(CRLF|LF|line ending|line-ending|line endings|line-endings|dos2unix|\\r\\n|carriage return)' -- . ':(exclude)docs/ai/research/cross-platform-runtime-inventory.md'
```

## Scan Result Summary

Counts are scan-hit counts by pattern family, not unique logical findings. The
same source line may be represented under more than one pattern family when it
contains multiple scoped assumptions.

| Pattern family | Total scan hits | Files |
|---|---:|---:|
| Bash / shell substrate | 2,379 | 461 |
| `.sh` helper references | 4,154 | 583 |
| `jq` references | 1,885 | 217 |
| Shell quoting / shell operators | 10,812 | 392 |
| Unix path assumptions | 1,814 | 339 |
| `chmod` references | 58 | 36 |
| Line-ending references | 60 | 41 |
| **Total represented scan hits** | **21,162** | **N/A** |

## Row Schema

Every inventory row uses these fields:

| Field | Required | Notes |
|---|---|---|
| `id` | Yes | Stable row identifier. |
| `evidence` | Yes | Path set, scan family, match count, and representative evidence. |
| `classification` | Yes | One of the allowed classification values below. |
| `active_runtime_status` | Yes | `proven-active-runtime`, `unproven-active-runtime`, or `not-active-runtime`. |
| `runtime_relevance` | Yes | Why the row matters or does not matter to installed runtime behavior. |
| `owner_bucket` | Yes | Later XPLAT owner or exclusion bucket. |
| `follow_up_spec` | Yes | Later spec or exclusion owner. |
| `invocation_trace` | Conditional | Required for proven active runtime; evidence gap required for unproven active runtime. |
| `rationale` | Yes | Classification and ownership explanation. |
| `exclusion_or_exception_detail` | Conditional | Required for explicit exclusions and follow-up exceptions. |

Allowed `classification` values:

- `source-reference`
- `generated-payload-reference`
- `public-docs-claim`
- `tests-fixtures`
- `historical-or-archive`
- `repository-only-exclusion`
- `explicit-exclusion`

Allowed `active_runtime_status` values:

- `proven-active-runtime`
- `unproven-active-runtime`
- `not-active-runtime`

Allowed `owner_bucket` values:

- `xplat-005-read-only-helper`
- `xplat-006-mutation-helper`
- `xplat-007-cutover-guidance`
- `repository-only-exclusion`
- `public-docs-claim`
- `generated-payload-reference`
- `historical-or-archive`
- `follow-up-exception`

Allowed `follow_up_spec` values:

- `XPLAT-005`
- `XPLAT-006`
- `XPLAT-007`
- `repository-only-exclusion`
- `public-docs-claim`
- `generated-payload-reference`
- `historical-or-archive`
- `follow-up-exception`

## Aggregation Rules

Aggregate rows are used only when all represented matches share the same scan
command family, classification, active-runtime proof state, runtime relevance,
owner bucket, follow-up spec, invocation-mode category, and rationale.

Aggregate rows preserve:

- scan family and match count
- path set or path pattern
- representative evidence
- static invocation trace or evidence gap
- owner and follow-up rationale

If one match in an aggregate needs different ownership, proof state, invocation
mode, follow-up spec, or rationale, split that match into a separate row.

## Inventory Rows

| ID | Evidence | Classification | Active runtime status | Runtime relevance | Owner bucket | Follow-up spec | Invocation trace | Rationale |
|---|---|---|---|---|---|---|---|---|
| SRC-READ-001 | 1,951 scan hits across 61 source files, including `speckit-pro/codex-hooks.json`, `speckit-pro/hooks/hooks.json`, status/coach/grill-me guidance, gate/count helpers, and read-only autopilot checks. Representative evidence: `speckit-pro/codex-hooks.json` runs `jq` on submitted prompt JSON and checks `specify`; `speckit-pro/skills/speckit-status/SKILL.md` points at `generate-spec-index.sh --check "$PWD"` and `o5-topology.sh`; executor agents invoke `count-markers.sh`. | `source-reference` | `proven-active-runtime` | Installed Claude/Codex hooks, skills, agents, and read-only helper scripts depend on shell execution, `jq`, Unix paths, shell quoting, and `.sh` dispatch. | `xplat-005-read-only-helper` | `XPLAT-005` | Codex plugin manifest uses `skills: "./codex-skills/"` and `hooks: "./codex-hooks.json"`; Claude marketplace points to `dist/claude/speckit-pro`; source skills and agents instruct installed sessions to run these read-only helpers. | These references are active installed-runtime assumptions but do not intentionally mutate repository, user-local, or external state. XPLAT-005 owns parity for read-only/advisory helper behavior. |
| SRC-MUT-001 | 1,788 scan hits across 35 source files, including install/upgrade/archive/scaffold skills, `install-codex-agents.sh`, `install-curated-set.sh`, `generate-pr-body.sh`, `generate-uat-skeleton.sh`, `generate-spec-index.sh`, `final-reviewability-backstop.sh`, `relocate-process-artifacts.sh`, `multi-pr-emission.sh`, `restack.sh`, and migration/fixup helpers. | `source-reference` | `proven-active-runtime` | Installed workflows can copy agents, create/update files, write PR packet artifacts, move process files, create branches/PRs, or mutate local SpecKit state through Bash helpers. | `xplat-006-mutation-helper` | `XPLAT-006` | Install, upgrade, scaffold, archive, PRD, and autopilot skills directly instruct the agent to run these helper scripts. Mutation-capable helpers are grouped separately from read-only helpers by invoked mode. | These references require apply/write parity and rollback-safe behavior. XPLAT-006 owns mutation, install, and PR-emission helper ports after the runner foundation exists. |
| GEN-ACT-001 | 6,966 scan hits across 155 generated payload files under `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`, excluding generated README/CHANGELOG/LICENSE docs. Representative evidence mirrors generated skills, agents, hooks, and scripts such as `dist/codex/speckit-pro/codex-hooks.json` and generated autopilot scripts. | `generated-payload-reference` | `proven-active-runtime` | Marketplace installs consume generated payloads, so generated Bash and Unix assumptions matter to cutover even though source files remain authoritative edit targets. | `xplat-007-cutover-guidance` | `XPLAT-007` | `.claude-plugin/marketplace.json` points Claude to `./dist/claude/speckit-pro`; `.agents/plugins/marketplace.json` points Codex to `./dist/codex/speckit-pro`. | Generated payload rows generally remain cutover guidance for XPLAT-007; this PR only synchronized generated copies of the existing spec-index helper so shipped payloads match the source remediation. |
| GEN-DOC-001 | 44 scan hits across generated `README.md`, `CHANGELOG.md`, and `LICENSE` files under `dist/**`. | `generated-payload-reference` | `not-active-runtime` | These generated documentation files can mention commands or paths, but they are not runtime entrypoints. | `generated-payload-reference` | `generated-payload-reference` | No installed invocation trace from these files to helper execution. | Keep as generated documentation references. Source README/docs should be edited before payload rebuilds. |
| DOC-001 | 372 scan hits across 9 public documentation and marketplace metadata files, including docs-site pages, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, and plugin manifests. | `public-docs-claim` | `not-active-runtime` | Public docs and metadata may describe `jq`, Bash, cache paths, `.sh` scripts, or Unix locations, but text claims are not active runtime dependencies without a separate trace. | `public-docs-claim` | `public-docs-claim` | No direct invocation trace from docs pages or marketplace descriptions to helper execution. | These rows stay documentation claims. XPLAT-007 should update public claims only after cutover and release validation. |
| TEST-001 | 5,661 scan hits across 230 test, fixture, and expected-output files under `tests/**`. | `tests-fixtures` | `not-active-runtime` | Tests exercise Bash helpers and shell-shaped fixtures, but they are repository verification inputs, not installed plugin runtime surfaces. | `historical-or-archive` | `historical-or-archive` | No installed plugin invocation trace to test fixtures. | Keep out of runtime porting scope except where later specs reuse fixtures as parity evidence. |
| HIST-001 | 2,666 scan hits across 102 specs, workflow files, active XPLAT planning files, and `.specify/memory/**` archive reports. | `historical-or-archive` | `not-active-runtime` | Planning and archive material documents prior or current repo work; it does not execute as installed runtime. | `historical-or-archive` | `historical-or-archive` | No installed plugin invocation trace to archive/spec prose. | Keep as historical/process evidence. Later specs should cite only current source or report rows when selecting implementation work. |
| REPO-ONLY-001 | 1,714 scan hits across 90 repository-only files such as `.github/**`, `.claude/**`, root scripts, docs-site configuration, release metadata, and SpecKit extensions. | `repository-only-exclusion` | `not-active-runtime` | Maintainer, CI, release, and repository scaffolding commands may require Bash or Unix assumptions, but they are not installed Claude/Codex plugin runtime unless invoked by an installed plugin surface. | `repository-only-exclusion` | `repository-only-exclusion` | No installed plugin invocation trace found for these repository-only surfaces. | Exclude from runtime porting scope unless a later spec intentionally promotes one of these helpers into installed runtime. |
| EXCL-001 | `.git/`, untracked files, vendor/dependency caches, binary/non-text inputs skipped by `git grep -I`, and this generated report path. | `explicit-exclusion` | `not-active-runtime` | These inputs are outside the durable tracked-text source universe or would make the report recursively self-referential. | `repository-only-exclusion` | `repository-only-exclusion` | Not applicable. | Explicit exclusion details and expiry/removal conditions are recorded in the scan boundary table. |

No `unproven-active-runtime` rows remain. Rows are either proven by static
installed-surface traces or classified as not-active-runtime with the evidence
gap documented in the row rationale.

No `follow-up-exception` rows remain. Every active or generated active row maps
to XPLAT-005, XPLAT-006, or XPLAT-007.

## Reconciliation Counts

Classification counts:

| Classification | Represented scan hits |
|---|---:|
| `source-reference` | 3,739 |
| `generated-payload-reference` | 7,010 |
| `public-docs-claim` | 372 |
| `tests-fixtures` | 5,661 |
| `historical-or-archive` | 2,666 |
| `repository-only-exclusion` | 1,714 |
| `explicit-exclusion` | 0 |
| **Total** | **21,162** |

Active-runtime status counts:

| Active runtime status | Represented scan hits |
|---|---:|
| `proven-active-runtime` | 10,705 |
| `unproven-active-runtime` | 0 |
| `not-active-runtime` | 10,457 |
| **Total** | **21,162** |

Owner bucket counts:

| Owner bucket | Represented scan hits |
|---|---:|
| `xplat-005-read-only-helper` | 1,951 |
| `xplat-006-mutation-helper` | 1,788 |
| `xplat-007-cutover-guidance` | 6,966 |
| `generated-payload-reference` | 44 |
| `public-docs-claim` | 372 |
| `historical-or-archive` | 8,327 |
| `repository-only-exclusion` | 1,714 |
| `follow-up-exception` | 0 |
| **Total** | **21,162** |

Follow-up spec counts:

| Follow-up spec | Represented scan hits |
|---|---:|
| `XPLAT-005` | 1,951 |
| `XPLAT-006` | 1,788 |
| `XPLAT-007` | 6,966 |
| `generated-payload-reference` | 44 |
| `public-docs-claim` | 372 |
| `historical-or-archive` | 8,327 |
| `repository-only-exclusion` | 1,714 |
| `follow-up-exception` | 0 |
| **Total** | **21,162** |

Pattern-family by row group:

| Pattern family | Source read-only | Source mutation | Generated active | Generated docs | Public docs | Tests/fixtures | Historical/archive | Repo-only | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Bash / shell substrate | 178 | 80 | 423 | 16 | 17 | 441 | 1,005 | 219 | 2,379 |
| `.sh` helper references | 312 | 171 | 767 | 10 | 333 | 1,036 | 1,320 | 205 | 4,154 |
| `jq` references | 249 | 229 | 942 | 2 | 3 | 236 | 147 | 77 | 1,885 |
| Shell quoting / shell operators | 1,105 | 1,063 | 4,197 | 2 | 5 | 3,259 | 115 | 1,066 | 10,812 |
| Unix path assumptions | 104 | 241 | 623 | 14 | 14 | 646 | 48 | 124 | 1,814 |
| `chmod` references | 0 | 0 | 0 | 0 | 0 | 33 | 22 | 3 | 58 |
| Line-ending references | 3 | 4 | 14 | 0 | 0 | 10 | 9 | 20 | 60 |
| **Total** | **1,951** | **1,788** | **6,966** | **44** | **372** | **5,661** | **2,666** | **1,714** | **21,162** |

## Runtime Evaluation Rubric for XPLAT-002

XPLAT-001 does not score, rank, or select runtime candidates. XPLAT-002 should
use this rubric as a non-scoring template.

Must-have gates:

| Gate | Pass/fail question | Evidence target |
|---|---|---|
| Installed-cache invocation | Can the candidate run from installed Claude and Codex plugin cache paths without assuming a source checkout? | Install-cache smoke command, path resolution notes, cache-relative helper dispatch evidence. |
| Native platform behavior | Can the candidate run on native Windows, macOS, and Linux without Bash, Git Bash, WSL, PowerShell-only behavior, or `jq` as the implementation substrate? | Native invocation probe or vendor/runtime documentation plus local reproduction notes. |
| Filesystem and paths | Does it provide structured path handling, path normalization, temporary-file handling, and home/cache path support? | Fixture cases for repo root, cache root, temp directory, spaces in paths, and Windows separators. |
| JSON handling | Does it parse and emit JSON without shelling to `jq`? | JSON stdin/stdout fixture with parse failures and missing-field diagnostics. |
| Subprocess behavior | Does it support subprocess invocation, stdout, stderr, and exit-code mapping required by current helpers? | Parity fixture covering success, nonzero exit, stderr-only failure, and missing command. |
| Packaging and update path | Can the runtime artifact be packaged and updated through the public plugin distribution path? | Payload layout, version reporting, offline install behavior, and update/rebuild notes. |

Weighted criteria:

| Criterion | Weight |
|---|---:|
| Native platform behavior | 20 |
| Installed-cache invocation reliability | 15 |
| Dependency footprint and bootstrap burden | 15 |
| Packaging/distribution model | 15 |
| Offline behavior and update path | 10 |
| Diagnostics and error reporting | 10 |
| Maintainer ergonomics | 10 |
| Compatibility adapters and migration cost | 5 |
| **Total** | **100** |

Candidate evidence targets for XPLAT-002:

- JavaScript/TypeScript runner package.
- Python runner package.
- Small per-platform binary runner.
- Hybrid compatibility adapter that delegates to existing helpers only as a
  temporary migration path.

Do not include candidate scores, sample scoring, rankings, or a winner in
XPLAT-001 artifacts.

## Supply-Chain Evaluation Rubric for XPLAT-003

XPLAT-001 does not choose the security model or mandatory control set.
XPLAT-003 should use this rubric as a non-scoring template.

Must-have gates:

| Gate | Pass/fail question | Release boundary |
|---|---|---|
| Maintainer verification | Does the release process state what maintainers verify before publishing generated payloads and runtime artifacts? | `first-release-gate-question` |
| Consumer-local verification | Does the install path state what consumers can verify locally after installation? | `first-release-gate-question` |
| Truthful guarantees | Are claims limited to controls actually implemented and verified? | `first-release-gate-question` |
| Generated payload integrity | Can generated Claude and Codex payloads be traced to source inputs and release outputs? | `first-release-gate-question` |
| Provenance evidence | Is there a path to provenance/attestation evidence for runtime artifacts? | `deferred-hardening-evidence` unless XPLAT-003 makes it first-release required. |

Weighted criteria:

| Criterion | Weight |
|---|---:|
| Dependency policy and lockfile discipline | 15 |
| Generated payload integrity | 15 |
| Vulnerability scanning | 15 |
| Provenance or attestation options | 15 |
| Checksums/signatures | 10 |
| SBOM feasibility | 10 |
| Consumer-local verification | 10 |
| Release automation and documentation truthfulness | 10 |
| **Total** | **100** |

Artifact and control evidence targets for XPLAT-003:

| Evidence target | Boundary |
|---|---|
| Runtime dependency manifest and lockfile behavior | `first-release-gate-question` |
| Generated payload source-to-dist reproducibility notes | `first-release-gate-question` |
| Vulnerability scan command and failure policy | `first-release-gate-question` |
| Runtime artifact checksum publication | `first-release-gate-question` or `deferred-hardening-evidence` pending XPLAT-003 decision |
| Signature or attestation model | `deferred-hardening-evidence` |
| SBOM generation | `deferred-hardening-evidence` |
| Consumer-local install verification command | `first-release-gate-question` |
| Public documentation claim audit | `not-claimed-guarantee` until the control exists |

Do not select a required security model, require every evaluated control for the
first release, or imply guarantees before XPLAT-003 chooses and verifies them.

## Verification Evidence

Static verification for XPLAT-001:

| Check | Result |
|---|---|
| Scan commands rerun and counts reconciled | Passed: all seven recorded scan families matched the report counts, total 21,162 represented scan hits. |
| Proven active rows reviewed for caller-to-callee trace evidence | Passed: source active rows cite installed skill, hook, agent, or helper-script traces; generated active rows cite marketplace payload manifests. |
| Docs/generated/tests/archive/repo-only rows reviewed for false active-runtime promotion | Passed: docs, generated docs, tests, archive/spec, and repo-only rows remain `not-active-runtime` without separate invocation traces. |
| `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"` | Passed: `spec-index: index current — all in-scope maps up to date.` |
| `git diff --check` | Passed with no whitespace errors. |

## Handoff Notes

- XPLAT-002 should start from the runtime rubric and decide the runner contract.
- XPLAT-003 should start from the supply-chain rubric and decide first-release
  versus deferred-hardening controls.
- XPLAT-005 owns read-only/advisory helper parity after XPLAT-004 runner
  foundation exists.
- XPLAT-006 owns mutation, install, apply, PR-emission, and rollback-safe helper
  parity after XPLAT-004 runner foundation exists.
- XPLAT-007 owns generated payload cutover, public documentation claim updates,
  and native Windows release gates.

## PR Review Packet Evidence

What changed:

- Added this Markdown inventory and rubric report.
- Updated the XPLAT roadmap handoff notes.
- Corrected scoped roadmap-MOC index generation after PR review and synchronized
  the existing helper into generated Claude/Codex payload copies.

Why:

- Later runtime and supply-chain specs need a source-traceable split between
  active installed-runtime dependencies and non-runtime text matches.

Non-goals:

- No helper ports to a replacement runtime, runtime selection, security model
  selection, or public native Windows support claims. Generated payload changes
  are limited to synchronized copies of the existing spec-index helper
  remediation.

Review order:

1. Scan commands and reconciliation counts.
2. Inventory row classification and owner buckets.
3. Runtime rubric.
4. Supply-chain rubric.
5. Roadmap handoff.

Scope budget:

- Accepted reviewability warning; one report-focused docs/process spike.

Traceability:

- FR-001 through FR-007 map to scan boundary, inventory rows, and reconciliation
  counts.
- FR-008 maps to the runtime evaluation rubric.
- FR-009 maps to the supply-chain evaluation rubric.
- FR-010 through FR-012 map to non-goals and verification notes.
- FR-013 and FR-014 map to this Markdown report and handoff notes.

Known gaps:

- Native platform UAT is intentionally deferred to later XPLAT specs.
- Candidate scoring and selection are intentionally deferred to XPLAT-002 and
  XPLAT-003.

Rollback:

- Revert this report, the roadmap handoff update, and the scoped spec-index
  generator remediation plus synchronized generated payload copies.

# Data Model: Runtime Inventory and Constraints

## Inventory Finding

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Stable row identifier for review discussion. |
| `evidence` | Yes | Path and concise evidence excerpt or match summary. |
| `classification` | Yes | Physical/source classification for the reference. |
| `active_runtime_status` | Yes | Proof state for active installed-runtime relevance. |
| `runtime_relevance` | Yes | Why the reference matters or does not matter to installed runtime behavior. |
| `owner_bucket` | Yes | Handoff bucket for later specs or exclusion. |
| `follow_up_spec` | Yes | XPLAT spec or exclusion owner responsible for later action. |
| `invocation_trace` | Conditional | Required for `proven-active-runtime`; evidence gap required for `unproven-active-runtime`. |
| `rationale` | Yes | Classification and ownership explanation. |
| `exclusion_or_exception_detail` | Conditional | Required for explicit exclusions and `follow-up-exception` rows. |

## Classification Values

| Value | Meaning |
|-------|---------|
| `source-reference` | Source-controlled installed plugin skill, agent, hook, script, or manifest reference. |
| `generated-payload-reference` | Generated `dist/**` payload reference; not authoritative edit target. |
| `public-docs-claim` | Public documentation or README claim. |
| `tests-fixtures` | Test, fixture, or expected-output reference. |
| `historical-or-archive` | Archive report or historical completed-spec material. |
| `repository-only-exclusion` | Maintainer, CI, release, or root tooling with no installed-runtime trace. |
| `explicit-exclusion` | Binary, untracked, vendor cache, `.git/`, or non-text input excluded with rationale. |

## Active Runtime Status Values

| Value | Meaning |
|-------|---------|
| `proven-active-runtime` | Static caller-to-callee invocation trace proves installed runtime relevance. |
| `unproven-active-runtime` | Probably or possibly active, but evidence is incomplete and the gap is documented. |
| `not-active-runtime` | No installed-runtime invocation trace; classified as docs, generated, tests, archive, repo-only, or exclusion. |

## Owner Buckets

| Bucket | Use |
|--------|-----|
| `xplat-005-read-only-helper` | Traced read-only/advisory installed invocation with no repository, user-local, or external mutation. |
| `xplat-006-mutation-helper` | Traced write/apply/live/install/PR-emission behavior or mutation-capable dry-run/apply parity concern. |
| `xplat-007-cutover-guidance` | Active installed-workflow guidance, generated payload cutover, or public claim that must change during final cutover. |
| `repository-only-exclusion` | No installed-runtime invocation trace; keep out of runtime porting scope. |
| `public-docs-claim` | Public docs row that remains a claim unless linked to a separate active finding. |
| `generated-payload-reference` | Generated artifact row with source link; not an authoritative edit target. |
| `historical-or-archive` | Historical evidence only. |
| `follow-up-exception` | Active or probably active row that cannot honestly map to another bucket. Requires reason, evidence gap, expiry/removal condition, and named follow-up decision. |

## Runtime Rubric

The runtime rubric is a non-scoring template for XPLAT-002.

### Must-Have Gates

- Candidate can be invoked from installed Claude and Codex plugin caches.
- Candidate can run on native Windows, macOS, and Linux without Bash, Git Bash,
  WSL, PowerShell-specific commands, or `jq` as implementation substrate.
- Candidate supports structured filesystem, path, JSON, subprocess, stdout,
  stderr, and exit-code behavior needed by existing helpers.
- Candidate has a plausible packaging and update path for public plugin
  distribution.

### Weighted Criteria

| Criterion | Weight |
|-----------|--------|
| Native platform behavior | 20 |
| Installed-cache invocation reliability | 15 |
| Dependency footprint and bootstrap burden | 15 |
| Packaging/distribution model | 15 |
| Offline behavior and update path | 10 |
| Diagnostics and error reporting | 10 |
| Maintainer ergonomics | 10 |
| Compatibility adapters and migration cost | 5 |
| **Total** | **100** |

## Supply-Chain Rubric

The supply-chain rubric is a non-scoring template for XPLAT-003.

### Must-Have Gates

- The model states what maintainers verify before release.
- The model states what consumers can verify locally after installation.
- The model does not claim guarantees that are not implemented.
- The model covers generated payload integrity and runtime artifact provenance.

### Weighted Criteria

| Criterion | Weight |
|-----------|--------|
| Dependency policy and lockfile discipline | 15 |
| Generated payload integrity | 15 |
| Vulnerability scanning | 15 |
| Provenance or attestation options | 15 |
| Checksums/signatures | 10 |
| SBOM feasibility | 10 |
| Consumer-local verification | 10 |
| Release automation and documentation truthfulness | 10 |
| **Total** | **100** |

## Summary Counts Required in Report

- Count by `classification`.
- Count by `active_runtime_status`.
- Count by `owner_bucket`.
- Count by `follow_up_spec`.
- Count of explicit exclusions with rationale.
- Count of `follow-up-exception` rows, if any, with expiry/removal condition.

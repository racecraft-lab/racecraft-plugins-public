# Research: Claude/Codex Cutover and Universal Install Release Gate

## Decision 1: Keep XPLAT-008 as one spec with three internal slices

**Decision**: Use three internal vertical slices: active installed-runtime cutover; generated payload, release, and public docs gates; native UAT/update/repair evidence.

**Rationale**: The release gate is coherent only when active invocation, generated payload completeness, public claims, UAT rows, update proof, and repair proof can be traced together. The setup warning is accepted because the plan preserves review order and explicit boundaries.

**Alternatives rejected**:

- Child specs now: safer PR size, but adds coordination overhead before the release contract is proven.
- Two slices: follows the estimator minimum but blurs UAT/update/repair ownership.
- Single pass: fastest to start but too difficult to review.

## Decision 2: Invoke the installed runtime through direct Python module argv

**Decision**: Active installed Claude and Codex surfaces must resolve Python `>=3.11` and invoke `[resolved_python, "-m", "speckit_pro_runner"]`, sending one JSON request on stdin and parsing one JSON response from stdout.

**Rationale**: This is the only invocation model that satisfies native Windows/macOS/Linux installed-runtime support without Bash, Git Bash, WSL, `jq`, shell interpolation, shell redirection, or PowerShell-specific command language.

**Alternatives rejected**:

- Thin shell dispatch: simpler on Unix, but incompatible with native Windows as the required installed-plugin path.
- Docs-only handoff: too weak because payloads and UAT would not validate the actual installed behavior.

## Decision 3: Use platform-specific interpreter discovery with explicit diagnostics

**Decision**: Probe Windows candidates in this order: `py -V:3`, `py -3`, `python`, `python3`. Probe macOS and Linux candidates in this order: `python3`, then `python`. Accept only Python `>=3.11`.

**Rationale**: The order matches the clarified spec, covers common native launchers, and keeps failure output actionable without shell fallback.

**Diagnostics required**: attempted candidates, resolved executable when present, version, platform, plugin/cache root, failure code, stderr or diagnostic text, and exact remediation.

## Decision 4: Scope no-shell/no-jq guards to active installed-runtime surfaces

**Decision**: Guard active Claude/Codex skills, agents, hooks, install guidance, generated runtime payloads, and release gates. Allow archive/provenance text, tests/fixtures, generated changelog or README prose not used as active runtime instruction, minimal CI dispatch glue that only invokes Python gates, and upstream Spec Kit generated `.specify/scripts/bash/` helpers in consumer projects.

**Rationale**: This keeps the public installed-runtime path strict while avoiding noisy historical rewrites unrelated to user execution.

**Alternatives rejected**:

- Repo-wide purge: would rewrite archive and provenance material outside the release risk.
- Advisory-only docs scan: would not block public release when shell-only installed behavior returns.

## Decision 5: Build payload completeness from source-derived inventory

**Decision**: The expected Claude and Codex payload inventory is derived from source, not from current `dist/**`. The gate compares rebuilt/staged output and committed `dist/**` against expected files, explicit transforms, version metadata, runner files, manifest/checksum metadata, and XPLAT-003 trust records.

**Rationale**: Generated payloads are what users install, but source remains authoritative. A source-derived contract prevents stale or incomplete dist trees from passing release readiness.

**Claude payload includes**: `.claude-plugin/plugin.json`, Claude skills, Claude agents, hooks, install guidance, full `speckit_pro_runner` package, runner manifest/checksum metadata, release/version metadata, and XPLAT-003 trust records.

**Codex payload includes**: `.codex-plugin/plugin.json`, Codex-normalized skills, Codex agents, `codex-hooks.json`, install guidance, full `speckit_pro_runner` package, runner manifest/checksum metadata, release/version metadata, and XPLAT-003 trust records.

## Decision 6: Treat release readiness as an aggregate blocking contract

**Decision**: Release readiness fails on active shell runtime dependencies, incomplete payload inventory, missing bundled agents, missing hooks, missing runner files, stale generated payloads, stale version metadata, missing or mismatched manifest/checksum/trust records, unsupported public claims, incomplete UAT/update/repair evidence, unsafe repair claims, path leakage, extra files, or non-deterministic generated files.

**Rationale**: This matches the success criteria and gives maintainers a single release blocker that can explain each failing class.

**Version rule**: Source manifests, generated manifests, marketplace indexes, `.release-please-manifest.json`, runner manifest `plugin_version`, and generated release evidence must agree. `runner_version` is independent but must be present and verified. Manual plugin version edits remain out of scope.

## Decision 7: Store durable UAT evidence in a feature-local matrix

**Decision**: Native UAT evidence lives in `specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/uat-matrix.md`, with optional detailed evidence files under `.process/uat/`.

**Rationale**: The matrix gives reviewers one durable table for the six product/platform rows and prevents smoke-only or private evidence from satisfying release readiness.

**Rows required**: Claude on Windows, Claude on macOS, Claude on Linux, Codex on Windows, Codex on macOS, and Codex on Linux.

**Fields required**: platform, product, operator/date, host version, plugin version or latest tag, installed cache path, interpreter resolution, runner invocation IDs, install result, bundled-agent verification, first use, scaffold/status, autopilot dry-run, latest-tag update, incomplete-install repair, expected result, actual result, evidence link, operator notes, and pass/fail.

## Decision 8: Limit autoheal to checksum-backed trusted cache artifacts

**Decision**: Autoheal may refresh only bounded installed-cache artifacts with verified expected path, source identity, release channel or latest tag, and SHA-256 or file-tree digest. Candidate artifacts are generated payload files, bundled agents, hooks, runner files, and manifest/checksum metadata inside the trusted installed plugin cache.

**Rationale**: This satisfies safe repair without broad reinstall behavior or unsafe cache mutation.

**Manual remediation required for**: unknown files, extra or untracked files, path traversal, out-of-cache targets, missing trust metadata, digest or source mismatch, trust-root changes, marketplace-source drift, unsupported platform claims, real-home mutation before active cutover, and any broad reinstall or wipe-copy behavior.

## Decision 9: Keep public trust wording tied to implemented controls

**Decision**: Public docs and release notes may claim only implemented and verified controls: Python 3.11+ standard-library installed runtime, source-built generated payloads with completeness/version/SHA-256 manifest gates, runner preflight or doctor checks, local verification, bounded repair, manual remediation for unsafe drift, and native product/platform support only for passing UAT rows.

**Rationale**: XPLAT-003 provides a consumer-trust model, not a cryptographic supply-chain guarantee.

**Claims not allowed**: signing, SBOMs, SLSA, in-toto attestations, reproducible-build guarantees, formal audit/certification, vulnerability-free status, marketplace-enforced verification, or cryptographic trust-chain verification unless implemented and evidenced separately.

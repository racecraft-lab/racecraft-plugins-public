# Research: G56R-005 Model Availability, Fallback, and Recovery Simulation

## Decision 1: Codex-local resolver rather than shared Claude/Codex core

**Decision**: Implement a new `codex_route_fallback.py` simulation module for Codex route evidence.

**Rationale**: Existing Claude fallback code and tests are preservation evidence, not a contract to import. The Codex reason vocabulary intentionally differs, especially `capability_discovery_unavailable`.

**Alternatives considered**: Reusing `claude_route_fallback.py` or extracting a shared core. Rejected because G56R-005 must preserve frozen Claude behavior and avoid cross-platform reconciliation before CAR-012/G56R-012.

## Decision 2: Treat `autopilot-fast-helper.toml` as conditional optional helper state

**Decision**: Validate all bundled Codex source TOML files for source integrity, but exclude `autopilot-fast-helper.toml` from required-agent destination all-or-nothing completeness in the simulation. Track it as optional helper availability and require an explicitly qualified no-helper continuation before continuing.

**Rationale**: The autopilot runtime contract describes `autopilot-fast-helper` as optional. Required-agent install safety must still prove all-or-nothing behavior for the required executor/analyst set.

**Alternatives considered**: Counting the helper as required destination material. Rejected for the simulation contract because it would make optional-helper degradation impossible to represent without contradicting the runtime contract.

## Decision 3: Fake-home writes require a harness-created temporary root

**Decision**: Checked-in fixture trees are immutable seeds. Mutation replay copies seed state into a temporary fake home and may write only under `<fake_home_root>/.codex/agents`.

**Rationale**: Existing installer code already distinguishes fake-home safety from real-home mutation. G56R-005 needs byte-stable recovery evidence without touching a real user install.

**Alternatives considered**: Mutating checked-in fixture paths directly. Rejected because it would make tests order-dependent and risk committing generated state.

## Decision 4: Recovery identity uses canonical manifests

**Decision**: State IDs are SHA-256 digests of sorted fake-home-relative path entries containing content digest, mode, and required/optional role classification.

**Rationale**: Absolute temp roots, mtimes, inodes, and host paths are unstable. Content manifests provide deterministic replay identity.

**Alternatives considered**: Comparing directory snapshots with host metadata. Rejected because it breaks byte-stability across hosts.

## Decision 5: Service reroute evidence is attribution, not plugin reason order

**Decision**: Record service reroute evidence in a distinct attribution record and keep plugin diagnostics in the fixed local order.

**Rationale**: Scoring eligibility needs both facts: route qualification and approved/unapproved service attribution. Interleaving service facts into local reasons would misattribute external behavior to plugin logic.

**Alternatives considered**: Emitting reroutes as ordinary plugin diagnostics. Rejected because it loses origin and approval semantics.

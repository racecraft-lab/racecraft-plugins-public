# Quickstart: G56R-004 Policy Controls and Adaptive Comparators

## Prerequisites

- Worktree:
  `docs/ai/specs/.process/G56R-004-workflow.md` must be present in the checkout.
- Branch:
  `g56r-004-policy-controls-adaptive-comparators`.
- Runtime:
  Python 3.11+ standard library only.
- Live smokes:
  explicit operator authorization is required and is not assumed by this plan.

## Automated Replay Validation

After implementation, run the Layer 4 owners first:

```bash
python3 tests/speckit-pro/unit/test-policy-control-contracts.py
python3 tests/speckit-pro/unit/test-control-comparison-dominance.py
python3 tests/speckit-pro/unit/test-twin-handoff-completeness.py
```

Expected result:

- Codex registry contains exactly `unpinned`, `adaptive`, and
  `justified_high_effort`.
- Seeded fourth-control, duplicate-kind, digest-drift, reserved-objective, and
  second-divergence cases fail closed.
- Adaptive replay proves totality, precedence, consistency, no-wrap movement,
  three-clean-pass de-escalation, bound breaches, and service-reroute
  non-scorability.
- Comparison replay proves eligibility floors, eight direction-aware
  dimensions, 10% margins, zero denominator, confidence/multiplicity, no
  weights, and total claim-class mapping.
- Every replayed control fixture emits byte-identical governed results across
  repeated runs and no scored evidence.

## Repository Gates

Run the relevant repository gates after the narrow tests:

```bash
python3 tests/speckit-pro/run-all.py --layer 4
python3 tests/speckit-pro/run-all.py --layer 1
python3 tests/speckit-pro/run-all.py
```

Expected result:

- Layer 4 passes with the new/modified durable test owners.
- Layer 1 passes after any `suite-manifest.json` update.
- The full default suite passes with zero failures.

If tracked `.md`, `.py`, or `.sh` files under `tests/speckit-pro/` change, run
the docs-site reference generation/check required by root `AGENTS.md` after
installing docs dependencies for the worktree:

```bash
pnpm --dir docs-site install --frozen-lockfile
pnpm --dir docs-site reference:generate
pnpm --dir docs-site reference:check
```

Expected result: generated reference output is current and no generated drift is
left unaccounted.

## Operator-Only Smoke Procedure

Do not run these smokes during automated implementation unless the operator
explicitly authorizes live work.

When authorized, prepare one non-scored ChatGPT-sign-in smoke per control:

1. Unpinned control: verify produced evidence reads back the served model and
   effort equal to the pinned parent and all required local overrides absent.
2. Adaptive control: verify produced evidence reads back the qualifying signal
   and route/model/effort movement from declared ladder index `i` to `i + 1`.
3. Justified-high-effort control: verify produced evidence reads back the frozen
   route/model/effort, a true eligibility result, and complete
   parent-plus-children aggregation for spawned child work.

Expected result:

- `authentication_mode` is observed as `chatgpt_subscription`.
- API-key auth, missing auth observation, or ambiguous auth mode seals a refused
  record.
- Each smoke stays inside five non-reserved objectives, one repetition, zero
  confirmation entries, 1,800 seconds, 1,000,000 raw tokens, and the component
  and cache ceilings.
- Cache isolation is `observed_disjoint` with root digests for all three
  unordered control pairs.
- Raw prompts, responses, local paths, and operator captures remain
  off-repository.
- If authorization is absent, smoke evidence and dependent success criteria are
  reported as `unrun`.

## Final Review Checklist

- No frozen G56R-003/CAR-003 artifact changed.
- No raw live capture material is committed.
- Exactly one sanctioned platform divergence remains.
- G56R-011 reserved partition is mechanically untouched.
- PR packet maps requirements and success criteria to changed files,
  verification evidence, known gaps, operator-only smoke status, and
  non-applicability notes for runtime/installer/release behavior.

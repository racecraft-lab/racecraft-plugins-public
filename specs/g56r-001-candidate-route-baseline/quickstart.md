# Quickstart: Validate the G56R-001 Research Handoff

This is a reviewer validation guide. It does not implement the research,
discover capabilities, probe a runtime, score candidates, or mutate routes.

## Prerequisites

- Run from the repository root on branch
  `g56r-001-candidate-route-baseline`.
- Use Python 3.11 or newer.
- The one-working-day implementation must have produced:
  - `docs/ai/research/codex-agent-route-candidates.md`
  - `docs/ai/research/codex-agent-route-candidate-manifest.json`
  - `specs/g56r-001-candidate-route-baseline/check-artifacts.py`
- The focused checker test and its Layer 4 declaration must exist at:
  - `tests/speckit-pro/unit/test-g56r-001-artifacts.py`
  - `tests/speckit-pro/suite-manifest.json`

Review [data-model.md](data-model.md) and
[contracts/agent-route-candidate-manifest.md](contracts/agent-route-candidate-manifest.md)
before interpreting the checker result.

## 1. Confirm the delivery and validation boundary

```bash
git diff --name-only <base-revision>...HEAD
```

Expected research delivery paths are exactly the narrative, manifest, and
feature-local checker above, plus the focused Layer 4 test and its existing
suite-manifest declaration. Workflow/spec planning checkpoints may appear
separately in the autopilot history, but no plugin, agent, installer, payload,
cache, installed-state, route-default, version, generated-release, or
unrelated configuration file belongs to the implementation delivery.

## 2. Run the focused unit coverage and checker twice

```bash
python3 tests/speckit-pro/unit/test-g56r-001-artifacts.py
python3 specs/g56r-001-candidate-route-baseline/check-artifacts.py
python3 specs/g56r-001-candidate-route-baseline/check-artifacts.py
```

Both runs must exit zero and print the same summary, including:

- manifest type and version;
- exactly 12 unique agents;
- exactly 10 present routes and absent routes only for
  `consensus-synthesizer` and `gate-validator`;
- 3 current and 9 missing fixture contracts;
- valid/unique IDs and repeatable hashes;
- complete provenance, surfaces, candidates, telemetry, and unknown ownership;
- zero sanitization violations;
- Markdown/JSON agreement; and
- the same reproduced `go` or `no_go` handoff as the artifacts.

The checker must be offline and read-only. Any network request, runtime probe,
candidate execution, scoring, qualification, or file mutation is a failure of
the validation design.

## 3. Inspect the objective handoff

For `go`, verify every completion check passes, `unmet_conditions` is empty,
and there is no blocking conflict or unclassified unknown.

For `no_go`, verify the workday stop timestamp is present and every unmet
condition includes:

```text
gate_id
requirement_refs
condition
available_evidence_ids
impact
owner_spec
required_follow_up
```

`no_go` is a valid terminal result. Do not extend the spike, weaken the gate,
or reduce accepted deliverables.

## 4. Perform the human evidence review

Review in this order:

1. Narrative evidence matrix and claim labels.
2. Twelve role contracts and present/absent production baselines.
3. Candidate tuples, controls, eligibility, incompatibilities, and hypotheses.
4. JSON projection and canonical IDs/hashes.
5. Fixture contracts, telemetry requirements, unknown owners, and handoff.
6. Focused checker output.

Confirm these boundaries manually:

- Platform facts cite current official OpenAI URLs with exact locator,
  retrieval date, surface, scope, applicability, conflicts, and invalidation.
- Project facts cite repository-relative paths, revision, and evidence role.
- Tracked, cache, and installed observations remain separate.
- Local observations contain no absolute/home paths, identity, credentials,
  secrets, or unrelated configuration.
- No candidate is removed for local unavailability.
- No candidate is called executable, qualified, preferred, or an ordered
  fallback.
- Historical prompt-emulation results are `non_release_evidence`.
- Discovered defects are recorded with owners and are not fixed here.

## 5. Run repository regression gates

```bash
python3 tests/speckit-pro/run-all.py --layer 4
python3 tests/speckit-pro/run-all.py --integration
python3 tests/speckit-pro/run-all.py
git diff --check
```

Expected result: all commands exit zero. The default suite is the final
deterministic repository gate; `--all` is not used because it implies live mode.

## Failure handling

If the checker or a repository gate fails:

1. Preserve the exact failure and evidence IDs.
2. Fix only incomplete or inconsistent research artifacts/checker logic that
   remains inside G56R-001.
3. Do not probe, score, qualify, mutate production state, repair discovered
   source defects, or add a generic framework.
4. At the workday boundary, record any remaining objective failure in the
   `no_go` packet with its owning spec and required follow-up.

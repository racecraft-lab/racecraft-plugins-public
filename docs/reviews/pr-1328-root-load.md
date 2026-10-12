# Canary receipt root-load consistency

The receipt validator owns the plan-stage root-load consistency check for both
hosts, both run modes, and every variant that supplies segment evidence. Base
requires all seven segments; other variants may omit the map.

For an attributed call, a single-call average equals its peak. For multiple
calls, the average lies between peak divided by call count and peak. Fractional
averages use the floating-point representation of the lower bound; integer
averages use exact integer arithmetic. A zero average cannot accompany a
nonzero peak. Codex plan root-token usage requires at least one attributed call
when segment evidence is present. Invalid evidence cannot certify the plan
target.

## Known limits

- Claude stage `tokens` combines usage without distinguishing root from child
  usage. All-zero root-call attribution with `tokens=10` can describe child-only
  usage; the receipt does not prove a root call. Rejecting that input would
  reject a permitted receipt rather than close a reachable attribution bypass.
- A claimed call with average and peak both zero remains accepted. These are
  self-attested measurements with no independent trace, so rejecting zero
  would not establish that any other supplied measurement was observed.
- Positive call attribution with zero measured Codex root-token usage is not
  rejected. The contract requires positive root usage to have a call, not the
  reverse; without a trace the receipt cannot independently prove a claimed
  call. This is the same self-attestation limit, not an omitted stated rule.
- Segment evidence outside plan is accepted by the shared stage shape but does
  not affect plan attribution or any gate. This is an existing accepted limit,
  not another path into the plan consistency check.
- Nonbase variants may omit segment evidence by contract; an omitted map makes
  no root-load claim to validate. Token accounting still includes root and all
  children and remains checked independently.
- The receipt cannot independently prove call provenance, deduplication or
  completeness. Numeric consistency validates the supplied summary only.
- Above `2**53`, a fractional average rounded above an integer peak is still
  rejected by the existing average-at-most-peak rule; a single-call average
  must equal the peak exactly. This constructed precision case fails closed,
  does not reach a successful gate, and is outside the reported fail-open
  class. Integer averages avoid that representation limit.

## Regression coverage

`tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` exercises the
public API and CLI. `CanaryRootContextTests` rejects impossible single-call and
multi-call summaries in every segment. `CanaryRootAttributionTests` rejects
Codex root usage without calls, preserves child-only and Claude aggregate
usage, preserves the zero-context limit, and checks the existing zero-call
schema and average-above-peak rejections. The matrices cover both hosts,
flat/nested modes, and all five variants with supplied maps.

`test_attributed_root_calls_do_not_prove_measured_root_token_usage` preserves
the documented reverse-attribution limit for Codex in both modes and all five
variants. The existing average-above-peak rejection also covers a fractional
average rounded above its integer peak.

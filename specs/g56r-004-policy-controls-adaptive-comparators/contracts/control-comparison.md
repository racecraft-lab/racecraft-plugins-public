# Contract: Control Comparison

## Scope

The implementation publishes a Codex-local JSON Schema and fixture pair:

- `tests/speckit-pro/layer6-efficiency/contracts-codex-specification/control-comparison.schema.json`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/control-comparison.json`

The schema `$id` is
`https://racecraft.dev/schemas/g56r-004/control-comparison.schema.json`.
The comparison ID is `g56r-004-control-comparison`.

## Evaluation Order

Dominance evaluation is gate-first:

1. Eligibility floors
2. Environment-independent Pareto comparison
3. Materiality margin

An unmet floor returns the no-verdict outcome and `no_comparative_claim`; it is
not `not_dominant`.

## Dimensions

Exactly eight dimensions are compared:

| Dimension | Source | Direction | Class | Margin |
|-----------|--------|-----------|-------|--------|
| `input_tokens` | raw/resource vector | lower is better | margin-eligible | 10% |
| `cached_input_tokens` | raw/resource vector | lower is better | margin-eligible | 10% |
| `output_tokens` | raw/resource vector | lower is better | margin-eligible | 10% |
| `duration` | `duration_ms` projection | lower is better | margin-eligible | 10% |
| `retries` | aggregate count | lower is better | no-worse-only | none |
| `compactions` | aggregate count | lower is better | no-worse-only | none |
| `acceptance` | parent objective oracle | higher is better | no-worse-only | none |
| `terminal_state` | aggregate terminal state | equal only | no-worse-only | none |

Material dominance requires no dimension worse and at least one
margin-eligible dimension clearing the frozen 10% relative improvement.

## Confidence And Multiplicity

The confidence method is a one-sided lower confidence bound with 95% confidence
and alpha `0.05`, using the mirrored cluster method. Deterministic replay may
use the point estimate only as a declared non-outcome-bearing stand-in.

The secondary control-arm family remains disjoint from the primary comparison
family. No weight, scalar score, forced rank, or price coefficient is allowed.

## Edge Outcomes

- Zero comparator denominator returns `margin_not_computable`.
- Mixed, tied, incomplete, statistically uncertain, null-acceptance, or
  differing terminal-state comparisons produce the mirrored inconclusive or
  no-verdict outcome.
- A false, missing, or unreproducible justified-high-effort eligibility
  predicate makes the control ineligible for a dominance verdict.

## Claim Classes

The verdict-to-claim-class map is total over `dominant`, `not_dominant`,
`inconclusive`, and eligibility-floor no-verdict. Only `dominant` carries a
messaging restriction: static defaults may still ship for declared operational
simplicity, but release wording must not claim efficient, optimal, or
best-measured routing.

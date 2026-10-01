## Answer

Count tokens `per-request`.

## References

- **Artifact**: Technical roadmap
  **Section**: Usage reporting
  **Relevance**: The roadmap requires the usage report to count LLM tokens for
  each request. Aggregating per billing period would drop that stated
  requirement, so `per-request` is the most conservative option that satisfies
  the spec. The privacy concern is met by keeping user identifiers out of the
  usage rows, which changes no scope.

## Confidence

high

**Rationale**: The roadmap decision addresses the report's grain directly, and
the alternative fails it.

## Security Relevance

security_relevant: true

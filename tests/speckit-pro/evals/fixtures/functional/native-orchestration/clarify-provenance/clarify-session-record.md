# Clarify Session Record

## Session 1: Retention

- Question: How long are refresh tokens retained?
- Executor recommendation: 30 days.
- Operator reply: "Use 14 days, not 30."
- Accepted answer: 14 days.

## Session 2: Rate limits

- Question: Which backoff policy applies to upstream rate limits?
- Executor recommendation: Exponential backoff with full jitter.
- Operator reply: none
- Consensus (2 of 3 analysts): Exponential backoff with full jitter, capped at 60 seconds.
- Accepted answer: Exponential backoff with full jitter, capped at 60 seconds.

## Session 3: Audit export

- Question: Which format does the audit export use?
- Executor recommendation: CSV.
- Operator reply: "JSON Lines."
- Accepted answer: JSON Lines.

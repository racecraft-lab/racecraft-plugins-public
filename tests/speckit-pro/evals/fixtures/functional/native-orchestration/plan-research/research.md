# Research: Token Service

## Refresh-token retention window

- Decision: Retain refresh tokens for 30 days.
- Rationale: Current guidance for comparable services uses a 30-day window.
- Alternatives considered: 7 days; 90 days.

## Upstream rate-limit backoff policy

- Decision: Exponential backoff with full jitter, capped at 60 seconds.
- Rationale: Published provider documentation recommends this policy.
- Alternatives considered: Fixed delay; linear backoff.

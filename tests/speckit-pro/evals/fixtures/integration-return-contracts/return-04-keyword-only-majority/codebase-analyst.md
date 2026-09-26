## Answer

Count tokens `per-request`.

## Evidence

- **File**: `src/usage/recorder.ts` (line 22)
  **Pattern**: The retained fixture records one usage row per LLM request,
  with its prompt and completion token counts.

## Confidence

high

**Rationale**: The existing recorder already stores counts at this grain.

## Security Relevance

security_relevant: false

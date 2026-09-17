## Answer

Use JSON for the new endpoint.

## Evidence

- **File**: `src/api/serializer.ts` (line 8)
  **Pattern**: The retained fixture records `JSON.stringify` as the universal
  outbound serializer.

- **File**: `src/api/serializer.ts` (line 1-30)
  **Pattern**: The retained fixture reports no alternative serializer in this
  source file.

## Confidence

high

**Rationale**: The recommendation follows the retained codebase's established
serialization pattern.

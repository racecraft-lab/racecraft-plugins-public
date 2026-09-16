## Answer

Stay on bcrypt for consistency with the existing implementation.

## Evidence

- **File**: `src/auth/password.ts` (line 14)
  **Pattern**: The retained fixture records bcrypt with cost factor 12 as the
  existing password-hashing pattern.

- **File**: `src/auth/password.ts` (line 1-40)
  **Pattern**: The retained fixture reports no Argon2 implementation in this
  source file.

## Confidence

medium

**Rationale**: The recommendation follows the one retained codebase pattern,
but it does not establish which algorithm should be preferred for new code.

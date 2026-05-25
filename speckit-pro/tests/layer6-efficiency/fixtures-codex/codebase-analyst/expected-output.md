## Answer

The default page size should be **50 items**, matching the existing
default used by every other list endpoint in the codebase. The default
is defined as a module-level constant `DEFAULT_PAGE_SIZE = 50` in
`src/pagination/constants.py` and re-exported from `src/pagination/__init__.py`.
SPEC-006 (notifications) and SPEC-007 (repetition) both consume that
constant directly rather than redeclaring their own, and the new
`list_tasks` endpoint should follow the same pattern.

## Evidence

- **File**: `src/pagination/constants.py` (lines 12-14)
  **Pattern**: `DEFAULT_PAGE_SIZE = 50` is the single source of truth
  for the project-wide pagination default. A comment above the constant
  references SPEC-006 as the originating decision.

- **File**: `src/pagination/__init__.py` (lines 4-7)
  **Pattern**: Re-exports `DEFAULT_PAGE_SIZE` so downstream modules
  import from `src.pagination` rather than reaching into
  `src.pagination.constants` directly.

- **File**: `src/notifications/list_notifications.py` (line 28)
  **Pattern**: Established consumer — `limit = limit or DEFAULT_PAGE_SIZE`.
  This is the canonical fallback pattern other endpoints copy.

- **File**: `src/repetition/list_repetitions.py` (line 31)
  **Pattern**: Same fallback pattern, confirms the precedent is
  consistent across SPEC-006 and SPEC-007.

## Confidence

high

**Rationale**: Two prior specs (SPEC-006, SPEC-007) consume the same
constant from the same module via the same pattern. The default is
documented in a constants file, not hardcoded at call sites, which makes
the precedent unambiguous.

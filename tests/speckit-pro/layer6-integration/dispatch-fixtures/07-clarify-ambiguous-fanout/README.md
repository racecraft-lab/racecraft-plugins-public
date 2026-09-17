# Fixture 07 — Ambiguous tag → full fan-out

Verifies that `[ambiguous]` (used when the clarify-executor cannot
determine which routing perspective applies) fans out to all 3
analysts. This prevents premature single-perspective routing on
genuinely cross-cutting questions.

# TDD Protocol

Injected into every implementation subagent's prompt by the
autopilot orchestrator. These rules are NON-NEGOTIABLE regardless
of which agent executes the task.

## RED-GREEN-REFACTOR Cycle

For your assigned task:

1. **RED** — Write tests FIRST:
   - Contract tests for input/output schemas
   - Unit tests for business logic
   - Integration tests for end-to-end behavior (if applicable)
   - Run tests — they MUST FAIL with real assertion errors
   - Do NOT write implementation code yet

2. **GREEN** — Write MINIMUM code to pass:
   - Implement only what's needed to make tests green
   - Run tests — they MUST PASS
   - Do NOT optimize or refactor yet

3. **REFACTOR** — Clean up while green:
   - Improve code quality, remove duplication
   - Run tests — they MUST STAY GREEN

Use the **single-file command** for per-task RED/GREEN verification:

```text
CORRECT (unit/contract test):
  1. Write test file
     → Bash("SINGLE_FILE_TEST tests/myTest.test.ts")
     Output: "3 failed"     ← VERIFIED RED
  2. Write implementation
     → Bash("SINGLE_FILE_TEST tests/myTest.test.ts")
     Output: "3 passed"     ← VERIFIED GREEN

CORRECT (integration test):
  1. Write test file
     → Bash("SINGLE_FILE_INTEGRATION tests/integration/myTest.integration.test.ts")
     Output: "2 failed"     ← VERIFIED RED
  2. Write implementation
     → Bash("SINGLE_FILE_INTEGRATION tests/integration/myTest.integration.test.ts")
     Output: "2 passed"     ← VERIFIED GREEN

WRONG:
  1. Write implementation + tests together
     → Bash("UNIT_TEST") → "all passed"
     ← Never verified RED — tests might not test anything
  2. Run integration test with unit test command
     → Test file excluded by config, 0 tests run
```

## Banned Test Patterns

The following are NOT tests and MUST NEVER appear:

```text
BANNED (these are placeholders, not tests):
  it.todo('should create a task')
  it.skip('should validate input', () => { ... })
  xit('should handle errors', () => { ... })
  test.todo('should return results')
  it('should work', () => {})          ← empty body
  it('should work', () => { pass() })  ← no assertion
```

Every test MUST have:
- A setup that creates inputs or conditions
- A call to the function/module being tested
- At least one assertion (`expect`, `assert`, `toEqual`,
  `toThrow`, etc.) that verifies behavior

## Verify Test Failure Explicitly

After writing tests and BEFORE writing implementation, run the
tests and confirm the output shows REAL FAILURES (not "skipped"
or "pending"). Log the failure count.

```text
CORRECT output after RED phase:
  "3 failed"                    ← real assertion failures
  "Expected false, received undefined"

WRONG output after RED phase:
  "3 skipped"                   ← not testing anything
  "3 todo"                      ← not testing anything
  "0 failed"                    ← tests are vacuous
```

If tests pass or skip before you write implementation code:
- The tests are placeholders (rewrite with assertions)
- The tests are wrong (not testing what they should)
- The implementation already exists (skip the task)

In all cases, investigate before proceeding.

## Integration Tests

When your task includes integration tests:

1. Check for existing integration test patterns:
   `Glob("tests/integration/**")` or `Glob("tests/e2e/**")`
2. Follow the project's existing pattern (structure, setup,
   teardown, naming)
3. If no integration test directory exists, create one
4. Integration tests follow the same RED→GREEN cycle
5. Use the INTEGRATION test command — NOT the default unit
   test command (which may exclude integration tests)

## Project Patterns

If the orchestrator's prompt includes PRESET_CONVENTIONS or
references to project-specific patterns (from CLAUDE.md or
the project constitution), follow those patterns. TDD still
applies — project patterns govern WHAT you build, TDD
governs HOW you build it.

## Summary Format

Return this summary when your task completes:

```text
## Task Result: <TASK_ID>

**TDD Evidence:**
- Tests written: N
- RED verified: N failed (real assertion errors)
- GREEN verified: N passed
- REFACTOR: ✅ tests stayed green / N/A

**Test commands used:**
- Unit/contract: <SINGLE_FILE_TEST command used>
- Integration: <SINGLE_FILE_INTEGRATION command used>

**Files created/modified:**
- path/to/file (created/modified)

**Errors:** None (or describe)
```

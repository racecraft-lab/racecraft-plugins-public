# Fixture 17 — Phase-executor error handling

Verifies that when a phase agent returns an error, the orchestrator
behaves per the documented error-handling protocol:

- Never retries blindly (no immediate re-dispatch of the same phase)
- Never escalates to `grill-me` (HITL is forbidden inside autopilot)
- Either re-dispatches with a corrective prompt (a different phase or
  a structurally different prompt to the same phase), OR defers the
  blocking issue to the end-of-run request and keeps independent work
  moving
- Never stops the run or asks a question mid-run

Both outcomes are acceptable; the structural assertions only catch
the bad behaviors (grill-me dispatch, forbidden inner-Agent spawn,
runaway dispatching, and in live runs a question to the user).

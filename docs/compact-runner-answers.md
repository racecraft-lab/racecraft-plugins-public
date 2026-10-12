# Compact runner answers

The runner envelope is the deep module boundary: autopilot root requests select
`answer_format: compact`, while phase-local artifact consumers retain detailed
answers. Compact answers retain status, next action, and decision data. The
default remains detailed for existing consumers.

The cap includes serialized stdout and duplicate stderr diagnostics. Ordinary
answers allow 16 KiB. Tasks binding handoffs allow that metadata budget plus six
times the existing 32 KiB text input bound, preserving even fully escaped text.
An oversized answer stops after dispatch, preserves the helper outcome, and
instructs reconciliation without repeating a mutation.

## Known limits

- Very large partition results can stop at the ordinary cap. This fails closed;
  it cannot bypass a gate. Phase-local reduction is required before continuing.
- The structural guard recognizes explicit read directives, including multiline
  instructions and `consult`. Arbitrary paraphrases are outside this syntactic
  check; no such directive remains in either rendered host's root guidance.
- The shared dispatcher wraps its existing return paths separately to preserve
  routing behavior. This is minor repetition of a single response policy call.
- Linux launcher tests cover both shipped host payloads. Native macOS isolation,
  live interactive question steps, and end-to-end token savings are not certified
  by these tests.
- The local Linux VM's full suite fails unchanged privacy and carry-forward
  tests: its generic account name collides with public operating-system text,
  and unmapped ancestor ownership is correctly rejected. These failures do not
  reach the compact-answer seam. Focused acceptance and parity tests pass.
- Ripwire reports new unittest methods as unused despite dynamic discovery, plus
  minor contract registration and generated guidance growth. No gating regression
  or acknowledgement is introduced. Its reported architecture edge from
  `gates/payloads.py` to `runtime.py` is also present on the base revision.

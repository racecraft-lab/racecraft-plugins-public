# Fixture 11 — Round 2 escape-hatch fan-out

Verifies the Round 2 escalation path: when a single-routed Round 1
returns an escape-hatch keyword ("no precedent", "insufficient
context", "outside my scope"), the orchestrator must fan out to the
remaining analysts in Round 2. This protects against single-perspective
routing on questions where that perspective lacked the answer.

Pairs with `parse-consensus-categories.sh` (Layer 4) which encodes the
escape-hatch keyword detection logic.

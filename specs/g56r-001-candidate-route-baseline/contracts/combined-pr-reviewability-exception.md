# Combined PR Reviewability Exception

Reviewability-Exception: infra

The operator explicitly requires one pull request containing both the complete
G56R-001 research slice and the durable SpecKit Pro repair for the autopilot
terminal-success-without-a-PR failure. The two scopes are causally coupled: the
completed spike exposed the missing packet/creation invariant, and the repair
must ship with the recovered PR evidence that proves it.

This exception permits the combined file count only. It does not waive focused
tests, the full default suite, generated Claude/Codex payload parity, packet
currentness validation, or live verification of the final PR URL and number.

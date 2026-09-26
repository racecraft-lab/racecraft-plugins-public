# Fixture 06 — Security tag → defense-in-depth full fan-out

Verifies the consensus protocol's hardcoded defense-in-depth rule: any
`[security]` tag dispatches all three analysts regardless of which
other categories are present. This is the safety net that prevents
single-analyst routing of a security decision.

A security keyword alone needs no tag: parse-consensus-categories widens
a narrowly tagged item that contains one (for example `session` or
`tokens`) to all three analysts by itself. The two routes differ only in
the agreement bar: a `[security]` tag always needs 3/3, while a
keyword-only item needs 3/3 only when an analyst returns
`security_relevant: true`.

# Fixture 04 — Synthesizer, keyword-only item, 2-of-3 majority applies

The item carries no `[security]` tag, but `tokens` is a security
keyword, so parse-consensus-categories widened it from `[domain]` to
all three analysts and returned `security_route: keyword`. Every
analyst returned `security_relevant: false`: the keyword was used in
another sense. The synthesizer must apply the ordinary rule, so the
2-of-3 majority (`per-request`) wins and no human review is flagged.

Fixture 05 is the sibling: the same item and inputs, except one analyst
returns `security_relevant: true`.

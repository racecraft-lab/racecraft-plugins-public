# The backend chain moves down only and skips hops on the same account

Status: accepted

The `evaluate` tool in typesafe-jev gains an ordered backend chain (`JEV_CHAIN`,
or `~/.config/racecraft-jev/chain`) of up to four hops, such as
`openrouter,typesafe,ollama-local,ollama`. Before this, one fallback took over
once and kept the session, so a session never alternated between two accounts.

We decided three things (owner, 2026-11-14).

1. **A session only moves down the chain, never back.** A hop that cannot serve
   its account or cannot be reached (401, 402, 403, 404, 429, 5xx, a refused
   connection) moves the session to the next hop for the rest of that session.
   A restart starts again at the top. One session's answers then come from one
   account per stretch, never interleaved, and the move is easy to read in the
   log.
2. **A hop that bills the same account as the one that failed is skipped.**
   `ollama-local` (the signed-in daemon) and `ollama` (cloud direct) share one
   Ollama account, so a credit, key or throttle failure on one would repeat on
   the other. Only an unreachable daemon moves on to cloud direct.
3. **A hop timeout moves only that call, not the session.** Each hop gets at
   most `JEV_HOP_TIMEOUT` (10 s) inside the one request deadline (45 s), so a
   hanging hop cannot spend the time every later hop needs. A timeout can come
   from one heavy request, and the timed-out request may still run and bill
   upstream, so it is not treated as the backend being down.

## Considered Options

- **Move back after a cool-off** (retry the first hop some minutes after a 429,
  5xx or timeout). It spends fewer last-resort credits after a brief outage,
  but one session's answers would come from changing models and accounts.
- **Start every call at hop 1.** Most calls would pay for the failed hops'
  latency.
- **A one-hop fallback with Ollama as a third provider.** Smaller, but it
  cannot hold the owner's order: OpenRouter credit, then TypeSafe credit, then
  Ollama only when both are spent.

## Consequences

A brief outage of every Jev hop leaves the rest of that session on the last
hop (Clef), spending its credits, until the MCP server restarts.

## Settled after the grill (owner, 2026-11-14)

- **A keyless hop always loads.** `ollama-local` needs no key, so the rule that
  drops a hop with no loadable key at start-up does not apply to it. A daemon
  that is down shows at call time as unreachable and moves the session to the
  next hop.
- **Every entry point reads the same chain.** `evaluate call --plugin-defaults`
  resolves the chain exactly as the server does, and `evaluate setup` writes
  `JEV_CHAIN` into a client's config instead of the old provider pair.

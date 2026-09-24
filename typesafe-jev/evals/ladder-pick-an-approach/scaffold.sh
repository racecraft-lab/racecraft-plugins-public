#!/bin/sh
set -eu
. "$(dirname "$0")/../lib/link-server.sh"
link_evaluate_server

cat > options.md <<'FIXTURE'
# Deduplicating webhook deliveries

Context: the provider retries a webhook on any non-2xx, and occasionally
delivers the same event twice even on success. Each event carries a stable
`event_id`. We process roughly 400 events a minute, across 6 replicas.

## Option A: in-memory LRU per replica
Keep the last 10,000 event ids in each process. No new infrastructure.
Does not survive a restart, and replicas do not share state.

## Option B: a unique index on event_id in the existing Postgres table
Insert first, let a duplicate violate the constraint, and treat the
violation as "already processed". One migration. Shares state across all
replicas and survives restarts. Adds one write per event on the hot path.

## Option C: a new Redis instance holding seen ids with a 24h TTL
Shared across replicas and fast. Adds a service to run, monitor and pay
for, and a new failure mode when Redis is unreachable.
FIXTURE

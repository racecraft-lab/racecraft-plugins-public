#!/bin/sh
set -eu
. "$(dirname "$0")/../lib/link-server.sh"
link_evaluate_server

cat > policy.md <<'FIXTURE'
The service must never write a customer's email address to any log, at any level, including debug.
FIXTURE

cat > change.md <<'FIXTURE'
Add a debug log line to the signup handler so we can trace failures:

    log.debug("signup failed for %s: %v", req.Email, err)

Gated behind the existing LOG_LEVEL=debug flag, which is off in production.
FIXTURE

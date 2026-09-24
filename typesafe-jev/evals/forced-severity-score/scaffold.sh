#!/bin/sh
set -eu
. "$(dirname "$0")/../lib/link-server.sh"
link_evaluate_server

cat > findings.json <<'FIXTURE'
{
  "findings": [
    {
      "id": "F1",
      "text": "A debug endpoint returns the full environment, including API keys, to any unauthenticated caller."
    },
    {
      "id": "F2",
      "text": "A log line records the number of retries, which is slightly misleading when a request is cancelled."
    },
    {
      "id": "F3",
      "text": "A helper function is duplicated in two packages."
    }
  ]
}
FIXTURE

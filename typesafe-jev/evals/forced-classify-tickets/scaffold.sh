#!/bin/sh
set -eu
. "$(dirname "$0")/../lib/link-server.sh"
link_evaluate_server

cat > tickets.json <<'FIXTURE'
{
  "tickets": [
    {
      "id": "A-1",
      "text": "SSO redirect returns a 500 right after the Okta callback."
    },
    {
      "id": "A-2",
      "text": "The invoice PDF shows last month's totals."
    },
    {
      "id": "A-3",
      "text": "Page is blank until I hard-refresh; console shows a router error."
    }
  ]
}
FIXTURE

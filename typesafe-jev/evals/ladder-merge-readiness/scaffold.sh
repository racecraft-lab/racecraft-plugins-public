#!/bin/sh
set -eu
. "$(dirname "$0")/../lib/link-server.sh"
link_evaluate_server

cat > pr.json <<'FIXTURE'
{
  "number": 118,
  "title": "close the fan-out absence and packaging-lock gaps",
  "files_changed": 23,
  "additions": 604,
  "deletions": 87,
  "tests_added": 9,
  "ci": { "tests": "pass", "lint": "pass", "typecheck": "pass" },
  "review_comments": [
    { "author": "reviewer-a", "body": "The HOME fix is right but the test still writes to a temp dir it does not clean up on failure." },
    { "author": "reviewer-b", "body": "Can we split this? Four unrelated fixes in one PR makes bisecting painful." }
  ]
}
FIXTURE

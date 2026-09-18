#!/bin/sh
set -eu
. "$(dirname "$0")/../lib/link-server.sh"
link_evaluate_server

cat > ci.log <<'FIXTURE'
> test suite
PASS  auth.test.ts (12 tests)
PASS  billing.test.ts (31 tests)
FAIL  upload.test.ts
  ● uploads a large file › completes within the timeout
    Timeout - Async callback was not invoked within the 5000 ms timeout.
    at Object.<anonymous> (upload.test.ts:88:3)
  ● uploads a large file › completes within the timeout
    (retry 1) Timeout - Async callback was not invoked within the 5000 ms timeout.
PASS  render.test.ts (8 tests)
Tests: 1 failed, 51 passed
FIXTURE

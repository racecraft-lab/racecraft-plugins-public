#!/bin/sh
set -eu
. "$(dirname "$0")/../lib/link-server.sh"
link_evaluate_server

cat > config.yaml <<'FIXTURE'
server:
  host: 0.0.0.0
  port: 8443
  tls: true
FIXTURE

#!/usr/bin/env bash
# test-speckit-pro-read-only-helpers.sh — Unit and parity coverage for XPLAT-005 helpers.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/test-speckit-pro-read-only-helpers.py" "$@"

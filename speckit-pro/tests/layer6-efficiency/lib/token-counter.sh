#!/usr/bin/env bash
# token-counter.sh — Parse token usage from claude -p output
#
# Usage: echo "$claude_output" | bash token-counter.sh
#
# Expects claude -p --output-format json output with usage metadata.
# Returns JSON with input_tokens, output_tokens, cache_read, cache_write.

set -euo pipefail

input=$(cat)

# claude -p --output-format json returns a JSON object with a "usage" field
if echo "$input" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
  python3 -c "
import sys, json

data = json.load(sys.stdin)

# Handle both direct usage and nested result formats
usage = data.get('usage', {})
if not usage and 'result' in data:
    usage = data['result'].get('usage', {})

print(json.dumps({
    'input_tokens': usage.get('input_tokens', 0),
    'output_tokens': usage.get('output_tokens', 0),
    'cache_read': usage.get('cache_read_input_tokens', 0),
    'cache_write': usage.get('cache_creation_input_tokens', 0)
}))
" <<< "$input"
else
  echo '{"input_tokens": 0, "output_tokens": 0, "cache_read": 0, "cache_write": 0}'
  echo "WARNING: Could not parse token usage from claude output" >&2
fi

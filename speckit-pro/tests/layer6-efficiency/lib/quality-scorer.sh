#!/usr/bin/env bash
# quality-scorer.sh — Score output quality against a baseline
#
# Usage: bash quality-scorer.sh <actual_output_file> <expected_output_file>
#
# Scoring criteria:
#   - Structural completeness: required sections present (0-1)
#   - Content accuracy: key phrases/patterns match baseline (0-1)
# Returns JSON with structural_score, content_score, overall.

set -euo pipefail

ACTUAL="$1"
EXPECTED="$2"

if [ ! -f "$ACTUAL" ] || [ ! -f "$EXPECTED" ]; then
  echo '{"structural_score": 0, "content_score": 0, "overall": 0, "error": "missing files"}'
  exit 1
fi

python3 -c "
import sys, json, re

with open('$ACTUAL') as f:
    actual = f.read()
with open('$EXPECTED') as f:
    expected = f.read()

# Extract expected section headers (## lines)
expected_sections = re.findall(r'^##\s+(.+)$', expected, re.MULTILINE)
actual_sections = re.findall(r'^##\s+(.+)$', actual, re.MULTILINE)

# Structural: what fraction of expected sections appear in actual
if expected_sections:
    found = sum(1 for s in expected_sections if any(s.lower() in a.lower() for a in actual_sections))
    structural = found / len(expected_sections)
else:
    structural = 1.0 if actual.strip() else 0.0

# Content: extract key phrases from expected (lines starting with - or *)
expected_phrases = re.findall(r'^[\-\*]\s+\*?\*?(.+?)\*?\*?\s*$', expected, re.MULTILINE)
if expected_phrases:
    matches = 0
    for phrase in expected_phrases:
        words = [w.lower() for w in re.findall(r'\w+', phrase) if len(w) > 3]
        if words:
            found_words = sum(1 for w in words if w in actual.lower())
            if found_words / len(words) >= 0.5:
                matches += 1
    content = matches / len(expected_phrases)
else:
    content = 1.0 if actual.strip() else 0.0

overall = (structural + content) / 2
print(json.dumps({
    'structural_score': round(structural, 2),
    'content_score': round(content, 2),
    'overall': round(overall, 2)
}))
"

# Marker Checkpoint: us1

| Field | Value |
|-------|-------|
| Marker | us1 |
| Review order | 1 |
| Source boundary | User Story 1 - Active Installed-Runtime Surface Cutover |
| Head SHA | 4041d16b |
| Status | Complete |

## Evidence

- Active installed-runtime cutover implemented in the first implementation slice.
- Focused guard coverage is declared through `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py`.
- Final verification includes the active runtime guard request and Layer 1 Claude/Codex hook structural checks.

## Review Note

This checkpoint is the first stack boundary. Review remediation is included in
the final PR#289 head.

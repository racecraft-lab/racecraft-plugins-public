# Marker Checkpoint: us3

| Field | Value |
|-------|-------|
| Marker | us3 |
| Review order | 3 |
| Source boundary | User Story 3 - Native UAT, Update, and Safe Repair |
| Head SHA | 53b0d319 |
| Status | Complete |

## Evidence

- Native UAT matrix, release-readiness packet, install-health repair, and
  bounded blocker evidence are included in this checkpoint.
- Local isolated Codex/macOS installed-cache UAT evidence is recorded in
  `.process/uat/codex-macos.md`.
- The release-readiness gate is expected to block current native UAT pending
  evidence while passing the explicit ready fixture.

## Review Note

This checkpoint is review-ready but not native-release-ready. Review remediation
is included in the final PR#291 head, and the six native operator rows remain
pending until separate platform evidence is filled.

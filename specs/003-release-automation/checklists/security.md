# Security Checklist: Release Automation

**Purpose**: Validate security requirements quality for the release automation workflow — token permissions, supply chain integrity, secret exposure prevention, and injection attack surface.
**Created**: 2026-04-01
**Feature**: [specs/003-release-automation/spec.md](../spec.md)
**Depth**: Standard | **Audience**: Reviewer (PR)

## GITHUB_TOKEN Permissions — Least Privilege

- [x] CHK001 - Are all required GITHUB_TOKEN permission scopes explicitly enumerated at the workflow level with least-privilege justification for each? [Completeness, Spec §FR-007, §SEC-002]
- [x] CHK002 - Is the `contents: write` permission scope justified with the specific operations it enables (release creation, tag creation, sync commit push)? [Clarity, Spec §FR-007]
- [x] CHK003 - Is the `pull-requests: write` permission scope justified with the specific operations it enables (Release PR creation and update by release-please)? [Clarity, Spec §FR-007]
- [x] CHK004 - Does the spec explicitly state that no other permission scopes beyond `contents: write` and `pull-requests: write` are required, ensuring least-privilege is documented as intentional? [Completeness, Spec §SEC-002]
- [x] CHK005 - Are requirements defined for what happens when permissions are over-provisioned (e.g., a maintainer adds `packages: write` unnecessarily) — is there guidance or a principle against scope creep? [Completeness, Spec §SEC-002 — SEC-002 states "No additional permission scopes are required or permitted for this workflow"]
- [x] CHK006 - Is the requirement to use GITHUB_TOKEN (not a PAT or GitHub App token) explicitly stated as a security requirement, not just an implementation preference? [Clarity, Spec §FR-007, §SEC-004]

## GITHUB_TOKEN — Infinite Loop Prevention as Security Control

- [x] CHK007 - Is the GITHUB_TOKEN's built-in property (commits do not trigger workflows) documented as a security control, not just a convenience feature? [Clarity, Spec §FR-007, §US5]
- [x] CHK008 - Are the security implications of switching from GITHUB_TOKEN to a PAT or App token explicitly documented (loss of loop prevention, potential for runaway resource consumption)? [Coverage, Spec Edge Cases — PAT/App token scenario]
- [x] CHK009 - Is the defense-in-depth strategy (GITHUB_TOKEN loop prevention + `chore:` prefix + `[skip ci]`) documented as layered security rather than redundant mechanisms? [Clarity, Spec §US5, §FR-005, §FR-007]

## Supply Chain Security — Action Version Pinning

- [x] CHK010 - Does FR-008 specify whether "specific version" means a full-length commit SHA, a major version tag (e.g., `v4`), or a minor version tag (e.g., `v4.1.0`)? [Clarity, Spec §FR-008 — updated to specify SHA preferred, major version tags acceptable for first-party actions]
- [x] CHK011 - Does the spec define the supply chain threat model that action pinning is intended to mitigate (tag mutation, compromised maintainer, upstream repository takeover)? [Completeness, Spec §FR-008 — updated to enumerate threat model]
- [x] CHK012 - Are requirements defined for how pinned action versions should be updated (e.g., Dependabot, manual review process, verification of upstream changelog)? [Completeness, Spec §FR-008 — updated to recommend Dependabot or manual changelog review]
- [x] CHK013 - Is the `actions/checkout` action also covered by the version pinning requirement in FR-008, or does it only apply to the release-please action? [Clarity, Spec §FR-008 — updated to explicitly name both actions]
- [x] CHK014 - Does the plan specify concrete version pins for both `googleapis/release-please-action` and `actions/checkout` (major version tag vs. SHA)? [Completeness, Plan §Security Design]

## Secret Exposure Prevention — Sync Step

- [x] CHK015 - Are requirements defined to prevent the sync step from echoing sensitive token values, git credentials, or authentication headers in workflow logs? [Completeness, Spec §SEC-003]
- [x] CHK016 - Does the spec address whether `actions/checkout` with `persist-credentials: true` stores credentials in a way that could be exposed by subsequent steps (e.g., `.git/config` containing token URLs)? [Completeness, Spec §SEC-004]
- [x] CHK017 - Are requirements defined for whether the sync step's git operations (commit, push) should mask or avoid logging the remote URL (which may embed the GITHUB_TOKEN)? [Completeness, Spec §SEC-003 — GitHub Actions automatically masks GITHUB_TOKEN in logs; standard git operations do not print credential headers]
- [x] CHK018 - Does the spec define requirements for log verbosity control in the sync step to prevent accidental secret leakage through debug output or `set -x` usage? [Completeness, Spec §SEC-003 — sync script uses `set -euo pipefail` without `set -x`]

## Script Injection Attack Surface — Commit Messages

- [x] CHK019 - Does the spec address the script injection risk from `github.event.head_commit.message` being used in workflow expressions or inline scripts? [Completeness, Spec §SEC-001]
- [x] CHK020 - Are requirements defined to ensure the workflow YAML does not interpolate commit message content, PR titles, or branch names directly into `run:` shell commands? [Completeness, Spec §SEC-001]
- [x] CHK021 - Does the spec require that all user-controlled inputs (commit messages, PR titles, branch names) be passed through environment variables rather than direct expression interpolation to prevent injection? [Completeness, Spec §SEC-001]
- [x] CHK022 - Are the sync step's inline git commands (commit message, author configuration) documented as using hardcoded strings rather than dynamic user-controlled values? [Clarity, Spec §FR-005, §SEC-001]

## Workflow Trigger Security

- [x] CHK023 - Is the push-to-main-only trigger (FR-001) documented as a security boundary that prevents workflow execution from arbitrary branches or forks? [Clarity, Spec §FR-001 — updated to document branch scope and fork security model]
- [x] CHK024 - Is the explicit exclusion of `workflow_dispatch` (FR-001) justified from a security perspective (preventing unauthorized manual triggers)? [Clarity, Spec §FR-001]
- [x] CHK025 - Are requirements defined for whether the workflow should run on pushes from forks (relevant if the repo accepts external contributions)? [Completeness, Spec §FR-001 — updated to clarify fork pushes do not trigger upstream workflows]

## Concurrency and Race Condition Security

- [x] CHK026 - Does the concurrency group requirement (FR-015) address the security risk of concurrent release runs creating conflicting tags or duplicate releases? [Coverage, Spec §FR-015]
- [x] CHK027 - Is `cancel-in-progress: false` justified from a security perspective (ensuring a release in progress is not interrupted by a potentially malicious subsequent push)? [Clarity, Spec §FR-015]

## Dependency and Environment Security

- [x] CHK028 - Is the runner environment (`ubuntu-latest`) documented with acknowledgment that it is a moving target (new versions may change available tools or security posture)? [Completeness, Spec Assumptions — updated to acknowledge moving target and tool availability]
- [x] CHK029 - Are requirements defined for validating the integrity of the `jq` binary available on the runner (pre-installed by GitHub, not fetched at runtime)? [Completeness, Spec Assumptions — updated to note reliance on GitHub's runner image provenance controls; no additional integrity validation needed]
- [x] CHK030 - Does the spec address whether the sync script should validate the structure/integrity of `marketplace.json` and `plugin.json` before reading them (defense against malicious content injected via a compromised commit)? [Completeness — sync script already validates JSON structure of both files (lines 40-53 for marketplace.json, lines 102-106 for plugin.json) and validates semver format (lines 119-122); path traversal is also rejected (lines 88-92)]

## Authentication and Credential Flow

- [x] CHK031 - Is the credential flow documented end-to-end: GITHUB_TOKEN provisioned by Actions runtime -> passed to `actions/checkout` -> persisted in git config -> used by sync step for push? [Completeness, Spec §FR-007, §SEC-004, Clarifications]
- [x] CHK032 - Are requirements defined for credential cleanup after the sync step completes (or is runner ephemerality sufficient)? [Completeness, Spec §SEC-003 — runner ephemerality is documented as the cleanup mechanism]
- [x] CHK033 - Does the spec address whether the GITHUB_TOKEN's credential persistence scope extends beyond the checkout step to all subsequent steps in the same job? [Clarity, Spec §SEC-004]

## Notes

- Focus areas: GITHUB_TOKEN scope (least privilege), action version pinning (supply chain), secret exposure (sync step), script injection (commit messages), workflow trigger boundaries
- Depth: Standard
- Audience: Reviewer (PR review gate)
- User-specified must-haves incorporated: GITHUB_TOKEN `contents: write` scope correctness (CHK001-CHK006), action SHA/version pinning (CHK010-CHK014), no secret exposure in sync logs (CHK015-CHK018), no injection via crafted commit messages (CHK019-CHK022)
- All 15 [Gap] items remediated by adding SEC-001 through SEC-004 to spec.md, updating FR-001, FR-008, and Assumptions, and adding Security Design section to plan.md

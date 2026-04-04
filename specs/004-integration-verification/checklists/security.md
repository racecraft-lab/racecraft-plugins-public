# Security Checklist: Integration & Verification

**Purpose**: Validate the quality, completeness, and clarity of security-relevant requirements in the SPEC-004 Integration & Verification specification — focused on branch protection, GITHUB_TOKEN bypass semantics, merge enforcement, and secrets handling.
**Created**: 2026-04-03
**Feature**: [spec.md](../spec.md)

## Requirement Completeness

- [ ] CHK001 - Are the exact branch protection fields required by the legacy API payload fully enumerated — including `required_status_checks`, `enforce_admins`, `required_pull_request_reviews`, and `restrictions` — so an implementer can construct a complete, correct `gh api` call without inferring omitted fields? [Completeness, Spec §FR-005]
- [ ] CHK002 - Does the spec define what the `required_pull_request_reviews` and `restrictions` fields should be set to in the branch protection payload, or does it leave those fields unspecified? Omitting them from the PUT body silently removes any existing review requirements or push restrictions. [Completeness, Gap]
- [ ] CHK003 - Are requirements specified for what happens if the legacy branch protection API call fails mid-run — for example, if the maintainer's token lacks admin scope — including who is responsible and what corrective action to take? [Completeness, Gap]
- [ ] CHK004 - Does the spec define the minimum required `GITHUB_TOKEN` permissions for the SPEC-003 marketplace sync workflow that performs the direct push to `main`? The plan references "admin-equivalent permissions" but does not state whether the workflow's `permissions:` block is constrained or relies on the repo default. [Completeness, Gap]
- [ ] CHK005 - Are requirements for secret or credential handling explicitly excluded, or is it documented that no new secrets are introduced by this feature? The spec discusses `GITHUB_TOKEN` but does not state whether the feature introduces any new repository secrets, environment variables, or PATs. [Completeness, Spec §Assumptions]

## Requirement Clarity

- [ ] CHK006 - Is the term "admin-equivalent permissions" for `GITHUB_TOKEN` on personal repositories defined with a reference to the specific GitHub documentation source so the claim is verifiable and not assumed? [Clarity, Spec §FR-004]
- [ ] CHK007 - Is the bypass mechanism described in FR-004 clearly distinguished from the rulesets bypass actors feature — including an explicit statement of what "enforce_admins: false" does and does not do — so there is no ambiguity about what actions it permits? [Clarity, Spec §FR-004]
- [ ] CHK008 - Is "non-exempt actors" in FR-003 defined with sufficient precision to determine whether a third-party GitHub App, a collaborator with write access, or a PAT-authenticated CLI call is exempt or not? [Clarity, Spec §FR-003, Supplemental §FR-003]
- [ ] CHK009 - Is the scope of "direct push to main" in FR-003 and FR-004 unambiguous — does it cover force-push (`--force`), branch deletion, and tag creation in addition to regular pushes, or only regular pushes? [Clarity, Gap]
- [ ] CHK010 - Is the phrase "no embedded credentials or PATs are permitted in committed scripts" in FR-005 supplemental adequately operationalized — does it state how the `gh api` command should authenticate (e.g., via `GH_TOKEN` environment variable sourced at runtime) rather than being a prohibition only? [Clarity, Spec §FR-005 Supplemental]

## Requirement Consistency

- [ ] CHK011 - Does the spec consistently apply the "enforce_admins: false" requirement across FR-004, the Key Entities definition of Bypass Mechanism, and the Assumptions section — or are there any wording discrepancies that could lead an implementer to interpret the setting differently in each location? [Consistency, Spec §FR-004, §Key Entities, §Assumptions]
- [ ] CHK012 - Do FR-003 (prevent direct pushes for non-exempt actors) and FR-004 (allow GITHUB_TOKEN direct pushes via enforce_admins: false) produce a consistent, non-contradictory protection posture when read together — or does the spec need an explicit reconciliation statement? [Consistency, Spec §FR-003, §FR-004]
- [ ] CHK013 - Is Copilot code review consistently described as advisory-only and non-blocking in all locations where it is mentioned — FR-006, Key Entities, Clarifications, and Supplemental §FR-006 — with no location implying it could enforce security policy? [Consistency, Spec §FR-006, §Key Entities, §Clarifications]

## Acceptance Criteria Quality

- [ ] CHK014 - Is SC-003 ("The GitHub Actions bot can push a chore: commit to main without a PR — automated sync commits succeed") measurable in terms of the branch protection configuration state, or does it rely solely on runtime observation that could be affected by factors outside this spec's scope? [Acceptance Criteria, Spec §SC-003]
- [ ] CHK015 - Is SC-001 ("merge is blocked 100% of the time") qualified with a clear definition of what "blocked" means at the API level — specifically whether the GitHub API returns a 405 or 422 status when a PR with a failing required check is merged via the API, not just the UI? [Acceptance Criteria, Spec §SC-001, Supplemental §SC-001]
- [ ] CHK016 - Does SC-001's manual test definition (Supplemental §SC-001) specify what tool or method the maintainer uses to confirm branch protection required checks are registered correctly — for example, `gh api GET /repos/{owner}/{repo}/branches/main/protection` — so the verification step is reproducible? [Acceptance Criteria, Spec §SC-001 Supplemental]

## Scenario Coverage

- [ ] CHK017 - Are requirements defined for the scenario where a maintainer accidentally runs the `gh api` branch protection setup command a second time with an incomplete payload, silently overwriting and disabling previously configured protections? The supplemental note on idempotency addresses re-runs but not partial re-runs with missing fields. [Coverage, Spec §FR-005 Supplemental]
- [ ] CHK018 - Is there a requirement or documented decision addressing what happens if a future maintainer upgrades the repository to a GitHub Organization — specifically, that the enforce_admins: false bypass mechanism stops working and must be replaced with an explicit bypass actor? [Coverage, Spec §FR-004, §Assumptions]
- [ ] CHK019 - Are requirements defined for protecting the branch protection configuration itself from being removed or weakened — for example, a rogue PR that deletes the setup script or a manual UI change that disables required checks? [Coverage, Gap]
- [ ] CHK020 - Is the security posture of release-please PRs addressed from a branch protection standpoint — specifically, is it documented whether release-please PRs are reviewed by a human before merge, given that CI checks do not run on them (per Supplemental §Edge Case Resolutions)? [Coverage, Spec §Edge Case Resolutions]

## Edge Case Coverage

- [ ] CHK021 - Does the spec address the edge case where `enforce_admins: false` is accidentally set to `true` by a UI change after the setup script runs — what would break, how would it be detected, and how would it be recovered? [Edge Case, Gap]
- [ ] CHK022 - Is there a requirement or documented expectation for what happens when the sentinel job `validate-plugins` is the only required status check on a release-please PR, and CI does not run on it — does the branch protection silently allow the merge, and is this acceptable from a security/quality standpoint? [Edge Case, Spec §FR-001, §Edge Case Resolutions]
- [ ] CHK023 - Does the spec address the scenario where the `GITHUB_TOKEN` default permission level is changed at the repository or organization level (e.g., from Read+Write to Read-only) — which would break the marketplace sync push and potentially the bypass mechanism? [Edge Case, Gap]

## Non-Functional Requirements (Security)

- [ ] CHK024 - Is there a requirement that the branch protection setup command (FR-005) be stored in a location that is itself version-controlled and access-controlled — for example, in the verification checklist only, or also in a script file — so the configuration can be audited and reproduced? [Non-Functional, Spec §FR-005 Supplemental]
- [ ] CHK025 - Does the spec state the minimum GitHub token scope required for a maintainer to run the `gh api` branch protection setup command — specifically that a `repo` scope PAT or admin-level GITHUB_TOKEN is required — so an implementer does not attempt it with insufficient credentials? [Non-Functional, Spec §FR-005]
- [ ] CHK026 - Is there a requirement specifying that the verification checklist itself (FR-007) must be reviewed for accuracy before being used as a security configuration record — given that it serves as the Infrastructure-as-Code record for branch protection per FR-005 Supplemental? [Non-Functional, Spec §FR-005 Supplemental, §FR-007]

## Dependencies and Assumptions

- [ ] CHK027 - Is the platform dependency in FR-004 (that GITHUB_TOKEN has admin-equivalent permissions on personal repos) acknowledged with a documented risk-acceptance decision and an explicit trigger condition for re-evaluation — for example, "re-evaluate if the repo is transferred to an organization or if GitHub changes personal-repo token semantics"? [Assumption, Spec §FR-004 Supplemental]
- [ ] CHK028 - Is the dependency on the Copilot Pro/Pro+ subscription explicitly listed as a prerequisite with a documented impact statement if the subscription lapses — specifically that Copilot review silently stops without any CI failure or alert? [Dependency, Spec §FR-006, §FR-006 Supplemental]
- [ ] CHK029 - Is the assumption that no PATs are stored as repository secrets verified and documented — or is it merely implied by "GITHUB_TOKEN is used"? If the SPEC-003 sync workflow already stores a PAT, this assumption would be violated and FR-005's no-embedded-credentials requirement would need clarification. [Assumption, Gap]

## Ambiguities and Conflicts

- [ ] CHK030 - Does the spec clarify whether "squash-only merge" enforcement (FR-002) is enforced at the branch protection level, the repository settings level, or both — and which takes precedence if they conflict? The supplemental note for FR-002 states these are repository-level settings, not branch protection payload fields, which creates ambiguity about where enforcement actually lives. [Ambiguity, Spec §FR-002, §Supplemental FR-002]
- [ ] CHK031 - Is there an explicit statement clarifying that the `enforce_admins: false` setting does not weaken required PR review requirements or other branch protection rules — only that it exempts admin-context direct pushes — so readers do not interpret it as a general security downgrade? [Ambiguity, Spec §FR-004]
- [ ] CHK032 - Is the relationship between the legacy branch protection API configuration (FR-005) and the Copilot ruleset (FR-006) documented to make clear they are two independent GitHub configuration mechanisms, so an implementer does not attempt to configure Copilot review via the branch protection API call? [Ambiguity, Spec §FR-005, §FR-006]

## Notes

- Check items off as completed: `[x]`
- Mark gaps that require spec updates with `[Gap]` inline
- Items flagged `[Gap]` indicate missing requirements that must be added to spec.md or plan.md before implementation
- Security-keyword items (auth, token, credential, permission) are flagged for extra scrutiny per the consensus protocol

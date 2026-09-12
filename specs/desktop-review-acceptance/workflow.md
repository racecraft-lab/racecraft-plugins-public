# Desktop Artifact Review Acceptance Workflow

**Purpose:** disposable issue #571 acceptance fixture. The planning files below
are seeded test preconditions; they are not a claim that the full SpecKit
phases ran.

## Workflow Overview

| Phase | Command | Status | Notes |
| ------- | ------- | ------- | ------- |
| Specify | `/speckit-specify` | ✅ Complete | Seeded fixture scope in `spec.md`; precondition only |
| Clarify | `/speckit-clarify` | ✅ Complete | Evidence boundary stated; precondition only |
| Plan | `/speckit-plan` | ✅ Complete | Durable workflow handoff chosen; precondition only |
| Checklist | `/speckit-checklist` | ✅ Complete | Generation, preview, approval, and UAT separated |
| Tasks | `/speckit-tasks` | ✅ Complete | `tasks.md` covers four pages and planned gap |
| Analyze | `/speckit-analyze` | ✅ Complete | Brownfield resolver/artifact-review map recorded |
| Confidence Gate | `artifact-review` | ✅ Complete | Initial fixture may proceed to preview delivery |
| Implement | `/speckit-implement` | ⏳ Pending | Not started; this fixture has no production implementation |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Basic Information

| Field | Value |
| ------- | ------- |
| **Spec ID** | ART-571 |
| **Feature** | Desktop Artifact Review Acceptance |
| **Branch** | `codex/issue-571-desktop-acceptance` |
| **Stage** | plan |
| **Draft PR** | [#577](https://github.com/racecraft-lab/racecraft-plugins-public/pull/577) |
| **Purpose** | Disposable evidence fixture — DO NOT MERGE |

## Generation Boundary

Generation checks cover actual template-derived bytes, marker completeness,
sample-banner removal, source fingerprints, and the planned architecture-viewer
gap. They do not prove browser rendering, human approval, or manual UAT.

## Artifact Review Handoff

```json
{
  "schema_version": "1.0",
  "feature_dir": "specs/desktop-review-acceptance",
  "input_hashes": {
    "specs/desktop-review-acceptance/spec.md": "b0369e0b512ae12e4aad0a8c62de7f7de0bfe9845268be6595dfa8b0d427db70",
    "specs/desktop-review-acceptance/plan.md": "a54deacb21f818cafc70356351c1223a8e9cdeb89fa609fc6cc398d43a80dad6",
    "specs/desktop-review-acceptance/tasks.md": "8bd2ff1cc135f4576822cf8e7a7128b4587fcc71528d4bc4782e8cf15f4d8de0"
  },
  "manifest_sha256": "af9a4944ff96ab0dcaf99909f5298edd6c8ea25c627ce97029084c17bb83d06a",
  "template_hashes": {
    "implementation-plan": "781bd0ea88a97bd5d0b38d4791b96bf04479042f544994488d5a7b7444c088b9",
    "spec-explainer": "b8a4c87b550aeae38ff3dc645367676439b88292107e821e188a5553b053f555",
    "code-approaches": "28631395c17a39b03060704aef3cf0462a7e0212fb2fa139219af93290b05e03",
    "module-map": "9cb043012178506be09a0e5b987df67507c34e2ca12f6ea198bfdab3a1c528e5",
    "architecture-viewer": null
  },
  "generation_error": null,
  "pages": [
    {
      "id": "implementation-plan",
      "generation": "generated",
      "path": "specs/desktop-review-acceptance/artifacts/implementation-plan.html",
      "sha256": "83991a628c386343f7881f002145e8c9458c10f0c193c885a45b9f179ae913c0",
      "expected_title": "Implementation Plan — Desktop Artifact Review Acceptance",
      "expected_content": "Four rendered pages share one durable handoff",
      "preview": {"status": "pending", "blocker": "Not observed yet", "observation": null}
    },
    {
      "id": "spec-explainer",
      "generation": "generated",
      "path": "specs/desktop-review-acceptance/artifacts/spec-explainer.html",
      "sha256": "cc2b4092fab312f2d65cfb6e1a02f550ffd1800882454402d3944a80a6d7557b",
      "expected_title": "Spec Explainer — Desktop Artifact Review Acceptance",
      "expected_content": "A disposable evidence fixture that separates generated gallery pages",
      "preview": {"status": "pending", "blocker": "Not observed yet", "observation": null}
    },
    {
      "id": "code-approaches",
      "generation": "generated",
      "path": "specs/desktop-review-acceptance/artifacts/code-approaches.html",
      "sha256": "dd09107edfb98f6cbc7af32b405189aa0e436af91c0ad5dbba94d50e5649e5bc",
      "expected_title": "Code Approaches — Desktop Artifact Review Acceptance",
      "expected_content": "Two ways to carry artifact evidence",
      "preview": {"status": "pending", "blocker": "Not observed yet", "observation": null}
    },
    {
      "id": "module-map",
      "generation": "generated",
      "path": "specs/desktop-review-acceptance/artifacts/module-map.html",
      "sha256": "e5e761e930c072a7cf82cab2e67c55adeee9dd00cd68b69fca461e87a5821949",
      "expected_title": "Module Map — Desktop Artifact Review Acceptance",
      "expected_content": "The existing resolver and artifact-review module meet at one workflow handoff",
      "preview": {"status": "pending", "blocker": "Not observed yet", "observation": null}
    },
    {
      "id": "architecture-viewer",
      "generation": "gap",
      "reason": "The manifest marks architecture-viewer as planned, but no shipped template exists in the active gallery."
    }
  ]
}
```

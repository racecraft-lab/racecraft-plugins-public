# Data Model: Static docs framework and IA spike

## Framework Candidate

Represents one documentation stack under evaluation.

**Fields**:
- `name`: Docusaurus/MDX, VitePress, Astro/Starlight, or repo-native fallback.
- `support_class`: built-in, official, community, third-party paid, or unsupported per capability.
- `github_pages_support`: whether the stack can publish to GitHub Pages from this repository.
- `interactivity_model`: MDX/React, Vue in Markdown, Astro/MDX components, or Markdown-only.
- `search_model`: official hosted, built-in local, community local, external, or unsupported.
- `versioning_model`: first-party, custom/manual, third-party/community, or unsupported.
- `link_checking_model`: build-time, external tool, manual, or unsupported.
- `maintenance_load`: low, medium, or high.
- `decision`: accept, reject, defer, or fallback.
- `decision_reason`: concise acceptance or rejection rationale.

**Validation rules**:
- Every required candidate must be represented.
- Every candidate must record GitHub Pages support and interactivity support.
- Rejected or deferred candidates must include a decision reason.

## Evaluation Criterion

Represents one comparison dimension reviewers need to validate.

**Fields**:
- `criterion`: static hosting, GitHub Pages, interactivity, search, versioning, accessibility, link checking, docs-as-code, maintenance load, commands, or support class.
- `weight`: hard blocker, high, medium, or tie-breaker.
- `candidate_result`: pass, tradeoff, blocked, unsupported, or not applicable.
- `evidence`: local file path or official URL plus retrieval date when applicable.
- `notes`: short source-backed explanation.

**Validation rules**:
- Hard blockers cannot be unresolved.
- Current framework/platform claims must include retrieval date.
- Support class must distinguish official/built-in from community or third-party support.

## IA Route

Represents one route-level docs-site IA record for DOC-002.

**Fields**:
- `route_path`
- `route_label`
- `diataxis_mode`
- `secondary_modes`
- `target_audience`
- `route_purpose`
- `source_evidence`
- `success_criterion`
- `shell_owner_doc`
- `full_content_owner_doc`

**Validation rules**:
- The 11 required PRD route labels must be covered.
- `diataxis_mode` must be Tutorial, How-to, Reference, or Explanation.
- `shell_owner_doc` must be DOC-002 for every top-level route.
- `full_content_owner_doc` must name the downstream DOC spec or specs that own full content.
- No route may contain placeholder evidence or placeholder success criteria.

## Source Evidence

Represents a cited local or official source used by the spike.

**Fields**:
- `source_type`: local artifact or official URL.
- `source_ref`: path or URL.
- `retrieval_date`: required for current platform/framework claims.
- `evidence_note`: short explanation of what the source supports.

**Validation rules**:
- Official framework/platform claims require `retrieval_date: 2026-06-12`.
- Local source evidence must reference existing source inputs or existing repo facts.

## Command Recommendation

Represents the report-only package/build/test command handoff to DOC-002.

**Fields**:
- `package_manager`: recommended package manager.
- `setup_command`: future scaffold/install command.
- `build_command`: minimum future build validation command.
- `preview_command`: future local preview command.
- `test_command`: minimum future validation command.
- `scope_note`: reminder that DOC-001 does not execute or create tooling.

**Validation rules**:
- Commands are report-only in DOC-001.
- Commands must map to the selected stack.
- No package file or lockfile may be created in DOC-001.

## Spike Report

Represents the final research decision record.

**Fields**:
- `recommendation`
- `decision_date`
- `candidate_matrix`
- `source_evidence`
- `ia_skeleton`
- `command_handoff`
- `doc_002_consumption`
- `scope_boundary`
- `verification_notes`

**Validation rules**:
- Must be written to `docs/ai/research/interactive-documentation-framework-spike.md`.
- Must include acceptance/rejection reasons for every candidate.
- Must state how DOC-002 consumes the recommendation.
- Must record that DOC-001 did not create implementation scaffolding.

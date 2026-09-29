Priority: major

## Summary

Stack-manager qualification accepts only a gh-stack SKILL.md matching one pinned digest under three trusted roots, and the documentation mentions neither. A newer upstream copy fails qualification and runs silently fall back to explicit-gh. The recorded support_status mislabels untrusted or operator-chosen cases, and the re-verified retry path added in the open stack drops the attempted mutation boundary.

## Evidence

- **pr-emission-and-stack-1-002** (major): qualify_tools accepts only a gh-stack SKILL.md whose bytes hash to one pinned digest and that sits under three trusted install roots. stack-manager.md documents neither the pin nor the roots, and AGENTS.md tells operators to install the current upstream skill. A newer upstream copy therefore fails qualification, and every run silently falls back to explicit-gh. Installed copies of different ages were seen to hash differently from the pin. Tests overwrite the pin, so nothing checks its provenance.
  - `speckit-pro/speckit_pro_runner/helpers/stack_manager.py:17`, `speckit-pro/speckit_pro_runner/helpers/stack_manager.py:118-129`, `speckit-pro/skills/speckit-autopilot/references/stack-manager.md:8-10`, `speckit-pro/skills/speckit-autopilot/references/stack-manager.md:39-44`, `AGENTS.md:178-182`
- **pr-emission-and-stack-1-010** (minor): The reverified_retry path in the stack ending at PR 852 rebuilds the decision with select_manager, so mutation_boundary is reset to planned and the attempted boundary and recovery record are dropped. The updated stack-manager.md still says never to erase the attempted boundary. Only the caller re-persisting an attempted boundary keeps it, and the helper does not say so. Introduced by open PR #852.
  - `speckit-pro/speckit_pro_runner/helpers/stack_manager.py:206-242`, `speckit-pro/skills/speckit-autopilot/references/stack-manager.md:73-80`
- **pr-emission-and-stack-1-011** (minor): support_status records 'missing' when a skill exists but sits outside the trusted roots or fails the digest, and 'ambiguous' when the operator chose explicit-gh without any inspection. stack-manager.md says never to relabel unavailable evidence. The schema also allows values no code emits: support_status private_preview_unavailable, phase restack, and operation sync and restack.
  - `speckit-pro/speckit_pro_runner/helpers/stack_manager.py:122-129`, `speckit-pro/speckit_pro_runner/helpers/stack_manager.py:222`, `speckit-pro/skills/speckit-autopilot/contracts/stack-manager-decision.schema.json:24-27`, `speckit-pro/skills/speckit-autopilot/contracts/stack-manager-decision.schema.json:341-350`

## Proposed fix

- pr-emission-and-stack-1-002: Document the pin, the trusted roots and the refresh procedure in stack-manager.md, and add a check that ties the pinned digest to a committed reference copy or a stated upstream tag so a stale pin is caught.
- pr-emission-and-stack-1-010: Carry the prior attempted mutation_boundary and recovery evidence into the re-verified decision, or state in stack-manager.md that the parent must re-persist the boundary before the retry.
- pr-emission-and-stack-1-011: Add distinct statuses for untrusted and mismatched skills and for an operator preference, and trim schema enum values the runner never emits, or mark them as reserved.

## Acceptance

- [ ] stack-manager.md documents the pin, the trusted roots and the refresh procedure; a check ties the pin to a committed reference or upstream tag.
- [ ] Distinct statuses for untrusted, mismatched and operator-preferred cases; schema values no code emits are removed or marked reserved.
- [ ] A regression test that fails before the fix: a reverified retry keeps the attempted mutation_boundary and recovery record.
- [ ] Runner trust metadata and dist/ are regenerated.

## Related

- Overlaps files changed by the open stop-policy stack: #850. Land after that stack merges.
- pr-emission-and-stack-1-010 was introduced by open PR #852.

Found by the 2026-09 coherence audit.

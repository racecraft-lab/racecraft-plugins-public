Priority: minor

## Summary

Qualified Docker verification requires a Linux/arm64 daemon, hard-coded in five places, and the guidance never says so. On an amd64 host it fails with a ValueError. The verification records module also acts as a primitives library for the Docker modules, which import a private name from it and break the resulting cycle with local imports.

## Evidence

- **brokers-and-verification-004** (minor): verification_records.py is both the copy-only host executor and the home of primitives (sha, digest, tree_digest, evidence_directories, workflow_argv, _read_bounded_regular) that every Docker module needs. The Docker modules import a private name from it while it lazily imports the Docker workflow back, and the Docker qualification module uses four function-local imports to break the cycle.
  - `speckit-pro/speckit_pro_runner/verification_records.py:309`, `speckit-pro/speckit_pro_runner/verification_records.py:38-60`, `speckit-pro/speckit_pro_runner/verification_docker_qualification.py:14`, `speckit-pro/speckit_pro_runner/verification_docker_qualification.py:222-241`
- **brokers-and-verification-011** (minor): The Linux/arm64 requirement is hard-coded in five places, and the Docker verification guidance in execution-efficiency.md never says qualified verification only works against an arm64 daemon. On an amd64 host or CI runner the run fails with ValueError('Docker daemon must report Linux/arm64').
  - `speckit-pro/speckit_pro_runner/verification_docker.py:64`, `speckit-pro/speckit_pro_runner/verification_docker.py:126`, `speckit-pro/speckit_pro_runner/verification_docker_image.py:53`, `speckit-pro/speckit_pro_runner/verification_docker_image.py:121`, `speckit-pro/speckit_pro_runner/verification_docker_runtime.py:178`, `speckit-pro/skills/speckit-autopilot/references/execution-efficiency.md:526-560`

## Proposed fix

- brokers-and-verification-004: Move the shared snapshot and evidence primitives into a small leaf module that both the host executor and the Docker modules import, and make _read_bounded_regular public there.
- brokers-and-verification-011: Define one PLATFORM constant used by all three modules and add the arm64-only limit to the Docker section of the guidance.

## Acceptance

- [ ] One PLATFORM constant; execution-efficiency.md states the arm64-only limit.
- [ ] Shared snapshot and evidence primitives live in a leaf module with public names; no function-local imports remain.
- [ ] Runner trust metadata and dist/ are regenerated; both suites pass.

## Related

- Overlaps files changed by the open stop-policy stack: #837, #838, #846, #847, #848, #850. Land after that stack merges.

Found by the 2026-09 coherence audit.

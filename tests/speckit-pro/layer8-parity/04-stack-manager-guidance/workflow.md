# PRSG-014 Stack Manager Guidance Fixture

## Stack Manager Guidance Contract

| Supported Path | Fallback Path | Blocked Path | Recovery Path | Shared Runner Helper | Shared Contract |
|----------------|---------------|--------------|---------------|---------------|-----------------|
| `gh-stack` only after deterministic `gh stack` version, read-only proof, packet, and topology checks pass | explicit `gh pr create/edit --base --head --title --body-file` before any `gh stack` mutation when support is missing, unsupported, ambiguous, unsafe, or topology-incompatible | partial or unknown `gh stack` mutation blocks with `fallback_allowed=false`; no manager mixing | reload decision and recovery evidence, revalidate topology, PR identity, base/head refs, head SHA, and packet identity before same-manager resume | `detect-stack-manager-plan` is registered `out_of_scope`; do not invoke it in installed workflows | `speckit-pro/skills/speckit-autopilot/contracts/stack-manager-decision.schema.json` |

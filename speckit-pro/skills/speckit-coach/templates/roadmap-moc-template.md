---
# Roadmap-level Map of Content (MOC). Frontmatter join-key contract (PRSG-002).
# Authored by maintainers (not scaffold-substituted). Single shared, runtime-agnostic
# copy. The instance filename convention for the roadmap-MOC is defined by PRSG-004
# (out of scope here).
#
# up: MUST be a quoted relative markdown link — "[text](relative/path.md)", NEVER a
#     [[wikilink]]. The () target is load-bearing: the stale-index lint parses the
#     relative []() target and resolves it. A top-level roadmap map may have no parent;
#     when it does, point up: at it with a relative []() link.
up: ""                       # relative []() link to the parent map, if any; NEVER a [[wikilink]]
related: []                  # list of relative []() links; carried, unenforced in v1
status: ""                   # carried, unenforced in v1
rank:                        # carried, unenforced in v1
spec_id: ""                  # the roadmap identity — namespace-matches the containing directory
structureVersion: 1          # keep in sync with the lint scripts' hardcoded literal
---

# Roadmap — Map of Content

Navigation map for this roadmap. Add relative `[]()` links to each spec's
`SPEC-MOC.md` in the body below so every spec is reachable from the roadmap map.
The generated down-link index and the PRD-derived home note are owned by later
specs (PRSG-003 / PRSG-004); this template ships only the contract-carrying shape.

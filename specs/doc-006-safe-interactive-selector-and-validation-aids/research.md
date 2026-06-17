# Research: Safe Interactive Selector and Validation Aids

## Decision: Enhance the existing choose-your-path route

**Decision**: Keep DOC-006 on `docs-site/src/content/docs/choose-your-path.*`.

**Rationale**: The design concept records Q1 as "Enhance Choose Your Path". This keeps path selection where users already choose between Claude Code, Codex, and install scope.

**Rejected alternatives**: A new route would add navigation and maintenance surface. Embedding across multiple install pages would duplicate command metadata and fallback content.

## Decision: Build-time read-only manifest metadata

**Decision**: Read manifest-backed values from the six checked-in JSON/manifest files during docs generation or focused validation. Keep curated command templates, prerequisites, success signals, and handoff labels in a small docs metadata helper.

**Rationale**: Q3 chose "Build-time read only". The spec clarifies that source-derived means manifest-backed values are read from checked-in repository files, while command guidance may be curated as docs metadata.

**Rejected alternatives**: A committed generated metadata file would introduce source/generated drift. A reusable generator script would expand DOC-006 into tooling work. Parsing install Markdown would make prose pages a brittle machine data source.

## Decision: Static-first enhancement with native controls

**Decision**: Render complete semantic static content first, then add small progressive enhancement only for selector/checker filtering.

**Rationale**: Q4 chose "Static-first enhancement". Static tables/lists keep every command path, checker value, diagram node, and checklist item reviewable without JavaScript.

**Rejected alternatives**: A rich app widget would increase JavaScript and testing scope. Static tables only would miss the selector/checker experience promised by DOC-006.

## Decision: Repository consistency checker only

**Decision**: Compare source and dist marketplace/plugin values for stable fields such as plugin name, version, marketplace source/path, and counterpart presence. Treat intentional platform packaging differences as informational context.

**Rationale**: Q6 chose "Repo consistency only". The checker is a maintainer/evaluator trust aid, not a user-local diagnostic.

**Rejected alternatives**: A pasted JSON checker would require input handling and could imply local diagnosis. A maintainer-only hidden view would reduce installer value.

## Decision: Lightweight troubleshooting handoffs

**Decision**: Mismatch, unavailable, and caution states should link to existing install, stale-update, contribute/release, or DOC-008-owned troubleshooting content without building a symptom matrix.

**Rationale**: Q5 chose "Lightweight handoff only". This gives users a safe next step while keeping full troubleshooting ownership with DOC-008.

**Rejected alternatives**: A full troubleshooting scaffold would overlap DOC-008. Deferring handoffs entirely would leave checker caution states without a safe route.

## Decision: Accessible static payload diagram

**Decision**: Represent source tree, Claude distribution, Codex distribution, marketplace entries, and Codex cache as text-backed nodes with list/table equivalents.

**Rationale**: Q7 chose "Accessible static diagram". Screen readers and static review need the same information as the visual flow.

**Rejected alternatives**: Mermaid-only output is weaker as a fallback. Interactive graph behavior is too much for this safe-aids slice.

## Decision: Docs validation plus focused fixture

**Decision**: Require docs validation, link validation, and a focused metadata/rendering fixture or test.

**Rationale**: Q8 chose "Docs plus focused fixture". Standard docs checks are necessary but do not protect against source-derived metadata drift or command-surface leakage.

**Rejected alternatives**: Docs checks only would miss manifest/rendering drift. Full repo suite is disproportionate unless implementation touches plugin source, shared scripts, manifests, or payload-generation behavior.

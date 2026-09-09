# PRD authoring protocol

This platform-neutral protocol turns validated user decisions into a lean PRD,
a technical roadmap, and a roadmap-MOC. The active SKILL.md owns the Claude or
Codex interaction mechanism.

## Input and update modes

- **Create:** accept an idea, brief, transcript, or interactive description;
  derive a kebab-case slug and create the three output paths.
- **Update:** when the user supplies an existing PRD, revise that file in place
  after confirming its scope. Preserve stable feature, acceptance-criteria, and
  SPEC identifiers for unchanged work. Issued Feature, acceptance-criteria, and
  SPEC identifiers are permanently reserved. Never renumber or reuse a retired
  identifier; allocate every new identifier above all historical use. If its
  roadmap or roadmap-MOC exists, update it to keep the crosswalk and navigation
  consistent. Never backfill a missing roadmap-MOC onto a legacy roadmap unless
  the user asks.

Read applicable project instructions, `.specify/memory/constitution.md`, existing
roadmaps, prior decisions, and targeted code. Ground each recommendation in real
evidence; skip questions the input already answers.

## Interview

Ask one question at a time, resolving one decision axis per turn. Put the
grounded choice first, mark it `(Recommended)`, and offer 1-2 mutually exclusive
alternatives with concise tradeoffs. Walk the highest impact times uncertainty
branch first:

| Branch | PRD result |
| --- | --- |
| Problem, users, and why now | Problem and audience |
| Outcomes and success | Goals |
| Explicit scope cuts | Non-goals |
| Feature boundaries | Features and SPEC crosswalk |
| Observable proof | Acceptance criteria |
| Dependencies and release order | Migration and roadmap graph |
| Governance, technology, and at-risk qualities | Constraints |
| Deferred decisions | Open Questions |

Feature boundaries are the key decomposition decision. Each feature must be one
independently valuable, reviewable, end-to-end vertical slice with its own
acceptance criteria. Use SPIDR seams (Spike, Path, Interface, Data, Rule) and the
INVEST bar to split oversized work. A layer-only unit such as all models or all
UI is not independently valuable; re-slice it through the layers it needs.

Prefer natural convergence. Also stop when the user ends the interview. Around
25-30 questions, recommend wrapping up and place remaining unknowns in Open
Questions. Do not invent a decision.

## Author or update the PRD

Use the shared PRD template. Keep WHAT and WHY in the PRD; put implementation
detail in roadmap scopes. Fill only sections that reduce ambiguity:

1. Problem and audience.
2. Goals and Non-goals.
3. Features with `AC-N.*` acceptance criteria and a `SPEC-NNN` mapping.
4. Migration or sequence when applicable.
5. Constraints.
6. Open Questions.
7. A SPEC Catalog Crosswalk that is 1:1 with Features.

Drop an optional appendix unless a sketch materially resolves ambiguity. Write
new files to `docs/prd-<slug>.md`; preserve the confirmed path in update mode.

## Author or update the technical roadmap

Use the shared technical-roadmap template. Map every PRD Feature and its
acceptance-criteria group to exactly one `SPEC-NNN` entry. Each entry includes:

- scope detailed enough to seed `/speckit-specify`;
- dependencies and enables, priority, and pending status;
- the existing Reviewability Budget and Projected reviewable LOC fields;
- key files or surfaces and `Source PRD: docs/prd-<slug>.md`.

Confirm the dependency graph and execution order with the user before finalizing.
Preserve unchanged IDs during updates and confirm any feature addition, removal,
or reorder that would change the mapping.

For each entry, derive user-story or acceptance-criteria groups, touched surfaces,
functional requirements, and new-versus-modify status. Run runner operation
`estimate-spec-size` and populate the existing Projected reviewable LOC field.
A research-only Spike is timeboxed. Treat `warn` as an advisory opportunity to
split; it never blocks the roadmap. If the operation is unavailable, non-zero,
empty, or unparseable, leave the estimate absent, note it, and continue.

## Author or update the roadmap-MOC

For a newly authored PRD and roadmap, create
`docs/ai/specs/<slug>-roadmap-MOC.md` from the shared roadmap-MOC template. For
an update, revise an existing home note but honor the legacy no-backfill rule.

- Derive the editable curated epics zone from roadmap phase or tier groupings
  without asking new questions. If the catalog is flat, use one `Specs` epic and
  add an advisory to consider grouping.
- Set `up:` to a relative Markdown link to `<slug>-technical-roadmap.md`.
- Preserve exactly the template's empty `GENERATED:INDEX` sentinel pair; do not
  add PRS or BACKLINKS sentinels or author index rows.
- Run runner operation `generate-spec-index-write` in apply mode with the
  consumer project root supplied explicitly. The generator, not this skill,
  writes normalized SPEC-MOC links and statuses inside the INDEX zone.
- Add a reciprocal relative link from the technical roadmap to the home note.
- More than about ten epics produces a one-line advisory, never a block.

Do not change per-spec MOC `up:` fields or the spec-MOC template.

## Verify and hand off

Before reporting success, prove that PRD Features, acceptance-criteria groups,
the PRD crosswalk, and roadmap entries agree on count, names, and IDs. Confirm
every roadmap scope can seed `/speckit-specify`, the home note contains its
curated zone plus generated INDEX, and reciprocal links resolve.

Report every created or updated path. Recommend status inspection followed by
`speckit-scaffold-spec <SPEC-ID>` for the first ready roadmap entry.

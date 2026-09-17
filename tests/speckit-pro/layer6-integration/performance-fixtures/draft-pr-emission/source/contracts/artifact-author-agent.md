# Contract: The `artifact-author` Subagent

**Owner surface**: `speckit-pro/agents/artifact-author.md` (new),
`speckit-pro/codex-agents/artifact-author.toml` (new),
`speckit-pro/speckit_pro_runner/helpers/install.py` (bundle registration).

Satisfies FR-001, FR-002, FR-003, FR-004. Supports SC-002 and SC-003.

---

## 1. Role

Read the feature's planning record, decide which draft-stage gallery templates
apply, fill their marked regions, and write the finished pages into
`specs/<branch>/artifacts/`.

Fail-open. A failure of any kind leaves the pages that succeeded on disk, marks
the rest as gaps, and never blocks pull-request creation.

---

## 2. Inputs

| Input | Path |
| --- | --- |
| specification | `specs/<branch>/spec.md` |
| plan | `specs/<branch>/plan.md` |
| tasks | `specs/<branch>/tasks.md` |
| design concept | `docs/ai/specs/.process/<SPEC-ID>-design-concept.md` |
| gallery manifest | `speckit-pro/artifact-gallery/manifest.json` |
| templates | `speckit-pro/artifact-gallery/templates/<entry-id>.html` |

Templates and the manifest are **read-only**. Writing into
`speckit-pro/artifact-gallery/` is a defect: this feature authors into the
shipped templates, it does not change them.

---

## 3. Selection

Filter the manifest to entries whose `stage` is `draft-pr`, then apply each
entry's `trigger`:

| Entry | `trigger` | Fires when |
| --- | --- | --- |
| `implementation-plan` | `{"always": true}` | every run |
| `spec-explainer` | `{"always": true}` | every run |
| `code-approaches` | `{"any_of": ["competing_approaches"]}` | the design concept carries "Alternatives offered" blocks |
| `module-map` | `{"any_of": ["brownfield_change"]}` | the spec's primary surface names existing code the change edits |

The signal names are two members of the manifest's closed five-signal
vocabulary. The other three route final-PR artifacts and are out of scope here.

---

## 4. Fill

Each template carries paired HTML-comment markers and a slot inventory comment
naming each slot's source document:

```html
<!-- FILL:tldr:START -->
...replace this region...
<!-- FILL:tldr:END -->
```

Rules:

- Write only between a `START` and its matching `END`. Never move, delete, or
  duplicate a marker.
- Fill every slot the template's inventory declares. A page with an unfilled slot
  is a gap, not a partial success.
- Leave no placeholder text behind.
- Content comes from the planning record, never invented.

Output path: `specs/<branch>/artifacts/<entry-id>.html`, one page per selected
entry.

---

## 5. Failure semantics

| Failure | Response |
| --- | --- |
| one page fails | write the others; report that page as a gap with a reason |
| every page fails | write nothing; report a whole-set gap |
| a template is unreadable | that page is a gap; the others proceed |
| the design concept is missing | `competing_approaches` does not fire; the two always-on pages still generate |

The agent never raises to its caller and never returns a blocking status. Its
result is a list of per-entry outcomes, each `generated` or `gap`, which the
terminal step turns into index rows, a stop-report note, and the workflow row's
gap note.

---

## 6. Definition shape

### 6.1 Claude — `speckit-pro/agents/artifact-author.md`

YAML frontmatter, then a Markdown body. Mirrors `uat-runbook-author`, the closest
shipped analogue: a fail-open content-authoring role dispatched at pull-request
time that edits files in place and must never block PR creation.

| Field | Value | Why |
| --- | --- | --- |
| `name` | `artifact-author` | matches the filename stem |
| `description` | trigger-quality prose naming when to dispatch and the fail-open promise | this is what the model matches on |
| `model` | `sonnet` | same as the analogue |
| `color` | a distinct value | cosmetic |
| `disallowedTools` | `Skill, Agent, TeamCreate, SendMessage` | same deny-list as the analogue: an authoring role dispatches nothing |
| `maxTurns` | `30` | same as the analogue |
| `effort` | `max` | same as the analogue |

`model` must be one of `opus`, `sonnet`, `haiku`, `inherit`, and `name` must
match `^[a-zA-Z0-9][a-zA-Z0-9-]{2,49}$`.

### 6.2 Codex — `speckit-pro/codex-agents/artifact-author.toml`

Flat TOML, no frontmatter fence, prompt body inside `developer_instructions`.
Required keys: `name`, `description`, `model`, `model_reasoning_effort`,
`sandbox_mode`, `developer_instructions`.

| Field | Value |
| --- | --- |
| `name` | `artifact-author`, matching the filename stem exactly |
| `model` | `gpt-5.5` |
| `model_reasoning_effort` | `xhigh` |
| `sandbox_mode` | `workspace-write` — the agent writes files |

The Claude-only fields `tools`, `disallowedTools`, `permissionMode`, `color`,
`maxTurns`, `background`, and `effort` are forbidden in the TOML and are swept
for by the Codex agent validator. Codex expresses the equivalent constraint
through `sandbox_mode`.

**Identical instructions across platforms** (FR-001): the two bodies say the same
thing about selection, filling, output paths, and failure. Only the runtime
primitives differ. No test compares their prose, so this is the author's
obligation.

---

## 7. Registration

| Platform | Requirement |
| --- | --- |
| Claude | none — agents are discovered by directory convention |
| Codex | `"artifact-author.toml"` must be added to `REQUIRED_CODEX_AGENT_NAMES` in `speckit-pro/speckit_pro_runner/helpers/install.py` |

The Codex frozenset is closed in both directions: the bundle loader fails with
`incomplete_agent_bundle` on a missing file **or an unexpected one**. Shipping
the TOML without this edit makes every Codex install refuse the bundle.

---

## 8. Governed-corpus boundary

`artifact-author` ships **outside** the twelve-role Layer 6 corpus. The corpus is
a hand-committed JSON document keyed by explicit role bindings, not a directory
scan, so a thirteenth file under a new name touches no digest in its chain. A
thirteenth registered role is explicitly refused.

Corpus membership is a tracked deferral to ART-009, which must open the corpus
for its own rename work. **This feature must not edit any of the twelve governed
agent definitions**, including `uat-runbook-author`, which is inside the corpus.
Copying its frontmatter shape is safe; editing its file is not.

---

## 9. Test obligations

| Obligation | Where |
| --- | --- |
| Both new definitions pass the generic payload frontmatter sweep | Layer 1, existing `validate-payload-conformance.py`, no edit needed |
| The Codex bundle loads with the new agent present | Layer 4, `tests/speckit-pro/unit/` coverage of `install.py` |
| Claude/Codex agent existence parity holds | Layer 1, existing `validate-codex-parity.py` |
| The Layer 6 corpus still reports exactly twelve roles | Layer 4, existing `test-role-corpus-governance.py`, unchanged |

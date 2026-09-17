# Native-agent bootstrap reconciliation

Audit date: 2026-09-15

## Status and boundary

This note reconciles the eight legacy Layer 2 rows grouped under the five
`native-agent-availability-bootstrap` requirements. It does not add catalog
cases, change coverage counts, or record a native pass. The eight rows remain
unqualified host-local adapter checks, and the paired native-agent availability
case remains pending.

The key distinction is that legacy `should_trigger: false` is local to the
measured target. It does not prove that no sibling should be selected. For the
shared Codex-agent-install prompt, Codex must reject `speckit-install` and
`speckit-upgrade` while selecting their `install` sibling. Claude must reject
its two measured targets and select no skill because the Claude plugin has no
agent-installer skill.

## Exact source reconciliation

Every future adapter check must stage the measured target and the complete
host sibling catalog with descriptions copied exactly from source frontmatter.
Every selection criterion below has `allowed_extra: []`.

| Requirement | Host and measured target | Exact source provenance | Exact prompt | Required global selection |
|---|---|---|---|---|
| `trigger-unresolved-320e4ad27e58b004c93c1bc7` | Claude `speckit-install`; source `should_trigger: false` | [`evals/speckit-install-trigger.json`](../../layer2-trigger/evals/speckit-install-trigger.json) — `l2-1b43ca2d753dec02b20c5e17`, position 7 | `install the bundled SpecKit Pro Codex subagents into ~/.codex/agents` | `[]` |
| `trigger-unresolved-320e4ad27e58b004c93c1bc7` | Claude `speckit-upgrade`; source `should_trigger: false` | [`evals/speckit-upgrade-trigger.json`](../../layer2-trigger/evals/speckit-upgrade-trigger.json) — `l2-e76897ec42591baaf72a123b`, position 7 | `install the bundled SpecKit Pro Codex subagents into ~/.codex/agents` | `[]` |
| `trigger-unresolved-320e4ad27e58b004c93c1bc7` | Codex `speckit-install`; source `should_trigger: false` | [`codex-evals/speckit-install-trigger.json`](../../layer2-trigger/codex-evals/speckit-install-trigger.json) — `l2-1b79461d58e7889e96bae039`, position 7 | `install the bundled SpecKit Pro Codex subagents into ~/.codex/agents` | `["install"]` sibling |
| `trigger-unresolved-320e4ad27e58b004c93c1bc7` | Codex `speckit-upgrade`; source `should_trigger: false` | [`codex-evals/speckit-upgrade-trigger.json`](../../layer2-trigger/codex-evals/speckit-upgrade-trigger.json) — `l2-16c455c0a4f2da6c3070aaee`, position 7 | `install the bundled SpecKit Pro Codex subagents into ~/.codex/agents` | `["install"]` sibling |
| `trigger-unresolved-76bb97e51930577fdba31890` | Codex `install`; source `should_trigger: true` | [`codex-evals/install-trigger.json`](../../layer2-trigger/codex-evals/install-trigger.json) — `l2-b17609d6e21200d9d5f902e9`, position 1 | `Please use the install skill for its documented purpose in this repository.` | `["install"]` target |
| `trigger-unresolved-8dbf3e9ae65d8cbaa3464fbc` | Codex `install`; source `should_trigger: true` | [`codex-evals/install-trigger.json`](../../layer2-trigger/codex-evals/install-trigger.json) — `l2-e6d7dd4396cbae9b4152e502`, position 2 | `install the bundled SpecKit Pro Codex subagents into my user-scope Codex config and tell me if I need to restart` | `["install"]` target |
| `trigger-unresolved-8ee949e37342f6ca4e5896b9` | Codex `install`; source `should_trigger: true` | [`codex-evals/install-trigger.json`](../../layer2-trigger/codex-evals/install-trigger.json) — `l2-a22017765ee84d8405ead810`, position 3 | `refresh the SpecKit custom agents in ~/.codex/agents because autopilot says the subagents are missing` | `["install"]` target |
| `trigger-unresolved-d113bff02054c64fe2e33485` | Codex `install`; source `should_trigger: true` | [`codex-evals/install-trigger.json`](../../layer2-trigger/codex-evals/install-trigger.json) — `l2-be010e07dcad628021134fd7`, position 4 | `copy the plugin's Codex TOML subagents into ~/.codex/agents and verify what got installed` | `["install"]` target |

The explicit Codex prompt stays exactly as authored. It must not be replaced by
a cross-host `{{skill}}` prompt or a fictional “host-native installer” label.
The source [`install` description](../../../../speckit-pro/codex-skills/install/SKILL.md)
specifically installs or refreshes bundled Codex TOML agents, verifies them,
and reports the restart requirement. The Codex
[`speckit-install`](../../../../speckit-pro/codex-skills/speckit-install/SKILL.md) and
[`speckit-upgrade`](../../../../speckit-pro/codex-skills/speckit-upgrade/SKILL.md)
descriptions explicitly exclude this work and route it to `$install`. Their
Claude counterparts describe SpecKit CLI/project installation and upgrade, not
plugin-agent installation.

## Exact host catalogs and selection checks

The Claude catalog is the exact frontmatter-derived set `grill-me`,
`speckit-archive-cleanup`, `speckit-autopilot`, `speckit-coach`,
`speckit-install`, `speckit-prd`, `speckit-resolve-pr`,
`speckit-scaffold-spec`, `speckit-status`, `speckit-upgrade`, and
`ubiquitous-language`, plus the measurement-only `no-speckit-skill`. The two
Claude vectors pass only with no completed skill activation. Any target,
sibling, unknown, failed, or multiple activation is non-passing.

The Codex catalog is the same named product-skill set plus the Codex-only
`install` skill and the measurement-only `no-speckit-skill`. All six Codex
vectors pass only with one qualified exact-body `install` activation. Missing,
failed, unknown, target-instead-of-sibling, or multiple activation is
non-passing. The raw source descriptions and evidence remain retained; the
adapter must not rewrite descriptions to manufacture parity.

## Smallest faithful replacement

### 1. Host-local Layer 2 adapter matrix

Keep one parameterized adapter check containing the exact eight vectors above.
This preserves the two Claude target-local negatives, the two Codex sibling
routes, and the four Codex target positives without inserting unequal behavior
into the paired trigger catalog. A green adapter matrix is selection evidence
only; it is not proof that agents were installed or invokable.

### 2. Pending paired availability and invocation case

The smallest shared behavior is:

> The host's packaged required native-agent roster is available through its
> documented runtime surface, and the common `codebase-analyst` role completes
> one invocation.

The paired case has no skill selection: expected activations are `[]` on both
hosts. Claude uses the enabled plugin's `agents/*.md` roster and invokes
`Agent(subagent_type="speckit-pro:codebase-analyst")`. Codex uses a verified
preinstalled `.codex/agents/*.toml` roster and invokes the native
`codebase-analyst` role through `spawn_agent`. The adapter may normalize the
successful native tool names to `subagent`, but must retain the original trace
and exact role identity.

Parity is limited to roster availability and successful invocation of that
common role. It does not compare roster counts, Markdown with TOML, model or
reasoning settings, source bytes, or installation mechanisms. This paired
case does not replace the Codex-only installer requirements.

The current Claude non-trigger adapter copies the full plugin, including its
agent definitions. The current Codex non-trigger adapter stages skills but does
not materialize `.codex/agents/*.toml`. Before the paired case is executable,
the Codex adapter needs trusted pre-launch agent materialization, exact roster
validation and fingerprinting, and retained native invocation evidence. It
must not install agents during the subject session and then claim immediate
availability, because changed custom agents require a Codex restart.

### 3. Codex-only deterministic installation matrix

Preserve these mechanics outside the paired availability case:

- initial isolated user-scope install: exact rendered roster, verified writes,
  and `restart_required: true`;
- missing or stale refresh: repair required files, preserve unrelated agents,
  verify the result, and require restart;
- explicit TOML copy and verification: exact filenames, rendered bytes and
  SHA-256 identities, allowed model rewrites, no-clobber publication, and
  fail-closed rollback;
- verified no-op reinstall: `restart_required: false`.

Use an isolated fake home or disposable project destination. These are Codex
mechanics, not a basis for creating a Claude install skill.

## Qualification status

The eight legacy rows remain accounted for but unqualified. The host-local
adapter matrix, paired availability/invocation case, and Codex installer matrix
must each be implemented and pass their own evidence requirements before any
coverage migration or count change. Existing deterministic installer tests are
supporting evidence only and do not constitute native availability coverage.

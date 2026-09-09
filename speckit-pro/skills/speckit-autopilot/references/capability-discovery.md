# Capability Discovery Directive

Shared source directive:
`speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`

Use this directive whenever research or context gathering informs an answer,
artifact edit, consensus recommendation, or gate-remediation decision.

Pair it with [`grounding.md`](./grounding.md): discovery decides *which*
capability to use; grounding requires that every asserted fact actually came
from an invoked capability result. Open discovery is only safe when grounded.

## Universal Scope

This directive binds every component of the plugin, not only research agents:
all subagents, the orchestrator (the main-session executor), and the
user-invocable skills. Each proactively discovers and uses the capabilities its
runtime actually exposes — within the role boundary defined below.

The available set is unknown ahead of time and varies per user. Do not assume a
fixed set of installed tools or skills; discover what is present before
selecting, and never hardcode a particular tool or skill as the default.

## Capability Categories

Capability categories are a taxonomy, not an ordered fallback chain. Identify
the task need first, then choose among installed matches by fit and evidence
quality.

Required capability categories:

- codebase context
- spec context
- library documentation
- web or domain research
- source extraction
- installed skills/plugins
- repo-local helpers

## Discovery Step

Before selecting, enumerate the capabilities your runtime actually exposes right
now — installed tools, MCP capabilities, and installed skills alike. Read the
real, current inventory; do not work from a remembered or assumed list, and
select capabilities by their exact runtime identifier rather than a guessed name.
A component that cannot enumerate (its runtime exposes only a fixed set) selects
directly from what it has.

Agents acting on trusted input do not pin a plugin-owned availability allowlist.
The two Claude agents that read reviewer-derived text, `sweep-classifier` and
`sweep-analyst`, instead pin exactly the six snapshot broker tools. Codex does
not install those roles and uses its separate permission-scoped launcher. This
keeps attacker-writable reviewer text behind the closed broker surface while
trusted-input agents enumerate only the capabilities their runtime actually
exposes. User-invocable skills may still declare
platform-specific authorization metadata, such as Claude Code `allowed-tools`,
so the invocation can call the core primitives it needs. That metadata is not
an installed-tool inventory or a vendor/MCP availability allowlist; it is
applied before discovery, and components enumerate only the runtime surface
they actually receive.

A read-only subagent enumerates and selects like any other component, but only
among read/research capabilities: its role boundary (below) is enforced by
denying the built-in mutation primitives, not by shrinking what it can see.

## Selection Rule

1. Identify the needed capability category.
2. Select the best installed capability for that need using task fit,
   source authority/directness, freshness needs, expected evidence quality,
   and minimal necessary inventory disclosure.
3. Select any tool only when discovery picks it as the best available capability.
4. Do not encode a fixed tool order or fixed capability fallback chain.

## Capability Boundaries by Role

Proactive discovery never overrides a component's role. A platform cannot
categorically tell a "read" capability from a "write" one for an arbitrary
installed tool, so the boundary is enforced two ways: the built-in mutation
primitives (`Write`, `Edit`, `MultiEdit`, `NotebookEdit`) are denied at the
platform layer (Claude `disallowedTools`, Codex `sandbox_mode`), and this role
rule governs everything the platform cannot classify.

- A component declared **read-only** (research and context agents) must never
  invoke a capability that writes, mutates, installs, pushes, or otherwise
  changes state. It sees the full installed surface and selects freely among
  read/research capabilities — including any the operator installed that this
  plugin has never heard of — but anything that changes state is off-limits by
  role, regardless of availability.
- A component declared **mutating** (the implementation and artifact executors,
  the orchestrator) may use capabilities appropriate to its role, scoped to the
  work it is authorized to perform.
- A **mechanical** component (it returns an exit code or verbatim aggregation of
  already-grounded input) acquires nothing new; it is exempt from discovery and
  from grounding.

A read-only component that finds it needs a write to make progress stops and
reports that, rather than acquiring write capability.

## Fallback Rule

If no installed capability is available, reachable, or usable for the needed
category, continue with local files, native platform context, or repo-local
helpers when they can support the work.

When fallback evidence is used because no installed capability covers the need,
include this disclosure:

```text
No installed <capability> was available/usable; used <local/native/repo-local fallback>; confidence is <medium|low> because <reason>.
```

Fallback confidence must be `medium` or `low`; do not report fallback evidence
as high confidence.

## Evidence Output

Discovery-informed answers must include this compact evidence note:

```text
Capability path: <need> -> <selected capability/source>; Evidence: <citations or local file refs>; Confidence: <high|medium|low> (<brief reason>)
```

Use citations when the selected source supports citations. Use local file
references when the evidence comes from repository files or local artifacts.

## Inventory Disclosure

Normal answers must report only the selected capability path and any material fallback gap.

Full installed-capability inventories are allowed only when directly requested,
needed for troubleshooting, or required as PR evidence.

## Metadata Policy

Exact IDs may remain when they are schema-required metadata rather than active preferred behavior.

Metadata examples:

- Codex dependency values in generated or runtime metadata.
- Claude frontmatter `disallowedTools` built-in IDs (role denials name
  built-in tools only, never a vendor-qualified MCP tool).
- Generated manifest or path-rewrite metadata.
- Historical, archive, changelog, or provenance references.

Behavior surfaces name no default preferred tool. Behavior surfaces include
agent body text, Codex TOML `developer_instructions`, and shared reference
prose.

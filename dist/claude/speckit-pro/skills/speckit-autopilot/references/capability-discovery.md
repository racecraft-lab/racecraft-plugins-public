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

The orchestrator and the user-invocable skills run with the full session surface
and enumerate it directly. A read-only subagent does not enumerate beyond its
granted set; it works within its role boundary (below) and consumes capability
results the orchestrator gathered and passed to it.

## Selection Rule

1. Identify the needed capability category.
2. Select the best installed capability for that need using task fit,
   source authority/directness, freshness needs, expected evidence quality,
   and minimal necessary inventory disclosure.
3. Use formerly named tools only when discovery selects them as the best available capability.
4. Do not encode a fixed tool order or fixed capability fallback chain.

## Capability Boundaries by Role

Proactive discovery never overrides a component's role. A platform cannot
categorically tell a "read" capability from a "write" one for an arbitrary
installed tool, so the boundary is enforced by which capabilities a component is
granted, not by inspecting each tool at call time.

- A component declared **read-only** (research and context agents) must never
  acquire or invoke a capability that writes, mutates, installs, pushes, or
  otherwise changes state. It is granted only read/research capabilities, and it
  gains breadth from results the orchestrator already gathered — not by reaching
  for new write-capable capabilities itself.
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
- Claude frontmatter `tools:` allowlist IDs.
- Generated manifest or path-rewrite metadata.
- Historical, archive, changelog, or provenance references.

Behavior surfaces must not describe formerly named optional tools as default
preferred capabilities. Behavior surfaces include agent body text, Codex TOML
`developer_instructions`, and shared reference prose.

# Capability Discovery Directive

Shared source directive:
`speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`

Use this directive whenever research or context gathering informs an answer,
artifact edit, consensus recommendation, or gate-remediation decision.

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

## Selection Rule

1. Identify the needed capability category.
2. Select the best installed capability for that need using task fit,
   source authority/directness, freshness needs, expected evidence quality,
   and minimal necessary inventory disclosure.
3. Use formerly named tools only when discovery selects them as the best available capability.
4. Do not encode a fixed tool order or fixed capability fallback chain.

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

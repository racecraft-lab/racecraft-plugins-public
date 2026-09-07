# Presets & Extensions Guide

Presets customize how installed Spec Kit workflows generate artifacts;
extensions add capabilities. The active installation owns their exact commands,
resolution behavior, manifests, hooks, and configuration schema.

## Inspect before advising

1. Confirm the target project and active host. Preserve unrelated work.
2. Before advising on installed preset or extension behavior, read the active
   `specify` version/help and host-integration evidence, then inspect the
   installed manifest, command registration, and current project configuration.
   Follow observed manifest or command paths; do not assume one schema or host.
3. Distinguish observed state from a catalog description. If a command,
   manifest, or schema cannot be read, disclose the missing evidence instead of
   guessing a path, flag, event, priority rule, or fallback.
4. Use the Coach's capability-discovery and grounding contracts for any external
   lookup. Do not substitute an unverified network catalog for installed state.

## The curated set

Before listing or recommending the SpecKit Pro curated set, read the complete
current roster from
[`scripts/curated-set.json`](../../../scripts/curated-set.json). Install and
upgrade skills compare that file with the target project's installed presets and
extensions, then ask the operator which missing entries to install. Do not copy
the roster into this guide or infer that an entry outside it should be removed.

## Explain or discover

- Explain a preset from its installed `preset.yml` and the templates or commands
  that the active resolver reports it owns.
- Explain an extension from its observed installed manifest, registered
  commands, and active configuration. Derive supported hook events and fields
  from that evidence, not from a generic example.
  Separate installed presence, host command registration, and enabled hook
  wiring. An installed id or description does not prove a callable command or
  automatic hook. Report empty command or hook declarations as empty; if the
  registration or wiring evidence is unavailable, say it is unverified.
- For catalog discovery, use the catalog stack and search capability exposed by
  the installed CLI. Clearly label information that is available only from an
  external current source.
- For Autopilot behavior, read the installed `speckit-autopilot` skill as a
  reference only. Do not invoke it or duplicate its extension-routing rules.
- Before answering about user-named or observed extensions, identify the scope
  of the list and explicitly state that it is non-exhaustive; do not imply it
  is the complete catalog.

## Change state only with approval

For an install, removal, enable/disable, priority, hook, or configuration change:

1. Show the exact target, proposed operation, scope, and files or external state
   expected to change.
2. Obtain the user's confirmation before executing the mutation.
3. Use only syntax observed in the active installed CLI or command definition.
4. Stop on an unavailable capability, non-zero result, unexpected target, or
   ambiguous state. Do not retry, force, or reconstruct configuration by guess.
5. Re-read the affected manifest, registry, resolver result, or configuration and
   report the observed outcome plus any manual follow-up.

Route plugin installation and upgrade recovery to the maintained install or
upgrade skill for the active host. Route archive cleanup to
`speckit-archive-cleanup`. Preserve project-owned customizations; never edit core
templates as a shortcut for a preset or extension change.

# Campaign templates

The committed `*.draft.json` files are stable planning templates, not frozen
experiment manifests. They retain the reviewed campaign inputs but deliberately
omit volatile observer, catalog and fixture identities (ADR 0025).

Bind a template to a new, untracked evidence manifest before checking it:

```text
python3 tests/speckit-pro/layer2-trigger/compare-trigger-evals.py rebind --manifest tests/speckit-pro/layer2-trigger/campaign-drafts/issue-573-pilot.draft.json --out <new-manifest.json>
python3 tests/speckit-pro/layer2-trigger/compare-trigger-evals.py validate --manifest <new-manifest.json> --inventory tests/speckit-pro/layer2-trigger/case-inventory.json
```

Use the full template the same way. `--out` must not exist; binding cannot
overwrite the template or retained evidence. `rebind` reads `--manifest` only
as a regular file of at most 1 MiB, with no symlink anywhere in its path, so pass
a real path (on macOS, `/private/tmp` rather than `/tmp`). Validation rejects
stale bindings with exit code 2. The CI campaign suite exercises both templates and stale
bindings without provider access.

Before a native launch, select the evidence output directory and obtain the
existing separate budget approval against the final concrete manifest. Binding
does not authorize a launch, verify the pinned CLI/model availability, or
establish qualification. Never rebind retained campaign evidence to disguise
changed inputs; the in-place rebind mode remains for concrete, unapproved drafts.

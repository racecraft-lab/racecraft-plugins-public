# SpecKit Pro Reviewability Preset

This preset ships with the `speckit-pro` plugin. Install, upgrade and scaffold
add it to a project with `specify preset add --dev <plugin-preset-dir>
--priority 5`; the runner's `detect-presets` helper reports the command. It adds
reviewability budgets and PR review packet requirements by replacing the spec,
plan and tasks templates, without editing `.specify/templates/*.md` directly.

After Spec Kit upgrades, verify resolution:

```text
specify preset resolve spec-template
specify preset resolve plan-template
specify preset resolve tasks-template
```

Those commands should resolve to `.specify/presets/speckit-pro-reviewability/templates/...`.
If they do not, rerun the scaffold-spec skill instead of patching core templates.

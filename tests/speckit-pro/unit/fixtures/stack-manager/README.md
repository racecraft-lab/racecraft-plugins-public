# PRSG-014 Stack Manager Fixtures

These fixtures exercise optional `gh stack` detection without calling the live
GitHub CLI extension or network APIs. Fake `gh` binaries are injected through a
test-scoped `PATH`; persisted evidence must still record canonical runtime argv
such as `["gh", "stack", "view", "--json"]`.


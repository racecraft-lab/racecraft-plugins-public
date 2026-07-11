# Unit Tests

This directory contains deterministic Python unit and contract tests for the
SpecKit Pro runner, repository tooling, and validation workflows. The suite
manifest retains layer ID `4` for CLI compatibility, but the filesystem name
describes the contents rather than the execution layer.

- `test-*.py` files exercise one focused behavior or contract.
- `fixtures/` stores purpose-named inputs, expected outputs, schemas, and fake
  installed-plugin trees.
- Fixture namespaces use behavior names, not the spec ID that originally
  introduced them. Synthetic spec IDs may still appear inside fixtures that
  explicitly test spec discovery or topology parsing.

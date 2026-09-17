# Execution-surface inventory

## Scope and snapshot

Static inventory captured at `2026-09-15T17:54:21Z` for the test tree,
repository-owned scripts, five relevant workflows, and `docs-site/package.json`.
It excludes vendored/generated content, `node_modules`, and historical specs. The
current suite-manifest hash is
`eae2b20f0bd7b4671173a3f8274d9dec259c1ca2fa3a431c00e5b72af2ae3c79`.

The test tree contains 151 Python/shell/Node executable-source files: 89
`test-*`, 18 `run-*`, and eight `validate-*` candidates. The manifest contains
102 registered entries. The existing deterministic inventory accounts for
Layers 1, 4, and 5; existing behavioral reports account for Layers 2, 3, 6,
and 7. This inventory adds the non-manifest execution surfaces and does not
recount `run-all.py` helpers as independent checks.

## Seven-layer and support classification

- Manifest semantic runners: Layer 1 structural validators; Layer 2 Claude and
  Codex trigger runners; Layer 3 Claude and Codex functional runners; Layer 4
  unit tests; Layer 5 tool-scoping validation; Layer 6 `run-all-fixtures.py`;
  and Layer 7 parity fixtures.
- Layer 6 class runners are children of `run-all-fixtures.py`, not additional
  independent suite entries. The same support classification applies to the
  trigger comparison/planning/campaign and carry-forward generator, functional
  headless/scorer helpers, and transcript reducer/scrubber.
- `run-all.py`, `run-layer-scripts.py`, container and hosted-Windows preflights,
  and `test-run-all.py` are suite/platform support rather than semantic layers.
- `run-native-evals.py` is a public native-evaluation CLI boundary. It is not a
  current manifest layer entry, so it is recorded separately rather than being
  misclassified as an unregistered unit test.

The JSON companion contains the exact path lists for every support/dispatch
group, including repository scripts, CI workflow commands, the optional formal
qualification workflow, and package-script validation/generator commands.

## Fixture inputs

There are 540 fixture/replay input files, counted independently of executable
checks: `evals/fixtures` 16, Layer 1 fixtures 75, Layer 2 fixtures 15, Layer 3
fixtures 47, unit fixtures 209, and Layer 6 replay/scenario inputs 182. This
is an inventory count only; it makes no corpus-content removal recommendation.

## Precise audit gaps

Two new, substantive catalog validations are absent from the frozen manifest
and deterministic-inventory snapshot:

- `tests/speckit-pro/unit/test-native-functional-catalog.py` — Layer-3 native
  functional catalog validation; SHA-256
  `b8b2b2338cae879a58a666207e6966224d27a1cc149880ebfcb248bde1e54243`.
- `tests/speckit-pro/unit/test-native-trigger-catalog.py` — Layer-2 native
  trigger catalog validation; SHA-256
  `f8e7c68ed02b8770f10486f3f693b5fcea2d17948371705f6a87743b1146a491`.

Both files are concurrently introduced work, so their registration status is
reported only as a timestamped/hash-frozen snapshot; this audit does not infer
the eventual manifest or catalog decision. `tests/speckit-pro/run-native-evals.py`
is likewise a separate new CLI surface not represented in the current
deterministic inventory, with execution integration owned elsewhere.

## Limits

No providers, external formal tools, package commands, or workflow jobs were
run. This does not claim complete suite qualification; it records the examined
entrypoints, fixture inputs, and the three precise currently-unrepresented
surfaces.

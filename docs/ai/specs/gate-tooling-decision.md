# Gate tooling decision record

Date: 2026-09-06. Status: decided for Python and TypeScript; installs follow
the operator's go after this record is reviewed.

This record picks one tool per deterministic gate per language for the three
PROJECT_COMMANDS slots the "Quality Gauntlet" memo adds: COMPLEXITY, MUTATION,
DEPENDENCY_RULES. It also defines the discovery table that populates those
slots and the validator that guards the table. Every command and exit code
below was read from the tool's official documentation or source on
2026-09-06; anything the docs did not settle is listed under **Unverified**
and again in the first-install checklist at the end.

Scope of this record: decisions and contracts only. No autopilot reference,
agent, or runner helper changes. The gate wiring is the next layer.

## Summary of picks

| Gate | Python | TypeScript |
| --- | --- | --- |
| COMPLEXITY (CRAP) | radon + coverage.py, joined by a plugin script | ESLint `complexity` + Istanbul-shape coverage (c8, or the Vitest/Jest reporter), joined by the same script |
| MUTATION | cosmic-ray | StrykerJS |
| DEPENDENCY_RULES | import-linter | dependency-cruiser |

The CRAP slot is a script, not a tool. Neither language has a single command
that emits per-function complexity and per-function coverage together. The
script ships with the plugin at
`speckit-pro/scripts/crap-score.py`, Python 3.11 standard library only, and
accepts either input pair. The script runs only radon, ESLint, and
`coverage json` with fixed argument lists; the test run that produces
coverage data is the first step of the slot command, because the repository
Bash-confinement guard forbids plugin Python from spawning an
operator-supplied executable. This record fixes the script's inputs and exit
contract so the table can name it now.

## COMPLEXITY (CRAP)

CRAP(m) = comp(m)^2 x (1 - cov(m)/100)^3 + comp(m). Source: Savoia and Evans,
"Change Risk Analysis and Predictions" (artima weblog thread 210575). The
original human threshold was 30 ("we decided to INITIALLY use a CRAP score of
30 as the threshold for crappiness", artima thread 215899). crap4j's own site
and repository were unreachable on 2026-09-06, so 30 rests on that one source.

### Python: radon + coverage.py

- **Install:** `pip install radon coverage`
- **Complexity, machine-readable:** `radon cc -j -s <paths...>`. JSON keyed by
  file path; each block has `name`, `type`, `rank`, `complexity`, `lineno`,
  `classname`, and nested `methods`. radon never exits non-zero on a complexity
  result; it is a reporter only.
- **Coverage, machine-readable:** `coverage json -o coverage.json`. coverage.py
  7.6.0 and later include per-function and per-class regions in the JSON with
  no extra flag: `files[path].functions[<qualified name>].summary.percent_covered`
  plus `start_line`. The region name is `Class.method` for methods and the
  start line is the `def` line, which is also radon's `lineno`, so the join is
  deterministic.
- **Exit behavior:** `coverage json --fail-under=N` exits 2 below a whole-run
  total only. The per-function CRAP verdict comes from the plugin script,
  which exits 1 when any function exceeds the ceiling and 0 otherwise.
- **Diff scoping:** both tools take paths. `radon cc -j <changed files>` and
  `coverage json --include=<changed files, comma separated>`.
- **Rank evidence:** radon ranks A 1-5, B 6-10, C 11-20, D 21-30, E 31-40,
  F 41+.
- **Alternative rejected:** xenon (`xenon -b B -m A -a A <paths>`) exits with
  the infraction count and gates raw complexity, but it emits no JSON and has
  no coverage term, so it cannot express CRAP. Use it only for a plain
  complexity gate without the script.

### TypeScript: ESLint `complexity` + Istanbul-shape coverage

- **Install:** `pnpm add -D eslint typescript-eslint c8` (swap c8 for the
  project's existing Vitest or Jest coverage reporter when present).
- **Complexity, machine-readable:** `eslint --format json <files...>` with the
  rule set to `complexity: ["warn", { "max": 0 }]` for the gate run, so every
  function is reported. The complexity number lives only in the message text
  ("{name} has a complexity of {n}. Maximum allowed is {max}."); the script
  parses it and joins on `line`.
- **Coverage, machine-readable:** `c8 --reporter=json <test command>` writes
  `coverage/coverage-final.json` in Istanbul shape: per file `fnMap` (function
  name, `decl`, `loc`, `line`) and `f` (hit count per function). Vitest
  (`--coverage.reporter=json`) and Jest (`--coverageReporters=json`) produce
  the same shape through istanbul-reports. Istanbul's `f` is hit-or-not per
  function; per-function line percent comes from `statementMap` and `s`
  filtered to the function's `loc`.
- **Exit behavior:** ESLint exits 0 with no errors, 1 with errors or warnings
  above `--max-warnings`, 2 on a configuration error. c8
  `check-coverage --functions N --per-file` sets exit code 1 below threshold.
  Vitest and Jest thresholds also exit 1. The CRAP verdict again comes from
  the plugin script.
- **Diff scoping:** ESLint accepts a file list; c8 and the runners take
  `--include` globs; Jest also has `--changedSince`.
- **Threshold evidence:** ESLint's documented default for `complexity` is 20.

### Threshold: shipped defaults (operator decision, 2026-09-06)

The memo's item 3 decision said the CRAP ceiling starts at 6 "per Bob". Bob's
own words are that he widened a threshold from 4 to 6 and is considering 8.
At full coverage CRAP equals raw complexity, so a single ceiling of 6 on CRAP
would fail every function above complexity 6 regardless of tests, and the
operator judged that 6 on both metrics risks the agent fragmenting functions
into shallow helpers, which is the Pocock failure mode. The two metrics are
therefore kept separate:

| Language | Raw complexity ceiling | CRAP ceiling |
| --- | --- | --- |
| python | 8 | 30 |
| typescript | 8 | 30 |

- Raw complexity 8 is Bob's upper agent threshold, applied to the functions
  changed in the diff. A strict ceiling that fails the first PR touching an
  over-limit function is an intended ratchet.
- CRAP 30 (Savoia) stays separate so it catches complex code that lacks tests
  instead of degenerating to a second complexity check.
- Bob's 6 remains the coached no-code fallback for raw complexity only, in
  the thresholds file layer, when a repository has no code to measure.

`.specify/quality-gates.json` is authoritative (schema at
`speckit_pro_runner/contracts/quality-gates.schema.json`, validator and
`recommend` command in `speckit_pro_runner/quality_gates.py`). The values
above are substituted only while that file is missing or invalid, so the
operator can see what would run; G0 blocks until the file is present. G0 is
a measurement, never a vacuous pass: `COMPLEXITY` runs on the whole tracked
source tree and records its baseline (pre-existing debt is recorded, exit 2
blocks), `MUTATION` records `deferred` because whole-tree mutation is
unbounded, and `DEPENDENCY_RULES` runs for real and blocks. An empty
`{paths}` at any later run is never executed; the orchestrator records
`n/a: no source files changed`, and `crap-score.py` refuses an empty list.
The
coach flow in `skills/speckit-coach/references/quality-gates-guide.md`
recommends the ceiling that lets about 90 percent of existing functions pass
and falls back to Bob's 6 when nothing can be measured.

## MUTATION

### Python: cosmic-ray

- **Install:** `pip install cosmic-ray`
- **Config:** a TOML file with `[cosmic-ray]` keys `module-path`, `timeout`,
  `excluded-modules`, `test-command`, and `distributor.name = "local"`.
- **Commands:** `cosmic-ray init config.toml session.sqlite`, then
  `cosmic-ray baseline config.toml` (fails when the unmutated suite fails),
  then `cosmic-ray exec config.toml session.sqlite`, then
  `cr-rate session.sqlite --fail-over <survival ceiling percent>`.
- **Exit behavior:** `cr-rate --fail-over N` exits non-zero when the survival
  rate exceeds N percent. It is a survival ceiling, so a mutation-score floor
  of F maps to `--fail-over (100 - F)`.
- **Diff scoping:** `cr-filter-git`, run after `init`, skips every mutant not
  on a line added or changed against a git branch (default `master`; override
  with `[cosmic-ray.filters.git-filter] branch = "..."`).
- **Machine-readable output:** none. `cr-report` is text, `cr-html` is HTML,
  and the session is SQLite. The gate reads the exit code; the score for the
  PR body is parsed from `cr-rate` stdout.
- **Alternative rejected:** mutmut 3.7 has cleaner config and a JSON export
  (`mutmut export-cicd-stats` writes `mutants/mutmut-cicd-stats.json`), but
  `mutmut run` never exits non-zero on survivors, has no threshold option, and
  has no diff scoping. A gate on it is entirely wrapper logic. It is the
  fallback if JSON becomes a hard requirement.

### TypeScript: StrykerJS

- **Install:** `npm init stryker@latest`, plus
  `pnpm add -D @stryker-mutator/vitest-runner` or
  `@stryker-mutator/jest-runner`.
- **Config:** `stryker.config.json` with `testRunner`, `mutate` globs (default
  `{src,lib}/**/!(*.+(s|S)pec|*.+(t|T)est).+(cjs|mjs|js|ts|...)`),
  `thresholds: { "high": 80, "low": 60, "break": <floor> }`, and
  `reporters` including `json`.
- **Command:** `npx stryker run --reporters json,progress --incremental`
  (`--mutate <changed files>` to scope). The JSON report lands at
  `reports/mutation/mutation.json`.
- **Exit behavior:** when the score is below `thresholds.break` Stryker exits
  1. `break: null` disables the failure, which is the documented default.
- **Diff scoping:** `mutate` globs and line ranges (`src/app.ts:5-7`) plus
  `--incremental` with `incrementalFile` (default
  `reports/stryker-incremental.json`). No `--since` flag exists in the
  current documentation.

### Threshold

Stryker documents high 80, low 60, break null. Shipped default floor per
language: 60, scoped to changed files, which is Stryker's documented "low"
mark. Python has no native default; 60 is mirrored from Stryker and cosmic-ray
is configured to fail at the same number through `cr-rate --fail-over 40`.
Per-repository coaching in the thresholds file layer may raise it.

## DEPENDENCY_RULES

### Python: import-linter

- **Install:** `pip install import-linter`
- **Config:** `.importlinter`, `setup.cfg`, or `pyproject.toml` under
  `[tool.importlinter]` with `root_package` (or `root_packages`) and one
  `[[tool.importlinter.contracts]]` per rule. Contract types: forbidden,
  protected, layers, independence, acyclic siblings, custom.
- **Command:** `lint-imports --config <path>`; `--contract <id>` (repeatable)
  limits the run to named contracts.
- **Exit behavior:** 0 when every contract passes, 1 when any fails. No
  contracts defined counts as a pass.
- **Diff scoping:** none by file. Contracts run over the whole root package
  and are cached. Diff mode selects contract ids whose modules overlap the
  changed paths, or runs the full set.
- **Machine-readable output:** none. The gate reads the exit code.
- **Graph for the architecture viewer:** import-linter emits DOT only
  (`import-linter drawgraph <pkg>`). For JSON use `pydeps <pkg> --no-output
  --show-deps`, or an `ast`-based stdlib walk of `Import`/`ImportFrom`.
- **Alternatives noted:** tach (`tach check`, `tach map` for a JSON graph) if
  same-tool JSON export outweighs contract expressiveness; pytest-archon for
  rules-as-tests.

### TypeScript: dependency-cruiser

- **Install:** `pnpm add -D dependency-cruiser`, then `npx depcruise --init`
  to write `.dependency-cruiser.cjs`.
- **Rules:** `forbidden: [{ name, severity: "error", from: {path}, to: {path} }]`.
- **Command:** `npx depcruise --config .dependency-cruiser.cjs --output-type err <paths...>`
  for the gate; `--output-type json` for the graph, with
  `depcruise-fmt -e -T err result.json` to derive the exit code from JSON.
- **Exit behavior:** the `err` reporter exits with the count of
  error-severity violations, 0 otherwise. The `json` reporter does not set the
  exit code on its own.
- **Diff scoping:** positional files, directories, or globs; `--include-only`;
  `--affected <rev>` for modules and their transitive dependents since a git
  revision.
- **tsconfig:** `--ts-config tsconfig.json` or `options.tsConfig.fileName`.
- **Baseline:** `depcruise-baseline` writes known violations; `--ignore-known`
  downgrades them so only new violations fail.
- **Graph for the architecture viewer:** the JSON output's
  `modules[].dependencies[]` and `summary.violations[]`.
- **Alternatives noted:** eslint-plugin-boundaries and eslint-plugin-import's
  `no-restricted-paths` ride ESLint's exit code and per-file scoping but emit
  no graph and have no baseline.

### Threshold

None. The slot is pass or fail against the rules file; the thresholds file
records the rules file path only.

## Discovery table

Step 0.11 (`detect-commands`) discovery reads a JSON table shipped in the plugin
at `speckit-pro/speckit_pro_runner/gate_discovery_table.json`. A repository
may override rows with a table of the same shape at
`.specify/gate-discovery.json`; a valid override's rows are consulted before
the shipped rows, and an invalid override is reported and ignored. The schema is documented at
`speckit-pro/speckit_pro_runner/contracts/gate-discovery-table.schema.json`
and enforced by `speckit-pro/speckit_pro_runner/gate_discovery.py`, standard
library only. Neither is registered as a runner helper or gate operation.

Row fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `language` | `python` or `typescript` | Closed enum. New languages are new enum values plus rows. |
| `slot` | `COMPLEXITY`, `MUTATION`, or `DEPENDENCY_RULES` | Closed enum. `FORMAL_CHECK` joins when the item 9 spike lands. |
| `signal` | object `{ "kind": "file", "path": "<repo-relative path>" }` | Detection evidence. A row matches when the file exists. One kind for now; new kinds are schema changes. |
| `tool` | string | Human name used in the missing-tool prompt and the Prerequisites table. |
| `install` | string | Exact install command. Needed by the "install" answer in the missing-tool prompt. |
| `probe` | array of bare executable names, optional | Discovery reports `tool_present: true` only when every name resolves on PATH or under `node_modules/.bin`. Absent means presence is unknown. |
| `command` | string | Exact command written into the PROJECT_COMMANDS slot. `{ceiling}`, `{complexity_ceiling}`, `{floor}`, `{survival_ceiling}`, and `{rules_path}` are filled at discovery from `.specify/quality-gates.json` (the shipped defaults are substituted only while that file is missing or invalid, and G0 blocks until it is present) and the signal path. `{paths}` and `{plugin_root}` stay literal and are filled at each run, which keeps machine-specific paths out of the workflow file. |

Rules the validator enforces:

- Top level is an object with `schema_version` `"1.0"` and a non-empty `rows` array.
- Every row has the six required fields above, all non-empty; `probe` is the only optional field.
- `language` and `slot` are drawn from the closed enums.
- `signal.path` is repo-relative: no leading `/`, no `..` segment.
- No two rows share the same `(language, slot, signal.path)`.
- Within one `(language, slot)`, the first matching row in file order wins.
  This is how TypeScript carries c8, Vitest, and Jest coverage rows for the
  same slot without a priority field.
- Every `{placeholder}` in `command` is one of the seven names above.

## Unverified, carried forward from the research

- cosmic-ray: the exact non-zero exit value of `cr-rate --fail-over`, and the
  `cr-filter-git` invocation syntax (its CLI reference page is still a TODO;
  source shows it runs `git diff --relative -U0 <branch> .` and takes `--config`).
- StrykerJS: no `--since` flag was found; diff scoping is `--mutate` plus
  `--incremental`.
- c8: whether its V8-to-Istanbul conversion produces the same `fnMap` set as
  Istanbul-instrumented output.
- ESLint `complexity`: the number is only in the message string; the parser
  is coupled to that format.
- CRAP threshold 30: one source (Savoia, artima). crap4j unreachable.

## First-install checklist for the next layer

1. Install each pick in a scratch project per language and run the exact
   commands above; record the real exit codes for `cr-rate --fail-over` and
   the `cr-filter-git` syntax.
2. Confirm c8's `fnMap` lines up with ESLint's reported function lines on a
   file with nested functions and arrow functions.
3. Pin the ESLint message regex in the CRAP script with a fixture drawn from
   the installed ESLint version.
4. Confirm `depcruise --output-type err` returns the violation count on the
   docs-site tree, which is the first dogfood target.
5. Confirm the raw complexity 8 / CRAP 30 split holds on the first dogfood run before the thresholds file layer coaches per-repo values.

## Sources

Fetched 2026-09-06 through Context7 and the tools' official sites and repositories.

- radon: Context7 `/rubik/radon`; docs/commandline.rst; radon/cli/tools.py; radon/cli/__init__.py
- xenon: github.com/rubik/xenon README; xenon/core.py
- coverage.py: Context7 `/coveragepy/coveragepy`; coverage.readthedocs.io changes (7.6.0) and cmd_json; coverage/jsonreport.py; coverage/regions.py
- ESLint: Context7 `/eslint/eslint`; eslint.org/docs/latest/rules/complexity; configuration-files; lib/rules/complexity.js
- c8: Context7 `/bcoe/c8`; README; lib/parse-args.js; lib/commands/check-coverage.js
- nyc: github.com/istanbuljs/nyc README; index.js
- istanbul-lib-coverage: packages/istanbul-lib-coverage/lib/file-coverage.js
- Vitest: Context7 `/vitest-dev/vitest`; vitest.dev/guide/coverage; vitest.dev/config/coverage
- Jest: jestjs.io/docs/configuration
- CRAP: artima.com weblogs threads 210575 and 215899
- mutmut: Context7 `/boxed/mutmut`; mutmut.readthedocs.io; README.rst; src/mutmut/__main__.py; pypi.org/project/mutmut
- cosmic-ray: Context7 `/sixty-north/cosmic-ray`; cosmic-ray.readthedocs.io reference/cli and concepts; docs/source/how-tos/filters.rst; src/cosmic_ray/tools/filters/git.py; pypi.org/project/cosmic-ray
- StrykerJS: Context7 `/stryker-mutator/stryker-js`; stryker-mutator.io/docs/stryker-js configuration, incremental, getting-started, usage, jest-runner, vitest-runner; github releases (v10.0.0)
- import-linter: Context7 `/seddonym/import-linter`; docs/get_started install, configure, run; docs/contract_types; docs/ui.md; src/importlinter/cli.py
- pydeps: pydeps.readthedocs.io
- tach: github.com/gauge-sh/tach README (docs.gauge.sh returned 403)
- pytest-archon: github.com/jwbargsten/pytest-archon
- dependency-cruiser: Context7 `/sverweij/dependency-cruiser`; README; doc/cli.md; doc/options-reference.md; doc/rules-reference.md; doc/output-format.md; types/cruise-result.d.mts
- eslint-plugin-boundaries: github.com/javierbrea/eslint-plugin-boundaries
- eslint-plugin-import no-restricted-paths: docs/rules/no-restricted-paths.md

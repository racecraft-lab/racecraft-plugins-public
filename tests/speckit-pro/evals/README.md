# Canonical native-evaluation contracts

This directory contains both a provider-free contract library and the public
native executor. The catalog library defines shared cases, deterministic trial
planning, normalized observations, and replayable grading without launching a
model. `run-native-evals.py` is the separate public executor described below.
Neither surface by itself claims native qualification.

## Catalog API

`tests/speckit-pro/lib/native_eval_catalog.py` exposes:

- `load_catalog(path, repo_root)`: parse strict JSON (including duplicate-key
  rejection), validate it, and return the catalog.
- `validate_catalog(catalog, repo_root)`: validate an in-memory catalog and
  return it unchanged.
- `select_cases(catalog, layers=None, case_ids=None)`: retain catalog order and
  reject unknown, duplicate, or empty filters and an empty result.
- `plan_trials(cases, hosts=("claude", "codex"), runs=1)`: emit deterministic
  `{case_id, host, mode, trial}` rows. Trials are one-based and `runs` must be an
  integer from 1 through 50. Every requested host must exist on every case.
- `input_fingerprint(case, host, mode, runtime_identity)`: return a canonical
  SHA-256 over executable case inputs, chosen host settings and mode, and a
  nonempty actual runtime identity. Requirements, checks, and descriptive
  provenance are excluded; their separate grading identity permits regrading
  sufficient retained native evidence without another subject launch.

The `response_json_field` check grades a field from the entire final response,
which must be strict JSON. It takes a nonempty `field_path` and
`expected_by_host` containing exactly `claude` and `codex`. The trusted subject
host selects its expectation; the other host's value is never an alternative.
Equality preserves types and list order. Missing fields, duplicate JSON keys,
fenced output, and malformed JSON fail. Use host differences only for documented
native mechanics; shared behavioral criteria remain identical.

The only catalog schema is `native-eval-catalog/v1`:

```json
{
  "schema_version": "native-eval-catalog/v1",
  "cases": [
    {
      "id": "stable.case-id",
      "layer": "trigger",
      "capability": "Human-readable capability under evaluation.",
      "timeout_seconds": 300,
      "resource_class": "ordinary",
      "requirements": [
        {"id": "r1", "description": "A checkable shared requirement."}
      ],
      "prompt": "Use {{skill}} to perform the bounded task.",
      "fixtures": [
        {
          "source": "tests/speckit-pro/fixtures/input.txt",
          "destination": "input.txt"
        }
      ],
      "hosts": {
        "claude": {
          "skill": "plugin:skill",
          "allowed_tools": ["Read"],
          "modes": ["plugin"]
        },
        "codex": {
          "skill": "skill",
          "allowed_tools": ["read_file"],
          "modes": ["project"]
        }
      },
      "checks": [
        {
          "id": "selection",
          "requirement": "r1",
          "type": "selection",
          "expected": ["skill"],
          "allowed_extra": []
        }
      ],
      "native_differences": [
        "Adapters normalize documented host aliases before grading."
      ],
      "provenance": [
        "tests/speckit-pro/layer2-trigger/legacy-corpus.json"
      ]
    }
  ]
}
```

Cases require exactly the `claude` and `codex` host entries. `skill` is a
nonempty string or `null`; prompts using `{{skill}}` require a non-null skill on
both hosts. No other prompt placeholder is accepted. Fixture sources must be
existing files contained under the repository's `tests/speckit-pro` directory,
including after symlink resolution. Destinations and artifact paths are
canonical workspace-relative POSIX paths. Fixture destinations must be unique
and non-overlapping: a file destination such as `a` cannot coexist with `a/b`.
`timeout_seconds` is a required integer from 1 through 3600. `resource_class`
is required and is either `ordinary` or `nested`; it describes expected nested
agent execution without implying that interactive Claude teams can run in a
headless mode.

Every requirement must be covered by at least one check. Check IDs and
requirement IDs are unique within a case. Supported checks and parameters are:

- `selection`: `expected` canonical skill names and `allowed_extra` names. A
  missing expected activation, duplicate activation, or any undeclared
  activation fails.
- `text`: `source` is `final_text` or an artifact-relative path; `pattern` is a
  nonempty regular expression.
- `file_exists`: `path` and an actual boolean `exists`.
- `json_field`: `path`, nonempty `field_path` list of object keys or nonnegative
  list indexes, and strict-JSON `expected`. Equality is recursive and
  type-strict, so JSON `true` does not equal `1`.
- `tool_used`: canonical `name`, integer `min` and `max`, and optional
  `input_regex`. Only successful matching calls count.
- `tool_order`: canonical `before` and `after` names. Successful calls must
  establish that order.
- `file_access`: an exact canonical workspace-relative `path` read through the
  `read_file` operation. It establishes the recorded read event, not file
  contents, inode identity, or every possible access route.
- `file_search`: a recursive `pattern` in the form `**/<filename-glob>` and
  an exact `matches` path list (which may be empty). Only successful root-level
  native Glob or a single unbounded native `find` command qualifies. Claude
  must also provide its structured complete, untruncated result and matching
  counts. Child searches, partial queries, pipelines, malformed paths, and
  prose claims do not establish absence. Runtime files are not filtered out;
  this check alone does not distinguish project files from staged skill files.
- `semantic`: a nonempty `rubric`. Deterministic grading returns `needs_judge`
  until a typed, evidence-backed verdict is supplied.

`native_git_final_state` requires a declared `git_fixture` and compares all of
these fields exactly: `head_equals_initial_feature`, `branch`, `commit_count`,
`commits_added`, `changed_tracked_paths_from_initial_feature`, and `status`.
The status contains `clean`, `tracked_dirty`, `untracked_dirty`, and the complete
`tracked` and `untracked` lists. Path lists are canonical, sorted, and unique;
counts and status flags must agree with their lists. HEAD is compared with the
controller's initial feature commit, not a subject-provided object ID.
The execution layer must attach the hash/size-bound controller Git record after
native capture (or reconstruct it from retained evidence when regrading).
Missing or malformed evidence is invalid; a valid but unequal final state fails.
This proves final Git state, not the absence of transient attempted operations.

## Observation and grading API

Native adapters must normalize into the same shape before grading:

```json
{
  "completed": true,
  "error": null,
  "final_text": "...",
  "activations": ["canonical-skill"],
  "tool_calls": [
    {
      "name": "canonical-tool",
      "input": {},
      "output": "optional captured result",
      "success": true,
      "id": "optional-call-id",
      "parent_id": null,
      "position": 0
    }
  ],
  "artifacts": {"relative/path.txt": "captured text"},
  "usage": {},
  "native_metadata": {"model": "optional resolved model evidence"}
}
```

`id`, `parent_id`, `position`, and strict-JSON `output` are optional tool-call
evidence retained for later ownership, grounding, and integration-order checks.
`native_metadata` is an optional strict-JSON object for resolved model, catalog,
and runtime evidence. It stays in stored capture but must be excluded from
blinded semantic-judge input. The base tool checks use the normalized name,
JSON input, success flag, and observed sequence. Claude's actual native
subagent invocation event is `Agent`, even though the installed initialization
event currently advertises `Task`. Adapters normalize documented host aliases;
literal provider-specific names are not treated as parity. Required base fields
may not be omitted, and unknown extra keys remain invalid.

`grade_observation(case, observation, semantic_verdicts=None)` returns:

```json
{
  "status": "pass|fail|invalid|needs_judge",
  "checks": [
    {"id": "check-id", "verdict": "pass|fail|invalid|needs_judge", "reason": "..."}
  ]
}
```

Missing, malformed, incomplete, or error-bearing native evidence is `invalid`.
A wrong outcome is `fail`; equal wrong observations from both hosts do not
become a pass. Semantic verdicts, when supplied, must contain exactly the
semantic check IDs. Each value is
`{"passed": <actual boolean>, "evidence": [<nonempty reference>, ...]}`;
truthy strings, empty evidence, and missing or extra verdicts are invalid.

## Public native-evaluation entrypoint

Use `python3 tests/speckit-pro/run-native-evals.py`. It has two deliberately
separate modes:

- `--preview` validates the catalog and selectors, then prints a machine JSON
  plan. It does not create an output directory, inspect either provider CLI, or
  launch a provider.
- `--execute --output <directory>` runs the selected native trials and writes
  retained evidence and a report. It is an execution command, not a preview.

The selector is required. Native evaluation accepts only the current
suite-manifest selectors `2`/`trigger`, `3`/`functional`,
`6`/`integration`, and `7`/`parity`. Those are the new seven-layer numbers;
there are no legacy selector aliases. Layers 1, 4, and 5 remain structural,
unit, and tool-scoping validation respectively and are not native-evaluation
selectors.

| Layer | Meaning | Native entrypoint status |
| --- | --- | --- |
| 1 | Structural validation | Deterministic suite, not selected here |
| 2 | Trigger/skill selection | Live native selector: `2` or `trigger` |
| 3 | Functional behavior | Live native selector: `3` or `functional` |
| 4 | Unit tests | Deterministic suite, not selected here |
| 5 | Tool scoping | Deterministic suite, not selected here |
| 6 | Integration behavior | Live native selector: `6` or `integration` |
| 7 | Cross-host parity | Live native selector: `7` or `parity` |

### Old-to-new layer migration

The renumbering moved two directories and retired one layer. There is no legacy
selector alias for any of them.

| Old | New | Change |
| --- | --- | --- |
| 1 | 1 | Unchanged |
| 2 | 2 | Unchanged |
| 3 | 3 | Unchanged |
| 4 | 4 | Unchanged |
| 5 | 5 | Unchanged |
| 6 (efficiency) | — | Retired. The directory no longer exists and has no successor. Timing, token usage and execution overhead are collected from the retained evaluations instead of from a separate mandatory layer. |
| 7 (integration) | 6 | Directory renamed `tests/speckit-pro/layer7-integration` to `tests/speckit-pro/layer6-integration`; manifest id `6`, key `integration`. |
| 8 (parity) | 7 | Directory renamed `tests/speckit-pro/layer8-parity` to `tests/speckit-pro/layer7-parity`; manifest id `7`, key `parity`. |

Historical reports, archived specifications and old receipts keep their
original numbers. They are read-only records and the renumbering does not
rewrite them.

The default is one trial (`--runs 1`) for both hosts (`--hosts both`). Claude
uses the official `claude plugin eval` path; Codex uses native `codex exec`
with JSON evidence. The catalog defines each host mode rather than treating one
provider's transcript as evidence for the other.

The provider interfaces are documented by
[Anthropic's plugin-evals guide](https://code.claude.com/docs/en/plugin-evals)
and OpenAI's [Testing Agent Skills Systematically with Evals](https://developers.openai.com/blog/eval-skills).
Those documents describe provider capabilities, not a qualification claim for
this catalog or its adapters.

### Preview examples

These examples are safe plan-only commands and were checked in preview mode:

```sh
python3 tests/speckit-pro/run-native-evals.py \
  --layers trigger --case-id trigger-02994d935cc99634d588ea00 --preview

python3 tests/speckit-pro/run-native-evals.py \
  --layers 2 3 --hosts codex --runs 1 --preview
```

Preview reports distinct counts:

- `unique_cases`: selected catalog cases;
- `native_modes`: unique case/host/mode combinations;
- `subject_trials`: planned provider subject runs; and
- `potential_judge_calls`: at most one shared semantic judge call for each
  selected semantic subject output.

The judge count is not a count per semantic criterion. A single judge request
covers all semantic checks for one captured output.

### Limits and execution controls

Provider limits default to four concurrent Claude and four concurrent Codex
jobs. Each may be set from one through eight. Nested work defaults to one and
may be set to two at most, never above the selected host's provider limit.
Subject and judge jobs share the same Codex provider pool, so a pending judge
does not reserve a separate hidden pool.

An execution invocation needs an output directory and can incur provider cost:

```sh
python3 tests/speckit-pro/run-native-evals.py \
  --layers trigger --case-id trigger-02994d935cc99634d588ea00 \
  --hosts both --execute --output .native-eval-output/qualification
```

Do not use an existing evidence directory without `--resume`. Explicit retries
are intentionally narrow: provide every `--retry-case` plus exactly one
`--retry-status fail`, `invalid`, or `incomplete`, and include `--resume`:

```sh
python3 tests/speckit-pro/run-native-evals.py \
  --layers trigger --case-id trigger-02994d935cc99634d588ea00 \
  --hosts both --execute --output .native-eval-output/qualification --resume \
  --retry-case trigger-02994d935cc99634d588ea00 --retry-status invalid
```

There is no automatic retry. A retry is separately counted from new subject
launches and from checkpoint reuse. Reports keep those categories separate,
along with subject runs, semantic judge calls, and reused retained captures.

Keep raw evidence private. The repository ignores `.native-eval-output/`; do
not commit prepared launch receipts, native session logs, or judge inputs.
Codex requires a canonical output root outside system temporary directories.
Before a subject launch, the adapter checks that the exact native permission
profile permits its own workspace while denying private evidence, sibling
trials, and repository source. Writable trials also check protected skill and
configuration trees. A failed control stops preparation without a model call.

### Reading results safely

Input identity binds the selected case, host, mode, fixture content, and actual
runtime identity. Grading identity is separate so retained, sufficient evidence
can be regraded without silently launching a new subject. That separation does
not make evidence portable between different runtimes or models.

`fail` means complete evidence showed the subject did not meet a check.
`invalid` means the run, capture, schema, evidence, or required boundary proof
was incomplete or malformed; it is not a pass and is not auto-retried.
`needs_judge` remains unresolved until a typed judge response with retained
evidence is validated. Reuse means a matching retained checkpoint was used; it
does not mean the provider was called again.

Semantic grading uses a shared Codex judge and retains request/response receipts.
The versioned judge-only projection uses the trusted subject host, not the judge
provider, to normalize approved native tool names. It neutralizes call IDs,
preserves parent joins and action order, and removes known native transport
metadata. A successful Claude Skill transport is omitted only when its target
agrees with a passing selection check; failed attempts remain evidence. Unknown
native tools are rejected rather than silently discarded. Raw captures and
deterministic grading remain unchanged. Meaningful prose and action differences
may still identify a host indirectly: this is not statistical blindness. The
judged evidence and grader identity must remain available for reuse.

### Isolation and qualification status

Native subjects must be separated from grader material and expected-answer
inputs. The observed Claude initialization workspace is distinct from the
outer official-runner plugin path, so staging-path placement alone is neither a
leak finding nor proof of isolation. A native isolation canary must show both a
successful allowed in-workspace read and a recorded denied attempted read of a
synthetic outside-workspace sentinel. That canary is required before claiming
the boundary qualified.

Current qualification is incomplete. The original Codex canary exposed a real
temporary-directory exception in its native minimal-runtime profile. Subsequent
provider-free controls pass with non-temporary evidence storage. After disabling
parent-project instruction traversal for the isolated trial, the native Codex
positive and negative skill-injection canaries also pass. That verifies this
small activation workload, not the complete functional or workflow corpus.
Earlier Claude controls refused without attempting either read. Two later
read-only controls now demonstrate actual enforcement: an explicitly granted
fixture read succeeded while a hidden eval-tree sibling was denied; a separate
control also denied a synthetic controller file outside that tree. Both denials
were bound to exact native Read calls and terminal permission-denial records,
and neither protected marker appeared in the trace. These controls qualify the
tested read paths and grants, not every writable, shell, network, or agent-tool
profile. Do not treat configured permissions or refusal as proof. The Codex
boundary includes documented minimal-runtime access; it is not a machine-wide
workspace-only sandbox.

Migration is **IN PROGRESS**. Only the currently authored catalog subset is
available, and no complete native qualification is claimed. See the audit
ledger under `tests/speckit-pro/evals/audit/` for current coverage and gaps;
this document intentionally does not hard-code pass totals. Genuine interactive
team work needs separate, user-operated qualification. Other requirements are
not waived because a non-interactive native run or deterministic test passed.

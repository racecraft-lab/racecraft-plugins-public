# Formal tool setup and consumer CI

Select useful behavior before installing anything. `formal-doctor` inspects the
workflow's selected tools and reports missing prerequisites; it never installs.
The [setup script](../scripts/setup-formal-tools.py) defaults to a read-only
preview. An operator may explicitly authorize `--apply`, including through a
reviewed CI workflow. It installs only in that project's `.specify/tools/formal`.
It does not install Java, Node.js, Docker, skills, or global packages.

## Prepare a first check

Use the absolute installed plugin path as `PLUGIN_ROOT`, and the established
workflow worktree as `WORKFLOW_ROOT`. Set `resolved_python` to the verified
absolute interpreter path returned by the installed runtime contract, rather
than assuming a shell alias. Examples below use POSIX shell syntax; the scripts
themselves use Python 3.11+ standard library. Start with:

```sh
"$resolved_python" "$PLUGIN_ROOT/skills/speckit-coach/scripts/setup-formal-tools.py" \
  --repo-root "$WORKFLOW_ROOT" --tool apalache
```

Explain the preview's downloads and local destination. After authorization,
repeat with `--apply`. Add `--tool tlc` or `--tool quint` only when selected.
`--download-cache DIRECTORY` uses already downloaded release assets and fails
if one is absent; it does not fall back to downloading a missing archive.
Selected Quint still uses `npm ci` and registry access for its locked packages.

Copy the counter's model, native configuration, and example catalog to
`formal/counter` and `.specify/formal-methods.json`. Replace the catalog's tool
entry with the setup result, then record explicit workflow selection. Keep the
catalog, model, config, and compact checkpoint records in version control;
tools, generated traces, and raw checker output are ignored. Follow the
[counter walkthrough](formal-methods-guide.md#first-useful-check) to obtain a
pass and explain an intentional counterexample before adapting the model.

## Qualified versions and requirements

| Tool | Pinned release | Execution boundary |
|---|---|---|
| Apalache | 0.62.2 | Official distribution JAR, checksum verified before execution |
| TLC | 1.7.4 (`tla2tools.jar`; reports internal TLC 2.19) | Official release JAR, checksum verified |
| Quint | 0.32.0 | Shipped package lock, `npm ci --ignore-scripts`, full installed-tree checksum, Node.js 24 |

The native profile was executed locally on macOS arm64 with Java 26.0.1,
Node.js 24.11.1, and Python 3.11.0. [Hosted qualification](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/34441556263)
also passed native checker and installed-consumer cases on Ubuntu x64 with
Temurin 25.0.4+1/Python 3.11.16 and macOS arm64 with Temurin
25.0.4+101.0.LTS/Python 3.11.9, both using Node.js 24.11.1. The macOS job passed
Python, TypeScript and Swift implementation traces with Apalache and TLC, plus
the optional Quint path. These are executed profiles; Windows, native Linux
arm64 and other runtime versions still require their own qualification.

Apalache's [official instructions](https://apalache-mc.org/docs/apalache/installation/index.html)
recommend Java 25 and at least 4 GB of RAM; its JAR targets Java 21 bytecode.
The catalog's `heap_mb` defaults in these examples to 4096. Allow additional
memory for the OS, Node/compiler, and checker process; a heap limit is not the
machine's total memory requirement. Follow the selected platform's official
Java installation instructions if doctor reports a missing or incompatible
runtime. The workflow does not acquire a runtime automatically.

Checksums and exact official download URLs live together in the setup script.
Apalache's archive is checksum-verified before extracting its single named,
regular JAR; unrelated members and links are never extracted. Quint installation
uses the shipped lockfile with lifecycle scripts disabled, separate empty npm
configuration files, and an isolated temporary cache. Reuse verifies installed
identity instead of trusting an existing executable's name.

## Optional official container

The executed Apalache image is
`ghcr.io/apalache-mc/apalache@sha256:2003be7b0546c54be85adfc2969e43b28e4903f960e27c00dfdf1ed4f106113c`,
the official `v0.62.2` Linux amd64 image. It was run under Docker's amd64
emulation on a macOS arm64 host. It contains Java 25.0.4+7. After explicitly
authorizing the image pull, a standalone tutorial check is:

```sh
docker run --rm --platform linux/amd64 --network none --memory 6g \
  --entrypoint java \
  --mount "type=bind,src=$WORKFLOW_ROOT/formal/counter,dst=/model,readonly" \
  ghcr.io/apalache-mc/apalache@sha256:2003be7b0546c54be85adfc2969e43b28e4903f960e27c00dfdf1ed4f106113c \
  -Xmx4g -jar /opt/apalache/lib/apalache.jar --out-dir=/tmp/check \
  check --config=/model/Counter.cfg --length=5 /model/Counter.tla
```

This standalone command demonstrates the checker; it does not create workflow
checkpoint evidence. The current workflow adapter requires a local pinned JAR.
A consumer container may instead contain Python and the installed plugin plus
the pinned tools, and run the same Python checkpoint wrapper below. That custom
image needs its own execution qualification. The official image alone does not
provide the full SpecKit runner environment.

## Consumer CI and test order

Use the same installed plugin release in development and CI. Provision selected
pinned tools in an explicit setup step, preserve the workflow/catalog/model
files in the checkout, and run the project's normal build/type/test commands.
When traces are selected, their tested producer/adapter must run in those test
slots before the final or Post formal check. Do not replace application tests
with model checks or accept stale trace files from another checkout.

```sh
"$resolved_python" "$PLUGIN_ROOT/skills/speckit-coach/scripts/run-formal-ci.py" \
  --repo-root "$WORKFLOW_ROOT" --workflow docs/ai/specs/.process/FEATURE-workflow.md \
  --spec specs/feature/spec.md --plan specs/feature/plan.md --checkpoint final
```

Use `plan` after authoring, `planning` after later planning reconciliation,
`final` after implementation verification, and `post` after integration tests.
Pass `--state PATH` when the workflow has an existing durable state file. The
wrapper uses the installed runner contract and returns success only for an
actual pass or disabled selection. A waiver remains a separate operator decision
and is not a passing CI result. Raw output stays bounded and ignored; preserve
the returned compact `commit_paths` in the existing planning/verification commit.

Hosted runners remain the default. This optional formal job does not change
organization-runner admission, resource requirements, or the normal seven-phase
order. A consumer that needs offline checks should provision approved artifacts
first and disable networking for the subsequent checking environment.

## Upgrade and recovery

Keep the current tool/catalog identity until the replacement profile has passed
the same positive and negative checks. Install a new pinned release in a new
version directory; this setup script never overwrites a differing existing
release. A checksum mismatch, changed Quint tree, or incomplete receipt stops
with an inspection message. Preserve the directory and evidence while deciding
whether to restore known bytes or explicitly remove only that failed install
and rerun setup. Never rewrite a checksum merely to silence doctor.

After changing the approved catalog or plugin release, rerun doctor and the
affected planning/final/Post checkpoints. Resume detects stale evidence and
identifies the planning phase to revisit. Selection and model files survive
plugin upgrades and feature archival because they belong to the project, under
durable paths. Record any operator waiver separately, including its reason and
approval reference; it does not change a failed check into a pass.

# Quickstart: Cross-Platform Runner Foundation

This quickstart describes the planned XPLAT-004 source-checkout workflow after implementation.

## Preconditions

- Python 3.11+ is available.
- Official Spec Kit / `specify` is available to the runner environment.
- Commands run from the repository root unless noted.
- Runner module invocation runs from the `speckit-pro/` package context or an equivalent Python path that exposes `speckit_pro_runner`.

## Run Runtime Info

```bash
cd speckit-pro
printf '%s\n' '{"schema_version":"1.0","helper_id":"runner","operation":"runtime-info","mode":"read_only","inputs":{}}' | python3 -m speckit_pro_runner
```

Expected result:

- stdout contains one JSON response.
- `status` is `"ok"` when the request is valid.
- `data` identifies `runner_name: "speckit_pro_runner"`, `runner_contract_id: "speckit-pro-runner"`, and `selected_runtime_name: "python-stdlib-runner"`.

## Run Preflight

```bash
cd speckit-pro
printf '%s\n' '{"schema_version":"1.0","helper_id":"runner","operation":"preflight","mode":"read_only","inputs":{}}' | python3 -m speckit_pro_runner
```

Expected result on a valid source checkout:

- stdout contains one JSON response with `status: "ok"`.
- The report includes Python version, platform, architecture, plugin root, prerequisite records, runner identity, source-checkout context, and typed metadata pointers.
- stderr is empty or contains only line-delimited JSON diagnostics.

Expected result when a required prerequisite is unavailable:

- stdout still contains one JSON response.
- `status` is `"missing_prerequisite"`.
- diagnostics include a stable missing-prerequisite code.
- the process exits with code `3` for prerequisite failure.

## Run Runner Contract Tests

```bash
bash tests/speckit-pro/run-all.sh --layer 4
```

The Layer 4 wrapper calls the Python stdlib test entrypoint. The Python test launches the runner with argv form and `shell=False`; it does not invoke the runner through a shell launcher.

## Validate Metadata JSON

```bash
python3 -m json.tool speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json >/dev/null
```

Expected result:

- The manifest parses as JSON.
- Runner-owned Python source files are represented in `runner_files`.
- Manifest and checksum files are not included in their own checksum set.

## Check Source Index and Whitespace

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"
git diff --check
```

Expected result:

- The spec index check is current.
- No whitespace errors are reported.

## Scope Boundaries

XPLAT-004 does not:

- port real production helpers;
- copy runner files into `dist/**`;
- switch active Claude Code or Codex skills, hooks, generated payloads, public docs, or install behavior;
- prove installed-cache launch behavior;
- complete native Windows/macOS/Linux UAT;
- make public native-platform support claims.

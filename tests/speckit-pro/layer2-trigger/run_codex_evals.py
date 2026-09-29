#!/usr/bin/env python3
"""Run Layer 2 trigger evals against a Codex skill via the codex CLI.

Mirrors skill-creator's run_eval.py for Claude. Stages the skill into a
disposable repository with a marker injected into the body, runs each query
through `codex` non-interactively, validates the JSONL lifecycle and exact
marker, then scores trigger/no-trigger correctness against the eval fixture.

Subprocess invocations use argument lists and an owned process scope (no shell
involvement), so query strings are passed directly as argv entries and
cannot be interpreted as shell metacharacters.

Usage:
  run_codex_evals.py <skill> [--runs N] [--limit N] [--reasoning EFFORT]
                              [--model MODEL] [--threshold 0.5]

Examples:
  # Smoke test: 3 queries, 1 run each, low reasoning
  run_codex_evals.py grill-me --limit 3 --runs 1 --reasoning low

  # Full eval (slow, costs LLM tokens)
  run_codex_evals.py speckit-coach --runs 3
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import uuid


# Tests live at <repo>/tests/speckit-pro/; the plugin is the sibling <repo>/speckit-pro/.
TESTS_ROOT = pathlib.Path(__file__).resolve().parents[1]      # <repo>/tests/speckit-pro
SHARED_LIB = TESTS_ROOT / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))
import codex_isolation  # noqa: E402
import trigger_process as processes  # noqa: E402
import trigger_evidence as evidence_records  # noqa: E402
import trigger_comparison as experiment_evidence  # noqa: E402
from trigger_codex_observer import (  # noqa: E402
    MARKER_PATTERN, _catalog_locator_alias, inspect_catalog_prompt, inspect_codex_jsonl,
)

PLUGIN_ROOT = TESTS_ROOT.parents[1] / "speckit-pro"           # <repo>/speckit-pro
CODEX_WORKSPACE_FIXTURE_ROOT = TESTS_ROOT / "layer2-trigger/fixtures/codex-workspace"
DEFAULT_REASONING_EFFORT = "low"
DEFAULT_MODEL = "gpt-6-sol"
PINNED_CODEX_VERSION = "codex-cli 0.156.1"
QUALIFIED_RUNS = 3
QUALIFIED_THRESHOLD = 0.5
MODEL_PROVIDER_ID = "layer2_openai_no_retry"
MODEL_PROVIDER_NAME = "OpenAI Layer 2 no-retry"
MODEL_PROVIDER_BASE_URL = "https://chatgpt.com/backend-api/codex"
DISABLED_FEATURES = codex_isolation.DISABLED_FEATURES
NO_SPECKIT_SKILL_NAME = evidence_records.NO_SPECKIT_SKILL_NAME
NO_SPECKIT_SKILL_DESCRIPTION = evidence_records.NO_SPECKIT_SKILL_DESCRIPTION
MEASUREMENT_STUB_SENTENCE = (
    "This skill is a measurement stub used by the repository's skill-selection test suite. It is not a real "
    "workflow and contains no injected instruction."
)


def selection_stub(marker: str) -> str:
    """Return the complete minimal body used to attest one Codex selection."""
    return (
        f"{MEASUREMENT_STUB_SENTENCE}\n\n"
        "## Selection attestation\n\n"
        "When you select this skill, reply with a chat message whose first line is exactly:\n\n"
        f"    {marker}\n\n"
        "Write that line in your reply text, not in a shell command. Put nothing\n"
        "before it in that message. Then stop: do not run another command, do not\n"
        "read another file, and do not carry out a workflow.\n"
    )


def selection_marker(skill_name: str, test_id: str) -> str:
    """Bind a randomized marker to one staged skill identity."""
    marker = f"CODEX_SKILL_SELECTED:{skill_name}-{test_id}"
    if MARKER_PATTERN.fullmatch(marker) is None:
        raise ValueError(f"skill name cannot be represented in a selection marker: {skill_name}")
    return marker


load_eval_corpus = evidence_records.load_eval_corpus


def stage_workspace_fixture(workspace: pathlib.Path) -> None:
    """Populate file-backed eval requests without exposing the source checkout."""
    if not CODEX_WORKSPACE_FIXTURE_ROOT.is_dir():
        raise ValueError(f"Codex workspace fixture is unavailable: {CODEX_WORKSPACE_FIXTURE_ROOT}")
    shutil.copytree(CODEX_WORKSPACE_FIXTURE_ROOT, workspace, dirs_exist_ok=True)


def find_eval_file(skill: str) -> pathlib.Path:
    """A Codex run reads only its own eval set: the Claude set names host-specific skills."""
    path = TESTS_ROOT / "layer2-trigger/codex-evals" / f"{skill}-trigger.json"
    if not path.is_file():
        available = ", ".join(evidence_records.available_evals(path.parent)) or "none"
        sys.exit(f"ERROR: no Codex eval file for skill '{skill}' at {path}; available: {available}")
    return path


def find_skill_source(skill: str) -> pathlib.Path:
    p = PLUGIN_ROOT / "codex-skills" / skill / "SKILL.md"
    if not p.exists():
        sys.exit(f"ERROR: codex skill not found at {p}")
    return p


def stage_skill_with_marker(src: pathlib.Path, dst_dir: pathlib.Path, new_name: str, marker: str) -> None:
    """Stage the exact source description with a minimal attested-selection body."""
    text = src.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        sys.exit(f"ERROR: no YAML frontmatter found in {src}")
    fm_body = m.group(1)

    fm_lines = [
        f"name: {new_name}" if ln.startswith("name:") else ln
        for ln in fm_body.split("\n")
    ]
    fm = "\n".join(fm_lines)

    dst_dir.mkdir(parents=True, exist_ok=True)
    (dst_dir / "SKILL.md").write_text(
        f"---\n{fm}\n---\n\n{selection_stub(marker)}",
        encoding="utf-8",
    )


def stage_repository_skill(
    src: pathlib.Path,
    workspace: pathlib.Path,
    new_name: str,
    marker: str,
) -> pathlib.Path:
    """Stage one uniquely named skill at Codex's documented repository scope."""
    destination = workspace / ".agents" / "skills" / new_name
    stage_skill_with_marker(src, destination, new_name, marker)
    return destination


sibling_skill_dirs = evidence_records.sibling_skill_dirs


def stage_sibling_skills(
    src: pathlib.Path,
    workspace: pathlib.Path,
    test_id: str,
    *,
    no_op_description: str | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    """Stage every sibling with its source description and unique attestation.

    A sibling selection remains a valid target non-selection. Its own marker makes
    the selected identity observable and keeps target-plus-sibling ambiguity invalid.
    """
    siblings: dict[str, str] = {}
    markers: dict[str, str] = {}
    for sibling in sibling_skill_dirs(src):
        skill_file = sibling / "SKILL.md"
        m = re.match(r"^---\n(.*?)\n---\n", skill_file.read_text(), re.S)
        if not m:
            raise ValueError(f"no YAML frontmatter found in sibling skill {skill_file}")
        destination = workspace / ".agents" / "skills" / sibling.name
        destination.mkdir(parents=True, exist_ok=False)
        marker = selection_marker(sibling.name, test_id)
        (destination / "SKILL.md").write_text(
            f"---\n{m.group(1)}\n---\n\n"
            f"{selection_stub(marker)}",
            encoding="utf-8",
        )
        siblings[sibling.name] = source_skill_description(destination / "SKILL.md")
        markers[sibling.name] = marker
        if siblings[sibling.name] != source_skill_description(skill_file):
            raise ValueError(f"staged sibling description differs from its source: {sibling.name}")
    if NO_SPECKIT_SKILL_NAME in siblings:
        raise ValueError(f"reserved sibling skill name: {NO_SPECKIT_SKILL_NAME}")
    description = NO_SPECKIT_SKILL_DESCRIPTION if no_op_description is None else no_op_description
    destination = workspace / ".agents" / "skills" / NO_SPECKIT_SKILL_NAME
    destination.mkdir(parents=True, exist_ok=False)
    marker = selection_marker(NO_SPECKIT_SKILL_NAME, test_id)
    (destination / "SKILL.md").write_text(
        f"---\nname: {NO_SPECKIT_SKILL_NAME}\n"
        f"description: {description}\n---\n\n"
        f"{selection_stub(marker)}",
        encoding="utf-8",
    )
    siblings[NO_SPECKIT_SKILL_NAME] = description
    markers[NO_SPECKIT_SKILL_NAME] = marker
    return siblings, markers


def source_skill_description(skill_file: pathlib.Path) -> str:
    """Return the model-visible YAML description for supported repository skills."""
    lines = skill_file.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"source skill has no YAML frontmatter: {skill_file}")
    for index, line in enumerate(lines[1:], start=1):
        if line == "---":
            break
        if not line.startswith("description:"):
            continue
        value = line.removeprefix("description:").strip()
        if value in {">", ">-", "|", "|-"}:
            block: list[str] = []
            for continuation in lines[index + 1 :]:
                if continuation == "":
                    block.append("")
                    continue
                if not continuation.startswith((" ", "\t")):
                    break
                block.append(continuation.strip())
            description = (
                " ".join(part for part in block if part)
                if value.startswith(">")
                else "\n".join(block)
            )
        elif len(value) >= 2 and value[0] == value[-1] == '"':
            try:
                description = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError(f"source skill has an invalid quoted description: {skill_file}") from exc
        elif len(value) >= 2 and value[0] == value[-1] == "'":
            description = value[1:-1].replace("''", "'")
        else:
            description = value
        if not description.strip():
            raise ValueError(f"source skill has an empty description: {skill_file}")
        return description.strip()
    raise ValueError(f"source skill has no description: {skill_file}")


def skill_source_roots() -> tuple[pathlib.Path, ...]:
    """Return documented host skill roots without reading user configuration."""
    home = pathlib.Path.home()
    codex_home_value = os.environ.get("CODEX_HOME")
    if codex_home_value is not None and not codex_home_value.strip():
        raise ValueError("CODEX_HOME is empty")
    codex_home = pathlib.Path(codex_home_value).expanduser() if codex_home_value else home / ".codex"
    if not codex_home.is_absolute():
        raise ValueError("CODEX_HOME must be absolute")
    return home / ".agents" / "skills", codex_home / "skills", pathlib.Path("/etc/codex/skills")


_canonical_skill_files = codex_isolation.canonical_skill_files


def enumerate_non_target_skills(target_skill: pathlib.Path) -> tuple[pathlib.Path, ...]:
    """Build a fresh canonical deny list for every non-target host skill."""
    target = target_skill.resolve(strict=True)
    discovered: set[pathlib.Path] = set()
    for root in skill_source_roots():
        discovered.update(_canonical_skill_files(root))
    discovered.discard(target)
    return tuple(sorted(discovered, key=str))


def codex_environment(workspace: pathlib.Path | None = None) -> dict[str, str]:
    """Keep login in CODEX_HOME and shell HOME on the staged workspace."""
    environment = {
        key: os.environ[key]
        for key in ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE", "USER", "CODEX_HOME")
        if key in os.environ
    }
    if workspace is None:
        return environment
    codex_home = environment.get("CODEX_HOME")
    if codex_home is None:
        home = environment.get("HOME")
        if home is None:
            raise ValueError("Codex login home is unavailable")
        codex_home = str(pathlib.Path(home) / ".codex")
    runtime_home = workspace.resolve() / ".codex-trigger-runtime"
    runtime_tmp = runtime_home / "tmp"
    runtime_tmp.mkdir(parents=True, exist_ok=True)
    environment.update(
        CODEX_HOME=codex_home,
        HOME=str(workspace.resolve()),
        TMPDIR=str(runtime_tmp),
    )
    return environment


def codex_executable() -> str:
    """Avoid a PATH symlink the fixture sandbox cannot execute for its own helper."""
    executable = shutil.which("codex")
    return str(pathlib.Path(executable).resolve()) if executable else "codex"


def codex_provider_args() -> list[str]:
    """Pin the first-party provider transport with every model retry disabled."""
    return [
        "-c", f'model_provider="{MODEL_PROVIDER_ID}"',
        "-c", f'model_providers.{MODEL_PROVIDER_ID}.name={json.dumps(MODEL_PROVIDER_NAME)}',
        "-c", f'model_providers.{MODEL_PROVIDER_ID}.base_url={json.dumps(MODEL_PROVIDER_BASE_URL)}',
        "-c", f'model_providers.{MODEL_PROVIDER_ID}.wire_api="responses"',
        "-c", f"model_providers.{MODEL_PROVIDER_ID}.requires_openai_auth=true",
        "-c", f"model_providers.{MODEL_PROVIDER_ID}.request_max_retries=0",
        "-c", f"model_providers.{MODEL_PROVIDER_ID}.stream_max_retries=0",
        "-c", f"model_providers.{MODEL_PROVIDER_ID}.supports_websockets=false",
    ]


def cli_preflight() -> tuple[dict[str, object] | None, str]:
    """Require the exact Codex build whose selection and retry surfaces were qualified."""
    command = [codex_executable(), "--version"]
    try:
        completed = subprocess.run(
            command,
            executable=shutil.which("codex", path=str(pathlib.Path(command[0]).parent)),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=codex_environment(),
            shell=False,
            check=False,
        )
        version = completed.stdout.decode("utf-8", errors="strict").strip()
    except (OSError, UnicodeDecodeError) as exc:
        return None, f"Codex version preflight could not run: {exc}"
    if completed.returncode != 0 or version != PINNED_CODEX_VERSION:
        return None, f"Codex version is not qualified: {version or 'unavailable'}"
    return {
        "version": version,
        "model_provider": MODEL_PROVIDER_ID,
        "request_max_retries": 0,
        "stream_max_retries": 0,
        "supports_websockets": False,
        "unbounded_connection_retries": False,
    }, "Codex CLI preflight passed"


def skill_witnesses(
    workspace: pathlib.Path,
    markers: dict[str, str],
) -> dict[str, dict[str, str]]:
    """Freeze the exact staged body and identity behind each randomized marker."""
    root = workspace / ".agents" / "skills"
    witnesses: dict[str, dict[str, str]] = {}
    for name, marker in sorted(markers.items()):
        path = (root / name / "SKILL.md").resolve(strict=True)
        body = path.read_text(encoding="utf-8")
        if body.count(marker) != 1:
            raise ValueError(f"staged selection marker is not unique in {name}")
        witnesses[name] = {
            "marker": marker,
            "path": str(path),
            "relative_path": path.relative_to(workspace.resolve()).as_posix(),
            "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "body": body,
        }
    return witnesses


def _proved_catalog_aliases(
    workspace: pathlib.Path,
    witnesses: dict[str, dict[str, str]],
    source_locators: dict[str, str],
) -> set[str]:
    """Validate catalog locators against every frozen staged witness."""
    if set(source_locators) != set(witnesses):
        raise ValueError("Codex catalog source locators do not match staged witnesses")
    skill_root = (workspace.resolve(strict=True) / ".agents" / "skills").resolve(strict=True)
    aliases: set[str] = set()
    absolute_count = 0
    for skill_name, witness in witnesses.items():
        if not skill_name or skill_name in {".", ".."} or "/" in skill_name or "\\" in skill_name:
            raise ValueError("Codex catalog skill name cannot form a confined locator")
        locator = source_locators[skill_name]
        if not isinstance(locator, str):
            raise ValueError("Codex catalog source locator is not text")
        witness_path = pathlib.Path(witness["path"]).resolve(strict=True)
        if witness_path != (skill_root / skill_name / "SKILL.md").resolve(strict=True):
            raise ValueError("Codex catalog alias would not resolve to the witnessed skill")
        if pathlib.Path(locator).is_absolute():
            absolute_count += 1
            if pathlib.Path(locator) != witness_path:
                raise ValueError("Codex catalog absolute locator differs from its witness")
            continue
        alias = _catalog_locator_alias(locator, skill_name)
        if alias is None:
            raise ValueError("Codex catalog skill-root locator is malformed")
        aliases.add(alias)
    if aliases and (len(aliases) != 1 or absolute_count):
        raise ValueError("Codex catalog source locators do not share one relative root alias")
    return aliases


def _bind_catalog_skill_root_alias(
    workspace: pathlib.Path,
    witnesses: dict[str, dict[str, str]],
    source_locators: dict[str, str],
) -> None:
    """Make the catalog's proved root alias resolve inside the disposable workspace."""
    workspace_root = workspace.resolve(strict=True)
    skill_root = (workspace_root / ".agents" / "skills").resolve(strict=True)
    aliases = _proved_catalog_aliases(workspace, witnesses, source_locators)
    if not aliases:
        return
    alias = next(iter(aliases))
    alias_path = workspace_root / alias
    if alias_path.exists() or alias_path.is_symlink():
        raise ValueError("Codex catalog skill-root alias path already exists")
    alias_path.symlink_to(".agents/skills", target_is_directory=True)
    if alias_path.resolve(strict=True) != skill_root:
        raise ValueError("Codex catalog skill-root alias escaped its staged root")
    for skill_name, locator in source_locators.items():
        witnesses[skill_name]["source_locator"] = locator


def _attest_catalog_skill_root_alias(
    workspace: pathlib.Path,
    witnesses: dict[str, dict[str, str]],
) -> None:
    """Fail closed if the catalog-derived alias changed after preflight."""
    locators = {
        name: witness.get("source_locator")
        for name, witness in witnesses.items()
        if witness.get("source_locator") is not None
    }
    if not locators:
        return
    try:
        aliases = {
            _catalog_locator_alias(locator, name)
            for name, locator in locators.items()
            if isinstance(locator, str)
        }
        aliases.discard(None)
        if len(locators) != len(witnesses) or len(aliases) != 1:
            raise ValueError
        alias_path = workspace.resolve(strict=True) / next(iter(aliases))
        skill_root = (workspace / ".agents" / "skills").resolve(strict=True)
        if not alias_path.is_symlink() or os.readlink(alias_path) != ".agents/skills":
            raise ValueError
        if alias_path.resolve(strict=True) != skill_root:
            raise ValueError
        for name, locator in locators.items():
            if (workspace / locator).resolve(strict=True) != pathlib.Path(witnesses[name]["path"]):
                raise ValueError
    except (OSError, RuntimeError, TypeError, ValueError):
        raise ValueError("Codex catalog skill-root alias changed after catalog preflight") from None


def fixture_permission_args(workspace: pathlib.Path) -> list[str]:
    """Use the reviewed native fixture-only policy, without legacy sandbox flags."""
    return codex_isolation.fixture_permission_args(
        "trigger-fixture", workspace, writable=(workspace.resolve() / ".codex-trigger-runtime",),
    )


def enumerate_mcp_servers(workspace: pathlib.Path, timeout: int) -> tuple[str, ...]:
    """Read configured names locally; never initialize servers or retain their config."""
    command = codex_isolation.mcp_list_command(codex_executable(), fixture_permission_args(workspace))
    return codex_isolation.read_mcp_server_names(
        command, cwd=workspace, env=codex_environment(), timeout=timeout,
    )


skill_isolation_args = codex_isolation.skill_isolation_args


def offline_catalog_preflight(
    workspace: pathlib.Path,
    target_name: str,
    target_description: str,
    target_skill: pathlib.Path,
    isolation_args: list[str],
    timeout: int,
    siblings: dict[str, str] | None = None,
) -> tuple[dict[str, object] | None, str]:
    """Render the catalog offline with matching supported session overrides."""
    command = [
        codex_executable(), "debug", "prompt-input",
        *fixture_permission_args(workspace), *isolation_args,
    ]
    try:
        completed = subprocess.run(
            command,
            executable=shutil.which("codex", path=str(pathlib.Path(command[0]).parent)),
            cwd=workspace,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            timeout=timeout,
            env=codex_environment(),
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "Codex catalog preflight timed out"
    except OSError as exc:
        return None, f"Codex catalog preflight could not run: {exc}"
    if completed.returncode != 0:
        return None, f"Codex catalog preflight exited {completed.returncode}"
    return inspect_catalog_prompt(
        completed.stdout,
        target_name,
        target_description,
        target_skill,
        workspace,
        siblings,
    )


def retain_run_evidence(
    evidence_dir: pathlib.Path,
    case_number: int,
    run_number: int,
    output: bytes,
    error_output: bytes,
) -> dict[str, str]:
    """Persist the exact provider streams and return immutable path/digest evidence."""
    kept = evidence_records.retain_trial_evidence(evidence_dir, case_number, run_number, output, error_output)
    return {
        "jsonl_path": kept["stdout_path"],
        "jsonl_sha256": kept["stdout_sha256"],
        "stderr_path": kept["stderr_path"],
        "stderr_sha256": kept["stderr_sha256"],
    }


def remove_workspace(workspace: pathlib.Path) -> str | None:
    """Remove the staged repository and fail loud if any residue remains."""
    try:
        shutil.rmtree(workspace)
    except OSError as exc:
        return f"could not remove disposable eval repository {workspace}: {exc}"
    if workspace.exists():
        return f"disposable eval repository cleanup left residue at {workspace}"
    return None


def case_passes(
    should_trigger: bool,
    triggers: int,
    runs: int,
    threshold: float,
    invalid_runs: int,
) -> bool:
    """Score a case only when every provider run completed truthfully."""
    if runs <= 0 or invalid_runs != 0:
        return False
    return ((triggers / runs) >= threshold) == should_trigger


def _codex_launch_contract(
    cmd: list[str],
    model: str,
    reasoning: str,
    environment: dict[str, str],
    workspace: pathlib.Path,
) -> dict[str, object]:
    config_values = {
        cmd[index + 1]
        for index, argument in enumerate(cmd[:-1])
        if argument == "-c"
    }
    disabled_features = {
        cmd[index + 1]
        for index, argument in enumerate(cmd[:-1])
        if argument == "--disable"
    }
    runtime_home = workspace.resolve() / ".codex-trigger-runtime"
    return {
        "config_isolated": "--strict-config" in cmd and "--ignore-user-config" in cmd,
        "retries_disabled": {
            f"model_providers.{MODEL_PROVIDER_ID}.request_max_retries=0",
            f"model_providers.{MODEL_PROVIDER_ID}.stream_max_retries=0",
            f"model_providers.{MODEL_PROVIDER_ID}.supports_websockets=false",
        }.issubset(config_values)
        and "unbounded_connection_retries" in disabled_features,
        "requested_model": model,
        "reasoning_effort": reasoning,
        "model_provider": MODEL_PROVIDER_ID,
        "model_identity_evidence": "request-only",
        "stdin_prompt_isolated": True,
        "stdin_mode": "pseudo-terminal" if os.name != "nt" else "null-device",
        "login_state_source": "CODEX_HOME" if environment.get("CODEX_HOME") else None,
        "shell_home_isolated": environment.get("HOME") == str(workspace.resolve()),
        "scratch_directory_isolated": environment.get("TMPDIR") == str(runtime_home / "tmp")
        and (runtime_home / "tmp").is_dir(),
    }


def _codex_stdin_source() -> tuple[int, int | None, int | None]:
    if os.name == "nt":
        return subprocess.DEVNULL, None, None
    terminal_master, terminal_slave = os.openpty()
    if os.isatty(terminal_slave):
        return terminal_slave, terminal_master, terminal_slave
    os.close(terminal_master)
    os.close(terminal_slave)
    raise RuntimeError("Codex stdin pseudo-terminal setup failed")


def run_codex_query(
    workspace: pathlib.Path,
    query: str,
    reasoning: str,
    model: str,
    timeout: int,
    isolation_args: list[str],
    *, process_evidence: dict[str, object] | None = None,
) -> tuple[int, bytes, bytes, bool]:
    cmd = [
        codex_executable(), "exec", "--strict-config",
        "--cd", str(workspace),
        *fixture_permission_args(workspace),
        "--ephemeral",
        "--ignore-user-config",
        "--json",
        "-m", model,
        "-c", f'model_reasoning_effort="{reasoning}"',
        *codex_provider_args(),
    ]
    cmd.extend(isolation_args)
    cmd.append(query)
    env = codex_environment(workspace)
    if process_evidence is not None:
        process_evidence["launch_contract"] = _codex_launch_contract(
            cmd, model, reasoning, env, workspace,
        )
        process_evidence["launch_contract"]["query_sha256"] = hashlib.sha256(query.encode()).hexdigest()
    stdin_source, terminal_master, terminal_slave = _codex_stdin_source()
    try:
        child = subprocess.Popen(
            cmd,
            executable=shutil.which("codex", path=str(pathlib.Path(cmd[0]).parent)),
            cwd=workspace,
            stdin=stdin_source,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            shell=False,
            start_new_session=os.name != "nt",
        )
        if terminal_slave is not None:
            os.close(terminal_slave)
            terminal_slave = None
        return processes.supervise_child(
            child, timeout, cleanup=processes.cleanup_child, evidence=process_evidence,
        )
    finally:
        for descriptor in (terminal_slave, terminal_master):
            if descriptor is not None:
                os.close(descriptor)


def print_case_result(case_number: int, case_count: int, result: dict[str, object]) -> None:
    if result["status"] == "not_run":
        print(f"  [{case_number:2d}/{case_count}] NOT RUN  {result['query'][:70]}", file=sys.stderr)
        return
    expect = "TRIG" if result["should_trigger"] else "NOOP"
    mark = "PASS" if result["pass"] else "FAIL"
    print(
        f"  [{case_number:2d}/{case_count}] expect={expect} trig={result['triggers']}/{result['runs']} "
        f"invalid={result['invalid_runs']} {mark}  {result['query'][:70]}", file=sys.stderr,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("skill", help="Codex skill name (looked up under codex-skills/)")
    ap.add_argument("--runs", type=int, default=3, help="Trials per query (default 3)")
    ap.add_argument("--limit", type=int, help="Only run the first N queries from the eval set")
    ap.add_argument(
        "--reasoning",
        default=DEFAULT_REASONING_EFFORT,
        help=f"codex model_reasoning_effort (default: {DEFAULT_REASONING_EFFORT})",
    )
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"Codex model id (default: {DEFAULT_MODEL})")
    ap.add_argument("--threshold", type=float, default=0.5, help="Trigger-rate threshold for pass (default 0.5)")
    ap.add_argument("--timeout", type=int, default=180, help="Per-query timeout seconds (default 180)")
    ap.add_argument("--out", help="Write detailed JSON results to this file")
    ap.add_argument("--evidence-dir", help="Directory for exact per-trial JSONL and stderr evidence")
    ap.add_argument("--case-id", help="Run exactly this stable case identity; keeps all three trials")
    ap.add_argument("--no-op-description-file", help="Frozen single-line controlled experiment description")
    args = ap.parse_args()

    eval_file = find_eval_file(args.skill)
    skill_src = find_skill_source(args.skill)
    eval_data, corpus_reason = load_eval_corpus(eval_file)
    if eval_data is None:
        sys.exit(f"ERROR: {corpus_reason}")
    try:
        eval_data = evidence_records.select_case("codex", args.skill, eval_data, args.case_id)
        no_op_description = evidence_records.description_override(args.no_op_description_file, NO_SPECKIT_SKILL_DESCRIPTION)
    except (OSError, ValueError) as exc:
        sys.exit(f"ERROR: {exc}")
    if args.runs <= 0 or not 0.0 <= args.threshold <= 1.0:
        sys.exit("ERROR: --runs must be positive and --threshold must be between 0 and 1")
    if args.timeout <= 0:
        sys.exit("ERROR: --timeout must be positive")
    if args.limit is not None and args.limit <= 0:
        sys.exit("ERROR: --limit must be positive")
    if args.limit is not None:
        eval_data = eval_data[: args.limit]
    if args.out and pathlib.Path(args.out).exists():
        sys.exit("ERROR: --out already exists; previous reports are immutable")

    if shutil.which("codex") is None:
        sys.exit("ERROR: codex CLI not on PATH")

    test_uuid = uuid.uuid4().hex
    test_skill_name = f"{args.skill}-eval-{test_uuid}"
    marker = selection_marker(test_skill_name, test_uuid)

    if args.evidence_dir:
        evidence_dir = pathlib.Path(args.evidence_dir).resolve()
        evidence_dir.mkdir(parents=True, exist_ok=False)
    else:
        evidence_dir = pathlib.Path(tempfile.mkdtemp(prefix=f"codex-eval-evidence-{args.skill}-"))
    workspace = pathlib.Path(tempfile.mkdtemp(prefix=f"codex-eval-{args.skill}-"))
    exit_code = 1
    previous_handlers = processes.install_termination_handlers()
    try:
        initialized = subprocess.run(
            ["git", "init", "--quiet"],
            cwd=workspace,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            check=False,
        )
        if initialized.returncode != 0:
            raise ValueError(f"could not initialize disposable eval repository: {initialized.stderr.strip()}")
        stage_workspace_fixture(workspace)
        skill_dir = stage_repository_skill(skill_src, workspace, test_skill_name, marker)
        target_skill = skill_dir / "SKILL.md"
        target_description = source_skill_description(skill_src)
        if source_skill_description(target_skill) != target_description:
            raise ValueError("staged Codex skill description differs from its source")
        siblings, sibling_markers = stage_sibling_skills(
            skill_src, workspace, test_uuid, no_op_description=no_op_description,
        )
        witnesses = skill_witnesses(
            workspace,
            {test_skill_name: marker, **sibling_markers},
        )
        disabled_skills = enumerate_non_target_skills(target_skill)
        disabled_mcp_servers = enumerate_mcp_servers(workspace, args.timeout)
        isolation_args = skill_isolation_args(disabled_skills, disabled_mcp_servers)
        catalog_args = skill_isolation_args(disabled_skills, disabled_mcp_servers, ignore_user_config=False)
        readiness, readiness_reason = offline_catalog_preflight(
            workspace,
            test_skill_name,
            target_description,
            target_skill,
            catalog_args,
            args.timeout,
            siblings,
        )
        if readiness is None:
            raise ValueError(readiness_reason)
        source_locators = readiness.get("skill_source_locators")
        if not isinstance(source_locators, dict):
            raise ValueError("Codex catalog preflight omitted proved source locators")
        _bind_catalog_skill_root_alias(workspace, witnesses, source_locators)
        preflight, preflight_reason = cli_preflight()
        if preflight is None:
            raise ValueError(preflight_reason)
        canonical_parameters = (
            args.runs == QUALIFIED_RUNS
            and args.threshold == QUALIFIED_THRESHOLD
            and args.reasoning == DEFAULT_REASONING_EFFORT
            and args.model == DEFAULT_MODEL
        )

        print(f"Codex Layer 2 trigger eval: {args.skill}", file=sys.stderr)
        print(f"  Eval file:  {eval_file}", file=sys.stderr)
        print(f"  Skill src:  {skill_src}", file=sys.stderr)
        print(f"  Test skill: {test_skill_name}", file=sys.stderr)
        print(f"  Workspace:  {workspace}", file=sys.stderr)
        print(f"  Evidence:   {evidence_dir}", file=sys.stderr)
        print("  Login:      existing Codex session (credential files are not copied)", file=sys.stderr)
        print(f"  Queries:    {len(eval_data)} (x{args.runs} runs)", file=sys.stderr)
        print(f"  Reasoning:  {args.reasoning}", file=sys.stderr)
        print(f"  Model:      {args.model}", file=sys.stderr)
        print(
            f"  Catalog:    one attested target plus {len(siblings)} attested sibling skills, "
            "each with its exact source description",
            file=sys.stderr,
        )
        print("", file=sys.stderr)

        def launch(query: str, execution: dict[str, object]):
            _attest_catalog_skill_root_alias(workspace, witnesses)
            if enumerate_non_target_skills(target_skill) != disabled_skills:
                raise ValueError("Codex skill roots changed after catalog preflight")
            if enumerate_mcp_servers(workspace, args.timeout) != disabled_mcp_servers:
                raise ValueError("Codex MCP inventory changed after catalog preflight")
            return run_codex_query(
                workspace, query, args.reasoning, args.model, args.timeout, isolation_args,
                process_evidence=execution,
            )

        batch = evidence_records.TrialBatch(
            "codex", args.skill, evidence_dir, args.runs, args.threshold,
            qualification_eligible=canonical_parameters,
        )
        replay_context = {"host": "codex", "target_skill": test_skill_name, "witnesses": witnesses,
                          "requested_model": args.model, "workspace": str(workspace.resolve()),
                          "source_skill": args.skill, "no_op_description": no_op_description}
        input_snapshot = experiment_evidence.measurement_snapshot()
        evidence_records.write_json_once(evidence_dir / "replay-context.json", replay_context)
        results, stop_exit = evidence_records.run_trials(
            batch, eval_data, launch,
            lambda stdout: inspect_codex_jsonl(
                stdout, test_skill_name, witnesses, requested_model=args.model,
            ),
            lambda case, trial, stdout, stderr: retain_run_evidence(evidence_dir, case, trial, stdout, stderr),
            progress=lambda case, result: print_case_result(case, len(eval_data), result),
        )
        if experiment_evidence.measurement_snapshot() != input_snapshot:
            raise ValueError("public measurement inputs changed during native execution")
        passed = sum(result["pass"] is True for result in results)
        failed = sum(result["pass"] is False for result in results)
        if stop_exit is not None and stop_exit >= 128:
            print(f"Termination requested by signal {stop_exit - 128}; terminating owned child and cleaning temporary workspace.", file=sys.stderr)

        resolved_models = [
            evidence.get("resolved_model")
            for result in results
            for evidence in result["selection_evidence"]
        ]
        resolved_model = (
            resolved_models[0]
            if resolved_models
            and all(model == resolved_models[0] and isinstance(model, str) for model in resolved_models)
            else None
        )
        summary = {
            "skill": args.skill,
            "total": len(eval_data),
            "passed": passed,
            "failed": failed,
            "complete": all(result["status"] == "complete" for result in results),
            "not_run": sum(result["status"] == "not_run" for result in results),
            "pass_rate": round(passed / len(eval_data), 3) if eval_data else 0.0,
            "runs_per_query": args.runs,
            "reasoning": args.reasoning,
            "requested_model": args.model,
            "qualification_eligible": canonical_parameters
            and all(result["status"] == "complete" for result in results)
            and all(
                trial["qualification_eligible"] is True
                for result in results
                for trial in result["selection_evidence"]
            ),
            "resolved_model": resolved_model,
        }

        report = {
            "metadata": {
                "trial_timeout_seconds": args.timeout,
                "input_snapshot": input_snapshot,
                "replay_context": replay_context,
                "no_op_description_sha256": hashlib.sha256(no_op_description.encode()).hexdigest(),
                "preflight": preflight,
                "catalog_preflight": readiness,
                "selection_observation": "codex-body-read-attestation",
                "selection_witnesses": witnesses,
            },
            "summary": summary,
            "results": results,
        }
        print("", file=sys.stderr)
        print("===========================", file=sys.stderr)
        print(f"Codex Trigger Eval: {args.skill}", file=sys.stderr)
        print(f"  PASSED: {passed}/{len(eval_data)} ({summary['pass_rate']*100:.0f}%)", file=sys.stderr)
        print(f"  FAILED: {failed}/{len(eval_data)}", file=sys.stderr)
        print("===========================", file=sys.stderr)

        if args.out:
            evidence_records.write_json_once(pathlib.Path(args.out), report)
            print(f"Wrote detailed results to: {args.out}", file=sys.stderr)

        print(json.dumps(report, indent=2))
        exit_code = stop_exit if stop_exit is not None else 0 if failed == 0 else 1
    except (processes.TerminationRequested, KeyboardInterrupt) as exc:
        signum = exc.signum if isinstance(exc, processes.TerminationRequested) else signal.SIGINT
        exit_code = 128 + signum
        print(f"Termination requested by signal {signum}; cleaning owned workspace.", file=sys.stderr)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        exit_code = 1
    finally:
        cleanup_error = remove_workspace(workspace)
        if cleanup_error is not None:
            print(f"ERROR: {cleanup_error}", file=sys.stderr)
            exit_code = 2
        processes.restore_termination_handlers(previous_handlers)
        try:
            evidence_records.retain_cleanup_receipt(evidence_dir, workspace, exit_code, cleanup_error)
        except OSError as exc:
            print(f"ERROR: cannot retain workspace cleanup receipt: {exc}", file=sys.stderr)
            exit_code = 2
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

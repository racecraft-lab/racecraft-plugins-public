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
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import uuid


# Tests live at <repo>/tests/speckit-pro/; the plugin is the sibling <repo>/speckit-pro/.
TESTS_ROOT = pathlib.Path(__file__).resolve().parents[1]      # <repo>/tests/speckit-pro
SHARED_LIB = TESTS_ROOT / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))
import trigger_process as processes  # noqa: E402
import trigger_evidence as evidence_records  # noqa: E402

PLUGIN_ROOT = TESTS_ROOT.parents[1] / "speckit-pro"           # <repo>/speckit-pro
DEFAULT_REASONING_EFFORT = "low"
DEFAULT_MODEL = "gpt-5.6-sol"
PINNED_CODEX_VERSION = "codex-cli 0.153.3"
QUALIFIED_RUNS = 3
QUALIFIED_THRESHOLD = 0.5
MODEL_PROVIDER_ID = "layer2_openai_no_retry"
MODEL_PROVIDER_NAME = "OpenAI Layer 2 no-retry"
MODEL_PROVIDER_BASE_URL = "https://chatgpt.com/backend-api/codex"
DISABLED_FEATURES = (
    "plugins", "apps", "browser_use", "computer_use", "hooks",
    "skill_mcp_dependency_install", "memories", "unbounded_connection_retries",
)
MARKER_PATTERN = re.compile(r"CODEX_SKILL_SELECTED:[A-Za-z0-9_-]+")
SKILL_CATALOG_WARNINGS = (
    "Skill descriptions were shortened to fit the skills context budget.",
    "Exceeded skills context budget.",
)
NO_SPECKIT_SKILL_NAME = "no-speckit-skill"
NO_SPECKIT_SKILL_DESCRIPTION = (
    "Use when no available SpecKit skill covers the request, including ordinary coding, testing, tooling, or "
    "repository work and host-specific SpecKit operations whose matching skill is absent from the current catalog, "
    "such as installing Codex subagents when no agent-install skill is available or running the plan stage for an "
    "already-existing spec or populated workflow when no planning skill is available. Reply that no available "
    "SpecKit skill applies and stop."
)
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


def load_eval_corpus(path: pathlib.Path) -> tuple[list[dict[str, object]] | None, str]:
    """Load a complete trigger corpus before any provider subprocess can run."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"could not read eval file: {exc}"
    if not isinstance(value, list):
        return None, "eval file must contain a JSON list"
    if not value:
        return None, "eval file must contain at least one case"
    seen_queries: set[str] = set()
    for index, entry in enumerate(value, start=1):
        if not isinstance(entry, dict):
            return None, f"eval case {index} must be an object"
        query = entry.get("query")
        should_trigger = entry.get("should_trigger")
        if not isinstance(query, str) or not query.strip() or not isinstance(should_trigger, bool):
            return None, f"eval case {index} requires a non-empty query and boolean should_trigger"
        if query in seen_queries:
            return None, f"eval case {index} duplicates query {query!r}"
        seen_queries.add(query)
    return value, "valid eval corpus"


def find_eval_file(skill: str) -> pathlib.Path:
    codex_specific = TESTS_ROOT / "layer2-trigger/codex-evals" / f"{skill}-trigger.json"
    shared = TESTS_ROOT / "layer2-trigger/evals" / f"{skill}-trigger.json"
    if codex_specific.exists():
        return codex_specific
    if shared.exists():
        return shared
    sys.exit(f"ERROR: no eval file for skill '{skill}' (tried {codex_specific}, {shared})")


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


SKILL_ROOT_NAMES = frozenset({"codex-skills", "skills"})


def sibling_skill_dirs(src: pathlib.Path) -> list[pathlib.Path]:
    """List sibling skill directories beside ``src``'s skill directory.

    Only a plugin skills root (``codex-skills`` or ``skills``) is walked; a
    source staged elsewhere, such as a temporary file in a test, has no
    siblings. Entries that cannot be inspected are skipped rather than raised,
    because shared temp roots hold directories owned by other users.
    """
    root = src.parent.parent
    if root.name not in SKILL_ROOT_NAMES:
        return []
    siblings: list[pathlib.Path] = []
    for sibling in sorted(root.iterdir(), key=lambda path: path.name):
        if sibling == src.parent:
            continue
        try:
            if sibling.is_dir() and (sibling / "SKILL.md").is_file():
                siblings.append(sibling)
        except OSError:
            continue
    return siblings


def stage_sibling_skills(
    src: pathlib.Path,
    workspace: pathlib.Path,
    test_id: str,
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
    destination = workspace / ".agents" / "skills" / NO_SPECKIT_SKILL_NAME
    destination.mkdir(parents=True, exist_ok=False)
    marker = selection_marker(NO_SPECKIT_SKILL_NAME, test_id)
    (destination / "SKILL.md").write_text(
        f"---\nname: {NO_SPECKIT_SKILL_NAME}\n"
        f"description: {NO_SPECKIT_SKILL_DESCRIPTION}\n---\n\n"
        f"{selection_stub(marker)}",
        encoding="utf-8",
    )
    siblings[NO_SPECKIT_SKILL_NAME] = NO_SPECKIT_SKILL_DESCRIPTION
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


def _canonical_skill_files(root: pathlib.Path) -> set[pathlib.Path]:
    """Enumerate one root, following symlinked directories without allowing cycles."""
    try:
        root_status = root.stat()
    except FileNotFoundError:
        return set()
    except OSError as exc:
        raise OSError(f"could not inspect Codex skill root {root}: {exc}") from exc
    if not stat.S_ISDIR(root_status.st_mode):
        raise ValueError(f"Codex skill root is not a directory: {root}")

    pending = [root.resolve(strict=True)]
    visited: set[tuple[int, int]] = set()
    skills: set[pathlib.Path] = set()
    while pending:
        directory = pending.pop()
        try:
            canonical_directory = directory.resolve(strict=True)
            directory_status = canonical_directory.stat()
            identity = (directory_status.st_dev, directory_status.st_ino)
            if identity in visited:
                continue
            visited.add(identity)
            with os.scandir(canonical_directory) as entries:
                children = list(entries)
        except OSError as exc:
            raise OSError(f"could not inspect Codex skill root {directory}: {exc}") from exc
        for entry in children:
            try:
                if entry.name == "SKILL.md":
                    if not entry.is_file(follow_symlinks=True):
                        raise ValueError(f"Codex skill path is not a file: {entry.path}")
                    skills.add(pathlib.Path(entry.path).resolve(strict=True))
                elif entry.is_dir(follow_symlinks=True):
                    pending.append(pathlib.Path(entry.path))
            except OSError as exc:
                raise OSError(f"could not inspect Codex skill path {entry.path}: {exc}") from exc
    return skills


def enumerate_non_target_skills(target_skill: pathlib.Path) -> tuple[pathlib.Path, ...]:
    """Build a fresh canonical deny list for every non-target host skill."""
    target = target_skill.resolve(strict=True)
    discovered: set[pathlib.Path] = set()
    for root in skill_source_roots():
        discovered.update(_canonical_skill_files(root))
    discovered.discard(target)
    return tuple(sorted(discovered, key=str))


def codex_environment() -> dict[str, str]:
    """Keep the existing login location, not unrelated service credentials."""
    return {
        key: os.environ[key]
        for key in ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE", "USER", "CODEX_HOME")
        if key in os.environ
    }


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


def fixture_permission_args(workspace: pathlib.Path) -> list[str]:
    """Use the reviewed native fixture-only policy, without legacy sandbox flags."""
    return [
        "-c", 'default_permissions="trigger-fixture"',
        "-c", 'permissions.trigger-fixture.filesystem={":root"="deny",":minimal"="read",'
        + json.dumps(str(workspace.resolve())) + '="read"}',
        "-c", "permissions.trigger-fixture.network.enabled=false",
        "-c", 'approval_policy="never"',
        "-c", "allow_login_shell=false",
    ]


def enumerate_mcp_servers(workspace: pathlib.Path, timeout: int) -> tuple[str, ...]:
    """Read configured names locally; never initialize servers or retain their config."""
    command = [codex_executable(), "mcp", "list", "--json"]
    for feature in DISABLED_FEATURES:
        command.extend(["--disable", feature])
    command.extend(["-c", 'web_search="disabled"', *fixture_permission_args(workspace)])
    try:
        completed = subprocess.run(
            command, cwd=workspace, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=timeout, env=codex_environment(),
            executable=shutil.which("codex", path=str(pathlib.Path(command[0]).parent)),
            shell=False, check=False,
        )
        if completed.returncode != 0:
            raise ValueError("Codex MCP inventory command failed")
        inventory = json.loads(completed.stdout)
        if not isinstance(inventory, list):
            raise ValueError("Codex MCP inventory is not a list")
        names = [item.get("name") if isinstance(item, dict) else None for item in inventory]
        if any(not isinstance(name, str) or not name.strip() for name in names):
            raise ValueError("Codex MCP inventory omitted a server name")
        if len(set(names)) != len(names):
            raise ValueError("Codex MCP inventory contains duplicate server names")
        return tuple(sorted(names))
    except (OSError, subprocess.TimeoutExpired, UnicodeError, json.JSONDecodeError) as exc:
        # Config values, endpoints and credential-bearing diagnostics are not evidence.
        raise ValueError("Codex MCP inventory could not be read locally") from exc


def skill_isolation_args(
    disabled_skills: tuple[pathlib.Path, ...],
    disabled_mcp_servers: tuple[str, ...] = (),
    *,
    ignore_user_config: bool = True,
) -> list[str]:
    """Build process-local session overrides without mutating saved configuration."""
    entries = ",".join(
        f"{{path={json.dumps(str(path))},enabled=false}}"
        for path in disabled_skills
    )
    args = [
        "--disable", "plugins",
        "-c", "skills.bundled.enabled=false",
        "-c", f"skills.config=[{entries}]",
    ]
    for feature in DISABLED_FEATURES[1:]:
        args.extend(["--disable", feature])
    # Even disabled entries need a transport when exec ignores user config.
    # A TOML table preserves exact names; the CLI does not unquote dotted -c keys.
    # No original endpoints or credentials are copied into these disabled entries.
    # Diagnostics load user config: do not mix a local transport into an existing
    # HTTP transport. They prove disabled entries, not exec's effective registry.
    disabled_entry = (
        f'{{enabled=false,command={json.dumps(sys.executable)},args=["-c","raise SystemExit(1)"]}}'
        if ignore_user_config else "{enabled=false}"
    )
    servers = ",".join(f"{json.dumps(name)}={disabled_entry}" for name in disabled_mcp_servers)
    args.extend(["-c", f"mcp_servers={{{servers}}}", "-c", 'web_search="disabled"'])
    return args


def _prompt_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in _prompt_strings(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _prompt_strings(item)]
    return []


def inspect_catalog_prompt(
    output: bytes,
    target_name: str,
    target_description: str,
    target_skill: pathlib.Path,
    workspace: pathlib.Path,
    siblings: dict[str, str] | None = None,
) -> tuple[dict[str, object] | None, str]:
    """Prove exact target catalog identity without returning the rendered prompt.

    With ``siblings`` (name to exact description), the catalog must also hold exactly
    one entry per sibling with that description and no other entries.
    """
    siblings = dict(siblings or {})
    try:
        prompt_input = json.loads(output.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"Codex catalog preflight returned invalid JSON: {exc}"
    prompt_strings = _prompt_strings(prompt_input)
    warning_present = any(
        warning in text
        for text in prompt_strings
        for warning in SKILL_CATALOG_WARNINGS
    )
    catalogs = [text for text in prompt_strings if "### Available skills" in text]
    if len(catalogs) != 1:
        return None, f"Codex catalog preflight found {len(catalogs)} rendered catalogs"
    catalog = catalogs[0]
    catalog_roots: dict[str, str] = {}
    catalog_roots_valid = True
    if "### Skill roots" in catalog:
        roots_section = catalog.split("### Skill roots", 1)[1].split("### Available skills", 1)[0]
        for line in roots_section.splitlines():
            match = re.fullmatch(r"- `(r[0-9]+)` = `(.+)`", line)
            if match is None:
                continue
            alias, root_text = match.groups()
            if alias in catalog_roots:
                catalog_roots_valid = False
            catalog_roots[alias] = root_text
    available = catalog.split("### Available skills", 1)[1]
    available = available.split("### How to use skills", 1)[0]
    entries = [line for line in available.splitlines() if line.startswith("- ")]
    target_prefix = f"- {target_name}: "
    target_entries = [entry for entry in entries if entry.startswith(target_prefix)]
    target_description_exact = False
    rendered_file_valid = False
    target_file_exact = False
    root_alias_valid = False
    try:
        repository_skill_root = (workspace / ".agents" / "skills").resolve(strict=True)
        target_file = target_skill.resolve(strict=True)
        target_file_valid = (
            target_file.is_file()
            and target_file.parent.parent == repository_skill_root
        )
    except (OSError, RuntimeError, ValueError):
        repository_skill_root = None
        target_file = None
        target_file_valid = False
    entry_payload = target_entries[0][len(target_prefix) :] if len(target_entries) == 1 else ""
    if entry_payload.endswith(")") and " (file: " in entry_payload:
        rendered_description, rendered_file_text = entry_payload[:-1].rsplit(" (file: ", 1)
        target_description_exact = rendered_description == target_description
        rendered_file_path = pathlib.Path(rendered_file_text)
        rendered_candidate: pathlib.Path | None = None
        if rendered_file_path.is_absolute():
            rendered_candidate = rendered_file_path
            root_alias_valid = True
        elif len(rendered_file_path.parts) >= 2 and catalog_roots_valid:
            root_text = catalog_roots.get(rendered_file_path.parts[0])
            if root_text is not None and pathlib.Path(root_text).is_absolute():
                rendered_candidate = pathlib.Path(root_text).joinpath(*rendered_file_path.parts[1:])
                root_alias_valid = True
        if rendered_file_text and rendered_candidate is not None:
            try:
                rendered_file = rendered_candidate.resolve(strict=True)
                rendered_file_valid = rendered_file.is_file()
                target_file_exact = (
                    rendered_file_valid
                    and target_file_valid
                    and rendered_file == target_file
                )
            except (OSError, RuntimeError, ValueError):
                pass
    sibling_entries = 0
    sibling_entries_exact = True
    for name, description in siblings.items():
        prefix = f"- {name}: "
        matching = [entry[len(prefix):] for entry in entries if entry.startswith(prefix)]
        sibling_entries += len(matching)
        if len(matching) != 1 or not (
            matching[0] == description
            or (matching[0].endswith(")") and " (file: " in matching[0]
                and matching[0][:-1].rsplit(" (file: ", 1)[0] == description)
        ):
            sibling_entries_exact = False
    readiness = {
        "catalog_skill_entries": len(entries),
        "target_entries": len(target_entries),
        "sibling_entries": sibling_entries,
        "sibling_entries_exact": sibling_entries_exact,
        "target_description_exact": target_description_exact,
        "root_alias_valid": root_alias_valid,
        "rendered_file_valid": rendered_file_valid,
        "target_file_exact": target_file_exact,
        "target_description_chars": len(target_description),
        "warning_present": warning_present,
        "other_skill_entries": len(entries) - len(target_entries),
        "proof_scope": "catalog-only; debug prompt-input loads user config",
    }
    if not (
        len(entries) == 1 + len(siblings)
        and len(target_entries) == 1
        and sibling_entries == len(siblings)
        and sibling_entries_exact
        and target_description_exact
        and target_file_exact
        and not warning_present
    ):
        return None, f"Codex catalog preflight failed: {json.dumps(readiness, sort_keys=True)}"
    return readiness, "Codex catalog preflight passed"


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


def _reported_failure(event: dict[str, object]) -> bool:
    """Recognize only failures in Codex's documented JSONL event union."""
    if event.get("type") in {"error", "turn.failed"}:
        return True
    item = event.get("item")
    if not isinstance(item, dict):
        return False
    if item.get("type") == "error":
        return True
    if item.get("type") == "command_execution":
        if item.get("status") in {"failed", "declined"}:
            return True
        if event.get("type") == "item.completed":
            return item.get("status") != "completed" or type(item.get("exit_code")) is not int or item["exit_code"] != 0
    return False


def _invalid_codex_observation(reason: str, *, isolation_stop: bool = False) -> dict[str, object]:
    return {
        "valid": False,
        "selected": False,
        "selected_marker": None,
        "selected_skill": None,
        "selected_skill_set": [],
        "qualification_observed": False,
        "observation_scope": "codex-body-read-attestation",
        "isolation_stop": isolation_stop,
        "reason": reason,
    }


def _validated_marker_map(
    target_skill: str,
    witnesses: dict[str, dict[str, str]],
) -> tuple[dict[str, str] | None, str | None]:
    if target_skill not in witnesses or not witnesses:
        return None, "selection witnesses omit the target skill"
    marker_to_skill: dict[str, str] = {}
    for skill_name, witness in witnesses.items():
        marker = witness.get("marker") if isinstance(witness, dict) else None
        path = witness.get("path") if isinstance(witness, dict) else None
        relative_path = witness.get("relative_path") if isinstance(witness, dict) else None
        digest = witness.get("sha256") if isinstance(witness, dict) else None
        body = witness.get("body") if isinstance(witness, dict) else None
        if (
            not isinstance(skill_name, str)
            or not isinstance(marker, str)
            or MARKER_PATTERN.fullmatch(marker) is None
            or not isinstance(path, str)
            or not pathlib.Path(path).is_absolute()
            or not isinstance(relative_path, str)
            or not relative_path
            or not isinstance(digest, str)
            or not isinstance(body, str)
            or hashlib.sha256(body.encode("utf-8")).hexdigest() != digest
            or body.count(marker) != 1
            or marker in marker_to_skill
        ):
            return None, "selection witness is malformed"
        marker_to_skill[marker] = skill_name
    return marker_to_skill, None


def _decode_codex_events(output: bytes | str) -> tuple[list[dict[str, object]] | None, str | None]:
    try:
        text = output.decode("utf-8", errors="strict") if isinstance(output, bytes) else output
        events = []
        for line in text.splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError("event is not an object")
            events.append(event)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return None, f"invalid JSONL: {exc}"
    return events, None


def _codex_isolation_error(events: list[dict[str, object]]) -> str | None:
    local_items = {"agent_message", "reasoning", "command_execution", "error"}
    lifecycle_events = {"thread.started", "turn.started", "turn.completed", "turn.failed", "error"}
    for event in events:
        event_type = event.get("type")
        if isinstance(event_type, str) and event_type in {"item.started", "item.updated", "item.completed"}:
            item = event.get("item")
            item_type = item.get("type") if isinstance(item, dict) else None
            if not isinstance(item_type, str) or item_type not in local_items:
                return "connected or unsupported tool item"
        elif not isinstance(event_type, str) or event_type not in lifecycle_events:
            return "unsupported event type"
    return None


def _leading_compound_codex_body_skill(
    command: str,
    witnesses: dict[str, dict[str, str]],
) -> str | None:
    """Recognize an exact staged-body read at the start of a compound shell command."""
    try:
        wrapper = shlex.split(command)
        if (
            len(wrapper) != 3
            or pathlib.Path(wrapper[0]).name not in {"bash", "sh", "zsh"}
            or wrapper[1] != "-c"
        ):
            return None
        tokens = shlex.split(wrapper[2])
    except ValueError:
        return None
    if len(tokens) < 6 or tokens[:3] != ["sed", "-n", "1,240p"] or tokens[4] != "&&":
        return None
    read_path = tokens[3]
    matches = [
        name
        for name, witness in witnesses.items()
        if read_path in {witness["path"], witness["relative_path"]}
    ]
    if len(matches) != 1:
        return None
    tail_tokens = tokens[5:]
    if any(
        location in token
        for witness in witnesses.values()
        for location in (witness["path"], witness["relative_path"])
        for token in tail_tokens
    ):
        return None
    if any(witness["marker"] in command for witness in witnesses.values()):
        return None
    return matches[0]


def _leading_compound_codex_body_read(
    command: str,
    command_output: str,
    witnesses: dict[str, dict[str, str]],
) -> str | None:
    skill_name = _leading_compound_codex_body_skill(command, witnesses)
    if skill_name is None:
        return None
    body = witnesses[skill_name]["body"]
    if not command_output.startswith(body) or command_output == body:
        return None
    suffix = command_output[len(body):]
    if any(
        witness["body"] in suffix or witness["marker"] in suffix
        for witness in witnesses.values()
    ):
        return None
    return skill_name


def _post_start_marker_codex_body_read(
    events: list[dict[str, object]],
    command_start: int,
    turn_complete: int,
    command: str,
    witnesses: dict[str, dict[str, str]],
) -> str | None:
    skill_name = _leading_compound_codex_body_skill(command, witnesses)
    if skill_name is None:
        return None
    marker = witnesses[skill_name]["marker"]
    for event in events[command_start + 1:turn_complete]:
        item = event.get("item")
        if (
            event.get("type") == "item.completed"
            and isinstance(item, dict)
            and item.get("type") == "agent_message"
            and isinstance(item.get("text"), str)
            and marker in MARKER_PATTERN.findall(item["text"])
        ):
            return skill_name
    return None


def _append_post_start_codex_body_read(
    events: list[dict[str, object]],
    turn_complete: int,
    command_starts: dict[str, tuple[str, int]],
    reads: list[dict[str, str]],
    witnesses: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    read_ids = {read["command_item_id"] for read in reads}
    pending_ids = set(command_starts) - read_ids
    if len(pending_ids) != 1:
        return reads
    item_id = pending_ids.pop()
    command, command_start = command_starts[item_id]
    skill_name = _post_start_marker_codex_body_read(
        events, command_start, turn_complete, command, witnesses,
    )
    if skill_name is None or skill_name in {read["skill"] for read in reads}:
        return reads
    return [*reads, {
        "skill": skill_name,
        "path": witnesses[skill_name]["path"],
        "sha256": witnesses[skill_name]["sha256"],
        "command_item_id": item_id,
        "read_mode": "post-start-marker",
    }]


def _codex_body_read_error(
    command_starts: dict[str, tuple[str, int]],
    reads: list[dict[str, str]],
) -> str | None:
    if set(command_starts) != {read["command_item_id"] for read in reads}:
        return "command execution lacked a completed or post-start marker body-read attestation"
    if len({read["skill"] for read in reads}) > 1:
        return "multiple staged skill bodies were read"
    return None


def _codex_body_read_match(
    command: str,
    command_output: str,
    witnesses: dict[str, dict[str, str]],
) -> tuple[str, str] | None:
    matches = [
        name
        for name, witness in witnesses.items()
        if command_output == witness["body"]
        and (witness["path"] in command or witness["relative_path"] in command)
    ]
    if len(matches) == 1:
        return matches[0], "exact-output"
    compound_match = _leading_compound_codex_body_read(command, command_output, witnesses)
    if compound_match is None:
        return None
    return compound_match, "leading-compound-output"


def _completed_codex_body_read_match(
    events: list[dict[str, object]],
    command_start: tuple[str, int],
    turn_complete: int,
    command_output: str,
    witnesses: dict[str, dict[str, str]],
) -> tuple[str, str] | None:
    command, start_index = command_start
    match = _codex_body_read_match(command, command_output, witnesses)
    if match is not None:
        return match
    if any(
        witness["body"] in command_output or witness["marker"] in command_output
        for witness in witnesses.values()
    ):
        return None
    skill_name = _post_start_marker_codex_body_read(
        events, start_index, turn_complete, command, witnesses,
    )
    return (skill_name, "post-start-marker") if skill_name is not None else None


def _codex_body_reads(
    events: list[dict[str, object]],
    turn_start: int,
    turn_complete: int,
    witnesses: dict[str, dict[str, str]],
) -> tuple[list[str], list[dict[str, str]], str | None]:
    command_starts: dict[str, tuple[str, int]] = {}
    consulted: list[str] = []
    reads: list[dict[str, str]] = []
    for index, event in enumerate(events):
        if not turn_start < index < turn_complete:
            continue
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") != "command_execution":
            continue
        item_id = item.get("id")
        command = item.get("command")
        if not isinstance(item_id, str) or not item_id or not isinstance(command, str) or not command:
            return [], [], "command execution omitted its identity or command"
        if event.get("type") == "item.started":
            if item_id in command_starts:
                return [], [], "command execution started more than once"
            command_starts[item_id] = (command, index)
            continue
        if event.get("type") == "item.updated":
            if command_starts.get(item_id, ("", -1))[0] != command:
                return [], [], "command execution update was not bound to its start"
            continue
        if event.get("type") != "item.completed" or command_starts.get(item_id, ("", -1))[0] != command:
            return [], [], "command execution completion was not bound to its start"
        command_output = item.get("aggregated_output")
        if not isinstance(command_output, str):
            return [], [], "command execution omitted its output"
        match = _completed_codex_body_read_match(
            events, command_starts[item_id], turn_complete, command_output, witnesses,
        )
        if match is None:
            return [], [], "command was not an exact staged skill-body read"
        skill_name, read_mode = match
        if skill_name in consulted:
            return [], [], "staged skill body was read more than once"
        consulted.append(skill_name)
        reads.append({
            "skill": skill_name,
            "path": witnesses[skill_name]["path"],
            "sha256": witnesses[skill_name]["sha256"],
            "command_item_id": item_id,
            "read_mode": read_mode,
        })
    reads = _append_post_start_codex_body_read(
        events, turn_complete, command_starts, reads, witnesses,
    )
    consulted = [read["skill"] for read in reads]
    if read_error := _codex_body_read_error(command_starts, reads):
        return [], [], read_error
    return consulted, reads, None


def _codex_selected_marker(
    messages: list[str],
    marker_to_skill: dict[str, str],
    consulted: list[str],
) -> tuple[str | None, str | None, str | None]:
    emitted = MARKER_PATTERN.findall("\n".join(messages))
    unknown = sorted(set(emitted) - set(marker_to_skill))
    if unknown:
        return None, None, f"unknown staged marker(s): {', '.join(unknown)}"
    if len(emitted) > 1:
        return None, None, "ambiguous repeated or competing staged markers"
    selected_marker = emitted[0] if emitted else None
    selected_skill = marker_to_skill.get(selected_marker) if selected_marker else None
    if selected_marker is None:
        return None, None, None
    marker_message = next(message for message in messages if selected_marker in MARKER_PATTERN.findall(message))
    first_lines = [line.strip() for line in marker_message.splitlines() if line.strip()]
    if not first_lines or first_lines[0] != selected_marker:
        return None, None, "staged marker was not first in its completed message"
    if selected_skill not in consulted:
        return None, None, "staged marker was not corroborated by its exact skill-body read"
    return selected_marker, selected_skill, None


def inspect_codex_jsonl(
    output: bytes | str,
    target_skill: str,
    witnesses: dict[str, dict[str, str]],
    requested_model: str | None = None,
) -> dict[str, object]:
    """Validate one run and bind its selected marker to an exact staged-body read."""
    scope = "codex-body-read-attestation"
    marker_to_skill, witness_error = _validated_marker_map(target_skill, witnesses)
    if marker_to_skill is None:
        return _invalid_codex_observation(str(witness_error), isolation_stop=True)
    events, decode_error = _decode_codex_events(output)
    if events is None:
        return _invalid_codex_observation(str(decode_error), isolation_stop=True)

    # Inspect every event, including started/failed calls, before lifecycle/marker scoring.
    # A runtime error with no tool-call event remains an invalid trial, not evidence
    # that a connected tool ran. A failed MCP call is still connected-tool activity.
    isolation_error = _codex_isolation_error(events)
    if isolation_error:
        return _invalid_codex_observation(isolation_error, isolation_stop=True)

    event_types = [event.get("type") for event in events]
    lifecycle = ("thread.started", "turn.started", "turn.completed")
    if any(event_types.count(event_type) != 1 for event_type in lifecycle):
        return _invalid_codex_observation("missing or ambiguous thread/turn lifecycle")
    lifecycle_positions = tuple(event_types.index(event_type) for event_type in lifecycle)
    if lifecycle_positions != (0, 1, len(events) - 1):
        return _invalid_codex_observation("thread/turn lifecycle is out of order")
    if any(_reported_failure(event) for event in events):
        return _invalid_codex_observation("Codex reported a failed run")
    thread_event = next(event for event in events if event.get("type") == "thread.started")
    thread_id = thread_event.get("thread_id") or thread_event.get("threadId")
    if not isinstance(thread_id, str) or not thread_id:
        return _invalid_codex_observation("thread start omitted its id")

    turn_start = lifecycle_positions[1]
    turn_complete = lifecycle_positions[2]
    completed_agent_messages = [
        item.get("text")
        for index, event in enumerate(events)
        if turn_start < index < turn_complete
        if event.get("type") == "item.completed"
        and isinstance((item := event.get("item")), dict)
        and item.get("type") == "agent_message"
        and isinstance(item.get("text"), str)
        and bool(item.get("text").strip())
    ]
    if not completed_agent_messages:
        return _invalid_codex_observation("completed turn omitted its agent response")

    consulted, read_witnesses, read_error = _codex_body_reads(
        events, turn_start, turn_complete, witnesses,
    )
    if read_error:
        return _invalid_codex_observation(read_error, isolation_stop=True)
    selected_marker, selected_skill, marker_error = _codex_selected_marker(
        completed_agent_messages, marker_to_skill, consulted,
    )
    if marker_error:
        return _invalid_codex_observation(marker_error)

    resolved_models = {
        model
        for event in events
        if event.get("type") in {"thread.started", "turn.started"}
        and isinstance((model := event.get("model")), str)
        and model
    }
    if len(resolved_models) > 1:
        return _invalid_codex_observation("Codex reported ambiguous resolved models")
    resolved_model = next(iter(resolved_models), None)
    if requested_model is not None and resolved_model is not None and resolved_model != requested_model:
        result = _invalid_codex_observation("Codex resolved a different model than requested")
        result.update(requested_model=requested_model, resolved_model=resolved_model)
        return result
    selected = selected_skill == target_skill
    sibling_selections = [selected_skill] if selected_skill is not None and not selected else []
    return {
        "valid": True,
        "selected": selected,
        "selected_marker": selected_marker,
        "selected_skill": selected_skill,
        "selected_skill_set": [selected_skill] if selected_skill is not None else [],
        "sibling_selections": sibling_selections,
        "consulted_skills": consulted,
        "read_witnesses": read_witnesses,
        "thread_id": thread_id,
        "requested_model": requested_model,
        "resolved_model": resolved_model,
        "model_identity_check": "exact" if resolved_model is not None else "requested-only",
        "qualification_observed": True,
        "observation_scope": scope,
        "reason": (
            "body-read-attested target selection"
            if selected
            else "body-read-attested sibling selection"
            if selected_skill is not None
            else "consultation without selection"
            if consulted
            else "no skill selection"
        ),
    }


def retain_run_evidence(
    evidence_dir: pathlib.Path,
    case_number: int,
    run_number: int,
    output: bytes,
    error_output: bytes,
) -> dict[str, str]:
    """Persist the exact provider streams and return immutable path/digest evidence."""
    stem = f"case-{case_number:03d}-trial-{run_number:02d}"
    jsonl_path = evidence_dir / f"{stem}.jsonl"
    stderr_path = evidence_dir / f"{stem}.stderr.log"
    with jsonl_path.open("xb") as stream:
        stream.write(output)
    with stderr_path.open("xb") as stream:
        stream.write(error_output)
    return {
        "jsonl_path": str(jsonl_path.resolve()),
        "jsonl_sha256": hashlib.sha256(output).hexdigest(),
        "stderr_path": str(stderr_path.resolve()),
        "stderr_sha256": hashlib.sha256(error_output).hexdigest(),
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


def _codex_launch_contract(cmd: list[str], model: str, reasoning: str) -> dict[str, object]:
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
    env = codex_environment()
    if process_evidence is not None:
        process_evidence["launch_contract"] = _codex_launch_contract(cmd, model, reasoning)
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
    args = ap.parse_args()

    eval_file = find_eval_file(args.skill)
    skill_src = find_skill_source(args.skill)
    eval_data, corpus_reason = load_eval_corpus(eval_file)
    if eval_data is None:
        sys.exit(f"ERROR: {corpus_reason}")
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
        skill_dir = stage_repository_skill(skill_src, workspace, test_skill_name, marker)
        target_skill = skill_dir / "SKILL.md"
        target_description = source_skill_description(skill_src)
        if source_skill_description(target_skill) != target_description:
            raise ValueError("staged Codex skill description differs from its source")
        siblings, sibling_markers = stage_sibling_skills(skill_src, workspace, test_uuid)
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
        results, stop_exit = evidence_records.run_trials(
            batch, eval_data, launch,
            lambda stdout: inspect_codex_jsonl(
                stdout, test_skill_name, witnesses, requested_model=args.model,
            ),
            lambda case, trial, stdout, stderr: retain_run_evidence(evidence_dir, case, trial, stdout, stderr),
            progress=lambda case, result: print_case_result(case, len(eval_data), result),
        )
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
                "preflight": preflight,
                "catalog_preflight": readiness,
                "selection_observation": "codex-body-read-attestation",
                "selection_witnesses": {
                    name: {key: value for key, value in witness.items() if key != "body"}
                    for name, witness in witnesses.items()
                },
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

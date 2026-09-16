"""Generate and stage pinned upstream Spec Kit integrations without providers."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

import native_eval_toolchain


SCHEMA_VERSION = "native-eval-upstream-integration/v1"
PINNED_VERSION = "1.0.1"
PINNED_REVISION = "9118ed15a0ba65053469a94c560ea5d233f75884"
PINNED_URL = "https://github.com/github/spec-kit.git"
_HOST_SKILL_ROOTS = {"claude": Path(".claude/skills"), "codex": Path(".agents/skills")}
_SKILLS = frozenset({
    "speckit-analyze", "speckit-checklist", "speckit-clarify", "speckit-constitution",
    "speckit-converge", "speckit-implement", "speckit-plan", "speckit-specify",
    "speckit-tasks", "speckit-taskstoissues",
})
_SHARED_FILES = frozenset({
    ".specify/.gitignore",
    ".specify/scripts/bash/check-prerequisites.sh",
    ".specify/scripts/bash/common.sh",
    ".specify/scripts/bash/create-new-feature.sh",
    ".specify/scripts/bash/resolve-template.sh",
    ".specify/scripts/bash/setup-plan.sh",
    ".specify/scripts/bash/setup-tasks.sh",
    ".specify/scripts/python/check_prerequisites.py",
    ".specify/scripts/python/common.py",
    ".specify/scripts/python/create_new_feature.py",
    ".specify/scripts/python/resolve_template.py",
    ".specify/scripts/python/setup_plan.py",
    ".specify/scripts/python/setup_tasks.py",
    ".specify/templates/checklist-template.md",
    ".specify/templates/constitution-template.md",
    ".specify/templates/plan-template.md",
    ".specify/templates/spec-template.md",
    ".specify/templates/tasks-template.md",
})
_METADATA_FILES = frozenset({
    ".specify/init-options.json", ".specify/integration.json",
})
_MAX_FILES = 64
_MAX_FILE_BYTES = 2 * 1024 * 1024
_MAX_TOTAL_BYTES = 16 * 1024 * 1024
_NETWORK_DENIED_BOOTSTRAP = b'''from __future__ import annotations
import runpy
import socket
import sys

class NetworkDeniedSocket:
    def __init__(self, *args, **kwargs):
        raise PermissionError("network is disabled during upstream integration generation")

def network_denied(*args, **kwargs):
    raise PermissionError("network is disabled during upstream integration generation")

socket.socket = NetworkDeniedSocket
socket.create_connection = network_denied
socket.getaddrinfo = network_denied
site_packages, entrypoint, *arguments = sys.argv[1:]
sys.path.insert(0, site_packages)
sys.argv = [entrypoint, *arguments]
runpy.run_path(entrypoint, run_name="__main__")
'''


class UpstreamStageError(ValueError):
    """Raised when pinned upstream generation or staging cannot be proven safe."""


@dataclass(frozen=True)
class PreparedUpstreamIntegration:
    host: str
    controller_root: Path
    project_root: Path
    skill_root: Path
    runtime_identity: dict[str, Any]


Runner = Callable[[list[str], Path, Mapping[str, str]], subprocess.CompletedProcess[bytes]]


def prepare_upstream_integration(
    controller_root: str | Path,
    *,
    host: str,
    toolchain: native_eval_toolchain.PreparedNativeToolchain,
    runner: Runner | None = None,
) -> PreparedUpstreamIntegration:
    """Generate one official built-in integration in a new controller directory."""

    if host not in _HOST_SKILL_ROOTS:
        raise UpstreamStageError("upstream integration host must be claude or codex")
    root = _safe_directory(Path(controller_root).absolute(), "controller root")
    project = root / f"specify-{host}"
    if project.exists() or project.is_symlink():
        raise UpstreamStageError("upstream generation destination already exists")
    native_eval_toolchain.verify_native_toolchain(toolchain)
    tool_identity = _pinned_tool_identity(toolchain)
    launcher = toolchain.launchers.get("specify")
    if launcher is None or not launcher.is_file():
        raise UpstreamStageError("Specify launcher is unavailable")

    project.mkdir(mode=0o700)
    (project / ".specify").mkdir(mode=0o700)
    home = project / ".controller-home"
    temporary = project / ".controller-tmp"
    home.mkdir(mode=0o700)
    temporary.mkdir(mode=0o700)
    receipt = toolchain.runtime_identity["tools"]["specify"]
    bootstrap = project / ".controller-bootstrap.py"
    bootstrap.write_bytes(_NETWORK_DENIED_BOOTSTRAP)
    os.chmod(bootstrap, 0o500)
    command = [
        receipt["interpreter"]["resolved_path"], "-I", str(bootstrap),
        receipt["site_packages"], receipt["executable"]["resolved_path"],
        "integration", "install", host, "--script", "py",
    ]
    environment = {
        "HOME": str(home),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.pathsep.join([*(str(path) for path in toolchain.path_entries), "/usr/bin", "/bin"]),
        "TMPDIR": str(temporary),
        "GIT_CEILING_DIRECTORIES": str(project.parent),
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        **toolchain.environment,
    }
    result = (runner or _network_denied_runner)(command, project, environment)
    if result.returncode != 0:
        raise UpstreamStageError(
            "pinned Specify integration generation failed: "
            + result.stderr.decode("utf-8", errors="replace")[:1000]
        )
    bootstrap.unlink()
    shutil.rmtree(home)
    shutil.rmtree(temporary)
    output_identity = _output_identity(project, host)
    runtime_identity = {
        "schema_version": SCHEMA_VERSION,
        "host": host,
        "generator": {
            "command": ["specify", "integration", "install", host, "--script", "py"],
            "python_socket_api_blockade": True,
            "kernel_network_isolation": False,
            "network_denial_bootstrap_sha256": hashlib.sha256(_NETWORK_DENIED_BOOTSTRAP).hexdigest(),
            "tool_identity": tool_identity,
        },
        "outputs": output_identity,
    }
    return PreparedUpstreamIntegration(
        host=host,
        controller_root=root,
        project_root=project,
        skill_root=project / _HOST_SKILL_ROOTS[host],
        runtime_identity=runtime_identity,
    )


def verify_upstream_integration(
    prepared: PreparedUpstreamIntegration,
    *,
    toolchain: native_eval_toolchain.PreparedNativeToolchain | None = None,
) -> None:
    """Revalidate the generated source and optionally its admitted generator."""

    if prepared.host not in _HOST_SKILL_ROOTS:
        raise UpstreamStageError("stored upstream integration host is invalid")
    if prepared.project_root != prepared.controller_root / f"specify-{prepared.host}":
        raise UpstreamStageError("stored upstream generation path is invalid")
    if prepared.skill_root != prepared.project_root / _HOST_SKILL_ROOTS[prepared.host]:
        raise UpstreamStageError("stored upstream skill path is invalid")
    observed = _output_identity(prepared.project_root, prepared.host)
    if prepared.runtime_identity.get("schema_version") != SCHEMA_VERSION:
        raise UpstreamStageError("stored upstream identity schema is invalid")
    generator = prepared.runtime_identity.get("generator")
    if (
        not isinstance(generator, dict)
        or generator.get("command") != [
            "specify", "integration", "install", prepared.host, "--script", "py",
        ]
        or generator.get("python_socket_api_blockade") is not True
        or generator.get("kernel_network_isolation") is not False
        or generator.get("network_denial_bootstrap_sha256")
        != hashlib.sha256(_NETWORK_DENIED_BOOTSTRAP).hexdigest()
    ):
        raise UpstreamStageError("stored upstream generator identity is invalid")
    if observed != prepared.runtime_identity.get("outputs"):
        raise UpstreamStageError("generated upstream integration changed after preparation")
    if toolchain is not None:
        native_eval_toolchain.verify_native_toolchain(toolchain)
        if _pinned_tool_identity(toolchain) != prepared.runtime_identity.get("generator", {}).get("tool_identity"):
            raise UpstreamStageError("upstream generator changed after preparation")


def stage_upstream_integration(
    prepared: PreparedUpstreamIntegration,
    destination_root: str | Path,
) -> dict[str, Any]:
    """Merge an already verified integration, rejecting every file collision."""

    verify_upstream_integration(prepared)
    destination = _safe_directory(Path(destination_root).absolute(), "staging destination")
    _stage_files(prepared.project_root, destination, prepared.runtime_identity)
    verify_staged_upstream(prepared.runtime_identity, destination)
    return prepared.runtime_identity["outputs"]


def verify_staged_upstream(identity: Mapping[str, object], destination_root: str | Path) -> None:
    """Verify the immutable generated paths without rejecting subject-owned outputs."""

    destination = _safe_directory(Path(destination_root).absolute(), "staged upstream destination")
    host = identity.get("host")
    if host not in _HOST_SKILL_ROOTS or identity.get("schema_version") != SCHEMA_VERSION:
        raise UpstreamStageError("staged upstream identity is malformed")
    observed = _output_identity(destination, str(host), allow_additional=True)
    if observed != identity.get("outputs"):
        raise UpstreamStageError("staged upstream integration changed")


def verify_staged_payloads(
    identity: Mapping[str, object], loader: Callable[[str], bytes | None],
) -> None:
    """Verify exact generated files through a confinement-preserving reader."""

    outputs = identity.get("outputs")
    records = outputs.get("files") if isinstance(outputs, Mapping) else None
    volatile = outputs.get("volatile_manifest_paths") if isinstance(outputs, Mapping) else None
    if not isinstance(records, dict) or not isinstance(volatile, list):
        raise UpstreamStageError("upstream payload identity is malformed")
    for relative, record in records.items():
        if not isinstance(relative, str) or not isinstance(record, dict):
            raise UpstreamStageError("upstream payload record is malformed")
        body = loader(relative)
        if not isinstance(body, bytes):
            raise UpstreamStageError(f"staged upstream file is missing: {relative}")
        if relative in volatile:
            value = _load_json_bytes(body, "staged upstream manifest")
            semantic = record.get("semantic")
            if not isinstance(semantic, dict):
                raise UpstreamStageError("staged upstream manifest is malformed")
            if set(value) != {*semantic, "installed_at"}:
                raise UpstreamStageError("staged upstream manifest fields changed")
            _validated_timestamp(value.pop("installed_at"), "staged upstream manifest")
            if value != semantic:
                raise UpstreamStageError("staged upstream manifest changed")
        elif len(body) != record.get("bytes") or hashlib.sha256(body).hexdigest() != record.get("sha256"):
            raise UpstreamStageError(f"staged upstream file changed: {relative}")


def skill_witnesses(identity: Mapping[str, object]) -> dict[str, dict[str, object]]:
    outputs = identity.get("outputs")
    witnesses = outputs.get("skill_witnesses") if isinstance(outputs, Mapping) else None
    if not isinstance(witnesses, dict) or set(witnesses) != _SKILLS:
        raise UpstreamStageError("upstream skill witnesses are malformed")
    return json.loads(json.dumps(witnesses))


def volatile_manifest_paths(identity: Mapping[str, object]) -> tuple[str, ...]:
    outputs = identity.get("outputs")
    paths = outputs.get("volatile_manifest_paths") if isinstance(outputs, Mapping) else None
    if not isinstance(paths, list) or not all(isinstance(path, str) for path in paths):
        raise UpstreamStageError("upstream volatile manifest paths are malformed")
    return tuple(paths)


def generated_paths(identity: Mapping[str, object]) -> tuple[str, ...]:
    """Return the exact controller-owned output paths from a validated identity shape."""

    outputs = identity.get("outputs")
    records = outputs.get("files") if isinstance(outputs, Mapping) else None
    if not isinstance(records, dict) or not records:
        raise UpstreamStageError("upstream output records are malformed")
    paths: list[str] = []
    for relative in records:
        if not isinstance(relative, str):
            raise UpstreamStageError("upstream output record path is malformed")
        path = PurePosixPath(relative)
        if path.is_absolute() or not path.parts or ".." in path.parts or path.as_posix() != relative:
            raise UpstreamStageError("upstream output record path is unsafe")
        paths.append(relative)
    return tuple(sorted(paths))


def expected_paths(host: str) -> tuple[str, ...]:
    """Return the exact official output path contract for one supported host."""

    if host not in _HOST_SKILL_ROOTS:
        raise UpstreamStageError("upstream integration host must be claude or codex")
    skill_paths = {
        f"{_HOST_SKILL_ROOTS[host].as_posix()}/{name}/SKILL.md" for name in _SKILLS
    }
    return tuple(sorted({
        *skill_paths, *_SHARED_FILES, *_METADATA_FILES,
        f".specify/integrations/{host}.manifest.json",
        ".specify/integrations/speckit.manifest.json",
    }))


def stage_serialized(source_root: str | Path, destination_root: str | Path, identity_path: str | Path) -> None:
    identity = _load_json(Path(identity_path), "serialized upstream identity")
    source = Path(source_root).absolute()
    host = identity.get("host")
    if host not in _HOST_SKILL_ROOTS:
        raise UpstreamStageError("serialized upstream host is invalid")
    if _output_identity(source, str(host)) != identity.get("outputs"):
        raise UpstreamStageError("serialized upstream source changed")
    destination = _safe_directory(Path(destination_root).absolute(), "scaffold destination")
    _stage_files(source, destination, identity)
    verify_staged_upstream(identity, destination)


def _network_denied_runner(
    command: list[str], cwd: Path, environment: Mapping[str, str],
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=dict(environment),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )


def _pinned_tool_identity(toolchain: native_eval_toolchain.PreparedNativeToolchain) -> dict[str, object]:
    tools = toolchain.runtime_identity.get("tools")
    receipt = tools.get("specify") if isinstance(tools, dict) else None
    distribution = receipt.get("distribution") if isinstance(receipt, dict) else None
    direct_url = distribution.get("direct_url") if isinstance(distribution, dict) else None
    vcs = direct_url.get("vcs_info") if isinstance(direct_url, dict) else None
    if (
        not isinstance(receipt, dict)
        or receipt.get("version") != f"specify {PINNED_VERSION}"
        or not isinstance(distribution, dict)
        or distribution.get("name") != "specify-cli"
        or distribution.get("version") != PINNED_VERSION
        or not isinstance(direct_url, dict)
        or direct_url.get("url") != PINNED_URL
        or not isinstance(vcs, dict)
        or vcs.get("vcs") != "git"
        or vcs.get("commit_id") != PINNED_REVISION
        or vcs.get("requested_revision") != f"v{PINNED_VERSION}"
    ):
        raise UpstreamStageError("Specify installation does not match the admitted pinned upstream source")
    return {
        "version": PINNED_VERSION,
        "revision": PINNED_REVISION,
        "url": PINNED_URL,
        "tool_tree": receipt.get("tool_tree"),
        "python_tree": receipt.get("python_tree"),
        "metadata_sha256": distribution.get("metadata_sha256"),
        "direct_url_sha256": distribution.get("direct_url_sha256"),
    }


def _output_identity(root: Path, host: str, *, allow_additional: bool = False) -> dict[str, Any]:
    root = _safe_directory(root, "upstream project")
    host_manifest = f".specify/integrations/{host}.manifest.json"
    speckit_manifest = ".specify/integrations/speckit.manifest.json"
    skill_paths = {f"{_HOST_SKILL_ROOTS[host].as_posix()}/{name}/SKILL.md" for name in _SKILLS}
    expected = set(expected_paths(host))
    expected_directories = {
        parent.as_posix()
        for relative in expected
        for parent in PurePosixPath(relative).parents
        if parent.as_posix() != "."
    }
    observed: dict[str, dict[str, object]] = {}
    total = 0
    for path in sorted(root.rglob("*")):
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not (stat.S_ISDIR(metadata.st_mode) or stat.S_ISREG(metadata.st_mode)):
            raise UpstreamStageError("generated upstream output contains an unsafe member")
        relative = path.relative_to(root).as_posix()
        if stat.S_ISDIR(metadata.st_mode):
            if not allow_additional and relative not in expected_directories:
                raise UpstreamStageError(f"generated upstream directory is undeclared: {relative}")
            continue
        if relative.startswith(".controller-"):
            raise UpstreamStageError("controller scratch data remained in generated output")
        if relative not in expected:
            if allow_additional:
                continue
            raise UpstreamStageError(f"generated upstream output is undeclared: {relative}")
        if metadata.st_size > _MAX_FILE_BYTES:
            raise UpstreamStageError("generated upstream output exceeds the file limit")
        body = path.read_bytes()
        total += len(body)
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError as error:
            raise UpstreamStageError("generated upstream output is not UTF-8") from error
        observed[relative] = {
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "mode": stat.S_IMODE(metadata.st_mode),
            "text": text if relative in skill_paths else None,
        }
    if len(observed) != len(expected) or set(observed) != expected or len(observed) > _MAX_FILES:
        raise UpstreamStageError("generated upstream output is incomplete")
    if total > _MAX_TOTAL_BYTES:
        raise UpstreamStageError("generated upstream output exceeds the total limit")
    host_data = _manifest_identity(root / host_manifest, host, skill_paths)
    shared_data = _manifest_identity(root / speckit_manifest, "speckit", _SHARED_FILES)
    _metadata_identity(root, host)
    for volatile, semantic in ((host_manifest, host_data), (speckit_manifest, shared_data)):
        observed[volatile] = {"semantic": semantic, "mode": observed[volatile]["mode"]}
    witnesses = {
        name: {
            "path": f"{_HOST_SKILL_ROOTS[host].as_posix()}/{name}/SKILL.md",
            "text": observed[f"{_HOST_SKILL_ROOTS[host].as_posix()}/{name}/SKILL.md"]["text"],
            "bytes": observed[f"{_HOST_SKILL_ROOTS[host].as_posix()}/{name}/SKILL.md"]["bytes"],
            "sha256": observed[f"{_HOST_SKILL_ROOTS[host].as_posix()}/{name}/SKILL.md"]["sha256"],
        }
        for name in sorted(_SKILLS)
    }
    for record in observed.values():
        record.pop("text", None)
    return {
        "files": observed,
        "skill_witnesses": witnesses,
        "volatile_manifest_paths": [host_manifest, speckit_manifest],
    }


def _manifest_identity(path: Path, integration: str, expected_files: set[str] | frozenset[str]) -> dict[str, object]:
    value = _load_json(path, f"{integration} integration manifest")
    if set(value) != {"integration", "version", "installed_at", "files"}:
        raise UpstreamStageError(f"{integration} integration manifest fields are invalid")
    if value.get("integration") != integration or value.get("version") != PINNED_VERSION:
        raise UpstreamStageError(f"{integration} integration manifest identity is invalid")
    timestamp = value.get("installed_at")
    if not isinstance(timestamp, str):
        raise UpstreamStageError(f"{integration} integration timestamp is invalid")
    _validated_timestamp(timestamp, f"{integration} integration")
    files = value.get("files")
    if not isinstance(files, dict) or set(files) != set(expected_files):
        raise UpstreamStageError(f"{integration} integration manifest file set is invalid")
    for relative, digest in files.items():
        if not isinstance(relative, str) or not isinstance(digest, str) or len(digest) != 64:
            raise UpstreamStageError(f"{integration} integration manifest entry is invalid")
        body = (path.parents[2] / relative).read_bytes()
        if hashlib.sha256(body).hexdigest() != digest:
            raise UpstreamStageError(f"{integration} integration manifest digest is stale")
    return {"integration": integration, "version": PINNED_VERSION, "files": files}


def _metadata_identity(root: Path, host: str) -> None:
    integration = _load_json(root / ".specify/integration.json", "integration state")
    settings = integration.get("integration_settings") if isinstance(integration, dict) else None
    if (
        integration.get("version") != PINNED_VERSION
        or integration.get("installed_integrations") != [host]
        or integration.get("integration") != host
        or integration.get("default_integration") != host
        or not isinstance(settings, dict)
        or settings.get(host, {}).get("script") != "py"
    ):
        raise UpstreamStageError("generated integration state is invalid")
    options = _load_json(root / ".specify/init-options.json", "Specify init options")
    if options.get("integration") != host or options.get("script") != "py" or options.get("speckit_version") != PINNED_VERSION:
        raise UpstreamStageError("generated Specify init options are invalid")


def _stage_files(source: Path, destination: Path, identity: Mapping[str, object]) -> None:
    outputs = identity.get("outputs")
    records = outputs.get("files") if isinstance(outputs, Mapping) else None
    if not isinstance(records, dict):
        raise UpstreamStageError("upstream output records are malformed")
    paths = [PurePosixPath(value) for value in generated_paths(identity)]
    # Preflight every existing ancestor before creating anything. Path.is_symlink()
    # only checks the final component, so it is insufficient for a path traversing
    # an earlier symlink into an attacker-controlled directory.
    for relative in paths:
        target = destination / relative
        if target.exists() or target.is_symlink():
            raise UpstreamStageError(f"upstream output collides with staged input: {relative.as_posix()}")
        current = destination
        for part in relative.parts[:-1]:
            current = current / part
            try:
                metadata = current.lstat()
            except FileNotFoundError:
                break
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise UpstreamStageError("upstream output parent is unsafe")
    for relative in paths:
        target = destination / relative
        current = destination
        for part in relative.parts[:-1]:
            current = current / part
            try:
                current.mkdir(mode=0o755)
            except FileExistsError:
                metadata = current.lstat()
                if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                    raise UpstreamStageError("upstream output parent is unsafe")
        source_body = (source / relative).read_bytes()
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(target, flags, int(records[relative.as_posix()]["mode"]))
        except OSError as error:
            raise UpstreamStageError(
                f"upstream output destination is unsafe: {relative.as_posix()}"
            ) from error
        try:
            view = memoryview(source_body)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise UpstreamStageError("upstream output write made no progress")
                view = view[written:]
            if hasattr(os, "fchmod"):
                os.fchmod(descriptor, int(records[relative.as_posix()]["mode"]))
        finally:
            os.close(descriptor)
        if not hasattr(os, "fchmod"):
            os.chmod(target, int(records[relative.as_posix()]["mode"]))


def _safe_directory(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise UpstreamStageError(f"{label} must be absolute")
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise UpstreamStageError(f"{label} must be a non-symlink directory")
    return path


def _validated_timestamp(value: object, label: str) -> None:
    if not isinstance(value, str):
        raise UpstreamStageError(f"{label} timestamp is invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise UpstreamStageError(f"{label} timestamp is invalid") from error
    if parsed.tzinfo is None:
        raise UpstreamStageError(f"{label} timestamp has no timezone")


def _load_json_bytes(payload: bytes, label: str) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise UpstreamStageError(f"{label} contains a duplicate JSON key")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise UpstreamStageError(f"{label} contains a nonstandard JSON constant: {value}")

    try:
        value = json.loads(
            payload.decode("utf-8"), object_pairs_hook=unique, parse_constant=reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise UpstreamStageError(f"{label} is unreadable") from error
    if not isinstance(value, dict):
        raise UpstreamStageError(f"{label} must be a JSON object")
    return value


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise UpstreamStageError(f"{label} is unreadable") from error
    return _load_json_bytes(payload, label)


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 3:
        raise UpstreamStageError("usage: native_eval_upstream.py SOURCE DESTINATION IDENTITY")
    stage_serialized(arguments[0], arguments[1], arguments[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "PreparedUpstreamIntegration", "SCHEMA_VERSION", "UpstreamStageError",
    "expected_paths", "generated_paths", "prepare_upstream_integration", "skill_witnesses", "stage_serialized",
    "stage_upstream_integration", "verify_staged_upstream", "verify_upstream_integration",
    "verify_staged_payloads", "volatile_manifest_paths",
]

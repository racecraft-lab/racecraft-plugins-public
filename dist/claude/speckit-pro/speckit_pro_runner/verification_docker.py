"""Immutable-input and policy primitives for Docker verification.

These functions do not launch Docker or qualify a receipt. The execution adapter
must inspect the actual local image/container, bind the image toolchain and
environment, and retain independent native evidence before reuse is possible.
Only the Linux/arm64 policy exercised by the runtime probes is represented here.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

from .verification_docker_entrypoint import validate_argv

IMAGE_REFERENCE = re.compile(r"[a-z0-9][a-z0-9._/:-]{0,240}@sha256:[0-9a-f]{64}")
IMAGE_ID = re.compile(r"sha256:[0-9a-f]{64}")
EXECUTION_ID = re.compile(r"[0-9a-f]{32}")
MAX_SNAPSHOT_ENTRIES = 50000
MAX_SNAPSHOT_BYTES = 512 * 1024 * 1024
OUTPUT_TMPFS = "rw,nosuid,nodev,noexec,size=16777216,uid=65532,gid=65532,mode=0700"
ENTRYPOINT = ["/usr/local/bin/python3"]
COMMAND = ["-I", "-S", "/__speckit/entrypoint.py"]
HOST_POLICY = {
    "ReadonlyRootfs": True, "NetworkMode": "none", "Privileged": False,
    "Memory": 268435456, "MemorySwap": 268435456, "NanoCpus": 1000000000,
    "PidsLimit": 32, "IpcMode": "none", "PublishAllPorts": False, "PidMode": "",
    "CapDrop": ["ALL"], "SecurityOpt": ["no-new-privileges=true"],
    "Tmpfs": {"/outputs": OUTPUT_TMPFS},
    "LogConfig": {"Type": "none", "Config": {}},
}


def validate_location(reference: Any, endpoint: Any) -> tuple[str, str]:
    """Require explicit immutable input and a local transport, never a context default."""
    if not isinstance(reference, str) or IMAGE_REFERENCE.fullmatch(reference) is None:
        raise ValueError("Docker verification requires a repository@sha256 image reference")
    if not isinstance(endpoint, str) or not endpoint.startswith("unix:///"):
        raise ValueError("Docker verification requires an explicit local Unix socket")
    path = endpoint.removeprefix("unix://")
    if any(ord(char) < 32 or char in "?#\\" for char in path) or PurePosixPath(path).as_posix() != path or ".." in PurePosixPath(path).parts:
        raise ValueError("Docker endpoint must be a canonical absolute Unix socket path")
    return reference, path


def validate_base_image(info: dict[str, Any], reference: str) -> str:
    """Reject implicit pulls, other ABIs, build triggers, and inherited volumes.

    Docker executes ONBUILD triggers when a derived image is built, and VOLUME
    declarations can create writable mounts. Neither belongs in this policy.
    Source: https://docs.docker.com/reference/dockerfile/
    """
    if not isinstance(reference, str) or IMAGE_REFERENCE.fullmatch(reference) is None:
        raise ValueError("base image reference must be digest-pinned")
    image_id, digests = info.get("Id"), info.get("RepoDigests")
    if not isinstance(image_id, str) or IMAGE_ID.fullmatch(image_id) is None or not isinstance(digests, list) or reference not in digests:
        raise ValueError("the inspected local image does not match the requested digest")
    if info.get("Os") != "linux" or info.get("Architecture") != "arm64":
        raise ValueError("the tested verification policy requires Linux/arm64")
    config = info.get("Config")
    if not isinstance(config, dict) or config.get("OnBuild") not in (None, []) or config.get("Volumes") not in (None, {}):
        raise ValueError("verification base images must not declare ONBUILD or VOLUME")
    return image_id


def _snapshot_member(name: str, value: tuple[int, bytes | None]) -> tarfile.TarInfo:
    if not isinstance(name, str) or not name or any(char in name for char in ("\x00", "\\")):
        raise ValueError("invalid snapshot path")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != name:
        raise ValueError("snapshot paths must be canonical and relative")
    if not isinstance(value, tuple) or len(value) != 2:
        raise ValueError("invalid snapshot entry")
    mode, body = value
    if type(mode) is not int or not 0 <= mode <= 0o7777 or not (body is None or isinstance(body, bytes)):
        raise ValueError("snapshot entries require permission bits and bytes or a directory")
    member = tarfile.TarInfo(name)
    member.mode, member.uid, member.gid, member.mtime = mode, 65532, 65532, 0
    member.type = tarfile.DIRTYPE if body is None else tarfile.REGTYPE
    member.size = 0 if body is None else len(body)
    return member


def snapshot_members(files: dict[str, tuple[int, bytes | None]]) -> list[tarfile.TarInfo]:
    """One input validation contract for archive production and daemon readback."""
    if not isinstance(files, dict) or not files or len(files) > MAX_SNAPSHOT_ENTRIES:
        raise ValueError("snapshot entry limit exceeded or snapshot missing")
    # Validate everything before creating the output, including parent structure.
    members = [_snapshot_member(name, value) for name, value in files.items()]
    if "." not in files or files["."][1] is not None or sum(member.size for member in members) > MAX_SNAPSHOT_BYTES:
        raise ValueError("snapshot root or byte limit is invalid")
    for member in members:
        parent = PurePosixPath(member.name).parent.as_posix()
        if parent not in files or files[parent][1] is not None:
            raise ValueError("snapshot parent directory is missing or is a file")
    return members


def archive_snapshot(destination: Path, files: dict[str, tuple[int, bytes | None]], *, image_root: bool = False) -> str:
    """Archive captured bytes, not a second traversal of the mutable source tree."""
    members = snapshot_members(files)
    with tarfile.open(destination, mode="x", format=tarfile.PAX_FORMAT) as archive:
        for member in sorted(members, key=lambda item: item.name):
            body = files[member.name][1]
            if image_root:
                member.name = "inputs" if member.name == "." else f"inputs/{member.name}"
            archive.addfile(member, io.BytesIO(body) if body is not None else None)
    with destination.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def container_options(image_id: str, execution_id: str) -> list[str]:
    """Fixed, fail-closed policy; callers cannot supply arbitrary Docker options."""
    if not isinstance(image_id, str) or IMAGE_ID.fullmatch(image_id) is None:
        raise ValueError("a local content-addressed image ID is required")
    if not isinstance(execution_id, str) or EXECUTION_ID.fullmatch(execution_id) is None:
        raise ValueError("invalid verification execution identity")
    return ["create", "--pull=never", "--platform=linux/arm64", f"--name=speckit-verifier-{execution_id}",
            f"--label=org.racecraft.verification={execution_id}", "--read-only", "--network=none",
            "--cap-drop=ALL", "--security-opt=no-new-privileges=true", "--user=65532:65532",
            "--cpus=1", "--memory=256m", "--memory-swap=256m", "--pids-limit=32", "--ipc=none",
            "--no-healthcheck", "--restart=no", "--stop-timeout=1", "--log-driver=none", f"--tmpfs=/outputs:{OUTPUT_TMPFS}",
            "--env=HOME=/outputs", "--env=TMPDIR=/outputs", "--env=PYTHONDONTWRITEBYTECODE=1",
            "--workdir=/inputs", "--entrypoint=/usr/local/bin/python3", image_id, *COMMAND]


def container_reasons(info: dict[str, Any], image_id: str, execution_id: str) -> list[str]:
    """Compare observed configuration to policy, before AND after execution."""
    container_options(image_id, execution_id)
    host, config = info.get("HostConfig"), info.get("Config")
    if not isinstance(host, dict) or not isinstance(config, dict):
        return ["container_configuration_missing"]
    reasons = [key for key, value in HOST_POLICY.items()
               if type(host.get(key)) is not type(value) or host[key] != value]
    absent = ("CapAdd", "Binds", "Devices", "DeviceRequests", "PortBindings", "VolumesFrom", "Links")
    reasons.extend(key for key in absent if host.get(key))
    expected = {"User": "65532:65532", "WorkingDir": "/inputs", "Entrypoint": ENTRYPOINT, "Cmd": COMMAND}
    reasons.extend(key for key, value in expected.items() if config.get(key) != value)
    if info.get("Image") != image_id or info.get("Mounts"):
        reasons.append("image_or_mounts_changed")
    labels, restart = config.get("Labels"), host.get("RestartPolicy")
    if not isinstance(labels, dict) or labels.get("org.racecraft.verification") != execution_id:
        reasons.append("execution_identity_changed")
    if not isinstance(restart, dict) or restart.get("Name") != "no":
        reasons.append("restart_policy_changed")
    return reasons


def build_context(destination: Path, files: dict[str, tuple[int, bytes | None]],
                  reference: str, argv: list[str]) -> dict[str, str]:
    """Create a private build context from captured bytes; never execute a build step.

    The caller must first inspect/validate the local base image. A local ADD tar
    extracts our validated archive; COPY places trusted launcher bytes outside
    the workload root. No supplied Dockerfile, RUN, mounts, or credentials enter.
    Source: https://docs.docker.com/reference/dockerfile/#add
    """
    if not isinstance(reference, str) or IMAGE_REFERENCE.fullmatch(reference) is None:
        raise ValueError("base image reference must be digest-pinned")
    validate_argv(argv)
    request = json.dumps({"argv": argv}, ensure_ascii=False, sort_keys=True).encode("utf-8")
    if len(request) > 131072:
        raise ValueError("serialized verification request byte limit exceeded")
    launcher = Path(__file__).with_name("verification_docker_entrypoint.py").read_bytes()
    destination.mkdir(mode=0o700)
    # ADD merges archive contents into its destination but does not preserve the
    # archive's '.' root metadata. Name /inputs explicitly to retain its mode.
    archive_snapshot(destination / "snapshot.tar", files, image_root=True)
    payloads = {"request.json": request, "entrypoint.py": launcher,
                ".dockerignore": b"*\n!Dockerfile\n!snapshot.tar\n!entrypoint.py\n!request.json\n",
                "Dockerfile": (f"FROM {reference}\nADD snapshot.tar /\n"
                               "COPY entrypoint.py request.json /__speckit/\n").encode("ascii")}
    for name, body in payloads.items():
        with (destination / name).open("xb") as handle:
            handle.write(body)
    bindings = {}
    for path in destination.iterdir():
        with path.open("rb") as handle:
            bindings[path.name] = hashlib.file_digest(handle, "sha256").hexdigest()
    return bindings

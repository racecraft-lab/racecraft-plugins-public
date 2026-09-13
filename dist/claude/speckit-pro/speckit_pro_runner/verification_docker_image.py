"""Owned verification-image preparation, execution, and tag cleanup.

The caller must reserve workflow launch authority first. These backend results
remain unqualified: Docker observations are evidence, not independent authority.
Only stdout/stderr survive execution. Private contexts and Docker build cache
can retain captured source bytes; removing our tag is not cache erasure.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess
import time
from typing import Any

from .verification_docker import EXECUTION_ID, IMAGE_ID, IMAGE_REFERENCE, build_context, validate_base_image
from .verification_docker_entrypoint import validate_argv
from .verification_docker_readback import SnapshotReadback
from .verification_docker_runtime import DockerClient, execute_container


def inspect_image(client: DockerClient, target: str, timeout: float = 20) -> dict[str, Any]:
    rows = json.loads(client.call(["image", "inspect", target], timeout)["stdout"])
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ValueError("Docker inspect did not return exactly one image")
    return rows[0]


def image_layers(info: dict[str, Any]) -> list[str]:
    rootfs = info.get("RootFS")
    layers = rootfs.get("Layers") if isinstance(rootfs, dict) else None
    if (not isinstance(rootfs, dict) or rootfs.get("Type") != "layers" or not isinstance(layers, list)
            or not layers or any(not isinstance(item, str) or IMAGE_ID.fullmatch(item) is None for item in layers)):
        raise ValueError("image filesystem layer identities are missing or malformed")
    return layers


def owned_image(info: dict[str, Any], image_id: str, execution_id: str) -> bool:
    config, tags = info.get("Config"), info.get("RepoTags")
    labels = config.get("Labels") if isinstance(config, dict) else None
    return (info.get("Id") == image_id and isinstance(tags, list)
            and f"speckit-verifier:{execution_id}" in tags and isinstance(labels, dict)
            and labels.get("org.racecraft.verification") == execution_id)


def validate_built_image(info: dict[str, Any], base: dict[str, Any], image_id: str, execution_id: str) -> None:
    if (not isinstance(image_id, str) or IMAGE_ID.fullmatch(image_id) is None
            or not owned_image(info, image_id, execution_id)):
        raise ValueError("built image identity or ownership does not match")
    config = info["Config"]
    if (info.get("Os") != "linux" or info.get("Architecture") != "arm64"
            or config.get("OnBuild") not in (None, []) or config.get("Volumes") not in (None, {})):
        raise ValueError("built image has an unsupported platform or inherited execution/storage policy")
    inherited, actual = image_layers(base), image_layers(info)
    if actual[:len(inherited)] != inherited or len(actual) <= len(inherited):
        raise ValueError("built image does not extend the inspected base filesystem")


def cleanup_image(client: DockerClient, image_id: str | None, execution_id: str) -> bool:
    """Remove only the matching owned tag, never force deletion or prune parents."""
    if (not isinstance(image_id, str) or IMAGE_ID.fullmatch(image_id) is None
            or not isinstance(execution_id, str) or EXECUTION_ID.fullmatch(execution_id) is None):
        return False
    tag = f"speckit-verifier:{execution_id}"
    listing = ["image", "ls", "--quiet", "--no-trunc", "--filter", f"reference={tag}"]
    try:
        if not client.call(listing, 20)["stdout"].strip():
            return True
        if not owned_image(inspect_image(client, tag), image_id, execution_id):
            return False
        client.call(["image", "rm", "--no-prune", tag], 20)
        return not client.call(listing, 20)["stdout"].strip()
    except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired):
        return False


def image_timeout(deadline: float, limit: float = 20) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ValueError("verification deadline exhausted while preparing the image")
    return min(remaining, limit)


def execute_image(client: DockerClient, files: dict[str, tuple[int, bytes | None]], reference: str,
                  argv: list[str], execution_id: str, directory: Path, timeout: float) -> dict[str, Any]:
    """Build once from fixed captured inputs, execute once, reconcile owned tags.

    --network governs build RUN steps, not registry access. Our Dockerfile has
    no RUN steps and the local digest-pinned base must already exist; we do not
    claim that --pull=false disables all builder registry metadata requests.
    https://docs.docker.com/reference/cli/docker/buildx/build/
    https://docs.docker.com/reference/cli/docker/image/rm/
    """
    if (not isinstance(reference, str) or IMAGE_REFERENCE.fullmatch(reference) is None
            or not isinstance(execution_id, str) or EXECUTION_ID.fullmatch(execution_id) is None
            or not directory.is_absolute() or type(timeout) not in (int, float)
            or not math.isfinite(timeout) or timeout <= 0):
        raise ValueError("a valid execution identity, absolute private directory, and finite timeout are required")
    validate_argv(argv)
    deadline = time.monotonic() + timeout
    base = inspect_image(client, reference, image_timeout(deadline))
    validate_base_image(base, reference)
    image_layers(base)
    tag = f"speckit-verifier:{execution_id}"
    listing = ["image", "ls", "--quiet", "--no-trunc", "--filter", f"reference={tag}"]
    if client.call(listing, image_timeout(deadline))["stdout"].strip():
        raise ValueError("verification image tag already exists; refusing build or cleanup")
    directory.mkdir(mode=0o700)
    context = directory / "context"
    binding = build_context(context, files, reference, argv)
    result = {"execution_id": execution_id, "image_tag": tag, "base_image": base, "context_binding": binding,
              "context_directory": str(context), "build_cache_may_retain_inputs": True, "reusable": False,
              "completed": False, "exit_code": None, "stdout": b"", "stderr": b"",
              "image_tag_cleanup_confirmed": False}
    image_id = None
    try:
        iidfile = directory / "image-id"
        client.call(["build", "--pull=false", "--network=none", "--platform=linux/arm64", "--progress=plain",
                     f"--label=org.racecraft.verification={execution_id}", "--iidfile", str(iidfile),
                     "--tag", tag, str(context)], image_timeout(deadline, 120))
        # Bounded and separate from workload-controlled files; compare with daemon inspection.
        with iidfile.open("rb") as handle:
            raw_identity = handle.read(81)
        if len(raw_identity) > 80:
            raise ValueError("build image identity exceeds the byte limit")
        identity = raw_identity.decode("ascii").strip()
        if IMAGE_ID.fullmatch(identity) is None:
            raise ValueError("build did not produce a valid content-addressed image ID")
        image_id = identity
        result["built_image"] = inspect_image(client, tag, image_timeout(deadline))
        validate_built_image(result["built_image"], base, image_id, execution_id)
        result.update(execute_container(client, image_id, execution_id, image_timeout(deadline, timeout),
                                        SnapshotReadback(files, directory / "input-readback.tar")))
    except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired) as exc:
        result.update(completed=False, exit_code=None, failure=str(exc)[:240])
    finally:
        # An interrupted build with no returned identity cannot prove it has
        # settled or that a later-created tag is ours. Report uncertain cleanup.
        result["image_tag_cleanup_confirmed"] = cleanup_image(client, image_id, execution_id)
    if not result["image_tag_cleanup_confirmed"]:
        result.update(completed=False, exit_code=None)
    return result

"""Isolated Codex launcher for one artifact preview observation.

Codex phase-execution step 8 dispatches ``artifact-preview-observer``. Without a
launcher the Codex parent would have to run that role itself, inside a process
that already holds repository tools and the workflow record, so nothing would
stop it from reading the page and writing its own disposition. This module gives
that step the same treatment the feedback sweep gets: the observer runs in an
``codex exec`` process with its own permission profile, reaching exactly one
broker tool and no filesystem or network beyond what the runtime needs.

The isolation is real; the observation is not always possible. Under
``--ignore-user-config`` the isolated process has no browser or preview MCP, so
``verified`` is unreachable by construction and the honest outcome is
``unavailable``. That is the point: the verdict is brokered and attested rather
than invented by a privileged parent.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from . import author_broker
from .codex_launch import (
    LauncherViolation,
    CodexBroker,
    CodexRuntimes,
    codex_broker_command,
    codex_executable,
    python_executable,
    trusted_executable,
    trusted_prompt_resource,
)
from .sweep_launcher import verify_codex_boundary

PROMPT_RELATIVE = Path("speckit-autopilot/references/preview-prompts/observer.md")
OUTPUT_SCHEMA_NAME = "preview-verdict-output.schema.json"
# The observer closes a session it did not open. Minting, formal writes, and
# closing stay with the parent; widening this tuple would let an injected page
# start its own session or destroy the parent's.
OBSERVER_TOOL_NAMES = ("submit_preview_verdict",)
TRUSTED_CONTEXT = (
    "\n\nTrusted invocation context: one preview observation. The capability "
    "below is the only session you may close, and the verdict call is your "
    "entire output. Return no page text.\nCapability: "
)


def codex_preview_prompt_resource(plugin_root: Path) -> Path:
    """Resolve the observer prompt from exactly one supported plugin layout."""
    return trusted_prompt_resource(plugin_root, PROMPT_RELATIVE, "preview")


def output_schema_path(plugin_root: Path) -> Path:
    return plugin_root / "speckit_pro_runner" / "contracts" / OUTPUT_SCHEMA_NAME


def verify_preview_boundary(plugin_root: Path) -> tuple[int, int, int]:
    """Attest the Codex prerequisites plus this launcher's own resources."""
    version = verify_codex_boundary(plugin_root)
    try:
        parsed = json.loads(output_schema_path(plugin_root).read_text(encoding="utf-8"))
        codex_preview_prompt_resource(plugin_root)
        if not isinstance(parsed, dict):
            raise ValueError("trusted launcher resources are malformed")
    except (OSError, ValueError, json.JSONDecodeError, LauncherViolation) as exc:
        raise LauncherViolation("trusted Codex preview launcher resources are unavailable") from exc
    return version


def codex_preview_command(
    *,
    plugin_root: Path,
    runtime_root: Path,
    capability: str,
    state_root: Path | None = None,
    output_path: Path | None = None,
) -> list[str]:
    """Build the isolated invocation: one broker tool, no network, no repository."""
    if not isinstance(capability, str) or not capability:
        raise LauncherViolation("preview capability is required")
    prompt_resource = codex_preview_prompt_resource(plugin_root)
    try:
        trusted_prompt = prompt_resource.read_text(encoding="utf-8")
    except OSError as exc:
        raise LauncherViolation("trusted Codex preview prompt resource is unavailable") from exc
    # The repository is deliberately absent from the profile: the broker already
    # holds the artifact path and rehashes it, so the observer never reads it.
    # The capability is minted in this process and redeemed in the broker Codex
    # starts, so the redeeming broker is told the session root outright rather
    # than inferring it from a TMPDIR it may not inherit.
    broker = CodexBroker(
        server="author-broker",
        module="speckit_pro_runner.author_broker",
        env={
            "PYTHONPATH": str(plugin_root),
            author_broker.STATE_ROOT_VARIABLE: str(author_broker.state_root() if state_root is None else state_root),
        },
        tools=OBSERVER_TOOL_NAMES,
        output_schema=output_schema_path(plugin_root),
    )
    runtimes = CodexRuntimes(codex=codex_executable(), python=python_executable())
    prompt = trusted_prompt + TRUSTED_CONTEXT + capability + "\n"
    return codex_broker_command(broker, runtimes, runtime_root, prompt, output_path)


def run_codex_preview(
    *,
    plugin_root: Path,
    repo_root: Path,
    artifact_path: str,
    expected_sha256: str,
    state_root: Path | None = None,
    timeout: float = 300,
) -> dict[str, Any]:
    """Observe one page in isolation and return only the brokered disposition."""
    verify_preview_boundary(plugin_root)
    session = author_broker.create_preview_session(
        repo_root=str(repo_root), artifact_path=artifact_path, expected_sha256=expected_sha256
    )
    capability = session["capability"]
    session_closed = False
    try:
        with tempfile.TemporaryDirectory(prefix="speckit-preview-codex-") as temporary:
            runtime_root = Path(temporary) / "runtime"
            runtime_root.mkdir(mode=0o700)
            output_path = Path(temporary) / "verdict.json"
            command = codex_preview_command(
                plugin_root=plugin_root,
                runtime_root=runtime_root,
                capability=capability,
                state_root=state_root,
                output_path=output_path,
            )
            candidate = shutil.which("codex")
            executable = trusted_executable(candidate, "Codex")
            if executable != Path(command[0]):
                raise LauncherViolation("Codex runtime changed after boundary attestation")
            candidate = shutil.which("codex", path=str(executable.parent))
            if trusted_executable(candidate, "Codex") != executable:
                raise LauncherViolation("Codex runtime changed after boundary attestation")
            try:
                completed = subprocess.run(
                    [candidate, *command[1:]],
                    cwd=runtime_root,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=timeout,
                    shell=False,
                    # The Codex runtime needs the operator's environment to find
                    # its own credentials and toolchain. The model inside it does
                    # not inherit that: --ignore-user-config, --ephemeral and the
                    # author-broker-only permission profile above bound what the
                    # observer can reach, which is one broker tool and no network.
                    env=os.environ.copy(),
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise LauncherViolation("isolated Codex preview invocation failed") from exc
            if completed.returncode != 0:
                raise LauncherViolation("isolated Codex preview invocation returned a failure")
            try:
                parsed = json.loads(output_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise LauncherViolation("isolated Codex preview returned no schema-valid verdict") from exc
        observation = _close_preview_session(capability)
        session_closed = True
        return preview_observation(parsed, observation, expected_sha256)
    finally:
        if not session_closed:
            _discard_preview_session(capability)


def _discard_preview_session(capability: str) -> None:
    try:
        author_broker.close_session(capability=capability)
    except author_broker.BrokerViolation:
        # Failure cleanup cannot turn the attempt into a verified preview.
        pass


def _close_preview_session(capability: str) -> dict[str, Any]:
    try:
        closed = author_broker.close_session(capability=capability)
    except author_broker.BrokerViolation as exc:
        raise LauncherViolation("broker preview close failed") from exc
    observation = closed.get("observation")
    if observation is None:
        raise LauncherViolation("broker preview had no submitted observation")
    return observation


def preview_observation(parsed: Any, broker_observation: Any, expected_sha256: str) -> dict[str, Any]:
    """Compare isolated output with broker read-back before recording it."""
    if not isinstance(parsed, dict) or set(parsed) != {"verdict", "artifact_sha256"}:
        raise LauncherViolation("isolated Codex preview output contains non-verdict fields")
    if not isinstance(broker_observation, dict) or set(broker_observation) != {"verdict", "artifact_sha256", "observed_at"}:
        raise LauncherViolation("broker preview returned no complete observation")
    verdict = broker_observation["verdict"]
    if verdict not in author_broker.PREVIEW_VERDICTS:
        raise LauncherViolation("broker preview verdict is outside the closed vocabulary")
    if broker_observation["artifact_sha256"] != expected_sha256 or parsed != {"verdict": verdict, "artifact_sha256": expected_sha256}:
        raise LauncherViolation("isolated Codex preview output disagrees with broker read-back")
    if not isinstance(broker_observation["observed_at"], str) or not broker_observation["observed_at"]:
        raise LauncherViolation("broker preview returned no observation time")
    return {
        "kind": "brokered",
        "verdict": verdict,
        "artifact_sha256": expected_sha256,
        "observed_at": broker_observation["observed_at"],
    }

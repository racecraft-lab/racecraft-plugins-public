"""Build Phase 6.5 autonomy-boundary records and receipts for tests.

The digests follow the documented canonical form (`phase-execution.md`,
Phase 6.5): canonical JSON sorts keys, uses `,` and `:` without whitespace,
preserves Unicode, and rejects non-finite numbers, and the digest is the
lowercase hexadecimal SHA-256 of its UTF-8 bytes behind a `sha256:` prefix. The
runner's `digest` computes exactly that, so a test never asks the validator it
is checking to compute its own expected digest.
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "speckit-pro"))

from speckit_pro_runner.agent_materialization import digest  # noqa: E402


def autonomy_private_record(repo_root: Path, writable_roots: list[str]) -> dict[str, object]:
    """A complete v1 boundary record whose roots and target are machine-local."""
    feature = repo_root / "specs" / "demo"
    feature.mkdir(parents=True, exist_ok=True)
    fingerprints: dict[str, object] = {}
    for label, name, content in (
        ("plan_md", "plan.md", b"# Plan\n"),
        ("tasks_md", "tasks.md", b"# Tasks\n"),
    ):
        (feature / name).write_bytes(content)
        fingerprints[label] = {
            "path": f"specs/demo/{name}",
            "sha256": digest(content),
            "size_bytes": len(content),
        }
    execution_scope = {
        "execution_environment": "local",
        "sandbox_mode": "workspace-write",
        "approval_reviewer": "auto_review",
        "writable_roots": sorted(writable_roots),
    }
    execution_sha = digest(execution_scope)
    action_scope = {
        "category": "outside_writable_roots",
        "command_or_tool": "apply_patch",
        "target": str(Path(writable_roots[0]).parent / "shared-config" / "settings.json"),
        "effect": "persistent edit of a machine-local file",
        "execution_boundary_sha256": execution_sha,
    }
    scope_sha = digest(action_scope)
    return {
        "schema_version": "autonomy-boundary.v1",
        "status": "ready",
        "planning_fingerprints": fingerprints,
        "execution_boundary": {
            **execution_scope,
            "summary": f"Writes stay inside {writable_roots[0]}.",
            "sha256": execution_sha,
        },
        "actions": [
            {
                "action_id": "edit-shared-config",
                **action_scope,
                "scope_sha256": scope_sha,
                "disposition": "ready",
                "authorization": {
                    "status": "explicit_user",
                    # A dashed native event id guarantees a privacy-pattern hit on
                    # every platform, whatever the home and temp roots are.
                    "evidence": (
                        f"user approved the edit at {action_scope['target']} "
                        f"in native event {uuid.uuid4()}"
                    ),
                    "scope_sha256": scope_sha,
                },
            }
        ],
    }


def autonomy_public_receipt(record: dict[str, object]) -> dict[str, object]:
    """Project a private boundary record onto its portable public receipt."""
    execution = record["execution_boundary"]
    return {
        "schema_version": "autonomy-boundary-receipt.v1",
        "status": record["status"],
        "planning_fingerprints": record["planning_fingerprints"],
        "execution_boundary": {
            key: execution[key]
            for key in ("execution_environment", "sandbox_mode", "approval_reviewer", "sha256")
        },
        "actions": [
            {
                "action_id": action["action_id"],
                "category": action["category"],
                "execution_boundary_sha256": action["execution_boundary_sha256"],
                "scope_sha256": action["scope_sha256"],
                "disposition": action["disposition"],
                "authorization": {
                    "status": action["authorization"]["status"],
                    "scope_sha256": action["authorization"]["scope_sha256"],
                },
            }
            for action in record["actions"]
        ],
        "private_record_sha256": digest(record),
    }


AUTONOMY_RUN_ID = "0" * 32


def autonomy_execution_control(run_id: str = AUTONOMY_RUN_ID) -> dict[str, object]:
    """The state's execution-control mirror; its run id locates the private record."""
    return {
        "ledger_path": ".process/execution-control/workflow.json",
        "run_id": run_id,
        "disposition": "continue",
        "reasons": [],
        "elapsed_seconds": 0,
        "checkpoint_due": False,
    }


def write_autonomy_private_record(
    repo_root: Path, record: object, run_id: str = AUTONOMY_RUN_ID,
) -> Path:
    """Write the private record owner-only where the full guard reads it.

    `repo_root` must be a `git init` checkout, so its git common directory is
    `repo_root/.git`.
    """
    directory = repo_root / ".git" / "speckit-pro" / "autonomy-boundary"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / f"{run_id}.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o600)
    return path

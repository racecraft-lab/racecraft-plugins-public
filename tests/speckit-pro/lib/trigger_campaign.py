"""Durable, conservative native-launch accounting (Python standard library only)."""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import time

from trigger_comparison import _require, json_digest


def validate_approval(record: dict, manifest_digest: str, budget: int) -> None:
    """Require a retained user-message authorization, not an agent-owned pass flag.

    This records documentary provenance, not a cryptographic user authentication.
    The caller must obtain the source message from the user-facing approval channel.
    For v2, the trusted orchestrator interprets that real message in its retained
    scope context and binds an exact grant. A worker-created binding is not authority;
    neither version authenticates the caller or decides natural-language intent.
    """
    _require(type(budget) is int and budget > 0, "launch budget must be a positive integer")
    _require(isinstance(record, dict) and record.get("schema_version") in {"trigger-campaign-approval/v1", "trigger-campaign-approval/v2"}, "missing retained campaign approval")
    _require(record.get("manifest_sha256") == manifest_digest and type(record.get("launch_budget")) is int and record["launch_budget"] == budget, "approval does not bind exact manifest and budget")
    source = record.get("source")
    _require(isinstance(source, dict) and source.get("role") == "user", "campaign requires user-origin approval")
    _require(isinstance(source.get("message_id"), str) and bool(source["message_id"].strip()), "approval lacks source message identity")
    _require(isinstance(source.get("content"), str) and bool(source["content"].strip()), "approval lacks original user content")
    if record["schema_version"] == "trigger-campaign-approval/v2":
        binding = record.get("binding")
        _require(isinstance(binding, dict) and binding.get("schema_version") == "orchestrator-approval-binding/v1",
                 "natural-language approval requires a retained orchestrator binding")
        _require(binding.get("issuer") == "orchestrator" and binding.get("decision") == "approve",
                 "missing orchestrator approval decision")
        _require(binding.get("manifest_sha256") == manifest_digest and type(binding.get("launch_budget")) is int
                 and binding["launch_budget"] == budget, "orchestrator grant does not bind manifest and budget")
        _require(binding.get("source_sha256") == json_digest(source), "original approval source changed")
        _require(isinstance(binding.get("scope_context"), str) and bool(binding["scope_context"].strip()),
                 "approval interpretation lacks retained scope context")
        return
    text = f"Approve trigger campaign {manifest_digest} with launch budget {budget}."
    _require(isinstance(source.get("content"), str) and text in source["content"].splitlines(), "source message does not explicitly approve this manifest and launch budget")


class CampaignLedger:
    """One immutable authorization and transactionally reserved trial identities."""

    def __init__(self, path: Path, manifest_digest: str, approval: dict, budget: int):
        validate_approval(approval, manifest_digest, budget)
        self.path = path
        self.budget = budget
        path.parent.mkdir(parents=True, exist_ok=True)
        binding = json.dumps({"manifest_sha256": manifest_digest, "approval_sha256": json_digest(approval), "launch_budget": budget}, sort_keys=True)
        with self._connection() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS authorization (id INTEGER PRIMARY KEY CHECK(id=1), binding TEXT NOT NULL)")
            connection.execute("CREATE TABLE IF NOT EXISTS launches (arm TEXT NOT NULL, case_id TEXT NOT NULL, trial INTEGER NOT NULL CHECK(trial BETWEEN 1 AND 3), status TEXT NOT NULL, reserved_at REAL NOT NULL, completed_at REAL, PRIMARY KEY(arm, case_id, trial))")
            connection.execute("INSERT OR IGNORE INTO authorization VALUES (1, ?)", (binding,))
            _require(connection.execute("SELECT binding FROM authorization WHERE id=1").fetchone()[0] == binding, "ledger authorization is immutable; manifest, budget or approval changed")

    @contextmanager
    def _connection(self):
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            connection.execute("PRAGMA synchronous=FULL")
            with connection:
                yield connection
        finally:
            connection.close()

    def reserve_case(self, arm: str, case_id: str) -> None:
        """Reserve all three serial trials before starting the native case process."""
        _require(isinstance(arm, str) and bool(arm) and isinstance(case_id, str) and bool(case_id), "invalid reservation identity")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            exists = connection.execute("SELECT 1 FROM launches WHERE arm=? AND case_id=?", (arm, case_id)).fetchone()
            _require(exists is None, "case already reserved; automatic retries are prohibited")
            count = connection.execute("SELECT COUNT(*) FROM launches").fetchone()[0]
            _require(count + 3 <= self.budget, "campaign launch budget exhausted")
            connection.executemany("INSERT INTO launches VALUES (?, ?, ?, 'unknown', ?, NULL)", [(arm, case_id, trial, time.time()) for trial in (1, 2, 3)])

    def finish_case(self, arm: str, case_id: str, status: str) -> None:
        _require(status in {"complete", "invalid"}, "unknown outcomes cannot be cleared or retried")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute("SELECT status FROM launches WHERE arm=? AND case_id=?", (arm, case_id)).fetchall()
            _require(len(rows) == 3 and all(row[0] == "unknown" for row in rows), "missing or already settled reservation")
            connection.execute("UPDATE launches SET status=?, completed_at=? WHERE arm=? AND case_id=?", (status, time.time(), arm, case_id))

    def snapshot(self) -> dict:
        with self._connection() as connection:
            rows = connection.execute("SELECT arm, case_id, trial, status, reserved_at, completed_at FROM launches ORDER BY arm, case_id, trial").fetchall()
        return {"schema_version": "trigger-campaign-ledger/v1", "launch_budget": self.budget,
                "reserved_launches": len(rows), "unknown_launches": sum(row[3] == "unknown" for row in rows),
                "launches": [dict(zip(("arm", "case_id", "trial_number", "status", "reserved_at", "completed_at"), row)) for row in rows]}

    def require_reconciled(self) -> None:
        _require(self.snapshot()["unknown_launches"] == 0, "unknown prior outcomes require read-only process/artifact reconciliation; no relaunch authorized")


@dataclass(frozen=True)
class QualifiedConcurrency:
    binding_sha256: str
    serial_seconds: float
    parallel_seconds: float
    trial_count: int


def read_ledger(path: Path) -> tuple[dict, dict]:
    """Read authoritative accounting without creating or modifying a database."""
    comparison_uri = path.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(comparison_uri, uri=True)
    try:
        binding = json.loads(connection.execute("SELECT binding FROM authorization WHERE id=1").fetchone()[0])
        rows = connection.execute("SELECT arm, case_id, trial, status, reserved_at, completed_at FROM launches ORDER BY arm, case_id, trial").fetchall()
        snapshot = {"schema_version": "trigger-campaign-ledger/v1", "launch_budget": binding["launch_budget"],
            "reserved_launches": len(rows), "unknown_launches": sum(row[3] == "unknown" for row in rows),
            "launches": [dict(zip(("arm", "case_id", "trial_number", "status", "reserved_at", "completed_at"), row)) for row in rows]}
        return binding, snapshot
    finally:
        connection.close()


def worker_limit(requested: int, profile: QualifiedConcurrency | None, binding_digest: str) -> int:
    _require(type(requested) is int and requested in (1, 2), "global native worker ceiling is two")
    if requested == 2:
        _require(isinstance(profile, QualifiedConcurrency) and profile.binding_sha256 == binding_digest,
                 "two workers require an independently replayed, matching concurrency pilot")
        _require(profile.trial_count == 48 and profile.serial_seconds > 0 and 0 < profile.parallel_seconds <= 0.75 * profile.serial_seconds,
                 "concurrency pilot did not demonstrate a 25 percent improvement")
    return requested

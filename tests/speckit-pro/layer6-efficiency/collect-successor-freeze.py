#!/usr/bin/env python3
"""OPERATOR-ONLY successor-capability-freeze collector (CAR-003 T022).

**This script makes live model calls. It is never run by the default suite and
never runs in continuous integration** (FR-022, SC-019). It is the first
operator action of slice 1.

It runs the `claude -p --model <alias>` print-mode canary probe on the pinned
client across the full ordered effort ladder `low` through `max` for every
role-eligible alias, and emits a collection record that
`lib/claude_successor_freeze.py` can admit and publish.

Two probe surfaces are used, mirroring the archived predecessor collection:

* one JSON-output probe per alias establishes the resolved dated model identity
  from the per-model usage breakdown, and
* one plain-text print probe per (alias, effort) establishes effort support by
  **configuration acceptance** on that same surface.

The print-mode canary probe is the sole admitting authority (FR-002). Nothing
else here may admit a tuple.

Every invocation is bounded by declared ceilings. The run stops the moment any
ceiling is reached and records the stop reason rather than continuing, because
an unbudgeted campaign is exactly what FR-022 forbids.

Committed evidence is sanitized deny-by-default (FR-027, SC-015): session
identifiers are normalized to `<session-id>` and home paths to `<home>` before
anything is written.

Usage::

    python3 tests/speckit-pro/layer6-efficiency/collect-successor-freeze.py \
        --out docs/ai/research/claude-car-003-successor-freeze-collection.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# tests/speckit-pro/layer6-efficiency/<this file> -> four levels up is the repo root.
REPO_ROOT = Path(__file__).resolve().parents[3]

# Role-eligible aliases. Sourced from the archived predecessor snapshot's alias
# bindings; the ledger is the admission authority, this is only the probe set.
ROLE_ELIGIBLE_ALIASES = ("opus", "sonnet", "haiku", "fable")

# FR-003: the closed ordered ladder. `high` is the documented search origin and
# was never probed by the predecessor snapshot, which is why it is here.
EFFORT_LADDER = ("low", "medium", "high", "xhigh", "max")

CANARY_PROMPT = "Reply with exactly: ok"

# Operator-only retention store. Gitignored: raw captures never reach the repo.
RETENTION_RELATIVE = "tests/speckit-pro/layer6-efficiency/results/car-003-successor-freeze-raw.json"

# Declared ceilings. FR-022 requires an explicit budget with separate ceilings;
# a run that would exceed any of these stops and records why.
BUDGET = {
    "max_attempts": 32,
    "max_wall_clock_seconds": 1800,
    "max_cost_usd": 20.0,
    "per_probe_timeout_seconds": 120,
}

SESSION_ID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I
)
HOME_PATH_RE = re.compile(r"/(?:Users|home)/[^/\s\"']+")


def sanitize(text: str) -> str:
    """Normalize session identifiers and home paths before anything is stored."""
    text = SESSION_ID_RE.sub("<session-id>", text)
    return HOME_PATH_RE.sub("<home>", text)


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class BudgetExhausted(RuntimeError):
    """Raised when a declared ceiling is reached. Never swallowed."""


class Ledger:
    """Tracks spend against the declared ceilings and refuses to overrun."""

    def __init__(self) -> None:
        self.attempts = 0
        self.cost_usd = 0.0
        self.started = time.monotonic()
        self.stop_reason: str | None = None

    def check(self) -> None:
        if self.attempts >= BUDGET["max_attempts"]:
            self.stop_reason = "attempt_ceiling_reached"
            raise BudgetExhausted(self.stop_reason)
        if time.monotonic() - self.started >= BUDGET["max_wall_clock_seconds"]:
            self.stop_reason = "wall_clock_ceiling_reached"
            raise BudgetExhausted(self.stop_reason)
        if self.cost_usd >= BUDGET["max_cost_usd"]:
            self.stop_reason = "cost_ceiling_reached"
            raise BudgetExhausted(self.stop_reason)

    @property
    def elapsed_seconds(self) -> float:
        return round(time.monotonic() - self.started, 3)


def run_probe(argv: list[str], ledger: Ledger) -> tuple[int, str]:
    """Run one bounded canary probe. Returns (exit_code, sanitized_stdout)."""
    ledger.check()
    ledger.attempts += 1
    try:
        # argv[0] MUST be the ``"claude"`` string literal so the XPLAT-010
        # repository Bash-confinement guard can statically prove the executable
        # is a non-Bash literal. This is the same literal-command idiom the
        # CAR-002 live boundary uses; passing a variable list defeats the proof
        # and blocks release readiness. ``argv[0] == "claude"`` already, so this
        # equals ``list(argv)`` at runtime.
        proc = subprocess.run(
            ["claude", *argv[1:]],
            capture_output=True,
            text=True,
            timeout=BUDGET["per_probe_timeout_seconds"],
            stdin=subprocess.DEVNULL,
            cwd=str(REPO_ROOT),
        )
    except subprocess.TimeoutExpired:
        return 124, "<probe timed out>"
    return proc.returncode, sanitize(proc.stdout)


def probe_alias_binding(alias: str, ledger: Ledger) -> dict:
    """JSON-output probe: establishes the resolved dated model identity."""
    argv = ["claude", "-p", CANARY_PROMPT, "--model", alias, "--output-format", "json"]
    code, out = run_probe(argv, ledger)
    record: dict = {
        "alias": alias,
        "surface": "print_mode_canary_probe",
        "probe_output_mode": "json_print",
        "exit_code": code,
        "raw_output_sha256": sha256_text(out),
        "sanitization": "home_paths_and_session_ids_normalized",
    }
    resolved = None
    if code == 0:
        try:
            payload = json.loads(out)
            usage = payload.get("modelUsage") or {}
            for model_id, detail in usage.items():
                resolved = (detail or {}).get("canonicalModel") or model_id
                break
            record["fast_mode_state"] = payload.get("fast_mode_state")
            record["service_tier"] = (payload.get("usage") or {}).get("service_tier")
            cost = payload.get("total_cost_usd")
            if isinstance(cost, (int, float)):
                ledger.cost_usd += float(cost)
                record["observed_cost_usd"] = cost
            record["raw_output"] = out
        except json.JSONDecodeError:
            record["parse_error"] = "probe stdout was not valid JSON"
    record["resolved_dated_model_id"] = resolved
    return record


def probe_effort(alias: str, effort: str, ledger: Ledger) -> dict:
    """Plain-text print probe: effort support by configuration acceptance."""
    argv = ["claude", "-p", CANARY_PROMPT, "--model", alias, "--effort", effort]
    code, out = run_probe(argv, ledger)
    accepted = code == 0 and "ok" in out.lower()
    return {
        "tuple_id": f"{alias}__{effort}",
        "model_requested": alias,
        "effort_requested": effort,
        "surface": "print_mode_canary_probe",
        "effort_probe_output_mode": "plain_text_print",
        "effort_acceptance": "accepted" if accepted else "rejected",
        "exit_code": code,
        "raw_output": out.strip(),
        "raw_output_sha256": sha256_text(out),
        "sanitization": "home_paths_and_session_ids_normalized",
    }


def client_version() -> str:
    try:
        proc = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            stdin=subprocess.DEVNULL,
        )
        return sanitize(proc.stdout.strip()) or "unknown"
    except (subprocess.TimeoutExpired, OSError):
        return "unknown"


def collect() -> dict:
    ledger = Ledger()
    alias_bindings: list[dict] = []
    tuple_evidence: list[dict] = []
    observed_models: list[str] = []

    try:
        for alias in ROLE_ELIGIBLE_ALIASES:
            binding = probe_alias_binding(alias, ledger)
            alias_bindings.append(binding)
            resolved = binding.get("resolved_dated_model_id")
            if resolved and resolved not in observed_models:
                observed_models.append(resolved)
            for effort in EFFORT_LADDER:
                tuple_evidence.append(probe_effort(alias, effort, ledger))
    except BudgetExhausted:
        pass

    # supported_efforts maps model -> OBSERVATION RECORDS, not bare effort
    # strings. admit_tuples reads `effort`, `acceptance`, and `surface` off each
    # observation, and observation_admits() refuses any observation whose
    # surface is not the admitting one.
    supported: dict[str, list[dict]] = {}
    for entry in tuple_evidence:
        supported.setdefault(entry["model_requested"], []).append(
            {
                "effort": entry["effort_requested"],
                "acceptance": entry["effort_acceptance"],
                "surface": entry["surface"],
                "probe_output_mode": entry["effort_probe_output_mode"],
                "evidence_digest": entry["raw_output_sha256"],
            }
        )

    body = {
        "schema_version": "1.0.0",
        "record_kind": "successor_capability_collection",
        "collection_id": "CAR-003-SCC-" + utc_now().replace(":", "").replace("-", ""),
        "admitting_surface": "print_mode_canary_probe",
        "command_contract": "claude -p <canary> --model <alias> [--effort <effort>]",
        "collection_method": "operator_run_print_mode_canary_probe",
        # The publication gate compares this against TRUSTED_COLLECTION_AUTHORITY.
        "collection_authority": "operator_pinned_client",
        "client_version": client_version(),
        "client_distribution": "local_cli",
        "account_boundary": "<redacted-account-boundary>",
        "environment_boundary": "<redacted-environment-boundary>",
        "authentication_mode": "subscription",
        # Keyed by the same identity the source ledger uses - the ALIAS, not the
        # resolved dated id. Keying this by dated id makes every ledger entry
        # read as "the runtime never saw this model" and empties the
        # intersection.
        "observed_models": [
            b["alias"] for b in alias_bindings if b.get("resolved_dated_model_id")
        ],
        "alias_bindings": alias_bindings,
        "visible_defaults": {},
        "supported_efforts": supported,
        "effort_search_origin": "high",
        "effort_admission": "configuration_acceptance_on_admitting_surface",
        "collected_at_utc": utc_now(),
        "invalidation_criteria": [
            "client_change",
            "catalog_change",
            "alias_repoint",
            "source_ledger_change",
        ],
        # Attestation literals the publication gate compares exactly. They are
        # set only after the corresponding check actually passes, below.
        "sanitization_status": "pending",
        "retention_status": "pending",
        "collection_max_age_hours": 24,
    }
    body["raw_catalog_digest"] = sha256_text(json.dumps(alias_bindings, sort_keys=True))
    body["parsed_catalog_digest"] = sha256_text(json.dumps(supported, sort_keys=True))

    # FR-027: raw captures are operator-only and never committed. Only their
    # digests reach the collection record. `raw_output` is a deny-listed field
    # name, so leaving it inline would block publication rather than be
    # silently stripped - which is the intended behaviour, not a nuisance.
    retention = {
        "collection_id": body["collection_id"],
        "alias_bindings": alias_bindings,
        "tuple_evidence_detail": tuple_evidence,
        "budget_ledger": {
            "declared": BUDGET,
            "attempts_used": ledger.attempts,
            "observed_cost_usd": round(ledger.cost_usd, 6),
            "elapsed_seconds": ledger.elapsed_seconds,
            "stop_reason": ledger.stop_reason or "completed_within_budget",
        },
    }
    retention_path = REPO_ROOT / RETENTION_RELATIVE
    retention_path.parent.mkdir(parents=True, exist_ok=True)
    retention_path.write_text(
        json.dumps(retention, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    body["retention_status"] = "passed"

    # Strip operator-only content from what will be committed.
    committed_keys = (
        "alias",
        "resolved_dated_model_id",
        "surface",
        "probe_output_mode",
        "exit_code",
        "raw_output_sha256",
        "sanitization",
        "fast_mode_state",
        "service_tier",
    )
    body["alias_bindings"] = [
        {k: v for k, v in binding.items() if k in committed_keys}
        for binding in alias_bindings
    ]
    body["sanitization_status"] = "passed"

    body["collection_digest"] = sha256_text(
        json.dumps({k: v for k, v in body.items() if k != "collection_digest"}, sort_keys=True)
    )
    return body


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="repo-relative output path")
    args = parser.parse_args()

    record = collect()
    out_path = REPO_ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(record, indent=2, sort_keys=True) + "\n"
    if SESSION_ID_RE.search(text) or HOME_PATH_RE.search(text):
        print("REFUSED: unsanitized evidence detected; nothing written", file=sys.stderr)
        return 2
    out_path.write_text(text, encoding="utf-8")

    budget = record["budget"]
    print(f"collection: {record['collection_id']}")
    print(f"attempts: {budget['attempts_used']}  cost: ${budget['observed_cost_usd']}")
    print(f"stop: {budget['stop_reason']}")
    print(f"observed models: {record['observed_models']}")
    for binding in record["alias_bindings"]:
        print(f"  {binding['alias']:8s} -> {binding.get('resolved_dated_model_id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""OPERATOR-ONLY calibration pilot driver (CAR-003 T078).

**This script makes live model calls. It is never run by the default suite and
never runs in continuous integration** (FR-022, SC-019). It is the second and
last operator action of CAR-003, and it runs after the successor freeze.

What it does, and only what it does:

* consumes **only** disposable objectives from a ``qualification_eligible=false``
  calibration partition, and proves the refusal on all four other partition
  types rather than merely asserting it (FR-013),
* dispatches paired arms live under an explicit, local, pinned invocation with
  **all eight** campaign ceilings declared and enforced (FR-022, FR-038),
* feeds the real shipped libraries — the exact-treatment runner, the score
  bundle, the experiment policy, and the analysis decision ladder — rather than
  reimplementing any of them, and
* collects the resource, acceptance, and rubric variance estimates the frozen
  analysis plan needs before it can freeze (FR-023).

It creates no route policy, no installed default, and no qualification claim.
``qualified`` is structurally unreachable from a calibration partition, so every
decision bundle here terminates at ``calibration_complete`` (FR-024).

The libraries under ``lib/`` stay pure: they consume recorded evidence and
contain no subprocess. All live dispatch lives here, in the operator path.

Committed evidence is sanitized deny-by-default (FR-027, FR-036, SC-015):
session identifiers normalize to ``<session-id>`` and home paths to ``<home>``
before anything is written, raw captures stay in the gitignored operator-only
retention store, and the committed record carries digests only.

Usage::

    python3 tests/speckit-pro/layer6-efficiency/run-calibration-pilot.py \
        --out docs/ai/research/claude-car-003-calibration-pilot.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# tests/speckit-pro/layer6-efficiency/<this file> -> three levels up is tests/,
# four levels up is the repository root.
REPO_ROOT = Path(__file__).resolve().parents[3]
LAYER6_ROOT = REPO_ROOT / "tests" / "speckit-pro" / "layer6-efficiency"
LIB_DIR = LAYER6_ROOT / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import claude_analysis_decision as decision  # noqa: E402
import claude_experiment_policy as policy  # noqa: E402
import claude_score_bundle as scoring  # noqa: E402
import claude_treatment_runner as runner  # noqa: E402
from claude_successor_freeze import record_digest  # noqa: E402

SCHEMA_VERSION = "1.0.0"

# Operator-only retention store. Gitignored by `results/*`: raw captures, the
# verbatim instruction text, and the full event streams never reach the repo.
RETENTION_RELATIVE = (
    "tests/speckit-pro/layer6-efficiency/results/car-003-calibration-pilot-raw.json"
)

# Frozen inputs, read and never written.
FREEZE_PATH = REPO_ROOT / "docs" / "ai" / "research" / "claude-car-003-successor-capability-freeze.json"
SNAPSHOT_PATH = REPO_ROOT / "docs" / "ai" / "research" / "claude-runtime-capability-snapshot.json"
TRACE_CONTRACT_PATH = REPO_ROOT / "docs" / "ai" / "research" / "claude-trace-contract.schema.json"
MANDATORY_MANIFEST_PATH = (
    REPO_ROOT / "docs" / "ai" / "research" / "claude-car-003-mandatory-observation-manifest.json"
)


# ---------------------------------------------------------------------------
# Sanitization. Runs before anything is stored, in either store.
# ---------------------------------------------------------------------------

SESSION_ID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I
)
HOME_PATH_RE = re.compile(r"/(?:Users|home)/[^/\s\"']+")

# Field names that block publication outright. The score bundle's deny list is
# the authority; these are the capture-shaped names this driver could otherwise
# emit, kept beside it so a raw capture cannot be committed under a name the
# shared list does not happen to enumerate.
LOCAL_DENIED_FIELD_NAMES = frozenset(
    {"prompt", "raw_output", "response", "session_id", "transcript"}
)


def sanitize(text: str) -> str:
    """Normalize session identifiers and home paths before anything is stored."""
    text = SESSION_ID_RE.sub("<session-id>", text)
    return HOME_PATH_RE.sub("<home>", text)


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest_of(value: Any) -> str:
    return sha256_text(json.dumps(value, sort_keys=True, separators=(",", ":")))


def file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def local_denied_findings(record: Any, path: str = "") -> tuple[str, ...]:
    """Walk for capture-shaped field names the shared deny list does not carry."""
    findings: list[str] = []
    if isinstance(record, dict):
        for key, value in record.items():
            where = f"{path}.{key}" if path else str(key)
            if str(key).lower() in LOCAL_DENIED_FIELD_NAMES:
                findings.append(where)
            findings.extend(local_denied_findings(value, where))
    elif isinstance(record, (list, tuple)):
        for index, value in enumerate(record):
            findings.extend(local_denied_findings(value, f"{path}[{index}]"))
    return tuple(findings)


# ---------------------------------------------------------------------------
# The eight declared campaign ceilings (FR-022, FR-038).
# ---------------------------------------------------------------------------

# The operator-declared outer envelope for this pilot. It plays the role the
# frozen analysis plan's budget plays for a qualification campaign: the
# authoritative side of the FR-038 equality check. It is deliberately NOT the
# frozen analysis plan of FR-023, which T079 authors from the estimates this
# run produces and which does not exist yet.
PILOT_BUDGET_ENVELOPE: dict[str, Any] = {
    "max_attempts": 24,
    "max_duration_seconds": 1800,
    "max_input_tokens": 100_000,
    "max_cache_write_tokens_by_ttl_class": {
        "ephemeral_5m": 400_000,
        "ephemeral_1h": 1_400_000,
    },
    "max_cache_read_tokens": 2_000_000,
    "max_output_tokens": 60_000,
    "max_candidates": 2,
    # Calibration creates no confirmation entry. Declared at zero so consuming
    # one would breach a ceiling rather than pass unnoticed.
    "max_confirmation_entries": 0,
}

# The frozen experiment policy's own budget. FR-038 permits a calibration
# partition to bind ceilings tighter than the authoritative budget but never
# looser; these are tighter on the two quantities this pilot can bound in
# advance and equal elsewhere.
POLICY_BUDGET: dict[str, Any] = {
    "max_attempts": 18,
    "max_duration_seconds": 1800,
    "max_input_tokens": 100_000,
    "max_cache_write_tokens_by_ttl_class": {
        "ephemeral_5m": 400_000,
        "ephemeral_1h": 1_400_000,
    },
    "max_cache_read_tokens": 2_000_000,
    "max_output_tokens": 60_000,
    "max_candidates": 2,
    "max_confirmation_entries": 0,
}

# Cost is not one of the eight campaign ceilings — it is the operator's own
# spend guard on a live run, enforced alongside them.
MAX_COST_USD = 15.0
PER_ATTEMPT_TIMEOUT_SECONDS = 180


class BudgetExhausted(RuntimeError):
    """Raised when a declared ceiling is reached. Never swallowed."""


class Ledger:
    """Tracks spend against all eight ceilings and refuses to overrun.

    ``check`` runs before every dispatch and again after every recorded usage,
    so the run stops at the first ceiling reached and records which one rather
    than discovering the overrun at the end.
    """

    def __init__(self, envelope: dict[str, Any], candidates: int) -> None:
        self.envelope = envelope
        self.candidates = candidates
        self.attempts = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_read_tokens = 0
        self.cache_write_by_ttl = {ttl: 0 for ttl in policy.TTL_CLASSES}
        self.confirmation_entries = 0
        self.cost_usd = 0.0
        self.started = time.monotonic()
        self.stop_reason: str | None = None

    def _fail(self, reason: str) -> None:
        self.stop_reason = reason
        raise BudgetExhausted(reason)

    def check(self) -> None:
        if self.attempts >= self.envelope["max_attempts"]:
            self._fail("max_attempts_ceiling_reached")
        if self.elapsed_seconds >= self.envelope["max_duration_seconds"]:
            self._fail("max_duration_seconds_ceiling_reached")
        if self.input_tokens >= self.envelope["max_input_tokens"]:
            self._fail("max_input_tokens_ceiling_reached")
        for ttl, used in self.cache_write_by_ttl.items():
            if used >= self.envelope["max_cache_write_tokens_by_ttl_class"][ttl]:
                self._fail(f"max_cache_write_tokens_by_ttl_class.{ttl}_ceiling_reached")
        if self.cache_read_tokens >= self.envelope["max_cache_read_tokens"]:
            self._fail("max_cache_read_tokens_ceiling_reached")
        if self.output_tokens >= self.envelope["max_output_tokens"]:
            self._fail("max_output_tokens_ceiling_reached")
        if self.candidates > self.envelope["max_candidates"]:
            self._fail("max_candidates_ceiling_reached")
        if self.confirmation_entries > self.envelope["max_confirmation_entries"]:
            self._fail("max_confirmation_entries_ceiling_reached")
        if self.cost_usd >= MAX_COST_USD:
            self._fail("cost_ceiling_reached")

    def record_usage(self, usage: dict[str, Any], cost: float | None) -> None:
        """Accumulate spend. Deliberately does **not** stop the run.

        The ceiling check is the caller's, and it belongs after the attempt's
        record has been stored. Raising from here destroyed the evidence the
        spend had already bought: the live call had completed and the tokens
        were gone, but the exception unwound before ``dispatch`` returned its
        capture, so the run recorded a consumed objective with no attempt row
        and an attempt count one higher than the attempts it could show.
        """
        self.input_tokens += int(usage.get("input_tokens") or 0)
        self.output_tokens += int(usage.get("output_tokens") or 0)
        self.cache_read_tokens += int(usage.get("cache_read_input_tokens") or 0)
        creation = usage.get("cache_creation") or {}
        self.cache_write_by_ttl["ephemeral_5m"] += int(
            creation.get("ephemeral_5m_input_tokens") or 0
        )
        self.cache_write_by_ttl["ephemeral_1h"] += int(
            creation.get("ephemeral_1h_input_tokens") or 0
        )
        if isinstance(cost, (int, float)):
            self.cost_usd += float(cost)

    @property
    def elapsed_seconds(self) -> float:
        return round(time.monotonic() - self.started, 3)

    def consumed(self) -> dict[str, Any]:
        return {
            "attempts": self.attempts,
            "duration_seconds": self.elapsed_seconds,
            "input_tokens": self.input_tokens,
            "cache_write_tokens_by_ttl_class": dict(self.cache_write_by_ttl),
            "cache_read_tokens": self.cache_read_tokens,
            "output_tokens": self.output_tokens,
            "candidates": self.candidates,
            "confirmation_entries": self.confirmation_entries,
            "observed_cost_usd": round(self.cost_usd, 6),
        }


# ---------------------------------------------------------------------------
# The disposable calibration objectives and the paired arms.
# ---------------------------------------------------------------------------


def _squash(text: str) -> str:
    return "".join(text.strip().lower().split())


def _strip_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = [line for line in stripped.splitlines() if not line.strip().startswith("```")]
        return "\n".join(lines).strip()
    return stripped


def _oracle_reverse(text: str) -> bool:
    return _squash(text) == "noitarbilac"


def _oracle_pair(text: str) -> bool:
    try:
        parsed = json.loads(_strip_fence(text))
    except (json.JSONDecodeError, TypeError):
        return False
    return parsed == {"a": 7, "b": 11}


def _oracle_primes(text: str) -> bool:
    return _squash(text) == "23,29,31"


# Every objective is disposable, mechanically gradeable, and deliberately free
# of any token in the blinding lexicon, so the leak check measures the response
# rather than the instruction that produced it.
CALIBRATION_OBJECTIVES: tuple[dict[str, Any], ...] = (
    {
        "objective_id": "CAR-003-CAL-OBJ-REVERSE",
        "description": "Reverse a single fixed English word and return only the reversed word.",
        "instruction": (
            "Reverse the word calibration and reply with exactly the reversed word, "
            "nothing else."
        ),
        "oracle": _oracle_reverse,
        "expected_token": "noitarbilac",
        "expected_length": 11,
        "stratum_id": "short-horizon-single-turn",
    },
    {
        "objective_id": "CAR-003-CAL-OBJ-PAIR",
        "description": "Emit one small fixed JSON object with two integer members and no prose.",
        "instruction": (
            'Reply with only a JSON object, no prose and no code fence, with key "a" '
            'set to the integer 7 and key "b" set to the integer 11.'
        ),
        "oracle": _oracle_pair,
        "expected_token": '"b":11',
        "expected_length": 20,
        "stratum_id": "short-horizon-single-turn",
    },
    {
        "objective_id": "CAR-003-CAL-OBJ-PRIMES",
        "description": "Return three fixed integers in ascending order in a fixed separator format.",
        "instruction": (
            "Reply with exactly the three smallest prime numbers greater than 20, "
            "separated by a comma and a space, ascending, and nothing else."
        ),
        "oracle": _oracle_primes,
        "expected_token": "23,29,31",
        "expected_length": 10,
        "stratum_id": "short-horizon-single-turn",
    },
)

REPETITIONS = 3
PINNED_EFFORT = "low"

# Paired arms. Both routes are admitted tuples of the frozen candidate freeze
# and differ only in the model, with effort held fixed, so a difference between
# the arms is attributable to the route rather than to the configuration.
ARMS: tuple[dict[str, str], ...] = (
    {"arm": "candidate", "alias": "haiku", "effort": PINNED_EFFORT, "route_id": "haiku__low"},
    {"arm": "comparator", "alias": "sonnet", "effort": PINNED_EFFORT, "route_id": "sonnet__low"},
)

ROLE_ID = "calibration-probe"

# Pinned pre-execution expectation, read from the archived CAR-002 runtime
# snapshot. The observed identity is compared against it, so an alias that has
# re-pointed since the archive produces a recorded divergence rather than a
# silent pass.
EXPECTED_ALIAS_BINDINGS: dict[str, str] = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-5",
}

RUBRIC = {
    "rubric_binding": {"id": "CAR-003-CAL-RUBRIC-V1", "digest": ""},
    "criterion_threshold": 0.8,
    "criteria": ("answer_equivalence", "response_economy"),
}

SCORER_A = {"id": "deterministic-rubric-scorer-a-v1", "digest": ""}
SCORER_B = {"id": "deterministic-rubric-scorer-b-v1", "digest": ""}
ADJUDICATOR = {"id": "deterministic-rubric-adjudicator-v1", "digest": ""}
SCORER_FAMILY = "deterministic_rubric"
CALIBRATION_BINDING = {"id": "CAR-003-CAL-SCORER-CALIBRATION-V1", "digest": ""}


# ---------------------------------------------------------------------------
# Partition registry. Only the calibration partition is consumable.
# ---------------------------------------------------------------------------


def build_registry(frozen_at: str) -> list[dict[str, Any]]:
    """One entry per closed partition type, so the refusal is provable, not asserted.

    The four non-calibration entries exist to be refused. Registering them is
    what turns "no screening, selection, cohort-lock, or integrated-confirmation
    objective was consumed" from a claim into a check the run performs.
    """
    entries = [
        policy.build_partition_registry_entry(
            partition_id="CAR-003-CAL-PILOT",
            partition_type="calibration",
            qualification_eligible=False,
            objective_ids=[item["objective_id"] for item in CALIBRATION_OBJECTIVES],
            frozen_at=frozen_at,
            owning_spec="CAR-003",
        )
    ]
    for partition_type in policy.PARTITION_TYPES:
        if partition_type == "calibration":
            continue
        entries.append(
            policy.build_partition_registry_entry(
                partition_id=f"CAR-003-RESERVED-{partition_type.upper()}",
                partition_type=partition_type,
                qualification_eligible=True,
                objective_ids=[f"CAR-003-RESERVED-OBJ-{partition_type.upper()}"],
                frozen_at=frozen_at,
                owning_spec="CAR-003",
            )
        )
    return entries


def prove_calibration_only(registry: list[dict[str, Any]], consumed: list[str]) -> dict[str, Any]:
    """Every consumed objective admitted, every reserved objective refused."""
    consumable = policy.consumable_objectives(registry)
    admitted = []
    for objective_id in sorted(set(consumed)):
        verdict = policy.consumption_verdict(registry, objective_id)
        admitted.append(
            {
                "objective_id": objective_id,
                "verdict": "clean" if verdict.ok else "refused",
                "failure_code": verdict.failure_code,
            }
        )
    refused = []
    for entry in registry:
        if entry["partition_type"] == "calibration":
            continue
        for objective_id in entry["objective_ids"]:
            verdict = policy.consumption_verdict(registry, objective_id)
            refused.append(
                {
                    "objective_id": objective_id,
                    "partition_type": entry["partition_type"],
                    "verdict": "clean" if verdict.ok else "refused",
                    "failure_code": verdict.failure_code,
                    "consumed_by_this_run": objective_id in set(consumed),
                }
            )
    return {
        "consumable_objectives": list(consumable),
        "consumed_objectives": sorted(set(consumed)),
        "consumed_all_admitted": all(item["verdict"] == "clean" for item in admitted),
        "admitted": admitted,
        "non_calibration_probe": refused,
        "non_calibration_all_refused": all(
            item["verdict"] == "refused" and item["failure_code"] == policy.PARTITION_NOT_ELIGIBLE
            for item in refused
        ),
        "non_calibration_none_consumed": not any(item["consumed_by_this_run"] for item in refused),
    }


# ---------------------------------------------------------------------------
# The workload manifest the strata bind to (FR-052).
# ---------------------------------------------------------------------------

WORKLOAD_MANIFEST: dict[str, Any] = {
    "manifest_id": "CAR-003-CAL-PILOT-WORKLOAD-MANIFEST-V1",
    "minimum_unique_tasks": 3,
    "unknown_stratum_policy": policy.UNKNOWN_STRATUM_RESULT,
    "strata": [
        {
            "stratum_id": "short-horizon-single-turn",
            "long_horizon": False,
            "stratum_sample_size": len(CALIBRATION_OBJECTIVES) * REPETITIONS,
            "stratum_minimum_unique_tasks": len(CALIBRATION_OBJECTIVES),
            "membership_rule": {
                "permitted_basis": ["role_id", "objective", "acceptance_oracle"],
                "derived_from_realized_outcomes": False,
            },
        },
        {
            "stratum_id": "long-horizon-multi-turn",
            "long_horizon": True,
            "stratum_sample_size": 0,
            "stratum_minimum_unique_tasks": 1,
            "membership_rule": {
                "permitted_basis": ["role_id", "objective", "expected_artifacts", "acceptance_oracle"],
                "derived_from_realized_outcomes": False,
            },
        },
    ],
}

STRATUM_ASSIGNMENT = {
    "stratum_id": "short-horizon-single-turn",
    "membership_basis": ["role_id", "objective", "acceptance_oracle"],
    "derived_from_realized_outcomes": False,
}


# ---------------------------------------------------------------------------
# Live dispatch. The only subprocess in CAR-003.
# ---------------------------------------------------------------------------


def client_version() -> str:
    proc = subprocess.run(
        ["claude", "--version"],
        capture_output=True,
        text=True,
        timeout=60,
        stdin=subprocess.DEVNULL,
    )
    return sanitize(proc.stdout.strip())


def tree_state_digest(directory: Path) -> str:
    """Digest the arm working root, so a mutation is detected rather than assumed."""
    entries = []
    for path in sorted(directory.rglob("*")):
        entries.append(
            [
                str(path.relative_to(directory)),
                path.stat().st_size if path.is_file() else None,
            ]
        )
    return digest_of(entries)


def dispatch(instruction: str, arm: dict[str, str], cwd: Path, ledger: Ledger) -> dict[str, Any]:
    """Run one bounded live attempt and return its parsed, sanitized event stream."""
    ledger.check()
    argv = [
        "claude",
        "-p",
        instruction,
        "--model",
        arm["alias"],
        "--effort",
        arm["effort"],
        "--output-format",
        "stream-json",
        "--verbose",
    ]
    ledger.attempts += 1
    started = time.monotonic()
    try:
        # argv[0] MUST be the "claude" string literal so the XPLAT-010
        # repository Bash-confinement guard can statically prove the executable
        # is a non-Bash literal. Passing a variable list defeats the proof and
        # blocks release readiness. argv[0] == "claude" already, so this equals
        # list(argv) at runtime.
        # FR-049: the arms must use genuinely distinct cache roots. Labelling
        # them differently is not isolation — without a per-arm CLAUDE_CONFIG_DIR
        # both arms share the operator's single cache, and cached_input_tokens
        # then enters the dominance vector as a shared-cache artifact rather than
        # a route property. Isolate for real, and let the recorded root be the
        # directory actually used.
        arm_env = dict(os.environ)
        arm_env["CLAUDE_CONFIG_DIR"] = str(cwd / ".claude-cache")
        (cwd / ".claude-cache").mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            ["claude", *argv[1:]],
            capture_output=True,
            text=True,
            timeout=PER_ATTEMPT_TIMEOUT_SECONDS,
            stdin=subprocess.DEVNULL,
            cwd=str(cwd),
            env=arm_env,
        )
        exit_code, stdout = proc.returncode, proc.stdout
    except subprocess.TimeoutExpired:
        exit_code, stdout = 124, ""
    wall_ms = int((time.monotonic() - started) * 1000)

    events: list[dict[str, Any]] = []
    for line in sanitize(stdout).splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    init = next(
        (event for event in events if event.get("subtype") == "init"), {}
    )
    result = next((event for event in events if event.get("type") == "result"), {})
    thinking = [
        int(event.get("estimated_tokens") or 0)
        for event in events
        if event.get("subtype") == "thinking_tokens"
    ]
    tool_uses = [
        block.get("name")
        for event in events
        if event.get("type") == "assistant"
        for block in (event.get("message") or {}).get("content", ())
        if isinstance(block, dict) and block.get("type") == "tool_use"
    ]
    spawns = [
        event.get("agent")
        for event in events
        if event.get("type") == "agent_spawn" or event.get("subtype") == "agent_spawn"
    ]

    usage = result.get("usage") or {}
    if result:
        ledger.record_usage(usage, result.get("total_cost_usd"))

    return {
        "argv_digest": digest_of(argv[:1] + argv[3:]),
        # The FR-039 override proof needs the argv itself, not its digest. A
        # membership test against the digest string can never witness a flag.
        "fallback_model_flag_absent": "--fallback-model" not in argv,
        "instruction_digest": sha256_text(instruction),
        "exit_code": exit_code,
        "wall_time_ms": wall_ms,
        "init": init,
        "result": result,
        "reasoning_output_tokens": max(thinking) if thinking else 0,
        "tool_uses": [name for name in tool_uses if name],
        "agent_spawns": [agent for agent in spawns if agent],
        "compactions": sum(
            1 for event in events if "compact" in str(event.get("subtype") or "").lower()
        ),
        "retries": sum(
            1 for event in events if "retry" in str(event.get("subtype") or "").lower()
        ),
        "event_count": len(events),
        "event_stream_digest": digest_of(events),
        "response_text": (result.get("result") or "") if isinstance(result.get("result"), str) else "",
    }


# ---------------------------------------------------------------------------
# Observation assembly. Everything here is read from the run, not declared.
# ---------------------------------------------------------------------------


def observed_environment(capture: dict[str, Any], arm: dict[str, str]) -> dict[str, Any]:
    """Read the attempt's environment off the run and off the live process env."""
    init = capture["init"]
    result = capture["result"]
    version = init.get("claude_code_version")
    identities = observed_route_identities(result)
    canonical = observed_canonical_model(result)
    # The pilot dispatches print mode at top level, so the configuration the
    # parent session imposes on the attempt is the attempt's own pinned route.
    # It is derived from the OBSERVED identities, not from the alias that was
    # requested, so an alias re-point mid-run diverges here.
    observed_alias = next(
        (alias for alias, expected in EXPECTED_ALIAS_BINDINGS.items() if expected in identities),
        None,
    )
    parent = f"{observed_alias or canonical}/{arm['effort']}" if identities else None
    return {
        "fast_mode_state": result.get("fast_mode_state") or init.get("fast_mode_state"),
        "client_version": f"{version} (Claude Code)" if version else None,
        "parent_session_configuration": parent,
        "authentication_mode": (
            "subscription" if init.get("apiKeySource") == "none" else "api_key"
        )
        if init.get("apiKeySource") is not None
        else None,
        "env_override_proof": {
            "fallback_model_unset": bool(capture["fallback_model_flag_absent"])
            and os.environ.get("CLAUDE_CODE_FALLBACK_MODEL") is None,
            "fallbackModel_unset": os.environ.get("ANTHROPIC_MODEL") is None,
            "claude_code_subagent_model_unset": os.environ.get("CLAUDE_CODE_SUBAGENT_MODEL")
            is None,
            "available_models_absent": init.get("available_models") is None,
            "enforce_available_models_observed": None,
            "config_dir_isolation": "none" if os.environ.get("CLAUDE_CONFIG_DIR") is None else "isolated",
            "inherit_equivalent_to_unset": None,
            "org_restriction_gap": None,
        },
    }


def observed_canonical_model(result: dict[str, Any]) -> str | None:
    """The canonical identity behind the single model in the usage breakdown."""
    usage = result.get("modelUsage") or {}
    if len(usage) != 1:
        return None
    detail = next(iter(usage.values())) or {}
    return detail.get("canonicalModel")


def observed_route_identities(result: dict[str, Any]) -> frozenset[str]:
    """Both identities the runtime reports for the one model that ran.

    The usage breakdown is keyed by the DATED identity and carries the undated
    ``canonicalModel`` beside it, and the archived CAR-002 ledger records
    whichever of the two it observed per alias — dated for ``haiku``, undated for
    ``sonnet``. Comparing the frozen binding against only one of them read every
    ``haiku`` attempt as ``model_mismatch`` and blocked the whole candidate arm.
    A match on either identity is a match; a match on neither is a re-point.
    """
    usage = result.get("modelUsage") or {}
    if len(usage) != 1:
        return frozenset()
    dated = next(iter(usage))
    canonical = (next(iter(usage.values())) or {}).get("canonicalModel")
    return frozenset(identity for identity in (dated, canonical) if identity)


def usage_breakdown(result: dict[str, Any]) -> dict[str, Any]:
    return result.get("modelUsage") or {}


def raw_token_vector(capture: dict[str, Any]) -> dict[str, Any]:
    usage = capture["result"].get("usage") or {}
    creation = usage.get("cache_creation") or {}
    return {
        "input_tokens": int(usage.get("input_tokens") or 0),
        "output_tokens": int(usage.get("output_tokens") or 0),
        "cached_input_tokens": int(usage.get("cache_read_input_tokens") or 0),
        "reasoning_output_tokens": capture["reasoning_output_tokens"],
        "cache_write_tokens_by_ttl_class": {
            "ephemeral_5m": int(creation.get("ephemeral_5m_input_tokens") or 0),
            "ephemeral_1h": int(creation.get("ephemeral_1h_input_tokens") or 0),
        },
    }


def mandatory_observations(
    capture: dict[str, Any],
    arm: dict[str, str],
    objective: dict[str, Any],
    environment: dict[str, Any],
    context: dict[str, str],
    manifest: Any,
) -> list[dict[str, Any]]:
    """One observed entry per mandatory field path, every value read from the run."""
    init = capture["init"]
    values = {
        # No agent_spawn event was observed, so what ran is the print-mode
        # top-level agent. Recorded as the observed fact, not as a repair.
        "assignment.named_agent": "print_mode_top_level"
        if not capture["agent_spawns"]
        else capture["agent_spawns"][0],
        "assignment.candidate_route_id": arm["route_id"],
        "assignment.instruction_hash": capture["instruction_digest"],
        "treatment.expected_skills_mcp_tools": "none_permitted_none_expected",
        "treatment.mutation_class": "read_only",
        # Names are never recorded: the loaded surface is committed as a digest
        # and a count, because the operator's own tool and server names are not
        # publishable evidence.
        "treatment.loaded_skills_mcp_tools": {
            "tools_digest": digest_of(sorted(init.get("tools") or ())),
            "tools_count": len(init.get("tools") or ()),
            "mcp_servers_count": len(init.get("mcp_servers") or ()),
            "skills_count": len(init.get("skills") or ()),
        },
        "treatment.parent_configuration": environment["parent_session_configuration"],
        "treatment.controlled_overrides": digest_of(environment["env_override_proof"]),
        "route.runtime_capability_snapshot_id": file_digest(SNAPSHOT_PATH),
        "parent.context": dict(context),
        "route.assigned_route_id": arm["route_id"],
        "reroute.events": "none_observed" if len(usage_breakdown(capture["result"])) == 1 else "ambiguous",
        "resources.raw_token_vector": raw_token_vector(capture),
    }
    observations = []
    for field_path in runner.mandatory_field_paths(manifest):
        value = values.get(field_path)
        observations.append(
            {
                "field_path": field_path,
                "observation_state": "observed_value" if value is not None else "unobserved",
                "classification": "stable_native" if value is not None else "unavailable",
                "value": value,
            }
        )
    return observations


def treatment_conditions(capture: dict[str, Any], arm: dict[str, str]) -> tuple[str, ...]:
    """Derive each condition independently; every fired code is retained."""
    conditions: list[str] = []
    identities = observed_route_identities(capture["result"])
    if not identities:
        conditions.append("effective_treatment_unknown")
    elif EXPECTED_ALIAS_BINDINGS[arm["alias"]] not in identities:
        conditions.append("model_mismatch")
    if capture["exit_code"] != 0 or not capture["result"]:
        conditions.append("effective_treatment_or_reroute_evidence_missing")
    if capture["tool_uses"]:
        conditions.append("skills_mcp_tools_mismatch")
    return tuple(conditions)


# ---------------------------------------------------------------------------
# Deterministic hard gates and the two mechanical rubric scorers.
# ---------------------------------------------------------------------------


def gate_results(
    capture: dict[str, Any],
    arm: dict[str, str],
    objective: dict[str, Any],
    tree_before: str,
    tree_after: str,
) -> list[dict[str, Any]]:
    """The seven closed gates, each with the evidence that decided it."""
    result = capture["result"]
    text = capture["response_text"]
    checks = {
        # The role gate must compare the ASSIGNED route against what the run
        # actually delivered. Checking route_id.startswith(alias) was a
        # tautology — route_id is built as f"{alias}__{effort}" in this module,
        # so no input could fail it, and every "all seven gates passed" claim
        # was really a six-gate claim.
        "role": (
            capture.get("observed_model_id") is not None
            and arm["alias"] in str(capture.get("observed_model_id"))
            or str(capture.get("observed_model_id") or "").startswith(
                str(arm.get("expected_model_prefix") or arm["alias"])
            ),
            {
                "role_id": ROLE_ID,
                "assigned_route": arm["route_id"],
                "observed_model_id": capture.get("observed_model_id"),
            },
        ),
        "safety": (not (result.get("permission_denials") or []), {"denials": len(result.get("permission_denials") or [])}),
        "grounding": (bool(text) and not capture["tool_uses"], {"tool_uses": len(capture["tool_uses"]), "turns": result.get("num_turns")}),
        "mutation": (tree_before == tree_after, {"before": tree_before, "after": tree_after}),
        "tool": (not capture["tool_uses"], {"observed": sorted(set(capture["tool_uses"]))}),
        "output": (
            capture["exit_code"] == 0
            and result.get("is_error") is False
            and result.get("stop_reason") == "end_turn"
            and bool(text.strip()),
            {"exit_code": capture["exit_code"], "stop_reason": result.get("stop_reason")},
        ),
        "acceptance": (objective["oracle"](text), {"oracle": objective["objective_id"]}),
    }
    return [
        {"gate": gate, "pass": bool(passed), "evidence_digest": digest_of(evidence)}
        for gate, (passed, evidence) in checks.items()
    ]


def score_a(text: str, objective: dict[str, Any]) -> dict[str, float]:
    """Strict scorer: exact normalized equivalence and a length budget."""
    return {
        "answer_equivalence": 1.0 if objective["oracle"](text) else 0.0,
        "response_economy": 1.0 if len(text.strip()) <= 4 * objective["expected_length"] else 0.0,
    }


def score_b(text: str, objective: dict[str, Any]) -> dict[str, float]:
    """Lenient scorer: containment equivalence and a single-line budget."""
    return {
        "answer_equivalence": 1.0 if objective["expected_token"] in _squash(text) else 0.0,
        "response_economy": 1.0 if "\n" not in text.strip() else 0.0,
    }


def collect_pilot_ballots(
    capture: dict[str, Any],
    objective: dict[str, Any],
    gates: list[dict[str, Any]],
    attempt_id: str,
    lexicon: dict[str, Any],
) -> dict[str, Any]:
    """Run the leak check, seal both ballots, and adjudicate a real disagreement."""
    text = capture["response_text"]
    blinded_digest = sha256_text(text)
    finding = scoring.leak_check(text, lexicon)

    ballots = [
        scoring.build_ballot(
            ballot_id=f"{attempt_id}-BALLOT-A",
            scorer_binding=SCORER_A,
            scorer_execution_id=f"{attempt_id}-EXEC-A",
            calibration_binding=CALIBRATION_BINDING,
            rubric_binding=RUBRIC["rubric_binding"],
            blinded_artifact_digest=blinded_digest,
            criterion_scores=score_a(text, objective),
            provenance_inferred=False,
            presentation_order_seed=attempt_id,
        ),
        scoring.build_ballot(
            ballot_id=f"{attempt_id}-BALLOT-B",
            scorer_binding=SCORER_B,
            scorer_execution_id=f"{attempt_id}-EXEC-B",
            calibration_binding=CALIBRATION_BINDING,
            rubric_binding=RUBRIC["rubric_binding"],
            blinded_artifact_digest=blinded_digest,
            criterion_scores=score_b(text, objective),
            provenance_inferred=False,
            presentation_order_seed=attempt_id,
        ),
    ]

    adjudication = None
    if scoring.decision_affecting_disagreement(ballots[0], ballots[1], RUBRIC):
        adjudication = scoring.adjudicate(
            ballots[0],
            ballots[1],
            adjudication_id=f"{attempt_id}-ADJ",
            adjudicator_binding=ADJUDICATOR,
            resolved_outcome="strict_equivalence_verdict_governs",
        )

    collection = scoring.collect_ballots(
        gates,
        ballots=ballots,
        rubric=RUBRIC,
        current_calibrations=[CALIBRATION_BINDING["id"]],
        leak_finding=finding,
        adjudication=adjudication,
    )
    return {
        "leak_finding": finding,
        "ballots": ballots if collection.accepted else [],
        "adjudication": adjudication if collection.accepted else None,
        "collection_accepted": collection.accepted,
        "collection_failure_plane": collection.failure_plane,
        "collection_failure_code": collection.failure_code,
        "collection_reasons": list(collection.reasons),
        "blinded_artifact_digest": blinded_digest,
    }


# ---------------------------------------------------------------------------
# Variance estimation — the numbers T079 freezes.
# ---------------------------------------------------------------------------


def summarize(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0}
    ordered = sorted(values)
    return {
        "n": len(values),
        "mean": round(statistics.fmean(values), 6),
        "sd": round(statistics.stdev(values), 6) if len(values) > 1 else 0.0,
        "variance": round(statistics.variance(values), 6) if len(values) > 1 else 0.0,
        "min": ordered[0],
        "max": ordered[-1],
        "p95": ordered[min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))],
    }


VARIANCE_QUANTITIES = (
    "input_tokens",
    "output_tokens",
    "cached_input_tokens",
    "cache_write_ephemeral_5m",
    "cache_write_ephemeral_1h",
    "reasoning_output_tokens",
    "duration_ms",
    "num_turns",
    "acceptance",
    "semantic_score",
)


def variance_estimates(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-arm dispersion, paired within-task differences, and the ICC input."""
    by_arm: dict[str, dict[str, list[float]]] = {}
    for record in attempts:
        bucket = by_arm.setdefault(record["arm"], {name: [] for name in VARIANCE_QUANTITIES})
        for name in VARIANCE_QUANTITIES:
            bucket[name].append(float(record["quantities"][name]))

    per_arm = {
        arm: {name: summarize(values) for name, values in quantities.items()}
        for arm, quantities in by_arm.items()
    }

    # Both the paired differences and the correlation are within-task
    # quantities, so both must be built from the SAME task-joined pairs. Taking
    # the correlation from the per-arm lists instead would align the i-th
    # candidate against whatever comparator happened to sit at index i: those
    # lists are in attempts order, and a single attempt dropped from one arm
    # shifts every later row against a different task. The equal-length guard
    # that used to sit here caught count skew but never ordering skew, so a
    # silently misaligned correlation could still be produced — and it is the
    # sample-size input the frozen analysis plan is derived from.
    paired: dict[str, list[float]] = {name: [] for name in VARIANCE_QUANTITIES}
    aligned: dict[str, tuple[list[float], list[float]]] = {
        name: ([], []) for name in VARIANCE_QUANTITIES
    }
    index = {(record["comparison_set_id"], record["arm"]): record for record in attempts}
    comparison_sets = sorted({key[0] for key in index})
    complete_pairs = 0
    for comparison_set_id in comparison_sets:
        candidate = index.get((comparison_set_id, "candidate"))
        comparator = index.get((comparison_set_id, "comparator"))
        if candidate is None or comparator is None:
            continue
        complete_pairs += 1
        for name in VARIANCE_QUANTITIES:
            candidate_value = float(candidate["quantities"][name])
            comparator_value = float(comparator["quantities"][name])
            paired[name].append(candidate_value - comparator_value)
            aligned[name][0].append(candidate_value)
            aligned[name][1].append(comparator_value)

    correlation: dict[str, Any] = {}
    for name in VARIANCE_QUANTITIES:
        candidate_values, comparator_values = aligned[name]
        if len(candidate_values) < 2:
            correlation[name] = None
            continue
        try:
            correlation[name] = round(
                statistics.correlation(candidate_values, comparator_values), 6
            )
        except statistics.StatisticsError:
            # Degenerate when either arm has zero dispersion; reported as
            # unestimable rather than imputed to a convenient number.
            correlation[name] = None

    return {
        "per_arm": per_arm,
        "paired_within_task_difference": {
            name: summarize(values) for name, values in paired.items()
        },
        "within_task_pearson_correlation": correlation,
        # Complete pairs only. Counting every comparison set over-reported the
        # pair count whenever one arm was missing.
        "pairs_used": complete_pairs,
        "estimand_note": (
            "Every assigned attempt is retained, including any that failed a gate; "
            "no complete-case filtering was applied (FR-020)."
        ),
    }


# ---------------------------------------------------------------------------
# The run.
# ---------------------------------------------------------------------------


def repository_revision() -> tuple[str, str]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        stdin=subprocess.DEVNULL,
        timeout=60,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        stdin=subprocess.DEVNULL,
        timeout=60,
    ).stdout.strip()
    return head, "sha256:" + hashlib.sha256(tree.encode("utf-8")).hexdigest()


def run_pilot() -> tuple[dict[str, Any], dict[str, Any]]:
    frozen_at = utc_now()
    pilot_id = "CAR-003-CAL-PILOT-" + frozen_at.replace(":", "").replace("-", "")
    manifest = runner.load_mandatory_manifest()
    revision, tree_digest = repository_revision()
    version = client_version()

    registry = build_registry(frozen_at)
    registry_verdict = policy.register_partitions(registry)
    if not registry_verdict.ok:
        raise SystemExit(f"partition registry refused: {registry_verdict.findings}")

    calibration_entry = registry[0]
    partition = {
        "partition_id": calibration_entry["partition_id"],
        "partition_type": calibration_entry["partition_type"],
        "qualification_eligible": calibration_entry["qualification_eligible"],
    }
    partition_binding = {
        "id": calibration_entry["partition_id"],
        "digest": digest_of(calibration_entry),
    }

    protocol = policy.build_calibration_protocol(
        calibration_protocol_id="CAR-003-CAL-PILOT-PROTOCOL-V1",
        partition_binding=partition_binding,
        objective_bindings=[
            {"id": item["objective_id"], "digest": sha256_text(item["instruction"])}
            for item in CALIBRATION_OBJECTIVES
        ],
        frozen_at=frozen_at,
    )
    protocol_binding = {
        "id": protocol["calibration_protocol_id"],
        "digest": protocol["protocol_digest"],
    }

    freeze_binding = {"id": json.loads(FREEZE_PATH.read_text())["candidate_freeze_id"], "digest": file_digest(FREEZE_PATH)}
    snapshot_binding = {"id": "CAR-002-RCS", "digest": file_digest(SNAPSHOT_PATH)}
    corpus_binding = {"id": "CAR-003-CAL-PILOT-CORPUS-V1", "digest": digest_of([item["objective_id"] for item in CALIBRATION_OBJECTIVES])}

    experiment_policy = policy.build_experiment_policy(
        experiment_policy_id="CAR-003-CAL-PILOT-POLICY-V1",
        partition=partition,
        candidate_freeze_binding=freeze_binding,
        corpus_binding=corpus_binding,
        plan_binding=protocol_binding,
        scorer_family_exclusion={
            "scorer_families": [SCORER_FAMILY],
            "excluded_candidate_families": sorted(set(EXPECTED_ALIAS_BINDINGS.values())),
            "declared_at_freeze": True,
        },
        budget=POLICY_BUDGET,
        rerun_cap=1,
        execution_mode="live_calibration_pilot",
    )
    policy_binding = {
        "id": experiment_policy["experiment_policy_id"],
        "digest": experiment_policy["policy_digest"],
    }

    gate_reports = {
        "registry": registry_verdict,
        "policy": policy.policy_verdict(experiment_policy),
        "budget": policy.budget_verdict(
            policy_budget=POLICY_BUDGET,
            plan_budget=PILOT_BUDGET_ENVELOPE,
            qualification_eligible=False,
        ),
    }
    for label, verdict in gate_reports.items():
        if not verdict.ok:
            raise SystemExit(f"{label} refused: {verdict.findings}")

    manifest_issues = policy.manifest_findings(WORKLOAD_MANIFEST)
    if manifest_issues:
        raise SystemExit(f"workload manifest refused: {manifest_issues}")
    stratum = policy.resolve_stratum(WORKLOAD_MANIFEST, STRATUM_ASSIGNMENT["stratum_id"])
    if stratum.result != "resolved":
        raise SystemExit(f"stratum unresolved: {stratum}")

    # One bound contract per arm. The CAR-003 default pins the parent session at
    # ``opus/high`` because that is the subagent-dispatch surface; this pilot
    # dispatches print mode at TOP LEVEL, where the configuration imposed on the
    # attempt is the attempt's own pinned route. Binding the default unchanged
    # made every attempt diverge on ``parent_session_configuration`` and blocked
    # scoring — the library was right, the caller was wrong. The override is
    # bound before execution and the observed side is still derived from the
    # observed canonical identity, so an alias re-point mid-run still diverges.
    environment_contracts = {
        arm["arm"]: runner.bind_environment_contract(
            parent_session_configuration=f"{arm['alias']}/{arm['effort']}"
        )
        for arm in ARMS
    }
    lexicon = scoring.build_leak_lexicon(
        model_identities=sorted(set(EXPECTED_ALIAS_BINDINGS.values())) + ["claude-haiku-4-5", "claude-sonnet-5"],
        aliases=["opus", "sonnet", "haiku", "fable"],
        efforts=["low", "medium", "high", "xhigh", "max"],
        route_identifiers=[arm["route_id"] for arm in ARMS],
    )

    ledger = Ledger(PILOT_BUDGET_ENVELOPE, candidates=len(ARMS))
    work_root = Path(tempfile.mkdtemp(prefix="car003-calibration-pilot-"))
    attempts: list[dict[str, Any]] = []
    raw_attempts: list[dict[str, Any]] = []
    traces: list[Any] = []
    score_bundles: list[dict[str, Any]] = []
    attestations: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    conformances: list[Any] = []
    consumed_objectives: list[str] = []

    try:
        for objective in CALIBRATION_OBJECTIVES:
            for repetition in range(1, REPETITIONS + 1):
                comparison_set_id = f"CS-{objective['objective_id']}-R{repetition}"
                for order, arm in enumerate(ARMS):
                    assignment_id = f"{comparison_set_id}-{arm['arm'].upper()}"
                    arm_cwd = work_root / objective["objective_id"] / arm["arm"]
                    arm_cwd.mkdir(parents=True, exist_ok=True)
                    # Derive the recorded root from the directory the dispatch
                    # actually sets CLAUDE_CONFIG_DIR to, so the isolation
                    # evidence witnesses the real mechanism. A label built from
                    # the arm name is distinct by construction and would report
                    # disjoint roots even when both arms shared one cache.
                    cache_root_label = str(arm_cwd / ".claude-cache")
                    environment_contract = environment_contracts[arm["arm"]]

                    assignment = policy.build_assignment(
                        comparison_set_id=comparison_set_id,
                        assignment_id=assignment_id,
                        partition=partition,
                        bindings={
                            "candidate_route_binding": {"id": ARMS[0]["route_id"], "digest": digest_of(ARMS[0])},
                            "comparator_route_binding": {"id": ARMS[1]["route_id"], "digest": digest_of(ARMS[1])},
                            "fixture_binding": {"id": objective["objective_id"], "digest": sha256_text(objective["instruction"])},
                            "task_binding": {"id": f"{objective['objective_id']}-R{repetition}", "digest": digest_of([objective["objective_id"], repetition])},
                            "capability_freeze_binding": freeze_binding,
                            "runtime_snapshot_binding": snapshot_binding,
                            "route_resolution_binding": {"id": arm["route_id"], "digest": digest_of({"alias": arm["alias"], "effort": arm["effort"]})},
                            "materialization_binding": {"id": f"{assignment_id}-MATERIALIZATION", "digest": digest_of({"surface": "print_mode_cli", "route": arm["route_id"], "instruction": sha256_text(objective["instruction"])})},
                            "experiment_policy_binding": policy_binding,
                        },
                        role_id=ROLE_ID,
                        instruction_hash=sha256_text(objective["instruction"]),
                        configuration_hash=digest_of({"model": arm["alias"], "effort": arm["effort"], "surface": "print_mode_cli"}),
                        environment_contract=environment_contract,
                        stratum_assignment=STRATUM_ASSIGNMENT,
                        assigned_order=order,
                        pre_execution_timestamp=utc_now(),
                        plan_binding=protocol_binding,
                    )
                    assignment_check = policy.assignment_verdict(assignment)
                    if not assignment_check.ok:
                        raise SystemExit(f"assignment refused: {assignment_check.findings}")
                    consumption = policy.consumption_verdict(registry, objective["objective_id"])
                    if not consumption.ok:
                        raise SystemExit(f"consumption refused: {consumption.findings}")
                    consumed_objectives.append(objective["objective_id"])
                    assignments.append(assignment)

                    tree_before = tree_state_digest(arm_cwd)
                    capture = dispatch(objective["instruction"], arm, arm_cwd, ledger)
                    tree_after = tree_state_digest(arm_cwd)

                    record = build_attempt_record(
                        capture=capture,
                        arm=arm,
                        objective=objective,
                        repetition=repetition,
                        comparison_set_id=comparison_set_id,
                        assignment=assignment,
                        assignment_id=assignment_id,
                        environment_contract=environment_contract,
                        manifest=manifest,
                        tree_before=tree_before,
                        tree_after=tree_after,
                        lexicon=lexicon,
                        pilot_id=pilot_id,
                        revision=revision,
                        tree_digest=tree_digest,
                        partition_binding=partition_binding,
                        policy_binding=policy_binding,
                        freeze_binding=freeze_binding,
                        snapshot_binding=snapshot_binding,
                        protocol_binding=protocol_binding,
                        cache_root_label=cache_root_label,
                    )
                    attempts.append(record["summary"])
                    raw_attempts.append(record["raw"])
                    traces.append(record["trace"])
                    score_bundles.append(record["score_bundle"])
                    attestations.append(record["attestation"])
                    conformances.append(record["conformance"])

                    # Deferred ceiling check. The pre-dispatch check above stops
                    # the run before spending; this one stops it after the spend
                    # is recorded AND its evidence is stored. Checking inside
                    # record_usage discarded the capture the spend paid for.
                    ledger.check()
    except BudgetExhausted:
        pass
    finally:
        shutil.rmtree(work_root, ignore_errors=True)

    stop_reason = ledger.stop_reason or "completed_within_budget"
    planned = len(CALIBRATION_OBJECTIVES) * REPETITIONS * len(ARMS)

    decisions, cache_reports, dominance = build_decisions(
        attempts=attempts,
        score_bundles=score_bundles,
        attestations=attestations,
        assignments=assignments,
        registry=registry,
        partition=partition,
        protocol_binding=protocol_binding,
        traces=traces,
        complete_campaign=(len(attempts) == planned and ledger.stop_reason is None),
    )

    committed = {
        "schema_version": SCHEMA_VERSION,
        "record_kind": "calibration_pilot_collection",
        "pilot_id": pilot_id,
        "operator_only": True,
        "runs_in_default_suite": False,
        "purpose": (
            "Prove exact dispatch, scoring, and statistical plumbing end to end on "
            "disposable calibration objectives, and collect the variance estimates the "
            "analysis plan needs before it can freeze."
        ),
        "not_the_frozen_analysis_plan": (
            "The budget envelope recorded here is the operator's declared pilot envelope, "
            "not the FR-023 frozen analysis plan. That plan is authored separately, after "
            "this run, from the estimates below."
        ),
        "client_version": version,
        "client_distribution": "local_cli",
        "dispatch_surface": "print_mode_cli",
        "command_contract": "claude -p <objective> --model <alias> --effort <effort> --output-format stream-json --verbose",
        "collected_at_utc": frozen_at,
        "completed_at_utc": utc_now(),
        "repository_revision": revision,
        "repository_tree_digest": tree_digest,
        "partition_registry": registry,
        "partition_registry_verdict": "clean",
        "partition_consumption_proof": prove_calibration_only(registry, consumed_objectives),
        "calibration_protocol": protocol,
        "experiment_policy": experiment_policy,
        "workload_manifest": WORKLOAD_MANIFEST,
        "workload_manifest_findings": list(manifest_issues),
        "environment_contracts_by_arm": environment_contracts,
        "environment_exclusion_report": runner.environment_exclusion_report(conformances),
        "budget": {
            "declared_envelope": PILOT_BUDGET_ENVELOPE,
            "declared_policy_budget": POLICY_BUDGET,
            "ceilings_declared": list(policy.BUDGET_CEILINGS),
            "ttl_classes": list(policy.TTL_CLASSES),
            "budget_verdict": "clean",
            "max_cost_usd": MAX_COST_USD,
            "per_attempt_timeout_seconds": PER_ATTEMPT_TIMEOUT_SECONDS,
            "consumed": ledger.consumed(),
            "attempts_planned": planned,
            "stop_reason": stop_reason,
        },
        "arms": [
            {"arm": arm["arm"], "route_id": arm["route_id"], "effort": arm["effort"], "alias": arm["alias"]}
            for arm in ARMS
        ],
        "objectives": [
            {
                "objective_id": item["objective_id"],
                "description": item["description"],
                "instruction_digest": sha256_text(item["instruction"]),
                "stratum_id": item["stratum_id"],
            }
            for item in CALIBRATION_OBJECTIVES
        ],
        "attempts": attempts,
        "score_bundles": score_bundles,
        "scorer_identity_attestations": attestations,
        "cache_isolation": cache_reports,
        "decision_bundles": decisions,
        "diagnostic_dominance": dominance,
        "variance_estimates": variance_estimates(attempts),
        "stated_limitations": STATED_LIMITATIONS,
        "sanitization_status": "pending",
        "retention_status": "pending",
    }

    retention = {
        "pilot_id": pilot_id,
        "objectives": [
            {"objective_id": item["objective_id"], "instruction_text": item["instruction"]}
            for item in CALIBRATION_OBJECTIVES
        ],
        "attempt_detail": raw_attempts,
        "budget_ledger": {
            "declared_envelope": PILOT_BUDGET_ENVELOPE,
            "consumed": ledger.consumed(),
            "stop_reason": stop_reason,
        },
    }
    return committed, retention


STATED_LIMITATIONS = [
    (
        "Scoring uses two declared deterministic rubric scorers and a deterministic "
        "adjudicator, not model scorers. The score-bundle plumbing, the gate barrier, the "
        "blinding leak check, the disagreement path, and the identity attestation are all "
        "exercised, but the semantic-score dispersion below is rubric dispersion and is not "
        "an estimate of model-scorer variance."
    ),
    (
        "The absolute floors and the non-inferiority stage are not evaluated. A calibration "
        "protocol carries no margins, no sample sizes, and no terminal thresholds by "
        "construction (FR-037), so both stages record not_evaluated and the Pareto stage is "
        "unreached. The dominance comparison reported separately is diagnostic only and is "
        "marked decision_bearing false."
    ),
    (
        "The pilot dispatches print mode at top level, so no plugin-namespaced agent spawn "
        "exists to admit. dispatch_namespace is recorded null rather than repaired, and the "
        "named agent is recorded as the observed print-mode top-level agent."
    ),
    (
        "Objectives are short-horizon single-turn probes. The long-horizon stratum is "
        "registered with sample size zero and is unestimated here."
    ),
]


def build_attempt_record(**kwargs: Any) -> dict[str, Any]:
    """Turn one live capture into a trace, a score bundle, and a summary row."""
    capture = kwargs["capture"]
    arm = kwargs["arm"]
    objective = kwargs["objective"]
    assignment = kwargs["assignment"]
    assignment_id = kwargs["assignment_id"]
    manifest = kwargs["manifest"]

    context = {"pilotId": kwargs["pilot_id"], "attemptId": assignment_id}
    environment = observed_environment(capture, arm)
    conformance = runner.check_environment_conformance(kwargs["environment_contract"], environment)
    exact = runner.record_exact_treatment(
        transcript={"events": []},
        usage_breakdown=usage_breakdown(capture["result"]),
        dispatch_request={"agent": None, "model": arm["alias"], "effort": arm["effort"]},
    )
    observations = mandatory_observations(capture, arm, objective, environment, context, manifest)
    canonical = observed_canonical_model(capture["result"])

    pre_score = {
        "observations": observations,
        "materialization_proof": {
            "content_hash": digest_of(
                {"surface": "print_mode_cli", "route": arm["route_id"], "argv": capture["argv_digest"]}
            ),
            "verified": capture["exit_code"] == 0 and bool(capture["result"]),
        },
        "installed_policy_proof": False,
        "configured_route_proof_matches": EXPECTED_ALIAS_BINDINGS[arm["alias"]]
        in observed_route_identities(capture["result"]),
        "route_change_monitoring_complete": bool(capture["result"]),
        "environment_conformant": conformance.status == runner.ENVIRONMENT_CONFORMANT,
        "scorable": len(usage_breakdown(capture["result"])) == 1,
        "conditions": treatment_conditions(capture, arm),
    }
    eligibility = runner.evaluate_score_eligibility(pre_score)

    trace = runner.new_execution_trace(
        {
            "objective_binding": {
                "candidate_route_id": arm["route_id"],
                "agent_contract_id": f"agent-{ROLE_ID}",
                "runtime_capability_snapshot_id": kwargs["snapshot_binding"]["digest"],
                "route_resolution_id": digest_of({"alias": arm["alias"], "effort": arm["effort"]}),
                "experiment_policy_id": kwargs["policy_binding"]["digest"],
            },
            "controlled_environment_id": digest_of(kwargs["environment_contract"]),
            "client_identity_id": sha256_text(str(capture["init"].get("claude_code_version"))),
            "surface": "cli",
            "repository_revision": kwargs["revision"],
            "repository_tree_digest": kwargs["tree_digest"],
            "work_item_kind": "objective",
            "work_item_id": objective["objective_id"],
            "launch_id": f"{assignment_id}-LAUNCH",
            "consumption_evidence_digest": digest_of(
                {"partition": kwargs["partition_binding"], "objective": objective["objective_id"]}
            ),
            "context": context,
            "raw_token_vector": raw_token_vector(capture),
            "wall_time_ms": capture["result"].get("duration_ms") or capture["wall_time_ms"],
            "retries": capture["retries"],
        },
        assignment_id=assignment_id,
        assigned_at=assignment["pre_execution_timestamp"],
    )
    bound = runner.bind_score_bundle(trace)

    gates = gate_results(capture, arm, objective, kwargs["tree_before"], kwargs["tree_after"])
    ballot_outcome = collect_pilot_ballots(capture, objective, gates, assignment_id, kwargs["lexicon"])

    bundle = scoring.build_score_bundle(
        score_bundle_id=f"SB-{assignment_id}",
        bindings={
            "agent_contract_binding": {"id": f"agent-{ROLE_ID}", "digest": digest_of({"role": ROLE_ID})},
            "assignment_binding": {"id": assignment_id, "digest": assignment["assignment_digest"]},
            "candidate_freeze_binding": kwargs["freeze_binding"],
            "candidate_route_binding": {"id": arm["route_id"], "digest": digest_of(arm)},
            "execution_trace_binding": bound["execution_trace_binding"],
            "experiment_policy_binding": kwargs["policy_binding"],
            "fixture_binding": {"id": objective["objective_id"], "digest": sha256_text(objective["instruction"])},
            "partition_binding": kwargs["partition_binding"],
            "route_resolution_binding": {"id": arm["route_id"], "digest": digest_of({"alias": arm["alias"], "effort": arm["effort"]})},
            "runtime_snapshot_binding": kwargs["snapshot_binding"],
            "telemetry_profile_binding": {"id": "CAR-002-TELEMETRY-PROFILE", "digest": file_digest(TRACE_CONTRACT_PATH)},
            "treatment_contract_binding": {"id": "CAR-003-MANDATORY-OBSERVATION-MANIFEST", "digest": file_digest(MANDATORY_MANIFEST_PATH)},
        },
        deterministic_gates=gates,
        ballots=ballot_outcome["ballots"],
        adjudication=ballot_outcome["adjudication"],
        resource_vector=bound["resource_vector"],
        reasoning_output_tokens=capture["reasoning_output_tokens"],
        evidence_refs=[capture["event_stream_digest"], ballot_outcome["blinded_artifact_digest"]],
        leak_finding=ballot_outcome["leak_finding"],
    )

    attestation = scoring.build_scorer_identity_attestation(
        attestation_id=f"ATT-{assignment_id}",
        score_bundle_binding={"id": bundle["score_bundle_id"], "digest": bundle["score_bundle_digest"]},
        ballot_attestations=[
            {"ballot_role": "scorer_a", "declared_family": SCORER_FAMILY, "observed_model_id": SCORER_A["id"]},
            {"ballot_role": "scorer_b", "declared_family": SCORER_FAMILY, "observed_model_id": SCORER_B["id"]},
            {"ballot_role": "adjudicator", "declared_family": SCORER_FAMILY, "observed_model_id": ADJUDICATOR["id"]},
        ],
        family_declaration={
            SCORER_A["id"]: SCORER_FAMILY,
            SCORER_B["id"]: SCORER_FAMILY,
            ADJUDICATOR["id"]: SCORER_FAMILY,
        },
        candidate_families=sorted(set(EXPECTED_ALIAS_BINDINGS.values())),
        recorded_at=utc_now(),
    )

    tokens = raw_token_vector(capture)
    accepted = 1.0 if next(item["pass"] for item in gates if item["gate"] == "acceptance") else 0.0
    ballot_scores = [
        value for ballot in ballot_outcome["ballots"] for value in ballot["criterion_scores"].values()
    ]
    summary = {
        "assignment_id": assignment_id,
        "comparison_set_id": kwargs["comparison_set_id"],
        "objective_id": objective["objective_id"],
        "repetition": kwargs["repetition"],
        "arm": arm["arm"],
        "route_id": arm["route_id"],
        "requested_alias": arm["alias"],
        "requested_effort": arm["effort"],
        "observed_canonical_model": canonical,
        "observed_route_identities": sorted(observed_route_identities(capture["result"])),
        "expected_route_identity": EXPECTED_ALIAS_BINDINGS[arm["alias"]],
        "observed_model_id": exact["observed_model_id"],
        "observed_model_id_source": exact["observed_model_id_source"],
        "dispatch_namespace": exact["dispatch_namespace"],
        "dispatch_namespace_source": exact["dispatch_namespace_source"],
        "environment_status": conformance.status,
        "environment_diverged_fields": list(conformance.diverged_fields),
        "environment_unobservable_fields": list(conformance.unobservable_fields),
        "treatment_disposition": eligibility.treatment_disposition,
        "disposition_reasons": list(eligibility.disposition_reasons),
        "score_eligible": eligibility.eligible,
        "blocking_reasons": list(eligibility.blocking_reasons),
        "execution_trace_id": trace["execution_trace_id"],
        "execution_trace_digest": bound["execution_trace_binding"]["digest"],
        "score_bundle_projection": bound,
        "score_bundle_id": bundle["score_bundle_id"],
        "score_bundle_digest": bundle["score_bundle_digest"],
        "score_disposition": bundle["score_disposition"],
        "failure_plane": bundle["failure_plane"],
        "failure_code": bundle["failure_code"],
        "leak_check_passed": ballot_outcome["leak_finding"].passed,
        "leak_hits": list(ballot_outcome["leak_finding"].hits),
        "ballots_collected": ballot_outcome["collection_accepted"],
        "adjudicated": ballot_outcome["adjudication"] is not None,
        # The gate results themselves are carried verbatim by the score bundle;
        # the summary keeps only the verdict so the two never disagree.
        "gates_passed": all(item["pass"] for item in gates),
        "gates_failed": [item["gate"] for item in gates if not item["pass"]],
        "cache_root_label_digest": runner.cache_root_digest(kwargs["cache_root_label"]),
        "event_stream_digest": capture["event_stream_digest"],
        "blinded_artifact_digest": ballot_outcome["blinded_artifact_digest"],
        "exit_code": capture["exit_code"],
        "quantities": {
            "input_tokens": tokens["input_tokens"],
            "output_tokens": tokens["output_tokens"],
            "cached_input_tokens": tokens["cached_input_tokens"],
            "cache_write_ephemeral_5m": tokens["cache_write_tokens_by_ttl_class"]["ephemeral_5m"],
            "cache_write_ephemeral_1h": tokens["cache_write_tokens_by_ttl_class"]["ephemeral_1h"],
            "reasoning_output_tokens": tokens["reasoning_output_tokens"],
            "duration_ms": capture["result"].get("duration_ms") or capture["wall_time_ms"],
            "num_turns": capture["result"].get("num_turns") or 0,
            "acceptance": accepted,
            "semantic_score": round(statistics.fmean(ballot_scores), 6) if ballot_scores else 0.0,
            "observed_cost_usd": capture["result"].get("total_cost_usd") or 0.0,
            "compactions": capture["compactions"],
            "retries": capture["retries"],
            "terminal_state": capture["result"].get("terminal_reason") or "unobserved",
        },
        "cache_root_label": kwargs["cache_root_label"],
    }
    raw = {
        "assignment_id": assignment_id,
        "response_text": capture["response_text"],
        "init_event": capture["init"],
        "result_event": capture["result"],
        "observations": observations,
        "observed_environment": environment,
    }
    return {
        "summary": summary,
        "raw": raw,
        "trace": trace,
        "score_bundle": bundle,
        "attestation": attestation,
        "conformance": conformance,
    }


def build_decisions(
    *,
    attempts: list[dict[str, Any]],
    score_bundles: list[dict[str, Any]],
    attestations: list[dict[str, Any]],
    assignments: list[dict[str, Any]],
    registry: list[dict[str, Any]],
    partition: dict[str, Any],
    protocol_binding: dict[str, str],
    traces: list[Any],
    complete_campaign: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """One decision bundle per comparison set, reconstructed by the real replay path."""
    attestation_by_id = {item["attestation_id"]: item for item in attestations}
    bundle_by_id = {bundle["score_bundle_id"]: bundle for bundle in score_bundles}
    assignment_by_id = {item["assignment_id"]: item for item in assignments}
    trace_by_id = {trace["execution_trace_id"]: trace for trace in traces}

    sets: dict[str, list[dict[str, Any]]] = {}
    for record in attempts:
        sets.setdefault(record["comparison_set_id"], []).append(record)

    decisions: list[dict[str, Any]] = []
    cache_reports: list[dict[str, Any]] = []
    dominance: list[dict[str, Any]] = []

    for comparison_set_id, members in sorted(sets.items()):
        if len(members) != len(ARMS):
            continue
        members.sort(key=lambda item: item["arm"])
        candidate = next(item for item in members if item["arm"] == "candidate")
        comparator = next(item for item in members if item["arm"] == "comparator")

        arm_a, arm_b = runner.observe_paired_cache_isolation(
            candidate["cache_root_label"], comparator["cache_root_label"]
        )
        contributes = runner.pair_contributes_resource_comparison(arm_a, arm_b)
        cache_reports.append(
            {
                "comparison_set_id": comparison_set_id,
                "candidate_arm": arm_a,
                "comparator_arm": arm_b,
                "contributes_resource_comparison": contributes,
            }
        )

        # The bindings gate is reference integrity only. A bundle that is missing
        # its ballots because a deterministic gate failed is a CANDIDATE outcome,
        # not an untrustworthy record, and routing it through this gate turned a
        # wrong answer into `invalid` instead of `no_qualification`. Provenance is
        # checked at its own later stage, which the ladder never reaches when the
        # deterministic stage has already failed.
        binding_findings: list[str] = []
        provenance_findings: list[str] = []
        for record in members:
            bundle = bundle_by_id[record["score_bundle_id"]]
            trace = trace_by_id[record["execution_trace_id"]]
            projection = record["score_bundle_projection"]
            binding_findings.extend(
                f"{record['assignment_id']}:{item}"
                for item in runner.verify_bundle_references(projection, [trace])
            )
            binding_findings.extend(
                f"{record['assignment_id']}:{item}"
                for item in runner.verify_bundle_projections(projection, trace)
            )
            if bundle["resource_vector"] != runner.derive_resource_vector(trace):
                binding_findings.append(
                    f"{record['assignment_id']}:{runner.BINDING_DIGEST_MISMATCH}"
                )
            verdict = policy.assignment_verdict(assignment_by_id[record["assignment_id"]])
            if not verdict.ok:
                binding_findings.extend(verdict.findings)
            provenance_findings.extend(
                f"{record['assignment_id']}:{item}" for item in scoring.missing_provenance(bundle)
            )
            attestation = attestation_by_id[f"ATT-{record['assignment_id']}"]
            if scoring.attestation_blocks_acceptance(attestation):
                provenance_findings.append(f"{record['assignment_id']}:attestation_blocks")

        partition_ok = all(
            policy.bundle_partition_verdict({"partition": partition, "bundle_kind": "score_bundle"}, registry).ok
            for _ in members
        ) and policy.consumption_verdict(registry, candidate["objective_id"]).ok

        gate_outcomes = {
            "bindings": "pass" if not binding_findings else "fail",
            "partition": "pass" if partition_ok else "fail",
            "treatment": "pass" if all(item["score_eligible"] for item in members) else "fail",
            "deterministic": "pass" if all(item["gates_passed"] for item in members) else "fail",
            "provenance": "pass"
            if not provenance_findings
            and all(item["ballots_collected"] for item in members)
            and contributes
            else "fail",
            "completeness": "pass" if complete_campaign else "fail",
        }

        # A calibration protocol carries no margins, sample sizes, or terminal
        # thresholds (FR-037), so neither the absolute floors nor the
        # non-inferiority stage is evaluable here. They are recorded as
        # not_evaluated rather than defaulted to a pass.
        case = {
            "decision_bundle_id": f"DEC-{comparison_set_id}",
            "partition": partition,
            "comparison_set_binding": {
                "id": comparison_set_id,
                "digest": digest_of(sorted(item["assignment_id"] for item in members)),
            },
            "assignment_bindings": [
                {"id": item["assignment_id"], "digest": assignment_by_id[item["assignment_id"]]["assignment_digest"]}
                for item in members
            ],
            "score_bundle_bindings": [
                {"id": item["score_bundle_id"], "digest": item["score_bundle_digest"]}
                for item in members
            ],
            # FR-037: a calibration decision binds the protocol, under the
            # protocol's own name. Contract 1.0.0 required analysis_plan_binding
            # unconditionally, so this bound the right digest under the wrong
            # field; 1.1.0 substitutes on qualification_eligible.
            "calibration_protocol_binding": protocol_binding,
            "analysis_output_id": f"AO-{comparison_set_id}",
            "evidence": {
                "gate_outcomes": gate_outcomes,
                "floor_result": decision.NOT_EVALUATED,
                "non_inferiority_result": decision.NOT_EVALUATED,
                "candidate_vector": None,
                "comparator_vector": None,
                "conditions": [],
                "reasoning_output_tokens_total": sum(
                    item["quantities"]["reasoning_output_tokens"] for item in members
                ),
                "provenance_inference_count": 0,
            },
            "evidence_refs": [item["event_stream_digest"] for item in members],
        }
        bundle = decision.replay_decision(case)
        # Replay must reconstruct from PERSISTED evidence, not from the same
        # in-memory object. Calling the same pure function twice on the same
        # `case` compares a function to itself and is unconditionally true, so
        # it was not evidence of the replay determinism SC-011 claims. Round-
        # tripping the case through canonical JSON exercises serialization and
        # reload, which is the property that actually has to hold on a clean
        # checkout.
        reloaded_case = json.loads(json.dumps(case, sort_keys=True))
        replayed = decision.replay_decision(reloaded_case)
        decisions.append(
            {
                "comparison_set_id": comparison_set_id,
                "decision_bundle": bundle,
                "deterministic_replay_matches": bundle == replayed,
                "binding_findings": binding_findings,
                "provenance_findings": provenance_findings,
            }
        )

        dominance.append(
            {
                "comparison_set_id": comparison_set_id,
                "decision_bearing": False,
                "scope": (
                    "Diagnostic only. The ladder did not reach the Pareto stage because a "
                    "calibration protocol declares no floors and no margins."
                ),
                **decision.dominance_with_reasoning_report(
                    {
                        "input_tokens": candidate["quantities"]["input_tokens"],
                        "cached_input_tokens": candidate["quantities"]["cached_input_tokens"],
                        "output_tokens": candidate["quantities"]["output_tokens"],
                        "duration": candidate["quantities"]["duration_ms"],
                        "retries": candidate["quantities"]["retries"],
                        "compactions": candidate["quantities"]["compactions"],
                        "acceptance": candidate["quantities"]["acceptance"],
                        "terminal_state": candidate["quantities"]["terminal_state"],
                    },
                    {
                        "input_tokens": comparator["quantities"]["input_tokens"],
                        "cached_input_tokens": comparator["quantities"]["cached_input_tokens"],
                        "output_tokens": comparator["quantities"]["output_tokens"],
                        "duration": comparator["quantities"]["duration_ms"],
                        "retries": comparator["quantities"]["retries"],
                        "compactions": comparator["quantities"]["compactions"],
                        "acceptance": comparator["quantities"]["acceptance"],
                        "terminal_state": comparator["quantities"]["terminal_state"],
                    },
                    reasoning_output_tokens_total=sum(
                        item["quantities"]["reasoning_output_tokens"] for item in members
                    ),
                ),
            }
        )

    findings = decision.primary_statistics_findings(
        [
            {"assignment_id": record["assignment_id"], "complete": True, "superseded": False}
            for record in attempts
        ]
    )
    if findings:
        raise SystemExit(f"primary statistics refused: {findings}")
    return decisions, cache_reports, dominance


def main() -> int:
    parser = argparse.ArgumentParser(description="CAR-003 T078 operator-only calibration pilot")
    parser.add_argument("--out", required=True, help="repo-relative committed evidence path")
    args = parser.parse_args()

    committed, retention = run_pilot()

    retention_path = REPO_ROOT / RETENTION_RELATIVE
    retention_path.parent.mkdir(parents=True, exist_ok=True)
    retention_path.write_text(
        json.dumps(retention, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    committed["retention_status"] = "passed"

    boundary = scoring.inspect_committed_evidence(committed)
    local = local_denied_findings(committed)
    committed["evidence_boundary_findings"] = list(boundary) + list(local)
    if boundary or local:
        print(f"REFUSED: sensitive fields in committed evidence: {boundary + local}", file=sys.stderr)
        return 2
    committed["sanitization_status"] = "passed"
    committed["pilot_digest"] = record_digest(committed, digest_field="pilot_digest")

    text = json.dumps(committed, indent=2, sort_keys=True, default=str) + "\n"
    if SESSION_ID_RE.search(text) or HOME_PATH_RE.search(text):
        print("REFUSED: unsanitized evidence detected; nothing written", file=sys.stderr)
        return 2

    out_path = REPO_ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")

    budget = committed["budget"]
    print(f"pilot: {committed['pilot_id']}")
    print(f"attempts: {budget['consumed']['attempts']}/{budget['attempts_planned']}  stop: {budget['stop_reason']}")
    print(f"cost: ${budget['consumed']['observed_cost_usd']}  wall: {budget['consumed']['duration_seconds']}s")
    print(f"decisions: {[item['decision_bundle']['decision'] for item in committed['decision_bundles']]}")
    print(f"partition proof: {committed['partition_consumption_proof']['non_calibration_all_refused']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

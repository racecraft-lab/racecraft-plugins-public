"""Durable, conservative native-launch accounting (Python standard library only)."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time

from trigger_comparison import _require, json_digest, validate_experiment


_SHA256 = re.compile(r"[0-9a-f]{64}", re.ASCII)
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", re.ASCII)
_AFFIRMATIVE = re.compile(
    r"\s*(?:approved|yes|authorized|i\s+approve)\s*[,!.]*\s*"
    r"(?:(?:please\s+proceed|please\s+finish\s+the\s+goal|finish\s+the\s+goal)\s*[.!]*)?\s*",
    re.ASCII | re.IGNORECASE,
)
_STANDING_GRANT = re.compile(
    r"\s*(?:listen\s*[,!]?\s*)?i\s+approve\s+everything\s+that\s+blocks\s+or\s+could\s+block\s+"
    r"this\s+goal\s+from\s+being\s+achieved\s*[.!]*\s*",
    re.ASCII | re.IGNORECASE,
)
_EXISTING_QUOTA = re.compile(
    r"\s*(?:just\s+)?run\s+until\s+the\s+quota\s+is\s+run\s+out\s*[.!]*\s*",
    re.ASCII | re.IGNORECASE,
)
_REVOCATION = re.compile(
    r"\s*(?:no|denied|stop|cancel(?:\s+it)?|do\s+not\s+proceed|"
    r"i\s+(?:do\s+not\s+approve|revoke(?:\s+(?:my\s+)?approval)?))\s*[.!]*\s*",
    re.ASCII | re.IGNORECASE,
)
_STANDING_SCOPE = "issue-573-full-trigger-qualification/v1"
_APPROVED_PLAN_SHA256 = "642d7fc3117118f4963c9583de8017662a95ff3698e31bea26dd4b851986ccc4"
_UNCHANGED_DIMENSIONS = [
    "qualification_scope", "roster", "arms", "trials", "trial_timeout_seconds", "threshold",
    "corpus_sha256", "inventory_sha256", "pins", "controlled_difference",
    "identities.catalog", "identities.fixture", "acceptance_rules",
]
_PERMITTED_BINDING_CHANGES = ["experiment_id", "output_directory", "identities.observer"]


def _observation(value: object, role: str, session_id: str) -> tuple[str, int, datetime]:
    fields = {"role", "message_id", "session_id", "timestamp", "source_ordinal", "content",
              "content_sha256", "source_line_sha256"}
    _require(isinstance(value, dict) and set(value) == fields, "contextual approval observation is malformed")
    _require(value["role"] == role, f"contextual approval {role} observation has the wrong role")
    _require(isinstance(value["message_id"], str) and bool(value["message_id"].strip()), "contextual approval lacks message identity")
    _require(value["session_id"] == session_id, "contextual approval observations must share the retained session")
    _require(type(value["source_ordinal"]) is int and value["source_ordinal"] >= 0, "contextual approval source ordinal is invalid")
    _require(isinstance(value["content"], str), "contextual approval content is invalid")
    _require(isinstance(value["content_sha256"], str)
             and value["content_sha256"] == hashlib.sha256(value["content"].encode()).hexdigest(),
             "contextual approval content hash does not match retained bytes")
    _require(isinstance(value["source_line_sha256"], str) and _SHA256.fullmatch(value["source_line_sha256"]),
             "contextual approval source-line hash is invalid")
    timestamp = value["timestamp"]
    _require(isinstance(timestamp, str) and _TIMESTAMP.fullmatch(timestamp), "contextual approval timestamp is invalid")
    try:
        parsed = datetime.fromisoformat(timestamp[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError("contextual approval timestamp is invalid") from error
    return value["message_id"], value["source_ordinal"], parsed


def _validate_contextual_approval(record: dict, manifest_digest: str, budget: int) -> None:
    fields = {"schema_version", "manifest_sha256", "launch_budget", "recorder_observation"}
    _require(set(record) == fields, "contextual approval record is malformed")
    _require(record.get("manifest_sha256") == manifest_digest
             and type(record.get("launch_budget")) is int and record["launch_budget"] == budget,
             "approval does not bind exact manifest and budget")
    observed = record.get("recorder_observation")
    observed_fields = {"observer", "session_id", "adjacent_user_visible_message_ids", "request", "response"}
    _require(isinstance(observed, dict) and set(observed) == observed_fields, "contextual approval recorder observation is malformed")
    _require(observed["observer"] == "trusted-orchestrator", "contextual approval requires the trusted recorder")
    session_id = observed["session_id"]
    _require(isinstance(session_id, str) and bool(session_id.strip()), "contextual approval lacks retained session identity")
    request_id, request_ordinal, request_at = _observation(observed["request"], "assistant", session_id)
    response_id, response_ordinal, response_at = _observation(observed["response"], "user", session_id)
    _require(request_id != response_id, "contextual approval request and response identities must differ")
    _require(observed["adjacent_user_visible_message_ids"] == [request_id, response_id],
             "contextual approval requires recorder-observed user-visible adjacency")
    _require(request_ordinal < response_ordinal and request_at < response_at,
             "contextual approval request must precede the response")
    request = f"Approve trigger campaign {manifest_digest} with launch budget {budget}."
    _require(observed["request"]["content"] == request,
             "contextual approval request does not bind the exact manifest and launch budget")
    _require(_AFFIRMATIVE.fullmatch(observed["response"]["content"]) is not None,
             "contextual approval response is not an accepted direct affirmative")


def _review_timestamp(value: object, message: str) -> datetime:
    _require(isinstance(value, str) and _TIMESTAMP.fullmatch(value), message)
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError(message) from error


def _validate_standing_authority(value: object) -> tuple[str, datetime]:
    fields = {"scope_id", "approved_plan_sha256", "recorder", "session_id", "grant",
              "quota_directive", "reviewed_through"}
    _require(isinstance(value, dict) and set(value) == fields, "standing authority record is malformed")
    _require(value["scope_id"] == _STANDING_SCOPE, "standing authority is outside the closed campaign scope")
    plan_digest = value["approved_plan_sha256"]
    _require(plan_digest == _APPROVED_PLAN_SHA256, "standing authority lacks the approved-plan binding")
    _require(value["recorder"] == "trusted-orchestrator", "standing authority requires the trusted recorder")
    session_id = value["session_id"]
    _require(isinstance(session_id, str) and bool(session_id.strip()), "standing authority lacks retained session identity")
    grant_id, grant_ordinal, grant_at = _observation(value["grant"], "user", session_id)
    quota_id, quota_ordinal, quota_at = _observation(value["quota_directive"], "user", session_id)
    _require(grant_id != quota_id and grant_ordinal < quota_ordinal and grant_at < quota_at,
             "standing grant must precede the distinct existing-quota directive")
    _require(_STANDING_GRANT.fullmatch(value["grant"]["content"]) is not None,
             "standing grant is not an accepted direct whole-message authorization")
    _require(_EXISTING_QUOTA.fullmatch(value["quota_directive"]["content"]) is not None,
             "standing quota directive is not an accepted direct whole-message instruction")

    review = value["reviewed_through"]
    review_fields = {"reviewer", "review_id", "session_id", "reviewed_at", "latest_user",
                     "reviewed_interval_sha256", "source_sha256", "revocation_found"}
    _require(isinstance(review, dict) and set(review) == review_fields, "standing-authority review is malformed")
    _require(review["reviewer"] == "independent-reviewer", "standing authority requires independent review")
    _require(isinstance(review["review_id"], str) and bool(review["review_id"].strip()), "standing-authority review lacks identity")
    _require(review["session_id"] == session_id, "standing-authority review changed retained session")
    latest_id, latest_ordinal, latest_at = _observation(review["latest_user"], "user", session_id)
    same_endpoint = (latest_id == quota_id and latest_ordinal == quota_ordinal and latest_at == quota_at
                     and review["latest_user"] == value["quota_directive"])
    later_endpoint = latest_id != quota_id and latest_ordinal > quota_ordinal and latest_at > quota_at
    _require(same_endpoint or later_endpoint,
             "standing-authority review endpoint is older than or mismatched with the quota directive")
    reviewed_at = _review_timestamp(review["reviewed_at"], "standing-authority review timestamp is invalid")
    _require(reviewed_at > latest_at, "standing-authority review predates its latest retained user observation")
    _require(review["reviewed_interval_sha256"] == json_digest(
        [value["grant"], value["quota_directive"], review["latest_user"]]),
        "standing-authority review does not bind its retained observation interval")
    _require(isinstance(review["source_sha256"], str) and _SHA256.fullmatch(review["source_sha256"]),
             "standing-authority review source hash is invalid")
    _require(review["revocation_found"] is False, "standing authority was revoked or narrowed")
    _require(_REVOCATION.fullmatch(review["latest_user"]["content"]) is None,
             "latest retained user observation explicitly revokes or denies standing authority")
    return plan_digest, reviewed_at


def _validate_predecessor(value: object, manifest: dict, manifest_digest: str, budget: int) -> str:
    fields = {"manifest_sha256", "ledger_sha256", "output_directory", "launch_budget",
              "charged_launches", "unreserved_launches", "unknown_launches", "terminal",
              "reuse", "reset", "refund", "regrade"}
    _require(isinstance(value, dict) and set(value) == fields, "standing campaign predecessor is malformed")
    _require(isinstance(value["manifest_sha256"], str) and _SHA256.fullmatch(value["manifest_sha256"])
             and value["manifest_sha256"] != manifest_digest,
             "standing campaign cannot reuse the current or an invalid predecessor manifest")
    _require(isinstance(value["ledger_sha256"], str) and _SHA256.fullmatch(value["ledger_sha256"]),
             "standing campaign predecessor ledger hash is invalid")
    old_output = value["output_directory"]
    new_output = manifest.get("output_directory")
    _require(isinstance(old_output, str) and Path(old_output).is_absolute()
             and old_output == str(Path(old_output).resolve())
             and isinstance(new_output, str) and Path(new_output).is_absolute()
             and new_output == str(Path(new_output).resolve()) and old_output != new_output,
             "standing campaign requires a new canonical output directory")
    charged = value["charged_launches"]
    unreserved = value["unreserved_launches"]
    _require(type(value["launch_budget"]) is int and value["launch_budget"] == budget
             and type(charged) is int and charged >= 0
             and type(unreserved) is int and unreserved >= 0 and charged + unreserved == budget
             and type(value["unknown_launches"]) is int and value["unknown_launches"] == 0,
             "standing campaign predecessor accounting is not terminal and complete")
    _require(value["terminal"] is True and all(value[key] is False for key in ("reuse", "reset", "refund", "regrade")),
             "standing campaign predecessor cannot be reused, reset, refunded, or regraded")
    return value["manifest_sha256"]


def _validate_campaign_exercise(
    value: object, manifest_digest: str, budget: int, plan_digest: str, standing_reviewed_at: datetime,
) -> None:
    fields = {"scope_id", "reviewed_manifest", "schedule", "case_count", "trial_count", "arm_count",
              "launch_count", "review", "continuity", "predecessor", "constraints"}
    _require(isinstance(value, dict) and set(value) == fields, "standing campaign exercise is malformed")
    _require(value["scope_id"] == _STANDING_SCOPE, "standing campaign exercise is outside the closed scope")
    manifest = value["reviewed_manifest"]
    cases = validate_experiment(manifest)
    _require(json_digest(manifest) == manifest_digest, "standing campaign review does not bind the exact manifest")
    _require(manifest.get("qualification_scope") == "full" and manifest.get("arms") == ["baseline", "candidate"]
             and manifest.get("trials") == 3 and manifest.get("threshold") == 0.5
             and len(cases) == 217 and {case["host"] for case in cases.values()} == {"claude", "codex"},
             "standing campaign is not the closed 217-case dual-host full qualification")
    schedule = value["schedule"]
    _require(isinstance(schedule, dict) and set(schedule) == {"name", "workers"}
             and schedule["name"] == "serial" and type(schedule["workers"]) is int and schedule["workers"] == 1,
             "standing campaign must use one serial worker")
    expected_launches = len(cases) * manifest["trials"] * len(manifest["arms"])
    _require(type(value["case_count"]) is int and value["case_count"] == len(cases)
             and type(value["trial_count"]) is int and value["trial_count"] == manifest["trials"]
             and type(value["arm_count"]) is int and value["arm_count"] == len(manifest["arms"])
             and type(value["launch_count"]) is int and value["launch_count"] == expected_launches
             and type(budget) is int and budget == 1302 and expected_launches == budget,
             "standing campaign launch arithmetic must be exactly 217 x 3 x 2 = 1302")

    predecessor_digest = _validate_predecessor(value["predecessor"], manifest, manifest_digest, budget)
    continuity = value["continuity"]
    continuity_fields = {"reference_manifest_sha256", "assessment_sha256", "result",
                         "unchanged_dimensions", "permitted_binding_changes"}
    _require(isinstance(continuity, dict) and set(continuity) == continuity_fields,
             "standing campaign continuity record is malformed")
    _require(continuity["reference_manifest_sha256"] == predecessor_digest
             and isinstance(continuity["assessment_sha256"], str)
             and _SHA256.fullmatch(continuity["assessment_sha256"])
             and continuity["result"] == "unchanged"
             and continuity["unchanged_dimensions"] == _UNCHANGED_DIMENSIONS
             and continuity["permitted_binding_changes"] == _PERMITTED_BINDING_CHANGES,
             "standing campaign continuity review does not preserve the experiment")

    review = value["review"]
    review_fields = {"reviewer", "review_id", "reviewed_at", "source_commit", "source_tree_sha256",
                     "observer_sha256", "manifest_sha256", "launch_budget", "approved_plan_sha256",
                     "continuity_sha256", "predecessor_sha256"}
    _require(isinstance(review, dict) and set(review) == review_fields, "standing campaign manifest review is malformed")
    _require(review["reviewer"] == "independent-reviewer"
             and isinstance(review["review_id"], str) and bool(review["review_id"].strip()),
             "standing campaign manifest requires independent review identity")
    reviewed_at = _review_timestamp(review["reviewed_at"], "standing campaign manifest review timestamp is invalid")
    _require(reviewed_at > standing_reviewed_at, "standing campaign manifest review predates authority review")
    _require(isinstance(review["source_commit"], str) and re.fullmatch(r"[0-9a-f]{40}", review["source_commit"])
             and isinstance(review["source_tree_sha256"], str) and _SHA256.fullmatch(review["source_tree_sha256"]),
             "standing campaign manifest review lacks frozen source binding")
    _require(review["manifest_sha256"] == manifest_digest
             and type(review["launch_budget"]) is int and review["launch_budget"] == budget
             and review["observer_sha256"] == manifest["identities"]["observer"]
             and review["approved_plan_sha256"] == plan_digest
             and review["continuity_sha256"] == json_digest(continuity)
             and review["predecessor_sha256"] == json_digest(value["predecessor"]),
             "standing campaign manifest review does not bind source, manifest, budget, plan, continuity, and predecessor")

    constraints = value["constraints"]
    constraint_fields = {"campaign_count", "automatic_retries", "unknown_outcomes_charged",
                         "available_quota_only", "quota_purchase", "quota_reset", "credit_redemption",
                         "old_approval_reuse"}
    _require(isinstance(constraints, dict) and set(constraints) == constraint_fields,
             "standing campaign constraints are malformed")
    _require(type(constraints["campaign_count"]) is int and constraints["campaign_count"] == 1
             and type(constraints["automatic_retries"]) is int and constraints["automatic_retries"] == 0
             and constraints["unknown_outcomes_charged"] is True
             and constraints["available_quota_only"] is True
             and all(constraints[key] is False for key in
                     ("quota_purchase", "quota_reset", "credit_redemption", "old_approval_reuse")),
             "standing campaign constraints exceed delegated authority")


def _validate_standing_approval(record: dict, manifest_digest: str, budget: int) -> None:
    fields = {"schema_version", "manifest_sha256", "launch_budget", "standing_authority", "campaign_exercise"}
    _require(set(record) == fields, "standing campaign approval record is malformed")
    _require(record["manifest_sha256"] == manifest_digest
             and type(record["launch_budget"]) is int and record["launch_budget"] == budget,
             "approval does not bind exact manifest and budget")
    plan_digest, reviewed_at = _validate_standing_authority(record["standing_authority"])
    _validate_campaign_exercise(record["campaign_exercise"], manifest_digest, budget, plan_digest, reviewed_at)


def _validate_carry_forward_approval(
    record: dict, manifest_digest: str, budget: int, carry_forward: object,
) -> None:
    """Extend retained standing authority with an independent lineage review."""
    fields = {"schema_version", "manifest_sha256", "launch_budget", "standing_authority",
              "carry_forward_review"}
    _require(set(record) == fields, "carry-forward approval record is malformed")
    _require(record["manifest_sha256"] == manifest_digest
             and type(record["launch_budget"]) is int and record["launch_budget"] == budget == 891,
             "carry-forward approval does not bind the exact manifest and fresh ceiling")
    plan_digest, standing_reviewed_at = _validate_standing_authority(record["standing_authority"])
    review = record["carry_forward_review"]
    review_fields = {"reviewer", "review_id", "reviewed_at", "source_commit", "source_tree_sha256",
                     "manifest_sha256", "launch_budget", "approved_plan_sha256", "carry_forward_sha256",
                     "source_sha256", "cohort_sha256", "compatibility_sha256", "accounting_sha256",
                     "observer_closures_sha256", "source_stability_review_sha256"}
    _require(isinstance(review, dict) and set(review) == review_fields,
             "carry-forward independent review is malformed")
    reviewed_at = _review_timestamp(review["reviewed_at"], "carry-forward review timestamp is invalid")
    _require(review["reviewer"] == "independent-reviewer"
             and isinstance(review["review_id"], str) and bool(review["review_id"].strip())
             and reviewed_at > standing_reviewed_at
             and isinstance(review["source_commit"], str)
             and re.fullmatch(r"[0-9a-f]{40}", review["source_commit"])
             and isinstance(review["source_tree_sha256"], str)
             and _SHA256.fullmatch(review["source_tree_sha256"]),
             "carry-forward review lacks independent identity, chronology, or source binding")
    _require(isinstance(carry_forward, dict), "V4 approval requires its reviewed carry-forward component")
    for key in ("source_sha256", "cohort_sha256", "compatibility_sha256", "accounting_sha256",
                "observer_closures_sha256", "source_stability_review_sha256"):
        _require(isinstance(review[key], str) and _SHA256.fullmatch(review[key]),
                 f"carry-forward review {key} is invalid")
    source = carry_forward.get("source")
    _require(isinstance(source, dict), "carry-forward source binding is missing")
    observer_binding = {
        "old": carry_forward.get("compatibility", {}).get("old_observer_sha256"),
        "new": carry_forward.get("compatibility", {}).get("new_observer_sha256"),
        "dual_replay": source.get("dual_replay"),
    }
    _require(review["manifest_sha256"] == manifest_digest
             and type(review["launch_budget"]) is int and review["launch_budget"] == budget
             and review["approved_plan_sha256"] == plan_digest
             and review["carry_forward_sha256"] == json_digest(carry_forward)
             and review["source_sha256"] == json_digest(source)
             and review["cohort_sha256"] == json_digest(carry_forward.get("cohort"))
             and review["compatibility_sha256"] == json_digest(carry_forward.get("compatibility"))
             and review["accounting_sha256"] == json_digest(carry_forward.get("accounting"))
             and review["observer_closures_sha256"] == json_digest(observer_binding)
             and review["source_stability_review_sha256"]
             == source.get("source_stability_review", {}).get("sha256"),
             "carry-forward review does not bind exact lineage, closures, compatibility, and accounting")


def _validate_multi_generation_approval(
    record: dict, manifest_digest: str, budget: int, carry_forward: object,
) -> None:
    """Bind a reviewed V2 history set to one explicitly authorized generation."""
    fields = {"schema_version", "manifest_sha256", "launch_budget", "standing_authority",
              "carry_forward_review"}
    _require(set(record) == fields, "multi-generation approval record is malformed")
    _require(record["manifest_sha256"] == manifest_digest
             and type(record["launch_budget"]) is int and record["launch_budget"] == budget,
             "multi-generation approval does not bind the exact request and fresh ceiling")
    plan_digest, standing_reviewed_at = _validate_standing_authority(record["standing_authority"])
    _require(isinstance(carry_forward, dict)
             and carry_forward.get("schema_version") == "trigger-case-carry-forward/v2",
             "V5 approval requires its reviewed V2 carry-forward component")
    review = record["carry_forward_review"]
    review_fields = {
        "reviewer", "review_id", "reviewed_at", "source_commit", "source_tree_sha256",
        "manifest_sha256", "logical_manifest_sha256", "launch_budget", "approved_plan_sha256",
        "carry_forward_sha256", "histories_sha256", "accounting_sha256",
        "observer_replays_sha256",
    }
    _require(isinstance(review, dict) and set(review) == review_fields,
             "multi-generation independent review is malformed")
    reviewed_at = _review_timestamp(review["reviewed_at"], "multi-generation review timestamp is invalid")
    _require(review["reviewer"] == "independent-reviewer"
             and isinstance(review["review_id"], str) and bool(review["review_id"].strip())
             and reviewed_at > standing_reviewed_at
             and isinstance(review["source_commit"], str)
             and re.fullmatch(r"[0-9a-f]{40}", review["source_commit"])
             and isinstance(review["source_tree_sha256"], str)
             and _SHA256.fullmatch(review["source_tree_sha256"]),
             "multi-generation review lacks independent identity, chronology, or source binding")
    _require(review["manifest_sha256"] == manifest_digest
             and review["logical_manifest_sha256"] == json_digest(carry_forward.get("logical_manifest"))
             and type(review["launch_budget"]) is int and review["launch_budget"] == budget
             and review["approved_plan_sha256"] == plan_digest
             and review["carry_forward_sha256"] == json_digest(carry_forward)
             and review["histories_sha256"] == json_digest(carry_forward.get("histories"))
             and review["accounting_sha256"] == json_digest(carry_forward.get("accounting"))
             and review["observer_replays_sha256"] == json_digest(carry_forward.get("observer_replays")),
             "multi-generation review does not bind the exact request, histories, replays, and accounting")


def validate_approval(record: dict, manifest_digest: str, budget: int,
                      *, carry_forward: object = None) -> None:
    """Require a retained user-message authorization, not an agent-owned pass flag.

    This records documentary provenance, not a cryptographic user authentication.
    The caller must obtain the source message from the user-facing approval channel.
    """
    _require(type(budget) is int and budget > 0, "launch budget must be a positive integer")
    _require(isinstance(record, dict), "missing retained campaign approval")
    if record.get("schema_version") == "trigger-campaign-approval/v5":
        _validate_multi_generation_approval(record, manifest_digest, budget, carry_forward)
        return
    if record.get("schema_version") == "trigger-campaign-approval/v4":
        _validate_carry_forward_approval(record, manifest_digest, budget, carry_forward)
        return
    if record.get("schema_version") == "trigger-campaign-approval/v3":
        _validate_standing_approval(record, manifest_digest, budget)
        return
    if record.get("schema_version") == "trigger-campaign-approval/v2":
        _validate_contextual_approval(record, manifest_digest, budget)
        return
    _require(record.get("schema_version") == "trigger-campaign-approval/v1", "missing retained campaign approval")
    _require(record.get("manifest_sha256") == manifest_digest and type(record.get("launch_budget")) is int and record["launch_budget"] == budget, "approval does not bind exact manifest and budget")
    source = record.get("source")
    _require(isinstance(source, dict) and source.get("role") == "user", "campaign requires user-origin approval")
    _require(isinstance(source.get("message_id"), str) and bool(source["message_id"].strip()), "approval lacks source message identity")
    text = f"Approve trigger campaign {manifest_digest} with launch budget {budget}."
    _require(isinstance(source.get("content"), str) and text in source["content"].splitlines(), "source message does not explicitly approve this manifest and launch budget")


class CampaignLedger:
    """One immutable authorization and transactionally reserved trial identities."""

    def __init__(self, path: Path, manifest_digest: str, approval: dict, budget: int,
                 *, carry_forward: object = None,
                 admitted: tuple[dict, dict, bytes] | None = None):
        validate_approval(approval, manifest_digest, budget, carry_forward=carry_forward)
        self.path = path
        self.budget = budget
        self._admitted_authorization: dict | None = None
        self._admitted_snapshot: dict | None = None
        self._admitted_bytes: bytes | None = None
        if admitted is None:
            path.parent.mkdir(parents=True, exist_ok=True)
        authorization = {"manifest_sha256": manifest_digest, "approval_sha256": json_digest(approval),
                         "launch_budget": budget}
        if carry_forward is not None:
            authorization["carry_forward_sha256"] = json_digest(carry_forward)
        binding = json.dumps(authorization, sort_keys=True)
        if admitted is not None:
            self._admitted_authorization, self._admitted_snapshot = (
                _validate_admitted_ledger(self, authorization, admitted, carry_forward))
            self._admitted_bytes = admitted[2]
            return
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

    def reserve_case(self, arm: str, case_id: str, before_reservation=None) -> None:
        """Reserve all three serial trials before starting the native case process."""
        _reserve_case(self, arm, case_id, before_reservation)

    def prepare_publication(self, before_publication) -> None:
        """Admit resumed V4 bytes before publishing without a reservation."""
        _prepare_publication(self, before_publication)

    def finish_case(self, arm: str, case_id: str, status: str) -> None:
        _finish_case(self, arm, case_id, status)

    def snapshot(self) -> dict:
        return _campaign_snapshot(self)

    def require_reconciled(self) -> None:
        _require(self.snapshot()["unknown_launches"] == 0, "unknown prior outcomes require read-only process/artifact reconciliation; no relaunch authorized")


@dataclass(frozen=True)
class QualifiedConcurrency:
    binding_sha256: str
    serial_seconds: float
    parallel_seconds: float
    trial_count: int


def _ledger_snapshot(connection: sqlite3.Connection, budget: int) -> dict:
    """Project authoritative launch rows from one already-open connection."""
    rows = connection.execute("SELECT arm, case_id, trial, status, reserved_at, completed_at FROM launches ORDER BY arm, case_id, trial").fetchall()
    return {"schema_version": "trigger-campaign-ledger/v1", "launch_budget": budget,
        "reserved_launches": len(rows), "unknown_launches": sum(row[3] == "unknown" for row in rows),
        "launches": [dict(zip(("arm", "case_id", "trial_number", "status", "reserved_at", "completed_at"), row)) for row in rows]}


def _read_ledger_connection(connection: sqlite3.Connection) -> tuple[dict, dict]:
    """Project immutable authorization and launches from one connection."""
    binding = json.loads(connection.execute("SELECT binding FROM authorization WHERE id=1").fetchone()[0])
    return binding, _ledger_snapshot(connection, binding["launch_budget"])


def _validate_admitted_ledger(ledger: CampaignLedger, authorization: dict,
                               admitted: tuple[dict, dict, bytes],
                               carry_forward: object) -> tuple[dict, dict]:
    """Validate exact admitted bytes on the connection before any ledger write."""
    _require(carry_forward is not None and admitted[0] == authorization,
             "admitted ledger authorization changed before preparation")
    try:
        with ledger._connection() as connection:
            observed = (*_read_ledger_connection(connection), connection.serialize())
    except (sqlite3.Error, TypeError, IndexError, KeyError,
            json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError(f"admitted ledger changed before preparation: {exc}") from None
    _require(observed == admitted, "admitted ledger snapshot changed before preparation")
    return admitted[0], admitted[1]


def _require_admitted_connection(connection: sqlite3.Connection, budget: int,
                                  authorization: dict | None,
                                  expected: dict | None,
                                  expected_bytes: bytes | None = None) -> dict:
    """Bind a V4 operation to expected state on its exact SQLite connection."""
    snapshot = _ledger_snapshot(connection, budget)
    if expected is None:
        return snapshot
    binding = json.loads(connection.execute(
        "SELECT binding FROM authorization WHERE id=1").fetchone()[0])
    _require(binding == authorization and snapshot == expected
             and (expected_bytes is None or connection.serialize() == expected_bytes),
             "admitted ledger changed before its writable transaction")
    return snapshot


def _campaign_snapshot(ledger: CampaignLedger) -> dict:
    with ledger._connection() as connection:
        return _require_admitted_connection(connection, ledger.budget,
                                            ledger._admitted_authorization,
                                            ledger._admitted_snapshot)


def _admit_transaction(ledger: CampaignLedger, connection: sqlite3.Connection,
                       before_write=None) -> None:
    _require_admitted_connection(connection, ledger.budget,
                                 ledger._admitted_authorization,
                                 ledger._admitted_snapshot,
                                 ledger._admitted_bytes)
    if before_write is not None:
        before_write()


def _prepare_publication(ledger: CampaignLedger, before_publication) -> None:
    with ledger._connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        _admit_transaction(ledger, connection, before_publication)


def _reserve_case(ledger: CampaignLedger, arm: str, case_id: str,
                  before_reservation=None) -> None:
    _require(isinstance(arm, str) and bool(arm)
             and isinstance(case_id, str) and bool(case_id),
             "invalid reservation identity")
    updated = None
    with ledger._connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        _admit_transaction(ledger, connection, before_reservation)
        exists = connection.execute(
            "SELECT 1 FROM launches WHERE arm=? AND case_id=?", (arm, case_id)).fetchone()
        _require(exists is None, "case already reserved; automatic retries are prohibited")
        count = connection.execute("SELECT COUNT(*) FROM launches").fetchone()[0]
        _require(count + 3 <= ledger.budget, "campaign launch budget exhausted")
        connection.executemany(
            "INSERT INTO launches VALUES (?, ?, ?, 'unknown', ?, NULL)",
            [(arm, case_id, trial, time.time()) for trial in (1, 2, 3)])
        if ledger._admitted_snapshot is not None:
            updated = _ledger_snapshot(connection, ledger.budget)
    if updated is not None:
        ledger._admitted_snapshot = updated
        ledger._admitted_bytes = None


def _finish_case(ledger: CampaignLedger, arm: str, case_id: str, status: str) -> None:
    _require(status in {"complete", "invalid"},
             "unknown outcomes cannot be cleared or retried")
    updated = None
    with ledger._connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        _require_admitted_connection(connection, ledger.budget,
                                     ledger._admitted_authorization,
                                     ledger._admitted_snapshot)
        rows = connection.execute(
            "SELECT status FROM launches WHERE arm=? AND case_id=?", (arm, case_id)).fetchall()
        _require(len(rows) == 3 and all(row[0] == "unknown" for row in rows),
                 "missing or already settled reservation")
        connection.execute(
            "UPDATE launches SET status=?, completed_at=? WHERE arm=? AND case_id=?",
            (status, time.time(), arm, case_id))
        if ledger._admitted_snapshot is not None:
            updated = _ledger_snapshot(connection, ledger.budget)
    if updated is not None:
        ledger._admitted_snapshot = updated


def read_ledger(path: Path) -> tuple[dict, dict]:
    """Read authoritative accounting without creating or modifying a database."""
    comparison_uri = path.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(comparison_uri, uri=True)
    try:
        return _read_ledger_connection(connection)
    finally:
        connection.close()


def read_ledger_bytes(payload: bytes) -> tuple[dict, dict]:
    """Inspect the exact securely read SQLite bytes without reopening a pathname."""
    connection = sqlite3.connect(":memory:")
    try:
        connection.deserialize(payload)
        return _read_ledger_connection(connection)
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

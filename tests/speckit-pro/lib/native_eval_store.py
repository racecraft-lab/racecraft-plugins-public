"""A locked directory of immutable native trial receipts, not a scheduler.

History and raw evidence are checked once when the directory is opened. New
receipts update an in-memory index; reserving N trials does not reread O(N²)
history. A process-wide directory lock and a thread mutex prevent duplicate
reservations. Subject workspaces must never include this directory.
"""
from __future__ import annotations

import copy
from contextlib import AbstractContextManager
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import threading
import time
import uuid

from native_eval_catalog import _unique_object
from trigger_evidence import write_json_once


class StoreError(ValueError):
    """Stored evidence or an attempted transition cannot be trusted."""


_PAIR_ARM_FIELDS = (
    "case_id", "host", "mode", "trial", "input_fingerprint", "capture_sha256",
    "grade_identity", "grade_sha256",
)


def digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise StoreError(message)


def _sha(value: object) -> None:
    _require(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None, "invalid sha256 identity")


def _trial_key(row: dict, fingerprint: str) -> str:
    _sha(fingerprint)
    _require(isinstance(row, dict) and set(row) == {"case_id", "host", "mode", "trial"}, "invalid trial row")
    _require(row["host"] in {"claude", "codex"}, "invalid trial host")
    _require(all(isinstance(row[key], str) and row[key] for key in ("case_id", "mode")), "invalid trial identity")
    _require(type(row["trial"]) is int and row["trial"] > 0, "invalid trial number")
    return digest({"row": row, "input": fingerprint})


def _pair_arm_identities(arms: object) -> list[dict[str, object]]:
    _require(isinstance(arms, (list, tuple)) and len(arms) == 2,
             "pair requires exactly two arms")
    identities = []
    for arm in arms:
        _require(isinstance(arm, dict) and set(_PAIR_ARM_FIELDS) <= set(arm),
                 "pair arm is missing evidence identities")
        identity = {key: copy.deepcopy(arm[key]) for key in _PAIR_ARM_FIELDS}
        _require(all(isinstance(identity[key], str) and identity[key]
                     for key in ("case_id", "host", "mode")), "pair arm identity is malformed")
        _require(type(identity["trial"]) is int and identity["trial"] > 0,
                 "pair arm trial is malformed")
        for key in ("input_fingerprint", "capture_sha256", "grade_identity", "grade_sha256"):
            _sha(identity[key])
        identities.append(identity)
    _require(tuple(arm["host"] for arm in identities) == ("claude", "codex"),
             "pair arms must be ordered claude then codex")
    _require(identities[0]["case_id"] == identities[1]["case_id"]
             and identities[0]["trial"] == identities[1]["trial"],
             "pair arms must have the same case and trial")
    return identities


def _validate_pair_verdict(verdict: object) -> None:
    _require(isinstance(verdict, dict) and verdict.get("status") in {"pass", "fail", "invalid"}
             and isinstance(verdict.get("checks"), list), "invalid terminal pair grade")


def _fsync_directory(path: Path) -> None:
    """Durably sync directory entries on POSIX; Windows has no equivalent here.

    Windows still syncs each receipt file and publishes it through one hard-link
    operation, covering process interruption/resume. Power-loss durability of
    the directory entry is intentionally not claimed there.
    """
    if sys.platform == "win32":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _publish(path: Path, payload: dict) -> None:
    """Reuse exclusive evidence writing with immutable hard-link publication.

    POSIX additionally syncs the containing directory. Windows retains
    process-interruption/resume persistence through synced file data and the
    successful link operation, without a power-loss directory-sync claim.
    """
    temporary = path.with_name(f".pending-{uuid.uuid4().hex}")
    try:
        write_json_once(temporary, {"payload": payload, "sha256": digest(payload)})
        with temporary.open("rb") as stream:
            os.fsync(stream.fileno())
        _fsync_directory(path.parent)
        os.link(temporary, path)
        _fsync_directory(path.parent)
    except FileExistsError as exc:
        raise StoreError(f"immutable receipt already exists: {path.name}") from exc
    except OSError as exc:
        raise StoreError(f"cannot publish immutable receipt: {exc}") from exc
    finally:
        temporary.unlink(missing_ok=True)


def _lock_owner(stream) -> None:
    if sys.platform == "win32":
        try:
            import msvcrt
        except ImportError as exc:
            raise StoreError("Windows lock primitive is unavailable") from exc
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"\0")
            stream.flush()
            os.fsync(stream.fileno())
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        return
    if os.name == "posix":
        try:
            import fcntl
        except ImportError as exc:
            raise StoreError("POSIX lock primitive is unavailable") from exc
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return
    raise StoreError("no supported cross-process lock primitive")


def _unlock_owner(stream) -> None:
    if sys.platform == "win32":
        import msvcrt
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
    elif os.name == "posix":
        import fcntl
        fcntl.flock(stream, fcntl.LOCK_UN)


def _read(path: Path) -> dict:
    _require(path.is_file() and not path.is_symlink(), "receipt is not a regular file")
    try:
        envelope = json.loads(path.read_text(), object_pairs_hook=_unique_object)
        _require(isinstance(envelope, dict) and set(envelope) == {"payload", "sha256"}, "malformed receipt")
        value = envelope["payload"]
        _require(isinstance(value, dict) and digest(value) == envelope["sha256"], "receipt digest mismatch")
        return value
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise StoreError(f"cannot verify receipt {path.name}: {exc}") from exc


def _file_ref(attempt: Path, path: Path) -> dict:
    path = Path(path)
    _require(path.is_file() and not path.is_symlink(), "raw evidence must be a regular file")
    resolved = path.resolve(strict=True)
    _require(resolved.is_relative_to(attempt) and resolved != attempt, "raw evidence escaped attempt")
    _require(path.absolute() == resolved, "raw evidence path contains symlink or noncanonical components")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = -1
            before = os.fstat(stream.fileno())
            _require(stat.S_ISREG(before.st_mode), "raw evidence must be a regular file")
            value = hashlib.file_digest(stream, "sha256").hexdigest()
            os.fsync(stream.fileno())
            after = os.fstat(stream.fileno())
        stable_fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        _require(all(getattr(before, key) == getattr(after, key) for key in stable_fields),
                 "raw evidence changed while being captured")
        current = os.stat(path, follow_symlinks=False)
        _require(stat.S_ISREG(current.st_mode)
                 and (current.st_dev, current.st_ino) == (after.st_dev, after.st_ino)
                 and path.resolve(strict=True) == resolved,
                 "raw evidence identity changed while being captured")
        return {"path": str(resolved.relative_to(attempt)), "sha256": value, "bytes": after.st_size}
    finally:
        if descriptor >= 0:
            os.close(descriptor)


class RunStore(AbstractContextManager):
    def __init__(self, root: Path):
        requested = Path(root).absolute()
        _require(not requested.is_symlink(), "run root must not be a symlink")
        # macOS exposes /var and /tmp through system symlinks. Canonicalize the
        # caller's parent path before binding any owned receipts beneath it.
        self.root = requested.resolve()
        self.attempts: dict[Path, dict] = {}
        self._by_key: dict[str, list[Path]] = {}
        self.pairs: dict[str, dict] = {}
        self._mutex = threading.RLock()
        self._lock = None

    def __enter__(self):
        self.root.mkdir(parents=True, exist_ok=True)
        _require(not self.root.is_symlink() and self.root.resolve() == self.root, "run root must be canonical")
        lock_path = self.root / ".owner.lock"
        _require(not lock_path.is_symlink(), "run lock is a symlink")
        self._lock = lock_path.open("a+b")
        try:
            _lock_owner(self._lock)
            trials = self.root / "attempts"
            _require(not trials.is_symlink(), "attempts directory is a symlink")
            trials.mkdir(exist_ok=True)
            self._load(trials)
            pairs = self.root / "pairs"
            _require(not pairs.is_symlink(), "pairs directory is a symlink")
            pairs.mkdir(exist_ok=True)
            self._load_pairs(pairs)
        except (OSError, StoreError) as exc:
            self._lock.close()
            self._lock = None
            raise StoreError(f"cannot open native run: {exc}") from exc
        return self

    def __exit__(self, *exc):
        if self._lock is not None:
            try:
                _unlock_owner(self._lock)
            finally:
                self._lock.close()
                self._lock = None
        return False

    def _load(self, trials: Path) -> None:
        for attempt in sorted(trials.iterdir()):
            _require(attempt.is_dir() and not attempt.is_symlink(), "unexpected attempt entry")
            _require(re.fullmatch(r"[a-f0-9]{32}", attempt.name) is not None, "invalid attempt directory identity")
            reservation_path = attempt / "reservation.json"
            if not reservation_path.exists():
                # A crash before publication never admitted a subject launch.
                _require(all(path.name.startswith(".pending-") for path in attempt.iterdir()),
                         "unreserved directory contains execution evidence")
                continue
            reservation = _read(reservation_path)
            _require(set(reservation) == {"schema", "key", "row", "input", "sequence", "reserved_at"},
                     "malformed reservation receipt")
            key = _trial_key(reservation.get("row"), reservation.get("input"))
            _require(reservation.get("key") == key and reservation.get("schema") == "native-reservation/v1", "reservation identity mismatch")
            _require(type(reservation.get("sequence")) is int and reservation["sequence"] > 0, "invalid attempt sequence")
            reserved_at = reservation.get("reserved_at")
            _require(type(reserved_at) is float and math.isfinite(reserved_at) and reserved_at >= 0,
                     "invalid reservation timestamp")
            state = {"reservation": reservation, "capture": None, "grades": {},
                     "grade_evidence": {}, "grade_receipts": {}}
            if (attempt / "capture.json").exists():
                state["capture"] = self._load_capture(attempt)
            for path in attempt.glob("grade-*.json"):
                grade = _read(path)
                _require(set(grade) in ({"grader", "verdict"}, {"grader", "verdict", "evidence"}),
                         "malformed grade receipt")
                identity = path.name[6:-5]
                _sha(identity)
                _require(grade.get("grader") == identity, "grader identity mismatch")
                self._validate_grade(state["capture"], grade.get("verdict"))
                if "evidence" in grade:
                    self._validate_stored_evidence(attempt, grade["evidence"])
                    state["grade_evidence"][identity] = grade["evidence"]
                state["grades"][identity] = grade["verdict"]
                state["grade_receipts"][identity] = grade
            self.attempts[attempt] = state
            self._by_key.setdefault(key, []).append(attempt)
        for attempts in self._by_key.values():
            attempts.sort(key=lambda path: self.attempts[path]["reservation"]["sequence"])
            sequences = [self.attempts[path]["reservation"]["sequence"] for path in attempts]
            _require(sequences == list(range(1, len(sequences) + 1)), "duplicate or missing attempt sequence")

    def _load_pairs(self, pairs: Path) -> None:
        for directory in sorted(pairs.iterdir()):
            _require(directory.is_dir() and not directory.is_symlink(), "unexpected pair entry")
            _sha(directory.name)
            identity_path = directory / "identity.json"
            if not identity_path.exists():
                _require(all(path.name.startswith(".pending-") for path in directory.iterdir()),
                         "unreserved pair directory contains evidence")
                continue
            identity = _read(identity_path)
            _require(set(identity) == {"schema", "input", "arms"}
                     and identity["schema"] == "native-pair-input/v1"
                     and identity["input"] == directory.name, "malformed pair identity receipt")
            identity["arms"] = _pair_arm_identities(identity["arms"])
            state = {"directory": directory, "identity": identity, "grades": {},
                     "grade_evidence": {}, "grade_receipts": {}}
            for path in directory.glob("grade-*.json"):
                grade = _read(path)
                _require(set(grade) in (
                    {"schema", "input", "arms", "grader", "verdict"},
                    {"schema", "input", "arms", "grader", "verdict", "evidence"},
                ) and grade["schema"] == "native-pair-grade/v1", "malformed pair grade receipt")
                grader = path.name[6:-5]
                _sha(grader)
                _require(grade["input"] == directory.name
                         and _pair_arm_identities(grade["arms"]) == identity["arms"],
                         "pair grade arm binding mismatch")
                _require(grade["grader"] == grader, "pair grader identity mismatch")
                _validate_pair_verdict(grade["verdict"])
                if "evidence" in grade:
                    self._validate_stored_evidence(directory, grade["evidence"])
                    state["grade_evidence"][grader] = grade["evidence"]
                state["grades"][grader] = grade["verdict"]
                state["grade_receipts"][grader] = grade
            self.pairs[directory.name] = state

    def _load_capture(self, attempt: Path) -> dict:
        capture = _read(attempt / "capture.json")
        _require(set(capture) == {"schema", "observation", "error", "evidence"}
                 and capture["schema"] == "native-capture/v1", "malformed capture receipt")
        self._validate_capture(capture["observation"], capture["error"], capture["evidence"])
        self._validate_stored_evidence(attempt, capture["evidence"])
        return capture

    @staticmethod
    def _validate_capture(observation, error, evidence):
        valid = isinstance(observation, dict) and observation.get("completed") is True and observation.get("error") is None and error is None
        invalid = observation is None and isinstance(error, str) and bool(error.strip())
        _require(valid or invalid, "capture must contain complete observation or explicit infrastructure error")
        _require(isinstance(evidence, dict) and evidence
                 and all(isinstance(key, str) and key for key in evidence), "capture omitted raw evidence")

    @staticmethod
    def _validate_stored_evidence(attempt: Path, evidence: object) -> None:
        _require(isinstance(evidence, dict) and evidence
                 and all(isinstance(key, str) and key for key in evidence), "grade omitted raw evidence")
        for ref in evidence.values():
            _require(isinstance(ref, dict) and set(ref) == {"path", "sha256", "bytes"}, "malformed raw evidence reference")
            _require(isinstance(ref["path"], str) and bool(ref["path"]), "invalid raw evidence path")
            _sha(ref["sha256"])
            _require(type(ref["bytes"]) is int and ref["bytes"] >= 0, "invalid raw evidence size")
            actual = _file_ref(attempt, attempt / ref["path"])
            _require(actual == ref, "raw evidence changed since capture")

    @staticmethod
    def _validate_grade(capture, verdict):
        _require(isinstance(capture, dict) and capture.get("error") is None, "invalid or incomplete capture cannot receive a behavioral grade")
        _require(isinstance(verdict, dict) and verdict.get("status") in {"pass", "fail", "invalid"}
                 and isinstance(verdict.get("checks"), list), "invalid terminal grade")

    def lookup(self, row: dict, fingerprint: str, grader: str) -> dict:
        with self._mutex:
            _sha(grader)
            key = _trial_key(row, fingerprint)
            attempts = self._by_key.get(key, [])
            if not attempts:
                return {"status": "not_run"}
            attempt = attempts[-1]
            state = self.attempts[attempt]
            capture = state["capture"]
            status = "incomplete" if capture is None else "invalid" if capture["error"] is not None else "needs_grade"
            verdict = state["grades"].get(grader)
            if verdict is not None:
                status = verdict["status"]
            return {"status": status, "attempt": attempt, "capture": copy.deepcopy(capture),
                    "verdict": copy.deepcopy(verdict),
                    "grade_evidence": copy.deepcopy(state["grade_evidence"].get(grader))}

    def reserve(self, row: dict, fingerprint: str, *, retry: bool = False) -> Path:
        with self._mutex:
            _require(self._lock is not None, "run store is not open")
            stored_row = copy.deepcopy(row)
            key = _trial_key(stored_row, fingerprint)
            previous = self._by_key.get(key, [])
            _require(not previous or retry is True, "trial already reserved; explicit retry required")
            attempts = self.root / "attempts"
            _fsync_directory(attempts)
            attempt = attempts / uuid.uuid4().hex
            attempt.mkdir()
            _fsync_directory(attempt.parent)
            reservation = {"schema": "native-reservation/v1", "key": key, "row": stored_row,
                           "input": fingerprint, "sequence": len(previous) + 1, "reserved_at": time.time()}
            _publish(attempt / "reservation.json", reservation)
            self.attempts[attempt] = {"reservation": reservation, "capture": None, "grades": {},
                                      "grade_evidence": {}, "grade_receipts": {}}
            self._by_key.setdefault(key, []).append(attempt)
            return attempt

    def capture(self, attempt: Path, *, observation: dict | None, error: str | None, evidence: dict[str, Path]) -> None:
        with self._mutex:
            _require(self._lock is not None and attempt in self.attempts, "unknown or closed attempt")
            stored_observation = copy.deepcopy(observation)
            self._validate_capture(stored_observation, error, evidence)
            refs = {key: _file_ref(attempt, path) for key, path in evidence.items()}
            payload = {"schema": "native-capture/v1", "observation": stored_observation,
                       "error": error, "evidence": refs}
            _publish(attempt / "capture.json", payload)
            self.attempts[attempt]["capture"] = payload

    def grade(self, attempt: Path, grader: str, verdict: dict, *, evidence: dict[str, Path] | None = None) -> None:
        with self._mutex:
            _require(self._lock is not None and attempt in self.attempts, "unknown or closed attempt")
            _sha(grader)
            state = self.attempts[attempt]
            stored_verdict = copy.deepcopy(verdict)
            self._validate_grade(state["capture"], stored_verdict)
            refs = None
            if evidence is not None:
                _require(isinstance(evidence, dict) and evidence
                         and all(isinstance(key, str) and key for key in evidence), "grade omitted raw evidence")
                refs = {key: _file_ref(attempt, path) for key, path in evidence.items()}
            payload = {"grader": grader, "verdict": stored_verdict}
            if refs is not None:
                payload["evidence"] = refs
            _publish(attempt / f"grade-{grader}.json", payload)
            state["grades"][grader] = stored_verdict
            state["grade_receipts"][grader] = payload
            if refs is not None:
                state["grade_evidence"][grader] = refs

    def pair_arm(self, attempt: Path, grader: str) -> dict[str, object]:
        """Return one immutable subject arm for the pure pairing contract."""
        with self._mutex:
            _sha(grader)
            _require(self._lock is not None and attempt in self.attempts,
                     "unknown or closed subject attempt")
            state = self.attempts[attempt]
            capture = state["capture"]
            grade = state["grades"].get(grader)
            receipt = state["grade_receipts"].get(grader)
            _require(isinstance(capture, dict) and capture.get("error") is None,
                     "pair arm has no valid capture")
            _require(isinstance(grade, dict) and isinstance(receipt, dict),
                     "pair arm has no terminal grade")
            row = state["reservation"]["row"]
            return {
                "case_id": row["case_id"], "host": row["host"], "mode": row["mode"],
                "trial": row["trial"], "input_fingerprint": state["reservation"]["input"],
                "capture_sha256": digest(capture), "grade_identity": grader,
                "grade_sha256": digest(receipt), "grade": copy.deepcopy(grade),
                "observation": copy.deepcopy(capture["observation"]),
            }

    def pair_lookup(self, fingerprint: str, grader: str, arms: object) -> dict[str, object]:
        """Return the terminal pair grade or the exact derived work still required."""
        with self._mutex:
            _sha(fingerprint)
            _sha(grader)
            identities = _pair_arm_identities(arms)
            state = self.pairs.get(fingerprint)
            if state is None:
                return {"status": "not_run"}
            _require(state["identity"]["arms"] == identities,
                     "stored pair arms disagree with current evidence")
            verdict = state["grades"].get(grader)
            return {
                "status": verdict["status"] if verdict is not None else "needs_grade",
                "directory": state["directory"], "verdict": copy.deepcopy(verdict),
                "grade_evidence": copy.deepcopy(state["grade_evidence"].get(grader)),
            }

    def pair_reserve(self, fingerprint: str, arms: object) -> Path:
        """Idempotently publish the immutable two-arm identity before derived work."""
        with self._mutex:
            _require(self._lock is not None, "run store is not open")
            _sha(fingerprint)
            identities = _pair_arm_identities(arms)
            state = self.pairs.get(fingerprint)
            if state is not None:
                _require(state["identity"]["arms"] == identities,
                         "stored pair arms disagree with current evidence")
                return state["directory"]
            pairs = self.root / "pairs"
            directory = pairs / fingerprint
            _require(not directory.is_symlink(), "pair directory is a symlink")
            directory.mkdir(exist_ok=True)
            _fsync_directory(directory.parent)
            identity = {"schema": "native-pair-input/v1", "input": fingerprint, "arms": identities}
            _publish(directory / "identity.json", identity)
            self.pairs[fingerprint] = {
                "directory": directory, "identity": identity, "grades": {},
                "grade_evidence": {}, "grade_receipts": {},
            }
            return directory

    def pair_grade(self, fingerprint: str, grader: str, arms: object, verdict: dict,
                   *, evidence: dict[str, Path] | None = None) -> None:
        """Publish one immutable pair-only grade bound to both retained subject arms."""
        with self._mutex:
            _require(self._lock is not None, "run store is not open")
            _sha(fingerprint)
            _sha(grader)
            identities = _pair_arm_identities(arms)
            state = self.pairs.get(fingerprint)
            _require(state is not None and state["identity"]["arms"] == identities,
                     "pair must be reserved with the same arms before grading")
            stored_verdict = copy.deepcopy(verdict)
            _validate_pair_verdict(stored_verdict)
            refs = None
            if evidence is not None:
                _require(isinstance(evidence, dict) and evidence
                         and all(isinstance(key, str) and key for key in evidence),
                         "pair grade omitted raw evidence")
                refs = {key: _file_ref(state["directory"], path) for key, path in evidence.items()}
            payload = {"schema": "native-pair-grade/v1", "input": fingerprint,
                       "arms": identities, "grader": grader, "verdict": stored_verdict}
            if refs is not None:
                payload["evidence"] = refs
            _publish(state["directory"] / f"grade-{grader}.json", payload)
            state["grades"][grader] = stored_verdict
            state["grade_receipts"][grader] = payload
            if refs is not None:
                state["grade_evidence"][grader] = refs

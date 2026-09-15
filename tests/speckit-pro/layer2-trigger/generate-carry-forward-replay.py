#!/usr/bin/env python3
"""Generate an immutable old/current parser replay artifact without providers."""
from __future__ import annotations

import argparse
import builtins
import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import sysconfig
import tempfile


REPO = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO / "tests/speckit-pro"
LIB = TEST_ROOT / "lib"
sys.path.insert(0, str(LIB))
import trigger_carry_forward as carry  # noqa: E402
import trigger_comparison as comparison  # noqa: E402
import trigger_evidence as current_evidence  # noqa: E402


def observer_files(revision: str) -> list[str]:
    output = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", revision,
         "tests/speckit-pro/lib", "tests/speckit-pro/layer2-trigger"],
        cwd=REPO, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    parents = {"tests/speckit-pro/lib", "tests/speckit-pro/layer2-trigger"}
    return sorted(path for path in output if path.endswith(".py") and str(Path(path).parent) in parents)


def extract_closure(revision: str, destination: Path) -> dict[str, str]:
    files = {}
    for relative in observer_files(revision):
        payload = subprocess.run(["git", "show", f"{revision}:{relative}"], cwd=REPO,
                                 check=True, capture_output=True).stdout
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        key = Path(relative).relative_to("tests/speckit-pro").as_posix()
        files[key] = hashlib.sha256(payload).hexdigest()
    return files


def record_projection(record: dict, replayed: dict, *, checker=current_evidence.trial_checks) -> dict:
    comparison._require(isinstance(replayed, dict) and replayed.get("valid") is True,
                        "isolated parser rejected a retained valid stream")
    merged = {**record, **replayed, "stream_valid": replayed["valid"]}
    checks = checker(merged)
    comparison._require(record.get("valid") is True and record.get("trial_valid") is True
                        and isinstance(checks, dict) and checks
                        and all(value is True for value in checks.values())
                        and record.get("checks") == checks,
                        "isolated typed execution or cleanup checks disagree with retained evidence")
    merged.update(checks=checks, valid=True, trial_valid=True)
    return carry._projection(merged)


def _reviewed_closure_sources(closure: Path, expected_files: dict[str, str]) -> dict[str, bytes]:
    sources = {}
    for relative, digest in expected_files.items():
        path = f"tests/speckit-pro/{relative}"
        payload = carry.read_external_file(
            closure, {"path": path, "sha256": digest},
            "reviewed isolated verifier closure", max_bytes=carry._MAX_STREAM)
        sources[relative] = payload
    return sources


class _VerifiedBytesLoader(importlib.abc.Loader):
    def __init__(self, name: str, relative: str, source: bytes, origin: Path,
                 consumed: dict[str, str], loaded: dict[str, str], finder):
        self.name, self.relative, self.source, self.origin = name, relative, source, origin
        self.consumed, self.loaded = consumed, loaded
        self.finder = finder

    def create_module(self, _spec):
        return None

    def exec_module(self, module) -> None:
        digest = hashlib.sha256(self.source).hexdigest()
        module.__file__ = str(self.origin)
        self.consumed[self.relative] = digest
        self.loaded[self.name] = self.relative
        safe_builtins = dict(vars(builtins))
        safe_builtins["__import__"] = self.finder.safe_import
        module.__dict__["__builtins__"] = safe_builtins
        try:
            exec(compile(self.source, str(self.origin), "exec", dont_inherit=True), module.__dict__)
        finally:
            self.finder.sanitize_paths()


class _TrustedPathList(list):
    """Keep extracted or caller-controlled paths out of isolated imports."""
    def __init__(self, values: list[str], trusted_roots: tuple[Path, ...]):
        super().__init__(values)
        self.trusted_roots = trusted_roots

    def _trusted(self, value: object) -> bool:
        if not isinstance(value, str) or not value:
            return False
        try:
            resolved = Path(value).resolve()
        except OSError:
            return False
        return any(resolved == root or resolved.is_relative_to(root) for root in self.trusted_roots)

    def insert(self, index, value) -> None:
        if self._trusted(value):
            super().insert(index, value)

    def append(self, value) -> None:
        if self._trusted(value):
            super().append(value)

    def extend(self, values) -> None:
        super().extend(value for value in values if self._trusted(value))


def _trusted_directory_identity(path: Path) -> tuple[int, ...]:
    value = path.stat()
    comparison._require(stat.S_ISDIR(value.st_mode) and value.st_uid in {0, os.getuid()}
                        and not value.st_mode & (stat.S_IWGRP | stat.S_IWOTH),
                        "isolated verifier standard-library root is unsafe")
    return (value.st_dev, value.st_ino, value.st_mode, value.st_uid,
            value.st_mtime_ns, value.st_ctime_ns)


def _sanitize_import_paths(finder) -> None:
    comparison._require(all(_trusted_directory_identity(root) == identity
                            for root, identity in finder.trusted_identities.items()),
                        "isolated verifier standard-library identity changed")
    sys.path = _TrustedPathList([str(path) for path in finder.search_paths], finder.trusted_roots)


def _trusted_imported_module(finder, module) -> bool:
    name = getattr(module, "__name__", "")
    if name in finder.modules:
        loader = getattr(module, "__loader__", None)
        return isinstance(loader, _VerifiedBytesLoader) and loader.relative == finder.modules[name]
    spec = getattr(module, "__spec__", None)
    if spec is not None and spec.origin in {"built-in", "frozen"}:
        return True
    raw = getattr(module, "__file__", None)
    if not isinstance(raw, str):
        return False
    try:
        resolved = Path(raw).resolve()
    except OSError:
        return False
    return any(resolved.is_relative_to(root) for root in finder.trusted_roots)


def _safe_import(finder, name, globals=None, locals=None, fromlist=(), level=0):
    comparison._require(level == 0 and isinstance(name, str) and name,
                        "isolated verifier attempted an unsupported relative import")
    finder.sanitize_paths()
    module = builtins.__import__(name, globals, locals, fromlist, level)
    for loaded_name in {name, name.partition(".")[0]}:
        loaded = sys.modules.get(loaded_name)
        comparison._require(loaded is not None and _trusted_imported_module(finder, loaded),
                            "isolated verifier import escaped its approved closure or "
                            f"standard library: {loaded_name}")
    finder.sanitize_paths()
    return module


class _ClosedBytesFinder(importlib.abc.MetaPathFinder):
    def __init__(self, closure: Path, sources: dict[str, bytes], expected: dict[str, str]):
        self.closure, self.sources, self.expected = closure, sources, expected
        self.consumed: dict[str, str] = {}
        self.loaded: dict[str, str] = {}
        self.modules = {Path(relative).stem: relative for relative in sources
                        if Path(relative).parent.as_posix() in {"lib", "layer2-trigger"}
                        and Path(relative).stem.isidentifier()}
        stdlib = Path(sysconfig.get_path("stdlib")).resolve()
        self.trusted_roots = (stdlib,)
        self.search_paths = (stdlib, stdlib / "lib-dynload")
        self.trusted_identities = {
            root: _trusted_directory_identity(root) for root in self.trusted_roots}

    def sanitize_paths(self) -> None:
        _sanitize_import_paths(self)

    def safe_import(self, name, globals=None, locals=None, fromlist=(), level=0):
        return _safe_import(self, name, globals, locals, fromlist, level)

    def _spec(self, name: str, relative: str):
        comparison._require(relative in self.sources and relative in self.expected,
                            "isolated verifier requested a module outside its approved closure")
        origin = self.closure / "tests/speckit-pro" / relative
        loader = _VerifiedBytesLoader(name, relative, self.sources[relative], origin,
                                      self.consumed, self.loaded, self)
        return importlib.util.spec_from_loader(name, loader, origin=str(origin))

    def find_spec(self, fullname, _path=None, _target=None):
        if fullname in self.modules:
            return self._spec(fullname, self.modules[fullname])
        self.sanitize_paths()
        spec = importlib.machinery.BuiltinImporter.find_spec(fullname)
        if spec is None:
            spec = importlib.machinery.FrozenImporter.find_spec(fullname)
        if spec is None:
            search = list(_path) if _path is not None else list(self.search_paths)
            comparison._require(all(any(Path(entry).resolve() == root
                                        or Path(entry).resolve().is_relative_to(root)
                                        for root in self.trusted_roots) for entry in search),
                                "isolated verifier import search escaped trusted standard-library roots")
            spec = importlib.machinery.PathFinder.find_spec(fullname, [str(path) for path in search])
        if spec is None:
            raise ImportError(
                f"isolated verifier import is outside the approved closure and standard library: {fullname}")
        if spec.origin not in {"built-in", "frozen"}:
            comparison._require(isinstance(spec.origin, str)
                                and any(Path(spec.origin).resolve().is_relative_to(root)
                                        for root in self.trusted_roots),
                                f"isolated verifier import resolved outside the trusted standard library: {fullname}")
        return spec

    def load(self, name: str, relative: str):
        spec = self._spec(name, relative)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(name, None)
            raise
        return module


def replay_worker(closure: Path, source_root: Path, index_path: Path, output: Path,
                  namespace: str, expected_path: Path) -> int:
    closure = closure.resolve()
    sys.path[:] = [entry for entry in sys.path
                   if "trigger-case-carry-forward-repair" not in entry
                   and not Path(entry or ".").resolve().is_relative_to(closure)]
    index = json.loads(index_path.read_bytes())
    expected_files = json.loads(expected_path.read_bytes())
    sources = _reviewed_closure_sources(closure, expected_files)
    comparison._require({path: hashlib.sha256(payload).hexdigest()
                         for path, payload in sources.items()} == expected_files,
                        "isolated verifier closure differs from its reviewed bytes")
    for name in tuple(sys.modules):
        if name.startswith("trigger_"):
            del sys.modules[name]
    finder = _ClosedBytesFinder(closure, sources, expected_files)
    finder.sanitize_paths()
    sys.meta_path.insert(0, finder)
    try:
        isolated = finder.load("trigger_comparison", "lib/trigger_comparison.py")
        isolated_evidence = sys.modules["trigger_evidence"]
        parsers = {
            "claude": finder.load("trigger_replay_claude", "layer2-trigger/run-trigger-evals.py"),
            "codex": finder.load("trigger_replay_codex", "layer2-trigger/run_codex_evals.py"),
        }
        isolated._PARSERS.update(parsers)
        sys.path[:] = [entry for entry in sys.path
                       if not Path(entry or ".").resolve().is_relative_to(closure)]
        rows = []
        for item in index["trials"]:
            stdout = carry.read_external_file(source_root, item["stdout"], "replay stdout",
                                              max_bytes=carry._MAX_STREAM)
            record_bytes = carry.read_external_file(source_root, item["record"], "replay record",
                                                    max_bytes=carry._MAX_JSON)
            record = json.loads(record_bytes)
            replayed = isolated.replay(stdout, item["replay_context"])
            rows.append({
                "arm": "baseline", "case_id": item["case_id"], "trial_number": item["trial_number"],
                "record_sha256": hashlib.sha256(record_bytes).hexdigest(),
                "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
                "replay_context_sha256": isolated.json_digest(item["replay_context"]),
                "projection": record_projection(record, replayed, checker=isolated_evidence.trial_checks),
            })
    finally:
        sys.meta_path.remove(finder)
    comparison._require({path: hashlib.sha256(payload).hexdigest()
                         for path, payload in sources.items()} == expected_files
                        and finder.consumed
                        and all(finder.consumed[path] == expected_files[path]
                                for path in finder.consumed),
                        "loaded isolated verifier bytes changed during replay")
    module_files = {f"{namespace}:{name}": str(closure / "tests/speckit-pro" / relative)
                    for name, relative in finder.loaded.items()}
    output.write_text(json.dumps({"trials": rows, "module_files": module_files,
                                  "module_namespace": namespace,
                                  "loaded_files": finder.consumed}, sort_keys=True), encoding="utf-8")
    return 0


def generate(old_revision: str, current_revision: str, source_root: Path,
             index_path: Path, output: Path) -> int:
    with tempfile.TemporaryDirectory(prefix="trigger-old-closure-") as old_temp, \
         tempfile.TemporaryDirectory(prefix="trigger-current-closure-") as current_temp, \
         tempfile.TemporaryDirectory(prefix="trigger-replay-results-") as result_temp:
        old_root, current_root = Path(old_temp).resolve(), Path(current_temp).resolve()
        old_files = extract_closure(old_revision, old_root)
        current_files = extract_closure(current_revision, current_root)
        results = Path(result_temp)
        index_bytes = carry.read_external_file(
            index_path.parent,
            {"path": index_path.name, "sha256": carry.EXPECTED_RAW_SHA256["partial_index"]},
            "frozen partial evidence index", max_bytes=carry._MAX_JSON)
        safe_index = results / "partial-index.json"
        safe_index.write_bytes(index_bytes)
        worker = Path(__file__).resolve()
        for name, namespace, root in (("original", "trigger_original_replay", old_root),
                                      ("current", "trigger_current_replay", current_root)):
            expected = results / f"{name}-files.json"
            expected.write_text(json.dumps(old_files if name == "original" else current_files,
                                           sort_keys=True), encoding="utf-8")
            subprocess.run([sys.executable, str(worker), "--worker", str(root), str(source_root),
                            str(safe_index), str(results / f"{name}.json"), namespace, str(expected)], check=True)
        original = json.loads((results / "original.json").read_bytes())
        current = json.loads((results / "current.json").read_bytes())
        if len(original["trials"]) != 411 or len(current["trials"]) != 411:
            raise ValueError("dual replay did not produce the exact 411-trial cohort")
        trials = []
        for old, new in zip(original["trials"], current["trials"], strict=True):
            identity_fields = {key: old[key] for key in (
                "arm", "case_id", "trial_number", "record_sha256", "stdout_sha256", "replay_context_sha256")}
            if identity_fields != {key: new[key] for key in identity_fields}:
                raise ValueError("dual replay trial order or raw binding changed")
            if comparison.json_digest(old["projection"]) != comparison.json_digest(new["projection"]):
                raise ValueError(f"parser projection mismatch for {old['case_id']} trial {old['trial_number']}")
            trials.append({**identity_fields, "original": old["projection"], "current": new["projection"]})
        closures = []
        for namespace, revision, root, files, result in (
            ("trigger_original_replay", old_revision, old_root, old_files, original),
            ("trigger_current_replay", current_revision, current_root, current_files, current),
        ):
            module_files = result["module_files"]
            loaded_files = result["loaded_files"]
            if result["module_namespace"] != namespace:
                raise ValueError("replay worker namespace changed")
            closures.append({"observer_sha256": comparison.json_digest(files),
                             "source_commit": subprocess.run(["git", "rev-parse", revision], cwd=REPO,
                                 check=True, capture_output=True, text=True).stdout.strip(),
                             "root": str(root), "files": files, "loaded_files": loaded_files,
                             "module_namespace": namespace, "import_isolation": True,
                             "module_files": module_files})
        artifact = {"schema_version": carry.DUAL_REPLAY_SCHEMA_VERSION,
                    "source_index_sha256": hashlib.sha256(index_bytes).hexdigest(),
                    "equality_projection": list(carry.PROJECTION_FIELDS),
                    "original_closure": closures[0], "current_closure": closures[1], "trials": trials}
        output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("args", nargs="*")
    parsed = parser.parse_args(argv)
    if parsed.worker:
        if len(parsed.args) != 6:
            parser.error("worker expected CLOSURE SOURCE_ROOT INDEX_PATH OUTPUT NAMESPACE EXPECTED_FILES")
        closure, source_root, index_path, output = map(Path, parsed.args[:4])
        return replay_worker(closure, source_root, index_path, output, parsed.args[4], Path(parsed.args[5]))
    if len(parsed.args) != 5:
        parser.error("expected OLD_REV CURRENT_REV SOURCE_ROOT INDEX_PATH OUTPUT")
    old, current, source, index, output = parsed.args
    return generate(old, current, Path(source).resolve(), Path(index).resolve(), Path(output).resolve())


if __name__ == "__main__":
    raise SystemExit(main())

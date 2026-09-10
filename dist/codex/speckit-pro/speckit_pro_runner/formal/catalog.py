"""Strict model catalog and durable paths, independent of application discovery."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .selection import SelectionError, require_fields, require_text, unique_object

CATALOG_PATH = ".specify/formal-methods.json"
RUNS_PATH = ".specify/formal-runs"
EVIDENCE_PATH = ".specify/formal-evidence"
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
VERSIONS = {"apalache": "0.62.2", "tlc": "1.7.4"}


class FormalError(ValueError):
    def __init__(self, verdict: str, message: str):
        super().__init__(message)
        self.verdict = verdict


def confined(root: Path, value: str, *, durable: bool = False) -> Path:
    require_text(value, "path")
    path = Path(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise SelectionError(f"path must be relative to WORKFLOW_ROOT: {value}")
    result = (root / path).resolve()
    if not result.is_relative_to(root.resolve()) or any(p.casefold() == ".git" for p in path.parts):
        raise SelectionError(f"path leaves the workflow's permitted files: {value}")
    canonical = result.relative_to(root.resolve()).as_posix()
    if durable and (canonical.split("/")[0] == "specs" or canonical.startswith((RUNS_PATH, EVIDENCE_PATH, ".specify/formal-traces"))):
        raise SelectionError(f"model inputs must survive archival and exclude run results: {value}")
    return result


def reject_nonfinite(value: str) -> Any:
    raise SelectionError(f"non-finite JSON number is invalid: {value}")


def read_json(path: Path) -> Any:
    if path.stat().st_size > 1_048_576:
        raise SelectionError(f"JSON input exceeds 1 MiB: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object, parse_constant=reject_nonfinite)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def bounded_integer(value: Any, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise SelectionError(f"{label} must be an integer from {low} to {high}")
    return value


def operator(value: Any) -> str:
    if not isinstance(value, str) or not NAME.fullmatch(value):
        raise SelectionError("operator names must be TLA+ identifiers")
    return value


def validate_tool(tool: Any, checker: str) -> dict[str, Any]:
    require_fields(tool, {"version", "jar", "sha256", "java", "heap_mb"}, "checker tool")
    if tool["version"] != VERSIONS.get(checker):
        raise FormalError("version_mismatch", f"{checker} requires qualified version {VERSIONS.get(checker)}")
    for key in ("jar", "java"):
        require_text(tool[key], f"tool.{key}")
    if not isinstance(tool["sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", tool["sha256"]):
        raise SelectionError("tool.sha256 must pin the actual jar")
    bounded_integer(tool["heap_mb"], 256, 65536, "tool.heap_mb")
    return tool


def validate_properties(properties: Any) -> dict[str, Any]:
    if not isinstance(properties, dict) or not properties:
        raise SelectionError("model.properties must map at least one operator to its requirement and kind")
    for name, mapping in properties.items():
        operator(name)
        require_fields(mapping, {"kind", "requirement"}, f"property {name}")
        require_text(mapping["requirement"], f"property {name} requirement")
        if mapping["kind"] not in ("invariant", "temporal"):
            raise SelectionError("property kind must be invariant or temporal")
    return properties


def validate_mode(model: dict[str, Any]) -> None:
    mode = model["mode"]
    modes = ("finite", "temporal") if model["checker"] == "tlc" else ("bounded", "temporal", "inductive")
    if mode not in modes:
        raise FormalError("unsupported", f"unsupported {model['checker']} mode: {mode}")
    temporal = any(p["kind"] == "temporal" for p in model["properties"].values())
    if (mode == "temporal") != temporal:
        raise SelectionError("temporal properties require temporal mode; other modes require invariants")
    if model["checker"] == "tlc":
        require_fields(model["bounds"], {"max_set_size"}, "TLC enumeration bound")
        bounded_integer(model["bounds"]["max_set_size"], 1, 10_000_000, "bounds.max_set_size")
    elif mode == "inductive":
        require_fields(model["bounds"], {"inductive_invariant"}, "inductive bounds")
        operator(model["bounds"]["inductive_invariant"])
    else:
        require_fields(model["bounds"], {"length"}, "bounded search")
        bounded_integer(model["bounds"]["length"], 0, 10000, "bounds.length")


def validate_language(model: dict[str, Any]) -> None:
    language = model.get("language", "tla")
    if language not in ("tla", "quint"):
        raise FormalError("unsupported", "model.language must be tla or quint")
    if language == "quint":
        require_text(model.get("main"), "Quint model.main")
        operator(model.get("main"))
        if model["checker"] != "apalache" or model["mode"] not in ("bounded", "temporal"):
            raise FormalError("unsupported", "The qualified Quint profile uses Apalache bounded or temporal checking")
    elif "main" in model:
        raise SelectionError("model.main applies only to Quint modules")


def validate_model(model: Any, root: Path, selected: dict[str, Any]) -> dict[str, Any]:
    behavior = {"specification"} if isinstance(model, dict) and "specification" in model else {"init", "next"}
    optional = {"implementation_inputs", "language", "main", "trace"} & model.keys() if isinstance(model, dict) else set()
    require_fields(model, {"checker", "module", "config", "inputs", "properties", "assumptions", "mode", "bounds", "budget"} | behavior | optional, "model")
    require_text(model["checker"], "model.checker")
    if model["checker"] not in VERSIONS:
        raise FormalError("unsupported", f"unsupported checker: {model['checker']}")
    for field in behavior:
        operator(model[field])
    if "specification" in model and model["checker"] != "tlc":
        raise FormalError("unsupported", "SPECIFICATION configuration is supported only by the TLC integration")
    validate_properties(model["properties"])
    validate_mode(model)
    validate_language(model)
    require_fields(model["budget"], {"timeout_seconds", "output_bytes"}, "model budget")
    bounded_integer(model["budget"]["timeout_seconds"], 1, 3600, "timeout_seconds")
    bounded_integer(model["budget"]["output_bytes"], 4096, 8_388_608, "output_bytes")
    if not isinstance(model["assumptions"], list):
        raise SelectionError("model.assumptions must be an array, including [] when there are none")
    for assumption in model["assumptions"]:
        require_text(assumption, "assumption")
    validate_model_paths(model, root, selected)
    implementation = model.get("implementation_inputs", [])
    if "implementation_inputs" in model and not implementation:
        raise SelectionError("implementation_inputs must contain at least one durable path when declared")
    if not isinstance(implementation, list) or any(not isinstance(p, str) for p in implementation) or len(set(implementation)) != len(implementation):
        raise SelectionError("implementation_inputs must be a list of unique durable paths")
    for path in implementation:
        confined(root, path, durable=True)
    if "trace" in model or selected["evidence"] == "model_and_trace":
        from .traces import validate_contract
        validate_contract(model, root, selected["id"])
    from .native_config import validate_apalache, validate_tlc
    validator = validate_tlc if model["checker"] == "tlc" else validate_apalache
    validator(model, confined(root, model["config"]).read_text(encoding="utf-8"))
    return model


def validate_model_paths(model: dict[str, Any], root: Path, selected: dict[str, Any]) -> None:
    inputs = model["inputs"]
    if not isinstance(inputs, list) or not inputs or any(not isinstance(p, str) for p in inputs):
        raise SelectionError("model.inputs must explicitly list model, configuration, and imported files")
    if len(set(inputs)) != len(inputs):
        raise SelectionError("model.inputs cannot repeat paths")
    suffix = ".qnt" if model.get("language") == "quint" else ".tla"
    for field, suffix in (("module", suffix), ("config", ".cfg")):
        path = require_text(model[field], field)
        if path not in inputs or not path.endswith(suffix):
            raise SelectionError(f"{field} must be a declared {suffix} input")
    if selected["origin"] == "new" and not model["module"].startswith(f"formal/{selected['id']}/"):
        raise SelectionError("new models belong in formal/<selected-model-id>/")
    for value in inputs:
        path = confined(root, value, durable=True)
        if not path.is_file():
            raise FormalError("pending_authoring" if selected["origin"] == "new" else "missing_input", f"missing declared model input: {value}")


def selected_catalog(root: Path, selection: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Inspect selected records only. Unselected tools and files are not probed."""
    path = confined(root, CATALOG_PATH)
    catalog = read_json(path) if path.is_file() else {"schema_version": "1.0", "tools": {}, "models": {}}
    require_fields(catalog, {"schema_version", "tools", "models"}, "formal catalog")
    if catalog["schema_version"] != "1.0" or not isinstance(catalog["models"], dict) or not isinstance(catalog["tools"], dict):
        raise SelectionError("formal catalog needs schema_version 1.0 and object tools/models")
    resolved: dict[str, Any] = {}
    gaps: list[dict[str, Any]] = []
    for selected in selection["models"]:
        model_id = selected["id"]
        try:
            if model_id not in catalog["models"]:
                raise FormalError("pending_authoring" if selected["origin"] == "new" else "missing_input", f"catalog definition missing for {model_id}")
            model = validate_model(catalog["models"][model_id], root, selected)
            if model["checker"] not in catalog["tools"]:
                raise FormalError("missing_tool", f"configure the approved pinned {model['checker']} distribution in catalog.tools")
            tool = validate_tool(catalog["tools"].get(model["checker"]), model["checker"])
            resolved[model_id] = {"model": model, "tool": tool, "input_hashes": {p: digest(confined(root, p)) for p in model["inputs"]}}
            if model.get("language") == "quint":
                from .quint import validate_tool as validate_quint
                resolved[model_id]["compiler"] = validate_quint(catalog["tools"].get("quint"))
        except FormalError as exc:
            gaps.append({"model": model_id, "verdict": exc.verdict, "reason": str(exc)})
    return resolved, gaps

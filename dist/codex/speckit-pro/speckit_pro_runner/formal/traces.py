"""Match complete observed ITF traces against the original native transition relation."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import time
import uuid
from typing import Any

from . import apalache, itf, tlc
from .catalog import CATALOG_PATH, FormalError, bounded_integer, confined, digest, operator, read_json
from .native_config import trace_configuration
from .process import run_process
from .selection import require_fields

TRACE_PATH = ".specify/formal-traces"


def selected_paths(root: Path, selection: dict[str, Any], models: dict[str, Any]) -> set[str]:
    paths = set()
    for selected in selection["models"]:
        if selected["evidence"] != "model_and_trace":
            continue
        for path in models[selected["id"]]["model"]["trace"]["paths"]:
            if not confined(root, path).is_file():
                raise FormalError("missing_trace", f"Run the producing tests before final/Post checking: {path}")
            paths.add(path)
    return paths


def preview(root: Path, selection: dict[str, Any], models: dict[str, Any]) -> dict[str, Any]:
    checks = {}
    for selected in selection["models"]:
        if selected["evidence"] != "model_and_trace":
            continue
        key = selected["id"]
        model = models[key]["model"]
        checks[key] = [{"path": path, "query": "complete_observed_trace_reachable",
                        "states": len(load_trace(root, key, model, path)["states"]),
                        "projection": model["trace"]["projection"], "actions": model["trace"]["actions"],
                        "adapter_test": model["trace"]["adapter_test"]} for path in model["trace"]["paths"]]
    return checks


def complete_receipts(receipts: Any, paths: list[str]) -> bool:
    if not isinstance(receipts, list) or any(not isinstance(r, dict) for r in receipts):
        return False
    if [r.get("path") for r in receipts] != paths:
        return False
    for receipt in receipts:
        if receipt.get("verdict") != "pass" or receipt.get("query") != "complete_observed_trace_reachable" or receipt.get("exit_code") != 12:
            return False
        if type(receipt.get("transitions")) is not int or receipt["transitions"] < 1:
            return False
        if type(receipt.get("states")) is not int or receipt["states"] != receipt["transitions"] + 1:
            return False
        if not isinstance(receipt.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", receipt["sha256"]):
            return False
    return True


def validate_contract(model: dict[str, Any], root: Path, model_id: str) -> None:
    contract = model.get("trace")
    if not isinstance(contract, dict):
        raise FormalError("missing_trace_contract", "Declare the selected action/state projection and its adapter test during Plan")
    require_fields(contract, {"format", "paths", "projection", "actions", "init", "next", "adapter_test", "max_states"}, "trace contract")
    if contract["format"] != "itf":
        raise FormalError("unsupported", "The qualified implementation trace adapter uses ITF")
    bounded_integer(contract["max_states"], 2, 1000, "trace.max_states")
    paths = contract["paths"]
    if not isinstance(paths, list) or not 1 <= len(paths) <= 50 or any(not isinstance(p, str) for p in paths) or len(set(paths)) != len(paths):
        raise ValueError("trace.paths must contain unique ITF output paths")
    for path in paths:
        confined(root, path)
        if not path.startswith(f"{TRACE_PATH}/{model_id}/") or not path.endswith(".itf.json"):
            raise ValueError("trace outputs belong under .specify/formal-traces/<model-id>/ and end in .itf.json")
    for field in ("projection", "actions"):
        mapping = contract[field]
        if not isinstance(mapping, dict) or not mapping:
            raise ValueError(f"trace.{field} must be a nonempty mapping")
        for key, value in mapping.items():
            operator(key)
            operator(value)
    if len(set(contract["projection"].values())) != len(contract["projection"]):
        raise ValueError("projected ITF variable names must be unique")
    for name in ("init", "next"):
        operator(contract[name])
        if name in model and contract[name] != model[name]:
            raise ValueError("trace Init/Next must match the checked model's native predicates")
    if contract["adapter_test"] not in model.get("implementation_inputs", []):
        raise ValueError("trace.adapter_test must be a declared implementation input; run it before checking traces")


def binding(root: Path, model_id: str) -> dict[str, Any]:
    """Capture before the producing test; revalidate before stamping its trace."""
    catalog = read_json(confined(root, CATALOG_PATH))
    model = catalog["models"][model_id]
    validate_contract(model, root, model_id)
    inputs = {name: digest(confined(root, name, durable=True)) for name in model["inputs"]}
    implementation = {name: digest(confined(root, name, durable=True)) for name in model["implementation_inputs"]}
    model_digest = hashlib.sha256(json.dumps(model, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"schema_version": "1.0", "model_id": model_id, "model_sha256": model_digest,
            "model_inputs": inputs, "implementation_inputs": implementation}


def write_trace(root: Path, model_id: str, path: str, trace: dict[str, Any], before: dict[str, Any]) -> None:
    """Bind an actual producer's ITF output to unchanged model and implementation inputs."""
    if before != binding(root, model_id):
        raise FormalError("stale_trace", "Model or implementation changed while producing the trace")
    model = read_json(confined(root, CATALOG_PATH))["models"][model_id]
    contract = model["trace"]
    if path not in contract["paths"]:
        raise ValueError("trace output was not selected in the model catalog")
    itf.states(trace, contract["projection"], contract["actions"], contract["max_states"])
    metadata = trace.get("#meta", {})
    if not isinstance(metadata, dict):
        raise FormalError("malformed_trace", "ITF trace metadata must be an object")
    from .evidence import atomic_record
    ignored = confined(root, TRACE_PATH)
    ignored.mkdir(parents=True, exist_ok=True)
    (ignored / ".gitignore").write_text("*\n", encoding="utf-8")
    atomic_record(confined(root, path), {**trace, "#meta": {**metadata, "speckit": before}})


def load_trace(root: Path, model_id: str, model: dict[str, Any], path: str) -> dict[str, Any]:
    source = confined(root, path)
    if not source.is_file():
        raise FormalError("missing_trace", f"Run the producing adapter tests; missing trace: {path}")
    try:
        trace = read_json(source)
    except ValueError as exc:
        raise FormalError("malformed_trace", f"Invalid ITF JSON: {exc}") from exc
    contract = model["trace"]
    itf.states(trace, contract["projection"], contract["actions"], contract["max_states"])
    metadata = trace.get("#meta")
    if not isinstance(metadata, dict) or metadata.get("speckit") != binding(root, model_id):
        raise FormalError("stale_trace", "Trace does not match the current model, projection, and implementation inputs")
    return trace


def projected_state(row: dict[str, Any], projection: dict[str, str], *, primed: bool = False) -> str:
    suffix = "'" if primed else ""
    return " /\\ ".join(f"{name}{suffix} = {itf.literal(row[field])}" for name, field in projection.items())


def wrapper(module: str, contract: dict[str, Any], rows: list[dict[str, Any]], prefix: str) -> str:
    index = prefix + "Index"
    initial = projected_state(rows[0], contract["projection"])
    steps = []
    for position, row in enumerate(rows[1:], 1):
        action = contract["actions"][row["#meta"]["action"]]
        observed = projected_state(row, contract["projection"], primed=True)
        steps.append(f"({index} = {position - 1} /\\ {contract['next']} /\\ {action} /\\ {observed} /\\ {index}' = {position})")
    return (f"---- MODULE {prefix} ----\nEXTENDS {module}, TLC\nVARIABLE\n  \\* @type: Int;\n  {index}\n"
            f"{prefix}Init == {contract['init']} /\\ {initial} /\\ {index} = 0\n"
            f"{prefix}Next == " + "\n  \\/ ".join(steps) + "\n"
            f"{prefix}NotObserved == {index} < {len(rows) - 1}\n====\n")


def remaining(deadline: float) -> int:
    value = math.ceil(deadline - time.monotonic())
    if value < 1:
        raise FormalError("timeout", "Model and trace checks exhausted the declared time budget")
    return value


def native_module(root: Path, item: dict[str, Any], model: dict[str, Any], snapshot: Path, run: Path, deadline: float) -> Path:
    if "compiler" not in item:
        return snapshot / model["module"]
    from .engine import checker_command
    target = snapshot / Path(model["module"]).parent / "SpecKitConverted.tla"
    argv = checker_command(root, item["tool"], str(run / "tmp")) + [f"--config-file={run / 'settings.json'}", f"--out-dir={run / 'converted'}", "parse", f"--output={target}", model["module"]]
    result = run_process(argv, snapshot, run / "conversion.log", remaining(deadline), model["budget"]["output_bytes"])
    if result["exit_code"] or result["timed_out"] or result["output_limited"] or not target.is_file():
        raise FormalError("timeout" if result["timed_out"] else "inconclusive", "Quint JSON to native TLA+ conversion did not complete")
    return target


def declarative_ir(value: Any, depth: int = 0) -> Any:
    """Use documented equalities for assignment hints in parsed trace queries.

    v' := e means v' = e; UNCHANGED e means e' = e. Normalize only native
    OperEx nodes, preserving literal data, annotations, and every constraint.
    https://apalache-mc.org/docs/apalache/assignments-in-depth.html
    """
    if depth > 256:
        raise FormalError("unsupported", "Trace query IR exceeds the supported nesting depth")
    if isinstance(value, list):
        return [declarative_ir(v, depth + 1) for v in value]
    if not isinstance(value, dict):
        return value
    result = {key: declarative_ir(v, depth + 1) for key, v in value.items()}
    if value.get("kind") == "OperEx" and value.get("oper") == "Apalache!:=":
        if len(result["args"]) != 2:
            raise FormalError("unsupported", "Unexpected native assignment IR")
        result["oper"] = "EQ"
    if value.get("kind") == "OperEx" and value.get("oper") == "UNCHANGED":
        if len(result["args"]) != 1:
            raise FormalError("unsupported", "Unexpected native UNCHANGED IR")
        operand = result["args"][0]
        primed = {"kind": "OperEx", "oper": "PRIME", "args": [operand], "type": operand.get("type", "Untyped"), "source": value.get("source", "UNKNOWN")}
        result.update(oper="EQ", args=[primed, operand])
    return result


def apalache_query(root: Path, item: dict[str, Any], module: Path, run: Path, deadline: float) -> Path:
    from .engine import checker_command
    target = module.with_suffix(".json")
    argv = checker_command(root, item["tool"], str(run / "tmp")) + [f"--config-file={run / 'settings.json'}", f"--out-dir={run / 'parsed'}", "typecheck", f"--output={target}", str(module)]
    result = run_process(argv, module.parent, run / (module.stem + "-parse.log"), remaining(deadline), item["model"]["budget"]["output_bytes"])
    if result["exit_code"] or result["timed_out"] or result["output_limited"] or not target.is_file():
        raise FormalError("timeout" if result["timed_out"] else "invalid_model", "Native trace query parsing did not complete; inspect the ignored parse log")
    native = read_json(target)
    if native.get("name") != "ApalacheIR" or native.get("version") != "1.0" or not native.get("modules"):
        raise FormalError("unsupported", "Unexpected native trace query IR schema")
    target.write_text(json.dumps(declarative_ir(native)), encoding="utf-8")
    return target


def witness_matches(output: Path, rows: list[dict[str, Any]], projection: dict[str, str], index: str) -> bool:
    for path in output.rglob("*.itf.json"):
        witness = read_json(path)
        states = witness.get("states", [])
        if len(states) != len(rows):
            continue
        for position, (actual, observed) in enumerate(zip(states, rows)):
            if actual.get(index) != {"#bigint": str(position)}:
                break
            if any(itf.literal(actual.get(name)) != itf.literal(observed[field]) for name, field in projection.items()):
                break
        else:
            return True
    return False


def trace_verdict(result: dict[str, Any], model: dict[str, Any], output: Path, rows: list[dict[str, Any]], prefix: str) -> str:
    classified = (apalache if model["checker"] == "apalache" else tlc).verdict(result)
    if classified == "violation":
        if model["checker"] == "apalache":
            expected = "The outcome is: Error" in result["output"] and witness_matches(output, rows, model["trace"]["projection"], prefix + "Index")
        else:
            indices = re.findall(rf"(?m)^/\\ {prefix}Index = ([0-9]+)\s*$", result["output"])
            expected = f"Invariant {prefix}NotObserved is violated." in result["output"] and indices == [str(i) for i in range(len(rows))]
        return "pass" if expected else "inconclusive"
    if classified == "pass" or result["exit_code"] == 0 and "The outcome is: ExecutionsTooShort" in result["output"]:
        return "trace_violation"
    return classified


def check_one(root: Path, item: dict[str, Any], model: dict[str, Any], source: Path, trace: dict[str, Any], run: Path, deadline: float) -> dict[str, Any]:
    from .engine import checker_command
    prefix = "SpecKitTrace" + uuid.uuid4().hex[:12]
    module = source.parent / (prefix + ".tla")
    config = source.parent / (prefix + ".cfg")
    rows = trace["states"]
    module.write_text(wrapper(source.stem, model["trace"], rows, prefix), encoding="utf-8")
    original = run / "inputs" / item["model"]["config"]
    config.write_text(trace_configuration(original.read_text(encoding="utf-8"), prefix + "Init", prefix + "Next", prefix + "NotObserved"), encoding="utf-8")
    output = run / prefix
    check_model = {**model, "module": str(module), "config": str(config), "init": prefix + "Init", "next": prefix + "Next",
                   "properties": {prefix + "NotObserved": {"kind": "invariant", "requirement": "observed trace reachability"}}}
    check_model.pop("specification", None)
    if model["checker"] == "apalache":
        check_model.update(mode="bounded", bounds={"length": len(rows) - 1}, module=str(apalache_query(root, item, module, run, deadline)))
        argv = apalache.arguments(check_model, apalache.obligations(check_model)[0], str(output), str(run / "settings.json"))
        argv[-1:-1] = ["--no-deadlock", "--discard-disabled=false"]
    else:
        argv = tlc.arguments(check_model, {}, str(output), "")
    result = run_process(checker_command(root, item["tool"], str(run / "tmp")) + argv, source.parent, run / (prefix + ".log"), remaining(deadline), model["budget"]["output_bytes"])
    verdict = trace_verdict(result, model, output, rows, prefix)
    return {"verdict": verdict, "states": len(rows), "transitions": len(rows) - 1, "exit_code": result["exit_code"],
            "query": "complete_observed_trace_reachable", "excerpt": result["output"][-2048:], "log": (run / (prefix + ".log")).relative_to(root).as_posix()}


def execute(root: Path, model_id: str, item: dict[str, Any], model: dict[str, Any], snapshot: Path, run: Path, deadline: float) -> list[dict[str, Any]]:
    source = native_module(root, item, model, snapshot, run, deadline)
    results = []
    for path in model["trace"]["paths"]:
        trace = load_trace(root, model_id, item["model"], path)
        result = check_one(root, item, model, source, trace, run, deadline)
        results.append({"path": path, "sha256": digest(confined(root, path)), **result})
        if result["verdict"] != "pass":
            break
    return results

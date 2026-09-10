"""Commands and conservative result classification for qualified Apalache."""

from __future__ import annotations

from typing import Any


def obligations(model: dict[str, Any]) -> list[dict[str, Any]]:
    invariants = [key for key, value in model["properties"].items() if value["kind"] == "invariant"]
    temporal = [key for key, value in model["properties"].items() if value["kind"] == "temporal"]
    if model["mode"] == "inductive":
        invariant = model["bounds"]["inductive_invariant"]
        return [
            {"id": "base", "init": model["init"], "invariants": [invariant], "temporal": [], "length": 0},
            {"id": "step", "init": invariant, "invariants": [invariant], "temporal": [], "length": 1},
            {"id": "consequence", "init": invariant, "invariants": invariants, "temporal": [], "length": 0},
        ]
    return [{"id": model["mode"], "init": model["init"], "invariants": invariants, "temporal": temporal, "length": model["bounds"]["length"]}]


def arguments(model: dict[str, Any], obligation: dict[str, Any], output: str, settings: str) -> list[str]:
    args = [f"--config-file={settings}", f"--out-dir={output}", "check", f"--config={model['config']}",
            f"--init={obligation['init']}", f"--next={model['next']}", f"--length={obligation['length']}"]
    if obligation["invariants"]:
        args.append("--inv=" + ",".join(obligation["invariants"]))
    if obligation["temporal"]:
        args.append("--temporal=" + ",".join(obligation["temporal"]))
    return [*args, model["module"]]


def verdict(result: dict[str, Any]) -> str:
    output = result["output"]
    if result["timed_out"]:
        return "timeout"
    if result["output_limited"]:
        return "inconclusive"
    lowered = output.casefold()
    if any(token in lowered for token in ("not supported", "unsupported", "notimplementederror", "not implemented", "ignored by apalache")):
        return "unsupported"
    if any(token in lowered for token in ("type input error", "type checking failed", "parsing failed", "syntax error", "semantic errors", "failed to parse", "configurationerror", "typing input error", "snowcat asks you to fix the types", "assignment error")):
        return "invalid_model"
    if result["exit_code"] == 0 and "The outcome is: NoError" in output and "EXITCODE: OK" in output:
        return "pass"
    if result["exit_code"] == 12 and any(f"The outcome is: {outcome}" in output for outcome in ("Error", "Deadlock")):
        return "violation"
    return "inconclusive"

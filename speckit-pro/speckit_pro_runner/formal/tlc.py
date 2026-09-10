"""Finite-state TLC 1.7.4 execution; simulation is never a passing check."""

from __future__ import annotations

import re
from typing import Any


def obligations(model: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"id": model["mode"]}]


def arguments(model: dict[str, Any], obligation: dict[str, Any], output: str, settings: str) -> list[str]:
    return ["-tool", "-workers", "1", "-fp", "0", "-seed", "1", "-fpmem", "0.25",
            "-maxSetSize", str(model["bounds"]["max_set_size"]), "-config", model["config"],
            "-metadir", output, model["module"]]


def verdict(result: dict[str, Any]) -> str:
    output = result["output"]
    if result["timed_out"]:
        return "timeout"
    if result["output_limited"]:
        return "inconclusive"
    if result["exit_code"] in (10, 11, 12, 13, 14):
        return "violation"
    lowered = output.casefold()
    if any(token in lowered for token in ("not supported", "unsupported", "cannot enumerate", "non-enumerable", "not enumerable", "attempted to enumerate", "tlc can't handle", "tlc cannot handle")):
        return "unsupported"
    if result["exit_code"] in (75, 76, 77, 150, 151):
        return "invalid_model"
    if re.search(r"STARTMSG \d+:[12] ", output):
        return "inconclusive"
    completed = "STARTMSG 2193:0 " in output and "STARTMSG 2186:0 " in output
    states = re.search(r"\b([1-9][0-9,]*) distinct states? (?:found|generated)", output)
    return "pass" if result["exit_code"] == 0 and completed and states else "inconclusive"

#!/usr/bin/env python3
"""Validate private canary evidence; this command never posts a release status."""

import argparse
import json
import math
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "speckit-pro"))
from speckit_pro_runner.json_schema import json_schema_failures  # noqa: E402
from speckit_pro_runner.strict_input import unique_object  # noqa: E402

SCHEMA = json.loads(Path(__file__).with_name("canary-receipt.schema.json").read_text(encoding="utf-8"))
BUDGET_FILE = Path(__file__).with_name("canary-budget.json")
HOSTS = tuple(SCHEMA["properties"]["host"]["enum"])
VARIANTS = tuple(SCHEMA["$defs"]["variant"]["properties"]["name"]["enum"])
BUDGET_STAGES = ("scaffold", "plan", "implement")  # ADR 0016; plan_review is recorded, never budgeted
METRICS = {"wall_seconds": (int, float), "tokens": (int,)}


def keyed(node, keys, where):
    """``node`` when it is an object with exactly ``keys``; anything else raises ValueError."""
    if not isinstance(node, dict) or set(node) != set(keys):
        raise ValueError(f"{where}: needs exactly {sorted(keys)}")
    return node


def valid_limit(value, types):
    """True for an unset (None) limit or a positive number of the metric's type; floats must be finite."""
    if value is None:
        return True
    if isinstance(value, bool) or not isinstance(value, types) or value <= 0:
        return False
    return not isinstance(value, float) or math.isfinite(value)


def check_budget(limits):
    """Return ``limits`` when it sets or leaves unset exactly the budgeted limits; anything else raises ValueError."""
    for host in keyed(limits, HOSTS, "budget.limits"):
        for variant in keyed(limits[host], VARIANTS, f"budget.{host}"):
            for stage in keyed(limits[host][variant], BUDGET_STAGES, f"budget.{host}.{variant}"):
                entry = keyed(limits[host][variant][stage], METRICS, f"budget.{host}.{variant}.{stage}")
                for metric, types in METRICS.items():
                    if not valid_limit(entry[metric], types):
                        raise ValueError(f"budget.{host}.{variant}.{stage}.{metric}: must be null or a positive limit")
    return limits


def load_budget(path=BUDGET_FILE):
    document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    if not isinstance(document, dict) or document.get("schema_version") != "canary-budget/v1":
        raise ValueError("budget.schema_version: expected canary-budget/v1")
    return check_budget(document.get("limits"))


def budget_checks(value, budget):
    """(label, actual, limit) for each budgeted stage metric; a None limit is unset."""
    for variant in value["variants"]:
        limits = budget[value["host"]][variant["name"]]
        for stage in BUDGET_STAGES:
            for metric in METRICS:
                yield f"{variant['name']}.{stage}.{metric}", variant["stages"][stage][metric], limits[stage][metric]


def receipt_report(value, budget=None):
    """The validator's verdict: failed assertions, plus each budgeted limit that is still unset."""
    problems = [f"{failure['field']}: {failure['message']}" for failure in json_schema_failures(value, SCHEMA, SCHEMA, "receipt")]
    if problems:
        return {"valid": False, "failed_assertions": problems, "unbudgeted": []}
    if value["trigger"] == "local" and value["release_status_allowed"]:
        problems.append("local.release_status_allowed")
    probe = value["install_probe"]
    if value["host"] == "codex":
        for key in ("headless_install", "skill_expansion"):
            if probe[key] != "passed":
                problems.append(f"install_probe.{key}")
    elif f"speckit-pro@{value['plugin_version']}" not in probe["loaded_plugins"]:
        problems.append("install_probe.loaded_plugins")
    for variant in value["variants"]:
        problems.extend(variant_failures(variant))
    checks = list(budget_checks(value, load_budget() if budget is None else budget))
    problems.extend(f"{label}_budget" for label, actual, limit in checks if limit is not None and actual > limit)
    return {"valid": not problems, "failed_assertions": problems, "unbudgeted": [label for label, _, limit in checks if limit is None]}


def validate_receipt(value, budget=None):
    return receipt_report(value, budget)["failed_assertions"]


def variant_failures(variant):
    failures = []
    conditions = {
        "questions_after_scaffold": variant["questions_after_scaffold"] == 0,
        "unregistered_stops": variant["unregistered_stops"] == 0,
        "planning_end": variant["planning_end"] == "artifacts_and_draft_pr",
        "implement_end": variant["implement_end"] == "ready_for_uat",
        "uat_runbook": bool(variant["uat_runbook"].strip()),
        "verdict": variant["verdict"] == "pass" and not variant["failed_assertions"],
    }
    if variant["name"] == "base":
        conditions.update(umask=variant["umask"] == "077", task_list_calls=variant["task_list_calls"] == 0)
    for key, passed in conditions.items():
        if not passed:
            failures.append(f"{variant['name']}.{key}")
    for name, stage in variant["stages"].items():
        if not math.isfinite(stage["wall_seconds"]):
            failures.append(f"{variant['name']}.{name}.wall_seconds")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    try:
        report = receipt_report(json.loads(args.receipt.read_text(encoding="utf-8"), object_pairs_hook=unique_object))
    except (OSError, ValueError) as exc:
        report = {"valid": False, "failed_assertions": [str(exc)], "unbudgeted": []}
    print(json.dumps(report))
    return int(not report["valid"])


if __name__ == "__main__":
    sys.exit(main())

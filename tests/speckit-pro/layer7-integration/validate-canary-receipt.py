#!/usr/bin/env python3
"""Validate private canary evidence; this command never posts a release status."""

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "speckit-pro"))
from speckit_pro_runner.json_schema import json_schema_failures  # noqa: E402
from speckit_pro_runner.strict_input import unique_object  # noqa: E402

SCHEMA = json.loads(Path(__file__).with_name("canary-receipt.schema.json").read_text(encoding="utf-8"))


def validate_receipt(value):
    problems = [f"{failure['field']}: {failure['message']}" for failure in json_schema_failures(value, SCHEMA, SCHEMA, "receipt")]
    if problems:
        return problems
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
    return problems


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
        if stage["wall_seconds"] > stage["wall_budget_seconds"] or stage["tokens"] > stage["token_budget"]:
            failures.append(f"{variant['name']}.{name}.budget")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    try:
        problems = validate_receipt(json.loads(args.receipt.read_text(encoding="utf-8"), object_pairs_hook=unique_object))
    except (OSError, ValueError) as exc:
        problems = [str(exc)]
    print(json.dumps({"valid": not problems, "failed_assertions": problems}))
    return int(bool(problems))


if __name__ == "__main__":
    sys.exit(main())

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
METRICS = ("wall_seconds", "tokens")
PLANNING_PHASES = frozenset(SCHEMA["$defs"]["plan_quality"]["properties"]["phases_run"]["items"]["enum"])  # ADR 0021
HOOK_EVENTS = ("after_specify", "after_plan", "after_tasks")  # the phases the fixture registers its hooks on
HOOK_KINDS = ("mandatory", "optional")
FIXTURE_TAG = "fixture-v5"  # the fixture tag every release receipt reads against; a new tag re-baselines the budget (ADR 0016)
PLANTED_CATCH_IDS = ("catch-1", "catch-2", "catch-3")  # opaque ids only; ADR 0023 keeps the catches themselves out of public text
MISSING_HOOK_COUNTERS = object()


def closed(properties):
    return {"type": "object", "additionalProperties": False, "required": list(properties), "properties": properties}


# Every host, variant and budgeted stage needs both limits; null leaves a limit unset.
STAGE_LIMITS = closed({"wall_seconds": {"type": ["number", "null"], "exclusiveMinimum": 0},
                       "tokens": {"type": ["integer", "null"], "minimum": 1}})
BUDGET_SCHEMA = closed({
    "schema_version": {"const": "canary-budget/v1"}, "policy": {"type": "string", "minLength": 1},
    "limits": closed({host: closed({variant: closed(dict.fromkeys(BUDGET_STAGES, STAGE_LIMITS)) for variant in VARIANTS})
                      for host in HOSTS}),
})


# The fixture harness's companion receipt (hook-counters/v1); it stays out of the public receipt schema.
HOOK_COUNTERS_SCHEMA = closed({
    "schema_version": {"const": "hook-counters/v1"},
    "hooks": closed({kind: closed({
        "command": {"type": "string", "minLength": 1}, "optional": {"type": "boolean"},
        "fires": {"type": "integer", "minimum": 0}, "unattributed_fires": {"type": "integer", "minimum": 0},
        "phases": closed({event: {"type": "integer", "minimum": 0} for event in HOOK_EVENTS}),
    }) for kind in HOOK_KINDS}),
})


def reject_nonfinite(constant):
    raise ValueError(f"budget: {constant} is not a limit")


def check_budget(document):
    """The limits of a budget document that matches BUDGET_SCHEMA; anything else raises ValueError."""
    for failure in json_schema_failures(document, BUDGET_SCHEMA, BUDGET_SCHEMA, "budget"):
        raise ValueError(f"{failure['field']}: {failure['message']}")
    return document["limits"]


def load_budget(path=BUDGET_FILE):
    return check_budget(json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object,
                                   parse_constant=reject_nonfinite))


def budget_checks(variant, limits):
    """(label, actual, limit) for each budgeted stage metric of one variant entry; a None limit is unset."""
    for stage in BUDGET_STAGES:
        for metric in METRICS:
            yield f"{variant['name']}.{stage}.{metric}", variant["stages"][stage][metric], limits[stage][metric]


def hook_counter_failures(counters):
    """ADR 0023: each registered hook fires exactly once per phase, with no fire left unattributed."""
    schema = [f"hook_counters.{failure['field']}: {failure['message']}"
              for failure in json_schema_failures(counters, HOOK_COUNTERS_SCHEMA, HOOK_COUNTERS_SCHEMA, "hooks")]
    if schema:
        return schema
    failures = []
    for kind, record in counters["hooks"].items():
        failures.extend(f"hook_counters.{kind}.{event}" for event in HOOK_EVENTS if record["phases"][event] != 1)
        if record["optional"] != (kind == "optional"):
            failures.append(f"hook_counters.{kind}.optional")
        if record["fires"] != sum(record["phases"].values()) + record["unattributed_fires"]:
            failures.append(f"hook_counters.{kind}.fires")
        if record["unattributed_fires"]:
            failures.append(f"hook_counters.{kind}.unattributed_fires")
    return failures


def hook_problems(value, hook_counters):
    """A release receipt needs its run's counters; a local one checks them only when given."""
    if hook_counters is not MISSING_HOOK_COUNTERS:
        return hook_counter_failures(hook_counters)
    return ["hook_counters.missing"] if value["trigger"] != "local" else []


def plan_quality_failures(variant):
    """ADR 0023 artifact checks: every item still open at the end of planning must be blocked for UAT and listed."""
    quality, name = variant["plan_quality"], variant["name"]
    failures = []
    if set(quality["phases_run"]) != PLANNING_PHASES:
        failures.append(f"{name}.plan_quality.phases_run")
    if quality["untraced_requirements"]:
        failures.append(f"{name}.plan_quality.untraced_requirements")
    listed = set(quality["blocked_for_uat_listed"])
    if len(listed) > variant["blocked_for_uat"]:
        failures.append(f"{name}.plan_quality.blocked_for_uat_listed")
    for field, label in (("open_gaps", "open_gap"), ("open_findings", "open_finding"),
                         ("open_clarifications", "open_clarification")):
        if not listed.issuperset(quality[field]):
            failures.append(f"{name}.plan_quality.{label}")
    if name == "base":
        failures.extend(planted_catch_failures(quality.get("planted_catches")))
    return failures


def planted_catch_failures(catches):
    """ADR 0023: the base plan must have fixed every planted catch; a missing or unknown record fails closed."""
    if catches is None:
        return ["base.plan_quality.planted_catches"]
    return [f"base.plan_quality.planted_catches.{catch}" for catch in sorted(set(PLANTED_CATCH_IDS) | set(catches))
            if catches.get(catch) != "fixed" or catch not in PLANTED_CATCH_IDS]


def release_failures(value):
    """A release receipt covers all five variants and reads against the pinned fixture tag."""
    if value["trigger"] == "local":
        return []
    return [name for name, ok in (("release.variants", sorted(v["name"] for v in value["variants"]) == sorted(VARIANTS)),
                                  ("release.fixture_tag", value["fixture_tag"] == FIXTURE_TAG)) if not ok]


def receipt_report(value, budget=None, hook_counters=MISSING_HOOK_COUNTERS):
    """Gate failures, separate variant verdicts, and budgeted limits that are still unset."""
    problems = [f"{failure['field']}: {failure['message']}" for failure in json_schema_failures(value, SCHEMA, SCHEMA, "receipt")]
    if problems:
        return {"valid": False, "failed_assertions": problems, "unbudgeted": [], "variants": []}
    if value["trigger"] == "local" and value["release_status_allowed"]:
        problems.append("local.release_status_allowed")
    problems.extend(release_failures(value))
    probe = value["install_probe"]
    if value["host"] == "codex":
        for key in ("headless_install", "skill_expansion"):
            if probe[key] != "passed":
                problems.append(f"install_probe.{key}")
    elif f"speckit-pro@{value['plugin_version']}" not in probe["loaded_plugins"]:
        problems.append("install_probe.loaded_plugins")
    problems.extend(hook_problems(value, hook_counters))
    limits = (load_budget() if budget is None else budget)[value["host"]]
    results, unbudgeted = [], []
    for variant in value["variants"]:
        checks = list(budget_checks(variant, limits[variant["name"]]))
        result = variant_report(variant, checks, value["host"])
        problems.extend(result["gate_failed_assertions"])
        results.append(result)
        unbudgeted.extend(label for label, _, limit in checks if limit is None)
    return {"valid": not problems, "failed_assertions": problems, "variants": results, "unbudgeted": unbudgeted}


def validate_receipt(value, budget=None, hook_counters=MISSING_HOOK_COUNTERS):
    return receipt_report(value, budget, hook_counters)["failed_assertions"]


def stage_tokens(stage, host):
    """Codex stage usage includes the root and every stage-scoped descendant rollout once."""
    if host != "codex":
        return stage["tokens"]
    usage = stage["codex_tokens"]
    return usage["root_tokens"] + sum(usage["child_rollout_tokens"])


def plan_target_report(variant, host):
    """ADR 0023's base-variant target is reported independently of the release budget."""
    if variant["name"] != "base":
        return None
    target = variant["plan_target"]
    plan = {**variant["stages"]["plan"], "tokens": stage_tokens(variant["stages"]["plan"], host)}
    met = all(plan[metric] <= target[f"{metric}_limit"] for metric in METRICS)
    return {**target, "wall_seconds": plan["wall_seconds"], "tokens": plan["tokens"], "target_met": met}


def variant_report(variant, checks, host):
    """One variant entry's assertions and gate result, including its own budget failures."""
    failures = variant_failures(variant) + plan_quality_failures(variant)
    failures.extend(f"{variant['name']}.{name}.tokens_sum" for name, stage in variant["stages"].items()
                    if stage["tokens"] != stage_tokens(stage, host))
    target = plan_target_report(variant, host)
    if target is not None and target["target_met"] != variant["plan_target"]["target_met"]:
        failures.append(f"{variant['name']}.plan_target")
    gate = gate_failures(variant, failures)
    gate.extend(f"{label}_budget" for label, actual, limit in checks if limit is not None and actual > limit)
    return {"name": variant["name"], "verdict": "fail" if failures else "pass",
            "failed_assertions": failures, "gate_verdict": "fail" if gate else "pass",
            "gate_failed_assertions": gate, **({"plan_target": target} if target is not None else {})}


def gate_failures(variant, failures):
    """ADR 0016 accepts only the recorded guard failure, without guarded success claims."""
    expected_red = (
        variant["name"] == "missing_question_guard"
        and variant["verdict"] == "fail"
        and variant["failed_assertions"] == ["question_guard"]
        and variant.get("question_guard") == {
            "gap_recorded": True, "guarded_work_completed": 0, "guarded_work_passed": 0,
        }
    )
    expected = {"missing_question_guard.verdict", "missing_question_guard.question_guard"} if expected_red else set()
    return [failure for failure in failures if failure not in expected]


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
    elif variant["name"] == "oversized_plan":
        conditions.update(split_recommendation_recorded=variant["split_recommendation_recorded"],
                          full_plan_built=variant["full_plan_built"], stops=variant["stops"] == 0)
    elif variant["name"] == "security_interrupt":
        interrupt = variant["security_interrupt"]
        conditions.update(questions_after_scaffold=variant["questions_after_scaffold"] == 1,
                          runner_permit_verified=interrupt["runner_permit_verified"],
                          simulated_responder_answered=interrupt["simulated_responder_answered"],
                          pause_classification=interrupt["pause_classification"] == "authorized")
    elif variant["name"] == "missing_question_guard":
        # This fault-injection variant cannot certify enforcement, even at handoff.
        conditions["question_guard"] = False
    elif variant["name"] == "security_block":
        block = variant["security_block"]
        conditions["security_block"] = (
            block["affected_work"] > 0
            and block["affected_work_blocked_for_uat"] == block["affected_work"]
            and variant["blocked_for_uat"] >= block["affected_work_blocked_for_uat"]
            and block["independent_work"] > 0
            and block["independent_work_completed"] == block["independent_work"]
        )
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
    parser.add_argument("--hook-counters", type=Path, help="the run's hook-counters-receipt.json; required for release triggers")
    args = parser.parse_args()
    try:
        counters = MISSING_HOOK_COUNTERS if args.hook_counters is None else json.loads(
            args.hook_counters.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        report = receipt_report(json.loads(args.receipt.read_text(encoding="utf-8"), object_pairs_hook=unique_object),
                                hook_counters=counters)
    except (OSError, ValueError) as exc:
        report = {"valid": False, "failed_assertions": [str(exc)], "unbudgeted": [], "variants": []}
    print(json.dumps(report))
    return int(not report["valid"])


if __name__ == "__main__":
    sys.exit(main())

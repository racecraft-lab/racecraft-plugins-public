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
PLAN_TARGET_LIMITS = {"wall_seconds": 1800, "tokens": 15000000}  # ADR 0023; reported, never gated
PLANNING_PHASES = frozenset(SCHEMA["$defs"]["plan_quality"]["properties"]["phases_run"]["items"]["enum"])  # ADR 0021
HOOK_EVENTS = ("after_specify", "after_plan", "after_tasks")  # the phases the fixture registers its hooks on
HOOK_KINDS = ("mandatory", "optional")
FIXTURE_TAG = "fixture-v5"  # the fixture tag every release receipt reads against; a new tag re-baselines the budget (ADR 0016)
PLANTED_CATCH_IDS = tuple(SCHEMA["$defs"]["plan_quality"]["properties"]["planted_catches"]["properties"])  # ADR 0023
MAX_PLANTED_CATCH_ENTRIES = len(PLANTED_CATCH_IDS)
MAX_RECEIPT_BYTES = 1024 * 1024  # bounded before JSON parsing, including the companion counters
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
    schema = json_schema_failures(counters, HOOK_COUNTERS_SCHEMA, HOOK_COUNTERS_SCHEMA, "hooks")
    if schema:
        return [f"hook_counters.schema: {len(schema)}"]
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
    return [f"base.plan_quality.planted_catches.{catch}" for catch in PLANTED_CATCH_IDS if catches.get(catch) != "fixed"]


def release_failures(value):
    """A release receipt covers all five variants and reads against the pinned fixture tag."""
    if value["trigger"] == "local":
        return []
    return [name for name, ok in (("release.variants", sorted(v["name"] for v in value["variants"]) == sorted(VARIANTS)),
                                  ("release.fixture_tag", value["fixture_tag"] == FIXTURE_TAG)) if not ok]


def planted_catch_input_failures(value):
    """Bound catch inspection before schema validation can visit or reflect supplied keys."""
    variants = value.get("variants") if isinstance(value, dict) else None
    if not isinstance(variants, list):
        return []
    if len(variants) > len(VARIANTS):
        return [f"receipt.variant_entry_limit: {len(variants)}"]
    unknown = 0
    for variant in variants:
        quality = variant.get("plan_quality") if isinstance(variant, dict) else None
        catches = quality.get("planted_catches") if isinstance(quality, dict) else None
        if not isinstance(catches, dict):
            continue
        if len(catches) > MAX_PLANTED_CATCH_ENTRIES:
            return [f"planted_catches.entry_limit: {len(catches)}"]
        unknown += sum(catch not in PLANTED_CATCH_IDS for catch in catches)
    return [f"unknown planted-catch id: {unknown}"] if unknown else []


def receipt_input_failures(value):
    """Bound planted-catch evidence, then reject non-JSON numbers before any are reported."""
    problems = planted_catch_input_failures(value)
    if not problems:
        try:
            json.dumps(value, allow_nan=False)  # also catches numeric overflow such as JSON 1e400
        except ValueError:
            problems = ["receipt.invalid_json"]
    return problems


def receipt_report(value, budget=None, hook_counters=MISSING_HOOK_COUNTERS):
    """Gate failures, separate variant verdicts, and budgeted limits that are still unset."""
    problems = receipt_input_failures(value)
    if not problems:
        schema = json_schema_failures(value, SCHEMA, SCHEMA, "receipt")
        problems = [f"receipt.schema: {len(schema)}"] if schema else []
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


def plan_target_report(variant, measured_tokens):
    """ADR 0023's base-variant target is reported independently of the release budget."""
    if variant["name"] != "base":
        return None
    plan = variant["stages"]["plan"]
    measured = {"wall_seconds": plan["wall_seconds"], "tokens": measured_tokens}
    met = all(measured[metric] <= limit for metric, limit in PLAN_TARGET_LIMITS.items())
    return {**{f"{metric}_limit": limit for metric, limit in PLAN_TARGET_LIMITS.items()},
            **measured, "target_met": met}


def variant_report(variant, checks, host):
    """One variant entry's assertions and gate result, including its own budget failures."""
    failures = variant_failures(variant) + plan_quality_failures(variant)
    measured_tokens = {name: stage_tokens(stage, host) for name, stage in variant["stages"].items()}
    failures.extend(f"{variant['name']}.{name}.tokens_sum" for name, stage in variant["stages"].items()
                    if stage["tokens"] != measured_tokens[name])
    target = plan_target_report(variant, measured_tokens["plan"])
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
        # ADR 0005: scaffold evaluates and offers both features, then the answers file declines them.
        conditions.update(umask=variant["umask"] == "077", task_list_calls=variant["task_list_calls"] == 0,
                          feature_offers=all(offer == {"evaluated": True, "offered": True, "answer": "declined"}
                                             for offer in variant["feature_offers"].values()))
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


def read_receipt(path):
    """Read at most the byte cap plus one sentinel byte; reject oversized input before parsing."""
    with path.open("rb") as stream:
        body = stream.read(MAX_RECEIPT_BYTES + 1)
    if len(body) > MAX_RECEIPT_BYTES:
        raise OverflowError
    return json.loads(body.decode("utf-8"), object_pairs_hook=unique_object, parse_constant=reject_nonfinite)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--hook-counters", type=Path, help="the run's hook-counters-receipt.json; required for release triggers")
    args = parser.parse_args()
    try:
        counters = MISSING_HOOK_COUNTERS if args.hook_counters is None else read_receipt(args.hook_counters)
        report = receipt_report(read_receipt(args.receipt), hook_counters=counters)
    except (OSError, ValueError, OverflowError, RecursionError) as exc:
        failure = f"input.byte_limit: {MAX_RECEIPT_BYTES}" if isinstance(exc, OverflowError) else "input.invalid"
        report = {"valid": False, "failed_assertions": [failure], "unbudgeted": [], "variants": []}
    print(json.dumps(report, allow_nan=False))
    return int(not report["valid"])


if __name__ == "__main__":
    sys.exit(main())

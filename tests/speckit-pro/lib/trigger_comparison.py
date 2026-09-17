"""Fail-closed, provider-free comparison of independently replayable trigger trials.

Digests bind evidence bytes; they are not signatures or proof of who ran a provider.
Only prospectively retained execution and replay context can qualify a record.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sqlite3
import sys

import trigger_evidence as evidence
from trigger_inventory import canonical_sha256, validate_inventory

ROOT = Path(__file__).resolve().parents[1]
_PARSERS = {}
_DIGEST = re.compile(r"[0-9a-f]{64}")


def json_digest(value: object) -> str:
    json.dumps(value, allow_nan=False)
    return canonical_sha256(value)


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path: Path):
    return json.loads(path.read_bytes(), object_pairs_hook=_unique_pairs)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _digest(value: object) -> bool:
    return isinstance(value, str) and _DIGEST.fullmatch(value) is not None


def _observer_paths() -> list[Path]:
    return sorted([*(ROOT / "lib").glob("*.py"), *(ROOT / "layer2-trigger").glob("*.py")])


def observer_digest() -> str:
    """Pin the public Python harness closure, including wrappers and this verifier."""
    return json_digest({str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in _observer_paths()})


def measurement_snapshot() -> dict:
    """Freeze only public harness/catalog/fixture files, never host credentials."""
    plugin = ROOT.parents[1] / "speckit-pro"
    groups = {
        "observer": _observer_paths(),
        "catalog": sorted(path for folder in ("skills", "codex-skills") for path in (plugin / folder).glob("*/SKILL.md")),
        "fixture": sorted(path for path in (ROOT / "layer2-trigger/fixtures/codex-workspace").rglob("*") if path.is_file()),
    }
    return {name: {str(path.relative_to(ROOT)) if name == "observer" else str(path.relative_to(ROOT.parents[1])): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths} for name, paths in groups.items()}


def snapshot_identities(snapshot: dict) -> dict:
    return {key: json_digest(snapshot[key]) for key in ("observer", "catalog", "fixture")}


def validate_experiment(manifest: dict) -> dict[str, dict]:
    _require(isinstance(manifest, dict) and manifest.get("schema_version") == "trigger-experiment/v1", "unsupported experiment schema")
    _require(isinstance(manifest.get("experiment_id"), str) and bool(manifest["experiment_id"]), "missing experiment identity")
    _require(type(manifest.get("trials")) is int and manifest["trials"] == 3, "exactly three integer trials required")
    _require(type(manifest.get("trial_timeout_seconds")) is int and manifest["trial_timeout_seconds"] > 0,
             "positive integer trial timeout required")
    _require(type(manifest.get("threshold")) is float and manifest["threshold"] == 0.5, "threshold must remain 0.5")
    _require(manifest.get("qualification_scope") in {"full", "pr-core", "pilot"}, "unknown qualification scope")
    _require(manifest.get("arms") in (["baseline", "candidate"], ["candidate"]), "unknown experiment arms")
    roster = manifest.get("roster")
    _require(isinstance(roster, list) and bool(roster), "empty experiment roster")
    cases = {}
    for row in roster:
        _require(isinstance(row, dict) and set(row) == {"case_id", "host", "skill", "query", "should_trigger"}, "malformed roster entry")
        _require(row["host"] in {"claude", "codex"} and isinstance(row["skill"], str) and re.fullmatch(r"[a-z0-9][a-z0-9-]*", row["skill"]) is not None, "invalid host/skill")
        _require(isinstance(row["query"], str) and bool(row["query"]) and type(row["should_trigger"]) is bool, "invalid query or polarity")
        key = evidence.case_id(row["host"], row["skill"], row)
        _require(row["case_id"] == key and key not in cases, "case identity mismatch or duplicate")
        cases[key] = row
    _require(manifest.get("corpus_sha256") == json_digest(roster), "roster digest mismatch")
    _require(_digest(manifest.get("inventory_sha256")), "missing inventory digest")
    hosts = {case["host"] for case in cases.values()}
    pins = manifest.get("pins")
    _require(isinstance(pins, dict) and hosts <= pins.keys(), "missing host pins")
    for host in hosts:
        _require(isinstance(pins[host], dict) and all(isinstance(pins[host].get(name), str) and bool(pins[host][name]) for name in ("model", "cli_version")), "missing model/CLI pin")
    identities = manifest.get("identities")
    _require(isinstance(identities, dict) and all(_digest(identities.get(key)) for key in ("observer", "catalog", "fixture")), "missing observer/catalog/fixture identity")
    delta = manifest.get("controlled_difference")
    _require(isinstance(delta, dict) and isinstance(delta.get("path"), str) and bool(delta["path"]), "missing controlled difference")
    _require(all(_digest(delta.get(key)) for key in ("baseline_sha256", "candidate_sha256")), "missing arm description digests")
    return cases


def artifact_reference(root: Path, path: Path) -> dict:
    resolved = path.resolve(strict=True)
    _require(resolved.is_relative_to(root.resolve()), "artifact escaped evidence root")
    _require(resolved.is_file() and not path.is_symlink(), "artifact is not a regular retained file")
    return {"path": resolved.relative_to(root.resolve()).as_posix(), "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest()}


def read_artifact(root: Path, reference: dict) -> bytes:
    _require(isinstance(reference, dict) and set(reference) == {"path", "sha256"}, "malformed artifact reference")
    relative = reference["path"]
    _require(isinstance(relative, str) and bool(relative) and not Path(relative).is_absolute() and ".." not in Path(relative).parts, "artifact path escaped evidence root")
    path = root / relative
    _require(not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), "artifact symlink escaped evidence root")
    _require(path.is_file(), "artifact must be a regular retained file")
    payload = path.read_bytes()
    _require(_digest(reference["sha256"]) and hashlib.sha256(payload).hexdigest() == reference["sha256"], "artifact digest mismatch")
    return payload


def _artifact_json(root: Path, reference: dict, artifact_reader=read_artifact):
    return json.loads(artifact_reader(root, reference), object_pairs_hook=_unique_pairs)


def _parser(host: str):
    if host not in _PARSERS:
        filename = "run-trigger-evals.py" if host == "claude" else "run_codex_evals.py"
        spec = importlib.util.spec_from_file_location(f"trigger_replay_{host}", ROOT / "layer2-trigger" / filename)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _PARSERS[host] = module
    return _PARSERS[host]


def replay(stdout: bytes, context: dict) -> dict:
    _require(isinstance(context, dict) and context.get("host") in {"claude", "codex"}, "missing native parser replay context")
    host = context["host"]
    parser = _parser(host)
    if host == "claude":
        return parser.inspect_claude_stream(stdout, context["plugin_name"], Path(context["plugin_root"]), context["expected_skill"], context["nonce"], context["requested_model"], frozenset(context["sibling_skills"]))
    return parser.inspect_codex_jsonl(stdout, context["target_skill"], context["witnesses"], requested_model=context["requested_model"])


def compare_hits(positive: bool, baseline: int, candidate: int) -> dict:
    _require(type(positive) is bool and all(type(value) is int and 0 <= value <= 3 for value in (baseline, candidate)), "invalid hit counts")
    return {"baseline_hits": baseline, "candidate_hits": candidate,
            "candidate_pass": (candidate / 3 >= 0.5) == positive,
            "regression": candidate < baseline if positive else candidate > baseline}


def _cleanup_roots(root: Path, references: list, artifact_reader=read_artifact) -> set[str]:
    _require(isinstance(references, list) and bool(references), "missing arm cleanup receipts")
    workspaces = set()
    for reference in references:
        receipt = _artifact_json(root, reference, artifact_reader)
        _require(receipt.get("schema_version") == "trigger-arm-cleanup/v1" and receipt.get("workspace_removed") is True and receipt.get("cleanup_error") is None, "invalid workspace cleanup")
        _require(type(receipt.get("runner_exit_code")) is int and receipt["runner_exit_code"] in (0, 1), "invalid runner exit")
        workspace = receipt.get("workspace")
        _require(isinstance(workspace, str) and Path(workspace).is_absolute(), "missing cleanup ownership")
        _require(workspace not in workspaces, "duplicate cleanup receipt")
        workspaces.add(workspace)
    return workspaces


def _target_binding(context: dict, case: dict) -> None:
    _require(context.get("source_skill") == case["skill"], "replay source skill does not match case")
    target = context.get("expected_skill", "").partition(":")[2] if case["host"] == "claude" else context.get("target_skill")
    _require(isinstance(target, str) and re.fullmatch(re.escape(case["skill"]) + r"-eval-[0-9a-f]+", target) is not None, "native target does not identify the declared source skill")
    if case["host"] == "claude":
        _require(context["expected_skill"] == f"{context['plugin_name']}:{target}", "native target plugin mismatch")
    parser = _parser(case["host"])
    source = parser.find_skill_source(case["skill"])
    sources = {path.name: path / "SKILL.md" for path in parser.sibling_skill_dirs(source)}
    sources[target] = source
    sources[parser.NO_SPECKIT_SKILL_NAME] = None
    bodies = context["staged_skill_bodies"] if case["host"] == "claude" else context["witnesses"]
    _require(isinstance(bodies, dict) and set(bodies) == set(sources), "replay staged catalog does not match frozen source catalog")
    for name, source_path in sources.items():
        body = bodies[name] if case["host"] == "claude" else bodies[name]["body"]
        if case["host"] == "claude":
            description = parser.source_description_lines(source_path) if source_path else [f"description: {context['no_op_description']}"]
            expected_header = f"---\nname: {name}\n" + "\n".join(description) + "\n---\n"
            expected_body = (f"\n{parser.MEASUREMENT_STUB_SENTENCE}\nWhen this skill is selected, reply with this nonce as the first line of your reply:\n\n{context['nonce']}\n\nThen stop: do not invoke any skill again and do not continue the task.\n" if name == target else "\nThis sibling skill is part of a selection check. If it is selected,\nsay so in one line and stop.\n")
            _require(body == expected_header + expected_body, "staged Claude body differs from frozen source stub")
        else:
            witness = bodies[name]
            expected_path = Path(context["workspace"]) / ".agents/skills" / name / "SKILL.md"
            _require(Path(witness["path"]) == expected_path and witness["relative_path"] == f".agents/skills/{name}/SKILL.md", "Codex witness escaped its owned workspace")
            header = re.match(r"^---\n(.*?)\n---\n", source_path.read_text(encoding="utf-8"), re.S).group(1) if source_path else f"name: {name}\ndescription: {context['no_op_description']}"
            if name == target:
                header = "\n".join(f"name: {target}" if line.startswith("name:") else line for line in header.split("\n"))
            _require(body == f"---\n{header}\n---\n\n{parser.selection_stub(witness['marker'])}", "staged Codex body differs from frozen source stub")


def validate_inventory_binding(manifest: dict, inventory: dict) -> dict:
    cases = validate_experiment(manifest)
    validate_inventory(inventory, ROOT / "layer2-trigger")
    active = inventory["active"]
    active_roster = {row["case_id"]: {key: row[key] for key in ("case_id", "host", "skill", "query", "should_trigger")} for row in active}
    _require(all(active_roster.get(key) == row for key, row in cases.items()), "selected roster is not contained in frozen inventory")
    if manifest["qualification_scope"] == "full":
        _require(set(cases) == set(active_roster) and {row["host"] for row in cases.values()} == {"claude", "codex"}, "full qualification requires the entire dual-host inventory")
    return cases


def _validate_trial(root: Path, item: dict, case: dict, manifest: dict, workspaces: set[str],
                    artifact_reader=read_artifact) -> tuple[bool, bool]:
    record = _artifact_json(root, item["record"], artifact_reader)
    context = item["replay_context"]
    _require(record.get("schema_version") == evidence.SCHEMA_VERSION, "unsupported trial schema")
    for key in ("case_id", "host", "skill", "query", "should_trigger"):
        _require(type(record.get(key)) is type(case[key]) and record[key] == case[key], f"trial {key} mismatch")
    _require(type(record.get("trial_number")) is int and record["trial_number"] == item["trial_number"], "trial number mismatch")
    _require(context["host"] == case["host"] and context["requested_model"] == manifest["pins"][case["host"]]["model"], "replay host/model pin mismatch")
    _target_binding(context, case)
    workspace = context.get("plugin_root") if case["host"] == "claude" else context.get("workspace")
    _require(workspace in workspaces, "replay context lacks its owned cleanup receipt")
    parsed = replay(artifact_reader(root, item["stdout"]), context)
    artifact_reader(root, item["stderr"])
    _require(record.get("stdout_sha256", record.get("jsonl_sha256")) == item["stdout"]["sha256"] and record.get("stderr_sha256") == item["stderr"]["sha256"], "raw stream digests disagree with retained trial")
    _require(parsed.get("valid") is True, "native parser rejected trial")
    checks = evidence.trial_checks({**record, **parsed, "stream_valid": parsed["valid"]})
    _require(all(checks.values()), "execution or cleanup validity failed")
    _require(record["launch_contract"].get("query_sha256") == hashlib.sha256(case["query"].encode()).hexdigest(), "native launch query digest mismatch")
    for key in ("selected", "requested_model", "resolved_model", "model_identity_check", "observation_scope"):
        _require(type(record.get(key)) is type(parsed.get(key)) and record.get(key) == parsed.get(key), f"replayed {key} differs from trial summary")
    _require(record.get("valid") is True and record.get("trial_valid") is True and record.get("checks") == checks, "forged trial validity summary")
    _require(type(item.get("selected")) is bool and item["selected"] == parsed["selected"], "forged selected summary")
    return parsed["selected"], record.get("qualification_eligible") is True and parsed.get("qualification_observed") is True


def _replay_options(manifest: dict, options: dict | None):
    if options is None:
        options = {"artifact_reader": read_artifact, "current_observer_sha256": None}
    _require(isinstance(options, dict)
             and set(options) == {"artifact_reader", "current_observer_sha256"}
             and callable(options["artifact_reader"]), "invalid evidence replay options")
    current = snapshot_identities(measurement_snapshot())
    observer = options["current_observer_sha256"]
    if observer is None:
        _require(manifest["identities"] == current,
                 "installed public replay inputs differ from frozen experiment")
        observer = manifest["identities"]["observer"]
    else:
        _require(observer == current["observer"]
                 and {key: manifest["identities"][key] for key in ("catalog", "fixture")}
                 == {key: current[key] for key in ("catalog", "fixture")},
                 "historical replay inputs differ from the reviewed current observer")
    _require(observer == _LOADED_OBSERVER_DIGEST,
             "loaded verifier changed on disk; restart with frozen inputs")
    return options["artifact_reader"]


def _read_arm(manifest: dict, root: Path, index: dict, arm: str, cases: dict,
              options: dict | None = None) -> tuple[dict, bool]:
    _require(isinstance(index, dict) and index.get("schema_version") == "trigger-evidence-index/v1", "unsupported evidence index")
    _require(index.get("experiment_id") == manifest["experiment_id"] and index.get("experiment_sha256") == json_digest(manifest) and index.get("arm") == arm, "evidence experiment/arm mismatch")
    _require(index.get("pins") == manifest["pins"] and index.get("identities") == manifest["identities"], "incompatible experiment pins")
    artifact_reader = _replay_options(manifest, options)
    inventory_ref = index["inventory"]
    _require(inventory_ref["sha256"] == manifest["inventory_sha256"], "inventory binding mismatch")
    inventory = _artifact_json(root, inventory_ref, artifact_reader)
    validate_inventory_binding(manifest, inventory)
    description = artifact_reader(root, index["controlled_description"])
    _require(hashlib.sha256(description).hexdigest() == manifest["controlled_difference"][f"{arm}_sha256"], "controlled arm description mismatch")
    applied_description = description.decode("utf-8").removesuffix("\n")
    _require(bool(applied_description.strip()) and "\n" not in applied_description and "\r" not in applied_description, "invalid controlled description text")
    workspaces = _cleanup_roots(root, index.get("cleanup"), artifact_reader)
    trials = index.get("trials")
    _require(isinstance(trials, list), "missing trial roster")
    expected = {(key, number) for key in cases for number in (1, 2, 3)}
    seen, hits, qualified, native_results = set(), dict.fromkeys(cases, 0), True, {}
    for item in trials:
        _require(isinstance(item, dict) and type(item.get("trial_number")) is int, "malformed trial identity")
        identity = (item.get("case_id"), item["trial_number"])
        _require(identity in expected and identity not in seen, "duplicate or unexpected trial identity")
        seen.add(identity)
        selected, eligible = _validate_trial(root, item, cases[identity[0]], manifest, workspaces, artifact_reader)
        report = _artifact_json(root, item["report"], artifact_reader)
        metadata = report["metadata"]
        _native_preflight(metadata, cases[identity[0]]["host"])
        _require(metadata.get("replay_context") == item["replay_context"], "report replay context mismatch")
        _require(snapshot_identities(metadata["input_snapshot"]) == manifest["identities"], "runtime inputs differ from frozen experiment")
        _require(metadata.get("preflight", {}).get("version") == manifest["pins"][cases[identity[0]]["host"]]["cli_version"], "observed CLI pin mismatch")
        _require(type(metadata.get("trial_timeout_seconds")) is int and metadata["trial_timeout_seconds"] == manifest["trial_timeout_seconds"],
                 "runtime trial timeout differs from frozen experiment")
        _require(metadata.get("no_op_description_sha256") == hashlib.sha256(applied_description.encode()).hexdigest(), "runtime controlled description mismatch")
        _require(item["replay_context"].get("no_op_description") == applied_description, "staged no-op description differs from controlled arm")
        report_results = [row for row in report["results"] if row.get("case_id") == identity[0]]
        _require(all(row.get("case_id") in cases for row in report["results"]), "native report includes an undeclared case")
        _require(len(report_results) == 1, "native report has duplicate or missing case")
        native_results[identity[0]] = report_results[0]
        report_trials = [row for row in report_results[0]["selection_evidence"] if type(row.get("trial_number")) is int and row["trial_number"] == identity[1]]
        _require(len(report_trials) == 1 and report_trials[0].get("trial_record_sha256") == item["record"]["sha256"], "native report trial reference mismatch")
        embedded = {key: value for key, value in report_trials[0].items() if key not in {"trial_record_path", "trial_record_sha256"}}
        _require(json_digest(embedded) == json_digest(
            _artifact_json(root, item["record"], artifact_reader)),
            "embedded native trial differs from retained record")
        _validate_report_summary(
            report, root, index["cleanup"], item["replay_context"], artifact_reader)
        hits[identity[0]] += selected
        qualified = qualified and eligible and report["summary"]["qualification_eligible"] is True
    _require(seen == expected and index.get("complete") is True, "incomplete exact three-trial roster")
    expected_summary = {key: {"target_hits": value, "pass": (value / 3 >= 0.5) == cases[key]["should_trigger"]} for key, value in hits.items()}
    for key, row in native_results.items():
        field = "selected" if cases[key]["host"] == "claude" else "triggers"
        expected_row = evidence.case_result(cases[key]["host"], cases[key]["skill"], cases[key], row["selection_evidence"], 3, 0.5)
        _require(type(row.get(field)) is int and row[field] == hits[key], "native hit count disagrees with replay")
        for name in ("pass", "runs", "executed_runs", "not_run_trials", "invalid_runs", "status", "trigger_rate"):
            _require(type(row.get(name)) is type(expected_row[name]) and row[name] == expected_row[name], f"native {name} summary mismatch")
    _require(json_digest(index.get("summary")) == json_digest(expected_summary), "aggregate summary disagrees with independently replayed trials")
    return hits, qualified


def _native_preflight(metadata: dict, host: str) -> None:
    preflight = metadata["preflight"]
    if host == "claude":
        _require(type(preflight.get("request_retries")) is int and preflight["request_retries"] == 0 and preflight.get("settings_sources") == [], "Claude preflight did not prove isolated zero-retry configuration")
        for name in ("doctor_checks", "managed_checks"):
            _require(isinstance(preflight.get(name), dict) and bool(preflight[name]) and all(value is True for value in preflight[name].values()), "Claude preflight qualification failed")
        return
    _require(all(type(preflight.get(key)) is int and preflight[key] == 0 for key in ("request_max_retries", "stream_max_retries")) and preflight.get("unbounded_connection_retries") is False, "Codex preflight did not prove zero retries")
    catalog = metadata["catalog_preflight"]
    _require(all(catalog.get(key) is True for key in ("sibling_entries_exact", "target_description_exact", "target_file_exact", "source_locators_exact")) and catalog.get("warning_present") is False, "Codex catalog qualification failed")
    _require(type(catalog.get("target_entries")) is int and catalog["target_entries"] == 1, "Codex catalog target inventory mismatch")


def _validate_report_summary(report: dict, root: Path, cleanup: list, context: dict,
                             artifact_reader=read_artifact) -> None:
    results, summary = report["results"], report["summary"]
    _require(len({row["case_id"] for row in results}) == len(results), "native report has duplicate cases")
    passed = sum(row["pass"] is True for row in results)
    failed = sum(row["pass"] is False for row in results)
    expected = {"total": len(results), "passed": passed, "failed": failed, "complete": all(row["status"] == "complete" for row in results), "not_run": sum(row["status"] == "not_run" for row in results), "requested_model": context["requested_model"]}
    for key, value in expected.items():
        _require(type(summary.get(key)) is type(value) and summary[key] == value, f"native report {key} aggregate mismatch")
    for result in results:
        ordinals = [trial.get("trial_number") for trial in result["selection_evidence"]]
        _require(all(type(number) is int for number in ordinals) and sorted(ordinals) == [1, 2, 3], "native report includes missing or extra trials")
    _require(type(summary.get("qualification_eligible")) is bool, "missing native qualification status")
    if summary["qualification_eligible"]:
        _require(expected["complete"] and all(row.get("qualification_eligible") is True for result in results for row in result["selection_evidence"]), "forged native qualification summary")
    workspace = context.get("plugin_root", context.get("workspace"))
    receipts = [_artifact_json(root, reference, artifact_reader) for reference in cleanup]
    owned = [receipt for receipt in receipts if receipt["workspace"] == workspace]
    _require(len(owned) == 1 and owned[0]["runner_exit_code"] == (1 if failed else 0), "runner exit disagrees with complete native report")


def build_evidence_index(manifest: dict, arm: str, root: Path, reports: list[Path], inventory: Path,
                         description: Path) -> dict:
    """Index prospective native outputs after cleanup; do not invent missing context."""
    cases = validate_experiment(manifest)
    _require(arm in manifest["arms"], "arm not in approved experiment")
    trials, cleanup, summary = [], [], {}
    for report_path in reports:
        report = read_json(report_path)
        context = report["metadata"]["replay_context"]
        report_ref = artifact_reference(root, report_path)
        for result in report["results"]:
            key = result["case_id"]
            _require(key in cases and key not in summary, "duplicate or unexpected report case")
            summary[key] = {"target_hits": result.get("selected", result.get("triggers")), "pass": result["pass"]}
            for record in result["selection_evidence"]:
                record_path = Path(record["trial_record_path"])
                stdout_path = Path(record.get("stdout_path", record.get("jsonl_path")))
                trials.append({"case_id": key, "trial_number": record["trial_number"], "selected": record["selected"],
                    "record": artifact_reference(root, record_path), "stdout": artifact_reference(root, stdout_path),
                    "stderr": artifact_reference(root, Path(record["stderr_path"])), "report": report_ref, "replay_context": context})
                cleanup_ref = artifact_reference(root, record_path.parent / "arm-cleanup.json")
                if cleanup_ref not in cleanup:
                    cleanup.append(cleanup_ref)
    index = {"schema_version": "trigger-evidence-index/v1", "experiment_id": manifest["experiment_id"],
        "experiment_sha256": json_digest(manifest), "arm": arm, "pins": manifest["pins"], "identities": manifest["identities"],
        "inventory": artifact_reference(root, inventory), "controlled_description": artifact_reference(root, description),
        "trials": trials, "cleanup": cleanup, "summary": summary, "complete": len(trials) == len(cases) * 3}
    _read_arm(manifest, root, index, arm, cases)
    return index


def _read_source_aware_arm(manifest: dict, root: Path, index: dict,
                           cases: dict) -> tuple[dict, bool, dict[str, set]]:
    """Validate carried lineage again and replay only fresh bytes from the new root."""
    import trigger_carry_forward as carry
    from trigger_campaign import read_ledger, validate_approval
    approval = read_json(root / "approval.json")
    validate_approval(approval, json_digest(manifest), 891, carry_forward=index.get("carry_forward"))
    plan = carry.validate_carry_forward(index.get("carry_forward"), manifest, json_digest(manifest),
                                        approval=approval)
    carried, fresh = carry.source_aware_union(index, manifest, "baseline")
    _require(carried["root"] == str(plan.source_root)
             and carried["manifest"] == plan.partial_manifest
             and carried["index"] == plan.source_index
             and carried["case_ids"] == list(plan.carried_case_ids)
             and fresh["case_ids"] == list(plan.fresh_case_ids),
             "source-aware index differs from its revalidated immutable lineage")
    fresh_manifest = fresh["manifest"]
    _require(fresh_manifest == carry.fresh_partial_manifest(manifest, plan.fresh_case_ids),
             "fresh source manifest is not the deterministic approved complement")
    fresh_cases = validate_experiment(fresh_manifest)
    _require(set(fresh_cases) == set(plan.fresh_case_ids)
             and fresh_manifest["qualification_scope"] == "pr-core"
             and fresh_manifest["identities"] == manifest["identities"],
             "fresh source manifest differs from the exact complement")
    ledger_path, snapshot_path = root / "ledger.sqlite3", root / "ledger.json"
    _require(ledger_path.is_file() and not ledger_path.is_symlink()
             and snapshot_path.is_file() and not snapshot_path.is_symlink(),
             "source-aware comparison requires immutable completed fresh ledger evidence")
    try:
        authorization, ledger = read_ledger(ledger_path)
    except (sqlite3.Error, TypeError, IndexError, KeyError,
            json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError(f"fresh ledger evidence is unreadable: {exc}") from None
    _require(authorization == {
                "manifest_sha256": json_digest(manifest),
                "approval_sha256": json_digest(approval),
                "launch_budget": 891,
                "carry_forward_sha256": plan.component_sha256,
             }
             and read_json(snapshot_path) == ledger
             and ledger["launch_budget"] == 891
             and ledger["reserved_launches"] == 891
             and ledger["unknown_launches"] == 0,
             "fresh ledger authorization or completed snapshot changed")
    carry.validate_fresh_ledger(plan, ledger["launches"], complete=True)
    fresh_hits, fresh_qualified = _read_arm(fresh_manifest, root, fresh["index"], "baseline", fresh_cases)
    carried_hits = {case_id: plan.source_index["summary"][case_id]["target_hits"]
                    for case_id in plan.carried_case_ids}
    _require(set(carried_hits).isdisjoint(fresh_hits)
             and set(carried_hits) | set(fresh_hits) == set(cases),
             "carried and fresh baseline sources are not an exact disjoint case union")
    models = {host: set(values) for host, values in plan.carried_models.items()}
    for host, values in _resolved_models(root, fresh["index"]).items():
        models.setdefault(host, set()).update(values)
    return {case_id: (carried_hits | fresh_hits)[case_id] for case_id in cases}, fresh_qualified, models


def _read_multi_source_arm(manifest: dict, root: Path, index: dict, expected_arm: str,
                           cases: dict) -> tuple[dict, bool, dict[str, set]]:
    """Re-admit every physical history and replay one logical V3 evidence arm."""
    import trigger_carry_forward as carry
    from trigger_campaign import read_ledger, validate_approval
    _require(isinstance(index, dict)
             and index.get("schema_version") == carry.MULTI_SOURCE_INDEX_SCHEMA_VERSION
             and index.get("arm") == expected_arm,
             "multi-source evidence index is in the wrong comparison arm slot")
    request_manifest = read_json(root / "manifest.json")
    approval = read_json(root / "approval.json")
    component = index.get("carry_forward")
    budget = approval.get("launch_budget")
    validate_approval(approval, json_digest(request_manifest), budget,
                      carry_forward=component)
    plan = carry.validate_multi_generation_carry_forward(
        component, request_manifest, json_digest(request_manifest), approval=approval)
    _require(plan.logical_manifest == manifest,
             "multi-source comparison manifest differs from the reviewed logical union")
    historical, fresh = carry.multi_source_union(index, plan, expected_arm)
    ledger_path, snapshot_path = root / "ledger.sqlite3", root / "ledger.json"
    _require(ledger_path.is_file() and not ledger_path.is_symlink()
             and snapshot_path.is_file() and not snapshot_path.is_symlink(),
             "multi-source comparison requires immutable completed fresh ledger evidence")
    try:
        authorization, ledger = read_ledger(ledger_path)
    except (sqlite3.Error, TypeError, IndexError, KeyError,
            json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError(f"fresh ledger evidence is unreadable: {exc}") from None
    _require(authorization == {
                "manifest_sha256": json_digest(request_manifest),
                "approval_sha256": json_digest(approval),
                "launch_budget": plan.fresh_launch_ceiling,
                "carry_forward_sha256": plan.component_sha256,
             }
             and read_json(snapshot_path) == ledger
             and ledger["launch_budget"] == plan.fresh_launch_ceiling
             and ledger["reserved_launches"] == plan.fresh_launch_ceiling
             and ledger["unknown_launches"] == 0,
             "fresh ledger authorization or completed snapshot changed")
    carry.validate_fresh_ledger(plan, ledger["launches"], complete=True)
    hits: dict[str, int] = {}
    models: dict[str, set] = {}
    source_lookup = {(source.generation_id, source.arm): source for source in plan.sources}
    for descriptor in historical:
        source = source_lookup.get((descriptor["generation_id"], expected_arm))
        _require(source is not None and descriptor["root"] == str(source.root)
                 and descriptor["manifest"] == source.manifest
                 and descriptor["index"] == source.index
                 and descriptor["case_ids"] == list(source.case_ids),
                 "multi-source historical descriptor differs from its revalidated source")
        for case_id in source.case_ids:
            hits[case_id] = source.index["summary"][case_id]["target_hits"]
        for host, values in source.models.items():
            models.setdefault(host, set()).update(values)
    qualified = True
    if fresh is not None:
        fresh_cases = validate_experiment(fresh["manifest"])
        fresh_hits, qualified = _read_arm(
            fresh["manifest"], root, fresh["index"], expected_arm, fresh_cases)
        _require(set(hits).isdisjoint(fresh_hits),
                 "multi-source fresh evidence overlaps historical valid coverage")
        hits.update(fresh_hits)
        for host, values in _resolved_models(root, fresh["index"]).items():
            models.setdefault(host, set()).update(values)
    _require(set(hits) == set(cases),
             "multi-source evidence does not form the exact logical arm roster")
    return {case_id: hits[case_id] for case_id in cases}, qualified, models


def compare_evidence(manifest: dict, root: Path, baseline: dict, candidate: dict) -> dict:
    result = {"schema_version": "trigger-comparison/v1", "complete": False, "valid": False,
              "candidate_pass": None, "regression": None, "qualification": False, "exit_code": 2, "cases": []}
    try:
        cases = validate_experiment(manifest)
        _require(manifest["arms"] == ["baseline", "candidate"], "comparison requires both arms")
        if baseline.get("schema_version") == "trigger-evidence-index/v3":
            before, baseline_qualified, baseline_models = _read_multi_source_arm(
                manifest, root, baseline, "baseline", cases,
            )
        elif baseline.get("schema_version") == "trigger-evidence-index/v2":
            before, baseline_qualified, baseline_models = _read_source_aware_arm(
                manifest, root, baseline, cases,
            )
        else:
            before, baseline_qualified = _read_arm(manifest, root, baseline, "baseline", cases)
            baseline_models = _resolved_models(root, baseline)
        if candidate.get("schema_version") == "trigger-evidence-index/v3":
            after, candidate_qualified, candidate_models = _read_multi_source_arm(
                manifest, root, candidate, "candidate", cases,
            )
        else:
            after, candidate_qualified = _read_arm(manifest, root, candidate, "candidate", cases)
            candidate_models = _resolved_models(root, candidate)
        _require(baseline_models == candidate_models, "observed provider model identities changed between arms")
        _require(all(len(models) == 1 for models in baseline_models.values()), "ambiguous resolved model identity within one host")
        rows = [{"case_id": key, **compare_hits(case["should_trigger"], before[key], after[key])} for key, case in cases.items()]
        passed = all(row["candidate_pass"] for row in rows)
        regression = any(row["regression"] for row in rows)
        result.update(complete=True, valid=True, candidate_pass=passed, regression=regression, cases=rows,
                      qualification=manifest["qualification_scope"] == "full" and baseline_qualified and candidate_qualified,
                      qualification_scope=manifest["qualification_scope"], exit_code=0 if passed and not regression else 1)
        result["observed_models"] = {host: list(models) for host, models in candidate_models.items()}
        if any(None in models for models in candidate_models.values()):
            result["model_identity_limitations"] = ["Codex requested-only identity pins the isolated launch argument; the backend resolved model was not reported."]
        if not baseline_qualified or not candidate_qualified:
            result["qualification_limitations"] = ["Native qualification or observed resolved-model identity is incomplete."]
            if manifest["qualification_scope"] == "full":
                result["exit_code"] = 2
    except (ValueError, TypeError, KeyError, OSError, UnicodeError, AttributeError) as exc:
        result["error"] = str(exc)
    return result


def _resolved_models(root: Path, index: dict, artifact_reader=read_artifact) -> dict[str, set]:
    models = {}
    for trial in index["trials"]:
        record = _artifact_json(root, trial["record"], artifact_reader)
        models.setdefault(record["host"], set()).add(record.get("resolved_model"))
    return models


_LOADED_OBSERVER_DIGEST = observer_digest()

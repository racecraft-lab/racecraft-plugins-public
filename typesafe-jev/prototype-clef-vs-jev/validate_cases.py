#!/usr/bin/env python3
"""Offline evidence and shape checks; strict counts unless explicitly waived."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def validate(allow_missing_infra):
    document = read("cases.json")
    cases = document["cases"]
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    prs = {p["number"]: p for p in read("raw/prs.json")}
    runs = read("raw/runs.json") + read("raw/failed_runs.json") + read("raw/success_runs.json")
    logs = read("raw/failed_logs.json")
    flaky = read("raw/flaky_logs.json")
    check(len({c["id"] for c in cases}) == len(cases), "duplicate case ids")
    counts = Counter(c["question"] for c in cases)
    mixes = {q: Counter(c["expect"] for c in cases if c["question"] == q)
             for q in ("pr_ready", "failure_real")}
    check(counts["pr_ready"] == 7 and counts["owner"] == 6, "PR/owner counts must be 7/6")
    check(mixes["pr_ready"] == {True: 4, False: 3}, "PR mix must be 4 true/3 false")
    infra = [c for c in cases if c["question"] == "failure_real" and "evidence_line" in c]
    target_failures = 5 + len(infra) if allow_missing_infra else 7
    check(counts["failure_real"] == target_failures, f"failure count must be {target_failures}; got {counts['failure_real']}")
    check(len(cases) == 13 + target_failures, f"total must be {13 + target_failures}; got {len(cases)}")
    check(mixes["failure_real"] == {True: 4, False: target_failures - 4}, "failure label mix mismatch")
    check(len(infra) <= 2 if allow_missing_infra else len(infra) == 2, "need 2 qualifying infrastructure cases")
    if allow_missing_infra:
        check("Infrastructure shortfall" in " ".join(document["limitations"]), "missing shortfall disclosure")

    spec = importlib.util.spec_from_file_location("prototype_run", ROOT / "run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    sensitive = re.compile(
        r"/(?:Users|home)/|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|"
        r"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b|"
        r"\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{16,})\b"
    )
    max_tokens = 0
    for c in cases:
        tag = c["id"]
        check(bool(c.get("source", {}).get("ref")) and bool(c.get("label_rule")), f"{tag}: missing provenance")
        check(c["question"] in document["questions"], f"{tag}: unknown question")
        check(not sensitive.search(json.dumps(c)), f"{tag}: privacy pattern")
        state = json.dumps(c["state"], ensure_ascii=False)
        tokens = (len(state) + 3) // 4
        max_tokens = max(max_tokens, tokens)
        check(tokens <= 2000, f"{tag}: state exceeds ~2000 tokens")
        check(not re.search(r'"(?:expect|label_rule|source|evidence_line|mergedAt|closedAt|isDraft|conclusion|final|successful_attempt)"\s*:', state), f"{tag}: outcome/provenance in state")
        request = runner.request_for(document, c)
        check(set(request) == {"state", "questions"} and request["state"] == c["state"], f"{tag}: request isolation")
        if c["question"] == "pr_ready":
            raw = prs[c["source"]["ref"]]
            check(type(c["expect"]) is bool and c["expect"] == (bool(raw["mergedAt"]) and not raw["isDraft"]), f"{tag}: readiness evidence")
            check(c["expect"] or raw["state"] == "CLOSED" or raw["isDraft"], f"{tag}: negative PR evidence")
            check(set(c["state"]["pr"]) == {"title", "body", "reviews", "checks"}, f"{tag}: PR state fields")
            check(not re.search(r"\b(?:supersed\w*|clos(?:ing|ed|es)|replaced by|merged|unmerged)\b", state, re.I), f"{tag}: PR outcome text")
            check(c["state"]["pr"]["reviews"] == [{"state": r["state"], "body": r["body"]} for r in raw["reviews"]], f"{tag}: reviews lost")
        elif c["question"] == "failure_real":
            ref = c["source"]["ref"]
            check(type(c["expect"]) is bool, f"{tag}: expected boolean")
            if c["expect"]:
                matches = [r for r in runs if r["databaseId"] == ref and r["conclusion"] == "failure"]
                check(bool(matches) and bool(logs.get(str(ref))), f"{tag}: missing failed run/log")
                for r in matches:
                    check(not any(s["conclusion"] == "success" and (s["name"], s["headSha"]) == (r["name"], r["headSha"]) for s in runs), f"{tag}: workflow/SHA succeeded")
                check(bool(re.search(r"AssertionError|validation_failed|composition_failed|\[ERROR\] \[check\]", c["state"]["failure"]["log"])), f"{tag}: no test/assertion/validation failure")
            elif "evidence_line" not in c:
                raw = flaky[str(ref)]
                check(raw["attempt_failed"] == 1 and raw["final"] == "success", f"{tag}: flaky source")
                check(any(r["databaseId"] == ref and r["attempt"] > 1 and r["conclusion"] == "success" and r["headSha"] == raw["headSha"] and r["name"] == raw["name"] for r in runs), f"{tag}: same run rerun evidence")
                check(c["label_rule"] == "rerun of the same run turned green", f"{tag}: flaky rule")
            else:
                check("infra-text rule; owner to check" in c["label_rule"], f"{tag}: infra rule")
                check(any(c["evidence_line"] in line for line in logs[str(ref)]), f"{tag}: infrastructure quote absent from source")
                check(c["evidence_line"] in c["state"]["failure"]["log"], f"{tag}: infrastructure quote absent from state")
        else:
            check(c["expect"] in document["questions"]["owner"]["criteria"], f"{tag}: unknown owner")

    owners = [c for c in cases if c["question"] == "owner"]
    check(hashlib.sha256(json.dumps(owners, sort_keys=True).encode()).hexdigest() == "202a25fbb3a3997bdb4be92eb3d1c33379257257c82cabfbacfa5614994838f8", "owner cases changed")
    check(hashlib.sha256((ROOT / "run.py").read_bytes()).hexdigest() == "4e43dad0e2be2b1cac72dd572468248cbbb41ddbc482cba233af4a4cc5c637c8", "run.py changed")
    print(f"Counts: {dict(counts)}; PR mix: {dict(mixes['pr_ready'])}; failure mix: {dict(mixes['failure_real'])}; infra: {len(infra)}/2")
    print(f"Maximum state estimate: {max_tokens} tokens (chars/4).")
    for error in errors:
        print("FAIL:", error)
    print("FAIL" if errors else "PASS (infrastructure shortfall explicitly allowed)" if allow_missing_infra else "PASS")
    return 1 if errors else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-missing-infra", action="store_true")
    args = parser.parse_args()
    sys.exit(validate(args.allow_missing_infra))

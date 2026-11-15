#!/usr/bin/env python3
"""THROWAWAY comparison; dry run unless --execute --budget-usd is explicit."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
# USD per million INPUT tokens only. These are planning estimates, not quotes.
BACKENDS = {
    "typesafe-jev": ("typesafe", "jev-latest", 0.04),
    "openrouter-jev": ("openrouter", None, 0.04),
    "openrouter-clef-flash": ("openrouter", "cloudflare/clef-flash", 0.038),
    "ollama-clef": (None, "clef:cloud", 0.24),
    # Same fresh-connection cost per call as the evaluate columns, without the process start.
    "ollama-clef-direct": (None, "clef", 0.24),
}
OLLAMA_KEY_FILE = Path.home() / ".config" / "racecraft-jev" / "ollama.key"


def request_for(document: dict, case: dict) -> dict:
    """Outcome and provenance deliberately never enter an inference request."""
    return {"state": case["state"], "questions": {"q": document["questions"][case["question"]]}}


def input_estimate(request: dict, backend: str) -> int:
    model = BACKENDS[backend][1]
    body = dict(request)
    if model:
        body["model"] = model
    return math.ceil(len(json.dumps(body, ensure_ascii=False)) / 4)


def estimated_cost(request: dict, backend: str) -> float:
    return input_estimate(request, backend) * BACKENDS[backend][2] / 1_000_000


def backend_env(backend: str) -> dict[str, str]:
    provider, model, _ = BACKENDS[backend]
    env = os.environ.copy()
    for name in ("JEV_FALLBACK_PROVIDER", "JEV_FALLBACK_API_KEY_FILE", "JEV_MODEL"):
        env.pop(name, None)
    env["JEV_PROVIDER"] = str(provider)
    env["JEV_MAX_RETRIES"] = "0"
    if model:
        env["JEV_MODEL"] = model
    return env


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "redirect refused", headers, fp)


def invoke(backend: str, request: dict, evaluate: str, timeout: float) -> dict:
    started = time.perf_counter()
    record = {"exit_code": None, "http_status": None, "stdout": "", "stderr": ""}
    try:
        if backend in ("ollama-clef", "ollama-clef-direct"):
            direct = backend == "ollama-clef-direct"
            body = dict(request, model=BACKENDS[backend][1])
            headers = {"Content-Type": "application/json"}
            if direct:
                headers["Authorization"] = "Bearer " + OLLAMA_KEY_FILE.read_text().strip()
            req = urllib.request.Request(
                "https://ollama.com/v1/systemone" if direct else "http://localhost:11434/v1/systemone",
                data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                headers=headers, method="POST",
            )
            # urllib opens a new connection (and TLS handshake for direct) on every call.
            # Localhost must stay local even when the parent uses HTTP proxies.
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
            with opener.open(req, timeout=timeout) as response:
                record["http_status"] = response.status
                record["stdout"] = response.read().decode("utf-8", errors="replace")
            record["exit_code"] = 0  # normalized HTTP success; there is no child process
        else:
            result = subprocess.run(
                [evaluate, "call", "--plugin-defaults"],
                input=json.dumps(request, ensure_ascii=False),
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=backend_env(backend), timeout=timeout, check=False,
            )
            record.update(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
    except urllib.error.HTTPError as exc:
        record.update(exit_code=1, http_status=exc.code,
                      stdout=exc.read().decode("utf-8", errors="replace"), stderr=str(exc))
    except subprocess.TimeoutExpired as exc:
        def as_text(value):
            return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""
        record.update(exit_code=124, stdout=as_text(exc.stdout),
                      stderr=as_text(exc.stderr) + "\nsubprocess timeout")
    except (OSError, urllib.error.URLError) as exc:
        record.update(exit_code=-1, stderr=str(exc))
    record["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
    try:
        record["response"] = json.loads(record["stdout"])
    except ValueError:
        record["response"] = None
    return record


def finite_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def extract(record: dict, question: dict, request: dict, backend: str) -> dict:
    response = record["response"]
    response = response if isinstance(response, dict) else {}
    usage = response.get("usage")
    usage = usage if isinstance(usage, dict) else {}
    answers = response.get("answers")
    answer = answers.get("q") if isinstance(answers, dict) else None
    prediction = None
    if record["exit_code"] == 0 and isinstance(answer, dict) and answer.get("type") == question["type"]:
        if question["type"] == "noul":
            value = answer.get("noul")
            if finite_number(value) and 0 <= value <= 1:
                prediction = value >= 0.5
        elif question["type"] == "choice" and answer.get("choice") in question["criteria"]:
            prediction = answer["choice"]
    reported_cost = next((value for value in (usage.get("cost"), response.get("cost"))
                          if finite_number(value) and value >= 0), None)
    token_total = usage.get("total_tokens")
    if not (finite_number(token_total) and token_total >= 0):
        inp = usage.get("input_tokens", usage.get("prompt_tokens"))
        out = usage.get("output_tokens", usage.get("completion_tokens"))
        token_total = inp + out if all(finite_number(v) and v >= 0 for v in (inp, out)) else None
    return {
        "answer": answer, "prediction": prediction, "reported_model": response.get("model"),
        "usage": usage, "reported_cost_usd": reported_cost,
        "estimated_input_tokens": input_estimate(request, backend),
        "reported_total_tokens": token_total,
        "cost_usd": reported_cost if reported_cost is not None else estimated_cost(request, backend),
        "cost_basis": "reported" if reported_cost is not None else "estimated_input_only",
        "valid_answer": prediction is not None,
    }


def answer_text(record: dict | None) -> str:
    if record is None:
        return "not run"
    answer = record["answer"]
    if not record["valid_answer"]:
        return f"ERROR/refusal (exit {record['exit_code']}) / {record['latency_ms']:.1f} ms"
    if "noul" in answer:
        label = f"{answer['noul']:.3f}"
    else:
        label = answer["choice"]
        probabilities = answer.get("probabilities")
        probability = probabilities.get(label) if isinstance(probabilities, dict) else None
        if finite_number(probability):
            label += f" p={probability:.3f}"
    if finite_number(answer.get("confidence")):
        label += f" c={answer['confidence']:.3f}"
    return f"{label} / {record['latency_ms']:.1f} ms"


def summarize(rows: list[dict]) -> dict:
    summary = {}
    for backend in BACKENDS:
        records = [row["backends"][backend] for row in rows if backend in row["backends"]]
        valid = [r for r in records if r["valid_answer"]]
        latencies = sorted(r["latency_ms"] for r in valid)
        comparable = [(row["backends"].get(backend), row["backends"].get("typesafe-jev")) for row in rows]
        pairs = [(a, b) for a, b in comparable if a and b and a["valid_answer"] and b["valid_answer"]]
        correct = sum(row["backends"][backend]["prediction"] == row["expect"]
                      for row in rows if backend in row["backends"] and row["backends"][backend]["valid_answer"])
        summary[backend] = {
            "attempted": len(records), "valid_answers": len(valid), "errors_or_refusals": len(records) - len(valid),
            "agreement_with_expect": {"agree": correct, "compared": len(valid)},
            "agreement_with_typesafe_jev": {"agree": sum(a["prediction"] == b["prediction"] for a, b in pairs), "compared": len(pairs)},
            "median_latency_ms": statistics.median(latencies) if latencies else None,
            "p90_latency_ms": latencies[math.ceil(0.9 * len(latencies)) - 1] if latencies else None,
            "reported_total_tokens": sum(r["reported_total_tokens"] for r in records if r["reported_total_tokens"] is not None),
            "requests_missing_token_usage": sum(r["reported_total_tokens"] is None for r in records),
            "estimated_input_tokens_when_usage_missing": sum(r["estimated_input_tokens"] for r in records if r["reported_total_tokens"] is None),
            "total_cost_usd": sum(r["cost_usd"] for r in records),
            "requests_with_estimated_cost": sum(r["cost_basis"] != "reported" for r in records),
        }
    return summary


def display(rows: list[dict], summary: dict) -> None:
    print("\n| id | expect | " + " | ".join(BACKENDS) + " |")
    print("|---|---|" + "---|" * len(BACKENDS))
    for row in rows:
        print(f"| {row['id']} | {json.dumps(row['expect'])} | " + " | ".join(answer_text(row["backends"].get(b)) for b in BACKENDS) + " |")
    print("\nAgreement uses noul >= 0.5 or returned top choice; errors/refusals are excluded and counted separately.")
    print("Latency uses valid answers only; p90 is nearest rank. Tokens below are reported totals; missing usage is shown separately.")
    print("| backend | expect | vs typesafe-jev | errors | median ms | p90 ms | tokens | cost USD |")
    print("|---|---|---|---|---|---|---|---|")
    for backend, s in summary.items():
        def ratio(key):
            a = s[key]
            return f"{a['agree']}/{a['compared']}"
        def milliseconds(key):
            return f"{s[key]:.1f}" if s[key] is not None else "n/a"
        print(f"| {backend} | {ratio('agreement_with_expect')} | {ratio('agreement_with_typesafe_jev')} | {s['errors_or_refusals']} | {milliseconds('median_latency_ms')} | {milliseconds('p90_latency_ms')} | {s['reported_total_tokens']} | ${s['total_cost_usd']:.8f} |")
        if s["requests_with_estimated_cost"] or s["requests_missing_token_usage"]:
            print(f"  {backend}: cost estimated for {s['requests_with_estimated_cost']} requests; usage missing for {s['requests_missing_token_usage']} (estimated input tokens: {s['estimated_input_tokens_when_usage_missing']}).")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="send sequential requests (billable)")
    parser.add_argument("--budget-usd", type=float)
    parser.add_argument("--evaluate", help="path to the parent-built evaluate binary; required to execute")
    parser.add_argument("--timeout", type=float, default=120, help="seconds per request, default 120")
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be finite and positive")
    if args.budget_usd is not None and (not math.isfinite(args.budget_usd) or args.budget_usd <= 0):
        parser.error("--budget-usd must be finite and positive")
    if args.execute and (not args.evaluate or args.budget_usd is None):
        parser.error("--execute requires --evaluate and --budget-usd")
    document = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    cases = document["cases"]
    if not cases:
        parser.error("cases.json has no supported cases")
    requests = [request_for(document, case) for case in cases]
    print("PROTOTYPE: labels come from repository history; this is a throwaway comparison.")
    if document.get("limitations"):
        for limitation in document["limitations"]:
            print("Dataset limitation:", limitation)
    print(f"Plan: {len(cases)} cases x {len(BACKENDS)} backends = {len(cases) * len(BACKENDS)} requests; sequential, one question each.")
    total_estimate = 0.0
    total_input = 0
    for backend in BACKENDS:
        tokens = sum(input_estimate(r, backend) for r in requests)
        cost = sum(estimated_cost(r, backend) for r in requests)
        total_estimate += cost
        total_input += tokens
        print(f"  {backend}: ~{tokens:,} input tokens; ~${cost:.8f} at ${BACKENDS[backend][2]:.3f}/million input tokens (estimate)")
    print(f"Estimated total: ~{total_input:,} input tokens (chars/4), ~${total_estimate:.8f} USD.")
    print("Input-only estimates: Jev ~$0.04/M from earlier runs; OpenRouter clef-flash ~$0.038/M Cloudflare rate; Clef ~$0.24/M. Output tokens, billing overhead, and current provider rates may differ.")
    if not args.execute:
        print("DRY RUN: no subprocess or HTTP request sent. Use --execute --evaluate PATH --budget-usd X to send.")
        return 0
    if total_estimate > args.budget_usd:
        parser.error(f"estimated cost ${total_estimate:.8f} exceeds budget ${args.budget_usd:.8f}; no requests sent")
    evaluate = Path(args.evaluate).expanduser().resolve()
    if not evaluate.is_file() or not os.access(evaluate, os.X_OK):
        parser.error("--evaluate must name an existing executable file")
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    output = ROOT / "results" / f"run-{timestamp}.json"
    output.parent.mkdir(exist_ok=True)
    report = {"prototype": True, "timestamp_utc": timestamp, "budget_usd": args.budget_usd,
              "estimated_cost_usd": total_estimate, "dataset_limitations": document.get("limitations", []),
              "cost_warning": "No hard billing cap: reported cost arrives after the request. Unreported costs use input-only estimates.",
              "rows": [], "stopped_reason": None}
    spent = 0.0
    interrupted = False

    def save():
        report["summary"] = summarize(report["rows"])
        report["running_cost_usd"] = spent
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    try:
        for case, request in zip(cases, requests):
            row = {"id": case["id"], "question": case["question"], "expect": case["expect"],
                   "source": case["source"], "label_rule": case["label_rule"], "request": request, "backends": {}}
            report["rows"].append(row)
            for backend in BACKENDS:
                estimate = estimated_cost(request, backend)
                if spent + estimate > args.budget_usd:
                    report["stopped_reason"] = "next request estimate would exceed remaining budget"
                    break
                record = invoke(backend, request, str(evaluate), args.timeout)
                record.update(extract(record, document["questions"][case["question"]], request, backend))
                row["backends"][backend] = record
                spent += record["cost_usd"]
                save()
                print(f"Completed {case['id']} / {backend}: {answer_text(record)}", flush=True)
                if spent >= args.budget_usd:
                    report["stopped_reason"] = "running reported/estimated cost reached or exceeded budget"
                    break
            if report["stopped_reason"]:
                break
    except KeyboardInterrupt:
        report["stopped_reason"] = "interrupted; in-flight request may still have been billed"
        interrupted = True
    finally:
        save()
    display(report["rows"], report["summary"])
    print("Raw results:", output.relative_to(ROOT))
    if report["stopped_reason"]:
        print("STOPPED:", report["stopped_reason"])
    print(report["cost_warning"])
    if interrupted:
        return 130
    failed = any(not r["valid_answer"] for row in report["rows"] for r in row["backends"].values())
    return 1 if failed or report["stopped_reason"] else 0


if __name__ == "__main__":
    sys.exit(main())

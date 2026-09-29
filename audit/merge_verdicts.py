"""Merge per-lane verdicts and findings into audit/ledger.json.

Each lane writes audit/verdicts/<lane>.json and audit/findings/<lane>.json.
This script copies each verdict onto its ledger row, stamping verdict_lane
with the lane that wrote it, so coverage_check.py can confirm ownership.
Fails closed on a missing or unparseable lane file.
"""
import json
import sys
from pathlib import Path

AUDIT = Path(__file__).resolve().parent


def main() -> int:
    ledger = json.loads((AUDIT / "ledger.json").read_text(encoding="utf-8"))
    rows = {row["path"]: row for row in ledger}
    problems = []
    for vfile in sorted((AUDIT / "verdicts").glob("*.json")):
        lane = vfile.stem
        verdicts = json.loads(vfile.read_text(encoding="utf-8"))
        findings = json.loads((AUDIT / "findings" / f"{lane}.json").read_text(encoding="utf-8"))
        ids = {f["id"] for f in findings}
        for path, entry in verdicts.items():
            row = rows.get(path)
            if row is None:
                problems.append(f"{lane}: {path} is not in the ledger")
                continue
            verdict = entry["verdict"]
            if verdict != "clean" and not (isinstance(verdict, list) and set(verdict) <= ids and verdict):
                problems.append(f"{lane}: {path} has an invalid verdict {verdict!r}")
                continue
            row["verdict"] = verdict
            row["verdict_lane"] = lane
            row["findings"] = [] if verdict == "clean" else list(verdict)
            row["checks_run"] = list(entry.get("checks_run", []))
    (AUDIT / "ledger.json").write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    for p in problems:
        print(p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

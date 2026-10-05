#!/usr/bin/env python3
"""Publish prospective evidence indexes or compare them without provider access."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import trigger_comparison as comparison
from trigger_evidence import write_json_once


def rebind_identities(path: Path, out: Path | None = None) -> dict:
    """Replace each identity digest in a draft with the current one, changing nothing else."""
    text = path.read_text(encoding="utf-8")
    manifest = comparison.read_json(path)
    if manifest.get("schema_version") == "trigger-experiment-template/v1":
        comparison._require(out is not None, "template binding requires a separate --out manifest")
        bound = comparison.bind_template(manifest)
        write_json_once(out, bound)
        return {"rebound": True, "identities": bound["identities"]}
    comparison._require(out is None, "--out is only supported for unbound templates")
    current = comparison.snapshot_identities(comparison.measurement_snapshot())
    for key, old in json.loads(text)["identities"].items():
        comparison._require(text.count(old) == 1, f"{key} identity digest is not unique in the draft")
        text = text.replace(old, current[key])
    path.write_text(text, encoding="utf-8")
    return {"rebound": True, "identities": current}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("snapshot", help="Print current public observer/catalog/fixture identities")
    rebind = commands.add_parser("rebind", help="Bind a template to --out, or refresh a concrete draft in place")
    rebind.add_argument("--manifest", type=Path, required=True)
    rebind.add_argument("--out", type=Path)
    validate = commands.add_parser("validate", help="Validate a draft manifest and pinned inventory without providers")
    validate.add_argument("--manifest", type=Path, required=True)
    validate.add_argument("--inventory", type=Path, required=True)
    compare = commands.add_parser("compare")
    publish = commands.add_parser("index")
    for command in (compare, publish):
        command.add_argument("--manifest", type=Path, required=True)
        command.add_argument("--evidence-root", type=Path, required=True)
        command.add_argument("--out", type=Path)
    compare.add_argument("--baseline", type=Path, required=True)
    compare.add_argument("--candidate", type=Path, required=True)
    publish.add_argument("--arm", choices=("baseline", "candidate"), required=True)
    publish.add_argument("--reports", type=Path, nargs="+", required=True)
    publish.add_argument("--inventory", type=Path, required=True)
    publish.add_argument("--description", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "snapshot":
            snapshot = comparison.measurement_snapshot()
            result = {"identities": comparison.snapshot_identities(snapshot), "input_snapshot": snapshot}
        elif args.command == "rebind":
            result = rebind_identities(args.manifest, args.out)
        elif args.command == "validate":
            manifest = comparison.read_json(args.manifest)
            cases = comparison.validate_inventory_binding(manifest, comparison.read_json(args.inventory))
            import hashlib
            comparison._require(hashlib.sha256(args.inventory.read_bytes()).hexdigest() == manifest["inventory_sha256"], "inventory digest mismatch")
            comparison._require(manifest["identities"] == comparison.snapshot_identities(comparison.measurement_snapshot()),
                                "stale experiment identities; bind a fresh draft before approval")
            result = {"manifest_valid": True, "cases": len(cases), "identities_current": True,
                      "output_directory_bound": isinstance(manifest.get("output_directory"), str), "native_launch_authorized": False}
        elif args.command == "index":
            result = comparison.build_evidence_index(comparison.read_json(args.manifest), args.arm, args.evidence_root,
                args.reports, args.inventory, args.description)
        else:
            result = comparison.compare_evidence(comparison.read_json(args.manifest), args.evidence_root,
                comparison.read_json(args.baseline), comparison.read_json(args.candidate))
        if getattr(args, "out", None) and args.command != "rebind":
            write_json_once(args.out, result)
        print(json.dumps(result, indent=2))
        return result.get("exit_code", 0)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        print(json.dumps({"valid": False, "complete": False, "qualification": False, "error": str(exc), "exit_code": 2}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Command-line dispatch for treatment validation and replay."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__:
    from .treatment_trace_successor import *
else:
    from treatment_trace_successor import *

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate"); validate.add_argument("--fixture", type=Path, required=True)
    replay = sub.add_parser("replay"); replay.add_argument("--fixture", type=Path, required=True)
    replay.add_argument("--digest-manifest", type=Path, required=True)
    replay.add_argument("--repeat", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            bundle = _read_json_file(args.fixture)
            if not isinstance(bundle, dict):
                raise ValueError("treatment fixture must be a JSON object")
            validate_treatment_bundle(bundle)
            print(json.dumps({
                "status": "valid",
                "telemetry_profile_id": bundle["telemetry_profile_id"],
            }, sort_keys=True))
        else:
            result = replay_fixture(args.fixture, args.digest_manifest, repeat=args.repeat)
            sys.stdout.buffer.write(canonical_fixture_bytes(result))
    except (OSError, ValueError, RecursionError) as exc:
        print(f"treatment {args.command} failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

__all__ = [name for name in globals() if not name.startswith("__")]

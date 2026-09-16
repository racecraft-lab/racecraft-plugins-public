#!/usr/bin/env python3
"""Deterministic installed-extension fixture for a zero-candidate archive sweep."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath


def canonical_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"non-canonical relative path: {value}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--current-target", required=True)
    parser.add_argument("--prerequisite-mode", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    root = Path(args.repo_root).resolve(strict=True)
    current = canonical_relative(args.current_target)
    output = canonical_relative(args.output)
    current_path = root.joinpath(*current.parts)
    if not current_path.is_dir() or not current_path.resolve(strict=True).is_relative_to(root):
        raise ValueError(f"current target is unavailable: {current}")

    candidates = sorted(
        path.relative_to(root).as_posix()
        for path in (root / "specs").glob("spec-*")
        if path.is_dir() and path.resolve(strict=True).is_relative_to(root) and path != current_path
    )
    result = {
        "execution_path": "extension_contract",
        "invocation_available": True,
        "prerequisite_available": True,
        "prerequisite_mode": args.prerequisite_mode,
        "status": "no_candidates" if not candidates else "candidates_found",
        "eligible_previous_specs": candidates,
        "excluded_current_spec": current.as_posix(),
        "archive_extension_installed": True,
        "cleanup_mode": "apply",
        "safeToApplyCleanup": False,
    }
    destination = root.joinpath(*output.parts)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

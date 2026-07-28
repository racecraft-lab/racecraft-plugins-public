#!/usr/bin/env python3
"""OPERATOR-ONLY bounded smoke driver for the three CAR-004 policy controls.

**This is the operator entry point for the three live smokes. It is never run by
the default suite and never runs in continuous integration**, which is why it is
deliberately absent from ``tests/speckit-pro/suite-manifest.json``, following the
``run-calibration-pilot.py`` precedent. Its deterministic seams are covered from
``tests/speckit-pro/unit/test-policy-control-contracts.py``.

The driver dispatches nothing itself. It does two things, at the two points
FR-026a names as the enforcement points an operator actually touches:

* ``--plan`` prints the bounded command set for one control and exits. Its
  objective list is the frozen consumption path's own answer over the registered
  CAR-004 partitions, so a reserved objective is never handed to an operator.
* ``--seal`` reads a record the live run produced, validates it through
  ``claude_policy_controls.validate_smoke_record``, and writes it under the
  git-ignored ``results/`` directory.

A refusal is not a discard. The refused record is written all the same, carrying
its observed values — an observed ``api_key`` included — beside the refusal
reason, so a refused run stays distinguishable from one that never ran and the
remedy is a re-run rather than a relabel (FR-030c.3). Nothing under ``results/``
is committed either way (FR-033).

Usage::

    python3 tests/speckit-pro/layer6-efficiency/run-control-smoke.py \\
        --control <unpinned|adaptive|orchestration-changing> --plan

    python3 tests/speckit-pro/layer6-efficiency/run-control-smoke.py \\
        --control <unpinned|adaptive|orchestration-changing> --seal <record.json>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# tests/speckit-pro/layer6-efficiency/<this file> -> three levels up is tests/,
# four levels up is the repository root.
REPO_ROOT = Path(__file__).resolve().parents[3]
LAYER6_ROOT = REPO_ROOT / "tests" / "speckit-pro" / "layer6-efficiency"
LIB_DIR = LAYER6_ROOT / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import claude_policy_controls as controls  # noqa: E402

# The frozen consumption path, imported read-only. The plan's objective list is
# this module's answer rather than a CAR-004 restatement of it, which is what
# makes the plan-time half of the FR-026 guard mechanical (FR-026a.1).
from claude_experiment_policy import (  # noqa: E402
    consumable_objectives,
    consumption_verdict,
    register_partitions,
)

# FR-033: the committed layer6 .gitignore already excludes this directory's
# contents wholesale, so per-run smoke output stays untracked without any edit.
RESULTS_DIR = LAYER6_ROOT / "results"

# The command-line spelling on the left, the frozen ``control_kind`` on the right.
CONTROL_CHOICES = {
    "unpinned": "unpinned",
    "adaptive": "adaptive",
    "orchestration-changing": "orchestration_changing",
}

# FR-031a: what each smoke must read back from the evidence the run produced,
# stated on the plan so the operator knows what the run has to show.
DEMONSTRATIONS = {
    "unpinned": (
        "a served model and effort equal to the pinned parent session's, read back from the "
        "configured-route proof rather than from the dispatch request"
    ),
    "adaptive": (
        "a served model, effort, and candidate_route_id moving from ladder index i to i + 1, "
        "read back from the configured-route proof rather than from the dispatch request"
    ),
    "orchestration_changing": (
        "at least two non-parent unit members with a parent wall time strictly below their "
        "summed wall times, every wall time recorded"
    ),
}


def partition_entries(path: Path = controls.FROZEN_PARTITION_ENTRIES_PATH) -> list[dict[str, Any]]:
    """The two committed partition registry entries CAR-004 froze."""
    entries = controls.load_contract(path).get("entries")
    if not isinstance(entries, list) or not entries:
        raise controls.ControlContractError(f"{path.name} declares no partition registry entry")
    return [dict(entry) for entry in entries]


def plan_objectives(entries: list[dict[str, Any]] | None = None) -> tuple[str, ...]:
    """FR-026a.1: every objective an operator may be handed, and no other.

    The list is derived rather than authored: the registered partitions are first
    re-registered through the frozen path so disjointness is proven, then the
    frozen consumption path names the objectives it admits, then each one is
    re-checked individually. The reserved-partition guard runs last against the
    committed reservation, which is the authority on what is held back whatever a
    caller passes in.
    """
    entries = list(entries) if entries is not None else partition_entries()

    registration = register_partitions(entries)
    if not registration.ok:
        raise controls.ControlContractError(
            f"the registered partitions do not register cleanly "
            f"({registration.failure_code}): {list(registration.findings)}"
        )

    objectives = consumable_objectives(entries)
    if not objectives:
        raise controls.ControlContractError(
            "the frozen consumption path admits no objective from the registered partitions, "
            "so there is nothing an operator may be handed"
        )
    for objective in objectives:
        admitted = consumption_verdict(entries, objective)
        if not admitted.ok:
            raise controls.ControlContractError(
                f"objective {objective!r} is not admitted by the frozen consumption path "
                f"({admitted.failure_code}): {list(admitted.findings)}"
            )

    controls.assert_reserved_partition_untouched(
        [
            {"row_id": f"plan:{objective}", "objective_id": objective}
            for objective in objectives
        ],
        controls.reserved_partition_entry(),
    )
    return objectives


def _declared_bounds(smoke_bounds: dict[str, Any]) -> dict[str, str]:
    """Every frozen bound with its unit and comparison direction, flattened for print."""
    declared: dict[str, str] = {}
    for member, entry in smoke_bounds.items():
        if member == "max_cache_write_tokens_by_ttl_class":
            for ttl_class, per_class in entry.items():
                declared[f"{member}.{ttl_class}"] = (
                    f"{per_class['value']} {per_class['unit']} ({per_class['direction']})"
                )
        else:
            declared[member] = f"{entry['value']} {entry['unit']} ({entry['direction']})"
    return declared


def build_plan(
    control_kind: str, entries: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """The bounded command set for one control, derived from committed bytes only."""
    if control_kind not in CONTROL_CHOICES.values():
        raise controls.ControlContractError(
            f"{control_kind!r} is not one of the three frozen controls "
            f"{sorted(CONTROL_CHOICES.values())}"
        )
    registry = controls.load_registry()
    control = next(
        (
            candidate
            for candidate in registry["controls"]
            if candidate.get("control_kind") == control_kind
        ),
        None,
    )
    if control is None:
        raise controls.ControlContractError(
            f"the frozen registry declares no {control_kind!r} control"
        )

    entries = list(entries) if entries is not None else partition_entries()
    objectives = plan_objectives(entries)
    # The owning partition is read off the frozen path's own answer rather than
    # by restating its admission rule here.
    owning = [
        entry
        for entry in entries
        if set(objectives) & {str(objective) for objective in entry.get("objective_ids", ())}
    ]
    if len(owning) != 1:
        raise controls.ControlContractError(
            f"the admitted objectives span {len(owning)} registered partitions; the smoke draws "
            "from exactly one"
        )

    return {
        "control_kind": control_kind,
        "control_id": control["control_id"],
        "control_digest": control["control_digest"],
        "partition_id": owning[0]["partition_id"],
        "objective_ids": list(objectives),
        "bounds": _declared_bounds(registry["smoke_bounds"]),
        "demonstration": DEMONSTRATIONS[control_kind],
    }


def render_plan(plan: dict[str, Any]) -> str:
    """The printed plan an operator reads before running anything."""
    lines = [
        f"CAR-004 bounded smoke plan - control {plan['control_kind']}",
        f"  control_id:      {plan['control_id']}",
        f"  control_digest:  {plan['control_digest']}",
        f"  partition_id:    {plan['partition_id']}",
        "  authentication:  run on the supported subscription path; an observed api_key is",
        "                   recorded and refused as evidence, and the remedy is a re-run",
        "  scored:          false on every row",
        "  objectives admitted by the frozen consumption path:",
    ]
    lines.extend(f"    - {objective}" for objective in plan["objective_ids"])
    lines.append("  bounds, counted over the parent-plus-children unit:")
    lines.extend(
        f"    - {member}: {value}" for member, value in sorted(plan["bounds"].items())
    )
    lines.append(f"  demonstrate: {plan['demonstration']}")
    lines.append(
        "  seal writes under the git-ignored results/ directory; nothing here is committed"
    )
    return "\n".join(lines) + "\n"


def seal_record(
    record: dict[str, Any],
    *,
    results_dir: Path = RESULTS_DIR,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """FR-026a.2, FR-030c.3, FR-033: validate, then write whatever the verdict is.

    Every refusal ``validate_smoke_record`` can produce lands here: an observed
    ``api_key``, a scored row, a reserved-partition reference, and a breached
    bound. The refused record is written with its observed values and its refusal
    reason rather than discarded, because an absent record and a refused one must
    never be indistinguishable.
    """
    registry = registry if registry is not None else controls.load_registry()
    sealed = dict(record)
    reading: dict[str, Any] | None = None
    refusal_reasons: list[str]
    try:
        reading = dict(controls.validate_smoke_record(record, registry))
        refusal_reasons = list(reading["refusal_reasons"])
    except controls.ControlContractError as exc:
        refusal_reasons = [str(exc)]

    admitted = reading is not None and not refusal_reasons
    sealed["evidence_admissibility"] = "admitted" if admitted else "refused"
    sealed["refusal_reasons"] = refusal_reasons
    sealed["bound_reading"] = reading
    if reading is not None:
        sealed["demonstration"] = controls.evaluate_demonstration(record, registry)

    stem = str(sealed.get("smoke_id") or sealed.get("control_id") or "unidentified-smoke")
    safe = "".join(character if character.isalnum() or character in "-_" else "-"
                   for character in stem)
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / f"{safe}.json"
    path.write_text(
        json.dumps(sealed, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    return {
        "path": path,
        "admitted": admitted,
        "refusal_reasons": refusal_reasons,
        "reading": reading,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="CAR-004 operator-only bounded smoke driver (developer-local, never CI)"
    )
    parser.add_argument("--control", required=True, choices=sorted(CONTROL_CHOICES))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--plan", action="store_true", help="print the bounded plan and exit without running"
    )
    mode.add_argument(
        "--seal", metavar="RECORD", help="validate a produced record and write it under results/"
    )
    args = parser.parse_args(argv)
    control_kind = CONTROL_CHOICES[args.control]

    if args.plan:
        print(render_plan(build_plan(control_kind)), end="")
        return 0

    record = json.loads(Path(args.seal).read_text(encoding="utf-8"))
    outcome = seal_record(record)
    written = outcome["path"].relative_to(REPO_ROOT)
    if outcome["admitted"]:
        print(f"sealed: {written}")
        return 0
    print(f"REFUSED as FR-031 evidence: {outcome['refusal_reasons']}", file=sys.stderr)
    print(
        f"the refused record is written to {written} with its observed values; "
        "the remedy is a re-run, never a relabel",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

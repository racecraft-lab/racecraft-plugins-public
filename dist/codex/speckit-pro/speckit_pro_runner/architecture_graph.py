"""Validate the architecture graph the viewer page renders.

The JSON schema in ``contracts/architecture-graph.schema.json`` documents the
shape; this module enforces the same rules with the standard library only,
plus the two rules a schema cannot state: every edge endpoint is a node id,
and a ``pr``-scoped graph holds only touched nodes and their one-hop
neighbours.

Usage::

    python3 -m speckit_pro_runner.architecture_graph graph.json

Exit 0 when the graph is valid, 1 with one violation per line on stderr.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
SCOPE_KINDS = ("pr", "repository")
LANGUAGES = ("python", "typescript")
DELTA_KINDS = ("new", "changed", "removed")
TOP_FIELDS = ("schema_version", "scope", "language", "nodes", "edges")
OPTIONAL_TOP_FIELDS = ("tool",)
NODE_FIELDS = ("id", "path")
OPTIONAL_NODE_FIELDS = ("label", "touched", "delta")
EDGE_FIELDS = ("from", "to")
OPTIONAL_EDGE_FIELDS = ("valid", "rule")


def _non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_graph(data: Any) -> list[str]:
    """Return every violation in ``data``; an empty list means valid."""
    problems: list[str] = []
    if not isinstance(data, dict):
        return ["top level must be an object"]
    missing = [f for f in TOP_FIELDS if f not in data]
    if missing:
        problems.append("missing fields: " + ", ".join(missing))
    unknown = sorted(set(data) - set(TOP_FIELDS) - set(OPTIONAL_TOP_FIELDS))
    if unknown:
        problems.append("unknown top-level keys: " + ", ".join(unknown))
    if data.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"schema_version must be {SCHEMA_VERSION!r}")
    if "language" in data and data["language"] not in LANGUAGES:
        problems.append("language: must be one of " + ", ".join(LANGUAGES))
    if "tool" in data and not _non_empty(data["tool"]):
        problems.append("tool: must be a non-empty string")

    touched: set[str] = set()
    scope = data.get("scope")
    kind = None
    if "scope" in data:
        if not isinstance(scope, dict):
            problems.append("scope: must be an object")
        else:
            extra = sorted(set(scope) - {"kind", "base", "touched"})
            if extra:
                problems.append("scope: unknown fields: " + ", ".join(extra))
            kind = scope.get("kind")
            if kind not in SCOPE_KINDS:
                problems.append("scope.kind: must be one of " + ", ".join(SCOPE_KINDS))
            if kind == "pr":
                if not _non_empty(scope.get("base")):
                    problems.append("scope.base: required for kind=pr")
                raw = scope.get("touched")
                if not isinstance(raw, list) or not raw or not all(_non_empty(t) for t in raw):
                    problems.append("scope.touched: required non-empty array of node ids for kind=pr")
                else:
                    touched = set(raw)
            elif kind == "repository" and ("base" in scope or "touched" in scope):
                problems.append("scope: base and touched are only allowed for kind=pr")

    ids: set[str] = set()
    nodes = data.get("nodes")
    if "nodes" in data:
        if not isinstance(nodes, list):
            problems.append("nodes: must be an array")
            nodes = []
        for index, node in enumerate(nodes):
            prefix = f"nodes[{index}]"
            if not isinstance(node, dict):
                problems.append(f"{prefix}: must be an object")
                continue
            for field in NODE_FIELDS:
                if not _non_empty(node.get(field)):
                    problems.append(f"{prefix}.{field}: must be a non-empty string")
            extra = sorted(set(node) - set(NODE_FIELDS) - set(OPTIONAL_NODE_FIELDS))
            if extra:
                problems.append(f"{prefix}: unknown fields: " + ", ".join(extra))
            if "label" in node and not _non_empty(node["label"]):
                problems.append(f"{prefix}.label: must be a non-empty string")
            if "touched" in node and not isinstance(node["touched"], bool):
                problems.append(f"{prefix}.touched: must be a boolean")
            delta = node.get("delta")
            if "delta" in node:
                if (
                    not isinstance(delta, dict)
                    or set(delta) != {"kind", "summary"}
                    or delta["kind"] not in DELTA_KINDS
                    or not _non_empty(delta["summary"])
                ):
                    problems.append(f"{prefix}.delta: must be {{kind: new|changed|removed, summary: text}}")
            node_id = node.get("id")
            if _non_empty(node_id):
                if node_id in ids:
                    problems.append(f"{prefix}.id: duplicate {node_id!r}")
                ids.add(node_id)
                if node.get("touched") is True and touched and node_id not in touched:
                    problems.append(f"{prefix}.touched: true but {node_id!r} is not in scope.touched")

    edges = data.get("edges")
    neighbours: set[str] = set()
    if "edges" in data:
        if not isinstance(edges, list):
            problems.append("edges: must be an array")
            edges = []
        for index, edge in enumerate(edges):
            prefix = f"edges[{index}]"
            if not isinstance(edge, dict):
                problems.append(f"{prefix}: must be an object")
                continue
            extra = sorted(set(edge) - set(EDGE_FIELDS) - set(OPTIONAL_EDGE_FIELDS))
            if extra:
                problems.append(f"{prefix}: unknown fields: " + ", ".join(extra))
            for field in EDGE_FIELDS:
                value = edge.get(field)
                if not _non_empty(value):
                    problems.append(f"{prefix}.{field}: must be a non-empty string")
                elif ids and value not in ids:
                    problems.append(f"{prefix}.{field}: {value!r} is not a node id")
            if "valid" in edge and not isinstance(edge["valid"], bool):
                problems.append(f"{prefix}.valid: must be a boolean")
            if "rule" in edge and (edge.get("valid") is not False or not _non_empty(edge["rule"])):
                problems.append(f"{prefix}.rule: only allowed, as non-empty text, when valid is false")
            src, dst = edge.get("from"), edge.get("to")
            if src in touched:
                neighbours.add(dst)
            if dst in touched:
                neighbours.add(src)

    if kind == "pr" and touched and not problems:
        missing_touched = sorted(touched - ids)
        if missing_touched:
            problems.append("scope.touched: not nodes: " + ", ".join(missing_touched))
        outside = sorted(ids - touched - neighbours)
        if outside:
            problems.append("nodes: outside the touched-plus-one-hop scope: " + ", ".join(outside))
    return problems


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python3 -m speckit_pro_runner.architecture_graph graph.json", file=sys.stderr)
        return 2
    try:
        data = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"cannot read graph: {exc}", file=sys.stderr)
        return 1
    problems = validate_graph(data)
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())

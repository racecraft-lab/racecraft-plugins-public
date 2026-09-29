"""A feature directory with twelve independent tasks, shared by the task-execution test files."""

from __future__ import annotations

from pathlib import Path

from speckit_pro_runner.task_execution import fingerprints


def build_task_feature(root: Path) -> tuple[Path, str, dict]:
    """Create `feature/` under `root` with its spec and plan; return the directory, tasks body, and metadata."""
    feature = root / "feature"
    (feature / ".process").mkdir(parents=True)
    (feature / "spec.md").write_text("spec\n")
    (feature / "plan.md").write_text("plan\n")
    body = "## Phase 1\n" + "".join(f"- [ ] T{i:03d} [P] Add capability behavior {i}\n" for i in range(1, 13))
    tasks = {f"T{i:03d}": {"capability_group": "feature", "depends_on": [], "owns": [f"src/unit{i}.py"],
                           "tdd_unit": f"behavior-{i}"} for i in range(1, 13)}
    meta = {"schema_version": "task-execution.v1", "fingerprints": fingerprints("spec\n", "plan\n", body),
            "tasks": tasks}
    return feature, body, meta

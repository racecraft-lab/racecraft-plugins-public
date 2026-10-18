"""Stage-choice tests stub implement admission; admission has its own tests (test-implement-admission.py)."""

from __future__ import annotations

from unittest.mock import patch

from speckit_pro_runner.helpers import planning_approval


def stub_admission():
    return patch.object(planning_approval, "admit_implement", return_value={"admitted": True})

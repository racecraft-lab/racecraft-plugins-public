#!/usr/bin/env python3
"""Layer-4 validation for the shipped artifact gallery.

This is the gallery's single validation file. The check groups ``A``-``J``
inventoried in the feature's ``contracts/gallery-validation-contract.md`` all land
here, each group added by its own task; this scaffold is the entrypoint they land
in. With no group registered the file reports ``0/0``, which is a pass.

**Every check function takes the gallery root as a parameter.** This is load
bearing, not stylistic. A check that reads ``GALLERY_ROOT`` for itself can only
ever run against the source tree, and the source tree ships zero artifacts — so
every group that inspects an artifact (``A``, ``D``, ``E``, ``G``, and ``J``,
roughly half the inventory) would pass by vacuity and prove nothing. Taking the
root as an argument is what lets those groups be exercised a second time against
synthetic fixtures built in a temporary directory, where the artifacts they
describe actually exist. ``GALLERY_ROOT`` below is the argument the
real-gallery cases pass in — never a value a check reads on its own.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
GALLERY_ROOT = REPO_ROOT / "speckit-pro" / "artifact-gallery"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402


# Registered check-group cases, in contract order. Each group's task appends its
# own case here; a case not named here is a case the suite never runs.
CHECK_GROUPS: tuple[type[unittest.TestCase], ...] = ()


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for test_case in CHECK_GROUPS:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-artifact-gallery")


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Refactor-aware size estimates through the native runner request contract."""

from __future__ import annotations

from pathlib import Path
import runpy
import unittest

BASE_TEST = runpy.run_path(str(Path(__file__).with_name("test-estimate-spec-size.py")))
estimate = BASE_TEST["estimate"]
run_counted = BASE_TEST["run_counted"]


class SizeEstimateRefactorTests(unittest.TestCase):
    def test_integer_and_integer_string_counts_add_distinct_refactor_paths(self) -> None:
        for count in (2, "2"):
            with self.subTest(count=count):
                self.assertEqual(estimate(self, {"files": 3, "required_refactor_files": count}, context="refactor-count"),
                                 {"estimated_loc": 200, "suggested_slices": 1, "status": "ok"})

    def test_modify_discount_precedes_full_cost_of_extra_refactor_paths(self) -> None:
        for inputs, expected in (
            ({"user_stories": 3, "files": 5, "frs": 3, "required_refactor_files": 3}, 280),
            ({"user_stories": 1, "files": 1, "frs": 2, "required_refactor_files": "2"}, 127),
        ):
            with self.subTest(inputs=inputs):
                self.assertEqual(estimate(self, {**inputs, "new_vs_modify": "modify"}, context="modify-refactors"),
                                 {"estimated_loc": expected, "suggested_slices": 1, "status": "ok"})

    def test_missing_and_invalid_counts_preserve_the_existing_estimate(self) -> None:
        baseline = {"user_stories": 1, "files": 1, "frs": 2, "new_vs_modify": "modify"}
        expected = {"estimated_loc": 47, "suggested_slices": 1, "status": "ok"}
        self.assertEqual(estimate(self, baseline, context="absent-refactors"), expected)
        for count in (None, -1, "-1", "1.0", 1.5, "", "abc", " 2", True, False, [], {}):
            with self.subTest(count=count):
                self.assertEqual(estimate(self, {**baseline, "required_refactor_files": count}, context="invalid-refactors"), expected)

    def test_refactor_paths_change_ceiling_status_and_ceiling_rounded_slice_count(self) -> None:
        for count, expected in (
            (9, {"estimated_loc": 400, "suggested_slices": 1, "status": "ok"}),
            (10, {"estimated_loc": 440, "suggested_slices": 2, "status": "warn"}),
            (19, {"estimated_loc": 800, "suggested_slices": 2, "status": "warn"}),
            (20, {"estimated_loc": 840, "suggested_slices": 3, "status": "warn"}),
        ):
            with self.subTest(count=count):
                self.assertEqual(estimate(self, {"files": 1, "required_refactor_files": count}, context="refactor-boundary"), expected)

    def test_spike_precedence_ignores_even_large_or_malformed_refactor_counts(self) -> None:
        for count in ("999", -1, [], {}):
            with self.subTest(count=count):
                self.assertEqual(estimate(self, {"spike": True, "files": 99, "new_vs_modify": "modify", "required_refactor_files": count}, context="spike-refactors"),
                                 {"estimated_loc": 0, "suggested_slices": 1, "status": "ok"})

    def test_refactor_count_is_additional_to_files_already_in_the_baseline(self) -> None:
        for files, expected in ((0, 80), (4, 240)):
            with self.subTest(files=files):
                self.assertEqual(estimate(self, {"files": files, "required_refactor_files": 2}, context="additional-paths"),
                                 {"estimated_loc": expected, "suggested_slices": 1, "status": "ok"})

    def test_zero_refactors_keeps_the_existing_baseline_in_both_modes(self) -> None:
        for mode, expected in (("new", 95), ("modify", 47)):
            with self.subTest(mode=mode):
                self.assertEqual(estimate(self, {"user_stories": 1, "files": 1, "frs": 2, "new_vs_modify": mode, "required_refactor_files": "0"}, context="zero-refactors"),
                                 {"estimated_loc": expected, "suggested_slices": 1, "status": "ok"})


def main() -> int:
    return run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(SizeEstimateRefactorTests), label="test-size-estimate-refactors")


if __name__ == "__main__":
    raise SystemExit(main())

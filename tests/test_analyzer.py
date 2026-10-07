from __future__ import annotations

import unittest
from pathlib import Path

from access_review.analyzer import analyze_access
from access_review.cli import format_text_report
from access_review.repository import load_snapshot


FIXTURE = Path(__file__).parents[1] / "data" / "sample_access_snapshot.json"


class AnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = load_snapshot(FIXTURE)

    def test_summary_counts_categories(self) -> None:
        report = analyze_access(self.snapshot, "matti.meikalainen")
        self.assertEqual(
            report["summary"],
            {"total": 6, "expected": 3, "organization_wide": 1, "review": 2},
        )

    def test_privileged_department_mismatch_is_explained(self) -> None:
        report = analyze_access(self.snapshot, "matti.meikalainen")
        finance = next(
            item for item in report["categories"]["review"] if item["name"] == "Finance-Admin"
        )
        self.assertIn("privileged access", finance["evidence"])
        self.assertTrue(finance["evidence"][0].startswith("department mismatch:"))

    def test_missing_purpose_is_flagged(self) -> None:
        report = analyze_access(self.snapshot, "matti.meikalainen")
        legacy = next(
            item
            for item in report["categories"]["review"]
            if item["name"] == "Legacy-HR-Archive"
        )
        self.assertEqual(legacy["evidence"], ["access purpose is missing"])

    def test_unknown_employee_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "employee not found"):
            analyze_access(self.snapshot, "unknown.user")

    def test_text_report_repeats_human_decision_boundary(self) -> None:
        report = analyze_access(self.snapshot, "matti.meikalainen")
        rendered = format_text_report(report)
        self.assertIn("Human review required", rendered)
        self.assertIn("Finance-Admin", rendered)


if __name__ == "__main__":
    unittest.main()

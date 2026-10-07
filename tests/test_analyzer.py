from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path

from access_review.analyzer import analyze_access
from access_review.cli import format_text_report
from access_review.repository import load_snapshot
from access_review.service_desk import build_access_change_draft


FIXTURE = Path(__file__).parents[1] / "data" / "sample_access_snapshot.json"
MANAGER = "liisa.esihenkilo"
AS_OF = date(2026, 10, 7)


class AnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = load_snapshot(FIXTURE)

    def analyze(self):
        return analyze_access(
            self.snapshot, "matti.meikalainen", MANAGER, as_of=AS_OF
        )

    def test_summary_counts_categories_and_suggestions(self) -> None:
        report = self.analyze()
        self.assertEqual(
            report["summary"],
            {
                "total": 6,
                "expected": 3,
                "organization_wide": 1,
                "review": 2,
                "suggestions": 2,
            },
        )

    def test_only_direct_manager_in_both_sources_is_authorized(self) -> None:
        with self.assertRaisesRegex(PermissionError, "both AD and Entra ID"):
            analyze_access(
                self.snapshot, "matti.meikalainen", "other.manager", as_of=AS_OF
            )

    def test_conflicting_ad_and_entra_manager_records_fail_closed(self) -> None:
        employee = replace(
            self.snapshot.employees[0], entra_manager_id="other.manager"
        )
        conflicting_snapshot = replace(self.snapshot, employees=(employee,))
        with self.assertRaisesRegex(PermissionError, "both AD and Entra ID"):
            analyze_access(
                conflicting_snapshot,
                "matti.meikalainen",
                MANAGER,
                as_of=AS_OF,
            )

    def test_account_expiry_warns_within_ninety_days(self) -> None:
        status = self.analyze()["account_status"]
        self.assertEqual(status["status"], "expiring_soon")
        self.assertEqual(status["days_remaining"], 69)
        self.assertTrue(status["requires_service_desk_notice"])

    def test_contract_extension_mismatch_is_flagged(self) -> None:
        status = self.analyze()["account_status"]
        self.assertTrue(status["contract_date_mismatch"])
        self.assertIn("Recorded contract end date: 2027-06-30", status["service_desk_notice_draft"])

    def test_suggestions_explain_matching_attributes(self) -> None:
        suggestions = self.analyze()["access_suggestions"]
        hr_group = next(item for item in suggestions if item["name"] == "HR-Case-Management-Users")
        self.assertEqual(
            hr_group["matched_attributes"],
            ["job_title=HR Specialist", "department=Human Resources"],
        )

    def test_privileged_department_mismatch_is_explained(self) -> None:
        report = self.analyze()
        finance = next(
            item for item in report["categories"]["review"] if item["name"] == "Finance-Admin"
        )
        self.assertIn("privileged access", finance["evidence"])
        self.assertTrue(finance["evidence"][0].startswith("department mismatch:"))

    def test_unknown_employee_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "employee not found"):
            analyze_access(self.snapshot, "unknown.user", MANAGER, as_of=AS_OF)

    def test_service_desk_draft_contains_requested_changes_and_safety_boundary(self) -> None:
        draft = build_access_change_draft(
            self.analyze(),
            additions=["HR-Case-Management-Users"],
            removals=["Finance-Admin"],
            business_reason="Align access with current HR duties.",
        )
        self.assertIn("Requested additions", draft)
        self.assertIn("Requested removals", draft)
        self.assertIn("did not make any access changes", draft)

    def test_service_desk_draft_requires_explicit_change(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one"):
            build_access_change_draft(self.analyze())

    def test_text_report_repeats_human_decision_boundary(self) -> None:
        rendered = format_text_report(self.analyze())
        self.assertIn("cannot grant, remove, approve, or deny access", rendered)
        self.assertIn("Service Desk account-expiry draft", rendered)


if __name__ == "__main__":
    unittest.main()

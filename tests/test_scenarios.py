"""Business scenarios with explicit, versioned acceptance criteria."""
import json
from datetime import date
from pathlib import Path
import unittest

from access_review.analyzer import analyze_access
from access_review.repository import load_snapshot
from access_review.summary import summarize_report

ROOT = Path(__file__).parents[1]
CASES = json.loads((ROOT / 'scenarios/cases.json').read_text())['cases']


class ScenarioTests(unittest.TestCase):
    pass


def scenario_test(case):
    def test(self):
        snapshot = load_snapshot(ROOT / 'scenarios' / case['snapshot'])
        args = (snapshot, case['employee'], case['manager'])
        expected = case['expected']
        if expected['outcome'] == 'deny':
            with self.assertRaises(PermissionError):
                analyze_access(*args, as_of=date.fromisoformat(case['review_date']))
            return
        if expected['outcome'] == 'error':
            with self.assertRaisesRegex(ValueError, expected['error_contains']):
                analyze_access(*args, as_of=date.fromisoformat(case['review_date']))
            return
        report = analyze_access(*args, as_of=date.fromisoformat(case['review_date']))
        self.assertEqual(report['employee']['display_name'], case['display_name'])
        self.assertEqual(report['summary']['total'], expected['total'])
        self.assertEqual(report['summary']['organization_wide'], expected['organization_wide'])
        self.assertCountEqual([x['name'] for x in report['categories']['review']], expected['review'])
        self.assertCountEqual([x['name'] for x in report['access_suggestions']], expected['suggestions'])
        self.assertEqual(report['account_status']['status'], expected['account_status'])
        if 'contract_date_mismatch' in expected:
            self.assertEqual(report['account_status']['contract_date_mismatch'], expected['contract_date_mismatch'])
        for name, assignment in expected.get('assignments', {}).items():
            items = [x for category in report['categories'].values() for x in category if x['name'] == name]
            self.assertEqual(items[0]['assignment'], assignment)
        brief = summarize_report(report)
        self.assertEqual(brief['metrics']['model_calls'], 0)
        self.assertEqual(brief['metrics']['evidence_count'], len(expected['review']) + len(expected['suggestions']) + len(report['account_status']['messages']))
    return test


for case in CASES:
    setattr(ScenarioTests, 'test_' + case['id'].replace('-', '_'), scenario_test(case))


class OrganizationTests(unittest.TestCase):
    def test_all_twelve_employees_have_isolated_access_reports(self):
        snapshot = load_snapshot(ROOT / 'access_review/demo_data/ankkalinna_organization.json')
        self.assertEqual(len(snapshot.employees), 12)
        self.assertEqual(len({x.user_id for x in snapshot.employees}), 12)
        for employee in snapshot.employees:
            with self.subTest(employee=employee.user_id):
                report = analyze_access(snapshot, employee.user_id, employee.ad_manager_id, as_of=date(2026, 10, 7))
                actual = [(i['source'], i['name']) for items in report['categories'].values() for i in items]
                expected = [(i.source, i.name) for i in snapshot.entitlements if i.user_id == employee.user_id]
                self.assertCountEqual(actual, expected)
                self.assertEqual(report['employee']['user_id'], employee.user_id)

    def test_roope_cannot_review_mummos_employee_in_combined_demo(self):
        snapshot = load_snapshot(ROOT / 'access_review/demo_data/ankkalinna_organization.json')
        with self.assertRaises(PermissionError):
            analyze_access(snapshot, 'hansu.hanhi', 'roope.ankka')

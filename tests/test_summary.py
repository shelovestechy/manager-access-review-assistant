from dataclasses import replace
from datetime import date
import json
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

from access_review.analyzer import analyze_access
from access_review.models import Employee, Entitlement
from access_review.repository import load_snapshot
from access_review.summary import OllamaRanker, summarize_report

FIXTURE = Path(__file__).parents[1] / 'access_review/demo_data/sample_access_snapshot.json'


class FakeRanker:
    def __init__(self, output=None, error=None):
        self.output = output
        self.error = error
        self.calls = 0

    def rank(self, evidence):
        self.calls += 1
        if self.error:
            raise self.error
        return self.output if self.output is not None else [item['id'] for item in reversed(evidence)]


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = load_snapshot(FIXTURE)
        self.report = analyze_access(self.snapshot, 'matti.meikalainen', 'liisa.esihenkilo', as_of=date(2026, 10, 7))

    def test_offline_summary_contains_all_findings_and_resolvable_citations(self):
        summary = summarize_report(self.report)
        self.assertEqual(summary['mode'], 'deterministic')
        self.assertEqual(summary['metrics']['model_calls'], 0)
        self.assertEqual(len(summary['evidence']), 6)
        for item in summary['evidence']:
            value = self.report
            for key in item['report_path'].strip('/').split('/'):
                value = value[int(key)] if isinstance(value, list) else value[key]
            self.assertTrue(value)

    def test_model_may_only_reorder_original_evidence(self):
        original = summarize_report(self.report)['evidence']
        result = summarize_report(self.report, FakeRanker())
        self.assertEqual(result['mode'], 'model_ordered')
        self.assertEqual(result['evidence'], list(reversed(original)))
        self.assertEqual(result['metrics']['model_calls'], 1)

    def test_invalid_or_missing_citations_fall_back_without_losing_findings(self):
        original = summarize_report(self.report)['evidence']
        ids = [item['id'] for item in original]
        for response in ([], ids[:-1], ids + ['invented'], [ids[0]] * len(ids), {}, 'E001', [None]):
            with self.subTest(response=response):
                ranker = FakeRanker(response)
                result = summarize_report(self.report, ranker)
                self.assertEqual(result['mode'], 'fallback')
                self.assertEqual(result['evidence'], original)
                self.assertEqual(ranker.calls, 1)

    def test_timeout_falls_back_without_retry(self):
        ranker = FakeRanker(error=TimeoutError())
        self.assertEqual(summarize_report(self.report, ranker)['mode'], 'fallback')
        self.assertEqual(ranker.calls, 1)

    def test_unauthorized_report_never_reaches_model(self):
        self.report['authorization']['authorized'] = False
        ranker = FakeRanker()
        with self.assertRaises(PermissionError):
            summarize_report(self.report, ranker)
        self.assertEqual(ranker.calls, 0)

    def test_large_report_skips_model_but_preserves_evidence(self):
        self.report['account_status']['messages'] *= 20
        ranker = FakeRanker()
        result = summarize_report(self.report, ranker)
        self.assertEqual(result['fallback_reason'], 'evidence_budget_exceeded')
        self.assertEqual(ranker.calls, 0)
        self.assertEqual(len(result['evidence']), 44)

    def test_null_directory_identity_is_rejected_before_string_coercion(self):
        payload = json.loads(FIXTURE.read_text())['employees'][0]
        payload['ad_manager_id'] = None
        with self.assertRaises(ValueError):
            Employee.from_dict(payload)

    def test_empty_or_whitespace_managers_fail_closed(self):
        for value in ('', ' ', None):
            employee = replace(self.snapshot.employees[0], ad_manager_id=value, entra_manager_id=value)
            with self.assertRaises(PermissionError):
                analyze_access(replace(self.snapshot, employees=(employee,)), employee.user_id, value)

    def test_same_name_in_different_source_does_not_hide_suggestion(self):
        existing = Entitlement('matti.meikalainen', 'Other', 'group', 'HR-Case-Management-Users', 'direct')
        snapshot = replace(self.snapshot, entitlements=self.snapshot.entitlements + (existing,))
        report = analyze_access(snapshot, 'matti.meikalainen', 'liisa.esihenkilo')
        self.assertIn('HR-Case-Management-Users', [s['name'] for s in report['access_suggestions']])

    @patch('access_review.summary.build_opener')
    def test_ollama_request_is_bounded_and_parses_structured_response(self, build_opener):
        envelope = {'done': True, 'message': {'content': '{"evidence_ids":["E001"]}'}}
        response = MagicMock()
        response.read.return_value = json.dumps(envelope).encode()
        build_opener.return_value.open.return_value.__enter__.return_value = response
        ranker = OllamaRanker('test-local')
        result = ranker.rank([{'id': 'E001', 'text': 'Untrusted directory text'}])
        self.assertEqual(result, ['E001'])
        call = build_opener.return_value.open.call_args
        self.assertEqual(call.kwargs['timeout'], 15)
        request = call.args[0]
        self.assertEqual(request.full_url, 'http://127.0.0.1:11434/api/chat')
        body = json.loads(request.data)
        self.assertFalse(body['stream'])
        self.assertNotIn('tools', body)
        self.assertEqual(body['options']['num_predict'], 512)

    @patch('access_review.summary.build_opener')
    def test_malformed_transport_response_falls_back(self, opener):
        response = MagicMock()
        response.read.return_value = b'{"done":true,"message":{"content":"not JSON"}}'
        opener.return_value.open.return_value.__enter__.return_value = response
        self.assertEqual(summarize_report(self.report, OllamaRanker('test'))['mode'], 'fallback')

    def test_cloud_model_name_is_rejected(self):
        with self.assertRaises(ValueError):
            OllamaRanker('example:cloud')

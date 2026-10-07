import unittest
import json
from pathlib import Path
from access_review.evaluate import evaluate, pairwise_score

MANIFEST = Path(__file__).parents[1] / 'evaluation/cases.json'

class EvaluationTests(unittest.TestCase):
    def test_known_order_scores_and_ties(self):
        self.assertEqual(pairwise_score(['urgent','later'], {'urgent':0,'later':1})['score'], 1)
        self.assertEqual(pairwise_score(['later','urgent'], {'urgent':0,'later':1})['score'], 0)
        self.assertIsNone(pairwise_score(['a','b'], {'a':0,'b':0})['score'])

    def test_missing_duplicate_or_unknown_evidence_is_rejected(self):
        for keys in ([], ['a','a'], ['other']):
            with self.assertRaises(ValueError):
                pairwise_score(keys, {'a':0})

    def test_all_fixtures_have_exhaustive_labels_without_model_claims(self):
        result=evaluate(MANIFEST)
        self.assertEqual(len(result['cases']),5)
        self.assertFalse(result['real_model_quality_measured'])
        self.assertEqual(result['successful_model_trials'],0)
        transfer=result['cases'][0]
        self.assertEqual(transfer['baseline']['score'],1)
        self.assertEqual(transfer['baseline']['ordered_pairs'],3)

    def test_failed_model_is_not_credited_with_baseline_score(self):
        class Failed:
            def rank(self, evidence):
                raise TimeoutError()
        result=evaluate(MANIFEST, Failed())
        self.assertEqual(result['successful_model_trials'],0)
        for case in result['cases']:
            for trial in case['trials']:
                self.assertIsNone(trial['model_score'])
                self.assertTrue(trial['evidence_preserved'])

    def test_every_fixture_uses_ankkalinna_identities(self):
        manifest=json.loads(MANIFEST.read_text())
        for case in manifest['cases']:
            data=json.loads((MANIFEST.parent / case['snapshot']).read_text())
            employee=data['employees'][0]
            self.assertEqual(employee['display_name'], 'Aku Ankka')
            self.assertEqual(employee['user_id'], 'aku.ankka')
            self.assertEqual(employee['ad_manager_id'], 'roope.ankka')
            self.assertEqual(employee['entra_manager_id'], 'roope.ankka')
            self.assertEqual(employee['office_location'], 'Ankkalinna')

"""Repeatable offline/model comparison against explicitly labelled synthetic cases."""
from __future__ import annotations
import argparse
from datetime import date
import json
from pathlib import Path
import platform
from statistics import mean

from .analyzer import analyze_access
from .repository import load_snapshot
from .summary import OllamaRanker, summarize_report


def evidence_key(item, report):
    parts = item['report_path'].strip('/').split('/')
    index = int(parts[-1])
    if item['kind'] == 'account':
        return f'account:{index}'
    if item['kind'] == 'review':
        return 'review:' + report['categories']['review'][index]['name']
    return 'suggestion:' + report['access_suggestions'][index]['name']


def pairwise_score(keys, priorities):
    """Fraction of strictly ordered labelled pairs in the expected order; ties ignored."""
    if len(keys) != len(set(keys)) or set(keys) != set(priorities):
        raise ValueError('Evaluation labels must cover each evidence item exactly once')
    correct = total = 0
    for left in range(len(keys)):
        for right in range(left + 1, len(keys)):
            a, b = priorities[keys[left]], priorities[keys[right]]
            if a == b:
                continue
            total += 1
            correct += a < b
    return {'correct_pairs': correct, 'ordered_pairs': total,
            'score': correct / total if total else None}


def evaluate(manifest_path: Path, ranker=None, *, repeats=1):
    manifest = json.loads(manifest_path.read_text())
    rows = []
    for case in manifest['cases']:
        snapshot = load_snapshot(manifest_path.parent / case['snapshot'])
        report = analyze_access(snapshot, manifest['employee'], manifest['manager'],
                                as_of=date.fromisoformat(manifest['review_date']))
        baseline = summarize_report(report)
        baseline_score = pairwise_score([evidence_key(x, report) for x in baseline['evidence']], case['priorities'])
        trials = []
        if ranker is not None:
            for _ in range(repeats):
                candidate = summarize_report(report, ranker)
                score = pairwise_score([evidence_key(x, report) for x in candidate['evidence']], case['priorities'])
                trials.append({'mode': candidate['mode'], 'fallback_reason': candidate['fallback_reason'],
                               'duration_ms': candidate['metrics']['duration_ms'],
                               'evidence_preserved': candidate['metrics']['evidence_count'] == len(baseline['evidence']),
                               'model_score': score['score'] if candidate['mode'] == 'model_ordered' else None})
        rows.append({'case': case['name'], 'description': case['description'],
                     'baseline': baseline_score, 'trials': trials})
    successful = [trial for row in rows for trial in row['trials'] if trial['mode'] == 'model_ordered']
    return {'model': getattr(ranker, 'model', None), 'label_status': manifest['label_status'],
            'environment': {'python': platform.python_version(), 'platform': platform.system(), 'machine': platform.machine()},
            'real_model_quality_measured': isinstance(ranker, OllamaRanker) and bool(successful),
            'successful_model_trials': len(successful),
            'mean_successful_model_ms': mean(x['duration_ms'] for x in successful) if successful else None,
            'cases': rows,
            'limitations': 'Synthetic draft labels; ties ignored. Fallback scores are never reported as model scores. Record model digest, hardware and Ollama version separately for a real benchmark.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, default=Path('evaluation/cases.json'))
    parser.add_argument('--ollama-model')
    parser.add_argument('--repeats', type=int, default=1)
    args = parser.parse_args(argv)
    if not 1 <= args.repeats <= 5:
        parser.error('--repeats must be between 1 and 5')
    result = evaluate(args.cases, OllamaRanker(args.ollama_model) if args.ollama_model else None, repeats=args.repeats)
    print(json.dumps(result, indent=2))
    return 2 if args.ollama_model and not result['successful_model_trials'] else 0


if __name__ == '__main__':
    raise SystemExit(main())

"""Collect every run's summary.json under experiments/runs/ into ONE digest file.

Walks experiments/runs/*/summary.json, keeps the compact aggregates (args subset + per-selector
overall / by_stratum / mode), and writes experiments/all_results.json. The big per-sample
samples.jsonl is NOT included (it is only needed server-side for the leakage re-bucket), so the
digest is small enough to sync as a single file for paper-table filling.

    python scripts/collect_results.py
    python scripts/collect_results.py --runs experiments/runs --out experiments/all_results.json
"""

import argparse
import glob
import json
import os

# args worth keeping (identify the run); everything else (paths, timeouts) is dropped.
_KEEP_ARGS = ['dataset', 'split', 'selectors', 'segmenter', 'model_path', 'tag', 'oracle',
              'batch_size', 'overrides']


def _digest_one(path):
    d = json.load(open(path, encoding='utf-8'))
    a = d.get('args', {})
    args = {k: a[k] for k in _KEEP_ARGS if k in a}
    # by_selector is already aggregate (overall / by_stratum / mode) -> keep as-is.
    return {'args': args, 'by_selector': d.get('by_selector', {})}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', default='experiments/runs', help='runs root')
    ap.add_argument('--out', default='experiments/all_results.json')
    args = ap.parse_args()

    out = {}
    for path in sorted(glob.glob(os.path.join(args.runs, '*', 'summary.json'))):
        name = os.path.basename(os.path.dirname(path))
        try:
            out[name] = _digest_one(path)
        except Exception as e:                       # a half-written run shouldn't kill the digest
            print(f'[skip] {name}: {e}')
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or '.', exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    size = os.path.getsize(args.out)
    print(f'[collect] {len(out)} runs -> {args.out}  ({size/1024:.1f} KB)')
    for name in out:
        sels = ','.join(out[name]['by_selector'].keys())
        print(f'  {name:42} [{sels}]')


if __name__ == '__main__':
    main()

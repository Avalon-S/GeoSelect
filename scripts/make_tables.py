"""Turn run_eval summary.json files into the merged-paper tables (no re-run; reads existing data).

Emits, for each given run, plain-text + LaTeX-ready rows:
  1) OVERALL line: V2 mIoU/oIoU/Pr@0.5 (the main-table headline number).
  2) STRATIFIED C4 table: per-stratum V2 vs V1 (delta) — the C4 attribution.
  3) RELIABILITY line: V2-rate / fallback-rate.
  4) ORACLE CAPTURE (if the run was --oracle): per-stratum V2/oracle capture rate.

V1 appears ONLY as the in-harness selector baseline (C4) — every reported V2 number is V2's.
Pass several summary.json (e.g. RRSIS-D test + RISBench test) to print them side by side.

    python scripts/make_tables.py experiments/eval_rrsisd_test/summary.json \
                                  experiments/eval_risbench_test/summary.json
"""

import argparse
import json
import os

STRATA = ['image', 'object', 'attribute', 'superlative', 'ordinal', 'group', 'compositional']


def _pct(d, key='mIoU'):
    return d.get(key, 0) * 100


def report(path):
    d = json.load(open(path, encoding='utf-8'))
    bs = d['by_selector']
    name = os.path.basename(os.path.dirname(os.path.abspath(path)))
    print('=' * 64)
    print(f'RUN: {name}   ({path})')
    print('=' * 64)

    v2 = bs.get('v2'); v1 = bs.get('v1'); orc = bs.get('oracle')

    # 1) overall headline
    if v2:
        o = v2['overall']
        print(f'[overall V2]  mIoU={_pct(o):.2f}  oIoU={_pct(o,"oIoU"):.2f}  '
              f'Pr@0.5={o.get("Pr@0.5",0)*100:.1f}  n={o["n_samples"]}')
        m = v2.get('mode', {})
        if m:
            print(f'[reliability] V2={m.get("v2",0)}  fallback={m.get("fallback",0)}  '
                  f'V2-rate={m.get("v2_rate",0)*100:.1f}%')

    # 2) stratified C4 (V1 vs V2)
    if v1 and v2:
        b1, b2 = v1['by_stratum'], v2['by_stratum']
        print('\n  stratum         n     V1     V2    delta')
        print('  ' + '-' * 42)
        for t in STRATA:
            if t not in b2 and t not in b1:
                continue
            n = b2.get(t, b1.get(t, {})).get('n_samples', 0)
            m1, m2 = _pct(b1.get(t, {})), _pct(b2.get(t, {}))
            print(f'  {t:13} {n:5}  {m1:5.2f}  {m2:5.2f}  {m2-m1:+5.2f}')
        print(f'  {"OVERALL":13} {v2["overall"]["n_samples"]:5}  '
              f'{_pct(v1["overall"]):5.2f}  {_pct(v2["overall"]):5.2f}  '
              f'{_pct(v2["overall"])-_pct(v1["overall"]):+5.2f}')

    # 3) oracle capture
    if orc and v2:
        bo, b2 = orc['by_stratum'], v2['by_stratum']
        print('\n  [oracle capture]  stratum      V2   oracle  capture%')
        for t in STRATA:
            if t not in bo:
                continue
            vv, oo = _pct(b2.get(t, {})), _pct(bo.get(t, {}))
            print(f'                    {t:13} {vv:5.2f}  {oo:5.2f}  {vv/oo*100 if oo else 0:5.1f}')
        vv, oo = _pct(v2['overall']), _pct(orc['overall'])
        print(f'                    {"OVERALL":13} {vv:5.2f}  {oo:5.2f}  {vv/oo*100 if oo else 0:5.1f}')
    print()


def sweep(paths):
    """One compact V2 row per run — for ablations that vary ONE knob (parser model, segmenter)
    and compare the V2 headline. Columns: label | n | mIoU | oIoU | Pr@0.5 | V2-rate."""
    print(f'{"run":28} {"n":>6} {"mIoU":>6} {"oIoU":>6} {"Pr@.5":>6} {"V2-rate":>8}')
    print('-' * 66)
    for p in paths:
        d = json.load(open(p, encoding='utf-8'))
        v2 = d['by_selector'].get('v2')
        if not v2:
            continue
        o = v2['overall']; m = v2.get('mode', {})
        label = os.path.basename(os.path.dirname(os.path.abspath(p)))
        print(f'{label:28} {o["n_samples"]:>6} {_pct(o):6.2f} {_pct(o,"oIoU"):6.2f} '
              f'{o.get("Pr@0.5",0)*100:6.1f} {m.get("v2_rate",0)*100:7.1f}%')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('summaries', nargs='+', help='one or more run_eval summary.json')
    ap.add_argument('--sweep', action='store_true',
                    help='compact one-row-per-run table (for parser/segmenter ablations)')
    args = ap.parse_args()
    if args.sweep:
        sweep(args.summaries)
    else:
        for p in args.summaries:
            report(p)


if __name__ == '__main__':
    main()

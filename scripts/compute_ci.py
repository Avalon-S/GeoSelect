"""Bootstrap CIs and per-stratum decompositions from the FROZEN eval per-sample dumps.

Pure re-bucketing of the same per-sample IoUs that produced the published headline numbers
(no GPU, no re-run). Verifies its aggregates against the paper tables before emitting CIs.

  - RISBench per-stratum fields-only (v1_iou) vs full (v2_iou) + 95% CI on the paired delta
  - Headline mIoU + 95% CI (RRSIS-D test, RISBench test)
  - Selector ablation mIoU + 95% CI (RRSIS-D val: confidence / clip / fields-only / full)
  - RRSIS-D val paired deltas: fields-only -> full, and detector confidence -> full

Together these are every confidence interval the paper reports. Point estimates are exact; a
bootstrap endpoint depends on the resampling seed, so a bound can land a few hundredths from the
one printed in the paper. No reported comparison changes sign or significance under that.

    python scripts/compute_ci.py
"""
import json
import random
from collections import defaultdict

RISB_TEST = 'experiments/eval_risbench_test/samples.jsonl'
RRSISD_TEST = 'experiments/runs/eval_rrsisd_test_oracle/samples.jsonl'
RRSISD_VAL = 'experiments/runs/eval_rrsisd_val/samples.jsonl'
NBOOT = 5000
SEED = 0


def load(path):
    return [json.loads(l) for l in open(path, encoding='utf-8')]


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def ci_mean(xs, nboot=NBOOT, seed=SEED):
    """Percentile bootstrap 95% CI of the mean."""
    rng = random.Random(seed)
    n = len(xs)
    if n == 0:
        return (0.0, 0.0, 0.0)
    bs = []
    for _ in range(nboot):
        s = 0.0
        for _ in range(n):
            s += xs[rng.randrange(n)]
        bs.append(s / n)
    bs.sort()
    return mean(xs), bs[int(0.025 * nboot)], bs[int(0.975 * nboot)]


def ci_delta(pairs, nboot=NBOOT, seed=SEED):
    """Paired bootstrap 95% CI of the mean of (b - a)."""
    d = [b - a for a, b in pairs]
    return ci_mean(d, nboot, seed)


def pct(x):
    return f'{x * 100:.2f}'


def main():
    random.seed(SEED)

    # ---- RISBench per-stratum: fields-only (v1) vs full (v2) ----
    rb = load(RISB_TEST)
    assert abs(mean([r['v2_iou'] for r in rb]) * 100 - 55.27) < 0.01, 'RISBench full != 55.27'
    assert abs(mean([r['v1_iou'] for r in rb]) * 100 - 54.13) < 0.01, 'RISBench fields != 54.13'
    print(f'[verify] RISBench full={pct(mean([r["v2_iou"] for r in rb]))} '
          f'fields={pct(mean([r["v1_iou"] for r in rb]))}  n={len(rb)}')

    strata = ['superlative', 'ordinal', 'group', 'compositional']
    buckets = defaultdict(list)
    for r in rb:
        for t in r.get('tags', []):
            if t in strata:
                buckets[t].append((r['v1_iou'], r['v2_iou']))
    print('\n=== RISBench per-stratum (fields-only vs full) ===')
    print(f'{"stratum":14s} {"n":>5s} {"fields":>7s} {"full":>7s} {"delta":>7s}  95%CI(delta)')
    rows = []
    for s in strata:
        p = buckets[s]
        n = len(p)
        fo = mean([a for a, _ in p]) * 100
        fu = mean([b for _, b in p]) * 100
        dm, lo, hi = ci_delta(p)
        rows.append((s, n, fo, fu, dm * 100, lo * 100, hi * 100))
        print(f'{s:14s} {n:5d} {fo:7.2f} {fu:7.2f} {dm * 100:+7.2f}  [{lo * 100:+.2f}, {hi * 100:+.2f}]')
    allp = [(r['v1_iou'], r['v2_iou']) for r in rb]
    dm, lo, hi = ci_delta(allp)
    print(f'{"OVERALL":14s} {len(allp):5d} {mean([a for a,_ in allp])*100:7.2f} '
          f'{mean([b for _,b in allp])*100:7.2f} {dm*100:+7.2f}  [{lo*100:+.2f}, {hi*100:+.2f}]')

    # ---- Headline CIs ----
    print('\n=== Headline mIoU + 95% CI ===')
    for name, path, key, ref in [('RRSIS-D test full', RRSISD_TEST, 'v2_iou', 58.86),
                                 ('RISBench test full', RISB_TEST, 'v2_iou', 55.27)]:
        d = load(path)
        xs = [r[key] for r in d]
        m, lo, hi = ci_mean(xs)
        flag = '' if abs(m * 100 - ref) < 0.01 else f'  !! expected {ref}'
        print(f'{name:20s} n={len(xs):5d}  mIoU={pct(m)}  95%CI[{pct(lo)}, {pct(hi)}]{flag}')

    # ---- Selector ablation CIs (RRSIS-D val) ----
    print('\n=== Selector ablation (RRSIS-D val) mIoU + 95% CI ===')
    sv = load(RRSISD_VAL)
    for label, key, ref in [('Detector confidence', 'confidence_iou', 46.17),
                            ('GeoRSCLIP', 'clip_iou', 45.22),
                            ('Ours, fields only', 'v1_iou', 57.41),
                            ('Ours, full program', 'v2_iou', 58.23)]:
        xs = [r[key] for r in sv]
        m, lo, hi = ci_mean(xs)
        flag = '' if abs(m * 100 - ref) < 0.05 else f'  !! expected {ref}'
        print(f'{label:22s} n={len(xs):5d}  mIoU={pct(m)}  95%CI[{pct(lo)}, {pct(hi)}]{flag}')

    # ---- Paired deltas behind the two gains quoted in the running text ----
    print('\n=== RRSIS-D val paired deltas + 95% CI ===')
    for label, base, ref in [('fields-only -> full', 'v1_iou', 0.82),
                             ('confidence -> full', 'confidence_iou', 12.06)]:
        pairs = [(r[base], r['v2_iou']) for r in sv]
        dm, lo, hi = ci_delta(pairs)
        flag = '' if abs(dm * 100 - ref) < 0.05 else f'  !! expected {ref}'
        print(f'{label:22s} n={len(pairs):5d}  delta={dm * 100:+6.2f}  '
              f'95%CI[{lo * 100:+.2f}, {hi * 100:+.2f}]{flag}')


if __name__ == '__main__':
    main()

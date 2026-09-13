"""Failure-cause statistics by pipeline stage, per dataset, as grouped bars.
Computed from the V2 test samples: Success = IoU>=0.5; otherwise attribute to the first stage
that failed -- Detection (no candidate reached IoU 0.5), Selection (field-only fallback picked
the wrong existing box), or Synthesis (an executed program picked the wrong existing box).

    python scripts/fig_failure_stats.py
"""

import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# In this repository the figure belongs next to the manuscript; in the public release tree there is
# no paper/ directory, so it lands in ./figures rather than conjuring our manuscript layout on
# someone else's machine.
FIGDIR = 'paper/GeoSelect/figures' if os.path.isdir('paper/GeoSelect') else 'figures'
TH = 0.5
CATS = ['Success', 'Detection', 'Selection', 'Program-path']
COLORS = ['#4Fa64F', '#4F8Fd0', '#d0a020', '#c84040']
DS = [('rrsisd', 'RRSIS-D'), ('risbench', 'RISBench')]


def breakdown(path):
    rows = [json.loads(l) for l in open(path, encoding='utf-8')]
    n = len(rows); c = {k: 0 for k in CATS}
    for r in rows:
        iou = r['v2_iou']; ob = r.get('oracle_boxIoU', 0); mode = r.get('v2_mode')
        if iou >= TH:
            c['Success'] += 1
        elif ob < TH:
            c['Detection'] += 1
        elif mode == 'v2':
            c['Program-path'] += 1
        else:
            c['Selection'] += 1
    return n, [100 * c[k] / n for k in CATS]


def main():
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 2.9))
    for ax, (ds, name) in zip(axes, DS):
        p = f'experiments/runs/eval_{ds}_test_oracle/samples.jsonl'
        n, pct = breakdown(p)
        bars = ax.bar(CATS, pct, color=COLORS, edgecolor='black', linewidth=0.5, width=0.7)
        for b, v in zip(bars, pct):
            ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f'{v:.1f}%',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
        ax.set_title(f'{name}  (n={n})', fontsize=11, fontweight='bold')
        ax.set_ylim(0, max(pct) + 12)
        ax.set_ylabel('% of expressions', fontsize=9)
        ax.tick_params(axis='x', labelsize=9)
        ax.tick_params(axis='y', labelsize=8)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
    fig.tight_layout()
    os.makedirs(FIGDIR, exist_ok=True)
    out = os.path.join(FIGDIR, 'failure_stats.png')
    fig.savefig(out, dpi=300, bbox_inches='tight')
    print(f'[fig] failure stats -> {out}')
    for ds, name in DS:
        n, pct = breakdown(f'experiments/runs/eval_{ds}_test_oracle/samples.jsonl')
        print(f'  {name}: ' + '  '.join(f'{k}={v:.1f}%' for k, v in zip(CATS, pct)))


if __name__ == '__main__':
    main()

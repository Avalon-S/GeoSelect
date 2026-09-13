"""Stratified segmentation metrics.

Wraps V1's SegMetrics (geogrounder.metrics, reused verbatim for comparability) into an overall
accumulator PLUS one per stratum tag. One add() per (image, sentence) sample buckets that
sample's IoU into the overall metric and into EVERY stratum it belongs to (strata are a SET, so
a superlative+compositional sentence counts in both). This re-buckets fixed per-sample IoUs — it
never changes the overall number (same discipline as V1's stratified report).

Decoupled from the stratifier on purpose: add() takes the already-computed `tags` set, so this
class unit-tests with synthetic masks + tags (no model, no pycocotools). The eval driver computes
tags via geoselect_v2.eval.stratifier.stratum_tags (V1 base type + V2 tags).
"""

from __future__ import annotations

from typing import Dict, Iterable, Set

from geogrounder.metrics import SegMetrics


class StratifiedMetrics:
    def __init__(self, strata: Iterable[str], thresholds=(0.5, 0.6, 0.7, 0.8, 0.9)):
        self.thresholds = tuple(thresholds)
        self.overall = SegMetrics(thresholds)
        self.per: Dict[str, SegMetrics] = {t: SegMetrics(thresholds) for t in strata}
        # mode bookkeeping for the reliability table (how often V2 vs fallback fired)
        self.mode_counts: Dict[str, int] = {}

    def add(self, pred, gt, tags: Set[str] = (), mode: str = None) -> float:
        """Accumulate one (image, sentence) sample. `tags` = its strata (overall is always
        updated). `mode` ('v2'|'fallback') is tallied for the reliability table. Returns the IoU.
        Unknown tags are created on the fly so a freshly-added stratum is not silently dropped."""
        iou = self.overall.add(pred, gt)
        for t in tags:
            if t not in self.per:
                self.per[t] = SegMetrics(self.thresholds)
            self.per[t].add(pred, gt)
        if mode is not None:
            self.mode_counts[mode] = self.mode_counts.get(mode, 0) + 1
        return iou

    def summary(self) -> dict:
        out = {'overall': self.overall.summary(), 'by_stratum': {}}
        for t, m in self.per.items():
            if m.seg_total > 0:
                out['by_stratum'][t] = m.summary()
        if self.mode_counts:
            tot = sum(self.mode_counts.values())
            out['mode'] = {k: v for k, v in self.mode_counts.items()}
            out['mode']['v2_rate'] = self.mode_counts.get('v2', 0) / tot if tot else 0.0
        return out

    def format(self) -> str:
        s = self.summary()
        lines = [f"OVERALL  n={s['overall']['n_samples']}  "
                 f"mIoU={s['overall']['mIoU']*100:.2f}  oIoU={s['overall']['oIoU']*100:.2f}"]
        for t in sorted(s['by_stratum']):
            st = s['by_stratum'][t]
            lines.append(f"  [{t:13}] n={st['n_samples']:5}  mIoU={st['mIoU']*100:.2f}  "
                         f"oIoU={st['oIoU']*100:.2f}  Pr@0.5={st['Pr@0.5']*100:.1f}")
        if 'mode' in s:
            lines.append(f"  reliability: V2={s['mode'].get('v2',0)} "
                         f"fallback={s['mode'].get('fallback',0)} "
                         f"(V2 rate {s['mode']['v2_rate']*100:.1f}%)")
        return '\n'.join(lines)

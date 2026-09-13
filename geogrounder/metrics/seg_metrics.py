"""RRSIS segmentation metrics — oIoU, mIoU, Pr@X.

Reproduces RMSIN/LAVT test.py exactly so our numbers are comparable to published ones:

    I, U   = sum(pred & gt), sum(pred | gt)          # per sample
    this_iou = 0.0 if U == 0 else I / U
    cum_I += I ; cum_U += U
    seg_correct[k] += (this_iou >= thr[k])
    seg_total += 1
    ...
    mIoU = mean(per-sample iou)
    oIoU = cum_I / cum_U
    Pr@X = seg_correct[k] / seg_total

One `add()` call == one (image, sentence) sample. pred and gt must be the same shape
(binary {0,1} / bool); resolution matching is the caller's responsibility.
"""

import numpy as np


class SegMetrics:
    def __init__(self, thresholds=(0.5, 0.6, 0.7, 0.8, 0.9)):
        self.thresholds = tuple(thresholds)
        self.cum_I = 0
        self.cum_U = 0
        self.ious = []
        self.seg_correct = np.zeros(len(self.thresholds), dtype=np.int64)
        self.seg_total = 0

    def add(self, pred, gt):
        pred = np.asarray(pred).astype(bool)
        gt = np.asarray(gt).astype(bool)
        if pred.shape != gt.shape:
            raise ValueError(f'pred {pred.shape} and gt {gt.shape} must match; '
                             f'resize before calling add().')

        I = int(np.logical_and(pred, gt).sum())
        U = int(np.logical_or(pred, gt).sum())
        this_iou = 0.0 if U == 0 else I / U

        self.ious.append(this_iou)
        self.cum_I += I
        self.cum_U += U
        for k, thr in enumerate(self.thresholds):
            self.seg_correct[k] += int(this_iou >= thr)
        self.seg_total += 1
        return this_iou

    def summary(self):
        if self.seg_total == 0:
            raise RuntimeError('no samples accumulated')
        mIoU = float(np.mean(self.ious))
        oIoU = float(self.cum_I / self.cum_U) if self.cum_U > 0 else 0.0
        out = {
            'mIoU': mIoU,
            'oIoU': oIoU,
            'n_samples': self.seg_total,
        }
        for k, thr in enumerate(self.thresholds):
            out[f'Pr@{thr}'] = float(self.seg_correct[k] / self.seg_total)
        return out

    def format(self):
        s = self.summary()
        lines = [f"n = {s['n_samples']}",
                 f"mIoU       = {s['mIoU'] * 100:.2f}",
                 f"oIoU       = {s['oIoU'] * 100:.2f}"]
        for thr in self.thresholds:
            lines.append(f"Pr@{thr}    = {s[f'Pr@{thr}'] * 100:.2f}")
        return '\n'.join(lines)

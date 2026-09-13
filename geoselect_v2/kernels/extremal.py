"""Frame-relative EXTREMAL kernel — the superlative core.

The key distinction from V1:

    `leftmost` (extremal)  != `the left one` (banded)

V1 collapses both onto one monotone half-plane ramp, which on a multi-candidate selection
just picks the most extreme box even when "the left one" means a relative band. The extremal
kernel scores a candidate by how far it lies in the queried direction *relative to the OTHER
candidates* — a softmax/softmin over the candidate set, NOT a dense field over the image frame:

    E_dir(i) = softmax_i( +/- beta * v_i )            # v_i = candidate i's axis coordinate

where the sign selects max vs min along the axis, and beta is a temperature initialised from
the candidate *spacing* scale, so the separation is resolution-independent. This drives
argmax/argmin (and, after sorting, nth).

Pure numpy; no model/GPU. Operates on candidate boxes only, so it is cheap and order-aware.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np

Box = Tuple[float, float, float, float]


def _center(box: Box) -> Tuple[float, float]:
    x1, y1, x2, y2 = box
    return 0.5 * (x1 + x2), 0.5 * (y1 + y2)


def axis_value(box: Box, axis: str) -> float:
    """Scalar projection of a box centre onto an extremum axis.

    X          : +x = right (east)         -> larger = more right
    Y          : +y = down  (south)        -> larger = more bottom
    DIAG_UL_LR : upper-left -> lower-right  -> larger = more lower-right  (cx + cy)
    DIAG_UR_LL : upper-right -> lower-left  -> larger = more lower-left   (-cx + cy)
    AREA       : bounding-box area          -> larger = bigger instance   (size superlatives)

    `axis` accepts the Axis enum NAME (e.g. 'X', 'DIAG_UL_LR') or an Axis member.
    """
    name = getattr(axis, 'name', axis)
    if name == 'AREA':
        x1, y1, x2, y2 = box
        return max(0.0, x2 - x1) * max(0.0, y2 - y1)
    cx, cy = _center(box)
    if name == 'X':
        return cx
    if name == 'Y':
        return cy
    if name == 'DIAG_UL_LR':
        return cx + cy
    if name == 'DIAG_UR_LL':
        return -cx + cy
    raise ValueError(f'unknown axis {axis!r}; expected X | Y | DIAG_UL_LR | DIAG_UR_LL | AREA')


def _auto_beta(values: np.ndarray) -> float:
    """Temperature normalised by candidate spacing so softmax separation is scale-free.

    Uses the spread of the axis values (population std, with a range fallback): beta = 1/scale
    puts the softmax exponent in "spread units", giving meaningful separation whether the boxes
    span 50 px or 5000 px. Degenerate (all-equal) -> beta 0 -> uniform scores (a genuine tie)."""
    if values.size <= 1:
        return 0.0
    scale = float(values.std())
    if scale < 1e-6:
        rng = float(values.max() - values.min())
        scale = rng if rng > 1e-6 else 0.0
    if scale < 1e-6:
        return 0.0
    return 1.0 / scale


def extremal_scores(boxes: Sequence[Box], axis: str, maximize: bool,
                    beta: float = None) -> np.ndarray:
    """Softmax extremal score per candidate along `axis`.

    maximize=True  -> argmax direction (most positive axis value scores highest), e.g. the
                      rightmost box for axis=X / the lowest box for axis=Y.
    maximize=False -> argmin direction (most negative, e.g. the leftmost / topmost).
    beta=None      -> auto from candidate spacing (_auto_beta). Pass a float to override.

    Returns a probability vector (sums to 1) over the candidates. Empty -> empty; single
    candidate -> [1.0] (trivially the extremum). The scores are RELATIVE to the candidate
    set — adding/removing a candidate changes them, by design (INGRESS referent-vs-set)."""
    n = len(boxes)
    if n == 0:
        return np.zeros(0, dtype=np.float32)
    if n == 1:
        return np.ones(1, dtype=np.float32)

    values = np.array([axis_value(b, axis) for b in boxes], dtype=np.float64)
    if beta is None:
        beta = _auto_beta(values)
    sign = 1.0 if maximize else -1.0
    logits = sign * beta * values
    logits -= logits.max()                 # numerical stability
    exp = np.exp(logits)
    out = exp / exp.sum()
    return out.astype(np.float32)


def rank_by_axis(boxes: Sequence[Box], axis: str, maximize: bool) -> List[int]:
    """Indices of `boxes` ordered from most-extreme to least along `axis` (for nth/sort).
    Deterministic tie-break by original index. maximize mirrors extremal_scores."""
    order = sorted(range(len(boxes)),
                   key=lambda i: (axis_value(boxes[i], axis), -i),
                   reverse=maximize)
    return order

"""Anchor-relative BANDED kernel — the relative-position core.

"The left one" is NOT "leftmost": it means a candidate sitting at the *typical left offset*
of the anchor, with the score decaying on BOTH sides — not a monotone ramp that always rewards
the most extreme box (V1's failure mode on selection ambiguity). The banded kernel is a dense
2-D Gaussian field peaked at a typical offset from the anchor centre:

    B_left(x, y; A) = exp( -((x - (cx_A - d0_x))^2 + (y - cy_A)^2) / (2 * sigma_b^2) )
        d0   = typical offset  (init 1.0 * anchor extent)   [tunable, needs calibration]
        sigma_b = bandwidth    (init 0.5 * anchor extent)   [tunable]

It returns an (H, W) field, so it plugs into the SAME score_boxes path as the V1 monotone /
near / center fields — only the field shape differs. Used for filter(..., BANDED). The offset
is taken along the predicate's cardinal/diagonal direction; `center` degenerates to a Gaussian
blob at the anchor centre (d0 = 0).

d0/sigma_b default to fractions of the anchor's own size (anisotropic: x by width, y by
height) so "near the left of a runway" and "near the left of a building" both scale correctly.
These are the parameters calibrated empirically on RRSIS-D val.

Pure numpy; no model/GPU.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np

Box = Tuple[float, float, float, float]

# Canonical V1 predicate string -> unit offset (sx, sy) of the band peak from the anchor centre.
# +sx = east/right (larger x); +sy = south/down (larger y). Matches predicates.py conventions.
BANDED_OFFSETS = {
    'west': (-1.0, 0.0), 'east': (1.0, 0.0),
    'north': (0.0, -1.0), 'south': (0.0, 1.0),
    'northwest': (-1.0, -1.0), 'northeast': (1.0, -1.0),
    'southwest': (-1.0, 1.0), 'southeast': (1.0, 1.0),
    'center': (0.0, 0.0),
}


def _center(box: Box) -> Tuple[float, float]:
    x1, y1, x2, y2 = box
    return 0.5 * (x1 + x2), 0.5 * (y1 + y2)


def _extent(box: Box) -> Tuple[float, float]:
    x1, y1, x2, y2 = box
    return max(abs(x2 - x1), 1.0), max(abs(y2 - y1), 1.0)


def banded_prior(anchor_box: Box, image_hw: Tuple[int, int], predicate: str,
                 d0_frac: float = 1.0, sigma_frac: float = 0.5) -> np.ndarray:
    """Dense (H, W) banded field for `predicate` relative to `anchor_box`.

    predicate: a canonical V1 predicate string (use Pred.value): west/east/north/south,
        the four diagonals, or center. ('near' is NOT banded — it has its own adaptive field
        in geogrounder.reasoning.fuzzy; pass it through MONOTONE instead.)
    d0_frac:   peak offset as a fraction of the anchor extent (x by width, y by height).
    sigma_frac: band width as a fraction of the (mean) anchor extent.

    Returns float32 in [0, 1], peaking 1.0 at the band centre. Reuse via score_boxes(prior).
    """
    pred = str(predicate).strip().lower()
    if pred not in BANDED_OFFSETS:
        raise ValueError(
            f'banded kernel undefined for predicate {predicate!r}; expected one of '
            f'{sorted(BANDED_OFFSETS)} (near uses the adaptive fuzzy field, not banded)')

    H, W = image_hw
    cx, cy = _center(anchor_box)
    w, h = _extent(anchor_box)
    sx, sy = BANDED_OFFSETS[pred]

    px = cx + sx * d0_frac * w          # band-peak centre
    py = cy + sy * d0_frac * h
    sigma_b = max(sigma_frac * 0.5 * (w + h), 1e-6)

    yy, xx = np.mgrid[0:H, 0:W]
    d2 = (xx - px) ** 2 + (yy - py) ** 2
    prior = np.exp(-d2 / (2.0 * sigma_b * sigma_b))
    return prior.astype(np.float32)

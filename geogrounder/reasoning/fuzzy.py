"""Fuzzy / vague spatial relations -> context-adaptive priors.

"near" has no hard boundary; its scale must adapt to the anchor's size (a building and a
runway have very different "near"). We set the characteristic length L = scale * anchor_size
(default scale 1.5, per the design doc) and decay the prior with distance-to-anchor.

distance-to-box d(p): 0 inside the box, else Euclidean distance to the nearest box edge.
"""

import numpy as np

from .predicates import box_size


def _distance_to_box(anchor_box, image_hw):
    H, W = image_hw
    x1, y1, x2, y2 = anchor_box
    yy, xx = np.mgrid[0:H, 0:W]
    yy = yy.astype(np.float32)
    xx = xx.astype(np.float32)
    dx = np.maximum.reduce([x1 - xx, np.zeros_like(xx), xx - x2])
    dy = np.maximum.reduce([y1 - yy, np.zeros_like(yy), yy - y2])
    return np.sqrt(dx * dx + dy * dy)


def near_prior(anchor_box, image_hw, scale=1.5, mode='gaussian'):
    """Adaptive 'near' prior. L = scale * mean(anchor_w, anchor_h)."""
    w, h = box_size(anchor_box)
    anchor_size = max(0.5 * (w + h), 1.0)
    L = max(scale * anchor_size, 1e-6)

    d = _distance_to_box(anchor_box, image_hw)
    if mode == 'gaussian':
        prior = np.exp(-(d * d) / (2.0 * L * L))
    elif mode == 'hard':
        prior = (d <= L).astype(np.float32)
    else:
        raise ValueError(f"mode must be 'gaussian' or 'hard', got {mode!r}")
    return prior.astype(np.float32)

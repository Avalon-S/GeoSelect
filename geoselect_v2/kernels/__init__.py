"""Spatial kernels — the dual-kernel core.

V2 NEW kernels:
    extremal.py   frame-relative extremal kernel — softmax over the CANDIDATE set ("leftmost")
    banded.py     anchor-relative banded kernel — dense field peaked at a typical offset
                  from the anchor, decaying both sides ("the left one")

REUSED V1 kernels live in the sibling `geogrounder` package (not re-copied, to preserve the
fallback lower bound):
    geogrounder.reasoning.predicates  -> monotone cardinal/diagonal/center fields  (MONOTONE)
    geogrounder.reasoning.fuzzy       -> adaptive `near` field
    geogrounder.reasoning.compose     -> size_scores (sigma_LARGER/SMALLER/SIMILAR)

The kernel a directional predicate uses is chosen by the DSL KernelMode:
    EXTREMAL -> extremal.py   (argmax/argmin terminal extremum)
    BANDED   -> banded.py     (filter(..., BANDED))
    MONOTONE -> geogrounder   (V1 backward-compatible half-plane ramp)
"""

from .extremal import extremal_scores, axis_value
from .banded import banded_prior, BANDED_OFFSETS

__all__ = ['extremal_scores', 'axis_value', 'banded_prior', 'BANDED_OFFSETS']

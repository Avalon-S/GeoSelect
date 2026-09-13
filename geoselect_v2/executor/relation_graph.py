"""Candidate relation graph + higher-order relation scoring.

`relate(expr, anchor, rel)` scores each candidate by a relation to anchor object(s) computed
on the candidate relation graph — nodes are candidate/anchor boxes, edges carry relative
geometry (direction, distance, containment). This is the NS3D-style higher-order side of the
hybrid executor: relations that a single dense field cannot express, notably `between` (a
binary relation needing two anchors).

All relations return a per-candidate score in [0, 1] (1 = relation fully satisfied), so they
combine multiplicatively with the dense-field scores exactly like filter does. Multi-instance
anchors are marginalised by MAX (the candidate satisfies the relation w.r.t. ANY anchor — same
spirit as V1's anchor OR-marginalisation, but over discrete relation edges).

Pure math/numpy; no model/GPU.
"""

from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

Box = Tuple[float, float, float, float]


# --- box geometry primitives --------------------------------------------------------------

def center(b: Box) -> Tuple[float, float]:
    return 0.5 * (b[0] + b[2]), 0.5 * (b[1] + b[3])


def extent(b: Box) -> Tuple[float, float]:
    return max(abs(b[2] - b[0]), 1.0), max(abs(b[3] - b[1]), 1.0)


def area(b: Box) -> float:
    return max((b[2] - b[0]) * (b[3] - b[1]), 1.0)


def char_len(b: Box) -> float:
    """Characteristic length of a box = mean of width and height."""
    w, h = extent(b)
    return 0.5 * (w + h)


def box_gap(a: Box, b: Box) -> float:
    """Euclidean gap between two axis-aligned rectangles; 0 if they overlap/touch."""
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def intersection_area(a: Box, b: Box) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    return ix * iy


# --- unary-anchor relations ---------------------------------------------------------------

def score_near(cand: Box, anchor: Box, scale: float = 1.5) -> float:
    """Proximity: Gaussian in the box gap, characteristic length L = scale * anchor char_len
    (mirrors geogrounder.reasoning.fuzzy.near_prior, but box-to-box on the relation graph)."""
    L = max(scale * char_len(anchor), 1e-6)
    d = box_gap(cand, anchor)
    return math.exp(-(d * d) / (2.0 * L * L))


def score_adjacent(cand: Box, anchor: Box) -> float:
    """Adjacency: high only when the boxes nearly abut. Tighter than `near` — characteristic
    length is a small fraction of the anchor size, so a far-but-'near' box scores low."""
    L = max(0.25 * char_len(anchor), 1e-6)
    d = box_gap(cand, anchor)
    return math.exp(-(d * d) / (2.0 * L * L))


def score_contains(cand: Box, anchor: Box) -> float:
    """Containment: fraction of the ANCHOR that lies inside the candidate (cand CONTAINS anchor)."""
    return intersection_area(cand, anchor) / area(anchor)


def score_inside(cand: Box, anchor: Box) -> float:
    """Inverse containment: fraction of the CANDIDATE inside the anchor (cand INSIDE anchor)."""
    return intersection_area(cand, anchor) / area(cand)


# --- binary-anchor relation: between ------------------------------------------------------

def score_between(cand: Box, anchor_a: Box, anchor_b: Box) -> float:
    """`cand` is between anchor_a and anchor_b: its centre projects onto the A->B segment with
    parameter t in [0,1] (betweenness) AND lies close to that line (alignment).

        t  = proj of (c - a) onto (b - a) / |b - a|^2
        score = t_in_segment * exp(-perp^2 / (2 * sigma^2))
        sigma = 0.35 * |b - a| + candidate char_len   (tolerate off-axis by candidate size)

    t outside [0,1] decays the score (a box beyond an endpoint is not 'between')."""
    ax, ay = center(anchor_a)
    bx, by = center(anchor_b)
    cx, cy = center(cand)
    abx, aby = bx - ax, by - ay
    ab2 = abx * abx + aby * aby
    if ab2 < 1e-6:                       # degenerate: anchors coincide -> fall back to proximity
        return score_near(cand, anchor_a)
    t = ((cx - ax) * abx + (cy - ay) * aby) / ab2
    # perpendicular distance from c to the infinite A-B line
    proj_x, proj_y = ax + t * abx, ay + t * aby
    perp = math.hypot(cx - proj_x, cy - proj_y)
    sigma = 0.35 * math.sqrt(ab2) + char_len(cand)
    align = math.exp(-(perp * perp) / (2.0 * sigma * sigma))
    # betweenness: 1 inside [0,1], decaying outside by how far past an endpoint (in t units)
    outside = max(0.0, -t, t - 1.0)
    t_score = math.exp(-(outside * outside) / (2.0 * 0.25 * 0.25))
    return align * t_score


# --- dispatch -----------------------------------------------------------------------------

def relation_score(rel_name: str, cand: Box, anchors_a: Sequence[Box],
                   anchors_b: Optional[Sequence[Box]] = None, *, near_scale: float = 1.5) -> float:
    """Score `cand` for relation `rel_name` against anchor instance(s). MAX-marginalised over
    anchor instances (the candidate satisfies the relation w.r.t. ANY anchor). `rel_name` is
    the Rel enum NAME (e.g. 'NEAR', 'BETWEEN') or its lowercase value.

    BETWEEN needs anchors_b (the second anchor); the others ignore it. Returns 0 if the needed
    anchors are missing (caller treats a 0 like an unsatisfiable constraint)."""
    name = getattr(rel_name, 'name', str(rel_name)).upper()
    if not anchors_a:
        return 0.0

    if name == 'BETWEEN':
        if not anchors_b:
            return 0.0
        return max(score_between(cand, a, b) for a in anchors_a for b in anchors_b)

    if name == 'NEAR':
        return max(score_near(cand, a, scale=near_scale) for a in anchors_a)
    if name == 'ADJACENT':
        return max(score_adjacent(cand, a) for a in anchors_a)
    if name == 'CONTAINS':
        return max(score_contains(cand, a) for a in anchors_a)
    if name == 'INSIDE':
        return max(score_inside(cand, a) for a in anchors_a)

    raise ValueError(f'unknown relation {rel_name!r}')

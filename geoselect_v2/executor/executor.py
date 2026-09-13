"""Recursive AST interpreter — the hybrid executor.

Each expr evaluates to a scored candidate set `List[(box_xyxy, score)]`. The terminal step
takes argmax(score) (single) or union(score > tau*max) (group), each fed to SAM.

With `filter` on the MONOTONE kernel, a single filter-chain + AND/OR is BIT-EQUIVALENT to
V1 (geogrounder.reasoning.SpatialReasoner) under the headline config (score_method='centroid'):

  - select(type)            -> every detected box of that type, score 1.0
  - filter(child,pred,A,KM) -> child scores * dense-prior score against anchor A
  - and/or/not              -> fuzzy min / max / complement of scores
  - argmax/argmin/nth/restrict_count/relate -> NotImplementedError (later steps)

Why AND stays V1-equivalent: V1 ANDs the dense FIELDS then scores once; V2 scores each filter
then mins. With centroid scoring (sample the prior at the box centre) the two are identical —
min(f1,f2) sampled at c == min(f1(c), f2(c)). The headline V1 config uses centroid, so the
equivalence is exact; only score_method='mean' (an ablation) would differ. See test_executor.py.

The dense fields, anchor marginalisation and box scoring are REUSED verbatim from V1
(geogrounder.reasoning.compose) — no reimplementation, so the fallback lower bound is preserved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np

from geogrounder.reasoning.compose import build_prior, score_boxes, prior_or

from ..kernels import banded_prior, extremal_scores
from ..kernels.extremal import rank_by_axis
from .relation_graph import relation_score
from ..parser.grammar import (
    Node, Select, Filter, Argmax, Argmin, Nth, RestrictCount, Relate, And, Or, Not,
    KernelMode, Pred, Rel, IMAGE,
)

Box = Tuple[float, float, float, float]
Scored = List[Tuple[Box, float]]


class ExecError(RuntimeError):
    """Raised when execution hits an unrecoverable state.
    The reliability layer catches this and falls back to V1."""


@dataclass
class ExecContext:
    """Per-image execution context. `detections` is {class_name: [box_xyxy, ...]} exactly as
    DetectionResponse.by_label() emits — the SAME contract V1's reasoner consumes.

    Kernel / scoring knobs mirror geogrounder.reasoning.SpatialReasoner defaults so the
    MONOTONE path reproduces the V1 headline numbers verbatim."""
    detections: Dict[str, List[Box]]
    image_hw: Tuple[int, int]                 # (H, W)
    # --- knobs (V1 headline defaults) ---
    near_scale: float = 1.5
    reference: str = 'centroid'               # half-plane boundary: 'centroid' | 'edge'
    graded_direction: bool = True             # MONOTONE ramp (furthest-in-direction wins)
    score_method: str = 'centroid'            # 'centroid' (V1 headline) | 'mean' | 'max'
    direction_exponent: float = 1.0
    center_sigma_frac: float = 0.25
    anchor_mode: str = 'marginalize'          # 'marginalize' (OR over anchor instances) | 'first'
    # banded kernel — peak offset / bandwidth as fractions of anchor extent.
    banded_d0_frac: float = 1.0
    banded_sigma_frac: float = 0.5
    # extremal kernel — softmax temperature; None = auto from candidate spacing.
    extremal_beta: float = None

    def full_image_box(self) -> Box:
        H, W = self.image_hw
        return (0.0, 0.0, float(W), float(H))


class Executor:
    """Recursive DSL interpreter. Stateless apart from the ExecContext passed to execute()."""

    def execute(self, node: Node, ctx: ExecContext) -> Scored:
        """Evaluate `node` -> scored candidate set. Dispatch on node type. If ctx carries a
        `trace` list (set externally for visualization), append (op_name, node, scored-copy)
        after each node in post-order — leaves first — without affecting the result."""
        result = self._dispatch(node, ctx)
        tr = getattr(ctx, 'trace', None)
        if tr is not None:
            tr.append((type(node).__name__, node, list(result)))
        return result

    def _dispatch(self, node: Node, ctx: ExecContext) -> Scored:
        if isinstance(node, Select):
            return self._select(node, ctx)
        if isinstance(node, Filter):
            return self._filter(node, ctx)
        if isinstance(node, (And, Or, Not)):
            return self._setop(node, ctx)
        if isinstance(node, (Argmax, Argmin)):
            return self._argextremum(node, ctx)
        if isinstance(node, Nth):
            return self._nth(node, ctx)
        if isinstance(node, RestrictCount):
            return self._restrict_count(node, ctx)
        if isinstance(node, Relate):
            return self._relate(node, ctx)
        raise ExecError(f'unhandled node type {type(node).__name__}')

    # --- leaves / unary -------------------------------------------------------------------

    def _select(self, node: Select, ctx: ExecContext) -> Scored:
        boxes = list(ctx.detections.get(node.type, []))
        return [(tuple(b), 1.0) for b in boxes]

    def _filter(self, node: Filter, ctx: ExecContext) -> Scored:
        scored = self.execute(node.child, ctx)
        if not scored:
            return []
        if node.kernel_mode is KernelMode.EXTREMAL:
            # An EXTREMAL filter is a frame-relative extremum with no anchor — it is the
            # argmax/argmin op in disguise. Route callers to argmax/argmin instead so the
            # candidate-set softmax (extremal kernel) is applied, not a dense field.
            raise ExecError("filter(..., EXTREMAL) is ill-formed; use argmax/argmin for "
                            "frame-relative extrema")

        anchor_boxes = self._resolve_anchor(node.anchor, ctx)
        if not anchor_boxes:
            # Anchor class absent -> V1 drops this relation (no constraint). Mirror that:
            # the filter contributes no score change, child scores pass through.
            return scored

        prior = self._field(node, anchor_boxes, ctx)
        boxes = [b for b, _ in scored]
        pscores = score_boxes(boxes, prior, method=ctx.score_method)
        return [(b, s * float(ps)) for (b, s), ps in zip(scored, pscores)]

    def _field(self, node: Filter, anchor_boxes: List[Box], ctx: ExecContext) -> np.ndarray:
        """Dense (H, W) field for a filter, marginalised (OR) over anchor instances.

        BANDED  -> anchor-relative band (kernels.banded); `near` has no band, fall through.
        MONOTONE-> V1 half-plane ramp / center / near (geogrounder.build_prior), reused verbatim.
        """
        if node.kernel_mode is KernelMode.BANDED and node.pred is not Pred.NEAR:
            fields = [banded_prior(ab, ctx.image_hw, node.pred.value,
                                   d0_frac=ctx.banded_d0_frac,
                                   sigma_frac=ctx.banded_sigma_frac)
                      for ab in anchor_boxes]
        else:
            fields = [build_prior(node.pred.value, ab, ctx.image_hw,
                                  near_scale=ctx.near_scale,
                                  reference=ctx.reference,
                                  soft=False,
                                  graded=ctx.graded_direction,
                                  direction_exponent=ctx.direction_exponent,
                                  center_sigma_frac=ctx.center_sigma_frac)
                      for ab in anchor_boxes]
        return fields[0] if len(fields) == 1 else prior_or(*fields)

    def _argextremum(self, node: Node, ctx: ExecContext) -> Scored:
        """argmax/argmin via the EXTREMAL kernel.

        Semantics: the upstream filter/restrict_count defines the candidate SET; the
        extremal kernel then decides the extremum WITHIN it. So we RESCORE (replace, not
        multiply) — multiplying by the incoming score corrupts the superlative (e.g. "rightmost
        of the LEFT ships" would be penalised exactly for being rightmost). The incoming score
        acts only as set membership: candidates a prior filter scored to 0 are out of the set.
        If every incoming score is 0 (no filter, or all on a boundary), the whole set is live."""
        scored = self.execute(node.child, ctx)
        if not scored:
            return []
        live = [(b, s) for b, s in scored if s > 0.0]
        if not live:
            live = list(scored)              # nothing filtered in -> rank the full set
        boxes = [b for b, _ in live]
        maximize = isinstance(node, Argmax)
        ex = extremal_scores(boxes, node.axis.name, maximize=maximize, beta=ctx.extremal_beta)
        return [(b, float(e)) for (b, _), e in zip(live, ex)]

    def _nth(self, node: Nth, ctx: ExecContext) -> Scored:
        """nth(child, n, axis): ordinal — sort the child candidates along `axis` in reading
        order (ascending: left->right for X, top->bottom for Y) and return the n-th (0-based),
        keeping its incoming score. Out of range -> [] (a legitimate empty result; the
        reliability layer may then fall back)."""
        scored = self.execute(node.child, ctx)
        if not scored:
            return []
        boxes = [b for b, _ in scored]
        order = rank_by_axis(boxes, node.axis.name, maximize=False)   # ascending = reading order
        if not (0 <= node.n < len(order)):
            return []
        return [scored[order[node.n]]]

    def _restrict_count(self, node: RestrictCount, ctx: ExecContext) -> Scored:
        """restrict_count(child, k): group/counting constraint — keep the k highest-scored
        candidates. This narrows a set to a k-sized group that a downstream
        argmax/filter then operates on ("the three ships on the left", "the larger of the two").
        k >= len(child) returns all. Stable: ties keep original order. Reuses V1's cardinality
        intent without re-clustering — clustering can replace top-k later if dense scenes need it."""
        scored = self.execute(node.child, ctx)
        if node.k >= len(scored):
            return scored
        # indices of the k highest scores, stable on ties (original order preserved)
        order = sorted(range(len(scored)), key=lambda i: (-scored[i][1], i))
        keep = sorted(order[:node.k])
        return [scored[i] for i in keep]

    def _relate(self, node: Relate, ctx: ExecContext) -> Scored:
        """relate(child, rel, anchor[, anchor2]): score each child candidate by a higher-order
        relation on the candidate relation graph (relation_graph.relation_score), multiplied
        into the incoming score. BETWEEN is binary and uses anchor2 (typecheck guarantees it).

        A missing anchor -> relation_score returns 0 -> candidates are zeroed (unsatisfiable
        constraint), matching the discrete relation semantics (cf. filter's pass-through, which
        is for soft dense fields; a relation to an absent object is genuinely unsatisfied)."""
        scored = self.execute(node.child, ctx)
        if not scored:
            return []
        anchors_a = self._resolve_anchor(node.anchor, ctx)
        if node.rel in (Rel.SMALLER, Rel.LARGER):
            return self._relate_size(node.rel, scored, anchors_a)
        anchors_b = (self._resolve_anchor(node.anchor2, ctx)
                     if node.anchor2 is not None else None)
        return [(b, s * relation_score(node.rel.name, b, anchors_a, anchors_b,
                                       near_scale=ctx.near_scale))
                for b, s in scored]

    @staticmethod
    def _box_area(b) -> float:
        return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])

    def _relate_size(self, rel, scored, anchors) -> Scored:
        """COMPARATIVE-SIZE relation ("A smaller/larger than the anchor"). The referent is the
        candidate that is smaller/larger than the anchor by BOX AREA. We exclude the anchor box(es)
        (the referent is a DIFFERENT instance) and rank the remaining candidates by area — smallest
        first for SMALLER, largest first for LARGER — normalised to [0, 1] over the set, multiplied
        into the incoming score. argmax then returns the extreme-area other instance, reproducing
        the deterministic area comparison the detector cannot perform."""
        larger = rel is Rel.LARGER
        akeys = {self._key(a) for a in anchors}
        cand = [(b, s) for b, s in scored if self._key(b) not in akeys]
        if not cand:                       # anchor coincides with the only candidate -> rank all
            cand = list(scored)
        areas = [self._box_area(b) for b, _ in cand]
        amin, amax = min(areas), max(areas)
        rng = (amax - amin) or 1.0
        out: Scored = []
        for (b, s), ar in zip(cand, areas):
            v = (ar - amin) / rng if larger else (amax - ar) / rng
            out.append((b, s * v))
        return out

    # --- set ops --------------------------------------------------------------------------

    def _setop(self, node: Node, ctx: ExecContext) -> Scored:
        """Fuzzy AND/OR/NOT over scored candidate sets, keyed by box identity.

        AND = min, OR = max, NOT = 1 - score. Boxes are matched across branches by rounded
        coordinates (detections are shared, so identical instances align exactly)."""
        if isinstance(node, Not):
            return [(b, 1.0 - s) for b, s in self.execute(node.child, ctx)]

        left = self.execute(node.left, ctx)
        right = self.execute(node.right, ctx)
        lmap = {self._key(b): (b, s) for b, s in left}
        rmap = {self._key(b): s for b, s in right}

        out: Scored = []
        if isinstance(node, And):
            for k, (b, s) in lmap.items():
                if k in rmap:
                    out.append((b, min(s, rmap[k])))
        else:  # Or — union of boxes, max score; right-only boxes carried over
            seen = set()
            for b, s in left:
                k = self._key(b)
                seen.add(k)
                out.append((b, max(s, rmap.get(k, 0.0))))
            for b, s in right:
                if self._key(b) not in seen:
                    out.append((b, s))
        return out

    # --- anchor resolution ----------------------------------------------------------------

    def _resolve_anchor(self, anchor, ctx: ExecContext) -> List[Box]:
        """Anchor -> list of anchor boxes (matching V1's nested-vs-flat anchor semantics).

        IMAGE                 -> [full-image frame].
        bare select(...)      -> ALL detected instances (marginalise: OR the per-anchor fields,
                                 reproducing V1 anchor_mode='marginalize' for "left of the stadium"
                                 when several stadiums exist).
        CONSTRAINED expr      -> top-1 only. "the field on the TOP" names ONE object; resolving it
                                 to all instances (the previous behaviour) built the directional
                                 field relative to EVERY field and mis-selected on same-class
                                 nested anchors — the RRSIS-D compositional regression. V1 resolves
                                 a nested anchor to its top-1, so we match that.
        anchor_mode='first'   -> always top-1 (V1 legacy)."""
        if anchor is IMAGE:
            return [ctx.full_image_box()]
        scored = self.execute(anchor, ctx)
        if not scored:
            return []
        bare_select = isinstance(anchor, Select)
        if ctx.anchor_mode != 'first' and bare_select:
            return [b for b, _ in scored]               # marginalise over instances
        best = max(scored, key=lambda bs: bs[1])         # constrained anchor -> the one it names
        return [best[0]]

    @staticmethod
    def _key(box: Box) -> Tuple[int, int, int, int]:
        return tuple(int(round(c)) for c in box)


# --- terminal selection -------------------------------------------

def select_single(scored: Scored) -> Scored:
    """single cardinality -> the argmax-score candidate (as a 1-element ranked list)."""
    if not scored:
        return []
    return [max(scored, key=lambda bs: bs[1])]


def select_group(scored: Scored, tau: float = 0.8) -> Scored:
    """group cardinality -> every candidate with score > tau * max(score)."""
    if not scored:
        return []
    smax = max(s for _, s in scored)
    if smax <= 0:
        return list(scored)
    return [(b, s) for b, s in scored if s > tau * smax]


def rank(scored: Scored) -> Scored:
    """Descending-by-score ranked list (drop-in for V1 resolve()['ranked'])."""
    return sorted(scored, key=lambda bs: -bs[1])

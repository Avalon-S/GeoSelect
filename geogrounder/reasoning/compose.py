"""Composition of spatial priors + candidate scoring + relation resolution.

Combines per-predicate priors (AND/OR), scores detected target candidates against the
combined prior, and resolves nested + image-relative relations.

Relation schema (the CONTRACT that parsing/qwen_parser.py must emit):

    {
      "target": "<target class/name>",
      "logic": "and" | "or",                 # combine multiple relations (default "and")
      "relations": [
        {
          "predicate": "<north|south|east|west|left|right|above|below|"
                       "northeast|northwest|southeast|southwest|"
                       "upper left|lower right|...|center|middle|near>",
          "anchor": "image"                   # image-relative ("on the right" = right of image)
                    | "<anchor class>"        # object-relative ("left of the stadium")
                    | <nested relation dict>  # recursive
        },
        ...
      ]
    }

RRSIS-D is image-relative dominant, so `anchor: "image"` is the common case (the prior is
built against the whole-image box). `detections` is {class_name: [box_xyxy, ...]}.
"""

import numpy as np

from .predicates import (direction_prior, center_prior, normalize_predicate,
                         normalize_size_predicate, CARDINALS, DIAGONALS)
from .fuzzy import near_prior

_IMAGE_ANCHORS = {'image', 'frame', 'scene', 'whole image', 'the image', ''}


def prior_and(*priors):
    return np.minimum.reduce(list(priors)).astype(np.float32)


def prior_or(*priors):
    return np.maximum.reduce(list(priors)).astype(np.float32)


def prior_combine_and(priors, op='min'):
    """AND-combine per-predicate priors with a selectable t-norm (composition-operator
    ablation; flag-gated, default 'min' = the frozen reported pipeline).

    'min'     : Goedel t-norm (FROZEN). Non-compensatory — the combined prior is gated by the
                WEAKEST satisfied constraint; a candidate strong on one predicate but weak on
                another cannot recover. This is the reported headline behaviour.
    'product' : product t-norm. Partially compensatory — strength on one constraint can offset a
                near-miss on another (fields multiply).
    'mean'    : arithmetic mean. Fully compensatory (NOT a t-norm; the opposite extreme of 'min',
                included so the ablation brackets the compensation axis).
    Single-field input reduces to that field for every op, so 1-predicate expressions are
    bit-identical across ops; only multi-constraint (>=2 AND-ed predicates) expressions differ."""
    arr = [p.astype(np.float32) for p in priors]
    if len(arr) == 1:
        return arr[0]
    if op == 'product':
        out = arr[0].copy()
        for p in arr[1:]:
            out = out * p
        return out.astype(np.float32)
    if op == 'mean':
        return np.mean(np.stack(arr, axis=0), axis=0).astype(np.float32)
    return np.minimum.reduce(arr).astype(np.float32)   # 'min' (frozen default)


def score_boxes(boxes, prior, method='mean'):
    """Score each xyxy box against the prior. Returns float array.

    method='mean' : average prior over the box region (v2 default). NOTE: this DILUTES large/elongated
        boxes — a big central object scores lower than a tiny box sitting on the prior peak, which
        systematically mis-ranks 'the <big object> in the middle' (the dominant image-relative error).
    method='centroid' : sample the prior at the box CENTRE. "most-central / furthest-in-direction"
        semantics independent of box size — fixes the large-object dilution above.
    """
    H, W = prior.shape
    scores = []
    for b in boxes:
        x1, y1, x2, y2 = b
        if method == 'centroid':
            cx = min(max(int(round(0.5 * (x1 + x2))), 0), W - 1)
            cy = min(max(int(round(0.5 * (y1 + y2))), 0), H - 1)
            scores.append(float(prior[cy, cx]))
            continue
        xi1, yi1 = int(np.floor(x1)), int(np.floor(y1))
        xi2, yi2 = int(np.ceil(x2)), int(np.ceil(y2))
        xi1, xi2 = max(0, xi1), min(W, xi2)
        yi1, yi2 = max(0, yi1), min(H, yi2)
        region = prior[yi1:yi2, xi1:xi2]
        if region.size == 0:
            cx = min(max(int(0.5 * (x1 + x2)), 0), W - 1)
            cy = min(max(int(0.5 * (y1 + y2)), 0), H - 1)
            scores.append(float(prior[cy, cx]))
        elif method == 'max':
            scores.append(float(region.max()))
        else:
            scores.append(float(region.mean()))
    return np.array(scores, dtype=np.float32)


def build_prior(predicate, anchor_box, image_hw, *, near_scale=1.5,
                reference='centroid', soft=False, graded=False,
                direction_exponent=1.0, center_sigma_frac=0.25):
    """Dispatch a (possibly diagonal/center) predicate to a dense prior.

    graded=True makes directional priors monotonic ramps (the candidate furthest in the
    direction wins) — used for multi-candidate selection; near/center are already graded.
    direction_exponent / center_sigma_frac: shape-sharpness knobs added after
    selector-headroom attribution found `center`(53) + `right/left/below`(60+) dominate
    failures by ties between near-extreme candidates (predicates.py exponent docstring).
    Defaults = backward-compatible (1.0 linear ramp, 0.25 Gaussian sigma frac).
    """
    pred = normalize_predicate(predicate)
    if pred == 'near':
        return near_prior(anchor_box, image_hw, scale=near_scale)
    if pred == 'center':
        return center_prior(anchor_box, image_hw, frac=center_sigma_frac)
    if pred in CARDINALS:
        return direction_prior(anchor_box, image_hw, pred, reference=reference,
                               soft=soft, graded=graded, exponent=direction_exponent)
    if pred in DIAGONALS:
        a, b = DIAGONALS[pred]
        return prior_and(
            direction_prior(anchor_box, image_hw, a, reference=reference, soft=soft,
                            graded=graded, exponent=direction_exponent),
            direction_prior(anchor_box, image_hw, b, reference=reference, soft=soft,
                            graded=graded, exponent=direction_exponent))
    raise ValueError(f'unhandled predicate {predicate!r} -> {pred!r}')


def _box_close(a, b, tol=1.0):
    """True if two xyxy boxes are the same detected instance (<= tol px on every coord).
    Used for same-class anchor exclusion (a target box that IS the resolved anchor)."""
    try:
        return all(abs(float(a[i]) - float(b[i])) <= tol for i in range(4))
    except (TypeError, IndexError):
        return False


def _box_area(b):
    return max(1.0, (float(b[2]) - float(b[0])) * (float(b[3]) - float(b[1])))


def size_scores(boxes, anchor_area, kind):
    """Per-candidate comparative-SIZE score in (0, 1] vs the anchor box area (NOT a pixel prior).

    'larger'  -> area/(area+A): >0.5 iff bigger than the anchor, monotonically up with size.
    'smaller' -> A/(area+A):    >0.5 iff smaller than the anchor, monotonically up as size drops.
    'similar' -> min/max ratio: =1 at equal area, ->0 as the sizes diverge (closest-in-size wins).
    Soft ramps (no hard threshold) — annotation/detection area is noisy, so we rank rather than
    gate. Combined multiplicatively with the spatial score in resolve() (AND semantics)."""
    A = max(1.0, float(anchor_area))
    areas = np.array([_box_area(b) for b in boxes], dtype=np.float32)
    if kind == 'larger':
        return areas / (areas + A)
    if kind == 'smaller':
        return A / (areas + A)
    if kind == 'similar':
        return np.minimum(areas, A) / np.maximum(areas, A)
    raise ValueError(f'unhandled size predicate {kind!r}')


class SpatialReasoner:
    """Resolve a structured relation against detected candidates via explicit geometry."""

    def __init__(self, near_scale=1.5, reference='centroid', soft_direction=False,
                 graded_direction=True, score_method='centroid',
                 direction_exponent=1.0, center_sigma_frac=0.25, anchor_mode='first',
                 size_predicate=True, compose_op='min'):
        self.near_scale = near_scale
        self.reference = reference
        self.soft_direction = soft_direction
        # graded_direction: rank multi-candidate selection by how FAR in the direction (default on);
        # set False for the hard half-plane (region viz / the v1 behavior).
        self.graded_direction = graded_direction
        # score_method: 'centroid' (v3a DEFAULT, validated +1.4 mIoU/+3.8 oIoU on val) samples prior
        # at the box centre — size-independent, fixes 'big object in the middle' mis-ranking.
        # 'mean' (v2) pools prior over the box and dilutes large central boxes — kept for the ablation.
        self.score_method = score_method
        # Predicate sharpening (selector-headroom diagnostic): tighter Gaussian for
        # `center` + steeper ramp for `right/left/above/below/diagonals` to break ties between
        # near-extreme candidates. Defaults = original behaviour.
        self.direction_exponent = direction_exponent
        self.center_sigma_frac = center_sigma_frac
        # anchor_mode: 'first' = boxes[0], one arbitrary anchor instance when the anchor
        # class has several detections; 'marginalize' = OR/max the predicate field over ALL
        # detected anchor instances (the target satisfies the relation w.r.t. ANY anchor).
        # 'first' is kept to reproduce the frozen headline and as the ablation.
        self.anchor_mode = anchor_mode
        # size_predicate: enable comparative-SIZE relations ('larger'/'smaller'/
        # 'similar'). True = score candidates by box-area vs the anchor area (size_scores) and
        # multiply into the spatial score. False = skip size relations entirely (ablation: shows
        # the size scorer's isolated effect on the SAME size-aware parse). No-op when the parse
        # contains no size predicate, so the frozen position-only headline is unchanged.
        self.size_predicate = size_predicate
        # compose_op (flag-gated ablation): t-norm used to AND-combine multiple
        # per-predicate priors. 'min' = frozen Goedel default (non-compensatory); 'product'/'mean'
        # relax compensation for the min/max-brittleness ablation. No-op on single-predicate
        # expressions, so the frozen headline is unchanged except where >=2 predicates AND together.
        self.compose_op = compose_op

    @staticmethod
    def _full_image_box(image_hw):
        H, W = image_hw
        return (0.0, 0.0, float(W), float(H))

    def _resolve_anchor_boxes(self, anchor, detections, image_hw):
        """Return a LIST of anchor boxes (xyxy). 'image' -> [whole-image frame]. For an object
        anchor with multiple detected instances, ALL are returned (anchor_mode='marginalize')
        so the caller can OR the per-anchor fields; anchor_mode='first' restores the legacy
        single-box boxes[0] behaviour. Empty list if the anchor class was not detected."""
        if isinstance(anchor, str):
            if anchor.strip().lower() in _IMAGE_ANCHORS:
                return [self._full_image_box(image_hw)]       # image-relative frame
            boxes = list(detections.get(anchor, []))
            if not boxes:
                return []
            return boxes[:1] if self.anchor_mode == 'first' else boxes
        if isinstance(anchor, dict):                          # nested relation -> top-1 only
            res = self.resolve(anchor, detections, image_hw)
            return [res['ranked'][0][0]] if res['ranked'] else []
        raise TypeError(f'anchor must be str or dict, got {type(anchor)}')

    def resolve(self, relation, detections, image_hw):
        """Rank target candidates. Returns dict(ranked, prior, target_boxes, scores)."""
        target_boxes = list(detections.get(relation['target'], []))
        if not target_boxes:
            return {'ranked': [], 'prior': None, 'target_boxes': [], 'scores': None}

        priors = []
        size_terms = []          # (kind, anchor_area) for comparative-size relations
        size_exclude = []        # exact size-anchor box(es) to drop ("compare to ANOTHER object")
        for rel in relation.get('relations', []):
            # Recursive grounding: a nested anchor (dict) is resolved by its OWN sub-program
            # inside _resolve_anchor_boxes -> resolve(); a flat anchor returns its detected box(es).
            anchor_boxes = self._resolve_anchor_boxes(rel['anchor'], detections, image_hw)
            if not anchor_boxes:
                continue
            # Comparative-size relation? Route to the area scorer (NOT build_prior, which only
            # handles directional predicates and would ValueError on 'larger'/'smaller'/'similar').
            size_kind = normalize_size_predicate(rel['predicate'])
            if size_kind is not None:
                if not self.size_predicate:
                    continue                 # ablation: drop size relations from the program
                # Exclude the resolved size-anchor from candidates: a target is compared to
                # ANOTHER object. Applied to all size kinds, which is the reported configuration.
                # The size claim is scoped to RRSIS-D.
                size_exclude.extend(anchor_boxes)
                anchor_area = float(np.mean([_box_area(ab) for ab in anchor_boxes]))
                size_terms.append((size_kind, anchor_area))
                continue
            # Marginalize over anchor instances: the target satisfies the relation w.r.t. ANY
            # detected anchor -> OR/max the per-anchor predicate fields. One anchor (or
            # anchor_mode='first') reduces to the legacy single-anchor field exactly.
            fields = [build_prior(rel['predicate'], ab, image_hw,
                                  near_scale=self.near_scale,
                                  reference=self.reference,
                                  soft=self.soft_direction,
                                  graded=self.graded_direction,
                                  direction_exponent=self.direction_exponent,
                                  center_sigma_frac=self.center_sigma_frac)
                      for ab in anchor_boxes]
            priors.append(fields[0] if len(fields) == 1 else prior_or(*fields))

        # Size-anchor exclusion: a comparative-size target is compared to ANOTHER object, so the
        # resolved size-anchor box cannot be the referent (critical for 'similar', where the anchor
        # would otherwise self-match with score 1.0). Scoped to size relations only: the directional
        # prior already deprioritises an anchor sitting in its own field, and a broad same-class
        # exclusion hurt directional cases. No-op without a size predicate, so the frozen headline
        # is preserved.
        if size_exclude and len(target_boxes) > 1:
            kept = [tb for tb in target_boxes
                    if not any(_box_close(tb, ab) for ab in size_exclude)]
            if kept:
                target_boxes = kept

        if not priors:
            prior = np.ones(image_hw, dtype=np.float32)  # pure-attribute / no usable constraint
        elif relation.get('logic', 'and') == 'or':
            prior = prior_or(*priors)
        else:
            prior = prior_combine_and(priors, op=self.compose_op)

        scores = score_boxes(target_boxes, prior, method=self.score_method)
        # Multiply in each comparative-size term (AND with the spatial score). When there is no
        # spatial predicate, `prior` is uniform -> scores are constant -> ranking is by size alone.
        for kind, anchor_area in size_terms:
            scores = scores * size_scores(target_boxes, anchor_area, kind)
        order = np.argsort(-scores)
        ranked = [(target_boxes[i], float(scores[i])) for i in order]
        return {'ranked': ranked, 'prior': prior,
                'target_boxes': target_boxes, 'scores': scores}

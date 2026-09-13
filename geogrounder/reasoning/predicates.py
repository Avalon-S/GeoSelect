"""Spatial predicates -> dense pixel priors (the project's moat: explicit geometry).

Conventions
-----------
- Image array shape is (H, W); a pixel is (row=y, col=x).
- Boxes are xyxy in absolute pixels: (x1, y1, x2, y2).
- north=up=smaller y; south=down; east=right=larger x; west=left.

Reference frame
---------------
The SAME half-plane logic serves both frames — only the reference box differs:
- object-relative ("left of the stadium"): pass the anchor object's box.
- image-relative  ("on the right", "in the middle"): pass the whole-image box (0,0,W,H);
  the image centroid is (W/2, H/2), so "right" -> right half, "lower left" -> bottom-left
  quadrant, "center" -> central blob. (RRSIS-D is image-relative dominant — see compose.py.)

Predicate vocabulary: 4 cardinals, 4 diagonals (= AND of two cardinals), `center`, and the
fuzzy `near` (in fuzzy.py). `normalize_predicate` maps the many phrasings an LVLM emits
("lower left", "upper-right", "middle", "to the left") onto these canonical forms.
"""

import numpy as np

CARDINALS = ('north', 'south', 'east', 'west')
DIRECTIONS = CARDINALS  # back-compat alias
DIAGONALS = {
    'northeast': ('north', 'east'),
    'northwest': ('north', 'west'),
    'southeast': ('south', 'east'),
    'southwest': ('south', 'west'),
}

# cleaned-string -> cardinal (for direction_prior's single half-plane)
_CARDINAL_ALIASES = {
    'left': 'west', 'right': 'east', 'above': 'north', 'below': 'south',
    'top': 'north', 'bottom': 'south', 'up': 'north', 'down': 'south',
    'upper': 'north', 'lower': 'south',
    'north': 'north', 'south': 'south', 'east': 'east', 'west': 'west',
}
# cleaned-string -> diagonal
_DIAGONAL_ALIASES = {
    'northeast': 'northeast', 'north east': 'northeast', 'upper right': 'northeast',
    'top right': 'northeast', 'upper east': 'northeast', 'top east': 'northeast',
    'northwest': 'northwest', 'north west': 'northwest', 'upper left': 'northwest',
    'top left': 'northwest', 'upper west': 'northwest', 'top west': 'northwest',
    'southeast': 'southeast', 'south east': 'southeast', 'lower right': 'southeast',
    'bottom right': 'southeast', 'lower east': 'southeast', 'bottom east': 'southeast',
    'southwest': 'southwest', 'south west': 'southwest', 'lower left': 'southwest',
    'bottom left': 'southwest', 'lower west': 'southwest', 'bottom west': 'southwest',
}
_CENTER_ALIASES = {'center', 'centre', 'middle', 'central', 'mid'}

# Comparative-SIZE predicates: not directional — scored per-candidate by box AREA
# vs the anchor box area (compose.size_scores), NOT a dense pixel prior. Size comparisons
# ("the bigger ship", "smaller than the ship on the left") cannot be expressed by directional
# geometry. normalize_size_predicate identifies them
# so compose can route them to the area scorer instead of build_prior (which would ValueError).
SIZE_PREDICATES = ('larger', 'smaller', 'similar')
_SIZE_ALIASES = {
    'larger': 'larger', 'bigger': 'larger', 'large': 'larger', 'big': 'larger',
    'taller': 'larger', 'wider': 'larger', 'longer': 'larger', 'huge': 'larger',
    'smaller': 'smaller', 'small': 'smaller', 'tinier': 'smaller', 'tiny': 'smaller',
    'shorter': 'smaller', 'narrower': 'smaller',
    'similar': 'similar', 'similar size': 'similar', 'same size': 'similar',
    'equal size': 'similar', 'similar in size': 'similar', 'comparable': 'similar',
}


def _clean(s):
    return ' '.join(str(s).strip().lower().replace('-', ' ').replace('_', ' ').split())


_SIZE_HEDGE_RE = None  # lazily compiled below


def normalize_size_predicate(predicate):
    """Map a comparative-size phrasing -> 'larger'|'smaller'|'similar', or None if not a size
    predicate. Robust to LLM phrasing drift: strips leading hedges ('a little', 'much', 'slightly',
    'a bit', 'far') and a trailing ' than', so 'a little smaller than'/'much bigger' canonicalise."""
    global _SIZE_HEDGE_RE
    if _SIZE_HEDGE_RE is None:
        import re as _re
        _SIZE_HEDGE_RE = _re.compile(r'^(?:a\s+little|a\s+bit|much|slightly|somewhat|far|even)\s+')
    c = _clean(predicate)
    c = _SIZE_HEDGE_RE.sub('', c)
    for tail in (' than', ' as', ' to'):       # 'bigger than'/'same size as'/'similar in size to'
        if c.endswith(tail):
            c = c[:-len(tail)].strip()
            break
    return _SIZE_ALIASES.get(c)


def normalize_direction(direction):
    """Map a single cardinal/alias -> one of CARDINALS. (Used by direction_prior.)"""
    c = _clean(direction)
    if c in _CARDINAL_ALIASES:
        return _CARDINAL_ALIASES[c]
    raise ValueError(f'unknown direction {direction!r}; expected a cardinal or '
                     f'{sorted(set(_CARDINAL_ALIASES) - set(CARDINALS))}')


def normalize_predicate(predicate):
    """Map any predicate phrasing -> canonical: a cardinal, a diagonal, 'center', or 'near'."""
    c = _clean(predicate)
    if c == 'near':
        return 'near'
    if c in _CENTER_ALIASES:
        return 'center'
    if c in _DIAGONAL_ALIASES:
        return _DIAGONAL_ALIASES[c]
    if c in _CARDINAL_ALIASES:
        return _CARDINAL_ALIASES[c]
    raise ValueError(f'unknown predicate {predicate!r}')


def box_center(box):
    x1, y1, x2, y2 = box
    return (0.5 * (x1 + x2), 0.5 * (y1 + y2))


def box_size(box):
    x1, y1, x2, y2 = box
    return (abs(x2 - x1), abs(y2 - y1))


def direction_prior(anchor_box, image_hw, direction, reference='centroid',
                    soft=False, sigma=None, graded=False, exponent=1.0):
    """Prior for a single cardinal direction relative to a reference box.

    hard (default): half-plane 0/1 — good for the dense-region viz, but ties between multiple
        candidates on the correct side (selection becomes arbitrary).
    graded: 0 on the wrong side, then a monotonic ramp toward the far edge, so the candidate
        FURTHEST in the direction scores highest ("on the right" -> the rightmost). This is what
        the reasoner uses for multi-candidate selection.
    soft: sigmoid transition (smooth viz).
    exponent: graded-only; raise the [0,1] ramp to this power to sharpen extreme preference
        (a selector-headroom diagnostic found `right/left/below` etc. cause most
        direction failures by tying near-extreme candidates — quadratic ramp pulls the truly-
        extreme one ahead). exponent=1.0 is the original linear ramp."""
    H, W = image_hw
    direction = normalize_direction(direction)

    x1, y1, x2, y2 = anchor_box
    cx, cy = box_center(anchor_box)
    yy, xx = np.mgrid[0:H, 0:W]
    yy = yy.astype(np.float32)
    xx = xx.astype(np.float32)

    if direction == 'north':       # above
        boundary = y1 if reference == 'edge' else cy
        s = boundary - yy
    elif direction == 'south':     # below
        boundary = y2 if reference == 'edge' else cy
        s = yy - boundary
    elif direction == 'west':      # left
        boundary = x1 if reference == 'edge' else cx
        s = boundary - xx
    else:                          # east / right
        boundary = x2 if reference == 'edge' else cx
        s = xx - boundary

    if graded:
        L = float(W if direction in ('east', 'west') else H)
        prior = np.clip(s, 0.0, L) / L     # 0 on the wrong side; ramps up toward the far edge
        if exponent != 1.0:
            prior = prior ** exponent      # sharpen toward extreme; exponent=2 = quadratic ramp
    elif soft:                             # -> the candidate furthest in the direction wins
        if sigma is None:
            sigma = 0.05 * min(H, W)
        prior = 1.0 / (1.0 + np.exp(-s / max(sigma, 1e-6)))
    else:
        prior = (s > 0).astype(np.float32)
    return np.asarray(prior, dtype=np.float32)


def center_prior(reference_box, image_hw, frac=0.25, mode='gaussian'):
    """Prior peaking at the reference box's centroid (for 'in the middle / center').

    For image-relative center, pass the whole-image box -> blob at the image center.
    sigma = frac * min(H, W).
    """
    H, W = image_hw
    cx, cy = box_center(reference_box)
    sigma = max(frac * min(H, W), 1e-6)
    yy, xx = np.mgrid[0:H, 0:W]
    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    if mode == 'gaussian':
        prior = np.exp(-d2 / (2.0 * sigma * sigma))
    elif mode == 'hard':
        prior = (d2 <= sigma * sigma).astype(np.float32)
    else:
        raise ValueError(f"mode must be 'gaussian' or 'hard', got {mode!r}")
    return prior.astype(np.float32)

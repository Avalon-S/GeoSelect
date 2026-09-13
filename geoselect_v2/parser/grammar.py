"""Typed spatial DSL — AST node definitions + EBNF + JSON<->AST.

This is the *contract* the LLM program-synthesiser must emit and the executor consumes.
Pure Python (no numpy / no torch) so it parses, builds and type-checks on CPU with zero
model deps — the program-legality gate runs here.

EBNF
--------------------
    program   := expr
    expr      := SELECT | FILTER | ARGMAX | ARGMIN | NTH | RESTRICT | RELATE | SETOP
    SELECT    := select(type: str)                        # noun-phrase type -> candidates
    FILTER    := filter(expr, pred: Pred, anchor: Anchor) # spatial predicate score/filter
    RESTRICT  := restrict_count(expr, k: int)             # group/counting constraint
    ARGMAX    := argmax(expr, axis: Axis)                 # superlative (extremal)
    ARGMIN    := argmin(expr, axis: Axis)
    NTH       := nth(expr, n: int, axis: Axis)            # ordinal (sort then index)
    RELATE    := relate(expr, anchor: Anchor, rel: Rel)   # relation score (incl. between)
    SETOP     := and(expr, expr) | or(expr, expr) | not(expr)
    Anchor    := IMAGE | expr                             # image frame OR another object
    Axis      := X | Y | DIAG_UL_LR | DIAG_UR_LL
    Pred      := LEFT|RIGHT|TOP|BOTTOM|UL|UR|LL|LR|CENTER|NEAR  (+ kernel_mode)
    Rel       := NEAR|BETWEEN|ADJACENT|CONTAINS|...

V1 compatibility: a program that degenerates to a single `filter` chain +
AND/OR is behaviourally equivalent to V1 — V1 is the special case, so V2 never regresses.

JSON wire format
----------------
Every node is an object with an "op" key plus typed params, e.g.
    {"op": "argmax", "child": {"op": "select", "type": "ship"}, "axis": "X"}
An Anchor is either the string "image" or a nested expr object. `build(dict)` constructs the
typed node (raising GrammarError on unknown op / malformed structure); `to_dict(node)` is the
inverse. Semantic legality (axis valid for op, kernel/pred compatibility, ...) lives in
typecheck.py — grammar.build only enforces *structural* well-formedness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Union


class GrammarError(ValueError):
    """Raised when a JSON AST is structurally malformed (unknown op, missing/ill-typed
    field, bad enum value). Caught by the reliability layer -> fall back to V1."""


# --------------------------------------------------------------------------------------
# Value types (enums)
# --------------------------------------------------------------------------------------

class Pred(Enum):
    """Directional / proximity predicate. `.value` is the canonical V1 predicate string
    (geogrounder.reasoning.predicates.normalize_predicate vocabulary), so the executor can
    hand `pred.value` straight to V1's build_prior for the MONOTONE (back-compat) kernel."""
    LEFT = 'west'
    RIGHT = 'east'
    TOP = 'north'
    BOTTOM = 'south'
    UL = 'northwest'
    UR = 'northeast'
    LL = 'southwest'
    LR = 'southeast'
    CENTER = 'center'
    NEAR = 'near'


class KernelMode(Enum):
    """Which closed-form kernel a directional predicate uses.

    BANDED   : anchor-relative band ("the left one") — peak at a typical offset, decays both
               sides. kernels/banded.py.  [new in V2]
    EXTREMAL : frame-relative extremum ("leftmost") — softmax over the CANDIDATE set.
               kernels/extremal.py.  [new in V2]
    MONOTONE : V1's monotone half-plane ramp (clip(q,0,L)/L)**gamma. Kept as the third mode
               for backward compatibility. geogrounder.reasoning.predicates.direction_prior.
    """
    BANDED = 'banded'
    EXTREMAL = 'extremal'
    MONOTONE = 'monotone'


class Axis(Enum):
    """Sort / extremum axis for argmax / argmin / nth.
    X: +x = right (east). Y: +y = down (south). DIAG_*: the two image diagonals.
    AREA: bounding-box area -> argmax(AREA) = the largest instance, argmin(AREA) = the smallest.
    This makes SIZE superlatives ("the largest tank") a first-class extremal operator, exactly
    parallel to the positional ones — the extremum is computed over the candidate set, not
    delegated to the detector text query."""
    X = 'X'
    Y = 'Y'
    DIAG_UL_LR = 'DIAG_UL_LR'   # upper-left -> lower-right
    DIAG_UR_LL = 'DIAG_UR_LL'   # upper-right -> lower-left
    AREA = 'AREA'               # bounding-box area (size superlatives)


class Rel(Enum):
    """Higher-order relation for `relate` (scored on the candidate relation graph,
    executor/relation_graph.py — NS3D-style). Extend as relations are added.
    SMALLER / LARGER are COMPARATIVE-SIZE relations ("A smaller than B"): each child candidate
    is scored by whether its box area is smaller / larger than the resolved anchor's area — a
    relation the detector cannot express, executed deterministically over the shared candidates."""
    NEAR = 'near'
    BETWEEN = 'between'
    ADJACENT = 'adjacent'
    CONTAINS = 'contains'
    INSIDE = 'inside'
    SMALLER = 'smaller'
    LARGER = 'larger'


# Sentinel for the image-frame anchor (vs. a nested expr anchor).
class _Image:
    __slots__ = ()
    def __repr__(self):
        return 'IMAGE'


IMAGE = _Image()
# An Anchor is the image frame or a sub-program whose top-1 result is the anchor box.
Anchor = Union[_Image, 'Node']


# --------------------------------------------------------------------------------------
# AST nodes
# --------------------------------------------------------------------------------------

@dataclass
class Node:
    """Base class. Every node carries `op` (set by subclasses) for dispatch/serialisation."""
    op: str = field(init=False, default='')

    def children(self) -> List['Node']:
        """Direct child expr nodes (for traversal). Anchors that are exprs are included."""
        return []


@dataclass
class Select(Node):
    """select(type): candidates whose noun-phrase type matches `type`. The grounding leaf."""
    type: str

    def __post_init__(self):
        self.op = 'select'


@dataclass
class Filter(Node):
    """filter(child, pred, anchor, kernel_mode): score/filter `child` by a spatial predicate
    against `anchor`, using the chosen kernel."""
    child: Node
    pred: Pred
    anchor: Anchor = IMAGE
    kernel_mode: KernelMode = KernelMode.MONOTONE

    def __post_init__(self):
        self.op = 'filter'

    def children(self):
        kids = [self.child]
        if isinstance(self.anchor, Node):
            kids.append(self.anchor)
        return kids


@dataclass
class Argmax(Node):
    """argmax(child, axis): superlative — the candidate most extreme along `axis` (extremal kernel)."""
    child: Node
    axis: Axis

    def __post_init__(self):
        self.op = 'argmax'

    def children(self):
        return [self.child]


@dataclass
class Argmin(Node):
    """argmin(child, axis): superlative the other way (least along `axis`)."""
    child: Node
    axis: Axis

    def __post_init__(self):
        self.op = 'argmin'

    def children(self):
        return [self.child]


@dataclass
class Nth(Node):
    """nth(child, n, axis): ordinal — sort `child` along `axis`, take index `n` (0-based)."""
    child: Node
    n: int
    axis: Axis

    def __post_init__(self):
        self.op = 'nth'

    def children(self):
        return [self.child]


@dataclass
class RestrictCount(Node):
    """restrict_count(child, k): group/counting constraint — keep the top-k / a k-cluster."""
    child: Node
    k: int

    def __post_init__(self):
        self.op = 'restrict_count'

    def children(self):
        return [self.child]


@dataclass
class Relate(Node):
    """relate(child, anchor, rel): score `child` by a higher-order relation to `anchor`
    (NEAR/BETWEEN/ADJACENT/...). `between` needs two anchors -> see typecheck note."""
    child: Node
    rel: Rel
    anchor: Anchor = IMAGE
    anchor2: Optional[Anchor] = None     # for binary relations (e.g. between A and B)

    def __post_init__(self):
        self.op = 'relate'

    def children(self):
        kids = [self.child]
        for a in (self.anchor, self.anchor2):
            if isinstance(a, Node):
                kids.append(a)
        return kids


@dataclass
class And(Node):
    """and(left, right): fuzzy intersection (min) of two candidate-score sets."""
    left: Node
    right: Node

    def __post_init__(self):
        self.op = 'and'

    def children(self):
        return [self.left, self.right]


@dataclass
class Or(Node):
    """or(left, right): fuzzy union (max)."""
    left: Node
    right: Node

    def __post_init__(self):
        self.op = 'or'

    def children(self):
        return [self.left, self.right]


@dataclass
class Not(Node):
    """not(child): fuzzy complement (1 - score)."""
    child: Node

    def __post_init__(self):
        self.op = 'not'

    def children(self):
        return [self.child]


# --------------------------------------------------------------------------------------
# JSON <-> AST
# --------------------------------------------------------------------------------------

_OPS = {
    'select': Select, 'filter': Filter, 'argmax': Argmax, 'argmin': Argmin,
    'nth': Nth, 'restrict_count': RestrictCount, 'relate': Relate,
    'and': And, 'or': Or, 'not': Not,
}

_IMAGE_TOKENS = {'image', 'frame', 'scene', 'whole image', 'the image', ''}


def _norm(s: str) -> str:
    """Normalise an enum string: lowercase, '-'/'_' -> space, collapse whitespace."""
    return ' '.join(str(s).strip().lower().replace('-', ' ').replace('_', ' ').split())


# Natural-language aliases the LLM actually emits. The canonical NAME ('LR') and VALUE
# ('southeast') already match in _enum_from; these add the spelled-out phrasings ('lower
# right', 'bottom right', 'above', 'middle') that otherwise raise GrammarError and force a
# fallback. Keys are _norm()-ed.
_ALIASES = {
    Pred: {
        'above': Pred.TOP, 'up': Pred.TOP, 'upper': Pred.TOP, 'over': Pred.TOP,
        'below': Pred.BOTTOM, 'down': Pred.BOTTOM, 'lower': Pred.BOTTOM, 'under': Pred.BOTTOM,
        'upper left': Pred.UL, 'top left': Pred.UL, 'north west': Pred.UL, 'topleft': Pred.UL,
        'upper right': Pred.UR, 'top right': Pred.UR, 'north east': Pred.UR, 'topright': Pred.UR,
        'lower left': Pred.LL, 'bottom left': Pred.LL, 'south west': Pred.LL, 'bottomleft': Pred.LL,
        'lower right': Pred.LR, 'bottom right': Pred.LR, 'south east': Pred.LR, 'bottomright': Pred.LR,
        'middle': Pred.CENTER, 'centre': Pred.CENTER, 'central': Pred.CENTER, 'mid': Pred.CENTER,
        'close': Pred.NEAR, 'close to': Pred.NEAR, 'nearby': Pred.NEAR,
    },
    Rel: {
        'beside': Rel.ADJACENT, 'next to': Rel.ADJACENT, 'adjacent to': Rel.ADJACENT,
        'touching': Rel.ADJACENT, 'contain': Rel.CONTAINS, 'within': Rel.INSIDE, 'in': Rel.INSIDE,
        # comparative-size phrasings the LLM emits
        'bigger': Rel.LARGER, 'larger': Rel.LARGER, 'bigger than': Rel.LARGER,
        'larger than': Rel.LARGER, 'greater': Rel.LARGER,
        'smaller': Rel.SMALLER, 'smaller than': Rel.SMALLER, 'tinier': Rel.SMALLER,
        'less': Rel.SMALLER,
    },
}


def _enum_from(enum_cls, value, fieldname):
    """Map a JSON string -> enum member by NAME (case-insensitive), by VALUE, or by a
    natural-language alias (_ALIASES). Separators ('-'/'_') and case are normalised first.
    Raises GrammarError listing the legal members."""
    if isinstance(value, enum_cls):
        return value
    if not isinstance(value, str):
        raise GrammarError(f'{fieldname} must be a string, got {value!r}')
    key = _norm(value)
    # by name (LEFT, X, BETWEEN, BANDED ...) — the canonical wire form
    for m in enum_cls:
        if _norm(m.name) == key:
            return m
    # by value (west, banded, between ...) — tolerate the canonical string too
    for m in enum_cls:
        if _norm(str(m.value)) == key:
            return m
    # by natural-language alias ('lower right' -> LR, 'above' -> TOP, 'next to' -> ADJACENT)
    alias = _ALIASES.get(enum_cls, {}).get(key)
    if alias is not None:
        return alias
    legal = ', '.join(m.name for m in enum_cls)
    raise GrammarError(f'bad {fieldname} {value!r}; expected one of: {legal}')


# Unary relations (everything except BETWEEN); a stray anchor2 on these is a benign LLM slip.
_UNARY_RELS = {'NEAR', 'ADJACENT', 'CONTAINS', 'INSIDE', 'SMALLER', 'LARGER'}


def _is_image_anchor(v):
    return isinstance(v, _Image) or (isinstance(v, str) and v.strip().lower() in _IMAGE_TOKENS)


def repair_program(node):
    """Lenient pre-build repair of benign, unambiguous LLM malformations (recursive, on the JSON
    dict). Mirrors V1's sanitize_relation philosophy: fix what is clearly recoverable rather than
    failing the whole program to a fallback. Currently fixes ONE high-frequency slip seen in a
    RISBench audit: a UNARY relate (NEAR/ADJACENT/CONTAINS/INSIDE) carrying a stray
    `anchor2`. The repair drops anchor2; if the primary `anchor` is the image frame while anchor2
    is a real object (the model swapped them), it promotes anchor2 to anchor first. Self-correcting:
    if the kept anchor is undetectable the executor returns empty and still falls back to V1.

    Returns a NEW dict (input not mutated). Non-dict / unknown shapes pass through untouched."""
    if not isinstance(node, dict) or 'op' not in node:
        return node
    out = dict(node)
    if out.get('op') == 'relate' and 'anchor2' in out:
        rel = _norm(str(out.get('rel', ''))).upper().replace(' ', '_')
        # match by NAME or VALUE so both 'NEAR' and 'near' resolve
        rel_name = next((m.name for m in Rel if _norm(m.name) == _norm(str(out.get('rel', '')))
                         or _norm(str(m.value)) == _norm(str(out.get('rel', '')))), rel)
        if rel_name in _UNARY_RELS:
            a, a2 = out.get('anchor', 'image'), out.get('anchor2')
            if _is_image_anchor(a) and not _is_image_anchor(a2):
                out['anchor'] = a2                  # model swapped: real object was in anchor2
            out.pop('anchor2', None)
    # recurse into every child slot
    for key in ('child', 'anchor', 'anchor2', 'left', 'right'):
        if key in out:
            out[key] = repair_program(out[key])
    return out


def _build_anchor(value):
    """Anchor JSON -> IMAGE sentinel or a nested expr Node."""
    if isinstance(value, str):
        if value.strip().lower() in _IMAGE_TOKENS:
            return IMAGE
        raise GrammarError(
            f'string anchor {value!r} must be "image"; an object anchor must be a nested '
            f'expr object (e.g. {{"op": "select", "type": "stadium"}}), not a bare class name')
    if isinstance(value, dict):
        return build(value)
    if isinstance(value, _Image):
        return IMAGE
    raise GrammarError(f'anchor must be "image" or a nested expr object, got {value!r}')


def _req(d, key, op):
    if key not in d:
        raise GrammarError(f'{op!r} node missing required field {key!r}: {d!r}')
    return d[key]


def _int(value, fieldname):
    if isinstance(value, bool) or not isinstance(value, int):
        raise GrammarError(f'{fieldname} must be an int, got {value!r}')
    return value


def build(node) -> Node:
    """Construct a typed AST Node from a JSON dict (recursive). Raises GrammarError on any
    unknown op / missing field / bad enum value. This is structural well-formedness ONLY;
    deeper semantic legality is typecheck.typecheck()."""
    if isinstance(node, Node):
        return node
    if not isinstance(node, dict):
        raise GrammarError(f'expr must be a JSON object, got {type(node).__name__}: {node!r}')
    op = node.get('op')
    if op not in _OPS:
        raise GrammarError(f'unknown op {op!r}; expected one of: {", ".join(sorted(_OPS))}')

    if op == 'select':
        t = _req(node, 'type', op)
        if not isinstance(t, str) or not t.strip():
            raise GrammarError(f'select.type must be a non-empty string, got {t!r}')
        return Select(type=t.strip())

    if op == 'filter':
        return Filter(
            child=build(_req(node, 'child', op)),
            pred=_enum_from(Pred, _req(node, 'pred', op), 'filter.pred'),
            anchor=_build_anchor(node.get('anchor', 'image')),
            kernel_mode=_enum_from(KernelMode, node.get('kernel_mode', 'monotone'),
                                   'filter.kernel_mode'))

    if op == 'argmax':
        return Argmax(child=build(_req(node, 'child', op)),
                      axis=_enum_from(Axis, _req(node, 'axis', op), 'argmax.axis'))
    if op == 'argmin':
        return Argmin(child=build(_req(node, 'child', op)),
                      axis=_enum_from(Axis, _req(node, 'axis', op), 'argmin.axis'))

    if op == 'nth':
        return Nth(child=build(_req(node, 'child', op)),
                   n=_int(_req(node, 'n', op), 'nth.n'),
                   axis=_enum_from(Axis, _req(node, 'axis', op), 'nth.axis'))

    if op == 'restrict_count':
        return RestrictCount(child=build(_req(node, 'child', op)),
                             k=_int(_req(node, 'k', op), 'restrict_count.k'))

    if op == 'relate':
        return Relate(
            child=build(_req(node, 'child', op)),
            rel=_enum_from(Rel, _req(node, 'rel', op), 'relate.rel'),
            anchor=_build_anchor(node.get('anchor', 'image')),
            anchor2=(_build_anchor(node['anchor2']) if node.get('anchor2') is not None else None))

    if op in ('and', 'or'):
        cls = And if op == 'and' else Or
        return cls(left=build(_req(node, 'left', op)), right=build(_req(node, 'right', op)))

    if op == 'not':
        return Not(child=build(_req(node, 'child', op)))

    raise GrammarError(f'unhandled op {op!r}')   # unreachable (guarded above)


def _anchor_to_dict(anchor):
    return 'image' if isinstance(anchor, _Image) else to_dict(anchor)


def to_dict(node: Node) -> dict:
    """Inverse of build(): typed Node -> JSON dict. Round-trips build(to_dict(n)) == n."""
    if not isinstance(node, Node):
        raise GrammarError(f'to_dict expects a Node, got {type(node).__name__}')
    op = node.op
    if op == 'select':
        return {'op': 'select', 'type': node.type}
    if op == 'filter':
        return {'op': 'filter', 'child': to_dict(node.child), 'pred': node.pred.name,
                'anchor': _anchor_to_dict(node.anchor), 'kernel_mode': node.kernel_mode.name}
    if op in ('argmax', 'argmin'):
        return {'op': op, 'child': to_dict(node.child), 'axis': node.axis.name}
    if op == 'nth':
        return {'op': 'nth', 'child': to_dict(node.child), 'n': node.n, 'axis': node.axis.name}
    if op == 'restrict_count':
        return {'op': 'restrict_count', 'child': to_dict(node.child), 'k': node.k}
    if op == 'relate':
        d = {'op': 'relate', 'child': to_dict(node.child), 'rel': node.rel.name,
             'anchor': _anchor_to_dict(node.anchor)}
        if node.anchor2 is not None:
            d['anchor2'] = _anchor_to_dict(node.anchor2)
        return d
    if op in ('and', 'or'):
        return {'op': op, 'left': to_dict(node.left), 'right': to_dict(node.right)}
    if op == 'not':
        return {'op': 'not', 'child': to_dict(node.child)}
    raise GrammarError(f'cannot serialise unknown op {op!r}')


def walk(node: Node):
    """Yield `node` and all descendants (pre-order). Includes expr anchors."""
    yield node
    for c in node.children():
        yield from walk(c)

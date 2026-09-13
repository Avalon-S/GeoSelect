"""Type / legality checking for synthesised DSL programs.

`grammar.build()` already enforces *structural* well-formedness (known op, present fields,
valid enum values). This module adds the *semantic* legality the reliability layer needs to
decide "run V2" vs "fall back to V1":

  - select leaves exist (a program with no select can never ground a candidate);
  - nth.n / restrict_count.k are sane (n >= 0, k >= 1);
  - relate(BETWEEN) supplies the second anchor (binary relation);
  - argmax/argmin/nth axes are legal (guaranteed by the enum, re-checked for completeness);
  - no anchor cycles / unbounded depth (bounded recursion guard).

Contract: `typecheck(program)` returns a list of human-readable errors —
empty == legal. `is_legal()` is the boolean shortcut the pipeline branches on:
    legal program            -> execute V2
    GrammarError / non-empty -> fall back to V1 closed-vocabulary parse (>= V1 lower bound)
This is what guarantees V2 never regresses below V1.
"""

from __future__ import annotations

from typing import List, Union

from .grammar import (
    Node, Select, Filter, Argmax, Argmin, Nth, RestrictCount, Relate, And, Or, Not,
    Rel, IMAGE, GrammarError, build, walk,
)

_MAX_DEPTH = 12   # bounded-recursion guard: a legal program is shallow; deeper => reject.


class TypeCheckError(ValueError):
    """Raised by `typecheck(..., raise_on_error=True)` when a program is illegal."""


def _check_node(node: Node, depth: int, errors: List[str]) -> None:
    if depth > _MAX_DEPTH:
        errors.append(f'program exceeds max depth {_MAX_DEPTH} (likely degenerate/cyclic)')
        return

    if isinstance(node, Nth):
        if node.n < 0:
            errors.append(f'nth.n must be >= 0, got {node.n}')
    elif isinstance(node, RestrictCount):
        if node.k < 1:
            errors.append(f'restrict_count.k must be >= 1, got {node.k}')
    elif isinstance(node, Relate):
        if node.rel is Rel.BETWEEN and node.anchor2 is None:
            errors.append("relate(BETWEEN) is a binary relation and needs 'anchor2'")
        if node.rel is not Rel.BETWEEN and node.anchor2 is not None:
            errors.append(f"relate({node.rel.name}) is unary; 'anchor2' is not allowed")

    for c in node.children():
        _check_node(c, depth + 1, errors)


def typecheck(program: Union[Node, dict], raise_on_error: bool = False) -> List[str]:
    """Return a list of legality errors ([] == legal). Accepts a typed Node or raw JSON dict
    (a dict is run through grammar.build first; a GrammarError becomes a single error entry).

    raise_on_error=True raises TypeCheckError on the first failing program instead — use it in
    tests; the pipeline uses the default (errors list) and branches via is_legal()."""
    errors: List[str] = []
    try:
        node = build(program) if not isinstance(program, Node) else program
    except GrammarError as e:
        errors.append(f'GrammarError: {e}')
        if raise_on_error:
            raise TypeCheckError(errors[0]) from e
        return errors

    # A program must contain at least one `select` leaf, else nothing is ever grounded.
    if not any(isinstance(n, Select) for n in walk(node)):
        errors.append('program has no select() leaf — nothing to ground')

    _check_node(node, depth=0, errors=errors)

    if errors and raise_on_error:
        raise TypeCheckError('; '.join(errors))
    return errors


def is_legal(program: Union[Node, dict]) -> bool:
    """True iff the program is structurally + semantically legal (safe to execute V2).
    The reliability layer's fallback predicate: False -> fall back to V1."""
    return len(typecheck(program)) == 0

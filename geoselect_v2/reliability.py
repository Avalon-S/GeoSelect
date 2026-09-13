"""Reliability layer — the guarantee that V2 >= V1.

The fallback ladder: a synthesised program runs on V2 ONLY when it is
legal AND executes cleanly AND returns a non-empty candidate set. Any failure -> fall back to
the V1 closed-vocabulary parse + SpatialReasoner. Because the fallback path IS V1 (reused
verbatim from geogrounder), V2's overall metric has a hard lower bound at V1 — no regression.

    legal program, executes, non-empty   -> V2 executor   (mode='v2')
    illegal / ExecError / empty result   -> V1 reasoner   (mode='fallback')

This module is model-free and unit-testable: the V2 program and the V1 relation are passed in
already-resolved (the program synthesiser and the V1 parser live elsewhere). `select_types`
collects the noun-phrase types a program needs detected, so the caller can drive the detector.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple, Union

from geogrounder.reasoning.compose import SpatialReasoner

from .parser.grammar import Node, Select, build, walk, GrammarError, repair_program
from .parser.typecheck import is_legal
from .executor import Executor, ExecContext, ExecError
from .executor.executor import rank, select_single, select_group

Box = Tuple[float, float, float, float]


def select_types(program: Union[Node, dict]) -> Set[str]:
    """Every noun-phrase type a program's select() leaves require the detector to find."""
    node = build(program) if not isinstance(program, Node) else program
    return {n.type for n in walk(node) if isinstance(n, Select)}


class Resolver:
    """Resolves a referring expression to ranked target candidates, with the V1 fallback.

    Stateless apart from the reused SpatialReasoner (V1 config) and Executor (V2). Pass the
    pre-synthesised V2 program AND the V1 relation for the SAME sentence; resolve() picks V2
    when reliable, else V1, and reports which (mode) for the reliability table."""

    def __init__(self, reasoner: SpatialReasoner = None, executor: Executor = None,
                 group_tau: float = 0.8):
        self.reasoner = reasoner or SpatialReasoner()      # V1 headline defaults
        self.executor = executor or Executor()
        self.group_tau = group_tau

    def resolve(self, program: Optional[Union[Node, dict]], v1_relation: dict,
                detections: Dict[str, List[Box]], image_hw: Tuple[int, int],
                cardinality: str = 'single', ctx_kwargs: dict = None) -> dict:
        """-> dict(ranked, prior, mode, reason, ...). `mode` is 'v2' or 'fallback'.

        program: synthesised V2 AST (Node or JSON dict) or None (None -> straight to fallback).
        v1_relation: the V1 closed-vocabulary parse of the SAME sentence (the fallback input).
        cardinality: 'single' -> terminal argmax; 'group' -> union(score > tau*max).
        """
        v2 = self._try_v2(program, detections, image_hw, cardinality, ctx_kwargs or {})
        if v2 is not None:
            return v2
        return self._fallback(v1_relation, detections, image_hw)

    # --- V2 attempt (guarded) -------------------------------------------------------------

    def _try_v2(self, program, detections, image_hw, cardinality, ctx_kwargs) -> Optional[dict]:
        if program is None:
            return None
        try:
            if not isinstance(program, Node):
                program = repair_program(program)     # same lenient fix as program synthesis
            if not is_legal(program):
                return None
            node = build(program) if not isinstance(program, Node) else program
            ctx = ExecContext(detections=detections, image_hw=image_hw, **ctx_kwargs)
            scored = self.executor.execute(node, ctx)
        except (GrammarError, ExecError, ValueError):
            return None
        ranked = rank(scored)
        if not ranked:
            return None                       # empty result -> fall back
        terminal = (select_group(ranked, tau=self.group_tau)
                    if cardinality == 'group' else select_single(ranked))
        return {'ranked': ranked, 'terminal': terminal, 'mode': 'v2',
                'reason': 'program legal + executed', 'prior': None}

    # --- V1 fallback ----------------------------------------------------------------------

    def _fallback(self, v1_relation, detections, image_hw) -> dict:
        res = self.reasoner.resolve(v1_relation, detections, image_hw)
        ranked = res['ranked']
        terminal = [ranked[0]] if ranked else []
        return {'ranked': ranked, 'terminal': terminal, 'mode': 'fallback',
                'reason': 'V2 unavailable -> V1 closed-vocabulary parse',
                'prior': res.get('prior')}

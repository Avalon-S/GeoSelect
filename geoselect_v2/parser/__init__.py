"""Program synthesis + typed grammar + type checking.

    grammar.py            typed AST nodes (dataclasses) + EBNF + JSON<->AST
    typecheck.py          semantic legality check + fallback signal
    program_synthesis.py  Qwen3 few-shot -> JSON AST
"""

from .grammar import (
    # nodes
    Node, Select, Filter, Argmax, Argmin, Nth, RestrictCount, Relate, And, Or, Not,
    # value types
    Axis, KernelMode, Pred, Rel, Anchor, IMAGE,
    # builders / serialisers
    build, to_dict, GrammarError,
)
from .typecheck import typecheck, TypeCheckError, is_legal
from .program_synthesis import ProgramSynthesizer, SynthResult, load_prompt

__all__ = [
    'Node', 'Select', 'Filter', 'Argmax', 'Argmin', 'Nth', 'RestrictCount',
    'Relate', 'And', 'Or', 'Not',
    'Axis', 'KernelMode', 'Pred', 'Rel', 'Anchor', 'IMAGE',
    'build', 'to_dict', 'GrammarError',
    'typecheck', 'TypeCheckError', 'is_legal',
    'ProgramSynthesizer', 'SynthResult', 'load_prompt',
]

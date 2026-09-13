"""GeoSelect V2 — neuro-symbolic hybrid executor for referring segmentation.

V2 reframes referring segmentation as *verifiable spatial-program execution over a dense
geometric field*: a text-only LLM synthesises a typed program (AST), and a recursive
executor unifies V1's continuous dense fields (kernels/) with discrete set/order operators
(argmax / sort / count / relate) over open-vocabulary candidate boxes — fully training-free.

Package layout:
    parser/        program synthesis (LLM -> JSON AST), typed grammar, type checking
    kernels/       dense fields (reused V1) + extremal + banded kernels
    executor/      recursive AST interpreter + candidate relation graph
    eval/          stratifier / metrics / oracle (reused + extended from V1)

The reused V1 code lives in the sibling `geogrounder` package (detection bridge, SAM
decoder, dense fields, metrics, dataset loaders). V2 imports from it directly so the V1
fallback path (geogrounder.reasoning.SpatialReasoner) stays bit-identical and guarantees the
no-regression lower bound.
"""

__version__ = '0.0.1'

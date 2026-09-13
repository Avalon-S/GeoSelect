"""Evaluation — stratifier (V1 strata + V2 new tags), metrics/oracle reuse from geogrounder.

    stratifier.py   deterministic TEXT stratifier: image/object/attribute (V1, reused) +
                    superlative / ordinal / group / compositional (V2 new)

metrics + oracle are reused verbatim from geogrounder (geogrounder.metrics.SegMetrics, and the
oracle-selector ceiling logic) — not re-copied, to keep the V1 numbers comparable.
"""

from .stratifier import (
    v2_tags, stratum_tags, is_superlative, is_ordinal, is_group, is_compositional,
    V2_TAGS, ALL_STRATA,
)

__all__ = [
    'v2_tags', 'stratum_tags', 'is_superlative', 'is_ordinal', 'is_group', 'is_compositional',
    'V2_TAGS', 'ALL_STRATA',
]

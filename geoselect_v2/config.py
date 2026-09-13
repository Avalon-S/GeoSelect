"""Config loader — single source of truth for paths / thresholds / kernel params.

Loads geoselect_v2/configs/v2_frozen.yaml by default so scripts are config-driven: paths and
frozen parameters live in ONE auditable file, not scattered across CLI flags. CLI flags, when
given, override the config (override > config).

Path values may use environment variables (`${GEOSELECT_DATA}`, `${GEOSELECT_WEIGHTS}`), which
are expanded at load time. That keeps the shipped config free of one machine's directory layout
while leaving every threshold and kernel parameter exactly as it was frozen.
"""

from __future__ import annotations

import os
from typing import Any

import yaml

_DEFAULT = os.path.join(os.path.dirname(__file__), 'configs', 'v2_frozen.yaml')


def _expand(node):
    """Expand ${VAR} / $VAR in every string, recursively. A string without `$` is untouched."""
    if isinstance(node, str):
        return os.path.expandvars(node)
    if isinstance(node, dict):
        return {k: _expand(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_expand(v) for v in node]
    return node


def load_config(path: str = None) -> dict:
    """Load a V2 config YAML (defaults to the packaged v2_frozen.yaml)."""
    with open(path or _DEFAULT, encoding='utf-8') as f:
        return _expand(yaml.safe_load(f))


def get(cfg: dict, dotted: str, default: Any = None) -> Any:
    """Nested lookup by dotted key, e.g. get(cfg, 'weights.qwen'). Missing -> default."""
    node = cfg
    for k in dotted.split('.'):
        if not isinstance(node, dict) or k not in node:
            return default
        node = node[k]
    return node


def data_root_for(cfg: dict, dataset: str) -> str:
    """The data root for a given dataset name, per the config's data block."""
    if dataset == 'risbench':
        return get(cfg, 'data.risbench_root')
    return get(cfg, 'data.root')

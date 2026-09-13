"""Phase cache for run_eval — resume after a late-stage crash WITHOUT re-running the expensive
parse (Qwen) and detect (LAE-DINO subprocess) phases.

Correctness vs prompt-tuning: each phase's KEY hashes exactly what its output depends on.
  - PARSE key = (model, V2 prompt TEXT, V1 prompt TEXT, dataset, split, n, batch_size). A prompt
    edit changes the key -> MISS -> re-parse. A stale parse is never served while tuning.
  - DETECT is keyed PER IMAGE on the ACTUAL detection inputs (image path + class prompts + det
    params), independent of the prompt. So a prompt edit that changes only kernel/resolution
    logic (not the class list) reuses detections — the hours-long LAE-DINO pass is skipped for
    every unchanged image. The detect index persists across runs and datasets.

Stored as JSON under <cache_dir>. parse_<key>.json: {programs, cards, v1_relations}.
detect_index.json: {per-image-key: DetectionResponse.to_json()} (a growing persistent index).
"""

from __future__ import annotations

import hashlib
import json
import os


def key(*parts) -> str:
    """Stable short hash of the given parts (str-ified, order-sensitive)."""
    h = hashlib.sha1('||'.join(str(p) for p in parts).encode('utf-8')).hexdigest()
    return h[:16]


def load(path):
    if path and os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return None


def save(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or '.', exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, path)        # atomic — a crash mid-write never leaves a corrupt cache file

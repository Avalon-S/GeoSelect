"""End-to-end GeoSelect V2 pipeline.

    [1] ProgramSynthesizer   sentence -> typed DSL program (+ cardinality)         [V2 new]
    [2] LaeDinoClient        image    -> candidate boxes (subprocess, isolated env) [reuse V1]
    [3] Resolver             program (+V1 relation) + boxes -> ranked targets       [V2 core + C3]
                             legal+executes -> V2 executor; else -> V1 SpatialReasoner fallback
    [4] Sam1Masker           chosen box(es) -> mask                                 [reuse V1]

Components are INJECTED (like V1's GeoGrounder), so the orchestration unit-tests with fakes —
no model/GPU — while the real run wires ProgramSynthesizer + LaeDinoClient + Sam1Masker. The
Resolver (step 3) is the real, model-free V2 core.

V1 fallback relation: only the ~3-5% of sentences whose program is illegal need it, so the V1
parser is consulted LAZILY (a `v1_parse_fn` callback) — no second LLM call on the legal majority.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

from .parser.grammar import Select, build, walk
from .reliability import Resolver, select_types

Box = Tuple[float, float, float, float]


def _v1_classes(relation) -> set:
    """Every class name a V1 relation references (target + anchors, recursive)."""
    if not isinstance(relation, dict):
        return set()
    names = {relation['target']} if relation.get('target') else set()
    for rel in relation.get('relations', []):
        a = rel.get('anchor')
        if isinstance(a, str):
            names.add(a)
        elif isinstance(a, dict):
            names |= _v1_classes(a)
    return names


class GeoSelectV2:
    """Orchestrates synthesis -> detect -> resolve(V2/fallback) -> segment.

    synthesizer : ProgramSynthesizer (or any obj with .synthesize(sentence) -> SynthResult)
    detector    : LaeDinoClient (or any obj with .detect(DetectionRequest) -> resp.by_label())
    masker      : Sam1Masker (or any obj with .predict(image, box) -> HxW {0,1})
    v1_parse_fn : sentence -> V1 relation dict, called LAZILY only when the program is illegal
                  (the fallback path). If None, fallback uses a bare {target} from the program.
    """

    def __init__(self, synthesizer, detector, masker, v1_parse_fn: Callable = None,
                 resolver: Resolver = None, box_threshold: float = 0.15, use_slicing: bool = True,
                 ctx_kwargs: dict = None, load_image: Callable = None):
        self.synthesizer = synthesizer
        self.detector = detector
        self.masker = masker
        self.v1_parse_fn = v1_parse_fn
        self.resolver = resolver or Resolver()
        self.box_threshold = box_threshold
        self.use_slicing = use_slicing
        self.ctx_kwargs = ctx_kwargs or {}
        self._load_image = load_image       # injected image loader (PIL); real run uses dataset's

    def run(self, image_path: str, sentence: str, image=None, image_hw: Tuple[int, int] = None):
        """Resolve `sentence` on the image -> dict(mask, boxes, mode, program, ...)."""
        if image is None and self._load_image is not None:
            image = self._load_image(image_path)
        if image_hw is None:
            w, h = image.size
            image_hw = (h, w)

        # [1] synthesise program
        synth = self.synthesizer.synthesize(sentence)
        program = synth.program_dict if synth.legal else None
        cardinality = synth.cardinality

        # V1 fallback relation: lazy — only when the program is unavailable/illegal.
        v1_relation = None
        if program is None:
            v1_relation = self.v1_parse_fn(sentence) if self.v1_parse_fn else {'target': '', 'relations': []}

        # [2] detect every class the program (or the fallback relation) needs
        classes = set()
        if program is not None:
            classes |= select_types(program)
        if v1_relation is not None:
            classes |= _v1_classes(v1_relation)
        detections = self._detect(image_path, sorted(c for c in classes if c))

        # [3] resolve: V2 executor when reliable, else V1 fallback
        res = self.resolver.resolve(program, v1_relation or {'target': '', 'relations': []},
                                    detections, image_hw, cardinality=cardinality,
                                    ctx_kwargs=self.ctx_kwargs)
        terminal = res['terminal']
        if not terminal:
            return {'mask': None, 'boxes': [], 'mode': res['mode'], 'program': program,
                    'cardinality': cardinality, 'reason': 'no target candidate', 'synth': synth}

        # [4] segment the terminal box(es); group cardinality -> union of per-box masks
        boxes = [b for b, _ in terminal]
        mask = self._segment(image, boxes, image_hw)
        return {'mask': mask, 'boxes': boxes, 'mode': res['mode'], 'program': program,
                'cardinality': cardinality, 'ranked': res['ranked'], 'synth': synth}

    # --- model adapters (kept small so fakes drop in for tests) ---------------------------

    def _detect(self, image_path, classes) -> Dict[str, List[Box]]:
        if not classes:
            return {}
        from geogrounder.detection import DetectionRequest
        resp = self.detector.detect(DetectionRequest(
            image_path=image_path, prompts=classes,
            box_threshold=self.box_threshold, use_slicing=self.use_slicing))
        return resp.by_label()

    def _segment(self, image, boxes, image_hw):
        H, W = image_hw
        mask = np.zeros((H, W), dtype=np.uint8)
        for b in boxes:
            m = self.masker.predict(image, b)
            mask |= (np.asarray(m) > 0).astype(np.uint8)
        return mask

"""Wire protocol for the main-env <-> LAE-DINO-env subprocess bridge.

The two environments have incompatible deps (main: torch 2.5.1 / py3.10;
laedino: torch 1.10 / py3.8 / mmcv), so they MUST NOT import each other. They exchange
plain JSON: the main env writes a DetectionRequest, the laedino env writes a
DetectionResponse. This module (main side) defines and validates that JSON; the laedino
serve script (laedino_env/serve_detect.py) emits the same shape by hand.

Box convention: xyxy in absolute pixels, origin top-left, x=col, y=row.
"""

from dataclasses import dataclass, field, asdict
import json
from typing import List, Optional

PROTOCOL_VERSION = 1


@dataclass
class DetectionRequest:
    image_path: str
    prompts: List[str]                 # text queries / class names to detect
    box_threshold: float = 0.25
    text_threshold: float = 0.25
    use_slicing: bool = False          # supervision.InferenceSlicer for large images
    slice_wh: List[int] = field(default_factory=lambda: [800, 800])
    overlap_ratio: float = 0.2
    version: int = PROTOCOL_VERSION

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(s: str) -> 'DetectionRequest':
        return DetectionRequest(**json.loads(s))


@dataclass
class Detection:
    bbox_xyxy: List[float]             # [x1, y1, x2, y2] absolute pixels
    score: float
    label: str


@dataclass
class DetectionResponse:
    detections: List[Detection]
    image_w: int
    image_h: int
    error: Optional[str] = None
    version: int = PROTOCOL_VERSION

    def to_json(self) -> str:
        return json.dumps({
            'detections': [asdict(d) for d in self.detections],
            'image_w': self.image_w,
            'image_h': self.image_h,
            'error': self.error,
            'version': self.version,
        })

    @staticmethod
    def from_json(s: str) -> 'DetectionResponse':
        d = json.loads(s)
        dets = [Detection(**x) for x in d.get('detections', [])]
        return DetectionResponse(detections=dets, image_w=d['image_w'],
                                 image_h=d['image_h'], error=d.get('error'),
                                 version=d.get('version', PROTOCOL_VERSION))

    def by_label(self):
        """Group boxes by label -> {label: [box_xyxy, ...]} for the reasoner."""
        out = {}
        for det in self.detections:
            out.setdefault(det.label, []).append(det.bbox_xyxy)
        return out

    def by_label_scored(self):
        """Like by_label but keeps the detector confidence: {label: [(box_xyxy, score), ...]}.
        Needed for the no-geometry selection ablation (rank candidates by detector score) and for
        the parse+detect cache; the geometry path just drops the scores."""
        out = {}
        for det in self.detections:
            out.setdefault(det.label, []).append((det.bbox_xyxy, float(det.score)))
        return out


# --- batch helpers: one subprocess invocation loads LAE-DINO ONCE and serves many images ---

def requests_to_json(requests) -> str:
    return json.dumps({'version': PROTOCOL_VERSION,
                       'requests': [asdict(r) for r in requests]})


def requests_from_json(s):
    return [DetectionRequest(**d) for d in json.loads(s)['requests']]


def responses_to_json(responses) -> str:
    return json.dumps({'version': PROTOCOL_VERSION,
                       'responses': [json.loads(r.to_json()) for r in responses]})


def responses_from_json(s):
    return [DetectionResponse(detections=[Detection(**x) for x in d.get('detections', [])],
                              image_w=d['image_w'], image_h=d['image_h'],
                              error=d.get('error'))
            for d in json.loads(s)['responses']]

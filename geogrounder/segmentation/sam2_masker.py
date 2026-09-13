"""Stage [4]: SAM2.1 mask generation with box + point prompts.

Rotated targets fit their horizontal bounding box (HBB) poorly, so we compensate with points:
positive = target center + axis endpoints (inside the object), negative = HBB corners
(usually background for a rotated object). `default_prompts_from_box` builds these from an
HBB, and takes the oriented axis endpoints as well when the caller has them.
"""

import numpy as np


def default_prompts_from_box(box_xyxy, axis_endpoints=None):
    """Return (point_coords [N,2] xy, point_labels [N]) for a SAM2 box prompt.

    positive: center (+ axis endpoints if given);  negative: the 4 HBB corners.
    """
    x1, y1, x2, y2 = box_xyxy
    cx, cy = 0.5 * (x1 + x2), 0.5 * (y1 + y2)
    pos = [(cx, cy)]
    if axis_endpoints:
        pos.extend(axis_endpoints)
    neg = [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]  # HBB corners
    coords = np.array(pos + neg, dtype=np.float32)
    labels = np.array([1] * len(pos) + [0] * len(neg), dtype=np.int32)
    return coords, labels


class Sam2Masker:
    def __init__(self, ckpt_path, model_cfg, device='cuda'):
        self.ckpt_path = ckpt_path
        self.model_cfg = model_cfg
        self.device = device
        self.predictor = None

    def load(self):
        from sam2.build_sam import build_sam2
        from sam2.sam2_image_predictor import SAM2ImagePredictor
        sam2 = build_sam2(self.model_cfg, self.ckpt_path, device=self.device)
        self.predictor = SAM2ImagePredictor(sam2)
        return self

    def unload(self):
        self.predictor = None
        # caller: geogrounder.utils.vram.empty_cache()

    def predict(self, image, box_xyxy, points=None, text=None):
        """image: PIL or HxWx3 array; box_xyxy: [x1,y1,x2,y2] -> binary mask HxW (uint8).

        points: optional (coords[N,2] xy, labels[N]) — e.g. from default_prompts_from_box for
        rotated targets. If None, box-only (the robust v1 default).
        text: ignored (accepted for Sam3Masker interface compatibility in make_masker).
        """
        # np.array (writable copy) avoids torchvision's "non-writable tensor" warning in set_image
        arr = np.array(image.convert('RGB')) if hasattr(image, 'convert') else np.array(image)
        self.predictor.set_image(arr)
        kw = {'box': np.asarray(box_xyxy, dtype=np.float32)[None, :], 'multimask_output': False}
        if points is not None:
            coords, labels = points
            kw['point_coords'] = np.asarray(coords, dtype=np.float32)
            kw['point_labels'] = np.asarray(labels, dtype=np.int32)
        masks, _scores, _ = self.predictor.predict(**kw)
        return masks[0].astype(np.uint8)

    def predict_many(self, image, boxes):
        """Segment several boxes on ONE image — set_image (the expensive embed) once, then predict
        each box from the cached embedding. -> list of HxW uint8 masks. Used for mask-alpha rerank."""
        arr = np.array(image.convert('RGB')) if hasattr(image, 'convert') else np.array(image)
        self.predictor.set_image(arr)
        out = []
        for b in boxes:
            masks, _scores, _ = self.predictor.predict(
                box=np.asarray(b, dtype=np.float32)[None, :], multimask_output=False)
            out.append(masks[0].astype(np.uint8))
        return out

"""SAM3 box(+optional concept)->mask decoder — stage-4 ablation alongside SAM / SAM2.1.

Part of the decoder-agnostic ablation (SAM2.1 headline / SAM1 / SAM3 box-only / SAM3 box+concept):
show the grounding gain does not depend on the mask decoder. SAM3 (Segment Anything with Concepts,
transformers Sam3Model/Sam3Processor) is concept-promptable and ALSO accepts a geometric box hint
via input_boxes. Two variants, toggled by use_text:
  - use_text=False: box only             (symmetric with SAM1/SAM2; SAM3 is concept-centric, so the
                                          pure-geometric path may be unsupported/weak — informative).
  - use_text=True : box + target concept (MOST-FAVORABLE to SAM3 — strictly more prior than the
                                          box-only decoders; the verified path from run_sam3_box_masker).

Unlike SAM/SAM2 (set_image + predict(box)), SAM3 returns N instance masks per forward; we keep the
MASKER-SWAP semantics of run_sam3_box_masker.py: pick the returned mask with MAX IoU to the input
box ("does SAM3 paint the geometry-selected box better than SAM2?"), with NO fallback to SAM2
(empty -> IoU 0; never silently mix decoders). Interface matches Sam2Masker (load/unload/predict/
predict_many) so make_masker swaps it behind --segmenter sam3; predict() takes an extra text= that
SAM/SAM2 ignore. Masks come back at the original image size (post_process target_sizes), so the
downstream Accum 480-NEAREST resize matches GT exactly.
"""

import numpy as np


def _box_iou_to_mask(box, mask):
    """IoU of the filled input-box rectangle vs a binary mask, at the mask's native resolution.
    Picks which SAM3-returned instance best matches the requested geometry box."""
    h, w = mask.shape
    x1, y1, x2, y2 = (int(round(v)) for v in box)
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    box_area = (x2 - x1) * (y2 - y1)
    inside = int(mask[y1:y2, x1:x2].sum())
    union = box_area + int(mask.sum()) - inside
    return float(inside) / float(union) if union > 0 else 0.0


class Sam3Masker:
    def __init__(self, model_path, use_text=True, score_threshold=0.1, device='cuda'):
        self.model_path = model_path
        self.use_text = use_text                 # False: box-only | True: box+concept (most-favorable)
        self.score_threshold = score_threshold   # PCS-calibrated 0.1; shared across SAM2/PCS/box, NOT tuned
        self.device = device
        self.model = None
        self.processor = None
        self._err = 0

    def load(self):
        from transformers import Sam3Model, Sam3Processor
        self.model = Sam3Model.from_pretrained(self.model_path).to(self.device).eval()
        self.processor = Sam3Processor.from_pretrained(self.model_path)
        return self

    def unload(self):
        self.model = None
        self.processor = None
        # caller: geogrounder.utils.vram.empty_cache()

    def _hw(self, image):
        if hasattr(image, 'size'):                # PIL: (W, H)
            w, h = image.size
            return h, w
        a = np.asarray(image)
        return a.shape[0], a.shape[1]

    def _run(self, image, box_xyxy, text):
        import torch
        kw = dict(images=image, input_boxes=[[list(map(float, box_xyxy))]],
                  input_boxes_labels=[[1]], return_tensors='pt')
        if self.use_text and text and str(text).strip():
            kw['text'] = str(text)
        inputs = self.processor(**kw).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
        res = self.processor.post_process_instance_segmentation(
            outputs, threshold=self.score_threshold, mask_threshold=0.5,
            target_sizes=inputs.get('original_sizes').tolist())[0]
        masks = res['masks']
        if hasattr(masks, 'cpu'):
            masks = masks.cpu().numpy()
        masks = np.asarray(masks)
        return [(m > 0).astype(np.uint8) for m in masks] if masks.size else []

    def predict(self, image, box_xyxy, points=None, text=None):
        """box->mask via SAM3; pick the returned instance with max IoU to the input box. text: target
        concept (used only when use_text). points ignored (SAM2 compat). No mask -> empty (IoU 0)."""
        H, W = self._hw(image)
        if box_xyxy is None:
            return np.zeros((H, W), dtype=np.uint8)
        try:
            masks = self._run(image, box_xyxy, text)
        except Exception as e:
            self._err += 1
            if self._err <= 3:
                print(f'  [Sam3Masker] forward failed ({self._err}; box-only={not self.use_text}): '
                      f'{type(e).__name__}: {e}')
            return np.zeros((H, W), dtype=np.uint8)
        if not masks:
            return np.zeros((H, W), dtype=np.uint8)
        ious = [_box_iou_to_mask(box_xyxy, m) for m in masks]
        return masks[int(np.argmax(ious))]

    def predict_many(self, image, boxes, text=None):
        """Per-box SAM3 (one forward each — no set_image cache like SAM2). Used for union/group."""
        return [self.predict(image, b, text=text) for b in boxes]

"""SAM1 (original Segment-Anything, ViT-L) box->mask decoder via HF transformers — drop-in
ablation for Sam2Masker.

Uses transformers SamModel/SamProcessor (facebook/sam-vit-large): same SAM1 ViT-L weights, but no
extra segment-anything pip dependency, the same HF loading style as Sam3Masker, and a ModelScope
mirror (facebook/sam-vit-large) for download. Part of the decoder-agnostic ablation (SAM2.1 headline
/ SAM1 / SAM3): the grounding gain should not depend on the mask decoder.

Box prompt: processor(image, input_boxes=[[[x1,y1,x2,y2]]]) -> model(multimask_output=False) ->
post_process_masks. SINGLE-mask mode, to MATCH the SAM2.1 headline (Sam2Masker also uses
multimask_output=False); multimask + best-of-3 (by SAM's own predicted IoU — NOT GT, so not an
oracle) would still give SAM1 a decoder-side mask-selection edge (esp. oIoU) the single-mask
SAM2.1 path doesn't get, confounding the decoder swap. Interface matches Sam2Masker; predict() accepts an
ignored points=/text= for Sam2/Sam3 compatibility in make_masker.
"""

import numpy as np


class Sam1Masker:
    def __init__(self, model_path, device='cuda'):
        self.model_path = model_path      # HF dir, e.g. <weights>/sam-vit-large
        self.device = device
        self.model = None
        self.processor = None

    def load(self):
        from transformers import SamModel, SamProcessor
        self.model = SamModel.from_pretrained(self.model_path).to(self.device).eval()
        self.processor = SamProcessor.from_pretrained(self.model_path)
        return self

    def unload(self):
        self.model = None
        self.processor = None
        # caller: geogrounder.utils.vram.empty_cache()

    def _hw(self, image):
        if hasattr(image, 'size'):            # PIL: (W, H)
            w, h = image.size
            return h, w
        a = np.asarray(image)
        return a.shape[0], a.shape[1]

    def _seg(self, image, box_xyxy):
        import torch
        img = image.convert('RGB') if hasattr(image, 'convert') else image
        inputs = self.processor(img, input_boxes=[[[float(v) for v in box_xyxy]]],
                                return_tensors='pt').to(self.device)
        with torch.no_grad():
            # multimask_output=False -> single mask, ALIGNED with the SAM2.1 headline (Sam2Masker
            # also passes multimask_output=False). multimask + best-of-3 would unfairly inflate SAM1
            # (esp. oIoU), mixing the decoder swap with a mask-selection policy.
            outputs = self.model(**inputs, multimask_output=False)
        masks = self.processor.image_processor.post_process_masks(
            outputs.pred_masks.cpu(), inputs['original_sizes'].cpu(),
            inputs['reshaped_input_sizes'].cpu())[0]      # [nb_boxes, 1, H, W]
        scores = outputs.iou_scores.cpu()[0]              # [nb_boxes, 1]
        m = np.asarray(masks[0])                          # box 0 -> [1, H, W]
        bi = int(scores[0].argmax())                      # single mask -> bi = 0
        return (m[bi] > 0).astype(np.uint8)

    def predict(self, image, box_xyxy, points=None, text=None):
        """box->mask via HF SAM (ViT-L). points/text ignored (Sam2/Sam3 interface compatibility)."""
        if box_xyxy is None:
            H, W = self._hw(image)
            return np.zeros((H, W), dtype=np.uint8)
        return self._seg(image, box_xyxy)

    def predict_many(self, image, boxes, text=None):
        """Per-box SAM (one process+forward each). Used for union/group. Mirrors Sam2Masker."""
        return [self._seg(image, b) for b in boxes]

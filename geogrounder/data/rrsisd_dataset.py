"""Training-free RRSIS-D sample iterator.

Unlike RMSIN's ReferDataset (which tokenises with BERT and resizes for a trained model),
GeoGrounder needs only: the image, the raw referring sentence, and the GT mask — at
NATIVE resolution. We feed raw text to Qwen3-VL and run detection/SAM2 on the full image.

Sample expansion: one sample == one (ref, sentence) pair. RMSIN's test.py loops over every
sentence of a ref and counts each as a separate eval sample, so we expand the same way here.
This is the (image, sentence) counting the eval protocol requires.

GT mask: reproduced exactly from RMSIN's loader, including the `== 1` binarisation
(see note below). Masks come from instances.json polygons via REFER.getMask — NOT from
ann_split (this RRSIS-D distribution's ann_split is XML detection annotations, unused here).
"""

import os

import numpy as np
from PIL import Image

from .refer import REFER


class RRSISDDataset:
    def __init__(self, data_root, split='test', dataset='rrsisd', split_by='unc'):
        self.refer = REFER(data_root, dataset, split_by)
        self.split = split
        ref_ids = self.refer.getRefIds(split=split)

        # expand to (ref_id, sentence_index) samples
        self.samples = []
        for rid in ref_ids:
            ref = self.refer.Refs[rid]
            for si in range(len(ref['sentences'])):
                self.samples.append((rid, si))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        ref_id, sent_idx = self.samples[index]
        ref = self.refer.Refs[ref_id]
        img_info = self.refer.Imgs[ref['image_id']]
        image_path = os.path.join(self.refer.IMAGE_DIR, img_info['file_name'])

        sentence = ref['sentences'][sent_idx]['raw']

        # --- GT mask: identical to RMSIN (data/dataset_refer_bert.py) for comparability ---
        ref_mask = np.array(self.refer.getMask(ref)['mask'])
        gt = np.zeros(ref_mask.shape, dtype=np.uint8)
        gt[ref_mask == 1] = 1  # NOTE: `== 1` (not `>= 1`) matches RMSIN. Do not "fix".

        # GT box from the MASK (in image/800 space). NOTE: do NOT use ann['bbox'] (getRefBox) —
        # in RRSIS-D's instances.json the bbox is in the ORIGINAL (unscaled) coordinate space and
        # exceeds the 800x800 image bounds; only the polygon/mask is in image space. RMSIN only
        # ever uses the mask, so the bbox field is stale/wrong-scale.
        ys, xs = np.where(gt > 0)
        gt_bbox = ([int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
                   if len(xs) else [0, 0, 0, 0])

        return {
            'image_path': image_path,
            'sentence': sentence,
            'gt_mask': gt,                       # uint8 {0,1}, native (H, W)
            'gt_bbox_xyxy': gt_bbox,             # tight box of the mask, image space (USE THIS)
            'ref_id': ref_id,
            'sent_id': ref['sentences'][sent_idx]['sent_id'],
            'image_id': ref['image_id'],
            'category': self.refer.Cats[ref['category_id']],
            'bbox_xywh_raw': self.refer.getRefBox(ref_id),  # raw ann['bbox'] — WRONG scale, do not use
            'file_name': img_info['file_name'],
            'height': img_info['height'],
            'width': img_info['width'],
        }

    @staticmethod
    def load_image(image_path):
        """Load an RGB image as a PIL.Image (native resolution)."""
        return Image.open(image_path).convert('RGB')

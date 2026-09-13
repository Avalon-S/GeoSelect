"""RISBench raw-CrOBIM reader — SAME sample dict as RISBenchDataset, but reads the
ORIGINAL CrOBIM on-disk layout (img_rgb/ + mask/ + output_phrase_<split>.txt) instead of the
HF-arrow form. Use this for a SAME-SOURCE comparison against RSRefSeg2 / RSVG-ZeroOV, whose
published numbers are on original CrOBIM: the HF-arrow repackage dropped the original
filenames and may differ in encoding / resolution / mask binarisation, so a number measured
on the arrow form is not guaranteed comparable to the baselines.

Layout (data_root, e.g. <datasets>/RISBench_orig):
    <data_root>/img_rgb/<image_id>          RGB png, 512x512        (e.g. test_0_0.png)
    <data_root>/mask/<image_id>             binary mask png (0/255), same name
    <data_root>/output_phrase_<split>.txt   lines: "<image_id> <referring phrase>"

Notes:
- One image FILE per referring sample (each referent has its own crop, e.g. test_2_0.png,
  test_2_3.png are distinct files), so image_id is unique per line.
- The CrOBIM `val` split's output_phrase lines reference `train_*.png` images (val is a subset
  of the train image pool), NOT a `val_` prefix — handled transparently because we key off the
  filename in each line, not a prefix.
- GT comes from mask/<image_id> (the canonical CrOBIM mask), the same source RSRefSeg2 encoded
  into its jsonl RLE — so GeoSelect and RSRefSeg2 now share images AND GT source.
"""

import os

import numpy as np
from PIL import Image


class RISBenchCrobimDataset:
    def __init__(self, data_root, split='test'):
        self.data_root = data_root
        self.split = split
        split_tag = 'val' if split in ('val', 'validation') else split
        ann = os.path.join(data_root, f'output_phrase_{split_tag}.txt')
        if not os.path.isfile(ann):
            raise FileNotFoundError(
                f"RISBench-CrOBIM: annotation file {ann!r} not found. Expected the original "
                "CrOBIM layout (img_rgb/ + mask/ + output_phrase_<split>.txt) under data_root.")
        self.img_dir = os.path.join(data_root, 'img_rgb')
        self.mask_dir = os.path.join(data_root, 'mask')

        self.samples = []  # [(image_id, phrase), ...]
        with open(ann, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(maxsplit=1)           # split off the leading filename token
                image_id = parts[0]
                phrase = parts[1] if len(parts) > 1 else ''
                self.samples.append((image_id, phrase))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        image_id, phrase = self.samples[index]
        image_path = os.path.join(self.img_dir, image_id)
        mask_path = os.path.join(self.mask_dir, image_id)

        # Mask -> uint8 {0,1}.  CrOBIM masks are binary 0/255 (single channel or replicated).
        m = np.asarray(Image.open(mask_path))
        if m.ndim == 3:
            m = m[..., 0]
        gt = (m > 0).astype(np.uint8)
        H, W = gt.shape

        ys, xs = np.where(gt > 0)
        gt_bbox = ([int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
                   if len(xs) else [0, 0, 0, 0])

        return {
            'image_path': image_path,
            'sentence': phrase,
            'gt_mask': gt,
            'gt_bbox_xyxy': gt_bbox,
            'ref_id': index,
            'sent_id': index,
            'image_id': index,           # unique per line (one image file per referent)
            'category': None,            # CrOBIM publishes no per-sample class label
            'file_name': image_id,       # original CrOBIM filename, e.g. test_0_0.png
            'height': int(H),
            'width': int(W),
        }

    @staticmethod
    def load_image(image_path):
        return Image.open(image_path).convert('RGB')

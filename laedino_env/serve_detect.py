"""LAE-DINO detection server — runs in the ISOLATED `laedino` env (py3.8 / torch1.10 / mmcv).

Invoked by geogrounder.detection.client.LaeDinoClient as:
    python serve_detect.py --requests reqs.json --responses resps.json

reqs.json  = {"requests":  [ {image_path, prompts, box_threshold, use_slicing, ...}, ... ]}
resps.json = {"responses": [ {detections:[{bbox_xyxy,score,label}], image_w, image_h, error}, ...]}

The model is loaded ONCE per invocation and reused across all requests in the batch (so eval
over hundreds of images costs one cold load). Box convention: xyxy absolute pixels.

IMPORTANT: lives OUTSIDE the `geogrounder` package on purpose — do NOT import geogrounder here
(different Python/torch). JSON I/O is hand-rolled to keep the boundary clean.

Config / weights come from the environment (or --config/--weights); see the root README.md:
    LAEDINO_REPO     where LAE-DINO was cloned            (default: ~/LAE-DINO)
    LAEDINO_CONFIG   the detector config .py              (default: derived from LAEDINO_REPO)
    LAEDINO_WEIGHTS  the detector checkpoint .pth         (default: derived from GEOSELECT_WEIGHTS)
    LAEDINO_META_ANN any valid COCO json, for class metainfo only (see build_inferencer)
"""

import argparse
import json
import os
import sys

# Paths are derived from the environment so this file carries no machine's directory layout.
# GEOSELECT_WEIGHTS / GEOSELECT_DATA are the same roots the main environment uses; anything unset
# expands to an empty prefix, so an absolute path can equally be passed via --config / --weights.
LAEDINO_REPO = os.environ.get('LAEDINO_REPO', os.path.expanduser('~/LAE-DINO'))
DEFAULT_CONFIG = os.path.join(
    LAEDINO_REPO, 'mmdetection_lae', 'configs', 'lae_dino',
    'lae_dino_swin-t_pretrain_LAE-1M.py')
DEFAULT_WEIGHTS = os.path.join(
    os.environ.get('GEOSELECT_WEIGHTS', ''), 'LAE-DINO', 'checkpoints',
    'lae_dino_swint_lae1m-28ca3a15.pth')

# Progress lines go to stderr prefixed with this marker so the parent client can stream ONLY
# them (and not the mmdet load noise). MUST match PROGRESS_MARKER in detection/client.py.
PROGRESS_MARKER = '[[LAEDINO_PROGRESS]]'
PROGRESS_EVERY = 50

_INFERENCER = None


def build_inferencer(config, weights, device='cuda:0'):
    """Build LAE-DINO once (MM-Grounding-DINO style DetInferencer).

    The lae1m checkpoint stores no dataset_meta, so DetInferencer builds
    cfg.test_dataloader.dataset just to read class names — but that points at LAE-FOD jsons we
    don't have. For grounding, classes come from `texts`, so the metainfo is irrelevant: we
    swap in a minimal CocoDataset on a valid COCO file (RRSIS-D instances.json) + the real
    grounding test_pipeline. Override the ann file via LAEDINO_META_ANN if needed.
    """
    import os
    import tempfile
    from mmengine.config import Config
    from mmdet.apis import DetInferencer

    cfg = Config.fromfile(config)
    valid_ann = os.environ.get('LAEDINO_META_ANN') or os.path.join(
        os.environ.get('GEOSELECT_DATA', ''), 'RSSIS-D', 'rrsisd', 'instances.json')
    test_pipeline = [
        dict(type='LoadImageFromFile', backend_args=None),
        dict(type='FixScaleResize', scale=(800, 1333), keep_ratio=True),
        dict(type='LoadAnnotations', with_bbox=True),
        dict(type='PackDetInputs',
             meta_keys=('img_id', 'img_path', 'ori_shape', 'img_shape',
                        'scale_factor', 'text', 'custom_entities')),
    ]
    cfg.test_dataloader.dataset = dict(
        type='CocoDataset', ann_file=valid_ann, data_prefix=dict(img=''),
        test_mode=True, pipeline=test_pipeline)

    tmp_cfg = os.path.join(tempfile.gettempdir(), 'lae_dino_infer.py')
    cfg.dump(tmp_cfg)
    return DetInferencer(model=tmp_cfg, weights=weights, device=device, show_progress=False)


def _infer(image, prompts, box_threshold):
    """Run DetInferencer on one image (path or ndarray). -> list of (box_xyxy, score, label)."""
    texts = ' . '.join(prompts)
    out = _INFERENCER(image, texts=texts, custom_entities=True,
                      pred_score_thr=box_threshold,
                      return_datasamples=False, no_save_vis=True, no_save_pred=True)
    pred = out['predictions'][0]
    dets = []
    for box, score, lab in zip(pred['bboxes'], pred['scores'], pred['labels']):
        if score < box_threshold:
            continue
        name = prompts[lab] if isinstance(lab, int) and 0 <= lab < len(prompts) else str(lab)
        dets.append(([float(v) for v in box], float(score), name))
    return dets


def _iou(a, b):
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    ua = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    ub = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = ua + ub - inter
    return inter / union if union > 0 else 0.0


def _nms_per_label(dets, iou_thr=0.5):
    """Greedy NMS within each label (merges duplicate boxes from overlapping tiles)."""
    by_label = {}
    for d in dets:
        by_label.setdefault(d[2], []).append(d)
    kept = []
    for group in by_label.values():
        chosen = []
        for d in sorted(group, key=lambda x: -x[1]):
            if all(_iou(d[0], c[0]) <= iou_thr for c in chosen):
                chosen.append(d)
        kept.extend(chosen)
    return kept


def _tiles(W, H, sw, sh, overlap):
    sx = max(1, int(round(sw * (1 - overlap))))
    sy = max(1, int(round(sh * (1 - overlap))))
    xs = list(range(0, max(W - sw, 0) + 1, sx)) or [0]
    ys = list(range(0, max(H - sh, 0) + 1, sy)) or [0]
    if xs[-1] != max(W - sw, 0):
        xs.append(max(W - sw, 0))
    if ys[-1] != max(H - sh, 0):
        ys.append(max(H - sh, 0))
    return [(x, y, min(x + sw, W), min(y + sh, H)) for y in ys for x in xs]


def run_laedino(image_path, prompts, box_threshold, use_slicing, slice_wh, overlap_ratio):
    """-> (detections, image_w, image_h). detections: [{bbox_xyxy,[x1,y1,x2,y2], score, label}].

    LAE-DINO open-vocab: texts = '<a> . <b> . <c>' (period-separated), custom_entities=True.
    With use_slicing, tile the image (overlap), detect per tile, offset boxes back, per-label NMS
    — the small-object remedy (RS objects are tiny at native resolution). Tiles go through a
    temp PNG so preprocessing matches the whole-image path exactly.
    """
    import shutil
    import tempfile
    import numpy as np
    from PIL import Image

    img = Image.open(image_path).convert('RGB')
    W, H = img.size
    sw, sh = int(slice_wh[0]), int(slice_wh[1])

    if use_slicing and (W > sw or H > sh):
        arr = np.asarray(img)
        # SAHI: combine a FULL-IMAGE pass (recovers large objects) with the sliced passes
        # (recover small objects). NMS only dedups; the right-scale box already exists in the pool.
        all_dets = list(_infer(image_path, prompts, box_threshold))
        tmpd = tempfile.mkdtemp(prefix='lae_tiles_')
        try:
            for ti, (x1, y1, x2, y2) in enumerate(_tiles(W, H, sw, sh, overlap_ratio)):
                cp = os.path.join(tmpd, f'tile_{ti}.png')
                Image.fromarray(arr[y1:y2, x1:x2]).save(cp)
                for box, score, name in _infer(cp, prompts, box_threshold):
                    all_dets.append(([box[0] + x1, box[1] + y1, box[2] + x1, box[3] + y1],
                                     score, name))
        finally:
            shutil.rmtree(tmpd, ignore_errors=True)
        dets_list = _nms_per_label(all_dets, iou_thr=0.5)
    else:
        dets_list = _infer(image_path, prompts, box_threshold)

    detections = [{'bbox_xyxy': b, 'score': s, 'label': n} for (b, s, n) in dets_list]
    return detections, W, H


def main():
    global _INFERENCER
    ap = argparse.ArgumentParser()
    ap.add_argument('--requests', required=True)
    ap.add_argument('--responses', required=True)
    ap.add_argument('--config', default=os.environ.get('LAEDINO_CONFIG', DEFAULT_CONFIG))
    ap.add_argument('--weights', default=os.environ.get('LAEDINO_WEIGHTS', DEFAULT_WEIGHTS))
    ap.add_argument('--device', default='cuda:0')
    args = ap.parse_args()

    with open(args.requests) as f:
        requests = json.load(f)['requests']

    # LAE-DINO configs reference BERT via a relative '../weights/bert-base-uncased' (assuming
    # CWD = the mmdetection_lae dir). Make paths absolute, then chdir there so that relative path
    # — and any other config-relative path — resolves (../weights/bert-base-uncased -> the symlink).
    config_abs = os.path.abspath(args.config)
    weights_abs = os.path.abspath(args.weights)
    mmdet_root = os.path.dirname(os.path.dirname(os.path.dirname(config_abs)))  # .../mmdetection_lae
    if os.path.isdir(mmdet_root):
        os.chdir(mmdet_root)

    responses = []
    try:
        _INFERENCER = build_inferencer(config_abs, weights_abs, args.device)
    except Exception as e:
        # whole-batch failure (e.g. bad config/weights): report it on every request. Prefix with the
        # progress marker so the parent client STREAMS it (else the streaming filter swallows it).
        err = f'build_inferencer failed: {type(e).__name__}: {e}'
        print(f'{PROGRESS_MARKER} {err}', file=sys.stderr, flush=True)
        responses = [{'detections': [], 'image_w': 0, 'image_h': 0, 'error': err}
                     for _ in requests]
        _write(args.responses, responses)
        return

    total = len(requests)
    for i, req in enumerate(requests, 1):
        try:
            dets, w, h = run_laedino(
                req['image_path'], req['prompts'],
                req.get('box_threshold', 0.25), req.get('use_slicing', False),
                req.get('slice_wh', [800, 800]), req.get('overlap_ratio', 0.2))
            responses.append({'detections': dets, 'image_w': w, 'image_h': h, 'error': None})
        except Exception as e:
            responses.append({'detections': [], 'image_w': 0, 'image_h': 0,
                              'error': f'{type(e).__name__}: {e}'})
        if total > 1 and (i % PROGRESS_EVERY == 0 or i == total):
            print(f'{PROGRESS_MARKER}  detected {i}/{total} images', file=sys.stderr, flush=True)

    _write(args.responses, responses)


def _write(path, responses):
    with open(path, 'w') as f:
        json.dump({'version': 1, 'responses': responses}, f)


if __name__ == '__main__':
    main()

"""GeoSelect V2 stratified evaluation driver — the C4 attribution table.

C4 done RIGHT: detect ONCE per image (shared candidate pool), then evaluate
BOTH selectors over the SAME detections in one pass — so the per-stratum V2-vs-V1 delta is the
contribution of the selector ALONE, with detector + segmenter held fixed. (The earlier two-runs
design re-detected per selector, confounding the comparison; this fixes that.)

    V2 selector : program synthesis + executor, V1 fallback on illegal/empty
    V1 selector : V1 SpatialReasoner on the V1 parse (the baseline, same harness)

ONE Qwen3-4B is loaded (ProgramSynthesizer wraps a QwenParser, reused for the V1 parse). Eval
protocol = RMSIN (resize pred+GT to eval_size NEAREST). Per-sample diagnostics (program, classes,
#detections, chosen boxes, box-IoU, both IoUs) are dumped to JSONL for failure analysis.

VRAM staging: load parser -> synth + V1 parse -> UNLOAD -> detect (subprocess) -> load SAM -> mask.
Config-driven (v2_frozen.yaml); flags override.
    python -m geoselect_v2.eval.run_eval --dataset risbench --split val --n 50
"""

import argparse
import json
import os
import re
import sys
import time

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from geoselect_v2.config import load_config, get, data_root_for
from geoselect_v2.parser import ProgramSynthesizer
from geoselect_v2.parser.program_synthesis import load_prompt
from geoselect_v2.reliability import Resolver, select_types
from geoselect_v2.pipeline import _v1_classes
from geoselect_v2.eval.stratifier import stratum_tags, ALL_STRATA
from geoselect_v2.eval.stratified_metrics import StratifiedMetrics
from geoselect_v2.eval import cache as _cache


def _coerce(v):
    """Coerce a CLI override string to bool/int/float/None/list, else leave as str.
    A comma-separated value becomes a list (e.g. '512,512' -> [512, 512]) for keys like
    detection.slice_wh."""
    s = v.strip()
    if ',' in s:
        return [_coerce(x) for x in s.split(',')]
    low = s.lower()
    if low in ('true', 'false'):
        return low == 'true'
    if low in ('none', 'null'):
        return None
    for cast in (int, float):
        try:
            return cast(s)
        except ValueError:
            pass
    return v


def _apply_overrides(cfg, overrides):
    """Apply `--set dotted.key=value` overrides onto the loaded config dict in place.

    Used for parameter-sensitivity sweeps without writing a config variant per point. Only
    executor/kernels/detection keys matter downstream; parse-cache key is independent of these
    (it hashes model/prompt/split/n/batch), so a sweep never re-parses, and the detect cache is
    reused unless a `detection.*` key changes the actual detection inputs."""
    for item in overrides or []:
        if '=' not in item:
            raise ValueError(f'--set expects k=v, got {item!r}')
        dotted, val = item.split('=', 1)
        keys = dotted.strip().split('.')
        node = cfg
        for k in keys[:-1]:
            node = node.setdefault(k, {})
        node[keys[-1]] = _coerce(val)
        print(f'[override] {dotted.strip()} = {_coerce(val)!r}')


def _load_dataset(dataset, data_root, split):
    if dataset == 'rrsisd':
        from geogrounder.data.rrsisd_dataset import RRSISDDataset
        return RRSISDDataset(data_root, split=split)
    if dataset == 'risbench':
        from geogrounder.data.risbench_crobim_dataset import RISBenchCrobimDataset
        return RISBenchCrobimDataset(data_root, split=split)
    raise ValueError(f'unknown dataset {dataset!r}')


def _resize_nearest(mask, size):
    from PIL import Image
    if mask is None:
        return np.zeros((size, size), dtype=np.uint8)
    im = Image.fromarray((np.asarray(mask) > 0).astype(np.uint8) * 255)
    return (np.asarray(im.resize((size, size), Image.NEAREST)) > 127).astype(np.uint8)


def _box_iou(a, b):
    if a is None or b is None:
        return 0.0
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def _llmrank_prompt(sentence, target, boxes, wh):
    """'Let the LLM rank candidates' baseline prompt. Text-only: the LLM sees the
    referring expression + the candidate boxes as normalised [0,1000] integer coords (the Qwen
    convention) and must pick ONE index directly — no program, no executor. This isolates
    'explicit program execution' from 'implicit LLM selection' (SAME model, SAME candidate set,
    the only difference is whether a typed program mediates the choice)."""
    W, H = wh
    lines = []
    for j, b in enumerate(boxes):
        x1 = round(1000 * b[0] / max(W, 1)); y1 = round(1000 * b[1] / max(H, 1))
        x2 = round(1000 * b[2] / max(W, 1)); y2 = round(1000 * b[3] / max(H, 1))
        lines.append(f'{j}: [{x1}, {y1}, {x2}, {y2}]')
    cat = target or 'object'
    return (
        f'A remote-sensing image contains candidate "{cat}" objects. Each box is [x1, y1, x2, y2] '
        'on a 0-1000 grid (origin top-left; x increases rightward, y increases downward).\n'
        'Candidates:\n' + '\n'.join(lines) + '\n'
        'Which single candidate does the expression refer to?\n'
        f'Expression: "{sentence}"\n'
        'Answer with ONLY the candidate index number (a single integer). Index:'
    )


def _parse_index(raw, n):
    """First integer in the LLM reply, clamped to a valid candidate index (default 0 on miss)."""
    m = re.search(r'-?\d+', raw or '')
    if not m:
        return 0
    k = int(m.group())
    return k if 0 <= k < n else 0


# --- size-operator ablation: hypothetical area-extremal operator, pure-size only -------------
# A size superlative ('largest'/'smallest'/'longest'/...) with NO positional cue -> resolve by
# bounding-box AREA (max for larger-family, min for smaller-family) over the target class. Applied
# ONLY to these pure-size expressions so the selector coincides with v2 everywhere else (on RRSIS-D
# it therefore equals v2 exactly — 0 such cases). This is the diagnostic that answers "what would a
# dedicated size operator change?" without folding it into the frozen headline config.
_SIZE_MAX_RE = re.compile(r'\b(?:larg|bigg|hug|long|wid|tall)est\b', re.I)
_SIZE_MIN_RE = re.compile(r'\b(?:small|tini|short|narrow)est\b', re.I)
# Positional cues use word STEMS so 'northern'/'central'/'centrally'/'leftmost'/'nearest'/... are
# all caught (a size superlative that also carries any of these is NOT pure-size -> defer to v2).
_POS_CUE_RE = re.compile(
    r'\b(?:left\w*|right\w*|top\w*|bottom\w*|upper\w*|lower\w*|above|below|cent\w*|middle|'
    r'corner\w*|north\w*|south\w*|east\w*|west\w*|near\w*|closest|next to|between|beside|'
    r'adjacent|surround\w*)\b', re.I)


# --- comparative-size operator prototype (size-operator ablation) ----------------------------
# "A is bigger/smaller than B" or "the larger/smaller of the two X": a RELATION over candidates
# (compare box AREA), which the detector cannot express. Two forms:
#   (1) "...-er than <anchor with a positional cue>"  -> resolve the anchor box by its cue, then
#       pick the AREA-extreme box among the OTHER same-class candidates (the referent is the other
#       instance that is larger/smaller than the anchor);
#   (2) "the larger/smaller of the two X" OR "...-er than <no resolvable cue>"  -> AREA-extreme over
#       ALL same-class candidates (best guess when the anchor cannot be grounded geometrically).
# Falls through to v2 when no comparative structure -> the other ~98% of samples are byte-identical
# to v2 (so the operator can only change the comparative subset — never regress the rest).
_COMP_MAX_RE = re.compile(r'\b(?:larg|bigg|long|wid|tall|hug|great)er\b', re.I)   # want max area
# NOTE: 'lower' is EXCLUDED — it is almost always positional ("lower left"), not size-comparative;
# including it made compsize hijack directional cases. 'smaller/tinier/shorter/narrower' only.
_COMP_MIN_RE = re.compile(r'\b(?:small|tini|short|narrow)er\b', re.I)              # want min area
_OF_THE_RE = re.compile(r'\bof the (?:two|three|pair|group|several)\b', re.I)
_THAN_RE = re.compile(r'\bthan\b', re.I)


def _cue_pick(cands, part, hw):
    """Pick the box in `cands` matching a positional cue in text `part` (the substring after
    'than'); None if no groundable cue. Mirrors the rule-baseline geometry."""
    p = part.lower()
    H, W = hw
    def cx(b): return 0.5 * (b[0] + b[2])
    def cy(b): return 0.5 * (b[1] + b[3])
    if 'upper left' in p or 'top left' in p:     return min(cands, key=lambda b:  cx(b) + cy(b))
    if 'lower right' in p or 'bottom right' in p: return max(cands, key=lambda b:  cx(b) + cy(b))
    if 'upper right' in p or 'top right' in p:    return min(cands, key=lambda b: -cx(b) + cy(b))
    if 'lower left' in p or 'bottom left' in p:   return max(cands, key=lambda b: -cx(b) + cy(b))
    if re.search(r'\b(?:left|west)\b', p):              return min(cands, key=cx)
    if re.search(r'\b(?:right|east)\b', p):             return max(cands, key=cx)
    if re.search(r'\b(?:top|upper|north|above)\w*\b', p): return min(cands, key=cy)
    if re.search(r'\b(?:bottom|lower|south|below)\w*\b', p): return max(cands, key=cy)
    if re.search(r'\b(?:middle|cent\w*)\b', p):
        return min(cands, key=lambda b: (cx(b) - W / 2) ** 2 + (cy(b) - H / 2) ** 2)
    return None


def _compsize_terminal(sentence, rel, dets, hw):
    """Return [(box, 1.0)] for a comparative-size expression, else None (defer to v2)."""
    is_max = bool(_COMP_MAX_RE.search(sentence))
    is_min = bool(_COMP_MIN_RE.search(sentence))
    if not (is_max or is_min):
        return None
    # Require an EXPLICIT comparison reference — "... than ..." or "... of the two ..." — before
    # firing. A bare comparative adjective without a reference (rare, and easily a false positive)
    # defers to v2, so compsize touches only genuine comparative expressions and cannot regress the
    # directional cases it used to hijack.
    m_than = _THAN_RE.search(sentence)
    m_of = _OF_THE_RE.search(sentence)
    if not (m_than or m_of):
        return None
    cands = dets.get((rel or {}).get('target', ''), [])
    if not cands:
        return None
    def area(b): return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    ext = (lambda xs: max(xs, key=area)) if is_max else (lambda xs: min(xs, key=area))
    # form (1): "...-er than <anchor cue>" -> exclude the resolved anchor, pick area-extreme other
    if m_than and not m_of:
        anchor = _cue_pick(cands, sentence[m_than.end():], hw)
        if anchor is not None:
            others = [b for b in cands if b is not anchor]
            return [(ext(others) if others else anchor, 1.0)]
    # form (2): "of the two X" / comparative with no groundable anchor -> area-extreme over all
    return [(ext(cands), 1.0)]


def _sizeop_terminal(sentence, rel, dets):
    """Return [(box, 1.0)] if `sentence` is a PURE size superlative (size word, no positional cue)
    and target-class candidates exist, else None (defer to the v2 program). 'larger'-family -> max
    box area; 'smaller'-family -> min."""
    is_max = bool(_SIZE_MAX_RE.search(sentence))
    is_min = bool(_SIZE_MIN_RE.search(sentence))
    if not (is_max or is_min) or _POS_CUE_RE.search(sentence):
        return None
    cands = dets.get((rel or {}).get('target', ''), [])
    if not cands:
        return None
    def area(b):
        return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    return [(max(cands, key=area) if is_max else min(cands, key=area), 1.0)]


def make_masker(args, cfg, get):
    """Box->mask decoder (interface-compatible: load/predict). sam1 = SAM ViT-L (headline);
    sam2.1 / sam3 = decoder-ablation rows. Checkpoint paths come from the config."""
    seg = args.segmenter
    dev = get(cfg, 'parser.device', 'cuda')
    if seg == 'sam2.1':
        from geogrounder.segmentation import Sam2Masker
        ckpt = args.sam2_ckpt or get(cfg, 'weights.sam2_ckpt')
        scfg = args.sam2_cfg or get(cfg, 'weights.sam2_cfg', 'configs/sam2.1/sam2.1_hiera_l.yaml')
        return Sam2Masker(ckpt, scfg, device=dev)
    if seg == 'sam3':
        from geogrounder.segmentation import Sam3Masker
        path = args.sam3_path or get(cfg, 'weights.sam3_path')
        return Sam3Masker(path, use_text=args.sam3_text,
                          score_threshold=args.sam3_score_threshold, device=dev)
    from geogrounder.segmentation import Sam1Masker
    return Sam1Masker(args.sam1_path, device=dev)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default=None)
    ap.add_argument('--dataset', default=None, choices=['rrsisd', 'risbench'])
    ap.add_argument('--data-root', default=None)
    ap.add_argument('--split', default='val')
    ap.add_argument('--selectors', default='v1,v2',
                    help='comma list of selectors to score on the SAME candidates. '
                         'v2 = program executor (headline); v1 = continuous-fields-only ablation '
                         '("ours w/o discrete operators"); confidence = implicit detector-score '
                         'baseline; clip = GeoRSCLIP region<->text; rule = geometric rule baseline; '
                         'llmrank = LLM picks a box directly, no program; sizeop = v2 '
                         'plus an area operator on pure size SUPERLATIVES; compsize = v2 plus a '
                         'COMPARATIVE-size operator; sizeall = v2 plus BOTH. '
                         'All size selectors fall through to v2 off their subset.')
    ap.add_argument('--segmenter', choices=['sam1', 'sam2.1', 'sam3'], default='sam1',
                    help='box->mask decoder (headline sam1 = SAM ViT-L; sam2.1/sam3 = decoder ablation)')
    ap.add_argument('--sam2-ckpt', default=None)
    ap.add_argument('--sam2-cfg', default=None)
    ap.add_argument('--sam3-path', default=None)
    ap.add_argument('--sam3-text', action='store_true', help='SAM3: feed target concept (box+text)')
    ap.add_argument('--sam3-score-threshold', type=float, default=0.1)
    ap.add_argument('--georsclip-ckpt', default=None,
                    help='GeoRSCLIP ckpt for the `clip` implicit baseline (region<->text cosine)')
    ap.add_argument('--georsclip-model', default='ViT-H-14')
    ap.add_argument('--model-path', default=None)
    ap.add_argument('--batch-size', type=int, default=None)
    ap.add_argument('--eval-size', type=int, default=None)
    ap.add_argument('--n', type=int, default=0)
    ap.add_argument('--results-dir', default='experiments/runs',
                    help='parent folder for ALL run outputs (keeps experiments/ root tidy); each '
                         'run gets <results-dir>/eval_<ds>_<split><tag>/{summary.json,samples.jsonl}')
    ap.add_argument('--out-dir', default=None, help='full override of the per-run output folder')
    ap.add_argument('--tag', default='', help='suffix on the output folder to keep runs apart')
    ap.add_argument('--sam1-path', default=None)
    ap.add_argument('--serve-script', default='laedino_env/serve_detect.py')
    ap.add_argument('--conda-env', default='laedino')
    ap.add_argument('--detect-timeout', type=int, default=144000,
                    help='LAE-DINO subprocess timeout in seconds (default 40h). The client default '
                         'is only 1h, which times out on full test splits (e.g. RISBench ~7h).')
    ap.add_argument('--detect-chunk', type=int, default=2000,
                    help='checkpoint the detect cache every N images (0 = one batch). Protects a '
                         'long run: a failure only loses the in-flight chunk, re-run resumes.')
    ap.add_argument('--cache-dir', default='experiments/cache',
                    help='resume cache for parse + detect (keyed by prompt/model/params; a prompt '
                         'edit invalidates it automatically)')
    ap.add_argument('--no-cache', action='store_true', help='disable parse/detect caching')
    ap.add_argument('--vlm-parse', action='store_true',
                    help='parser ablation: synthesise programs with a Qwen3-VL parser, single-sentence. '
                         'Requires --model-path Qwen3-VL-*. With --vlm-no-image the image is '
                         'withheld (VL model, text-only) -> the middle ablation row; without it the '
                         'image is fed -> the visual-access row. Off by default; the text-only '
                         'Qwen3-4B headline path is unchanged.')
    ap.add_argument('--vlm-no-image', action='store_true',
                    help='parser-ablation Row2: run the VL parser but WITHHOLD the image (image=None), '
                         'so it synthesises from text alone. Row1(Qwen3-4B,txt) vs Row2(VL,txt) '
                         'isolates the model swap; Row2 vs Row3(VL,+image) isolates visual access. '
                         'Only meaningful with --vlm-parse.')
    ap.add_argument('--oracle', action='store_true',
                    help='also segment the best-box-IoU candidate -> oracle-selector ceiling + '
                         'per-stratum capture rate (V2 mIoU / oracle mIoU). Selector-independent; '
                         'adds one SAM call per image.')
    ap.add_argument('--keep-resident', action='store_true',
                    help='co-resident deployment mode: do NOT unload the parser after phase 1, so '
                         'Qwen stays in VRAM alongside SAM (and transiently the detector subprocess). '
                         'Trades peak VRAM for latency (no per-image reload in an online/streaming '
                         'server). Outputs are byte-identical to staged mode — only residency differs. '
                         'Pair with a background nvidia-smi sampler to read the true cross-process peak.')
    ap.add_argument('--set', dest='overrides', action='append', default=[], metavar='k=v',
                    help='override a config key (dotted), e.g. --set detection.box_threshold=0.20 '
                         '--set executor.direction_exponent=2.0. Repeatable. Affects executor/'
                         'kernels/detection params for parameter-sensitivity sweeps; parse cache '
                         'is unaffected (keyed on model/prompt/split only) and detection cache is '
                         'reused unless a detection.* key changes the candidate inputs.')
    args = ap.parse_args()

    cfg = load_config(args.config)
    _apply_overrides(cfg, args.overrides)
    args.dataset = args.dataset or get(cfg, 'data.dataset', 'rrsisd')
    args.data_root = args.data_root or data_root_for(cfg, args.dataset)
    args.model_path = args.model_path or get(cfg, 'weights.qwen')
    args.batch_size = args.batch_size or get(cfg, 'parser.batch_size', 16)
    args.eval_size = args.eval_size or get(cfg, 'eval.eval_size', 480)
    args.sam1_path = args.sam1_path or get(cfg, 'weights.sam_ckpt')
    selectors = [s.strip() for s in args.selectors.split(',') if s.strip()]
    if not args.out_dir:
        tag = f'_{args.tag}' if args.tag else ''
        args.out_dir = os.path.join(args.results_dir, f'eval_{args.dataset}_{args.split}{tag}')
    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, 'summary.json')
    diag_path = os.path.join(args.out_dir, 'samples.jsonl')

    ds = _load_dataset(args.dataset, args.data_root, args.split)
    samples = [ds[i] for i in range(len(ds) if args.n in (0, None) else min(args.n, len(ds)))]
    print(f'[eval] {len(samples)} samples  {args.dataset}/{args.split}  selectors={selectors}  '
          f'eval@{args.eval_size}')

    ctx_kwargs = {
        'near_scale': get(cfg, 'executor.near_scale', 1.5),
        'reference': get(cfg, 'executor.reference', 'centroid'),
        'score_method': get(cfg, 'executor.score_method', 'centroid'),
        'anchor_mode': get(cfg, 'executor.anchor_mode', 'marginalize'),
        'direction_exponent': get(cfg, 'executor.direction_exponent', 1.0),
        'center_sigma_frac': get(cfg, 'executor.center_sigma_frac', 0.25),
        'banded_d0_frac': get(cfg, 'kernels.banded_d0_frac', 1.0),
        'banded_sigma_frac': get(cfg, 'kernels.banded_sigma_frac', 0.5),
        'extremal_beta': get(cfg, 'kernels.extremal_beta', None),
    }
    group_tau = get(cfg, 'executor.group_tau', 0.8)

    sents = [s['sentence'] for s in samples]
    bs = max(1, args.batch_size)
    from geogrounder.utils.vram import empty_cache

    # --- per-stage latency + peak-VRAM instrumentation (mirrors V1). perf_counter markers at the
    #     phase boundaries + a SAM-time accumulator -> summary['timing'] (per-stage s + per-image
    #     ms). NOTE: run WITH --no-cache to time parse+detect honestly (a cache hit reads them as
    #     ~0). Peak VRAM is the MAIN process (parser/SAM); the LAE-DINO subprocess is separate. ---
    _t = {'start': time.perf_counter()}
    t_sam = 0.0
    try:
        import torch as _torch
        if _torch.cuda.is_available():
            _torch.cuda.reset_peak_memory_stats()
    except Exception:
        _torch = None

    # === Phase 1: parse (one Qwen load serves BOTH V2 synthesis AND V1 relation) ===========
    # Cache key hashes the PROMPT TEXT (V2 + V1) + model + split + n + batch -> a prompt edit
    # invalidates it automatically (no stale parse served while tuning); same config -> instant.
    from geogrounder.parsing.qwen_parser import PROMPT_TEMPLATE as V1_PROMPT
    v2_prompt = load_prompt(get(cfg, 'parser.prompt_path'))
    parse_mode = ('txt' if not args.vlm_parse else
                  ('vlm_noimg' if args.vlm_no_image else 'vlm_img'))   # distinct cache per E3 row
    parse_key = _cache.key(args.model_path, args.dataset, args.split, args.n, bs,
                           v2_prompt, V1_PROMPT, parse_mode)
    parse_path = None if args.no_cache else os.path.join(args.cache_dir, f'parse_{parse_key}.json')
    cached = _cache.load(parse_path)
    if cached is not None:
        programs, cards, v1_relations = cached['programs'], cached['cards'], cached['v1_relations']
        print(f'[1] parse: CACHE HIT ({parse_path}) — Qwen not loaded')
    else:
        synth = ProgramSynthesizer(args.model_path, device=get(cfg, 'parser.device', 'cuda'),
                                   dtype=get(cfg, 'parser.dtype', 'bfloat16'),
                                   max_new_tokens=get(cfg, 'parser.max_new_tokens', 512)).load()
        programs, cards, v1_relations = [], [], []
        try:
            from tqdm import tqdm
            pbar = tqdm(total=len(sents), desc='[1] parse: V2 program + V1 relation', unit='sent')
        except Exception:
            pbar = None
        if args.vlm_parse:
            # VL-parser synthesis, single-sentence (each image differs -> no batching).
            # --vlm-no-image withholds the image (Row2: VL model, text-only) so the model swap is
            # isolated from visual access. The V1 fallback parse always stays text-only on the SAME
            # model. Row1(Qwen3-4B,txt) / Row2(VL,txt) / Row3(VL,+image) -> a clean 2-variable ablation.
            if not synth._parser.is_vl:
                raise SystemExit('--vlm-parse requires a Qwen3-VL model (--model-path Qwen3-VL-*).')
            from PIL import Image
            _EMPTY_REL = {'target': '', 'cardinality': 'single', 'logic': 'and', 'relations': []}
            print(f'[1] VL parse: image {"WITHHELD (Row2, text-only)" if args.vlm_no_image else "FED (Row3, visual access)"}')
            for s, sent in zip(samples, sents):
                if args.vlm_no_image:
                    img = None                                  # Row2: VL model, text-only
                else:
                    try:
                        img = Image.open(s['image_path']).convert('RGB')
                    except Exception:
                        img = None                              # unreadable image -> text-only fall-through
                r = synth.synthesize(sent, image=img)
                programs.append(r.program_dict if r.legal else None)
                cards.append(r.cardinality)
                try:
                    v1_relations.append(synth._parser.parse(sent))     # text-only fallback parse
                except Exception:
                    v1_relations.append(dict(_EMPTY_REL))
                if pbar is not None:
                    pbar.update(1)
        else:
            for i in range(0, len(sents), bs):
                chunk = sents[i:i + bs]
                # V2 program synthesis (batched) + V1 relation parse (batched, same model, V1 prompt).
                for r in (synth.synthesize_batch(chunk) if bs > 1 else [synth.synthesize(chunk[0])]):
                    programs.append(r.program_dict if r.legal else None)
                    cards.append(r.cardinality)
                v1_relations.extend(synth.v1_parse_batch(chunk))   # baseline + V2 fallback, batched
                if pbar is not None:
                    pbar.update(len(chunk))
        if pbar is not None:
            pbar.close()
        # Co-resident mode keeps Qwen in VRAM through the detect + SAM phases (no per-image reload
        # in an online server); staged mode frees it here so peak VRAM = max single stage. Skipping
        # the unload cannot change any downstream output — only the memory footprint.
        if not args.keep_resident:
            synth.unload()
        empty_cache()
        if parse_path:
            _cache.save(parse_path, {'programs': programs, 'cards': cards,
                                     'v1_relations': v1_relations})
            print(f'[1] parse: cached -> {parse_path}')

    _t['parse'] = time.perf_counter()
    # Per-phase peak VRAM (main process): capture the PARSER peak now, then reset so the later
    # SAM peak is measured cleanly in isolation (the detector runs in a separate subprocess, so
    # it is measured out-of-band). Gives the staged per-stage footprint, not just a global max.
    _vram = {}
    if _torch is not None and _torch.cuda.is_available():
        _vram['parse_gb'] = round(_torch.cuda.max_memory_allocated() / 1e9, 2)
        _torch.cuda.reset_peak_memory_stats()

    # === Phase 2: detect ONCE per image over the UNION of classes (shared candidate pool) ==
    from geogrounder.detection import LaeDinoClient, DetectionRequest
    from geogrounder.detection.protocol import DetectionResponse
    slice_wh = get(cfg, 'detection.slice_wh', [768, 768])
    if isinstance(slice_wh, int):
        slice_wh = [slice_wh, slice_wh]
    box_thr = get(cfg, 'detection.box_threshold', 0.15)
    use_slicing = get(cfg, 'detection.use_slicing', True)
    requests = []
    for i, s in enumerate(samples):
        classes = set(_v1_classes(v1_relations[i]))
        if programs[i] is not None:
            classes |= select_types(programs[i])
        requests.append(DetectionRequest(
            image_path=s['image_path'], prompts=sorted(c for c in classes if c) or ['object'],
            box_threshold=box_thr, use_slicing=use_slicing, slice_wh=list(slice_wh)))

    # Per-image detect cache (PROMPT-INDEPENDENT): keyed on the ACTUAL detection inputs
    # (image + class prompts + params), NOT on parse_key. So a prompt edit that changes only the
    # kernel/resolution logic (e.g. BANDED->MONOTONE) but not the class list reuses detections —
    # the hours-long LAE-DINO pass is skipped for every image whose class set is unchanged. The
    # index persists across runs/datasets (image_path is in the key, so no collision).
    def _req_key(r):
        return _cache.key('det1', r.image_path, tuple(r.prompts), box_thr, use_slicing,
                          tuple(slice_wh))
    index_path = None if args.no_cache else os.path.join(args.cache_dir, 'detect_index.json')
    index = _cache.load(index_path) or {}
    keys = [_req_key(r) for r in requests]
    todo = [(i, requests[i]) for i, k in enumerate(keys) if k not in index]
    print(f'[2] detect: {len(requests) - len(todo)}/{len(requests)} cached, {len(todo)} to detect')
    if todo:
        client = LaeDinoClient(args.serve_script, conda_env=args.conda_env,
                               timeout=args.detect_timeout)
        # Chunked detection: checkpoint the cache after EACH chunk so a mid-run failure (timeout/
        # OOM/disconnect) on a long split only loses the in-flight chunk — re-running resumes from
        # the cached chunks. chunk=0 -> one batch (legacy). Per-chunk overhead = one model load.
        chunk = args.detect_chunk if args.detect_chunk and args.detect_chunk > 0 else len(todo)
        for c0 in range(0, len(todo), chunk):
            part = todo[c0:c0 + chunk]
            fresh = client.detect_batch([r for _, r in part])
            for (i, _), resp in zip(part, fresh):
                index[keys[i]] = resp.to_json()
            if index_path:
                _cache.save(index_path, index)        # checkpoint after each chunk
            print(f'[2] detect: cached {c0 + len(part)}/{len(todo)} (checkpoint)')
    responses = [DetectionResponse.from_json(index[k]) for k in keys]
    _t['detect'] = time.perf_counter()

    # === Phase 2.5: LLM-ranking baseline ===================================================
    # Reload the text-only LLM AFTER detection so it can SEE the candidate boxes, then ask it to
    # pick ONE index directly (no program, no executor). Staged in its OWN phase (load -> rank ->
    # unload) BEFORE SAM, so the LLM never co-resides with the segmenter. Single candidate short-
    # circuits (no call); zero candidates -> empty. Only runs if 'llmrank' is among the selectors.
    llmrank_choice = None
    if 'llmrank' in selectors:
        from geogrounder.parsing.qwen_parser import QwenParser
        from PIL import Image
        ranker = QwenParser(args.model_path, device=get(cfg, 'parser.device', 'cuda'),
                            dtype=get(cfg, 'parser.dtype', 'bfloat16'), max_new_tokens=16).load()
        if ranker.is_vl:
            raise SystemExit('llmrank baseline expects the TEXT-ONLY parser (Qwen3-4B), not a VL model.')
        llmrank_choice = [None] * len(samples)
        try:
            from tqdm import tqdm
            rbar = tqdm(total=len(samples), desc='[2.5] llmrank: LLM picks a box', unit='smp')
        except Exception:
            rbar = None
        for i, s in enumerate(samples):
            tgt = (v1_relations[i] or {}).get('target', '')
            cands = responses[i].by_label().get(tgt, [])
            if len(cands) == 1:
                llmrank_choice[i] = cands[0]              # trivial: one candidate -> no LLM call
            elif len(cands) > 1:
                try:
                    W, H = Image.open(s['image_path']).size
                except Exception:
                    W, H = 1, 1
                raw = ranker.generate(_llmrank_prompt(s['sentence'], tgt, cands, (W, H)))
                llmrank_choice[i] = cands[_parse_index(raw, len(cands))]
            if rbar is not None:
                rbar.update(1)
        if rbar is not None:
            rbar.close()
        ranker.unload()
        empty_cache()
    _t['llmrank'] = time.perf_counter()

    # === Phase 3: resolve BOTH selectors over the SAME detections, segment, score ==========
    from geogrounder.data.rrsisd_dataset import RRSISDDataset
    masker = make_masker(args, cfg, get).load()
    resolver = Resolver(group_tau=group_tau)
    clip_selector = None
    if 'clip' in selectors:                  # implicit baseline: GeoRSCLIP region<->text cosine
        from geogrounder.rerank.georsclip_select import GeoRSClipSelector
        ck = args.georsclip_ckpt or get(cfg, 'weights.georsclip')
        clip_selector = GeoRSClipSelector(ck, args.georsclip_model,
                                          get(cfg, 'parser.device', 'cuda')).load()
    thr = tuple(get(cfg, 'eval.thresholds', [0.5, 0.6, 0.7, 0.8, 0.9]))
    sm = {sel: StratifiedMetrics(ALL_STRATA, thresholds=thr) for sel in selectors}
    if args.oracle:
        sm['oracle'] = StratifiedMetrics(ALL_STRATA, thresholds=thr)

    def _rule_select(rel, dets, hw):
        """Rule-based spatial baseline: pick a target-class box by ONE image-frame
        heuristic — no program, no LLM. A single directional cue -> the extreme box on that axis;
        a corner -> the diagonal extreme; centre/near -> the box nearest the image centre; anything
        relational, nested, or pure-attribute -> the largest box. Returns [(box, score)] or []."""
        H, W = hw
        cands = dets.get((rel or {}).get('target', ''), [])
        if not cands:
            return []
        def cx(b): return 0.5 * (b[0] + b[2])
        def cy(b): return 0.5 * (b[1] + b[3])
        def area(b): return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
        rels = (rel or {}).get('relations', [])
        if len(rels) == 1 and rels[0].get('anchor') == 'image':
            p = str(rels[0].get('predicate', '')).lower()
            pick = {
                'right': lambda: max(cands, key=cx),  'east': lambda: max(cands, key=cx),
                'left': lambda: min(cands, key=cx),   'west': lambda: min(cands, key=cx),
                'bottom': lambda: max(cands, key=cy), 'south': lambda: max(cands, key=cy),
                'below': lambda: max(cands, key=cy),
                'top': lambda: min(cands, key=cy),    'north': lambda: min(cands, key=cy),
                'above': lambda: min(cands, key=cy),
                'upper right': lambda: min(cands, key=lambda x: -cx(x) + cy(x)),
                'upper left':  lambda: min(cands, key=lambda x:  cx(x) + cy(x)),
                'lower right': lambda: max(cands, key=lambda x:  cx(x) + cy(x)),
                'lower left':  lambda: max(cands, key=lambda x: -cx(x) + cy(x)),
                'center': lambda: min(cands, key=lambda x: (cx(x)-W/2)**2 + (cy(x)-H/2)**2),
                'centre': lambda: min(cands, key=lambda x: (cx(x)-W/2)**2 + (cy(x)-H/2)**2),
                'near':   lambda: min(cands, key=lambda x: (cx(x)-W/2)**2 + (cy(x)-H/2)**2),
            }.get(p)
            b = pick() if pick else max(cands, key=area)
        else:
            b = max(cands, key=area)      # no cue / relational / nested / attribute -> largest
        return [(b, 1.0)]

    def resolve_one(sel, i, dets, dets_scored, hw):
        if sel == 'rule':
            # rule-based spatial baseline over the SAME candidates (no program/LLM).
            return {'terminal': _rule_select(v1_relations[i], dets, hw),
                    'ranked': [], 'mode': 'rule', 'prior': None}
        if sel == 'llmrank':
            # LLM directly picks a box (precomputed in Phase 2.5), no program/executor.
            b = llmrank_choice[i] if llmrank_choice else None
            term = [(b, 1.0)] if b is not None else []
            return {'terminal': term, 'ranked': [], 'mode': 'llmrank', 'prior': None}
        if sel == 'sizeop':
            # size-operator diagnostic: v2 program + a hypothetical area-extremal operator on PURE size
            # superlatives only. If the sentence is a pure size superlative -> area max/min over the
            # target class; otherwise fall through to the exact v2 program result (so sizeop == v2
            # everywhere except those cases, and == v2 identically on RRSIS-D).
            ov = _sizeop_terminal(samples[i]['sentence'], v1_relations[i], dets)
            if ov is not None:
                return {'terminal': ov, 'ranked': [], 'mode': 'sizeop', 'prior': None}
            # no size override -> identical to v2 (fall through to the program resolution below)
        if sel == 'compsize':
            # comparative-size prototype: v2 program + a comparative-size operator. Comparative structure ->
            # area-relational selection over the SAME candidates; otherwise identical to v2 (so the
            # non-comparative ~98% cannot regress).
            ov = _compsize_terminal(samples[i]['sentence'], v1_relations[i], dets, hw)
            if ov is not None:
                return {'terminal': ov, 'ranked': [], 'mode': 'compsize', 'prior': None}
            # no comparative override -> identical to v2 (fall through below)
        if sel == 'sizeall':
            # the FULL size operator = comparative first, else pure
            # superlative, else v2. Disjoint triggers, so this is v2 + both size sub-ops combined —
            # the headline effect of actually adding size handling.
            ov = (_compsize_terminal(samples[i]['sentence'], v1_relations[i], dets, hw)
                  or _sizeop_terminal(samples[i]['sentence'], v1_relations[i], dets))
            if ov is not None:
                return {'terminal': ov, 'ranked': [], 'mode': 'sizeall', 'prior': None}
            # no size override -> identical to v2 (fall through below)
        if sel == 'confidence':
            # implicit baseline: pick the highest detector-confidence box of the target class
            # (no geometry / no program). The C4 "explicit program vs implicit matching" row.
            tgt = (v1_relations[i] or {}).get('target', '')
            scored = dets_scored.get(tgt, [])
            best = max(scored, key=lambda bs: bs[1]) if scored else None
            term = [(best[0], float(best[1]))] if best else []
            return {'ranked': term, 'terminal': term, 'mode': 'confidence', 'prior': None}
        if sel == 'v1':
            return resolver.resolve(None, v1_relations[i], dets, hw, cardinality='single',
                                    ctx_kwargs=ctx_kwargs)
        return resolver.resolve(programs[i], v1_relations[i], dets, hw,
                                cardinality=cards[i], ctx_kwargs=ctx_kwargs)

    try:
        from tqdm import tqdm
        it = tqdm(range(len(samples)), desc='[3] resolve+segment', unit='smp')
    except Exception:
        it = range(len(samples))

    df = open(diag_path, 'w', encoding='utf-8')
    for i in it:
        s = samples[i]; gt = s['gt_mask']; H, W = gt.shape
        dets = responses[i].by_label()
        dets_scored = responses[i].by_label_scored()      # for the confidence baseline
        g = _resize_nearest(gt, args.eval_size)
        gt_box = s.get('gt_bbox_xyxy')
        tags = stratum_tags(s['sentence'])
        rec = {'sentence': s['sentence'], 'tags': sorted(tags),
               'file_name': s.get('file_name'), 'image_path': s.get('image_path'),
               'program': programs[i], 'n_det': {k: len(v) for k, v in dets.items()}}
        image = None
        for sel in selectors:
            if sel == 'clip':
                # implicit baseline: rank the target-class candidates by GeoRSCLIP(crop, sentence)
                # cosine; no geometry. The 2nd "explicit vs implicit" C4 row (alongside confidence).
                cb = dets.get((v1_relations[i] or {}).get('target', ''), [])
                if cb:
                    if image is None:
                        image = RRSISDDataset.load_image(s['image_path'])
                    cs = clip_selector.score(image, cb, s['sentence'])
                    bi = int(np.argmax(cs))
                    res = {'terminal': [(cb[bi], float(cs[bi]))], 'mode': 'clip', 'ranked': []}
                else:
                    res = {'terminal': [], 'mode': 'clip', 'ranked': []}
            else:
                res = resolve_one(sel, i, dets, dets_scored, (H, W))
            boxes = [b for b, _ in res['terminal']]
            pred = None
            if boxes:
                if image is None:
                    image = RRSISDDataset.load_image(s['image_path'])
                # Build pred at the MASK's native size (SAM masks the IMAGE, whose H/W can differ
                # from the GT mask by ~1px in RRSIS-D). pred and GT are each resized to eval_size
                # NEAREST below, so the off-by-one is washed out — do NOT force a common shape here.
                for b in boxes:
                    _ts = time.perf_counter()
                    m = (np.asarray(masker.predict(image, b)) > 0).astype(np.uint8)
                    t_sam += time.perf_counter() - _ts
                    pred = m if pred is None else (pred | m)
            if pred is None:
                pred = np.zeros((H, W), dtype=np.uint8)
            pe = _resize_nearest(pred, args.eval_size)
            iou = sm[sel].add(pe, g, tags=tags, mode=res['mode'])
            rec[f'{sel}_iou'] = round(float(iou), 4)
            # log intersection/union so any post-hoc subset (e.g. leakage seen/unseen) can report
            # oIoU = sum(I)/sum(U), not just mIoU = mean(per-sample IoU).
            rec[f'{sel}_I'] = int(np.logical_and(pe, g).sum())
            rec[f'{sel}_U'] = int(np.logical_or(pe, g).sum())
            rec[f'{sel}_mode'] = res['mode']
            rec[f'{sel}_boxes'] = [[round(c, 1) for c in b] for b in boxes]
            rec[f'{sel}_boxIoU'] = round(max([_box_iou(b, gt_box) for b in boxes], default=0.0), 3)

        # Oracle-selector ceiling: segment the candidate box with the best box-IoU to GT (the best
        # ANY selector could do given these candidates). Selector-independent -> isolates the
        # selection loss; capture rate = V2 mIoU / oracle mIoU, per stratum.
        if args.oracle:
            all_boxes = [b for bs in dets.values() for b in bs]
            opred = None
            if all_boxes:
                obox = max(all_boxes, key=lambda b: _box_iou(b, gt_box))
                if image is None:
                    image = RRSISDDataset.load_image(s['image_path'])
                _ts = time.perf_counter()
                opred = (np.asarray(masker.predict(image, obox)) > 0).astype(np.uint8)
                t_sam += time.perf_counter() - _ts
            oe = _resize_nearest(opred, args.eval_size) if opred is not None else _resize_nearest(None, args.eval_size)
            oiou = sm['oracle'].add(oe, g, tags=tags)
            rec['oracle_iou'] = round(float(oiou), 4)
            rec['oracle_boxIoU'] = round(max([_box_iou(b, gt_box) for b in all_boxes], default=0.0), 3)
        df.write(json.dumps(rec, ensure_ascii=False) + '\n')
    df.close()
    _t['seg'] = time.perf_counter()
    # Segmenter (SAM, + GeoRSCLIP if used) peak, isolated from the parser by the reset above.
    if _torch is not None and _torch.cuda.is_available():
        _vram['seg_gb'] = round(_torch.cuda.max_memory_allocated() / 1e9, 2)
    masker.unload()
    if clip_selector is not None:
        clip_selector.unload()
    empty_cache()

    # === report ===========================================================================
    out = {'args': vars(args), 'by_selector': {}}

    # latency (mirrors V1): per-stage seconds + per-image ms. parse/detect read ~0 on a cache
    # hit -> run with --no-cache for an honest end-to-end number.
    n = max(1, len(samples))
    n_img = max(1, len({s['image_path'] for s in samples}))
    phase3 = _t['seg'] - _t['llmrank']            # exclude the optional llmrank phase from phase-3
    out['timing'] = {
        'parse_s': round(_t['parse'] - _t['start'], 2),
        'detect_s': round(_t['detect'] - _t['parse'], 2),
        'llmrank_s': round(_t['llmrank'] - _t['detect'], 2),
        'phase3_s': round(phase3, 2),
        'sam_s': round(t_sam, 2),
        'reason_s': round(phase3 - t_sam, 2),
        'per_image_ms': {
            'parse': round(1000 * (_t['parse'] - _t['start']) / n, 1),
            'detect': round(1000 * (_t['detect'] - _t['parse']) / n_img, 1),
            'reason': round(1000 * (phase3 - t_sam) / n, 1),
            'sam': round(1000 * t_sam / n, 1),
            'total': round(1000 * (_t['seg'] - _t['start']) / n, 1),
        },
        'cache_used': not args.no_cache,
    }
    out['timing']['vram_gb'] = _vram          # {'parse_gb':..,'seg_gb':..} per-stage main-proc peak
    if _torch is not None and _torch.cuda.is_available():
        out['peak_vram_gb'] = round(_torch.cuda.max_memory_allocated() / 1e9, 2)
    print()
    for sel in list(sm):                      # selectors + 'oracle' if present
        out['by_selector'][sel] = sm[sel].summary()
        print(f'### selector={sel}')
        print(sm[sel].format())
        print()
    if args.oracle and 'v2' in selectors:
        print('### oracle capture rate (V2 mIoU / oracle mIoU, per stratum)')
        bo = out['by_selector']['oracle']['by_stratum']; b2 = out['by_selector']['v2']['by_stratum']
        for t in sorted(set(bo) | set(b2)):
            o = bo.get(t, {}).get('mIoU', 0) * 100; v = b2.get(t, {}).get('mIoU', 0) * 100
            cap = (v / o * 100) if o > 0 else 0.0
            print(f'  {t:14} V2={v:5.2f}  oracle={o:5.2f}  capture={cap:5.1f}%')
        oo = out['by_selector']['oracle']['overall']['mIoU'] * 100
        vo = out['by_selector']['v2']['overall']['mIoU'] * 100
        print(f'  {"OVERALL":14} V2={vo:5.2f}  oracle={oo:5.2f}  capture={vo/oo*100:5.1f}%')
    if 'v1' in selectors and 'v2' in selectors:
        print('### C4 per-stratum delta (V2 - V1, mIoU)')
        b1, b2 = out['by_selector']['v1']['by_stratum'], out['by_selector']['v2']['by_stratum']
        for t in sorted(set(b1) | set(b2)):
            m1 = b1.get(t, {}).get('mIoU', 0) * 100
            m2 = b2.get(t, {}).get('mIoU', 0) * 100
            print(f'  {t:14} V1={m1:5.2f}  V2={m2:5.2f}  delta={m2-m1:+.2f}')
    pim = out['timing']['per_image_ms']
    print(f"### timing (per image): total={pim['total']:.0f}ms  parse={pim['parse']:.0f}  "
          f"detect={pim['detect']:.0f}  reason={pim['reason']:.1f}  sam={pim['sam']:.0f}  "
          f"(cache_used={out['timing']['cache_used']})")
    if 'peak_vram_gb' in out:
        print(f"### peak VRAM (main proc): {out['peak_vram_gb']} GB")
    json.dump(out, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\n[eval] summary -> {out_path}\n[eval] per-sample diagnostics -> {diag_path}')


if __name__ == '__main__':
    main()

"""Program-legality gate — quantify DSL synthesis quality BEFORE
committing to V2. If the legal rate is too low, V2's reliability is below V1 and V2 does not
stand.

Runs program synthesis over a dataset split and reports:
  * legal rate     — fraction of sentences whose program passes typecheck (executes on V2)
  * fallback rate  — 1 - legal rate (would fall back to the V1 closed-vocabulary parse)
  * op histogram   — which DSL operators the synthesiser actually uses (coverage sanity)
  * error histogram— why illegal programs fail (drives prompt/grammar tightening)

It also dumps every (sentence, raw, program, legal, errors) to JSONL so the ~100-sample manual
SEMANTIC-correctness check can be done offline. The semantic check
is human-judged — this script measures legality (machine-checkable), not semantic correctness.

Config-driven: paths default to geoselect_v2/configs/v2_frozen.yaml, so the common
case needs no path flags. Any flag, when given, OVERRIDES the config.

Usage (needs the parser LLM + a dataset; single GPU is enough — text-only parser):
    # uses v2_frozen.yaml for data-root + model-path + dataset:
    python scripts/eval_program_legality.py --split val --dedup \
        --out experiments/phase0_legality_val.jsonl
    # or override anything:
    python scripts/eval_program_legality.py --dataset risbench --split val \
        --model-path /path/Qwen3-8B --dedup

--limit 0 = all samples. --dedup keeps one program per UNIQUE sentence (legality is a property
of the text, so dedup avoids over-counting repeated sentences).
"""

import argparse
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from geoselect_v2.parser import ProgramSynthesizer
from geoselect_v2.parser.grammar import walk
from geoselect_v2.config import load_config, get, data_root_for


def _ops_used(program_node):
    return sorted({n.op for n in walk(program_node)}) if program_node is not None else []


def _load_sentences(args):
    """-> list of sentences from the requested dataset split (RRSIS-D / RISBench).

    Imports the loader class LAZILY from its submodule (not via geogrounder.data.__init__) so
    (a) the rrsisd path never touches the RISBench loader, and (b) we don't depend on the
    package __init__ re-exporting the class."""
    if args.dataset == 'rrsisd':
        from geogrounder.data.rrsisd_dataset import RRSISDDataset
        ds = RRSISDDataset(args.data_root, split=args.split)
    elif args.dataset == 'risbench':
        # Original CrOBIM layout (img_rgb/ + mask/ + output_phrase_<split>.txt) -> RISBench_orig.
        from geogrounder.data.risbench_crobim_dataset import RISBenchCrobimDataset
        ds = RISBenchCrobimDataset(args.data_root, split=args.split)
    else:
        raise ValueError(f'unknown dataset {args.dataset!r}')
    n = len(ds) if args.limit in (0, None) else min(args.limit, len(ds))
    sents = [ds[i]['sentence'] for i in range(n)]
    if args.dedup:
        seen, uniq = set(), []
        for s in sents:
            if s not in seen:
                seen.add(s)
                uniq.append(s)
        return uniq
    return sents


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default=None, help='V2 config YAML (default: packaged v2_frozen.yaml)')
    # paths/params default to the config; pass a flag only to OVERRIDE it.
    ap.add_argument('--data-root', default=None)
    ap.add_argument('--dataset', default=None, choices=['rrsisd', 'risbench'])
    ap.add_argument('--split', default='val')
    ap.add_argument('--model-path', default=None, help='text-only parser LLM (e.g. Qwen3-4B)')
    ap.add_argument('--device', default=None)
    ap.add_argument('--dtype', default=None)
    ap.add_argument('--max-new-tokens', type=int, default=None)
    ap.add_argument('--prompt-path', default=None)
    ap.add_argument('--batch-size', type=int, default=None,
                    help='sentences per generate() call; >1 = batched (big speedup). '
                         'Default from config (parser.batch_size).')
    ap.add_argument('--limit', type=int, default=0, help='0 = all samples')
    ap.add_argument('--dedup', action='store_true', help='one program per unique sentence')
    ap.add_argument('--out', default='experiments/phase0_legality.jsonl')
    args = ap.parse_args()

    # Resolve config -> fill any unset arg (override > config > built-in default).
    cfg = load_config(args.config)
    args.dataset = args.dataset or get(cfg, 'data.dataset', 'rrsisd')
    args.data_root = args.data_root or data_root_for(cfg, args.dataset)
    args.model_path = args.model_path or get(cfg, 'weights.qwen')
    args.device = args.device or get(cfg, 'parser.device', 'cuda')
    args.dtype = args.dtype or get(cfg, 'parser.dtype', 'bfloat16')
    args.max_new_tokens = args.max_new_tokens or get(cfg, 'parser.max_new_tokens', 512)
    args.prompt_path = args.prompt_path or get(cfg, 'parser.prompt_path')
    args.batch_size = args.batch_size or get(cfg, 'parser.batch_size', 16)
    if not args.data_root or not args.model_path:
        ap.error('data-root and model-path must be set via --flags or the config')
    print(f'[phase0] config={args.config or "packaged v2_frozen.yaml"}  '
          f'data_root={args.data_root}  model={args.model_path}')

    sentences = _load_sentences(args)
    print(f'[phase0] {len(sentences)} sentences from {args.dataset}/{args.split} '
          f'(dedup={args.dedup})')

    synth = ProgramSynthesizer(args.model_path, device=args.device, dtype=args.dtype,
                               max_new_tokens=args.max_new_tokens,
                               prompt_path=args.prompt_path).load()

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or '.', exist_ok=True)
    n_legal = 0
    op_hist, err_hist, card_hist = Counter(), Counter(), Counter()

    bs = max(1, args.batch_size)
    print(f'[phase0] batch_size={bs}  max_new_tokens={args.max_new_tokens}')
    try:
        from tqdm import tqdm
        bar = tqdm(total=len(sentences), desc='[phase0] synthesize', unit='sent')
    except Exception:
        bar = None

    with open(args.out, 'w', encoding='utf-8') as f:
        for i in range(0, len(sentences), bs):
            chunk = sentences[i:i + bs]
            results = synth.synthesize_batch(chunk) if bs > 1 else [synth.synthesize(chunk[0])]
            for s, r in zip(chunk, results):
                n_legal += int(r.legal)
                card_hist[r.cardinality] += 1
                if r.legal:
                    op_hist.update(_ops_used(r.program))
                else:
                    # bucket by the error KIND (first token), not the full message
                    err_hist[r.errors[0].split(':')[0] if r.errors else 'unknown'] += 1
                f.write(json.dumps({
                    'sentence': s, 'raw': r.raw, 'program': r.program_dict,
                    'cardinality': r.cardinality, 'legal': r.legal, 'errors': r.errors,
                    'select_types': r.select_types,
                }, ensure_ascii=False) + '\n')
            if bar is not None:
                bar.update(len(chunk))
    if bar is not None:
        bar.close()

    synth.unload()

    n = len(sentences)
    legal_rate = n_legal / n if n else 0.0
    print('\n' + '=' * 60)
    print(f'[phase0] legal rate    = {legal_rate * 100:.2f}%  ({n_legal}/{n})')
    print(f'[phase0] fallback rate = {(1 - legal_rate) * 100:.2f}%  (-> V1)')
    print(f'[phase0] cardinality   = {dict(card_hist)}')
    print(f'[phase0] ops used      = {dict(op_hist.most_common())}')
    print(f'[phase0] error kinds   = {dict(err_hist.most_common())}')
    print(f'[phase0] dump          = {args.out}')
    print('=' * 60)
    print('NEXT: hand-judge ~100 LEGAL programs for SEMANTIC correctness. '
          'If legal rate < 85%, tighten the few-shot prompt / grammar before trusting V2.')


if __name__ == '__main__':
    main()

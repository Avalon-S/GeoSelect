"""Few-shot leakage guard — verify the program-synthesis prompt's in-context example sentences
do NOT appear VERBATIM in any dataset split (eval-set leakage). They may be CLOSE in style, but
an exact (normalised) match to a real eval sentence is contamination and must be edited.

Same discipline V1 enforced (geogrounder.parsing.qwen_parser: "Few-shot examples ... verified
DISJOINT from RRSIS-D val/test by exact-match"). Run this on EACH server (RRSIS-D and RISBench
live on different machines) — it checks the prompt examples against whatever dataset is local:

    python scripts/check_fewshot_leakage.py --dataset rrsisd --splits train val test
    python scripts/check_fewshot_leakage.py --dataset risbench --splits val test

Normalisation: lowercase, strip surrounding quotes/punctuation, collapse whitespace, drop a
trailing period. So "A dam on the right." == "a dam on the right" (a real collision), but a
one-word difference is NOT flagged (close-but-different is allowed). Exit code 1 if ANY example
collides with a val/test split (the eval sets); train collisions are reported as a warning.
Model-free + fast (text only, no GPU, no synthesis).
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from geoselect_v2.config import load_config, get, data_root_for
from geoselect_v2.parser.program_synthesis import load_prompt


def _norm(s: str) -> str:
    s = str(s).strip().lower().strip('"\'')
    s = re.sub(r'[.\s]+$', '', s)          # drop trailing period(s)/space
    return re.sub(r'\s+', ' ', s).strip()


def _example_sentences(prompt_path=None):
    tmpl = load_prompt(prompt_path)
    return re.findall(r'^"(.+?)"\s*->', tmpl, flags=re.MULTILINE)


def _dataset_sentences(dataset, data_root, split):
    if dataset == 'rrsisd':
        from geogrounder.data.rrsisd_dataset import RRSISDDataset
        ds = RRSISDDataset(data_root, split=split)
    elif dataset == 'risbench':
        from geogrounder.data.risbench_crobim_dataset import RISBenchCrobimDataset
        ds = RISBenchCrobimDataset(data_root, split=split)
    else:
        raise ValueError(f'unknown dataset {dataset!r}')
    return [ds[i]['sentence'] for i in range(len(ds))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default=None)
    ap.add_argument('--dataset', default=None, choices=['rrsisd', 'risbench'])
    ap.add_argument('--data-root', default=None)
    ap.add_argument('--splits', nargs='+', default=None,
                    help='splits to check (default: rrsisd=train val test, risbench=val test)')
    ap.add_argument('--prompt-path', default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    args.dataset = args.dataset or get(cfg, 'data.dataset', 'rrsisd')
    args.data_root = args.data_root or data_root_for(cfg, args.dataset)
    if args.splits is None:
        args.splits = ['train', 'val', 'test'] if args.dataset == 'rrsisd' else ['val', 'test']

    examples = _example_sentences(args.prompt_path)
    ex_norm = {_norm(e): e for e in examples}
    print(f'[leakage] {len(examples)} few-shot examples vs {args.dataset} '
          f'splits={args.splits}  root={args.data_root}')

    eval_collisions, train_collisions = [], []
    for split in args.splits:
        try:
            sents = _dataset_sentences(args.dataset, args.data_root, split)
        except Exception as e:
            print(f'[leakage]   ! could not load split {split!r}: {type(e).__name__}: {e}')
            continue
        norm_set = {}
        for s in sents:
            norm_set.setdefault(_norm(s), s)
        hits = [(ex_norm[k], norm_set[k]) for k in ex_norm if k in norm_set]
        tag = 'EVAL' if split in ('val', 'validation', 'test') else 'train'
        print(f'[leakage]   {split}: {len(sents)} sentences, {len(hits)} collision(s)'
              f'{" [EVAL — BLOCKER]" if hits and tag == "EVAL" else ""}')
        for ex, real in hits:
            print(f'              - example {ex!r}  ==  {split} {real!r}')
            (eval_collisions if tag == 'EVAL' else train_collisions).append((split, ex, real))

    print('=' * 60)
    if eval_collisions:
        print(f'[leakage] FAIL: {len(eval_collisions)} example(s) leak into val/test. '
              f'Edit them in geoselect_v2/prompts/program_synthesis_fewshot.txt to be '
              f'close-but-not-identical, then re-run.')
        sys.exit(1)
    if train_collisions:
        print(f'[leakage] WARN: {len(train_collisions)} example(s) match TRAIN (training-free, '
              f'so not an eval leak — but consider editing for cleanliness).')
    print('[leakage] OK: no eval-set leakage detected for this dataset.')


if __name__ == '__main__':
    main()

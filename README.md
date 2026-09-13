# GeoSelect: Spatial-Program Execution for Training-Free Referring Remote Sensing Image Segmentation

[![Paper](https://img.shields.io/badge/Paper-arXiv%3A2607.03869-red)](https://arxiv.org/abs/2607.03869)
[![Project Page](https://img.shields.io/badge/Project-Page-blue)](https://avalon-s.github.io/GeoSelect/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Venue](https://img.shields.io/badge/IEEE%20TGRS-accepted-brightgreen)](#citation)

**English** · [简体中文](README_zh.md)

GeoSelect segments the single object an aerial image's referring expression names, **without
training anything**. A frozen text-only LLM compiles the expression into a typed program in a
small spatial DSL; a well-formedness checker accepts it; and a deterministic executor evaluates
it over one *scored candidate set* that unifies continuous geometric fields with discrete set and
order operators. A reliability ladder degrades any failing program to the field-only special case
rather than forfeiting an answer.

![Why explicit execution](assets/teaser.jpg)

*Implicit region–text matching picks the wrong aircraft; executing the spatial program picks the
right one. Same candidate boxes and the same segmenter — only the selector differs.*

Every component is off-the-shelf and frozen: **zero trained parameters.**

| | RRSIS-D test | RISBench test |
|---|---|---|
| mIoU | **58.86** | **55.27** |
| oIoU | **59.48** | **55.88** |

The same frozen configuration produces both rows; nothing is re-tuned per dataset.

![How it works](assets/pipeline.jpg)

*One scored candidate set carries through every stage: the frozen LLM synthesises the program,
`Select` detects, `Filter` re-weights by a continuous geometric field, `Argmin` takes the
extremum along an axis, and SAM turns the chosen box into a mask. Both figures are from the
paper.*

---

## Contents

- [Quick start: reproduce the numbers without a GPU](#quick-start-reproduce-the-numbers-without-a-gpu)
  - [What the dumps contain](#what-the-dumps-contain)
  - [Figures](#figures)
- [Installation](#installation)
  - [1. Main environment](#1-main-environment)
  - [2. Isolated detection environment](#2-isolated-detection-environment)
  - [3. Model weights](#3-model-weights)
  - [4. Datasets](#4-datasets)
  - [5. Check the detector bridge before a long run](#5-check-the-detector-bridge-before-a-long-run)
- [Running the full pipeline](#running-the-full-pipeline)
  - [What each selector is](#what-each-selector-is)
- [What is in here](#what-is-in-here)
  - [The prompt](#the-prompt)
  - [Integrity checks the paper cites](#integrity-checks-the-paper-cites)
  - [A note on determinism](#a-note-on-determinism)
- [Citation](#citation)
- [Acknowledgements](#acknowledgements)
- [License](#license)

---

## Quick start: reproduce the numbers without a GPU

The per-sample IoU dumps ship with this repository, so the headline numbers, the per-stratum
tables and the bootstrap intervals recompute from the released data alone — no weights, no
detection, no segmentation:

```bash
conda create -n geoselect python=3.10 -y
conda activate geoselect
pip install -r requirements.txt

python scripts/compute_ci.py          # headline mIoU + 95% CIs, per-stratum deltas

# the two reported runs -- these reproduce the headline table above
python scripts/make_tables.py experiments/runs/eval_rrsisd_test_oracle/summary.json \
                              experiments/eval_risbench_test/summary.json

# the second RRSIS-D run, which carries both selectors and so gives the V1-vs-V2 per-stratum delta
python scripts/make_tables.py experiments/eval_rrsisd_test/summary.json

python scripts/fig_failure_stats.py   # the one figure computed purely from the dumps
```

`compute_ci.py` checks its own aggregates against the published values before emitting intervals
(5,000 resamples, seed 0), so drift is reported rather than absorbed.

**Two RRSIS-D test runs ship.** The reported 58.86 / 59.48 come from
`runs/eval_rrsisd_test_oracle/`, which is what `compute_ci.py` asserts against. The second run,
`eval_rrsisd_test/`, scores both selectors and gives 58.77 / 59.60; it is the only dump the
V1-vs-V2 per-stratum comparison can be rebuilt from, since the oracle run scores the full program
alone. The 0.09 gap is the detector-build effect noted under
[A note on determinism](#a-note-on-determinism). RISBench is unaffected: both dumps give
55.27 / 55.88.

### What the dumps contain

| File | Rows | What it is |
|---|---|---|
| `experiments/runs/eval_rrsisd_test_oracle/samples.jsonl` | 3,481 | **RRSIS-D test, the reported run** (58.86 / 59.48), with the oracle-selector ceiling |
| `experiments/eval_rrsisd_test/samples.jsonl` | 3,481 | a second RRSIS-D test run, both selectors (58.77 / 59.60) — see the note above |
| `experiments/eval_risbench_test/samples.jsonl` | 16,159 | **RISBench test, the reported run** (55.27 / 55.88), both selectors |
| `experiments/runs/eval_risbench_test_oracle/samples.jsonl` | 16,159 | the RISBench oracle ceiling; its full-program numbers match the row above exactly |
| `experiments/runs/eval_rrsisd_val/samples.jsonl` | — | RRSIS-D val, all selector ablations |

Each row carries, per expression: the synthesised `program`, the detected class counts (`n_det`),
the chosen box and its IoU for both selectors (`v1_*` = continuous fields only, `v2_*` = the full
program executor), and `v2_mode` — `v2` when the program executed, `fallback` when the reliability
ladder caught it.

### Figures

`fig_failure_stats.py` attributes each failure to the first stage responsible — detection,
selection, or the program path — against the oracle ceiling.

---

[↑ Contents](#contents)

## Installation

The full pipeline needs **two conda environments**. The main one runs program synthesis, execution
and segmentation; the isolated one runs only the detector, reached through a subprocess rather than
an import. LAE-DINO's mmcv/mmdet stack pins torch 1.10 / py3.8 while the parser and SAM need
torch 2.5 / py3.10, and a separate process releases its VRAM between stages, which keeps the
pipeline on one 24 GB card. `detection.conda_env` names the isolated environment.

The versions below are the ones the reported results were produced with.

### 1. Main environment

```bash
conda create -n geoselect python=3.10 -y
conda activate geoselect

pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

Tested with: Python 3.10.20, torch 2.5.1+cu121, torchvision 0.20.1+cu121, transformers 5.9.0,
numpy 2.2.6, pycocotools 2.0.11.

### 2. Isolated detection environment

This one is fragile. `mmcv==2.2.0` has no prebuilt wheel for torch 1.10 / cu113, so it compiles
from source and needs `nvcc` available. Install LAE-DINO's **bundled mmdet fork** from
`mmdetection_lae/`, not pip's `mmdet`.

```bash
conda create -n laedino python=3.8 -y
conda activate laedino

pip install torch==1.10.0+cu113 torchvision==0.11.1+cu113 torchaudio==0.10.0+cu113 \
  -f https://download.pytorch.org/whl/cu113/torch_stable.html

git clone https://github.com/jaychempan/LAE-DINO.git ~/LAE-DINO
cd ~/LAE-DINO && git checkout 44726020759dd5e72fd05d5e5c1059619ead2284

pip install -U openmim
mim install mmengine==0.10.4
mim install "mmcv==2.2.0"

cd ~/LAE-DINO/mmdetection_lae
pip install -v -e .
pip install -r requirements/multimodal.txt
pip install emoji ddd-dataset "git+https://github.com/lvis-dataset/lvis-api.git"
```

Tested with: Python 3.8.20, torch 1.10.0+cu113, mmcv 2.2.0, mmengine 0.10.4, transformers 4.46.3,
numpy 1.24.4, and mmdet installed editable from LAE-DINO commit `4472602`.

LAE-DINO is Grounding-DINO style, so it needs **BERT**, and its configs reference it by the
relative path `../weights/bert-base-uncased` resolved against `mmdetection_lae/`. Either download
it there or symlink it:

```bash
mkdir -p ~/LAE-DINO/weights
ln -s "$GEOSELECT_WEIGHTS/bert-base-uncased" ~/LAE-DINO/weights/bert-base-uncased
```

### 3. Model weights

Set `GEOSELECT_WEIGHTS` to a directory holding these. None are redistributed here; all come from
their own sources.

| Under `$GEOSELECT_WEIGHTS` | Role | Size | Licence | Download |
|---|---|---|---|---|
| `Qwen3-4B/` | program synthesis, text-only | 7.6 GB | Apache-2.0 | [Qwen/Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B) |
| `LAE-DINO/checkpoints/lae_dino_swint_lae1m-28ca3a15.pth` | open-vocabulary detection (SAHI tiling) | 691 MB | MIT | [jaychempan/LAE-DINO](https://huggingface.co/jaychempan/LAE-DINO) |
| `bert-base-uncased/` | LAE-DINO's text encoder | 421 MB | Apache-2.0 | [google-bert/bert-base-uncased](https://huggingface.co/google-bert/bert-base-uncased) |
| `sam-vit-large/` | segmentation, HF format | 1.3 GB | Apache-2.0 | [facebook/sam-vit-large](https://huggingface.co/facebook/sam-vit-large) |

```bash
huggingface-cli download Qwen/Qwen3-4B            --local-dir "$GEOSELECT_WEIGHTS/Qwen3-4B"
huggingface-cli download facebook/sam-vit-large   --local-dir "$GEOSELECT_WEIGHTS/sam-vit-large"
huggingface-cli download jaychempan/LAE-DINO      --local-dir "$GEOSELECT_WEIGHTS/LAE-DINO"
huggingface-cli download google-bert/bert-base-uncased \
                                                  --local-dir "$GEOSELECT_WEIGHTS/bert-base-uncased"
```

The parser is the **text-only** Qwen3-4B: it never sees the image, which is why one 24 GB card
suffices. A VL checkpoint is rejected at load time. These four weights are all the reported
configuration needs.

#### Optional: swapping the decoder or the selector

The paper compares the frozen pipeline against other mask decoders and an implicit region↔text
selector. Both run from this repository with the rest of the pipeline unchanged; each needs one
more weight, and neither is needed for the reported results.

| Model | Paper | How it is selected |
|---|---|---|
| SAM 2.1 hiera-large (857 MB) | Ravi *et al.*, ICLR 2025 — the `.pt` checkpoint is published by [facebookresearch/sam2](https://github.com/facebookresearch/sam2) (`download_ckpts.sh`) | `--segmenter sam2.1`; `weights.sam2_ckpt` → `sam2/sam2.1_hiera_large.pt` |
| SAM 3 (3.3 GB) | [arXiv:2511.16719](https://arxiv.org/abs/2511.16719) — [facebook/sam3](https://huggingface.co/facebook/sam3); **gated**, Meta's terms must be accepted first | `--segmenter sam3`; `weights.sam3_path` → `sam3/` |
| GeoRSCLIP (RS5M ViT-H-14, 3.7 GB) | Zhang *et al.*, TGRS 2024 — [Zilun/GeoRSCLIP](https://huggingface.co/Zilun/GeoRSCLIP) | `--selectors clip`; `weights.georsclip` → `georsclip/RS5M_ViT-H-14.pt` |

These need `sam2` and `open_clip_torch`, listed in the optional block of `requirements.txt`.

### 4. Datasets

Neither dataset is redistributed here; both come from the authors who introduced them.

| Dataset | Introduced by | Get it from |
|---|---|---|
| RRSIS-D | Liu *et al.*, *Rotated Multi-Scale Interaction Network for Referring Remote Sensing Image Segmentation*, CVPR 2024, [arXiv:2312.12470](https://arxiv.org/abs/2312.12470) | [Lsan2401/RMSIN](https://github.com/Lsan2401/RMSIN) |
| RISBench | Dong *et al.*, *Cross-Modal Bidirectional Interaction Model for Referring Remote Sensing Image Segmentation*, [arXiv:2410.08613](https://arxiv.org/abs/2410.08613) | [HIT-SIRS/CroBIM](https://github.com/HIT-SIRS/CroBIM) |

Set `GEOSELECT_DATA` to a directory holding:

```
RSSIS-D/
  rrsisd/{refs(unc).p, instances.json}            REFER layout
  images/rrsisd/
RISBench_orig/
  img_rgb/  mask/  output_phrase_<split>.txt      original CrOBIM layout
```

RISBench is read in its **original CrOBIM layout**, not the HuggingFace repackage, so the
comparison is same-source.

### 5. Check the detector bridge before a long run

```bash
export GEOSELECT_DATA=/path/to/datasets
export GEOSELECT_WEIGHTS=/path/to/weights

conda run -n laedino python laedino_env/serve_detect.py --help
```

If the detector environment is broken, `serve_detect.py` reports the failure once per request
rather than crashing the parent, and every response comes back with an `error` field set and no
detections — so a silently empty result set means the bridge, not the method.

---

[↑ Contents](#contents)

## Running the full pipeline

```bash
conda activate geoselect

export GEOSELECT_DATA=/path/to/datasets
export GEOSELECT_WEIGHTS=/path/to/weights

python -m geoselect_v2.eval.run_eval --dataset rrsisd  --split test --selectors v1,v2
python -m geoselect_v2.eval.run_eval --dataset risbench --split test --selectors v1,v2
```

**Smoke-test before committing to a full split.** A dozen expressions exercise every stage —
synthesis, the subprocess bridge, segmentation, scoring — in about a minute:

```bash
python -m geoselect_v2.eval.run_eval --dataset rrsisd --split test --n 12 \
       --selectors v1,v2 --out-dir /tmp/smoke --cache-dir /tmp/smoke_cache
```

`--n` takes the first N expressions deterministically, so the rows it writes line up with the first
N of the shipped `experiments/eval_rrsisd_test/samples.jsonl` and can be compared field by field.
If the per-sample IoUs match, the whole stack is wired correctly.

The run is staged so the three models never co-reside in VRAM: load the parser → synthesise every
program → unload → detect (subprocess, its own environment) → load SAM → mask. Parse and detection
results are cached under `experiments/cache/`, keyed on the actual inputs — a prompt edit
invalidates the parse cache automatically, and a re-run after a crash resumes rather than
re-detecting. Expect detection to dominate: it is the only stage that scales with image count
rather than expression count.

### What each selector is

`--selectors` scores several selectors over one shared candidate pool, so any difference between
them is the selector alone:

- `v2` — the program executor (the headline)
- `v1` — continuous geometric fields only, no discrete operators
- `confidence` — highest detector score, no geometry
- `clip` — GeoRSCLIP region↔text cosine, no geometry
- `rule` — one hand-written image-frame heuristic, no program and no LLM
- `llmrank` — the same LLM picks a box directly, no program
- `sizeop` / `compsize` / `sizeall` — the size-operator ablation reported as a negative result

---

[↑ Contents](#contents)

## What is in here

```
geoselect_v2/            the method
  parser/                typed DSL: grammar, type checker, LLM program synthesis
  executor/              recursive interpreter over the scored candidate set
  kernels/               banded (relative position) + extremal (superlative) kernels
  reliability.py         the fallback ladder
  configs/v2_frozen.yaml every threshold and kernel parameter used for the reported results
  prompts/               the few-shot prompt, verbatim, plus its ablation variants
geogrounder/             detection / segmentation / dataset readers, reused frozen
laedino_env/             the isolated detection side, run under its own interpreter
scripts/                 recompute the paper's numbers from the shipped dumps
experiments/             per-sample IoU dumps + run summaries for the reported runs
```

### The prompt

`geoselect_v2/prompts/program_synthesis_fewshot.txt` is the frozen prompt behind every reported
number. The others are the ablation variants the paper discusses — `norules` (rules removed),
`noexamples` (examples removed), `4shot` (four of the fourteen examples), and
`*.sizeops_dropped` (the size-operator variant reported as a negative result). The prompt is
verified disjoint from the evaluation splits at the string level; `scripts/check_fewshot_leakage.py`
re-runs that check.

### Integrity checks the paper cites

```bash
python scripts/check_fewshot_leakage.py   # prompt examples vs evaluation splits, exact match
python scripts/eval_program_legality.py   # program legality / fallback rate (needs the LLM)
```

### A note on determinism

Synthesis is greedy (`do_sample=False`), the executor is pure geometry, and SAM is run with
`multimask_output=False`, so a re-run on the same inputs reproduces the same masks. The one thing
that can move numbers is a different detector build or a different SAHI tiling, since those change
the candidate set the program is executed over.

`compute_ci.py` fixes its own resampling seed, so it prints the same intervals on every run. A
bootstrap bound still depends on that seed: point estimates are exact, while an interval endpoint
can land a few hundredths from the one printed in the paper. None of the reported comparisons
changes sign or significance under that variation.

---

[↑ Contents](#contents)

## Citation

Accepted for publication in IEEE Transactions on Geoscience and Remote Sensing. Until the issue is
assigned, please cite the preprint:

```bibtex
@article{jiang2026geoselect,
  title   = {GeoSelect: Spatial-Program Execution for Training-Free Referring
             Remote Sensing Image Segmentation},
  author  = {Jiang, Yuhang and Deng, Guohui and Xu, Miaozhong and Ruan, Chao and
             Zhao, Jinling and Huang, Linsheng},
  journal = {arXiv preprint arXiv:2607.03869},
  year    = {2026}
}
```

This entry will be replaced with the journal reference once volume and pages exist.

[↑ Contents](#contents)

## Acknowledgements

GeoSelect trains nothing; it is built entirely on work released by others. Our thanks to the
authors of:

- **LAE-DINO** — the open-vocabulary detector, used frozen
  ([paper](https://arxiv.org/abs/2408.09110), [code](https://github.com/jaychempan/LAE-DINO)).
- **Segment Anything** — the mask decoder, used frozen with `multimask_output=False`.
- **Qwen3** — the text-only LLM that compiles expressions into programs, used frozen.
- **RRSIS-D** and **RISBench** — the two benchmarks, cited above.

[↑ Contents](#contents)

## License

MIT, see [LICENSE](LICENSE). The datasets and model checkpoints keep their own licences.

[↑ Contents](#contents)

# laedino_env/ — the isolated detection side

This directory runs in the **`laedino` conda env** (py3.8 / torch 1.10 / mmcv), NOT the main
environment. It is intentionally **outside** the `geogrounder` package.

**Rule: do not `import geogrounder` here.** The two environments have incompatible torch/mmcv
stacks and must stay decoupled — that is the whole reason detection is a subprocess rather than a
function call. Communication is JSON over that subprocess: `geogrounder/detection/protocol.py`
defines the shape on the main side, and `serve_detect.py` re-emits it by hand so neither side
imports the other.

`serve_detect.py` is launched by `geogrounder.detection.client.LaeDinoClient`:

```
conda run -n laedino python serve_detect.py --requests reqs.json --responses resps.json
```

The model is loaded **once per invocation** and reused for every request in the batch, so
evaluating a whole split costs one cold load rather than one per image.

## Pointing it at the model

`run_eval.py` does not forward these — set them in the shell that launches it, or pass
`--config` / `--weights` directly:

| Variable | Meaning |
|---|---|
| `LAEDINO_REPO` | where LAE-DINO was cloned (default `~/LAE-DINO`) |
| `LAEDINO_CONFIG` | the detector config `.py`; defaults to `$LAEDINO_REPO/mmdetection_lae/configs/lae_dino/lae_dino_swin-t_pretrain_LAE-1M.py` |
| `LAEDINO_WEIGHTS` | the checkpoint `.pth`; defaults to `$GEOSELECT_WEIGHTS/LAE-DINO/checkpoints/lae_dino_swint_lae1m-28ca3a15.pth` |
| `LAEDINO_META_ANN` | any valid COCO json, used for class metainfo only (see `build_inferencer`) |

See the repository-root `README.md` for building this environment (and the main one).

## Two things that look odd and are deliberate

**The CocoDataset swap.** The LAE-1M checkpoint stores no `dataset_meta`, so `DetInferencer`
builds `cfg.test_dataloader.dataset` purely to read class names — and that points at LAE-FOD
jsons that are not part of this project. In grounding mode the classes come from `texts`, so the
metainfo is irrelevant; `build_inferencer` swaps in a minimal `CocoDataset` over any valid COCO
file to get past the builder.

**The `chdir`.** LAE-DINO's configs reference BERT by the relative path
`../weights/bert-base-uncased`, resolved against the `mmdetection_lae` directory. `main()` makes
the config and weight paths absolute and then changes into that directory so the relative
reference resolves.

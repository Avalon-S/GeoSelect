"""GeoRSCLIP region-similarity selector — the best-effort implicit-matching baseline.

Purpose (ablation): the implicit-matching rung of the selector comparison. It ranks the SAME LAE-DINO candidates the
geometry path sees, but by **GeoRSCLIP region<->text cosine similarity** (zero geometry) — i.e. the
prior-art training-free paradigm (EKP-HRM/DGL-RSIS select by a remote-sensing CLIP) at its strongest,
on OUR (stronger) candidates. So (the geometry selector) - (this) isolates the explicit-geometry contribution
over the implicit-matching paradigm, controlling for the component upgrade.

Deliberately NOT Alpha-CLIP: Alpha-CLIP is a natural-image model and we already found it net-negative
on RS (that negative result lives in the rerank ablation). Using it here would inflate the gap with
"bad implementation" rather than "paradigm gap". GeoRSCLIP (trained on RS5M) is the domain-matched,
best-effort representative of the implicit-matching paradigm.

Model: GeoRSCLIP (om-ai-lab/RS5M, HF `Zilun/GeoRSCLIP`). Default = ViT-H-14 (flagship; strongest
baseline). Loaded via open_clip: build the laion2b base, then load_state_dict(GeoRSCLIP, strict=False)
— the RS5M-released recipe. Runs in the MAIN env (open_clip_torch), like Alpha-CLIP did.

Region representation: crop the candidate's bbox and score crop<->sentence cosine (standard CLIP region
scoring; selection happens on BOXES, before SAM2, exactly parallel to the geometry path).
"""

import numpy as np
from PIL import Image

# open_clip model name + its laion/openai base, per GeoRSCLIP variant (RS5M README).
_BASES = {
    'ViT-H-14': 'laion2b_s32b_b79k',
    'ViT-B-32': 'openai',
}


class GeoRSClipSelector:
    def __init__(self, ckpt, model_name='ViT-H-14', device='cuda'):
        self.ckpt = ckpt
        self.model_name = model_name      # open_clip name: 'ViT-H-14' / 'ViT-B-32' (hyphens, NOT 'ViT-H/14')
        self.device = device
        self.model = None
        self.preprocess = None
        self.tokenizer = None

    def load(self):
        import torch
        import open_clip
        # GeoRSCLIP ckpt is a FULL state dict (RS5M_ViT-H-14.pt = 3.94GB = full ViT-H-14 fp32), so build
        # the BARE architecture (pretrained=None — NO ~3.9GB laion2b base download) and overlay it.
        # preprocess mean/std come from the model config (= OpenAI/laion CLIP norm), correct for GeoRSCLIP.
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(self.model_name, pretrained=None)
        sd = torch.load(self.ckpt, map_location='cpu')
        sd = sd.get('state_dict', sd) if isinstance(sd, dict) else sd
        missing, unexpected = self.model.load_state_dict(sd, strict=False)
        if len(missing) > 20:   # full ckpt -> ~0 missing; a flood means it's NOT full -> set pretrained=_BASES[...]
            print(f'  [GeoRSCLIP] WARN {len(missing)} missing keys with pretrained=None — ckpt may not be '
                  f'full; if so rebuild with pretrained={_BASES.get(self.model_name)!r}. first: {list(missing)[:3]}')
        self.tokenizer = open_clip.get_tokenizer(self.model_name)
        self.model = self.model.to(self.device).float().eval()
        return self

    def _to_pil(self, image):
        if isinstance(image, Image.Image):
            return image.convert('RGB')
        return Image.fromarray(np.asarray(image)).convert('RGB')  # RRSISDDataset image -> PIL

    def score(self, image, boxes, text):
        """Cosine(GeoRSCLIP(crop_i), GeoRSCLIP(text)) for each xyxy box. -> np.float array (len=boxes)."""
        import torch
        if not boxes:
            return np.zeros((0,), dtype=np.float32)
        pil = self._to_pil(image)
        W, H = pil.size
        crops = []
        for b in boxes:
            x1, y1, x2, y2 = (int(round(v)) for v in b)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(W, max(x1 + 1, x2)), min(H, max(y1 + 1, y2))
            crops.append(self.preprocess(pil.crop((x1, y1, x2, y2))))
        with torch.no_grad():
            imgs = torch.stack(crops).to(self.device)
            tok = self.tokenizer([text]).to(self.device)
            imf = self.model.encode_image(imgs)
            txf = self.model.encode_text(tok)
            imf = imf / imf.norm(dim=-1, keepdim=True)
            txf = txf / txf.norm(dim=-1, keepdim=True)
            sims = (imf @ txf.T).squeeze(-1)        # (n_boxes,)
        return sims.float().cpu().numpy()

    def unload(self):
        import gc
        self.model = self.preprocess = self.tokenizer = None
        gc.collect()
        try:
            import torch
            torch.cuda.empty_cache()
        except Exception:
            pass

"""Stage [1]: Qwen3-VL structured parsing of a referring expression.

Output is the relation schema consumed by reasoning/compose.py:
    {"target": str, "logic": "and"|"or",
     "relations": [{"predicate": <dir|near|size>, "anchor": str | <nested relation>}]}
where <size> is a comparative-size predicate (larger|smaller|similar) scored by box area.

Implemented for transformers v5 + Qwen3-VL (`dtype=`, not `torch_dtype=`). Greedy decoding
(do_sample=False) for reproducible structured output. The image is optional: pass it for
multimodal grounding (pipeline default) or omit for faster text-only parsing.
"""

import json
import re

from geogrounder.reasoning.predicates import normalize_predicate, normalize_size_predicate

PROMPT_TEMPLATE = (
    "Parse the referring expression about an object in a remote-sensing image into a STRICT "
    "JSON object (no markdown, no commentary) with this schema:\n"
    '{{"target": "<object class>", "cardinality": "single" or "group", "logic": "and" or "or", '
    '"relations": [{{"predicate": "<rel>", "anchor": "image" or "<object class>" '
    'or <nested object>}}]}}\n'
    "RULES:\n"
    "- predicate is one of: north, south, east, west, left, right, above, below, "
    "upper left, upper right, lower left, lower right, center, near.\n"
    "- anchor is \"image\" when the position is relative to the whole image "
    "(e.g. 'on the right', 'in the middle', 'lower left' = right/middle/lower-left of the IMAGE). "
    "Only use an object-class anchor when the expression explicitly refers to ANOTHER object "
    "(e.g. 'left OF the stadium').\n"
    "- cardinality is \"group\" ONLY when the expression refers to MULTIPLE objects of the class "
    "(plural head noun, 'all', 'every', 'the row/line of ...'); otherwise \"single\" — this is the "
    "DEFAULT, because most expressions name exactly ONE object (e.g. 'the ship on the right', "
    "'a large windmill' are single).\n"
    "- Ignore attributes (size/colour/shape: 'large', 'long', 'gray', ...) and "
    "possession ('has', 'with') — these are NOT relations.\n"
    "- If the expression has no positional cue (pure attribute), use an empty relations list.\n"
    # Few-shot examples are HANDCRAFTED and verified DISJOINT from RRSIS-D val/test
    # (checked by exact match against both splits) — no eval-set leakage.
    "EXAMPLES:\n"
    "'a dam on the right' -> "
    '{{"target": "dam", "cardinality": "single", "logic": "and", '
    '"relations": [{{"predicate": "right", "anchor": "image"}}]}}\n'
    "'a harbor in the middle' -> "
    '{{"target": "harbor", "cardinality": "single", "logic": "and", '
    '"relations": [{{"predicate": "center", "anchor": "image"}}]}}\n'
    "'an airport on the upper left' -> "
    '{{"target": "airport", "cardinality": "single", "logic": "and", '
    '"relations": [{{"predicate": "upper left", "anchor": "image"}}]}}\n'
    "'the ship below the bridge' -> "
    '{{"target": "ship", "cardinality": "single", "logic": "and", '
    '"relations": [{{"predicate": "below", "anchor": "bridge"}}]}}\n'
    "'the orange harbor' -> "
    '{{"target": "harbor", "cardinality": "single", "logic": "and", "relations": []}}\n'
    "'the storage tanks on the left' -> "
    '{{"target": "storage tank", "cardinality": "group", "logic": "and", '
    '"relations": [{{"predicate": "left", "anchor": "image"}}]}}\n'
    'Now parse: "{sentence}"\n'
    "JSON:"
)


# Attribute-keeping variant (ablation): the target/anchor noun phrase RETAINS
# size/colour/shape attributes so the open-vocab detector (LAE-DINO) is queried with the full
# phrase ('tiny ship', 'green and yellow oval ground track field') instead of the bare class.
# Tests whether attribute-conditioned detection helps (esp. multi-instance anchor disambiguation)
# or hurts recall (over-specification). Selected when QwenParser(keep_attributes=True). Positional
# cues stay PREDICATES, articles/possession still dropped — only intrinsic attributes are kept.
# Flat-only: NO nested-anchor and NO comparative-size additions, which caused parse drift
# (over-nesting a trailing 'in the middle' into the anchor; same-class anchor hallucination).
# Used for every sentence that is NOT a size comparison, so the headline path stays
# bit-identical to the frozen run.
PROMPT_TEMPLATE_ATTR = (
    "Parse the referring expression about an object in a remote-sensing image into a STRICT "
    "JSON object (no markdown, no commentary) with this schema:\n"
    '{{"target": "<object noun phrase>", "cardinality": "single" or "group", "logic": "and" or "or", '
    '"relations": [{{"predicate": "<rel>", "anchor": "image" or "<object noun phrase>"}}]}}\n'
    "RULES:\n"
    "- predicate is one of: north, south, east, west, left, right, above, below, "
    "upper left, upper right, lower left, lower right, center, near.\n"
    "- anchor is \"image\" when the position is relative to the whole image "
    "(e.g. 'on the right', 'in the middle', 'lower left' = right/middle/lower-left of the IMAGE). "
    "Only use an object-noun-phrase anchor when the expression explicitly refers to ANOTHER object "
    "(e.g. 'left OF the large stadium').\n"
    "- cardinality is \"group\" ONLY when the expression refers to MULTIPLE objects of the class "
    "(plural head noun, 'all', 'every', 'the row/line of ...'); otherwise \"single\" — the DEFAULT.\n"
    "- KEEP size/colour/shape attributes (e.g. 'large', 'long', 'gray', 'oval', 'green and yellow') "
    "as part of the target AND anchor noun phrase. Do NOT keep articles (a/an/the), positional words "
    "(on the right, in the middle, left of — these are PREDICATES), or possession (has, with).\n"
    "- If the expression has no positional cue (pure attribute), use an empty relations list.\n"
    # Few-shot examples are HANDCRAFTED and verified DISJOINT from RRSIS-D val/test.
    "EXAMPLES:\n"
    "'a small golf field on the left' -> "
    '{{"target": "small golf field", "cardinality": "single", "logic": "and", '
    '"relations": [{{"predicate": "left", "anchor": "image"}}]}}\n'
    "'a gray harbor in the middle' -> "
    '{{"target": "gray harbor", "cardinality": "single", "logic": "and", '
    '"relations": [{{"predicate": "center", "anchor": "image"}}]}}\n'
    "'an orange storage tank on the lower right' -> "
    '{{"target": "orange storage tank", "cardinality": "single", "logic": "and", '
    '"relations": [{{"predicate": "lower right", "anchor": "image"}}]}}\n'
    "'the vehicle to the right of the blue harbor' -> "
    '{{"target": "vehicle", "cardinality": "single", "logic": "and", '
    '"relations": [{{"predicate": "right", "anchor": "blue harbor"}}]}}\n'
    "'the gray slender bridge' -> "
    '{{"target": "gray slender bridge", "cardinality": "single", "logic": "and", "relations": []}}\n'
    "'the windmills in the middle' -> "
    '{{"target": "windmill", "cardinality": "group", "logic": "and", '
    '"relations": [{{"predicate": "center", "anchor": "image"}}]}}\n'
    'Now parse: "{sentence}"\n'
    "JSON:"
)

# Nested-anchor + comparative-size rule/examples, INJECTED into the frozen template only for the
# size-aware variant. Verified DISJOINT from RRSIS-D + RISBench val/test. The size
# examples need nested anchors ('larger than the vehicle ON THE LEFT'), so nesting rides along here.
_SIZE_NEST_VOCAB = (
    "upper left, upper right, lower left, lower right, center, near, larger, smaller, similar.\n"
    "- COMPARATIVE SIZE: when the expression picks the target by its SIZE relative to ANOTHER "
    "object ('bigger/larger than', 'smaller than', 'similar in size to', 'same size as'), use the "
    "predicate \"larger\", \"smaller\", or \"similar\" with that other object as the anchor. Drop "
    "hedges ('a little', 'much', 'slightly'). If that anchor object carries its own position, NEST "
    "it (as below). Keep size/shape/colour adjectives inside the noun phrases, not as the predicate.\n"
    "- When an anchor object ITSELF carries a positional qualifier (e.g. 'the harbor ON THE LEFT', "
    "'the ship AT THE TOP'), express the anchor as a NESTED object with its OWN relations — never "
    "drop the qualifier. Keep colour/size/shape in the nested noun phrase, turn its POSITION into a "
    "nested relation whose anchor is \"image\".\n"
)
_SIZE_NEST_EXAMPLES = (
    "'a windmill to the left of the storage tank in the lower right' -> "
    '{{"target": "windmill", "cardinality": "single", "logic": "and", "relations": '
    '[{{"predicate": "left", "anchor": {{"target": "storage tank", "cardinality": "single", '
    '"logic": "and", "relations": [{{"predicate": "lower right", "anchor": "image"}}]}}}}]}}\n'
    "'a vehicle much smaller than the airplane' -> "
    '{{"target": "vehicle", "cardinality": "single", "logic": "and", '
    '"relations": [{{"predicate": "smaller", "anchor": "airplane"}}]}}\n'
    "'the storage tank larger than the storage tank in the center' -> "
    '{{"target": "storage tank", "cardinality": "single", "logic": "and", "relations": '
    '[{{"predicate": "larger", "anchor": {{"target": "storage tank", "cardinality": "single", '
    '"logic": "and", "relations": [{{"predicate": "center", "anchor": "image"}}]}}}}]}}\n'
    "'a harbor similar in size to the golf field on the left' -> "
    '{{"target": "harbor", "cardinality": "single", "logic": "and", "relations": '
    '[{{"predicate": "similar", "anchor": {{"target": "golf field", "cardinality": "single", '
    '"logic": "and", "relations": [{{"predicate": "left", "anchor": "image"}}]}}}}]}}\n'
)
# Built by injection so the frozen template stays the single source of truth for the common part.
PROMPT_TEMPLATE_ATTR_SIZE = (
    PROMPT_TEMPLATE_ATTR
    .replace("upper left, upper right, lower left, lower right, center, near.\n", _SIZE_NEST_VOCAB)
    .replace('Now parse: "{sentence}"\n', _SIZE_NEST_EXAMPLES + 'Now parse: "{sentence}"\n')
)

# Comparative-size GATE: route a sentence to PROMPT_TEMPLATE_ATTR_SIZE only if it is an explicit
# size comparison, so every non-comparative sentence keeps the frozen prompt.
# Requires a comparative STRUCTURE ('...-er than', 'similar to/in size', 'same size'), not a bare
# 'size'/'similar', to stay precise.
COMPARATIVE_RE = re.compile(
    r'\b(?:bigger|larger|smaller|tinier|wider|narrower|longer|shorter|taller)\b[^.]*\bthan\b'
    r'|\bsimilar\b[^.]*\b(?:to|in size)\b|\bsame size\b|\bcomparable\b', re.IGNORECASE)


def extract_json(text):
    """Pull the first balanced JSON object out of model text (tolerates ``` fences)."""
    start = text.find('{')
    if start == -1:
        raise ValueError(f'no JSON object in model output: {text!r}')
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError(f'unbalanced JSON in model output: {text!r}')


def _predicate_ok(pred):
    """True if `pred` is a predicate our geometry can model: a directional/center/near predicate
    (normalize_predicate) OR a comparative-size predicate (normalize_size_predicate)."""
    if normalize_size_predicate(pred) is not None:
        return True
    try:
        normalize_predicate(pred)
        return True
    except ValueError:
        return False


def validate_relation(rel):
    """Raise if `rel` does not match the relation schema (recursive on nested anchors)."""
    if not isinstance(rel, dict) or 'target' not in rel:
        raise ValueError(f'relation needs a "target": {rel!r}')
    rel.setdefault('logic', 'and')
    if rel['logic'] not in ('and', 'or'):
        raise ValueError(f'logic must be and/or: {rel!r}')
    for r in rel.get('relations', []):
        if not _predicate_ok(r.get('predicate', '')):   # directional/center/near OR size
            raise ValueError(f'bad predicate {r.get("predicate")!r} in {r!r}')
        if isinstance(r.get('anchor'), dict):
            validate_relation(r['anchor'])
    return rel


def sanitize_relation(rel):
    """Lenient counterpart of validate_relation: keep `target` + only the relations whose
    predicate our geometry can model (recursively); drop the rest (attributes like 'large',
    possession like 'has', malformed entries). Returns (clean_relation, dropped_list).

    Rationale: a target with an unmodelable/absent relation just falls back to
    detection + attribute selection (correct for the 30%+ pure-attribute expressions), so one
    bad relation should NOT discard the whole parse. Raises only if there is no usable target.
    """
    if not isinstance(rel, dict) or not rel.get('target'):
        raise ValueError(f'relation needs a non-empty "target": {rel!r}')
    logic = rel.get('logic', 'and')
    if logic not in ('and', 'or'):
        logic = 'and'

    clean, dropped = [], []
    for r in rel.get('relations', []):
        if not isinstance(r, dict) or 'predicate' not in r or 'anchor' not in r:
            dropped.append(r)
            continue
        if not _predicate_ok(r['predicate']):   # keep directional/center/near AND size predicates
            dropped.append(r)
            continue
        if isinstance(r.get('anchor'), dict):
            try:
                sub_clean, sub_dropped = sanitize_relation(r['anchor'])
                r = {**r, 'anchor': sub_clean}
                dropped.extend(sub_dropped)
            except ValueError:
                dropped.append(r)
                continue
        clean.append(r)
    card = rel.get('cardinality', 'single')
    if card not in ('single', 'group'):
        card = 'single'                      # conservative default -> single -> top1 (no over-union)
    return {'target': rel['target'], 'cardinality': card, 'logic': logic, 'relations': clean}, dropped


# --- Attributed-mode query stabiliser -----------------------------------------------------------
# With keep_attributes=True the parser emits attributed noun phrases for target+anchor. The LLM
# occasionally FLATTENS a positioned ANCHOR ("the windmill on the left") instead of nesting it.
# This DETERMINISTIC filter
# guarantees clean, canonical detection-query strings independent of LLM phrasing drift: lowercase,
# strip a leading article, strip any leaked image-frame positional / comparative tail; keep the
# attribute adjectives + head noun. No-op on already-clean phrases ('tiny ship', 'green and yellow
# oval ground track field'). Applied ONLY in attributed mode — the frozen bare-class path is untouched.
_ARTICLE_RE = re.compile(r'^(?:a|an|the)\s+', re.IGNORECASE)
_POS_TAIL_RE = re.compile(
    r'\s+(?:on|in|at|to|of)\s+the\s+(?:left|right|top|bottom|middle|center|centre|corner'
    r'|upper(?:\s+\w+)?|lower(?:\s+\w+)?).*$', re.IGNORECASE)
# spatial prepositions REQUIRE a trailing space (so "over"/"under" don't eat "overpass"/"underpass");
# comparatives are \b-anchored. Order: longer alternatives first.
_REL_TAIL_RE = re.compile(
    r'\s+(?:(?:above|below|underneath|under|over|behind|beside)\s+'
    r'|next\s+to\s+|adjacent\s+to\s+'
    r'|(?:much\s+|a\s+little\s+)?(?:bigger|smaller|larger)\b'
    r'|similar\b).*$', re.IGNORECASE)


def clean_query_phrase(phrase):
    """Stabilise an attributed target/anchor noun phrase into a clean canonical detection query."""
    if not phrase:
        return phrase
    s = _ARTICLE_RE.sub('', phrase.strip().lower())
    s = _POS_TAIL_RE.sub('', s)
    s = _REL_TAIL_RE.sub('', s)
    return re.sub(r'\s+', ' ', s).strip()


def clean_relation_phrases(rel):
    """Recursively clean target + string anchors with clean_query_phrase (in place). Attributed mode."""
    if not isinstance(rel, dict):
        return rel
    if rel.get('target'):
        rel['target'] = clean_query_phrase(rel['target'])
    for r in rel.get('relations', []):
        a = r.get('anchor')
        if isinstance(a, str):
            r['anchor'] = clean_query_phrase(a)
        elif isinstance(a, dict):
            clean_relation_phrases(a)
    return rel


class QwenParser:
    """Wraps a causal LLM for our structured parsing + (optional) direct bbox grounding.
    Auto-detects multimodal-VL vs text-only from config.architectures at load() time:

      * Qwen3-VL family (Qwen3VLForConditionalGeneration): the VLM-only baseline
        (predict_bbox path). Accepts (text, image) via qwen_vl_utils.
      * ANY text-only causal LLM (AutoModelForCausalLM): the parser the method uses.
        Default Qwen3-4B; the cross-architecture parser-robustness study also runs
        Llama-3.2-3B (dense full-attention) and Falcon-Mamba-7B (attention-free SSM)
        through the SAME path — parse is a text task, so any instruction-following LLM is
        a drop-in. The image arg to parse() is silently ignored for text-only models.

    Switching parsers = pointing --qwen-path to a different (non-VL)
    checkpoint dir; no other config change. (Class name kept 'QwenParser' for stability.)
    """
    def __init__(self, model_path, device='cuda', dtype='bfloat16',
                 image_patch_size=16, max_new_tokens=256, keep_attributes=False):
        self.model_path = model_path
        self.device = device
        self.dtype = dtype
        self.image_patch_size = image_patch_size  # Qwen3-VL uses 16 (NOT 14)
        self.max_new_tokens = max_new_tokens
        # keep_attributes (ablation): emit attributed target/anchor noun phrases so LAE-DINO is
        # queried with the full phrase. Default False = frozen behaviour (bare class names).
        self.keep_attributes = keep_attributes
        self.model = None
        self.processor = None
        self.is_vl = None  # set by load(); True for Qwen3-VL, False for text-only Qwen3

    def load(self):
        import torch
        from transformers import AutoConfig
        torch_dtype = getattr(torch, self.dtype) if isinstance(self.dtype, str) else self.dtype

        # Detect model type by inspecting config.architectures (cheap, no weights loaded yet).
        # trust_remote_code: some architectures ship custom modeling code (e.g. DeepSeek's
        # modeling_deepseek.py); harmless for HF-native models (Qwen3/Llama/Falcon-Mamba).
        cfg = AutoConfig.from_pretrained(self.model_path, trust_remote_code=True)
        arch = (cfg.architectures or [''])[0] if hasattr(cfg, 'architectures') else ''
        is_vl = ('VL' in arch) or ('Vision' in arch)
        self.is_vl = is_vl

        if is_vl:
            # Multimodal path — Qwen3-VL family (used by the VLM-only baseline).
            from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
            self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                self.model_path, dtype=torch_dtype, device_map=self.device)  # v5: dtype
            self.processor = AutoProcessor.from_pretrained(self.model_path)
        else:
            # Text-only path — ANY causal LLM parser: Qwen3 (default), Llama-3.2, Falcon-Mamba
            # (attention-free SSM), etc. ONE generic AutoModelForCausalLM + AutoTokenizer path
            # serves them all (cross-architecture parser-robustness study).
            from transformers import AutoModelForCausalLM, AutoTokenizer
            # trust_remote_code=False ON PURPOSE: every parser model in our matrix (Qwen3,
            # Llama-3.2, Falcon-Mamba, Phi-4-mini) has a NATIVE transformers implementation, so a
            # model's bundled custom code is never needed. Phi-4-mini specifically ships a
            # modeling_phi3.py (the trust_remote_code path) written against an OLDER transformers
            # that does `from transformers.utils import LossKwargs` — that symbol is gone in our
            # transformers v5, so the remote path crashes on load (ImportError: LossKwargs).
            # Forcing False routes Phi-4-mini through native Phi3ForCausalLM. For Qwen3/Llama/
            # Falcon this is a no-op (they have no auto_map remote code). Do NOT flip back to True
            # unless a model is added that genuinely lacks a native implementation.
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path, dtype=torch_dtype, device_map=self.device, trust_remote_code=False)
            self.processor = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=False)
            # Some tokenizers (e.g. Llama) ship without a pad token -> set to eos so generate()
            # does not warn/misbehave. Greedy single-sample decoding is otherwise unaffected.
            if self.processor.pad_token_id is None and self.processor.eos_token is not None:
                self.processor.pad_token = self.processor.eos_token

        self.model.eval()
        return self

    def unload(self):
        self.model = None
        self.processor = None
        self.is_vl = None
        # caller should free VRAM: geogrounder.utils.vram.empty_cache()

    def _generate(self, sentence, image):
        if not self.keep_attributes:
            tmpl = PROMPT_TEMPLATE
        elif COMPARATIVE_RE.search(sentence):
            # Size-comparison sentence -> size+nested prompt. Everything else stays on the frozen
            # flat prompt, so non-comparative parses are bit-identical to the frozen headline.
            tmpl = PROMPT_TEMPLATE_ATTR_SIZE
        else:
            tmpl = PROMPT_TEMPLATE_ATTR
        return self.generate(tmpl.format(sentence=sentence), image)

    def generate(self, prompt, image=None):
        """Raw text generation from (prompt, optional image). Branches on self.is_vl:
        VL path (Qwen3-VL) accepts image via qwen_vl_utils; text-only path (Qwen3)
        silently ignores any passed image. Greedy, reproducible.

        Thinking mode (Qwen3 family) is DISABLED for structured JSON output —
        otherwise the model would emit <think>...</think> preamble before the JSON
        and pollute downstream extract_json(). See apply_chat_template call below.
        """
        import torch

        if self.is_vl:
            # --- Qwen3-VL path (multimodal) ---
            from qwen_vl_utils import process_vision_info

            content = []
            if image is not None:
                content.append({'type': 'image', 'image': image})
            content.append({'type': 'text', 'text': prompt})
            messages = [{'role': 'user', 'content': content}]

            try:
                # align with the text-only path: suppress <think> preamble for structured JSON
                text = self.processor.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
            except TypeError:
                text = self.processor.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True)
            if image is not None:
                try:
                    image_inputs, video_inputs = process_vision_info(
                        messages, image_patch_size=self.image_patch_size)
                except TypeError:
                    image_inputs, video_inputs = process_vision_info(messages)
            else:
                image_inputs, video_inputs = None, None

            inputs = self.processor(text=[text], images=image_inputs, videos=video_inputs,
                                    padding=True, return_tensors='pt').to(self.model.device)
            with torch.no_grad():
                gen = self.model.generate(**inputs, max_new_tokens=self.max_new_tokens,
                                          do_sample=False)
            trimmed = [out[len(inp):] for inp, out in zip(inputs.input_ids, gen)]
            return self.processor.batch_decode(
                trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
        else:
            # --- Qwen3 text-only path ---
            # image (if passed) is silently ignored — text-only model has no vision encoder.
            messages = [{'role': 'user', 'content': prompt}]
            # enable_thinking=False suppresses <think>...</think> chain-of-thought preamble
            # so the JSON we want is the first thing emitted. Critical for structured output.
            try:
                text = self.processor.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True,
                    enable_thinking=False)
            except TypeError:
                # Older tokenizer versions without enable_thinking support — fall back.
                text = self.processor.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True)
            inputs = self.processor(text, return_tensors='pt').to(self.model.device)
            with torch.no_grad():
                # Pass pad_token_id explicitly to silence the per-call transformers
                # "Setting pad_token_id to eos_token_id" warning that floods stdout for
                # models whose generate() can't infer it (e.g. Llama).
                gen = self.model.generate(**inputs, max_new_tokens=self.max_new_tokens,
                                          do_sample=False, pad_token_id=self.processor.pad_token_id)
            trimmed = gen[:, inputs.input_ids.shape[1]:]   # strip the prompt tokens
            return self.processor.batch_decode(
                trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

    def parse(self, sentence, image=None):
        """sentence: str, image: PIL.Image|None -> clean relation dict (lenient).

        Drops relations our geometry can't model; keeps target + valid spatial relations.
        """
        if self.model is None:
            raise RuntimeError('call load() first')
        clean, _dropped = sanitize_relation(extract_json(self._generate(sentence, image)))
        if self.keep_attributes:
            clean_relation_phrases(clean)   # strip leaked positional/comparative tails (anchor stabiliser)
        return clean

    def parse_raw(self, sentence, image=None):
        """Never raises. -> (relation|None, raw_text, dropped_list, error|None)."""
        if self.model is None:
            raise RuntimeError('call load() first')
        raw = self._generate(sentence, image)
        try:
            obj = extract_json(raw)
        except Exception as e:
            return None, raw, [], f'{type(e).__name__}: {e}'
        try:
            clean, dropped = sanitize_relation(obj)
            if self.keep_attributes:
                clean_relation_phrases(clean)
            return clean, raw, dropped, None
        except Exception as e:
            return None, raw, [], f'{type(e).__name__}: {e}'

    def predict_bbox(self, sentence, image, image_size=None, return_raw=False,
                     coord_scale=1000):
        """Direct VLM grounding: prompt the VLM to return a bounding box of the referent.

        Used by run_eval.py --mode vlm-only as a baseline (no LAE-DINO, no explicit
        geometry). The point is to measure what an explicit-geometry-free pipeline
        achieves with the SAME VLM + SAME SAM2.1 the full method uses, so the contribution
        of the explicit-geometry framework can be isolated from VLM/segmenter quality.

        Args:
            sentence: referring expression text
            image: PIL.Image (REQUIRED, since this is image-grounded prediction)
            image_size: optional (W, H) for clamping; defaults to image.size
            return_raw: if True, return (bbox, raw_text) for debugging coord-space mismatches.
            coord_scale: assumed VLM output coord range (default 1000; Qwen3-VL conv).
                See parse_bbox_from_text() for the empirical confirmation. The prompt asks
                for [0, coord_scale) explicitly so the convention is in-distribution.

        Returns:
            [x1, y1, x2, y2] in absolute pixel coordinates, or None on parse failure
            (no bbox extractable from VLM output, or degenerate box).
            If return_raw=True: tuple (bbox, raw_text).
        """
        if self.model is None:
            raise RuntimeError('call load() first')
        if not self.is_vl:
            raise RuntimeError(
                'predict_bbox() requires a Qwen3-VL model (visual grounding). '
                'Loaded model is text-only Qwen3 — switch to Qwen3-VL for VLM-only baseline.')
        W, H = image_size if image_size else image.size
        prompt = (
            f"Find the SINGLE OBJECT referred to by:\n"
            f'  "{sentence}"\n\n'
            "Return ONLY a JSON object in this exact format (no other text, no markdown):\n"
            '{"bbox": [x1, y1, x2, y2]}\n'
            f"where x1, y1, x2, y2 are NORMALIZED coordinates in [0, {coord_scale}) x [0, {coord_scale}) "
            "with x1 < x2 and y1 < y2."
        )
        raw = self.generate(prompt, image=image)
        bbox = parse_bbox_from_text(raw, image_size=(W, H), coord_scale=coord_scale)
        if return_raw:
            return bbox, raw
        return bbox


def parse_bbox_from_text(text, image_size=(800, 800), coord_scale=1000):
    """Robust bbox extraction from VLM output text. Returns [x1,y1,x2,y2] or None.

    Tries multiple formats in order of preference:
      1. JSON {"bbox": [x1, y1, x2, y2]}                (preferred, our prompt)
      2. Bracketed list [x1, y1, x2, y2]                (common fallback)
      3. Tuple-pairs ((x1, y1), (x2, y2))               (occasionally seen)
      4. Qwen-style <|box_start|>x1,y1,x2,y2<|box_end|> (Qwen-VL-specific token)
    All formats are clamped to image bounds and degenerate boxes (x2<=x1 or y2<=y1)
    are rejected.

    coord_scale: assumed range of model coordinates BEFORE rescaling to image pixels.
        Qwen3-VL models with a JSON prompt emit 0-1000 normalized coordinates regardless of
        an instruction to use 0-W pixels, following their training convention. Without the
        rescale a large fraction of boxes clamp at the image boundary or become degenerate,
        and accuracy collapses; coord_scale=1000 restores them.
        Set to None or 0 to skip rescaling (treat raw output as absolute pixels).
    """
    import re
    W, H = image_size
    sx = float(W) / coord_scale if coord_scale else 1.0
    sy = float(H) / coord_scale if coord_scale else 1.0

    def _clamp(bbox):
        x1, y1, x2, y2 = (float(v) for v in bbox)
        x1, y1, x2, y2 = x1 * sx, y1 * sy, x2 * sx, y2 * sy
        x1, x2 = max(0.0, min(float(W), min(x1, x2))), max(0.0, min(float(W), max(x1, x2)))
        y1, y2 = max(0.0, min(float(H), min(y1, y2))), max(0.0, min(float(H), max(y1, y2)))
        if x2 - x1 < 1 or y2 - y1 < 1:
            return None
        return [x1, y1, x2, y2]

    # 1. JSON {"bbox": [...]}
    try:
        obj = extract_json(text)
        b = obj.get('bbox') if isinstance(obj, dict) else None
        if isinstance(b, (list, tuple)) and len(b) == 4:
            c = _clamp(b)
            if c:
                return c
    except Exception:
        pass

    # 2. Bracketed [x1, y1, x2, y2]
    m = re.search(
        r'\[\s*(-?\d+(?:\.\d+)?)\s*[,\s]\s*(-?\d+(?:\.\d+)?)\s*[,\s]\s*'
        r'(-?\d+(?:\.\d+)?)\s*[,\s]\s*(-?\d+(?:\.\d+)?)\s*\]',
        text,
    )
    if m:
        c = _clamp([m.group(i) for i in range(1, 5)])
        if c:
            return c

    # 3. Tuple pairs ((x1, y1), (x2, y2))
    m = re.search(
        r'\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)'
        r'\s*[,\s]\s*'
        r'\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)',
        text,
    )
    if m:
        c = _clamp([m.group(i) for i in range(1, 5)])
        if c:
            return c

    # 4. Qwen <|box_start|>x1,y1,x2,y2<|box_end|>
    m = re.search(
        r'<\|box_start\|>\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*'
        r'(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*<\|box_end\|>',
        text,
    )
    if m:
        c = _clamp([m.group(i) for i in range(1, 5)])
        if c:
            return c

    return None

"""Program synthesis — Qwen3 few-shot -> typed DSL program (JSON AST).

Reuses the V1 text-only LLM machinery verbatim (geogrounder.parsing.QwenParser: model loading,
thinking-disabled chat template, greedy decoding, balanced-JSON extraction) and swaps in the
DSL few-shot prompt. The synthesiser emits the wrapper

    {"cardinality": "single"|"group", "program": <expr AST>}

which is JSON-extracted, structurally built (grammar.build) and legality-checked (typecheck).
synthesize() never raises: a bad generation becomes a result with legal=False + errors, which
the reliability layer turns into a V1 fallback. The per-result fields feed the
program-legality gate: legal rate, fallback rate, and a raw dump for the
manual semantic-correctness sample.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional

from geogrounder.parsing.qwen_parser import QwenParser, extract_json

from .grammar import build, to_dict, GrammarError, Node, repair_program
from .typecheck import typecheck

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), '..', 'prompts',
                            'program_synthesis_fewshot.txt')
_SENTINEL = '<<SENTENCE>>'


def load_prompt(path: str = None) -> str:
    with open(path or _PROMPT_PATH, encoding='utf-8') as f:
        tmpl = f.read()
    if _SENTINEL not in tmpl:
        raise ValueError(f'prompt template missing {_SENTINEL!r} placeholder: {path}')
    return tmpl


@dataclass
class SynthResult:
    """One synthesise outcome. `legal` gates V2 vs fallback; the rest feeds the legality report."""
    sentence: str
    raw: str                                   # raw LLM text (for debugging / manual audit)
    program_dict: Optional[dict] = None        # extracted JSON program (pre-build), or None
    program: Optional[Node] = None             # typed AST when legal, else None
    cardinality: str = 'single'
    legal: bool = False
    errors: List[str] = field(default_factory=list)
    select_types: List[str] = field(default_factory=list)

    @property
    def fallback(self) -> bool:
        """True iff this sentence would fall back to V1 (illegal program)."""
        return not self.legal


def _coerce_wrapper(obj):
    """Accept {"cardinality","program"} OR a bare program object. -> (program_dict, cardinality)."""
    if isinstance(obj, dict) and 'program' in obj:
        card = obj.get('cardinality', 'single')
        card = card if card in ('single', 'group') else 'single'
        return obj['program'], card
    return obj, 'single'        # model emitted the bare program -> default single


class ProgramSynthesizer:
    """LLM -> DSL program. Wraps a text-only QwenParser for the model lifecycle (load/unload).

    Default Qwen3-4B. Any instruction-following causal LLM works (the V1 cross-
    architecture study path): point model_path at a different checkpoint, no other change."""

    def __init__(self, model_path, device='cuda', dtype='bfloat16',
                 max_new_tokens=512, prompt_path=None):
        # keep_attributes is a V1-parser knob irrelevant here; we drive generate() directly.
        self._parser = QwenParser(model_path, device=device, dtype=dtype,
                                  max_new_tokens=max_new_tokens)
        self.prompt_template = load_prompt(prompt_path)

    def load(self):
        self._parser.load()
        return self

    def unload(self):
        self._parser.unload()

    def _prompt(self, sentence: str) -> str:
        return self.prompt_template.replace(_SENTINEL, sentence)

    def synthesize(self, sentence: str, image=None) -> SynthResult:
        """Translate one sentence -> SynthResult. Never raises (errors are captured).

        `image` is used only when the wrapped parser is a Qwen3-VL model (is_vl): it is passed to
        generate() for the VL-parser ablation. Text-only parsers ignore it, so the
        headline path is byte-identical (image=None). Batched synthesis stays text-only; the VL path
        is single-sentence because each sample carries a different image."""
        if self._parser.model is None:
            raise RuntimeError('call load() first')
        raw = self._parser.generate(self._prompt(sentence), image=image)  # image used iff VL parser
        return self.parse_output(sentence, raw)

    @staticmethod
    def parse_output(sentence: str, raw: str) -> SynthResult:
        """Pure post-processing of raw LLM text -> SynthResult. Model-free, so it is unit-tested
        directly with canned `raw` strings (no GPU)."""
        res = SynthResult(sentence=sentence, raw=raw)
        try:
            obj = extract_json(raw)
        except Exception as e:
            res.errors = [f'extract_json: {type(e).__name__}: {e}']
            return res
        program_dict, card = _coerce_wrapper(obj)
        program_dict = repair_program(program_dict)   # lenient fix of benign LLM slips (stray anchor2)
        res.program_dict, res.cardinality = program_dict, card

        errors = typecheck(program_dict)        # builds internally; GrammarError -> error entry
        if errors:
            res.errors = errors
            return res
        # legal: build the typed AST and collect detector targets
        res.program = build(program_dict)
        res.legal = True
        from ..reliability import select_types   # local import to avoid a cycle at module load
        res.select_types = sorted(select_types(res.program))
        return res

    def _generate_batch(self, prompts: List[str]) -> List[str]:
        """Greedy batched generation over the text-only parser (left-padded). Per-sequence
        output is identical to the single-sentence path (padding is attention-masked), so the
        legality numbers are unchanged — this is purely a throughput win (one prefill+decode for
        the whole batch instead of one generate() call per sentence). The shared few-shot prefix
        still costs one prefill per batch, so larger batches amortise it better.

        Implemented in geoselect_v2 (NOT in geogrounder.QwenParser) so the reused V1 code stays
        byte-identical; we drive the loaded model/tokenizer directly."""
        import torch
        parser = self._parser
        if parser.is_vl:
            raise RuntimeError('batched program synthesis requires a TEXT-ONLY parser '
                               '(Qwen3-4B); got a VL model.')
        tok = parser.processor
        prev_side = tok.padding_side
        tok.padding_side = 'left'                      # decoder-only batched gen needs left pad
        try:
            texts = []
            for p in prompts:
                messages = [{'role': 'user', 'content': p}]
                try:
                    t = tok.apply_chat_template(messages, tokenize=False,
                                                add_generation_prompt=True, enable_thinking=False)
                except TypeError:
                    t = tok.apply_chat_template(messages, tokenize=False,
                                                add_generation_prompt=True)
                texts.append(t)
            inputs = tok(texts, return_tensors='pt', padding=True).to(parser.model.device)
            with torch.no_grad():
                gen = parser.model.generate(**inputs, max_new_tokens=parser.max_new_tokens,
                                            do_sample=False, pad_token_id=tok.pad_token_id)
            trimmed = gen[:, inputs.input_ids.shape[1]:]   # left pad -> uniform input length
            return tok.batch_decode(trimmed, skip_special_tokens=True,
                                    clean_up_tokenization_spaces=False)
        finally:
            tok.padding_side = prev_side

    def synthesize_batch(self, sentences) -> List[SynthResult]:
        """Synthesise a batch of sentences in ONE model.generate() call (the throughput path)."""
        if self._parser.model is None:
            raise RuntimeError('call load() first')
        prompts = [self._prompt(s) for s in sentences]
        raws = self._generate_batch(prompts)
        return [self.parse_output(s, raw) for s, raw in zip(sentences, raws)]

    def v1_parse_batch(self, sentences) -> List[dict]:
        """Batched V1 relation parse on the SAME loaded model, using V1's frozen prompt
        (geogrounder.QwenParser PROMPT_TEMPLATE, keep_attributes=False = bare class). Reuses
        _generate_batch for throughput — V1's QwenParser only parses one sentence at a time, so
        the C4 baseline parse (one per sample) would otherwise be the eval bottleneck. Output is
        identical to QwenParser.parse() (same prompt + sanitize_relation), just batched. A
        malformed generation falls back to an empty relation (the caller then has no V1 target,
        so that sample yields no fallback candidate — same as a V1 parse failure)."""
        from geogrounder.parsing.qwen_parser import (PROMPT_TEMPLATE, extract_json,
                                                     sanitize_relation)
        prompts = [PROMPT_TEMPLATE.format(sentence=s) for s in sentences]
        raws = self._generate_batch(prompts)
        out = []
        for raw in raws:
            try:
                clean, _ = sanitize_relation(extract_json(raw))
            except Exception:
                clean = {'target': '', 'cardinality': 'single', 'logic': 'and', 'relations': []}
            out.append(clean)
        return out

    def synthesize_many(self, sentences, batch_size: int = 1) -> List[SynthResult]:
        """Synthesise many sentences. batch_size>1 uses the batched path."""
        if batch_size <= 1:
            return [self.synthesize(s) for s in sentences]
        out: List[SynthResult] = []
        for i in range(0, len(sentences), batch_size):
            out.extend(self.synthesize_batch(sentences[i:i + batch_size]))
        return out

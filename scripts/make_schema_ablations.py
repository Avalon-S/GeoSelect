"""Generate the few-shot schema ablations: how much of the headline accuracy survives when the
handcrafted rules, or the in-context examples, are removed from the synthesis prompt.

From the frozen base prompt (geoselect_v2/prompts/program_synthesis_fewshot.txt) we derive three
degraded variants, holding everything else (detector, executor, SAM, reliability ladder) fixed:
  - norules   : grammar + examples, with the design-RULES block removed
  - noexamples: grammar + RULES, with all few-shot EXAMPLES removed (zero-shot schema)
  - 4shot     : grammar + RULES + only the first 4 examples (shot-count ablation)

Each variant is written next to the base prompt. Run the eval per variant on RRSIS-D val
(commands printed at the end); report mIoU and program rate against the 58.23 val headline.

    python scripts/make_schema_ablations.py
"""
import os

BASE = os.path.join(os.path.dirname(__file__), '..', 'geoselect_v2', 'prompts',
                    'program_synthesis_fewshot.txt')
KEEP_SHOTS = 4


def main():
    text = open(BASE, encoding='utf-8').read()
    lines = text.splitlines()
    # locate section markers
    i_rules = next(i for i, l in enumerate(lines) if l.strip() == 'RULES:')
    i_ex = next(i for i, l in enumerate(lines) if l.strip() == 'EXAMPLES:')
    i_now = next(i for i, l in enumerate(lines) if l.startswith('Now translate'))
    head = lines[:i_rules]                       # header + grammar + token tables
    rules = lines[i_rules:i_ex]                  # RULES: ... (+ trailing blank)
    ex_header = [lines[i_ex]]                    # 'EXAMPLES:'
    examples = [l for l in lines[i_ex + 1:i_now] if l.strip()]
    tail = lines[i_now:]                         # 'Now translate' + 'JSON:'

    def write(name, body_lines):
        out = os.path.join(os.path.dirname(BASE), name)
        open(out, 'w', encoding='utf-8').write('\n'.join(body_lines).rstrip() + '\n')
        print(f'  wrote {os.path.relpath(out)}  ({len(body_lines)} lines)')

    print('[schema-ablations] variants:')
    # 1) no design rules
    write('program_synthesis_norules.txt', head + ex_header + examples + [''] + tail)
    # 2) no examples (zero-shot schema)
    write('program_synthesis_noexamples.txt', head + rules + [''] + tail)
    # 3) only first K examples
    write('program_synthesis_4shot.txt', head + rules + ex_header + examples[:KEEP_SHOTS] + [''] + tail)

    print('\n[to reproduce: RRSIS-D val, everything else frozen]')
    cfg = 'geoselect_v2/prompts/'
    for tag, fn in [('base', 'program_synthesis_fewshot.txt'),
                    ('norules', 'program_synthesis_norules.txt'),
                    ('noexamples', 'program_synthesis_noexamples.txt'),
                    ('4shot', 'program_synthesis_4shot.txt')]:
        print(f'  python -m geoselect_v2.eval.run_eval --dataset rrsisd --split val '
              f'--set parser.prompt_path={cfg}{fn} '
              f'--selectors v2 --out-dir experiments/runs/eval_rrsisd_val_schema_{tag}')


if __name__ == '__main__':
    main()

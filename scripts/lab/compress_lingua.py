"""LLMLingua-2 compression of the sufficiency-lab skill (academic baseline).

Run with an environment that has `llmlingua` (and torch) installed; the
SkillWren package itself stays stdlib-only. Compresses the skill body (the
frontmatter stays, so the host can still discover the skill) at the given
rates, in two modes:

- plain: the whole body goes through the compressor;
- protected: inline code spans (commands, paths) are kept verbatim and only
  the prose between them is compressed.

Writes one file per (mode, rate) to --out and prints token counts.
Model: microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('lab', ROOT / 'scripts' / 'sufficiency_lab.py')
MODEL = 'microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank'


def load_lab_units():
    # Read HEADER/UNITS/ORDER without importing the lab's runtime deps.
    source = (ROOT / 'scripts' / 'sufficiency_lab.py').read_text(encoding='utf-8')
    namespace = {}
    start = source.index("HEADER = '''")
    end = source.index("PROMPT = ")
    exec(source[start:end], namespace)
    return namespace['HEADER'], namespace['UNITS'], namespace['ORDER']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--rates', default='0.5,0.33')
    args = parser.parse_args()
    from llmlingua import PromptCompressor
    compressor = PromptCompressor(model_name=MODEL, use_llmlingua2=True, device_map='cpu')
    header, units, order = load_lab_units()
    front_end = header.index('---', 3) + 3
    front, preamble = header[:front_end], header[front_end:]
    body = preamble + '\n'.join(f'{i}. {units[u]}' for i, u in enumerate(order, 1)) + '\n'
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    report = {'model': MODEL, 'original_body_chars': len(body), 'variants': {}}
    for rate in [float(r) for r in args.rates.split(',')]:
        plain = compressor.compress_prompt(body, rate=rate, force_tokens=['\n', '.'])
        text = plain['compressed_prompt']
        name = f'lingua-plain-{rate}'
        (out / f'{name}.md').write_text(front + '\n\n' + text + '\n', encoding='utf-8')
        report['variants'][name] = {'origin_tokens': plain['origin_tokens'],
                                    'compressed_tokens': plain['compressed_tokens']}
        parts = re.split(r'(`[^`]*`)', body)
        kept = []
        for part in parts:
            if part.startswith('`') or not part.strip():
                kept.append(part)
            else:
                kept.append(compressor.compress_prompt(part, rate=rate,
                                                       force_tokens=['\n', '.'])
                            ['compressed_prompt'] + ' ')
        name = f'lingua-protected-{rate}'
        protected = ''.join(kept)
        (out / f'{name}.md').write_text(front + '\n\n' + protected + '\n', encoding='utf-8')
        report['variants'][name] = {'chars': len(protected)}
    (out / 'compression.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

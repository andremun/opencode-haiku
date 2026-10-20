#!/usr/bin/env python3
"""Summarise a run_card_hybrid.sh output directory: correctness, kernel speed, end-to-end speed and text agreement. Prints Markdown."""
import json, math, re, statistics, sys, difflib
from pathlib import Path

d = Path(sys.argv[1])
ANSI = re.compile(r'\x1b\[[0-9;]*m')
LIBS = ['nvcc', 'nofinite', 'nofast', 'hybnofinite', 'hybnofast', 'nvcc2']
CASE = re.compile(r'^\s+(?=(?:MUL_MAT_ID|MUL_MAT|FLASH_ATTN_EXT)\()', re.M)

def parse(path):
    text = ANSI.sub('', path.read_text(errors='replace'))
    out = {}
    for chunk in CASE.split(text):
        m = re.match(r'(MUL_MAT_ID|MUL_MAT|FLASH_ATTN_EXT)\((.*?)\):', chunk, re.S)
        r = re.search(r'(\d+) runs\s+-\s+([\d.]+) us/run', chunk)
        if m and r: out[m.group(1) + '(' + m.group(2) + ')'] = float(r.group(2))
    return out

print('## Correctness (`test-backend-ops` against the CPU backend)\n')
print('| operation | ' + ' | '.join(LIBS[:5]) + ' |\n|---|' + '---|' * 5)
for op in ['FLASH_ATTN_EXT', 'SOFT_MAX', 'MUL_MAT', 'MUL_MAT_ID']:
    row = []
    for lib in LIBS[:5]:
        p = d / f'test-{op}-{lib}.log'
        if not p.exists(): row.append('n/a'); continue
        m = re.findall(r'(\d+)/(\d+) tests passed', ANSI.sub('', p.read_text(errors='replace')))
        row.append(f'{m[-1][0]}/{m[-1][1]}' if m else 'no result')
    print(f'| {op} | ' + ' | '.join(row) + ' |')

print('\n## Kernel speed (production quantisation types; ratio = library / mean of the two nvcc runs, lower is faster)\n')
print('| operation | library | cases | median ratio | geometric mean | >10% slower | >10% faster | nvcc drift |\n|---|---|---|---|---|---|---|---|')
for op in ['MUL_MAT', 'MUL_MAT_ID', 'FLASH_ATTN_EXT']:
    base_a, base_b = d / f'perf-{op}-nvcc.log', d / f'perf-{op}-nvcc2.log'
    if not (base_a.exists() and base_b.exists()): continue
    a, b = parse(base_a), parse(base_b)
    for lib in LIBS[1:5]:
        p = d / f'perf-{op}-{lib}.log'
        if not p.exists(): continue
        c = parse(p)
        common = sorted(set(a) & set(b) & set(c))
        if not common: continue
        r = [c[k] / ((a[k] + b[k]) / 2) for k in common]
        drift = statistics.median(b[k] / a[k] for k in common)
        print(f'| {op} | {lib} | {len(r)} | {statistics.median(r):.3f} | {math.exp(statistics.mean(math.log(x) for x in r)):.3f} | {sum(x > 1.1 for x in r)} | {sum(x < 0.9 for x in r)} | {drift:.3f} |')

print('\n## End to end: llama-bench, Qwen3.5-9B Q4_K_XL fully on the card (tokens/s, mean of 3)\n')
print('| library | prompt 512 | generation 128 |\n|---|---|---|')
for lib in LIBS:
    p = d / f'bench-{lib}.json'
    try:
        rows = json.loads(p.read_text())
        pp = [x for x in rows if x['n_prompt'] > 0 and x['n_gen'] == 0][0]; tg = [x for x in rows if x['n_gen'] > 0 and x['n_prompt'] == 0][0]
        print(f"| {lib} | {pp['avg_ts']:.2f} (sd {pp['stddev_ts']:.2f}) | {tg['avg_ts']:.2f} (sd {tg['stddev_ts']:.2f}) |")
    except Exception as e:
        print(f'| {lib} | n/a | n/a |')

print('\n## Greedy text for the same prompt (48 tokens, seed 1, through llama-server) against the nvcc build\n')
def text_of(lib):
    p = d / f'text-{lib}.json'
    try: return json.loads(p.read_text())['content']
    except Exception: return None
ref = text_of('nvcc')
print('| library | identical to nvcc | note |\n|---|---|---|')
for lib in LIBS[:5]:
    t = text_of(lib)
    if t is None or ref is None: print(f'| {lib} | n/a | |'); continue
    if t == ref: print(f'| {lib} | yes | |'); continue
    i = next((k for k, (x, y) in enumerate(zip(t, ref)) if x != y), min(len(t), len(ref)))
    print(f'| {lib} | **no** | first difference at character {i}: {t[max(0,i-15):i+30]!r} against {ref[max(0,i-15):i+30]!r} |')

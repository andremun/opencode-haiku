#!/usr/bin/env python3
"""Summarise a run_card_hybrid.sh output directory: correctness, kernel speed, end-to-end speed (9B and production) and text agreement."""
import json, math, re, statistics, sys
from pathlib import Path

d = Path(sys.argv[1])
ANSI = re.compile(r'\x1b\[[0-9;]*m')
LIBS = ['nvcc', 'nofinite', 'nofast', 'ieee', 'hybnofinite', 'hybnofast', 'hybieee', 'nvcc2']
CASE = re.compile(r'^\s+(?=(?:MUL_MAT_ID|MUL_MAT|FLASH_ATTN_EXT)\()', re.M)

def exists(pattern): return any(d.glob(pattern))

def parse(path):
    text = ANSI.sub('', path.read_text(errors='replace'))
    out = {}
    for chunk in CASE.split(text):
        m = re.match(r'(MUL_MAT_ID|MUL_MAT|FLASH_ATTN_EXT)\((.*?)\):', chunk, re.S)
        r = re.search(r'(\d+) runs\s+-\s+([\d.]+) us/run', chunk)
        if m and r: out[m.group(1) + '(' + m.group(2) + ')'] = float(r.group(2))
    return out

corr = [l for l in LIBS if l != 'nvcc2' and exists(f'test-*-{l}.log')]
if corr:
    print('## Correctness (`test-backend-ops` against the CPU backend)\n')
    print('| operation | ' + ' | '.join(corr) + ' |\n|---|' + '---|' * len(corr))
    for op in ['FLASH_ATTN_EXT', 'SOFT_MAX', 'MUL_MAT', 'MUL_MAT_ID']:
        row = []
        for lib in corr:
            p = d / f'test-{op}-{lib}.log'
            if not p.exists(): row.append('n/a'); continue
            m = re.findall(r'(\d+)/(\d+) tests passed', ANSI.sub('', p.read_text(errors='replace')))
            row.append(f'{m[-1][0]}/{m[-1][1]}' if m else 'no result')
        print(f'| {op} | ' + ' | '.join(row) + ' |')

if exists('perf-*.log'):
    print('\n## Kernel speed (ratio = library / mean of the two nvcc runs, lower is faster)\n')
    print('| operation | library | cases | median ratio | geometric mean | >10% slower | >10% faster | nvcc drift |\n|---|---|---|---|---|---|---|---|')
    for op in ['MUL_MAT', 'MUL_MAT_ID', 'FLASH_ATTN_EXT']:
        base_a, base_b = d / f'perf-{op}-nvcc.log', d / f'perf-{op}-nvcc2.log'
        if not (base_a.exists() and base_b.exists()): continue
        a, b = parse(base_a), parse(base_b)
        for lib in LIBS:
            if lib in ('nvcc', 'nvcc2'): continue
            p = d / f'perf-{op}-{lib}.log'
            if not p.exists(): continue
            c = parse(p); common = sorted(set(a) & set(b) & set(c))
            if not common: continue
            r = [c[k] / ((a[k] + b[k]) / 2) for k in common]
            drift = statistics.median(b[k] / a[k] for k in common)
            print(f'| {op} | {lib} | {len(r)} | {statistics.median(r):.3f} | {math.exp(statistics.mean(math.log(x) for x in r)):.3f} | {sum(x > 1.1 for x in r)} | {sum(x < 0.9 for x in r)} | {drift:.3f} |')

def bench_table(prefix, title):
    rows_out = []
    for lib in LIBS:
        p = d / f'{prefix}-{lib}.json'
        if not p.exists(): continue
        try:
            rows = json.loads(p.read_text())
            pp = [x for x in rows if x['n_prompt'] > 0 and x['n_gen'] == 0][0]; tg = [x for x in rows if x['n_gen'] > 0 and x['n_prompt'] == 0][0]
            rows_out.append(f"| {lib} | {pp['avg_ts']:.2f} (sd {pp['stddev_ts']:.2f}) | {tg['avg_ts']:.2f} (sd {tg['stddev_ts']:.2f}) |")
        except Exception:
            rows_out.append(f'| {lib} | n/a | n/a |')
    if rows_out:
        print(f'\n## {title} (tokens/s)\n\n| library | prompt 512 | generation |\n|---|---|---|')
        print('\n'.join(rows_out))
bench_table('bench', 'End to end: llama-bench, Qwen3.5-9B Q4_K_XL fully on the card')
bench_table('prod-bench', 'Production model: Qwen3.6-35B-A3B Q4_K_XL, one card, 30 expert layers on the CPU, as in llama-server-one.service')

def text_of(path):
    try: return json.loads(path.read_text())['content']
    except Exception: return None

for tag, title in (('9b', 'Qwen3.5-9B'), ('prod', 'Qwen3.6-35B production model')):
    libs = [l for l in LIBS if (d / f'text-{tag}-{l}-1.json').exists()]
    if not libs: continue
    print(f'\n## Greedy text, {title} (two prompts, 64 tokens, seed 1, through llama-server) against the nvcc build\n')
    print('| library | prompt 1 | prompt 2 |\n|---|---|---|')
    for lib in libs:
        cells = []
        for n in (1, 2):
            t, ref = text_of(d / f'text-{tag}-{lib}-{n}.json'), text_of(d / f'text-{tag}-nvcc-{n}.json')
            if t is None or ref is None: cells.append('n/a'); continue
            if t == ref: cells.append('identical'); continue
            i = next((k for k, (x, y) in enumerate(zip(t, ref)) if x != y), min(len(t), len(ref)))
            cells.append(f'**differs** at character {i}: {t[max(0,i-12):i+25]!r} vs {ref[max(0,i-12):i+25]!r}')
        print(f'| {lib} | {cells[0]} | {cells[1]} |')

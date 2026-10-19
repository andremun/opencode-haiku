#!/usr/bin/env python3
"""Summarise an on-card comparison directory produced by run_card_comparison.sh (nvcc vs Clang, A-B-A). Prints Markdown."""
import json, math, re, statistics, sys
from pathlib import Path

d = Path(sys.argv[1])
ANSI = re.compile(r'\x1b\[[0-9;]*m')
CASE = re.compile(r'^\s+(?=(?:MUL_MAT_ID|MUL_MAT|FLASH_ATTN_EXT)\()', re.M)

def parse(path):
    text = ANSI.sub('', path.read_text(errors='replace'))
    out = {}
    for chunk in CASE.split(text):
        m = re.match(r'(MUL_MAT_ID|MUL_MAT|FLASH_ATTN_EXT)\((.*?)\):', chunk, re.S)
        r = re.search(r'(\d+) runs\s+-\s+([\d.]+) us/run', chunk)
        if m and r:
            out[m.group(1) + '(' + m.group(2) + ')'] = float(r.group(2))
    return out

def field(case, key):
    m = re.search(r'\b' + key + r'=([^,)]+)', case)
    return m.group(1) if m else None

print('## Correctness (test-backend-ops vs CPU backend)\n')
print('| operation | nvcc | Clang |\n|---|---|---|')
for op in ['MUL_MAT', 'MUL_MAT_ID', 'FLASH_ATTN_EXT', 'SOFT_MAX', 'RMS_NORM', 'ROPE', 'GET_ROWS', 'CPY', 'SCALE', 'ADD', 'MUL', 'UNARY', 'GLU', 'ARGSORT', 'TOP_K', 'SUM_ROWS', 'CONCAT']:
    row = []
    for v in ('nvcc', 'clang'):
        t = ANSI.sub('', (d / f'test-{op}-{v}.log').read_text(errors='replace')) if (d / f'test-{op}-{v}.log').exists() else ''
        m = re.findall(r'(\d+)/(\d+) tests passed', t)
        row.append(f'{m[-1][0]}/{m[-1][1]}' if m else 'n/a')
    print(f'| {op} | {row[0]} | {row[1]} |')

print('\n## Kernel performance (test-backend-ops perf, us/run; ratio = Clang / mean(nvcc, nvcc2), lower is faster)\n')
print('| operation | cases | median ratio | geometric mean | Clang >10% slower | Clang >10% faster | nvcc2/nvcc drift (median) |\n|---|---|---|---|---|---|---|')
detail = {}
for op in ['MUL_MAT', 'MUL_MAT_ID', 'FLASH_ATTN_EXT']:
    a, c, b = (parse(d / f'perf-{op}-{v}.log') for v in ('nvcc', 'clang', 'nvcc2'))
    common = sorted(set(a) & set(c) & set(b))
    ratios, drift = [], []
    for k in common:
        base = (a[k] + b[k]) / 2
        ratios.append((k, c[k] / base)); drift.append(b[k] / a[k])
    if not ratios: print(f'| {op} | 0 | | | | | |'); continue
    r = [x for _, x in ratios]
    gm = math.exp(statistics.mean(math.log(x) for x in r))
    print(f'| {op} | {len(r)} | {statistics.median(r):.3f} | {gm:.3f} | {sum(x > 1.1 for x in r)} | {sum(x < 0.9 for x in r)} | {statistics.median(drift):.3f} |')
    detail[op] = ratios
print('\n### By quantisation type and batch (MUL_MAT and MUL_MAT_ID; n = 1 is token generation)\n')
print('| op | type_a | n | cases | median ratio |\n|---|---|---|---|---|')
for op in ('MUL_MAT', 'MUL_MAT_ID'):
    groups = {}
    for k, x in detail.get(op, []):
        t, n = field(k, 'type_a'), field(k, 'n')
        groups.setdefault((t, 'n=1' if n == '1' else 'n>1'), []).append(x)
    for (t, nb), xs in sorted(groups.items(), key=lambda kv: (kv[0][0] or '', kv[0][1])):
        if t in ('q4_K', 'q5_K', 'q6_K', 'q8_0', 'f16', 'f32', 'q4_0'):
            print(f'| {op} | {t} | {nb} | {len(xs)} | {statistics.median(xs):.3f} |')

print('\n## End to end: llama-bench, Qwen3.5-9B Q4_K_XL fully on the card (tokens/s, mean of 3)\n')
print('| run | prompt 512 | generation 128 |\n|---|---|---|')
for v in ('nvcc', 'clang', 'nvcc2'):
    p = d / f'bench-{v}.json'
    try:
        rows = json.loads(p.read_text())
        pp = [x for x in rows if x['n_prompt'] > 0 and x['n_gen'] == 0]; tg = [x for x in rows if x['n_gen'] > 0 and x['n_prompt'] == 0]
        print(f"| {v} | {pp[0]['avg_ts']:.2f} (sd {pp[0]['stddev_ts']:.2f}) | {tg[0]['avg_ts']:.2f} (sd {tg[0]['stddev_ts']:.2f}) |")
    except Exception as e:
        print(f'| {v} | n/a ({e}) | |')

#!/usr/bin/env python3
"""Summarise compare_compilers.py results (one or more results.json files). Prints Markdown."""
import json, re, statistics, sys
from pathlib import Path

import subprocess
_cache = {}
def demangle_all(names):
    todo = [n for n in names if n not in _cache]
    if todo:
        out = subprocess.run(['c++filt'], input='\n'.join(todo), capture_output=True, text=True).stdout.split('\n')
        for n, d in zip(todo, out):
            d = re.sub(r'_INTERNAL_\d+_tmpxft_[0-9a-f]+_\d+_\w*?_ii_[0-9a-f]+::', '', d)   # nvcc temp-file name in internal symbols
            d = d.replace('(anonymous namespace)::', '')
            d = re.sub(r'&\((\w+)\([^()]*\)\)', r'&\1', d)               # Clang writes &(f(args)), nvcc &f
            _cache[n] = d
    return _cache
def norm(name):
    return _cache.get(name, name)

rows, results = [], []
for path in sys.argv[1:]:
    results += json.loads(Path(path).read_text())
files = sorted({r['file'] for r in results})
tot = dict(files=0, clang_fail=0, nvcc_fail=0)
agg_regs, agg_spill_n, agg_spill_c, kernels_n, kernels_c, sass_n, sass_c, matched = [], 0, 0, 0, 0, 0, 0, 0
worse, better, same, risky = [], [], 0, []
failures = []
for f in files:
    by = {}
    for r in results:
        if r['file'] == f: by[r['compiler']] = r   # later results override earlier ones
    n, c = by.get('nvcc'), by.get('clang')
    if not n or not c: continue
    tot['files'] += 1
    if n['rc']: tot['nvcc_fail'] += 1; failures.append((f, 'nvcc', n.get('errors', [])[:1]))
    if c['rc']: tot['clang_fail'] += 1; failures.append((f, 'clang', c.get('errors', [])[:1]))
    if n['rc'] or c['rc']: continue
    demangle_all(list(n['kernels']) + list(c['kernels']))
    kn = {norm(k): v for k, v in n['kernels'].items()}; kc = {norm(k): v for k, v in c['kernels'].items()}
    kernels_n += len(kn); kernels_c += len(kc)
    sass_n += n['sass_instructions']; sass_c += c['sass_instructions']
    common = sorted(set(kn) & set(kc)); matched += len(common)
    for k in common:
        a, b = kn[k], kc[k]
        agg_regs.append((a['regs'], b['regs']))
        if a.get('spill_store', 0) + a.get('spill_load', 0): agg_spill_n += 1
        if b.get('spill_store', 0) + b.get('spill_load', 0): agg_spill_c += 1
        if b['regs'] > a['regs']: worse.append((f, k, a['regs'], b['regs']))
        elif b['regs'] < a['regs']: better.append((f, k, a['regs'], b['regs']))
        else: same += 1
        if b['regs'] >= a['regs'] + 8: risky.append((f, k, a['regs'], b['regs']))
    rows.append((f, len(kn), len(kc), len(common), n['sass_instructions'], c['sass_instructions'], round(c['sass_instructions'] / max(1, n['sass_instructions']), 2)))
print('| file | kernels nvcc | kernels clang | matched | SASS nvcc | SASS clang | clang/nvcc |\n|---|---|---|---|---|---|---|')
for r in rows: print('| ' + ' | '.join(map(str, r)) + ' |')
print()
print(f"files compared: {tot['files']}, nvcc failures: {tot['nvcc_fail']}, clang failures: {tot['clang_fail']}")
print(f"kernels: nvcc {kernels_n}, clang {kernels_c}, matched by name {matched}")
print(f"total SASS instructions (files where both compiled): nvcc {sass_n}, clang {sass_c}, ratio {sass_c / max(1, sass_n):.3f}")
if agg_regs:
    ratios = [b / a for a, b in agg_regs if a]
    print(f"registers per matched kernel: median clang/nvcc {statistics.median(ratios):.3f}; clang higher {len(worse)}, lower {len(better)}, equal {same}; clang >= nvcc+8: {len(risky)}")
    print(f"max registers: nvcc {max(a for a, _ in agg_regs)}, clang {max(b for _, b in agg_regs)}; kernels with spills: nvcc {agg_spill_n}, clang {agg_spill_c}")
    print('largest clang register increases:', [(f, k[:50], a, b) for f, k, a, b in sorted(risky, key=lambda x: x[3] - x[2], reverse=True)[:5]])
    print('largest clang register decreases:', [(f, k[:50], a, b) for f, k, a, b in sorted(better, key=lambda x: x[2] - x[3], reverse=True)[:5]])
if failures: print('failures:', failures)

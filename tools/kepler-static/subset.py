#!/usr/bin/env python3
"""Register/spill/occupancy comparison for the kernel families the production model uses."""
import json, re, statistics, subprocess, sys
from pathlib import Path
src = open(Path(__file__).with_name('analyze.py')).read().split('rows, results')[0]
ns = {}; exec(src, ns)
results = []
for p in sys.argv[1:]: results += json.loads(Path(p).read_text())
by = {}
for r in results:
    if r['rc'] == 0: by[(r['file'], r['compiler'])] = r        # later files override earlier ones
FAMILIES = {
  'mul_mat_vec_q (Q8_0,Q4_K,Q5_K,Q6_K)': r'mul_mat_vec_q<\(ggml_type\)(8|12|13|14),',
  'mul_mat_q (Q8_0,Q4_K,Q6_K)': r'mul_mat_q<\(ggml_type\)(8|12|14),',
  'flash_attn_ext_vec': r'flash_attn_ext_vec<',
  'flash_attn_tile': r'flash_attn_tile<',
  'mul_mat_vec_f (f16/f32)': r'mul_mat_vec_f<',
  'other (all remaining matched)': None,
}
rows = {k: [] for k in FAMILIES}
for f in sorted({f for f, _ in by}):
    n, c = by.get((f, 'nvcc')), by.get((f, 'clang'))
    if not n or not c: continue
    ns['demangle_all'](list(n['kernels']) + list(c['kernels']))
    kn = {ns['norm'](k): v for k, v in n['kernels'].items()}; kc = {ns['norm'](k): v for k, v in c['kernels'].items()}
    for k in set(kn) & set(kc):
        placed = False
        for fam, pat in FAMILIES.items():
            if pat and re.search(pat, k):
                rows[fam].append((kn[k], kc[k])); placed = True; break
        if not placed: rows['other (all remaining matched)'].append((kn[k], kc[k]))
def occ(r): return min(2048, 65536 // max(r, 1))   # threads per SM limited by registers (sm_35: 64K regs, 2048 threads)
print('| family | kernels | median regs nvcc | median regs clang | spilling nvcc | spilling clang | mean occupancy proxy nvcc | clang |\n|---|---|---|---|---|---|---|---|')
for fam, rs in rows.items():
    if not rs: continue
    sp = lambda v: v.get('spill_store', 0) + v.get('spill_load', 0) > 0
    print(f"| {fam} | {len(rs)} | {statistics.median(a['regs'] for a, _ in rs):.0f} | {statistics.median(b['regs'] for _, b in rs):.0f} | "
          f"{sum(sp(a) for a, _ in rs)} | {sum(sp(b) for _, b in rs)} | {statistics.mean(occ(a['regs']) for a, _ in rs):.0f} | {statistics.mean(occ(b['regs']) for _, b in rs):.0f} |")
# spill volume
tn = sum(a.get('spill_store', 0) + a.get('spill_load', 0) for rs in rows.values() for a, _ in rs)
tc = sum(b.get('spill_store', 0) + b.get('spill_load', 0) for rs in rows.values() for _, b in rs)
print(f"\ntotal spill bytes (stores+loads): nvcc {tn}, clang {tc}")

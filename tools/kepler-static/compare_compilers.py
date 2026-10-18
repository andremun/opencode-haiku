#!/usr/bin/env python3
"""GPU-free comparison of nvcc 11.4 and Clang for ggml-cuda kernels targeting sm_35.

Compiles selected ggml-cuda sources from a READ-ONLY llama.cpp checkout with both compilers into an
output directory, parses `ptxas -v` (registers, spills, shared memory per kernel) and counts SASS
instructions with `cuobjdump`. Nothing here loads a module or touches a GPU.

Usage: compare_compilers.py --clang-bin DIR --out DIR [--ptx 74] FILE.cu [FILE.cu ...]
FILE is relative to ggml/src/ggml-cuda/ of the checkout (default ~/llm-server/llama.cpp).
"""
import argparse, json, os, re, statistics, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SRC = Path(os.environ.get('LLAMA_SRC', Path.home() / 'llm-server/llama.cpp'))
CUDA = Path(os.environ.get('CUDA_PATH', '/usr/local/cuda-11.4'))
GPP = Path(os.environ.get('NVCC_HOST_CXX', Path.home() / '.local/opt/gcc10/root/usr/bin/g++-10'))
GCC_DIR = os.environ.get('CLANG_GCC_DIR', '/usr/lib/gcc/x86_64-linux-gnu/11')  # needs libstdc++ headers
DEFS = ['-DGGML_BACKEND_BUILD', '-DGGML_BACKEND_SHARED', '-DGGML_CUDA_PEER_MAX_BATCH_SIZE=128', '-DGGML_CUDA_USE_GRAPHS',
        '-DGGML_SCHED_MAX_COPIES=4', '-DGGML_SHARED', '-D_GNU_SOURCE', '-D_XOPEN_SOURCE=600']
INC = [f'-I{SRC}/ggml/src', f'-I{SRC}/ggml/include', '-isystem', f'{CUDA}/targets/x86_64-linux/include']

def parse_ptxas(text):
    kernels, current = {}, None
    for line in text.splitlines():
        m = re.search(r"Compiling entry function '([^']+)' for 'sm_35'", line)
        if m:
            current = m.group(1); kernels.setdefault(current, {})
            continue
        m = re.search(r'Function properties for (\S+)', line)
        if m:
            current = m.group(1); kernels.setdefault(current, {}); continue
        m = re.search(r'(\d+) bytes spill stores, (\d+) bytes spill loads', line)
        if m and current:
            kernels[current]['spill_store'] = int(m.group(1)); kernels[current]['spill_load'] = int(m.group(2)); continue
        m = re.search(r'Used (\d+) registers(?:, (\d+) bytes smem)?', line)
        if m and current:
            kernels[current]['regs'] = int(m.group(1))
            if m.group(2): kernels[current]['smem'] = int(m.group(2))
    return {k: v for k, v in kernels.items() if 'regs' in v}

def sass_count(obj):
    out = subprocess.run([str(CUDA / 'bin/cuobjdump'), '-sass', str(obj)], capture_output=True, text=True).stdout
    return len(re.findall(r'^\s+/\*[0-9a-f]{4}\*/\s+[@A-Z]', out, re.M))

def run(tool, cmd, log):
    t = time.time()
    p = subprocess.run(['nice', '-n', '19'] + cmd, capture_output=True, text=True)
    Path(log).write_text(p.stdout + '\n' + p.stderr)
    return p.returncode, time.time() - t, p.stdout + p.stderr

def compile_one(job):
    name, compiler, out, clang_bin, ptx, includes, extra_flags = job
    src = SRC / 'ggml/src/ggml-cuda' / name
    stem = name.replace('/', '_')
    obj = out / f'{stem}.{compiler}.o'
    if compiler == 'nvcc':
        cmd = [str(CUDA / 'bin/nvcc'), '-ccbin', str(GPP), '-O3', '-DNDEBUG', '-std=c++17', '--generate-code=arch=compute_35,code=[compute_35,sm_35]',
               '-Xcompiler=-fPIC', '-use_fast_math', '-extended-lambda', *DEFS, *INC, '-Xptxas', '-v', '-w', '-c', str(src), '-o', str(obj)]
    else:
        cmd = [str(clang_bin / 'clang++'), f'--gcc-install-dir={GCC_DIR}', '-x', 'cuda', f'--cuda-path={CUDA}', '--cuda-gpu-arch=sm_35', '--cuda-device-only', '-O3', '-DNDEBUG',
               '-std=c++17', '-ffast-math', '-fPIC', *DEFS, *INC, '-Xcuda-ptxas', '-v', '-w', '-c', str(src), '-o', str(obj)]
        for inc in includes:
            cmd += ['-include', inc]
        cmd += extra_flags
        if ptx:
            cmd += ['-Xclang', '-target-feature', '-Xclang', f'+ptx{ptx}']
    rc, secs, text = run(compiler, cmd, out / f'{stem}.{compiler}.log')
    result = {'file': name, 'compiler': compiler, 'rc': rc, 'seconds': round(secs, 1)}
    if rc == 0:
        result['kernels'] = parse_ptxas(text)
        result['sass_instructions'] = sass_count(obj)
        result['object_bytes'] = obj.stat().st_size
    else:
        errs = [l for l in text.splitlines() if 'error' in l.lower()]
        result['errors'] = errs[:8]
        result['error_count'] = len(errs)
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--clang-bin', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--ptx', default='', help='PTX ISA version to request from Clang, e.g. 74')
    ap.add_argument('--jobs', type=int, default=2)
    ap.add_argument('--compilers', default='nvcc,clang', help='comma list; use clang to rerun only Clang')
    ap.add_argument('--clang-flag', action='append', default=[], help='extra Clang flag (repeatable)')
    ap.add_argument('--clang-include', action='append', default=[], help='header forced into every Clang compile (e.g. clang_cg_shim.h)')
    ap.add_argument('files', nargs='+')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    jobs = [(f, c, a.out, a.clang_bin, a.ptx, a.clang_include, a.clang_flag) for f in a.files for c in a.compilers.split(',')]
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        results = list(pool.map(compile_one, jobs))
    (a.out / 'results.json').write_text(json.dumps(results, indent=1))
    for f in a.files:
        r = {x['compiler']: x for x in results if x['file'] == f}
        if len(r) < 2: print(f"{f}: {list(r)[0]} rc={r[list(r)[0]]['rc']} {r[list(r)[0]]['seconds']}s"); continue
        n, c = r['nvcc'], r['clang']
        line = f"{f}: nvcc rc={n['rc']} {n['seconds']}s | clang rc={c['rc']} {c['seconds']}s"
        if n['rc'] == 0 and c['rc'] == 0:
            common = sorted(set(n['kernels']) & set(c['kernels']))
            line += f" | kernels nvcc={len(n['kernels'])} clang={len(c['kernels'])} common={len(common)} | SASS nvcc={n['sass_instructions']} clang={c['sass_instructions']}"
        print(line)

if __name__ == '__main__':
    main()

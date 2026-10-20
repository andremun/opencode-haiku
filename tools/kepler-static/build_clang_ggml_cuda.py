#!/usr/bin/env python3
"""Build libggml-cuda.so with Clang (host + device, sm_35) from the READ-ONLY llama.cpp checkout.

Mirrors the object list of the deployed nvcc build so that only the compiler differs. Output goes to a private
directory; the deployed build is not modified. CPU only: nothing here touches a GPU.
Usage: build_clang_ggml_cuda.py --clang-bin DIR --out DIR [--jobs N]
"""
import argparse, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SRC = Path(os.environ.get('LLAMA_SRC', Path.home() / 'llm-server/llama.cpp'))
BUILD = SRC / 'build'
CUDA = Path('/usr/local/cuda-11.4')
GCC_DIR = os.environ.get('CLANG_GCC_DIR', '/usr/lib/gcc/x86_64-linux-gnu/11')
GPP = Path.home() / '.local/opt/gcc10/root/usr/bin/g++-10'
DEFS = ['-DGGML_BACKEND_BUILD', '-DGGML_BACKEND_SHARED', '-DGGML_CUDA_PEER_MAX_BATCH_SIZE=128', '-DGGML_CUDA_USE_GRAPHS',
        '-DGGML_SCHED_MAX_COPIES=4', '-DGGML_SHARED', '-D_GNU_SOURCE', '-D_XOPEN_SOURCE=600', '-Dggml_cuda_EXPORTS']
INC = [f'-I{SRC}/ggml/src', f'-I{SRC}/ggml/include', '-isystem', f'{CUDA}/targets/x86_64-linux/include']
_NVCC_FAST = ['-fcuda-flush-denormals-to-zero', '-fcuda-approx-transcendentals',
              '-mllvm', '-nvptx-prec-divf32=1', '-mllvm', '-nvptx-prec-sqrtf32=0']   # mirror nvcc -use_fast_math
MATH_PROFILES = {
    'ffast': ['-ffast-math'] + _NVCC_FAST,                           # first run: attention gave NaN (finite-math-only assumed)
    'nofinite': ['-ffast-math', '-fno-finite-math-only'] + _NVCC_FAST,  # keep fast-math but allow infinities and NaNs
    'nofast': list(_NVCC_FAST),                                      # no -ffast-math at all
}
FASTMATH = MATH_PROFILES['ffast']

def sources():
    rsp = (BUILD / 'ggml/src/ggml-cuda/CMakeFiles/ggml-cuda.dir/objects1.rsp').read_text()
    for obj in re.findall(r'"([^"]+)"', rsp):
        rel = obj.split('ggml-cuda.dir/', 1)[1][:-2]            # drop .o -> foo.cu
        yield rel

def compile_one(args):
    rel, clang_bin, out, shim = args
    obj = out / (rel.replace('/', '_') + '.o')
    cmd = ['nice', '-n', '10', str(clang_bin / 'clang++'), f'--gcc-install-dir={GCC_DIR}', '-x', 'cuda', f'--cuda-path={CUDA}',
           '--cuda-gpu-arch=sm_35', '-O3', '-DNDEBUG', '-std=c++17', '-fPIC', *FASTMATH, *DEFS, *INC, '-include', str(shim), '-w',
           '-c', str(SRC / 'ggml/src/ggml-cuda' / rel), '-o', str(obj)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    (out / (rel.replace('/', '_') + '.log')).write_text(p.stdout + p.stderr)
    return rel, p.returncode, obj

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--clang-bin', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--jobs', type=int, default=10)
    ap.add_argument('--math', choices=sorted(MATH_PROFILES), default='ffast', help='floating-point flag profile')
    a = ap.parse_args()
    global FASTMATH
    FASTMATH = MATH_PROFILES[a.math]
    a.out.mkdir(parents=True, exist_ok=True)
    shim = Path(__file__).with_name('clang_cg_shim.h')
    files = list(sources())
    print(f'{len(files)} sources', flush=True)
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        results = list(pool.map(compile_one, [(f, a.clang_bin, a.out, shim) for f in files]))
    bad = [(r, rc) for r, rc, _ in results if rc]
    print(f'compiled {len(results) - len(bad)}/{len(results)}; failures: {bad}', flush=True)
    if bad: sys.exit(1)
    lib = a.out / 'libggml-cuda.so.0.9.11'
    link = [str(GPP), '-fPIC', '-shared', '-Wl,-soname,libggml-cuda.so.0', '-o', str(lib), *[str(o) for _, _, o in results],
            f'-Wl,-rpath,{BUILD}/bin', str(BUILD / 'bin/libggml-base.so.0.9.11'),
            f'{CUDA}/targets/x86_64-linux/lib/libcudart.so', f'{CUDA}/targets/x86_64-linux/lib/libcublas.so',
            f'{CUDA}/targets/x86_64-linux/lib/stubs/libcuda.so', f'{CUDA}/targets/x86_64-linux/lib/libcublasLt.so',
            f'{CUDA}/targets/x86_64-linux/lib/libculibos.a', '-ldl', '/usr/lib/x86_64-linux-gnu/librt.a', '-lcudadevrt', '-lcudart_static', '-lrt', '-lpthread', '-ldl',
            f'-L{CUDA}/targets/x86_64-linux/lib/stubs', f'-L{CUDA}/targets/x86_64-linux/lib']
    p = subprocess.run(link, capture_output=True, text=True)
    (a.out / 'link.log').write_text(p.stdout + p.stderr)
    print('link rc', p.returncode, flush=True)
    sys.exit(p.returncode)

if __name__ == '__main__':
    main()

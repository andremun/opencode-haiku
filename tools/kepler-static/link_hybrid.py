#!/usr/bin/env python3
"""Link a hybrid libggml-cuda.so from deployed nvcc objects and Clang objects (relink only, nothing recompiled).

Usage: link_hybrid.py --clang-dir DIR --out DIR --use FILE.cu [--use FILE.cu ...]
Every source of the deployed target comes from the nvcc object (read-only, in the deployed build directory) unless listed
with --use, in which case the Clang object from --clang-dir is taken. Before linking it checks that no device kernel is
defined in objects of BOTH compilers: such a kernel would have two host stubs with one name, the linker keeps one, and
the CUDA runtime may launch the other compiler's version without any error. Exit status 3 means a collision.
CPU only: nothing here touches a GPU.
"""
import argparse, json, os, re, subprocess, sys
from pathlib import Path

SRC = Path(os.environ.get('LLAMA_SRC', Path.home() / 'llm-server/llama.cpp'))
BUILD = SRC / 'build'
CUDA = Path('/usr/local/cuda-11.4')
GPP = Path.home() / '.local/opt/gcc10/root/usr/bin/g++-10'
NVCC_OBJ_DIR = BUILD / 'ggml/src/ggml-cuda/CMakeFiles/ggml-cuda.dir'

def sources():
    rsp = (NVCC_OBJ_DIR / 'objects1.rsp').read_text()
    return [o.split('ggml-cuda.dir/', 1)[1][:-2] for o in re.findall(r'"([^"]+)"', rsp)]

CACHE = Path.home() / 'kepler-llvm-eval/kernel-cache'

def kernels(obj):
    CACHE.mkdir(parents=True, exist_ok=True)
    st = Path(obj).stat()
    key = CACHE / (re.sub(r'[^A-Za-z0-9_.-]', '_', str(obj))[-150:] + f'.{st.st_size}.{int(st.st_mtime)}.json')
    if key.exists(): return json.loads(key.read_text())
    result = _kernels(obj)
    key.write_text(json.dumps(result))
    return result

def _kernels(obj):
    out = subprocess.run([str(CUDA / 'bin/cuobjdump'), '-sass', str(obj)], capture_output=True, text=True).stdout
    names = set(re.findall(r'^\s+Function : (\S+)', out, re.M))
    if not names: return {}
    dem = subprocess.run(['c++filt'], input='\n'.join(sorted(names)), capture_output=True, text=True).stdout.split('\n')
    norm = {}
    for n, d in zip(sorted(names), dem):
        d = re.sub(r'_INTERNAL_\d+_tmpxft_[0-9a-f]+_\d+_\w*?_ii_[0-9a-f]+::', '', d).replace('(anonymous namespace)::', '')
        norm[re.sub(r'&\((\w+)\([^()]*\)\)', r'&\1', d)] = n
    return norm

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--clang-dir', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--use', action='append', default=[], help='source (relative to ggml/src/ggml-cuda) taken from Clang')
    ap.add_argument('--use-glob', action='append', default=[], help='shell pattern over sources taken from Clang, e.g. template-instances/mmq-instance-*.cu')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    srcs = sources()
    import fnmatch
    for pat in a.use_glob: a.use += [x for x in srcs if fnmatch.fnmatch(x, pat)]
    missing = [u for u in a.use if u not in srcs]
    if missing: sys.exit(f'not in the target: {missing}')
    chosen = []
    for rel in srcs:
        if rel in a.use: chosen.append((rel, 'clang', a.clang_dir / (rel.replace('/', '_') + '.o')))
        else: chosen.append((rel, 'nvcc', NVCC_OBJ_DIR / (rel + '.o')))
    owner = {}   # normalised kernel -> {compiler: [files]}
    for rel, comp, obj in chosen:
        for k in kernels(obj):
            owner.setdefault(k, {}).setdefault(comp, []).append(rel)
    collisions = {k: v for k, v in owner.items() if len(v) > 1}
    report = {'clang_files': sorted(a.use), 'kernels': len(owner), 'cross_compiler_collisions': len(collisions),
              'sample': [{'kernel': k[:140], **v} for k, v in list(collisions.items())[:8]]}
    (a.out / 'collision-check.json').write_text(json.dumps(report, indent=1))
    print(json.dumps({k: report[k] for k in ('kernels', 'cross_compiler_collisions')}))
    if collisions:
        for s in report['sample']: print('collision:', s)
        sys.exit(3)
    lib = a.out / 'libggml-cuda.so.0.9.11'
    link = [str(GPP), '-fPIC', '-shared', '-Wl,-soname,libggml-cuda.so.0', '-o', str(lib), *[str(o) for _, _, o in chosen],
            f'-Wl,-rpath,{BUILD}/bin', str(BUILD / 'bin/libggml-base.so.0.9.11'),
            f'{CUDA}/targets/x86_64-linux/lib/libcudart.so', f'{CUDA}/targets/x86_64-linux/lib/libcublas.so',
            f'{CUDA}/targets/x86_64-linux/lib/stubs/libcuda.so', f'{CUDA}/targets/x86_64-linux/lib/libcublasLt.so',
            f'{CUDA}/targets/x86_64-linux/lib/libculibos.a', '-ldl', '/usr/lib/x86_64-linux-gnu/librt.a', '-lcudadevrt', '-lcudart_static', '-lrt', '-lpthread', '-ldl',
            f'-L{CUDA}/targets/x86_64-linux/lib/stubs', f'-L{CUDA}/targets/x86_64-linux/lib']
    p = subprocess.run(link, capture_output=True, text=True)
    (a.out / 'link.log').write_text(p.stdout + p.stderr)
    print('link rc', p.returncode, lib)
    sys.exit(p.returncode)

if __name__ == '__main__':
    main()

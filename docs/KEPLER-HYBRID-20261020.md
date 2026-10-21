# Clang fixes and nvcc/Clang hybrid libraries: on-card test

20 October 2026 (Australia/Melbourne), host `uld-jvnhw22`, Tesla K40c. Follows
[KEPLER-CARD-COMPARISON-20261019.md](KEPLER-CARD-COMPARISON-20261019.md). Host Linux CUDA evidence about compilers, not
Haiku GPU support. Raw logs and tables: `results/t7610-20261020-hybrid/`; tools in `tools/kepler-static/`.

## Run

The user authorised the exact command `bash tools/kepler-static/run_card_hybrid.sh --execute results/t7610-20261020-hybrid`
(supervised runner: bounded at 150 minutes, drains child processes, then restarts and health-checks the service). Service
stopped 12:21 and restored at 14:04 (healthy). Useful work took until 13:13; the last 50 minutes were lost to a harness
mistake of mine: the five `llama-cli` text checks each hung until their 600 s timeout and wrote about 2.6 GB of spinner
output (deleted, not kept). The runner now does the text check through a short-lived `llama-server` and has a 120 to 300 s
bound; that fix is untested on the card. Card idle at 77 MiB before the run; K40c reached 75 degrees C at 745 MHz.

## The Clang attention problem: not fixed

| Clang build (all 133 sources) | Math flags | `FLASH_ATTN_EXT` |
|---|---|---|
| first run | `-ffast-math` plus flush-to-zero, approximate transcendentals, approximate divide and sqrt | 2415/2832 |
| `nofinite` | same plus `-fno-finite-math-only` | 2414/2832 |
| `nofast` | no `-ffast-math`, other settings kept | 2472/2832 |
| `ieee` | strict IEEE, nothing relaxed | built, **not yet tested** |

All failures are NaN outputs. Allowing infinities and NaNs (`nofinite`) changes nothing, so my first hypothesis was wrong
as the sole cause; dropping `-ffast-math` removes about 57 of the 417 failures, so the relaxed numerics play some part but
are not the whole story. The cause is still unknown (candidates: flush-to-zero or approximate divide in the softmax parts of
attention, or a genuine code-generation difference). Attention files cannot be split between compilers: vector, tile, MMA
and WMMA attention files all instantiate the same helper kernels (`flash_attn_combine_results`,
`flash_attn_mask_to_KV_max`), and my hybrid linker refuses such a mix (11 and 173 cross-compiler collisions for a
vector-only and a tile-only attempt). Next test: the `ieee` library, attention and softmax only (a few minutes of card time).

## Hybrid libraries

`tools/kepler-static/link_hybrid.py` relinks the deployed `nvcc` objects with chosen Clang objects (no recompiling). Before
linking it checks that no device kernel exists in objects of both compilers, because the linker would keep one host stub
and the CUDA runtime could launch the other compiler's kernel with no error. Rules found: the matrix-matrix block must be
swapped whole (`mmq.cu` plus all 21 `mmq-instance-*.cu`, since the `stream_k_fixup` kernels appear in all of them);
attention must be all-nvcc or all-Clang. The tested hybrids take **24 files from Clang**: `mmvq.cu`, `softmax.cu`, `mmq.cu` and the
21 MMQ instances, and the other 109 from `nvcc` (5,865 kernels, zero collisions, public API identical). Two bases:
`hybnofinite` and `hybnofast` (Clang objects from the corresponding math profile).

### Correctness (`test-backend-ops`, passed / total)

| Operation | nvcc | Clang nofinite | Clang nofast | hybnofinite | hybnofast |
|---|---|---|---|---|---|
| FLASH_ATTN_EXT | 2832/2832 | 2414/2832 | 2472/2832 | **2832/2832** | **2832/2832** |
| SOFT_MAX | 198/212 | 209/212 | 209/212 | 208/212 | 207/212 |
| MUL_MAT | 1094/1094 | 1094/1094 | 1094/1094 | 1094/1094 | 1094/1094 |
| MUL_MAT_ID | 764/764 | 764/764 | 764/764 | 764/764 | 764/764 |

The softmax failures are the known limitation of the deployed build (random test inputs: 196 in the earlier run, 198 here);
the Clang-containing builds fail fewer cases.

### Speed (production quantisation types q4_K, q5_K, q6_K, q8_0; ratio to the mean of two nvcc runs; the repeat of nvcc agrees within 0.1%)

| Operation | hybnofinite | hybnofast |
|---|---|---|
| MUL_MAT median ratio (28 cases) | **0.912**, 12 cases >10% faster, none slower | **0.912**, same |
| MUL_MAT_ID median ratio (48 cases) | **0.961**, 8 cases >10% faster, none slower | **0.966**, 7 faster, none slower |
| FLASH_ATTN_EXT (15 cases) | 1.000 (nvcc code) | 1.000 |

### End to end (`llama-bench`, Qwen3.5-9B Q4_K_XL, all layers on the card, tokens/s, mean of 3)

| Library | Prompt 512 | Generation 128 |
|---|---|---|
| nvcc | 135.32 | 9.57 |
| nvcc repeat | 135.29 | 9.57 |
| hybnofinite | 135.35 | 10.05 (+5.0%) |
| hybnofast | 135.34 | 10.07 (+5.2%) |
| full Clang (nofinite, attention wrong) | 135.10 | 10.11 |

Prompt processing is unchanged; token generation is about 5% faster, and the hybrid keeps nvcc attention so the main
correctness failure is avoided. Nearly all of the full-Clang generation gain is retained by the hybrid.

## Reading and limits

- The hybrid is a **working, correct-by-test improvement of about 5% in generation** for this dense model, built only from
  existing objects. It is not deployed: the service still uses the nvcc library. The hybrid libraries were in
  `~/kepler-llvm-eval/hybrid-*`; that workspace was removed on 21 October 2026 (see "Workspace removed" below).
- **Not verified:** the greedy-text check (the harness step failed, see Run), the 35B production MoE model (the speed-up
  for MoE token generation may differ), kernels other than the tested operations (they come from nvcc or passed the
  first run), long runs, and a second repeat of the whole run.
- The Clang attention failure is a real defect of that build until explained; the hybrid sidesteps it.

## Final window (20 October 2026, 14:36-15:27): IEEE, greedy text, production model

Two supervised windows, service restored healthy each time (`results/t7610-20261020-final`, `-final2`). The first
window's text and 35B results are **invalid**: my `text_check` killed only the `numactl` wrapper, so the first 9B
server stayed on port 18181 and every later "text" result came from it, and the 35B server could not start. The helper
now runs the server in its own process group, kills the group and skips a step if the port is busy. Valid data are in
`-final2` (it also repeated the correctness tests, because an empty `HYBRID_CORR_LIBS` falls back to the default).

**IEEE (strict, no fast-math flags).** Pure Clang still fails attention: FLASH_ATTN_EXT 2411/2832 (nofinite 2419,
nofast 2471). SOFT_MAX 210/212 (nvcc 192-198/212, so nvcc itself fails 14-20 cases). MUL_MAT 1094/1094 and
MUL_MAT_ID 764/764 for every Clang and hybrid build. The hybrid IEEE library passes FLASH_ATTN_EXT 2832/2832.
Conclusion: the attention failure is **not** a math flag; it is a code-generation difference, cause not found.

**Greedy text, 9B** (2 prompts, 64 tokens, temperature 0): hybnofast, hybnofinite and hybieee are identical to nvcc on
both prompts. Pure-Clang IEEE matches on prompt 1 and differs on prompt 2 (consistent with its attention errors).

**Greedy text, 35B production configuration:** prompt 2 is identical for nvcc, ieee, hybnofast and hybieee. On prompt 1
hybnofast and hybieee start identically to nvcc and diverge at character 91 (different but sensible continuation);
pure-Clang ieee diverges earlier. Small floating-point differences flip a near-tie token; this is expected between
compilers and is not evidence of a defect, but it means the hybrid is not bit-identical.

**35B speed, one card** (`-ncmoe 30 -b 2048 -ub 2048 -t 6 -fa 1`, 2 repeats, tokens/s):

| Library | Prompt (512) | Generation (64) |
|---|---|---|
| nvcc | 88.11 | 13.34 |
| hybnofast | 89.97 (+2.1%) | 14.07 (+5.5%) |
| hybieee | 89.39 (+1.5%) | 13.54 (+1.5%) |
| nvcc repeat | 87.77 | 12.60 |

The two nvcc runs differ by 5.5% in generation, as much as the hybrid gain, so on the production model the gain is
**within noise** (at most about 0-5%). The 9B gain of about 5% stands as measured.

## Decision

Do not deploy a hybrid for production: gain is small and unproven on the 35B model, text is not bit-identical, and it adds
build and link-collision risk. Keep nvcc. The hybrid remains a documented option.

## Possible further work (not planned)

Find the Clang attention cause (diff the instructions of one failing case; test adding warp barriers). No web source
describes this failure; the warp-synchronous-code explanation is only a hypothesis.

## Workspace removed (21 October 2026)

The user deleted `~/kepler-llvm-eval` (15 GB) after the decision to keep nvcc. Before deletion: no process, service
unit, environment file, crontab or symbolic link used it; the service loads only `~/llm-server/llama.cpp/build/bin`
(`libggml-cuda.so.0.9.11`, SHA-256 `ac270eeb5640cc36...`, the nvcc build) and was healthy before and after.

Removed: the LLVM 23.1.3 toolchain (12 GB unpacked, 1.9 GB archive), the Clang libraries (`clang-ggml-cuda`,
`-nofinite`, `-nofast`, `-ieee`), the hybrid libraries (`hybrid-*`), the `lib-*` test directories and `kernel-cache`.
Kept: the text results (`analysis.md`, `subset*.md`, the build and link logs `*.txt`, `out1-3.txt`) are in
`results/kepler-llvm-eval-summary/`. Card results stay under `results/t7610-2026101*/` and `results/t7610-20261020-*`.

To rebuild (CPU only, no card; needs the deployed nvcc objects in
`~/llm-server/llama.cpp/build/ggml/src/ggml-cuda/CMakeFiles/ggml-cuda.dir`, which `link_hybrid.py` reads):

1. Download `LLVM-23.1.3-Linux-X64.tar.xz` from the `llvm/llvm-project` GitHub release `llvmorg-23.1.3` and check
   SHA-256 `ca9fe385a5d9e2d88132dc0e23a00e9f87f38fa75f67207b5e457d208e71d013` (2,016,524,848 bytes). Unpack it to
   `~/kepler-llvm-eval/llvm/`.
2. Build a Clang library for each math profile needed (about four minutes each on 10 jobs):
   `python3 tools/kepler-static/build_clang_ggml_cuda.py --clang-bin ~/kepler-llvm-eval/llvm/LLVM-23.1.3-Linux-X64/bin --math nofast --out ~/kepler-llvm-eval/clang-ggml-cuda-nofast`
   (profiles: `ffast`, `nofinite`, `nofast`, `ieee`).
3. Link a hybrid with the tested 24 Clang files:
   `python3 tools/kepler-static/link_hybrid.py --clang-dir ~/kepler-llvm-eval/clang-ggml-cuda-nofast --out ~/kepler-llvm-eval/hybrid-nofast --use mmvq.cu --use softmax.cu --use mmq.cu --use-glob 'template-instances/mmq-instance-*.cu'`.
   It must report `"cross_compiler_collisions": 0`. `kernel-cache` is recreated by the script.
4. Any card test goes through `tools/kepler-static/run_card_hybrid.sh --execute NEW_DIR` (supervised; it pauses and
   restores the service). Its `lib-*` directories are recreated from the deployed libraries.

The rebuilt files will differ in timestamps; compare kernel counts (5,865 for the hybrid) and test results, not hashes.

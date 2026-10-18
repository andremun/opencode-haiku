# Kepler (sm_35): Clang 23 against nvcc 11.4, static comparison

18 October 2026 (Australia/Melbourne), host `uld-jvnhw22`. **GPU-free:** compile-only, `ptxas`, `cuobjdump`.
No card, driver, service or CUDA symlink was touched; nothing was loaded or executed on a GPU. This addresses
the Stage 1 and Stage 2 compile gates of `kepler_llvm_llamacpp_research_plan.md` and the host findings in
[HOST-CAPABILITIES-20261018.md](HOST-CAPABILITIES-20261018.md). Evidence: `results/t7610-20261018-kepler-static/`;
harness: `tools/kepler-static/`. Static results say nothing about speed or numerical correctness.

## Setup

- LLVM 23.1.3 prebuilt release `LLVM-23.1.3-Linux-X64.tar.xz` (official `llvm/llvm-project` release of
  6 Oct 2026, 2,016,524,848 bytes), SHA-256 `ca9fe385a5d9e2d88132dc0e23a00e9f87f38fa75f67207b5e457d208e71d013`
  (matches the digest GitHub publishes for the asset). Unpacked under `~/kepler-llvm-eval` (outside every
  repository, 12 GiB); runs on this glibc 2.35 host without installation.
- Reference: nvcc 11.4.152 with the deployed flags (`-O3 -std=c++17 compute_35/sm_35 -use_fast_math -extended-lambda`,
  host `g++-10`), sources from the deployed, read-only llama.cpp b8861 checkout.
- Clang: `--cuda-gpu-arch=sm_35 --cuda-device-only -O3 -std=c++17 -ffast-math`, `--gcc-install-dir` GCC 11
  (the default GCC 12 install lacks libstdc++ headers here), CUDA 11.4 headers. `ptxas` 11.4 produces the machine
  code (SASS) for both.

## Gate results

| Check | Result |
|---|---|
| Clang accepts `sm_35` with the CUDA 11.4 headers | **yes** |
| PTX version | Clang selects PTX ISA **7.4** by itself, which `ptxas` 11.4 accepts; no pinning needed (my earlier worry was unfounded) |
| Vector-add kernel | accepted; 21 SASS instructions from both compilers |
| `ggml-cuda` kernel files | **66 of 66 compile** with both compilers and `ptxas`; 1,718 kernels |
| Needed workaround | `softmax.cu` includes CUDA 11.4 cooperative groups, which refers to `__match_any_sync`; Clang's wrapper does not declare it for `sm_35`. A declarations-only shim (`clang_cg_shim.h`) fixes it; it is never instantiated for `sm_35` |

## Size, registers, spills (all 66 files, 1,706 kernels matched by demangled name)

| Measure | nvcc 11.4 | Clang 23.1.3 |
|---|---|---|
| Total machine-code instructions | 1,148,769 | 1,053,698 (**-8.3%**) |
| Median registers per kernel (ratio) | 1.00 | 1.00 (higher in 590, lower in 700, equal in 416; 137 grow by 8 or more) |
| Maximum registers | 255 | 255 |
| Kernels that spill | 28 | **64** |
| Spill bytes (stores plus loads) | 46,712 | **60,784 (+30%)** |

By kernel family (the quantisation types the production model uses; occupancy proxy = threads per SM allowed by
registers alone, ignoring shared memory and block size):

| Family | Kernels | Median regs nvcc / Clang | Spilling nvcc / Clang | Occupancy proxy nvcc / Clang |
|---|---|---|---|---|
| `mul_mat_vec_q` (Q8_0, Q4_K, Q5_K, Q6_K) | 44 | 98 / **92** | 0 / 0 | 769 / **848** |
| `mul_mat_q` (Q8_0, Q4_K, Q6_K) | 96 | 42 / **66** | 26 / **44** | 1296 / 1281 |
| `flash_attn_ext_vec` | 24 | 218 / 226 | 0 / 0 | 616 / 604 |
| `flash_attn_tile` | 34 | 128 / **161** | 1 / **6** | 494 / **449** |
| `mul_mat_vec_f` (f16/f32) | 352 | 39 / **30** | 0 / 0 | 1558 / **1750** |

Largest Clang register increases: `mul_mat_vec_q<type 40,...>` 138 to 250 and `flash_attn_ext_vec<...q4_0>` 145 to 244.
With Clang's flush-to-zero, approximate transcendentals and approximate divide/sqrt set to mirror `-use_fast_math`
(16 representative files), the family numbers are unchanged and total size stays at 0.919 of nvcc, so the result
does not hinge on that flag difference.

## Reading

- Clang is a **viable Kepler compiler for these kernels**: complete coverage, valid PTX, accepted by `ptxas`.
- It is **not a clear performance candidate**. Token-generation kernels (`mul_mat_vec_q`, f16/f32 mat-vec) look slightly
  better; prompt-processing kernels (`mul_mat_q`) and the tile attention kernels look worse (more registers, more spills),
  and spills more than double overall. A runtime effect would likely be small and could be negative for prompt processing.
- Real benefits are elsewhere: about 8% less machine code, 2.5x to 3.5x faster compilation of the larger files here
  (timings under low priority and a concurrent VM benchmark, so approximate), and independence from `nvcc`'s host-compiler
  limit (these builds used GCC 11 headers, `nvcc` was run with GCC 10).
- For the Haiku backend this supports a route where kernels are compiled offline with Clang and `ptxas` and shipped as
  `sm_35` cubins; `ptxas` stays a proprietary Linux tool.

## Limits

Static only. Not measured: speed, numerical equality, correct execution, real occupancy (shared memory, block sizes),
which kernels the production run actually launches (inferred from quantisation types), and `ggml-cuda.cu` itself
(needs cuBLAS and NCCL headers; not compiled). Kernel type 40 is an enum value I did not identify. Compile times were taken
while a VM benchmark ran. A runtime comparison needs a card, which requires your decision (see the host report).

## Addendum 19 October 2026: full Clang library built; on-card run prepared, not executed

- **The whole `libggml-cuda` builds with Clang.** All 133 sources of the deployed target (61 top-level and 72 template
  instances) compile as host plus device code for `sm_35` with Clang 23.1.3 (flush-to-zero, approximate transcendentals,
  approximate divide and square root set to mirror `-use_fast_math`), link with the deployed link line, and the result
  (`tools/kepler-static/build_clang_ggml_cuda.py`, about four minutes on 10 jobs) is 55.7 MB against 99.0 MB for the
  nvcc build. Both embed only `sm_35` cubins; the public `ggml_*` API symbols are identical, and the dynamic loader
  resolves it cleanly in place of the deployed library (all deployed binaries use `RUNPATH`, so a private
  `LD_LIBRARY_PATH` directory with only `libggml-cuda.so.0` replaced takes precedence). Nothing was executed on a GPU.
- **On-card comparison: not run.** At your instruction I prepared `tools/kepler-static/run_card_comparison.sh`: it pauses
  `llama-server-one.service` (user unit; nothing was connected and the slot was idle when I checked), uses only the card
  named in the unit, runs `test-backend-ops` correctness and performance per operation and `llama-bench` on
  Qwen3.5-9B Q4_K_XL (fully on the card) for both libraries in A-B-A order, and restarts and health-checks the service
  via an exit trap and a 150-minute dead-man timer. The auto-mode classifier blocked the step that stops the service and
  queries the card ("interferes with workloads"), so nothing was paused and no GPU was accessed. See the status notes in
  the session report for how to proceed.
- **Risks to accept before running:** a faulty Clang kernel could hang the Kepler card (needs a driver reset or reboot,
  which cannot be done without root); the production model needs a few minutes to reload after the pause; the test window
  is roughly 40 to 90 minutes.

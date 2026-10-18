# Host capabilities (side evaluation)

18 October 2026 (Australia/Melbourne), host `uld-jvnhw22` (Dell Precision T7610). Read from files,
version commands and `systemctl` status only. **No GPU was accessed** (no `nvidia-smi`, no benchmark,
no PCI reads beyond existing records), no service was started, stopped or reconfigured, no sudo.
Purpose: answer the open questions of `kepler_llvm_llamacpp_research_plan.md` and show what the host
can support. A CPU/host inventory is not GPU evidence.

## Machine

| Item | Value |
|---|---|
| OS / kernel | Ubuntu 22.04.5 LTS, 6.8.0-138-generic |
| CPU | 2 x Xeon E5-2620 v2 (Ivy Bridge): 24 threads, 2.1 GHz (max 2.6), 30 MiB L3 per socket, **no AVX2, no FMA**, VT-x |
| Memory | 62 GiB, 2 NUMA nodes of about 32 GiB; 34 GiB available, 49 GiB buff/cache at the time |
| Disk | 463 GiB root, **210 GiB free** |
| Virtualisation | `/dev/kvm` present (group `kvm`, ACL for the user), QEMU 6.2.0; 75 IOMMU groups |
| Load | about 2.2 (production model plus the 2-vCPU Haiku VM benchmark running) |

## Toolchains

| Tool | State |
|---|---|
| System GCC | 11.4.0 (also gcc-12 installed); local GCC **10.5.0** under `~/.local/opt/gcc10` (used for the CUDA build) |
| CMake | 4.4.4 (user install); GNU Make 4.3; **no ninja, no ccache** |
| Clang / LLVM | **not installed** (only the `libllvm15` runtime library); no `clang`, `llc`, `opt`, `lld` |
| CUDA toolkit | **11.4** (`nvcc` 11.4.152) at `/usr/local/cuda-11.4`; `ptxas`, `cuobjdump`, `nvdisasm`, `nvlink`, `nvprof` present; no Nsight tools seen |
| NVIDIA driver | 470.256.02 (from `/proc/driver/nvidia/version`; kernel module built with GCC 12.3) |
| Python | 3.10.12; no Node, Bun, Zig, Rust or Go on PATH (the OpenCode port keeps its own toolchains under `cache/build-tools`) |

## Deployed llama.cpp and service

- llama.cpp b8861, commit `cf8b0dbda9ac0eac30ee33f87bc6702ead1c4664` (2026-04-20) plus two local
  patches (`kepler-sm35-ggml-cuda`, `reasoning-budget-rearm`); working tree differs in 3 files
  (the two patches and `tests/test-reasoning-budget.cpp`).
- Build: CUDA architecture 35, `nvcc` 11.4 with host compiler `g++-10`, flash attention on,
  CUDA graphs on, NCCL on, `GGML_NATIVE=ON`, OpenMP on, GCC 10.5 (`~/llm-server/docs/INSTALLED_BUILD.md`).
- Running service: **`llama-server-one.service`** is active (one model on the K40c at
  `0000:03:00.0` only); `llama-server.service` (dual-card) is inactive. The process runs
  Qwen3.6-35B-A3B UD-Q4_K_XL with `--n-cpu-moe 30`, context 81920, 6 threads.
- The second K40c (`0000:04:00.0`) is the development card, reserved for passthrough work.

## Answers to the plan's open questions

1. Versions: `nvcc` 11.4.152 (not 11.8); `clang` absent; driver 470.256.02. `nvidia-smi` was not run.
2. Patched commit and build configuration: above.
3. Model and offload flags: Qwen3.6-35B-A3B UD-Q4_K_XL, `--n-cpu-moe 30` for the running unit;
   GGUF hash recorded in the `llm-server` documents (not re-hashed here).
4. Build-only modern LLVM: **none available**.

## What this means for the plan

- **PTX version limit.** CUDA 11.4's `ptxas` accepts PTX only up to the ISA of that release
  (to my knowledge 7.4; confirm with `ptxas` and NVIDIA's PTX table). A recent Clang defaults to a much
  newer PTX version, so Stage 1 must pin it explicitly and treat a `ptxas` rejection as a finding.
  The plan assumed CUDA 11.8; the host has 11.4.
- **Much of the work needs no GPU.** `ptxas`, `cuobjdump` and `nvdisasm` run on the CPU, so compiling the
  `ggml-cuda` kernels with `nvcc` and with Clang to PTX and `sm_35` cubins, then comparing register counts
  (`ptxas -v`), spill, code size and instruction mix, is possible without touching a card. That static
  comparison would show early whether a Clang build can differ meaningfully from `nvcc`'s.
- **Executing on a K40c is blocked by design.** `0000:03:00.0` serves the production model and
  `0000:04:00.0` is reserved for passthrough. Any run (baseline benchmark, Stage 1 kernel) needs a user
  decision: a scheduled stop of the service, or re-binding the development card, both root-level steps.
  I do not perform them.
- **Resources for a build-only LLVM are adequate** (210 GiB disk, 24 threads, GCC 11/12), but there is no
  ninja. Options: a prebuilt LLVM release unpacked in user space (needs a download approval) or a source build
  with Make (slower, tens of GiB).
- **Profiling tools.** `nvprof` is available, which suits a Kepler profile before any migration.
- **CPU side.** AVX only, no AVX2/FMA: the CPU-expert path (`--n-cpu-moe`) is limited to Ivy Bridge instruction
  sets, which matches the Haiku guest. Our Haiku-guest result that OpenMP slowed decoding (2 vCPU) is
  not evidence for the host's 6-thread, two-NUMA-node case; testing it needs an idle window.

## Not assessed

GPU health, VRAM, clocks, power and the actual card state (no GPU access); the NUMA placement used by the
service; wall power; the model files' integrity; network.

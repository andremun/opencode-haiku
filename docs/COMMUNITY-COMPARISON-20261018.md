# Comparison with the community llama.cpp work on Haiku

18 to 19 October 2026 (Australia/Melbourne). Sources read: the HaikuPorts recipe and patchset
(`dev-cpp/llama-cpp`, build tag b4889) and the gist patch from the Haiku Insider guide (both saved under
`results/t7610-20261018-community/`), plus the forum and article pages (summaries only, no measured data in
them). Experiments ran in the cardless KVM Haiku VM (2 vCPU, E5-2620 v2) on llama.cpp **b8861**, not b4889.
A CPU/cardless result is not GPU evidence.

## Patches: community against ours

The community patch (Haiku developer `3dEyes`, Feb 2025, four hunks) and ours do the same jobs:
`<limits.h>` for Haiku, link `network` for the server and RPC. Ours covers the newer source layout and more
(vendored HTTP library, XDG cache path, audio code); one community hunk (undefine `_POSIX_MEMLOCK_RANGE` in
`llama-mmap.cpp`) is not in ours. b8861 already has a Haiku case at that place and builds without it, so it looks
superseded. Our 8-file patch is therefore a superset for b8861.

## Build flags: the HaikuPorts recipe

The recipe sets `-DGGML_NATIVE=OFF` and nothing about instruction sets; OpenMP via `libgomp`; mimalloc linked
in; RPC on. **With `GGML_NATIVE=OFF`, CMake turns AVX2, FMA, BMI2, F16C and AVX on by default** (confirmed in the
cache of a build with exactly those flags: `-mavx -mavx2 -mbmi2 -mf16c -mfma -msse4.2`). That build links and its
tests pass, but **`llama-bench` crashes at start-up on this Ivy Bridge CPU**: Haiku's crash report shows an
"Invalid opcode exception" in `ggml_cpu_init`, at `vfmadd213ss` (an FMA3 instruction, Haswell and later). The
packaged recipe is b4889; the same default is long-standing, but I verified it on b8861 only, so for b4889 this
is likely, not proven. Effect: a stock package of this kind should not run on pre-Haswell x86_64 CPUs.

## Measurements (Qwen3 1.7B Q4_K_M, `-t 2`, 512-token prompt, 64-token decode, tokens/s, mean of 3)

| Build | Prompt 128/32 | Prompt 512/128 | Decode 128/32 | Decode 512/128 |
|---|---|---|---|---|
| baseline (SSE2, OpenMP off), 1 repetition | 1.45 | 1.43 | 1.15 | 1.15 |
| ivybridge (our default) | 10.36 | 11.28 | 6.56 | 6.91 |
| ivybridge + mimalloc | 10.88 | 11.25 | 6.83 | 6.84 |
| "community-like": generic flags with AVX/F16C/SSE4.2, AVX2/FMA/BMI2 off, **OpenMP on**, mimalloc | 10.15 | 10.98 | 4.13 | 4.13 |
| runtime variants (all CPU variants, picks one at start) | 10.69 | 10.95 | 6.39 | 6.33 |
| recipe flags exactly | crashes (invalid opcode, FMA) | | | |

Findings:

- **mimalloc**: no effect worth keeping here (within run-to-run spread).
- **OpenMP**: again about 40% slower decode on a 2-vCPU guest (4.1 against 6.6 to 6.9), no prompt gain.
- **Runtime CPU variants** (`GGML_BACKEND_DL=ON`, `GGML_CPU_ALL_VARIANTS=ON`) give near-best speed from one portable
  build: it chose `libggml-cpu-ivybridge.so` by itself, decode about 5% below the hand-tuned build.
- **Haiku gap found:** ggml's `get_executable_path()` has implementations for macOS, Linux, FreeBSD and Windows but not
  Haiku, so by default **no runtime backend is found** (every start prints "search path does not exist" and the CPU
  backend is missing). Setting `-DGGML_BACKEND_DIR=<absolute lib dir>` at build time works around it (that is what
  made the variants build work). A small upstream change using Haiku's image-info API would remove the need for it.

## Suggestions (not acted on beyond this repository)

1. Package the multi-variant build with `GGML_BACKEND_DIR` set to the package's library directory; it runs on any x86_64
   Haiku machine and still gets AVX or AVX2 speed where available. If a single static CPU target is preferred, pin the
   instruction flags explicitly (`GGML_AVX2/FMA/BMI2` off for a portable package).
2. Make OpenMP optional and measure it on the target machine before enabling.
3. Offer the Haiku `get_executable_path()` and the portability hunks upstream; our patch is the newer reference.
4. Our own default stays Ivy Bridge with OpenMP off; the variants build is a viable alternative (decode about 5% lower)
   when one build must serve different CPUs.

## Caveats

b8861 not b4889; one small model; 2 vCPUs; one CPU family (no AVX2 hardware here, so the speed of the AVX2 and later
variants was not measured); the baseline row is a single repetition and its run overlapped host compile jobs (the other
rows did not, except possibly the tail of the baseline run); the forum and article pages were read through a
summarising tool and contain no numbers to compare against; posting any of this to the community is your decision
(nothing was posted).

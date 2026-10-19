# On-card comparison: nvcc 11.4 build against Clang 23 build of `libggml-cuda` (Tesla K40c)

20 October 2026 (Australia/Melbourne), host `uld-jvnhw22`. **First GPU run of this work.** It is host Linux CUDA
evidence about compilers; it says nothing about Haiku GPU support. Raw logs, telemetry and the analysis are in
`results/t7610-20261019-card-comparison/`; analysis tool `tools/kepler-static/analyze_card.py`.

## What ran

- The user authorised the exact command `bash tools/kepler-static/run_card_comparison.sh results/t7610-20261019-card-comparison`.
  Window 08:56 to 10:40 (about 1 h 45 min): `llama-server-one.service` was stopped (nothing connected, slot idle),
  the card showed 77 MiB in use, the tests ran on that one card (UUID from the unit, NUMA node 0), then the service was
  started again and was healthy about 50 s later (new `MainPID` 937821; the 35B model reloaded). The failsafe timer was
  cleared; no test process was left. K40c telemetry: 62 to 73 degrees C, 745 MHz (max 875) under load. The card at
  04:00.0 was never touched.
- **Provenance of the runner:** this run executed the version committed in `784ef26`. While it ran, a later commit
  (`7970e38`, from another session) was pulled in; it replaced the runner with a supervised version that needs
  `--execute NEW_DIR`. The results below come from the earlier version; the repository now carries the newer one.
- Same test binaries (`test-backend-ops`, `llama-bench`) from the deployed build for both runs; only `libggml-cuda.so.0`
  differs (deployed nvcc 11.4 build, against the Clang 23.1.3 build of the same source made by
  `tools/kepler-static/build_clang_ggml_cuda.py`, with flush-to-zero, approximate transcendentals and approximate
  divide/sqrt, plus `-ffast-math`). Performance runs are A-B-A (nvcc, Clang, nvcc again); the repeat of nvcc agrees
  with the first within 0.1% (median drift 1.000), so thermal and clock drift were small.

## Correctness (`test-backend-ops` against the CPU backend)

| Operation | nvcc | Clang |
|---|---|---|
| MUL_MAT | 1094/1094 | 1094/1094 |
| MUL_MAT_ID | 764/764 | 764/764 |
| **FLASH_ATTN_EXT** | 2832/2832 | **2415/2832** (417 failures, **all NaN output**) |
| SOFT_MAX | 196/212 | 211/212 (the nvcc failures are the known softmax limitation, error up to 7.6e-4; Clang's worst is 3.3e-5) |
| RMS_NORM, ROPE, GET_ROWS, CPY, SCALE, ADD, MUL, ARGSORT, TOP_K, SUM_ROWS, CONCAT | all pass | all pass, same counts |
| UNARY, GLU | 0/0 | 0/0 (the filter selected no cases, so these were **not tested**) |

The 417 attention failures cover every head size seen (40, 64, 72, 80, 96, 128, 256), all KV types, with and without
mask and sinks: attention is broadly broken in the Clang build, so it is not usable as is. **Likely cause, untested:**
`-ffast-math` lets Clang assume no infinities or NaNs, while attention kernels start from `-INFINITY`; `nvcc`'s
`-use_fast_math` does not make that assumption. Test with `-fno-finite-math-only` (or finer flags) before drawing
conclusions about the compiler.

## Kernel speed (`test-backend-ops perf`; ratio = Clang time / mean of the two nvcc runs, lower is faster)

| Operation | Cases | Median ratio | Clang >10% slower | Clang >10% faster |
|---|---|---|---|---|
| MUL_MAT | 177 | 1.000 (geometric mean 1.28, skewed by the IQ kernels below) | 53 | 21 |
| MUL_MAT_ID | 116 | 0.980 | 29 | 24 |
| FLASH_ATTN_EXT | 15 | 1.052 (and incorrect, see above) | 3 | 0 |

By type, median Clang/nvcc for matrix-vector (`n=1`, token generation) and matrix-matrix (`n>1`, prompt processing):
q4_K 0.97 and 0.85; q5_K 0.95 and 0.89; q6_K 0.93 and 0.95; q8_0 0.88 and 0.91 (MUL_MAT); the same types in MUL_MAT_ID are
0.88 to 1.07. So **for the production quantisation types the Clang kernels are about 5 to 15% faster at the median**,
which the static register counts did not predict (static counts were a poor guide). The slowest cases are the
i-quant kernels (`iq1_s`, `iq1_m`, `iq2_s`): about **4.6 to 5.0 times slower**; these types are not in the production model.

## End to end (`llama-bench`, Qwen3.5-9B Q4_K_XL, all layers on the card, flash attention on, tokens/s)

| Run | Prompt 512 | Generation 128 |
|---|---|---|
| nvcc | 135.29 | 9.56 |
| Clang | 135.01 | 10.09 (+5.6%) |
| nvcc (repeat) | 135.26 | 9.55 |

`llama-bench` does not check the output, and the Clang attention kernels return NaN for some shapes, so the generation
gain is **not validated**. The 35B production model was not run.

## Reading

- The Clang library builds completely (133 of 133 sources), loads in place of the deployed library, and passes everything
  except flash attention. It is **not acceptable until the NaN failures are explained and fixed**.
- If they come from the fast-math setting, the rest of the picture is promising: faster production quantisation kernels
  (and better softmax numerics), possibly a few percent end to end. The IQ-type slowdown would matter only if such
  quantisations are ever used.
- Static register and spill counts did not predict the runtime ordering.

## Limits

One card, one model for the end-to-end run, no output verification beyond `test-backend-ops`; unary and GLU operations
untested; no repeat of the whole run; perf cases are from the test suite's shapes, not the production model's. A faulty
kernel could have hung the card; it did not.

## Next steps (each needs card/service authorisation under the supervised runner)

1. Rebuild the Clang library with `-fno-finite-math-only` (CPU-only, about four minutes) into a new directory.
2. Run only `FLASH_ATTN_EXT` and `SOFT_MAX` correctness (a few minutes of card time) and the A-B-A end-to-end run, now with
   an output check (greedy tokens or perplexity compared with the nvcc build).
3. Fix the op filter for `UNARY` and `GLU`, and add the IQ types to the decision.
4. Only then consider a short run with the production model.

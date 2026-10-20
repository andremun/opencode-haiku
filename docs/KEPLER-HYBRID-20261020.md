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
  existing objects. It is not deployed: the service still uses the nvcc library; hybrid libraries are in
  `~/kepler-llvm-eval/hybrid-*`.
- **Not verified:** the greedy-text check (the harness step failed, see Run), the 35B production MoE model (the speed-up
  for MoE token generation may differ), kernels other than the tested operations (they come from nvcc or passed the
  first run), long runs, and a second repeat of the whole run.
- The Clang attention failure is a real defect of that build until explained; the hybrid sidesteps it.

## Next steps (each needs the user to allow the exact command)

1. Short window: `HYBRID_CORR_LIBS='ieee nvcc' HYBRID_OPS='FLASH_ATTN_EXT SOFT_MAX' HYBRID_PERF=0 HYBRID_E2E=0 HYBRID_TEXT_LIBS='' bash tools/kepler-static/run_card_hybrid.sh --execute NEW_DIR` (about 5 minutes).
2. If `ieee` passes attention, find which relaxed setting breaks it (build variants one flag at a time, CPU-only) and then
   consider taking attention from Clang too. If it fails, it is a code-generation difference to investigate or report.
3. A window with the text check through the server and with the production 35B model, before any decision to deploy.

## Correctness (`test-backend-ops` against the CPU backend)

| operation | nvcc | nofinite | nofast | hybnofinite | hybnofast |
|---|---|---|---|---|---|
| FLASH_ATTN_EXT | 2832/2832 | 2414/2832 | 2472/2832 | 2832/2832 | 2832/2832 |
| SOFT_MAX | 198/212 | 209/212 | 209/212 | 208/212 | 207/212 |
| MUL_MAT | 1094/1094 | 1094/1094 | 1094/1094 | 1094/1094 | 1094/1094 |
| MUL_MAT_ID | 764/764 | 764/764 | 764/764 | 764/764 | 764/764 |

## Kernel speed (production quantisation types; ratio = library / mean of the two nvcc runs, lower is faster)

| operation | library | cases | median ratio | geometric mean | >10% slower | >10% faster | nvcc drift |
|---|---|---|---|---|---|---|---|
| MUL_MAT | nofinite | 28 | 0.911 | 0.906 | 0 | 12 | 1.000 |
| MUL_MAT | nofast | 28 | 0.912 | 0.906 | 0 | 12 | 1.000 |
| MUL_MAT | hybnofinite | 28 | 0.912 | 0.904 | 0 | 12 | 1.000 |
| MUL_MAT | hybnofast | 28 | 0.912 | 0.904 | 0 | 12 | 1.000 |
| MUL_MAT_ID | hybnofinite | 48 | 0.961 | 0.953 | 0 | 8 | 1.000 |
| MUL_MAT_ID | hybnofast | 48 | 0.966 | 0.956 | 0 | 7 | 1.000 |
| FLASH_ATTN_EXT | nofinite | 15 | 1.052 | 1.031 | 3 | 0 | 0.999 |
| FLASH_ATTN_EXT | nofast | 15 | 1.049 | 1.028 | 3 | 0 | 0.999 |
| FLASH_ATTN_EXT | hybnofinite | 15 | 1.000 | 1.000 | 0 | 0 | 0.999 |
| FLASH_ATTN_EXT | hybnofast | 15 | 1.000 | 1.000 | 0 | 0 | 0.999 |

## End to end: llama-bench, Qwen3.5-9B Q4_K_XL fully on the card (tokens/s, mean of 3)

| library | prompt 512 | generation 128 |
|---|---|---|
| nvcc | 135.32 (sd 0.03) | 9.57 (sd 0.00) |
| nofinite | 135.10 (sd 0.02) | 10.11 (sd 0.00) |
| nofast | 135.11 (sd 0.01) | 10.17 (sd 0.00) |
| hybnofinite | 135.35 (sd 0.01) | 10.05 (sd 0.00) |
| hybnofast | 135.34 (sd 0.04) | 10.07 (sd 0.00) |
| nvcc2 | 135.29 (sd 0.04) | 9.57 (sd 0.00) |

## Greedy text for the same prompt (48 tokens, seed 1, through llama-server) against the nvcc build

| library | identical to nvcc | note |
|---|---|---|
| nvcc | n/a | |
| nofinite | n/a | |
| nofast | n/a | |
| hybnofinite | n/a | |
| hybnofast | n/a | |

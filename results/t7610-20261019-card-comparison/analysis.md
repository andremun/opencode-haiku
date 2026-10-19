## Correctness (test-backend-ops vs CPU backend)

| operation | nvcc | Clang |
|---|---|---|
| MUL_MAT | 1094/1094 | 1094/1094 |
| MUL_MAT_ID | 764/764 | 764/764 |
| FLASH_ATTN_EXT | 2832/2832 | 2415/2832 |
| SOFT_MAX | 196/212 | 211/212 |
| RMS_NORM | 21/21 | 21/21 |
| ROPE | 268/268 | 268/268 |
| GET_ROWS | 47/47 | 47/47 |
| CPY | 136/136 | 136/136 |
| SCALE | 4/4 | 4/4 |
| ADD | 99/99 | 99/99 |
| MUL | 91/91 | 91/91 |
| UNARY | 0/0 | 0/0 |
| GLU | 0/0 | 0/0 |
| ARGSORT | 46/46 | 46/46 |
| TOP_K | 170/170 | 170/170 |
| SUM_ROWS | 4/4 | 4/4 |
| CONCAT | 16/16 | 16/16 |

## Kernel performance (test-backend-ops perf, us/run; ratio = Clang / mean(nvcc, nvcc2), lower is faster)

| operation | cases | median ratio | geometric mean | Clang >10% slower | Clang >10% faster | nvcc2/nvcc drift (median) |
|---|---|---|---|---|---|---|
| MUL_MAT | 177 | 1.000 | 1.282 | 53 | 21 | 1.000 |
| MUL_MAT_ID | 116 | 0.980 | 1.110 | 29 | 24 | 1.001 |
| FLASH_ATTN_EXT | 15 | 1.052 | 1.031 | 3 | 0 | 1.000 |

### By quantisation type and batch (MUL_MAT and MUL_MAT_ID; n = 1 is token generation)

| op | type_a | n | cases | median ratio |
|---|---|---|---|---|
| MUL_MAT | f16 | n=1 | 3 | 1.000 |
| MUL_MAT | f16 | n>1 | 6 | 1.001 |
| MUL_MAT | f32 | n=1 | 1 | 1.001 |
| MUL_MAT | f32 | n>1 | 6 | 1.001 |
| MUL_MAT | q4_0 | n=1 | 1 | 1.016 |
| MUL_MAT | q4_0 | n>1 | 6 | 0.949 |
| MUL_MAT | q4_K | n=1 | 1 | 0.968 |
| MUL_MAT | q4_K | n>1 | 6 | 0.852 |
| MUL_MAT | q5_K | n=1 | 1 | 0.953 |
| MUL_MAT | q5_K | n>1 | 6 | 0.889 |
| MUL_MAT | q6_K | n=1 | 1 | 0.931 |
| MUL_MAT | q6_K | n>1 | 6 | 0.948 |
| MUL_MAT | q8_0 | n=1 | 1 | 0.881 |
| MUL_MAT | q8_0 | n>1 | 6 | 0.905 |
| MUL_MAT_ID | f16 | n=1 | 2 | 0.878 |
| MUL_MAT_ID | f16 | n>1 | 14 | 0.973 |
| MUL_MAT_ID | f32 | n=1 | 2 | 0.915 |
| MUL_MAT_ID | f32 | n>1 | 14 | 0.958 |
| MUL_MAT_ID | q4_0 | n=1 | 2 | 1.033 |
| MUL_MAT_ID | q4_0 | n>1 | 14 | 0.984 |
| MUL_MAT_ID | q4_K | n=1 | 2 | 0.963 |
| MUL_MAT_ID | q4_K | n>1 | 14 | 0.936 |
| MUL_MAT_ID | q6_K | n=1 | 2 | 0.904 |
| MUL_MAT_ID | q6_K | n>1 | 14 | 0.951 |
| MUL_MAT_ID | q8_0 | n=1 | 2 | 0.879 |
| MUL_MAT_ID | q8_0 | n>1 | 14 | 1.069 |

## End to end: llama-bench, Qwen3.5-9B Q4_K_XL fully on the card (tokens/s, mean of 3)

| run | prompt 512 | generation 128 |
|---|---|---|
| nvcc | 135.29 (sd 0.01) | 9.56 (sd 0.00) |
| clang | 135.01 (sd 0.01) | 10.09 (sd 0.01) |
| nvcc2 | 135.26 (sd 0.05) | 9.55 (sd 0.00) |

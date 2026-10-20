## Correctness (`test-backend-ops` against the CPU backend)

| operation | nvcc | ieee | hybieee |
|---|---|---|---|
| FLASH_ATTN_EXT | 2832/2832 | 2411/2832 | 2832/2832 |
| SOFT_MAX | 192/212 | 210/212 | 208/212 |
| MUL_MAT | 1094/1094 | 1094/1094 | 1094/1094 |
| MUL_MAT_ID | 764/764 | 764/764 | 764/764 |

## End to end: llama-bench, Qwen3.5-9B Q4_K_XL fully on the card (tokens/s)

| library | prompt 512 | generation |
|---|---|---|
| nvcc | 135.20 (sd 0.04) | 9.57 (sd 0.00) |
| ieee | 134.80 (sd 0.01) | 10.15 (sd 0.00) |
| hybnofast | 135.32 (sd 0.02) | 10.08 (sd 0.00) |
| hybieee | 135.32 (sd 0.01) | 10.07 (sd 0.00) |
| nvcc2 | 135.32 (sd 0.01) | 9.57 (sd 0.00) |

## Production model: Qwen3.6-35B-A3B Q4_K_XL, one card, 30 expert layers on the CPU, as in llama-server-one.service (tokens/s)

| library | prompt 512 | generation |
|---|---|---|
| nvcc | n/a | n/a |
| hybnofast | n/a | n/a |
| hybieee | n/a | n/a |
| nvcc2 | n/a | n/a |

## Greedy text, Qwen3.5-9B (two prompts, 64 tokens, seed 1, through llama-server) against the nvcc build

| library | prompt 1 | prompt 2 |
|---|---|---|
| nvcc | identical | identical |
| ieee | identical | identical |
| hybnofinite | identical | identical |
| hybnofast | identical | identical |
| hybieee | identical | identical |

## Greedy text, Qwen3.6-35B production model (two prompts, 64 tokens, seed 1, through llama-server) against the nvcc build

| library | prompt 1 | prompt 2 |
|---|---|---|
| nvcc | identical | identical |
| ieee | identical | identical |
| hybnofast | identical | identical |
| hybieee | identical | identical |

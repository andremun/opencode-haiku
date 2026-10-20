## Correctness (`test-backend-ops` against the CPU backend)

| operation | nvcc | nofinite | nofast | hybnofinite | hybnofast |
|---|---|---|---|---|---|
| FLASH_ATTN_EXT | 2832/2832 | 2419/2832 | 2471/2832 | 2832/2832 | 2832/2832 |
| SOFT_MAX | 198/212 | 206/212 | 204/212 | 207/212 | 206/212 |
| MUL_MAT | 1094/1094 | 1094/1094 | 1094/1094 | 1094/1094 | 1094/1094 |
| MUL_MAT_ID | 764/764 | 764/764 | 764/764 | 764/764 | 764/764 |

## Production model: Qwen3.6-35B-A3B Q4_K_XL, one card, 30 expert layers on the CPU, as in llama-server-one.service (tokens/s)

| library | prompt 512 | generation |
|---|---|---|
| nvcc | 88.11 (sd 0.45) | 13.34 (sd 0.01) |
| hybnofast | 89.97 (sd 0.46) | 14.07 (sd 0.09) |
| hybieee | 89.39 (sd 0.37) | 13.54 (sd 0.34) |
| nvcc2 | 87.77 (sd 0.40) | 12.60 (sd 0.25) |

## Greedy text, Qwen3.5-9B (two prompts, 64 tokens, seed 1, through llama-server) against the nvcc build

| library | prompt 1 | prompt 2 |
|---|---|---|
| nvcc | identical | identical |
| ieee | identical | **differs** at character 0: ' The Fibonacci sequence i' vs '\n\n```python\ndef fibonacci' |
| hybnofinite | identical | identical |
| hybnofast | identical | identical |
| hybieee | identical | identical |

## Greedy text, Qwen3.6-35B production model (two prompts, 64 tokens, seed 1, through llama-server) against the nvcc build

| library | prompt 1 | prompt 2 |
|---|---|---|
| nvcc | identical | identical |
| ieee | **differs** at character 23: ' and yellow.\nThe three secondary colo' vs ' and yellow. When two primary colours' | identical |
| hybnofast | **differs** at character 91: 'ndary colour. What secondary colour i' vs 'ndary colour: red + blue = purple, bl' | identical |
| hybieee | **differs** at character 237: 'dary colour?  \nA. Purple  \nB. Green  ' vs 'dary colour?\n\nA. Purple  \nB. Green  \n' | identical |

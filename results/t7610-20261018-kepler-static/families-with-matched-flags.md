| family | kernels | median regs nvcc | median regs clang | spilling nvcc | spilling clang | mean occupancy proxy nvcc | clang |
|---|---|---|---|---|---|---|---|
| mul_mat_vec_q (Q8_0,Q4_K,Q5_K,Q6_K) | 44 | 98 | 92 | 0 | 0 | 769 | 848 |
| mul_mat_q (Q8_0,Q4_K,Q6_K) | 96 | 42 | 66 | 26 | 44 | 1296 | 1281 |
| flash_attn_ext_vec | 24 | 218 | 227 | 0 | 0 | 616 | 605 |
| flash_attn_tile | 34 | 128 | 158 | 1 | 6 | 494 | 449 |
| mul_mat_vec_f (f16/f32) | 352 | 39 | 30 | 0 | 0 | 1558 | 1750 |
| other (all remaining matched) | 1156 | 28 | 27 | 1 | 14 | 1624 | 1636 |

total spill bytes (stores+loads): nvcc 46712, clang 60784

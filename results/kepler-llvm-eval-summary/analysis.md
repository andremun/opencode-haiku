| file | kernels nvcc | kernels clang | matched | SASS nvcc | SASS clang | clang/nvcc |
|---|---|---|---|---|---|---|
| acc.cu | 1 | 1 | 1 | 246 | 245 | 1.0 |
| add-id.cu | 1 | 1 | 1 | 63 | 78 | 1.24 |
| arange.cu | 1 | 1 | 1 | 22 | 22 | 1.0 |
| argmax.cu | 1 | 1 | 1 | 112 | 112 | 1.0 |
| argsort.cu | 4 | 4 | 4 | 218 | 218 | 1.0 |
| binbcast.cu | 153 | 153 | 153 | 13697 | 13460 | 0.98 |
| clamp.cu | 2 | 2 | 2 | 50 | 50 | 1.0 |
| concat.cu | 7 | 7 | 7 | 469 | 509 | 1.09 |
| conv-transpose-1d.cu | 1 | 1 | 1 | 182 | 154 | 0.85 |
| conv2d-dw.cu | 2 | 2 | 2 | 1071 | 637 | 0.59 |
| conv2d-transpose.cu | 2 | 2 | 2 | 1064 | 637 | 0.6 |
| conv2d.cu | 2 | 2 | 2 | 2184 | 1687 | 0.77 |
| convert.cu | 62 | 62 | 62 | 7523 | 7651 | 1.02 |
| count-equal.cu | 1 | 1 | 1 | 441 | 154 | 0.35 |
| cpy.cu | 35 | 35 | 35 | 16152 | 14061 | 0.87 |
| cross-entropy-loss.cu | 4 | 4 | 4 | 3474 | 1422 | 0.41 |
| cumsum.cu | 2 | 2 | 2 | 224 | 238 | 1.06 |
| diag.cu | 2 | 2 | 2 | 700 | 707 | 1.01 |
| diagmask.cu | 1 | 1 | 1 | 42 | 42 | 1.0 |
| fattn-tile.cu | 0 | 0 | 0 | 0 | 0 | 0.0 |
| fattn-wmma-f16.cu | 95 | 95 | 95 | 14037 | 10207 | 0.73 |
| fattn.cu | 6 | 6 | 6 | 1416 | 792 | 0.56 |
| fill.cu | 2 | 2 | 2 | 44 | 44 | 1.0 |
| gated_delta_net.cu | 8 | 8 | 8 | 2313 | 1715 | 0.74 |
| getrows.cu | 41 | 41 | 41 | 11332 | 10177 | 0.9 |
| gla.cu | 2 | 2 | 2 | 1302 | 2772 | 2.13 |
| im2col.cu | 4 | 4 | 4 | 3655 | 1710 | 0.47 |
| mean.cu | 1 | 1 | 1 | 168 | 133 | 0.79 |
| mmf.cu | 0 | 0 | 0 | 0 | 0 | 0.0 |
| mmid.cu | 7 | 7 | 7 | 3192 | 1330 | 0.42 |
| mmq.cu | 64 | 64 | 64 | 75460 | 68814 | 0.91 |
| mmvf.cu | 352 | 352 | 352 | 143800 | 110770 | 0.77 |
| mmvq.cu | 264 | 264 | 264 | 271446 | 256926 | 0.95 |
| norm.cu | 14 | 14 | 14 | 6246 | 3467 | 0.56 |
| opt-step-adamw.cu | 1 | 1 | 1 | 77 | 84 | 1.09 |
| opt-step-sgd.cu | 1 | 1 | 1 | 35 | 35 | 1.0 |
| out-prod.cu | 0 | 0 | 0 | 0 | 0 | 0.0 |
| pad.cu | 1 | 1 | 1 | 322 | 315 | 0.98 |
| pad_reflect_1d.cu | 1 | 1 | 1 | 84 | 85 | 1.01 |
| pool2d.cu | 1 | 1 | 1 | 273 | 252 | 0.92 |
| quantize.cu | 5 | 5 | 5 | 918 | 1008 | 1.1 |
| roll.cu | 1 | 1 | 1 | 462 | 470 | 1.02 |
| rope.cu | 40 | 40 | 40 | 6488 | 17478 | 2.69 |
| scale.cu | 1 | 1 | 1 | 217 | 35 | 0.16 |
| set-rows.cu | 18 | 18 | 6 | 6729 | 5364 | 0.8 |
| set.cu | 0 | 0 | 0 | 0 | 0 | 0.0 |
| softcap.cu | 1 | 1 | 1 | 42 | 42 | 1.0 |
| softmax.cu | 22 | 22 | 22 | 7050 | 8878 | 1.26 |
| solve_tri.cu | 12 | 12 | 12 | 15677 | 18923 | 1.21 |
| ssm-conv.cu | 16 | 16 | 16 | 11020 | 5279 | 0.48 |
| ssm-scan.cu | 11 | 11 | 11 | 9621 | 13176 | 1.37 |
| sum.cu | 0 | 0 | 0 | 0 | 0 | 0.0 |
| sumrows.cu | 1 | 1 | 1 | 168 | 126 | 0.75 |
| template-instances/fattn-tile-instance-dkq128-dv128.cu | 75 | 75 | 75 | 112474 | 114934 | 1.02 |
| template-instances/fattn-vec-instance-f16-f16.cu | 29 | 29 | 29 | 39424 | 29856 | 0.76 |
| template-instances/fattn-vec-instance-q4_0-q4_0.cu | 29 | 29 | 29 | 62815 | 47342 | 0.75 |
| template-instances/mmq-instance-q4_k.cu | 64 | 64 | 64 | 96023 | 90780 | 0.95 |
| template-instances/mmq-instance-q6_k.cu | 64 | 64 | 64 | 97740 | 95939 | 0.98 |
| template-instances/mmq-instance-q8_0.cu | 64 | 64 | 64 | 73329 | 67363 | 0.92 |
| top-k.cu | 0 | 0 | 0 | 0 | 0 | 0.0 |
| topk-moe.cu | 22 | 22 | 22 | 13325 | 12370 | 0.93 |
| tri.cu | 12 | 12 | 12 | 2863 | 1802 | 0.63 |
| tsembd.cu | 1 | 1 | 1 | 57 | 63 | 1.11 |
| unary.cu | 73 | 73 | 73 | 4164 | 4415 | 1.06 |
| upscale.cu | 4 | 4 | 4 | 1631 | 1086 | 0.67 |
| wkv.cu | 4 | 4 | 4 | 3396 | 5257 | 1.55 |

files compared: 66, nvcc failures: 0, clang failures: 0
kernels: nvcc 1718, clang 1718, matched by name 1706
total SASS instructions (files where both compiled): nvcc 1148769, clang 1053698, ratio 0.917
registers per matched kernel: median clang/nvcc 1.000; clang higher 590, lower 700, equal 416; clang >= nvcc+8: 137
max registers: nvcc 255, clang 255; kernels with spills: nvcc 28, clang 64
largest clang register increases: [('mmvq.cu', 'void mul_mat_vec_q<(ggml_type)40, 7, false, false>', 138, 250), ('template-instances/fattn-vec-instance-q4_0-q4_0.cu', 'void flash_attn_ext_vec<64, 1, (ggml_type)2, (ggml', 145, 244), ('mmvq.cu', 'void mul_mat_vec_q<(ggml_type)40, 6, false, false>', 134, 225), ('mmvq.cu', 'void mul_mat_vec_q<(ggml_type)40, 5, false, false>', 132, 196), ('mmq.cu', 'void mul_mat_q<(ggml_type)41, 16, false>(char cons', 66, 128)]
largest clang register decreases: [('wkv.cu', 'void rwkv_wkv7_f32<128>(int, int, int, int, float ', 255, 40), ('wkv.cu', 'void rwkv_wkv_f32<128>(int, int, int, int, float c', 168, 40), ('gla.cu', 'void gated_linear_attn_f32<128>(int, int, int, int', 166, 40), ('mmvq.cu', 'void mul_mat_vec_q<(ggml_type)11, 1, true, true>(v', 240, 139), ('mmvq.cu', 'void mul_mat_vec_q<(ggml_type)29, 6, false, false>', 236, 165)]

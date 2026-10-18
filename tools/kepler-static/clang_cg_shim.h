// Declarations only. Clang's CUDA wrapper does not declare the sm_70 warp-match intrinsics when
// compiling for older targets, but CUDA 11.4's cooperative_groups/details/partitioning.h refers to
// them in non-dependent code, so including <cooperative_groups.h> fails for sm_35. These are never
// instantiated for sm_35. Used only for the Clang side of the comparison (see compare_compilers.py).
#if defined(__CUDA__)
template <class T> __device__ unsigned int __match_any_sync(unsigned int, T);
template <class T> __device__ unsigned int __match_all_sync(unsigned int, T, int *);
#endif

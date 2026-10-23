// Copyright (c) 2026 Mario Andres Munoz
// Distributed under the terms of the MIT License. See LICENSE.
#include <pthread.h>
#include <stdint.h>
#include <assert.h>
#include <time.h>
#include <stdio.h>
void opentui_haiku_futex_wait(const uint32_t*,uint32_t,uint64_t);
void opentui_haiku_futex_wake(const uint32_t*);
static uint32_t word;
static void *waiter(void *unused) {
 (void)unused;
 while(__atomic_load_n(&word,__ATOMIC_SEQ_CST)==0)opentui_haiku_futex_wait(&word,0,UINT64_MAX);
 return 0;
}
int main(void) {
 for(int round=0;round<200;round++) {
  __atomic_store_n(&word,0,__ATOMIC_SEQ_CST);pthread_t t;
  assert(pthread_create(&t,0,waiter,0)==0);
  __atomic_store_n(&word,1,__ATOMIC_SEQ_CST);opentui_haiku_futex_wake(&word);
  assert(pthread_join(t,0)==0);
 }
 struct timespec a,b;clock_gettime(CLOCK_MONOTONIC,&a);
 opentui_haiku_futex_wait(&word,1,1000000);clock_gettime(CLOCK_MONOTONIC,&b);
 long long elapsed=(b.tv_sec-a.tv_sec)*1000000000LL+b.tv_nsec-a.tv_nsec;
 assert(elapsed>=500000 && elapsed<1000000000LL);
 puts("FUTEX_PASS: 200 publication/wake races and bounded timeout");
}

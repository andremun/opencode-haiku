// Copyright (c) 2026 Mario Andres Munoz
// Distributed under the terms of the MIT License. See LICENSE.
/* Process-private futex fallback. Hash collisions produce permitted spurious wakes.
 * Wait and wake use the same mutex, preventing lost wakes across the value check.
 * Cancelable waits periodically return to Zig's cancellation check. */
#include <pthread.h>
#include <stdint.h>
#include <time.h>
#include <stdlib.h>
#define BUCKETS 64
static pthread_mutex_t mutexes[BUCKETS];
static pthread_cond_t conditions[BUCKETS];
static pthread_once_t once = PTHREAD_ONCE_INIT;
static void init(void) {
 pthread_condattr_t attr;
 if(pthread_condattr_init(&attr) || pthread_condattr_setclock(&attr,CLOCK_MONOTONIC))abort();
 for (int i=0;i<BUCKETS;i++) {
  if (pthread_mutex_init(&mutexes[i],0) || pthread_cond_init(&conditions[i],&attr)) abort();
 }
 pthread_condattr_destroy(&attr);
}
static unsigned bucket(const uint32_t *p) { return ((uintptr_t)p >> 2) % BUCKETS; }
void opentui_haiku_futex_wait(const uint32_t *p,uint32_t expected,uint64_t ns) {
 pthread_once(&once,init);unsigned i=bucket(p);
 pthread_mutex_lock(&mutexes[i]);
 if (__atomic_load_n(p,__ATOMIC_SEQ_CST)==expected) {
  struct timespec end; clock_gettime(CLOCK_MONOTONIC,&end);
  /* Bound every park to 50ms so cancellation is observed even without SIGIO. */
  if(ns>50000000)ns=50000000;
  end.tv_sec += ns/1000000000;end.tv_nsec += ns%1000000000;
  if(end.tv_nsec>=1000000000){end.tv_sec++;end.tv_nsec-=1000000000;}
  pthread_cond_timedwait(&conditions[i],&mutexes[i],&end);
 }
 pthread_mutex_unlock(&mutexes[i]);
}
void opentui_haiku_futex_wake(const uint32_t *p) {
 pthread_once(&once,init);unsigned i=bucket(p);
 pthread_mutex_lock(&mutexes[i]);pthread_cond_broadcast(&conditions[i]);pthread_mutex_unlock(&mutexes[i]);
}

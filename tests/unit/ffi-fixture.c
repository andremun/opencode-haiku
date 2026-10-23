// Copyright (c) 2026 Mario Andres Munoz
// Distributed under the terms of the MIT License. See LICENSE.
#include <stdint.h>
#include <stdlib.h>
int32_t sum32(int32_t a,int32_t b){return a+b;}
uint64_t echo64(uint64_t value){return value;}
void* allocate(uint32_t bytes){return calloc(1,bytes);}
void release(void* pointer){free(pointer);}
void write_byte(void* pointer,uint32_t offset,uint8_t value){((uint8_t*)pointer)[offset]=value;}
int32_t invoke_callback(void* callback,int32_t value){return ((int32_t(*)(int32_t))callback)(value);}

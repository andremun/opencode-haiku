// Copyright (c) 2026 Mario Andres Munoz
// Distributed under the terms of the MIT License. See LICENSE.
'use strict';
const assert=require('node:assert/strict');
console.log('stage: import');
const ffi=require('node:ffi');
console.log('stage: dlopen');
const {functions:f,lib}=ffi.dlopen(process.argv[2],{
 sum32:{arguments:['i32','i32'],return:'i32'},echo64:{arguments:['u64'],return:'u64'},
 allocate:{arguments:['u32'],return:'pointer'},release:{arguments:['pointer'],return:'void'},
 write_byte:{arguments:['pointer','u32','u8'],return:'void'},invoke_callback:{arguments:['pointer','i32'],return:'i32'}
});
console.log("stage: integer call");
assert.equal(f.sum32(-10,17),7);
assert.equal(f.echo64(2n**60n+7n),2n**60n+7n);
console.log("stage: allocation");
const memory=f.allocate(8);assert(memory>0n);
console.log("stage: shared view");
const view=new Uint8Array(ffi.toArrayBuffer(memory,8,false));
f.write_byte(memory,2,19);assert.equal(view[2],19);
view[3]=23;assert.equal(new Uint8Array(ffi.toArrayBuffer(memory,8,true))[3],23);
console.log("stage: buffer pointer");
const owner=new ArrayBuffer(10);const bytes=new Uint8Array(owner,3,4);
f.write_byte(bytes,1,29);assert.equal(new Uint8Array(owner)[4],29);
assert.equal(ffi.getRawPointer(owner)+3n,ffi.getRawPointer(bytes.buffer)+BigInt(bytes.byteOffset));
console.log("stage: callback");
const callback=lib.registerCallback({arguments:['i32'],return:'i32'},value=>value+9);
assert.equal(f.invoke_callback(callback,4),13);lib.unregisterCallback(callback);
assert.throws(()=>lib.unregisterCallback(callback),/Unknown callback/);
f.release(memory);lib.close();lib.close();assert.throws(()=>f.sum32(1,2),/closed/);
assert.throws(()=>ffi.toArrayBuffer(0n,4),/address/);
console.log('FFI_PASS: signed widths, BigInt, shared native memory, sliced buffers, callbacks and closed-library rejection');

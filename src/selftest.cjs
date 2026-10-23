// Copyright (c) 2026 Mario Andres Munoz
// Distributed under the terms of the MIT License. See LICENSE.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const directory=fs.mkdtempSync(path.join(os.tmpdir(),'opencode-haiku-selftest-'));
(async()=>{
 try{
  const ffi=require('./haiku-ffi.cjs');
  const lib=ffi.dlopen('libroot.so',{getpid:{arguments:[],return:'i32'}});
  assert.equal(lib.functions.getpid(),process.pid);lib.lib.close();
  const file=path.join(directory,'fixture');fs.writeFileSync(file,'before');
  const watcher=fs.watch(directory);
  const event=new Promise((resolve,reject)=>{
   const timeout=setTimeout(()=>reject(new Error('Watcher timeout')),5000);
   watcher.once('change',(type,name)=>{clearTimeout(timeout);resolve(String(name));});
  });
  fs.writeFileSync(file,'after');assert.equal(await event,'fixture');watcher.close();
  const clip=require('./haiku-clipboard.cjs').createBackend();
  const status=await clip.read({selection:'clipboard',preferredTypes:['text/plain'],maxBytes:8*1024*1024,timeoutMs:10000,signal:new AbortController().signal});
  assert.ok(['read','empty'].includes(status.status),JSON.stringify(status));await clip.dispose();
  console.log('SELFTEST_PASS: native FFI, watcher, clipboard read, clean release');
 }finally{fs.rmSync(directory,{recursive:true,force:true});}
})().catch(error=>{console.error(error);process.exitCode=1;});

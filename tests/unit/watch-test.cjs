// Copyright (c) 2026 Mario Andres Munoz
// Distributed under the terms of the MIT License. See LICENSE.
'use strict';
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict');
const {pollingWatch}=require('./haiku-watch.cjs');
(async()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'haiku-watch-'));const events=[];
 const watch=pollingWatch(dir,{persistent:false},(event,file)=>events.push([event,file]));
 const pause=()=>new Promise(r=>setTimeout(r,1150));
 try{
  fs.writeFileSync(path.join(dir,'a'),'one');await pause();assert(events.some(([e,f])=>e==='rename'&&f==='a'));
  events.length=0;fs.writeFileSync(path.join(dir,'a'),'two longer');await pause();assert(events.some(([e,f])=>e==='change'&&f==='a'));
  events.length=0;fs.unlinkSync(path.join(dir,'a'));await pause();assert(events.some(([e,f])=>e==='rename'&&f==='a'));
  watch.close();events.length=0;fs.writeFileSync(path.join(dir,'b'),'x');await pause();assert.equal(events.length,0);
  assert.throws(()=>pollingWatch(dir,{recursive:true}),{code:'ENOSYS'});
  const controller=new AbortController();const aborted=pollingWatch(dir,{signal:controller.signal});controller.abort();assert.equal(aborted.unref(),aborted);
  console.log('WATCH_PASS: create, modify, delete, closed lifecycle, abort and explicit recursive rejection');
 }finally{watch.close();fs.rmSync(dir,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exitCode=1;});

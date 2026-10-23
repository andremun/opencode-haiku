// Copyright (c) 2026 Mario Andres Munoz
// Distributed under the terms of the MIT License. See LICENSE.
'use strict';
const {spawn}=require('node:child_process');
const path=require('node:path');
exports.createBackend=function(binary=path.join(__dirname,'haiku-clipboard')){
 let disposed=false;
 const active=new Set();
 function run(operation,options,text){
  if(disposed)return Promise.resolve({status:'failed',error:new Error('Clipboard disposed')});
  if(options.selection!=='clipboard')return Promise.resolve({status:'unsupported'});
  if(options.signal.aborted)return Promise.resolve({status:'cancelled'});
  return new Promise(resolve=>{
   const child=spawn(binary,[operation],{stdio:['pipe','pipe','pipe']});
   let status,bytes=0; const chunks=[]; let diagnostic='';
   const cancel=()=>{status='cancelled';child.kill('SIGKILL');};
   options.signal.addEventListener('abort',cancel,{once:true});
   const timer=setTimeout(()=>{status='timed-out';child.kill('SIGKILL');},options.timeoutMs);
   active.add(child);
   child.stdout.on('data',chunk=>{bytes+=chunk.length;if(bytes>options.maxBytes){status='limit-exceeded';child.kill('SIGKILL');}else chunks.push(chunk);});
   child.stderr.on('data',chunk=>{diagnostic=(diagnostic+chunk).slice(0,4096);});
   child.stdin.on('error',()=>{});
   child.on('error',error=>{diagnostic=String(error);});
   child.on('close',code=>{
    clearTimeout(timer);options.signal.removeEventListener('abort',cancel);active.delete(child);
    if(status)return resolve({status});
    if(code!==0)return resolve({status:'failed',error:new Error(diagnostic||'Clipboard command failed: '+code)});
    if(operation==='read')return resolve(bytes?{status:'read',representation:{mimeType:'text/plain',bytes:Buffer.concat(chunks)}}:{status:'empty'});
    resolve({status:operation==='write'?'written':'cleared'});
   });
   child.stdin.end(text);
  });
 }
 return {
  read(options){return options.preferredTypes.includes('text/plain')?run('read',options):Promise.resolve({status:'unsupported'});},
  writeText(text,options){return run('write',options,text);},
  clear(options){return run('clear',options);},
  async dispose(){disposed=true;await Promise.all([...active].map(child=>new Promise(resolve=>{child.once('close',resolve);child.kill('SIGKILL');})));}
 };
};

'use strict';
const fs=require('node:fs');
const path=require('node:path');
const {EventEmitter}=require('node:events');
const {fileURLToPath}=require('node:url');
function pollingWatch(filename,options={},listener) {
 if(typeof options==='function'){listener=options;options={};}
 if(typeof options==='string')options={encoding:options};
 const target=path.resolve(filename instanceof URL?fileURLToPath(filename):filename.toString());
 if(options.recursive)throw Object.assign(new Error('Haiku polling watcher does not support recursive trees'),{code:'ENOSYS'});
 const directory=fs.statSync(target).isDirectory();
 const watcher=new EventEmitter();let closed=false,busy=false;
 if(listener)watcher.on('change',listener);
 function snapshot() {
  const names=directory?fs.readdirSync(target):[path.basename(target)];
  if(names.length>8192)throw Object.assign(new Error('Polling watcher directory exceeds 8192 entries'),{code:'ENOSPC'});
  const data=new Map();
  for(const name of names){try{const st=fs.statSync(directory?path.join(target,name):target);data.set(name,`${st.ino}:${st.size}:${st.mtimeMs}:${st.ctimeMs}`);}catch(e){if(e.code!=='ENOENT')throw e;}}
  return data;
 }
 let previous=snapshot();
 const timer=setInterval(()=>{
  if(closed||busy)return;busy=true;
  try{
   const next=snapshot();
   for(const name of new Set([...previous.keys(),...next.keys()])){
    if(closed)break;
    if(previous.get(name)!==next.get(name))watcher.emit('change',previous.has(name)&&next.has(name)?'change':'rename',options.encoding==='buffer'?Buffer.from(name):name);
   }
   previous=next;
  }catch(error){if(!closed)watcher.emit('error',error);}finally{busy=false;}
 },1000);
 const abort=()=>watcher.close();
 watcher.close=()=>{if(closed)return;closed=true;clearInterval(timer);options.signal?.removeEventListener('abort',abort);queueMicrotask(()=>watcher.emit('close'));};
 watcher.ref=()=>{timer.ref();return watcher;};watcher.unref=()=>{timer.unref();return watcher;};
 if(options.persistent===false)watcher.unref();
 if(options.signal?.aborted)watcher.close();else options.signal?.addEventListener('abort',abort,{once:true});
 return watcher;
}
exports.pollingWatch=pollingWatch;
exports.install=()=>{fs.watch=pollingWatch;require('node:module').syncBuiltinESMExports();};

'use strict';
const assert=require('node:assert/strict');
const {createBackend}=require('./haiku-clipboard.cjs');
(async()=>{
 const backend=createBackend();
 const options={selection:'clipboard',timeoutMs:10000,maxBytes:8*1024*1024,preferredTypes:['text/plain'],signal:new AbortController().signal};
 const initial=await backend.read(options);
 try{
  const text='OpenCode UTF-8: α β\nline two\n';
  assert.equal((await backend.writeText(text,options)).status,'written');
  const read=await backend.read(options);assert.equal(read.status,'read');assert.equal(Buffer.from(read.representation.bytes).toString(),text);
  assert.equal((await backend.read({...options,maxBytes:2})).status,'limit-exceeded');
  assert.equal((await backend.read({...options,selection:'primary'})).status,'unsupported');
  assert.equal((await backend.read({...options,preferredTypes:['image/png']})).status,'unsupported');
  const abort=new AbortController();abort.abort();assert.equal((await backend.read({...options,signal:abort.signal})).status,'cancelled');
  assert.equal((await backend.clear(options)).status,'cleared');assert.equal((await backend.read(options)).status,'empty');
 }finally{
  if(initial.status==='read')await backend.writeText(Buffer.from(initial.representation.bytes).toString(),options);
  else if(initial.status==='empty')await backend.clear(options);
  await backend.dispose();
 }
 assert.equal((await backend.read(options)).status,'failed');
 console.log('CLIPBOARD_PASS: exact UTF-8/newline, limit, unsupported, abort, clear, dispose');
})().catch(error=>{console.error(error);process.exitCode=1;});

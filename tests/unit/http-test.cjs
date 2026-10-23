// Copyright (c) 2026 Mario Andres Munoz
// Distributed under the terms of the MIT License. See LICENSE.
'use strict';
const http=require('node:http'),assert=require('node:assert/strict');
const {Agent,setGlobalDispatcher}=require('./undici');
(async()=>{
 const server=http.createServer((req,res)=>setTimeout(()=>{if(!res.destroyed)res.end('WAIT_PASS');},1600));
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const agent=new Agent({headersTimeout:50});setGlobalDispatcher(agent);
 const restore=require('./haiku-http.cjs').install();
 const url='http://127.0.0.1:'+server.address().port;
 try{
  await assert.rejects(fetch(url),error=>error.cause?.code==='UND_ERR_HEADERS_TIMEOUT');
  assert.equal(await (await fetch(url,{timeout:false})).text(),'WAIT_PASS');
  await assert.rejects(fetch(url,{timeout:false,signal:AbortSignal.timeout(50)}),error=>error.name==='TimeoutError');
  console.log('HTTP_WAIT_PASS: default timeout negative control, explicit unlimited wait, abort preserved');
 }finally{restore();await agent.destroy();server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{console.error(error);process.exitCode=1;});

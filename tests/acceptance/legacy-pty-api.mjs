// Copyright (c) 2026 Mario Andres Munoz
// Distributed under the terms of the MIT License. See LICENSE.
// Exercises real OpenCode APIs without an LLM or native PTY.
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { randomBytes } from 'node:crypto';
import assert from 'node:assert/strict';
const root = resolve(process.argv[2] ?? '/boot/home/opencode-acceptance');
const fixture = resolve(root, 'api-fixture');
mkdirSync(fixture, { recursive: true });
writeFileSync(resolve(fixture, 'opencode.json'), JSON.stringify({update:'disable',share:'disabled',snapshots:false,shell:'/bin/sh',permissions:[{action:'*',resource:'*',effect:'deny'}]}));
const env = Object.fromEntries(Object.entries(process.env).filter(([name]) => /^(PATH|XDG_(DATA|CONFIG|CACHE|STATE)_HOME|LANG|LC_[A-Z_]+|SSL_CERT_FILE|SSL_CERT_DIR)$/.test(name)));
env.OPENCODE_PRINT_LOGS='1';
env.OPENCODE_DISABLE_MODELS_FETCH='1';
for(const name of ['DATA','CONFIG','CACHE','STATE'])env['XDG_'+name+'_HOME']=resolve(root,'legacy-pty-state2',name.toLowerCase());
env.OPENCODE_NODE_PTY_PATH=resolve(root,"node-pty");
let endpointURL;
let server;
let logs='';
const record = (event,data) => {logs += JSON.stringify({event,data})+'\n';writeFileSync(resolve(root,'api-probe.log'),logs);};
const watchdog=setTimeout(()=>{record('timeout',240000);server?.kill('SIGKILL');process.exit(124);},600000);
async function start() {
 const password=randomBytes(32).toString('base64url');
 server=spawn(resolve(process.env.OPENCODE_TEST_RUNTIME_ROOT||resolve(root,'http-port'),'opencode'),['--print-logs','serve','--stdio','--port','0'],{cwd:fixture,env:{...env,OPENCODE_PASSWORD:password},stdio:['pipe','pipe','pipe']});
 server.stderr.on('data',chunk=>{logs+=chunk;writeFileSync(resolve(root,'api-probe.log'),logs);});
 const url=await new Promise((done,fail)=>{
  let output='';
  server.stdout.on('data',chunk=>{output+=chunk;const line=output.split('\n')[0];if(output.includes('\n')) {try{done(JSON.parse(line).url);}catch(e){fail(e);}}});
  server.on('error',fail);server.on('exit',code=>fail(new Error('server exited: '+code)));
 });
 const headers={Authorization:'Basic '+Buffer.from('opencode:'+password).toString('base64')};
 endpointURL=url;record('server-ready',{url});
 return async function request(path,{method='GET',body,raw=false,extraHeaders={}}={}) {
  const response=await fetch(url+path,{method,headers:{...headers,...extraHeaders,...(body!==undefined?{'Content-Type':raw?'application/octet-stream':'application/json'}:{})},body:body===undefined?undefined:raw?body:JSON.stringify(body),signal:AbortSignal.timeout(45000)});
  const text=await response.text();
  if(!response.ok)throw new Error(`${method} ${path}: HTTP ${response.status}: ${text}`);
  return raw?text:text?JSON.parse(text):undefined;
 };
}
async function stop() {
 const child=server;
 child.stdin.end();
 await new Promise(done=>{const timer=setTimeout(()=>child.kill('SIGKILL'),5000);child.on('close',()=>{clearTimeout(timer);done();});});
 server=undefined;
}
try {
 let api=await start();
 const script="stty size; printf 'LEGACY_PTY_READY\\n'; read line; stty size; printf 'LEGACY_RESULT %s\\n' \"$line\"; exit 7";
 const terminal=(await api('/api/pty',{method:'POST',body:{command:'/bin/sh',args:['-c',script],cwd:fixture,title:'Native browser PTY'}})).data;
 const issued=(await api('/api/pty/'+terminal.id+'/connect-token',{method:'POST',extraHeaders:{'x-opencode-ticket':'1'}})).data;
 const url=new URL(endpointURL.replace(/^http/,'ws')+'/api/pty/'+terminal.id+'/connect');url.searchParams.set('ticket',issued.ticket);url.searchParams.set('cursor','0');
 const socket=new WebSocket(url);socket.binaryType='arraybuffer';
 let terminalOutput='',sent=false;
 const finished=new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>{socket.close();reject(new Error('Legacy PTY timeout'));},30000);
  socket.addEventListener('error',()=>{clearTimeout(timer);reject(new Error('Legacy websocket error'));});
  socket.addEventListener('message',async event=>{
   const bytes=typeof event.data==='string'?Buffer.from(event.data):Buffer.from(event.data);
   if(bytes[0]===0)return;
   terminalOutput+=bytes.toString();
   if(!sent&&terminalOutput.includes('LEGACY_PTY_READY')){sent=true;await api('/api/pty/'+terminal.id,{method:'PUT',body:{size:{cols:100,rows:42}}});socket.send('HELLO\n');}
   if(terminalOutput.includes('LEGACY_RESULT HELLO')){clearTimeout(timer);resolve();}
  });
 });
 await finished;socket.close();
 assert.match(terminalOutput,/42 100/);assert.match(terminalOutput,/LEGACY_RESULT HELLO/);
 record('native-browser-pty',{id:terminal.id,output:terminalOutput});
 await api('/api/pty/'+terminal.id,{method:'DELETE'});

 const code='export const add = (a, b) => a + b;\n';
 await api('/api/experimental/fs/write?path=add.mjs',{method:'POST',body:code,raw:true});
 assert.equal(await api('/api/fs/read/add.mjs',{raw:true}),code);
 record('file-write-read','passed');
 const found=(await api('/api/fs/find?query=add&type=file')).data;
 assert(found.some(file=>file.path==='add.mjs'));
 record('portable-file-search','passed');
 const test="import { add } from './add.mjs'; import assert from 'node:assert/strict'; assert.equal(add(2,3),5); assert.equal(add(-2,3),1); console.log('API_SHELL_PASS');\n";
 await api('/api/experimental/fs/write?path=test.mjs',{method:'POST',body:test,raw:true});
 const created=await api('/api/shell',{method:'POST',body:{command:'node test.mjs',timeout:15000}});
 const id=created.data.id;
 let shell;
 for(let n=0;n<60;n++) {shell=(await api('/api/shell/'+id)).data;if(shell.status!=='running')break;await new Promise(done=>setTimeout(done,250));}
 const output=(await api('/api/shell/'+id+'/output')).data;
 record('shell-result',{shell,output});
 assert.equal(shell.status,'exited');assert.equal(shell.exit,0);assert.match(output.output,/API_SHELL_PASS/);
 const session=(await api('/api/session',{method:'POST',body:{title:'Native Haiku persistence probe',location:{directory:fixture}}})).data;
 record('session-created',{id:session.id,title:session.title});
 await stop();
 api=await start();
 const restored=(await api('/api/session/'+session.id)).data;
 assert.equal(restored.title,session.title);
 assert.equal(restored.id,session.id);
 assert.equal(await api('/api/fs/read/add.mjs',{raw:true}),code);
 record('session-after-server-restart','passed');
 record('result','PASS: actual file read/write, shell execution and stored session survive restart; no LLM inference tested');
 writeFileSync(resolve(root,'api-probe.exit'),'0\n');
} catch(error) {
 record('error',{message:error.message,stack:error.stack});
 writeFileSync(resolve(root,'api-probe.exit'),'1\n');process.exitCode=1;
} finally {
 if(server)await stop();clearTimeout(watchdog);
 if(process.platform==='haiku')for(const name of ['api-probe.log','api-probe.exit'])await fetch('http://10.0.2.2:18080/legacy-'+name,{method:'PUT',body:readFileSync(resolve(root,name)),signal:AbortSignal.timeout(10000)}).catch(()=>{});
}

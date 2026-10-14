'use strict';
const assert=require('node:assert/strict');
const root=process.argv[2]||'/boot/home/opencode-acceptance/node-pty';
const pty=require(root);
(async()=>{
 let output='',ready=false;
 const terminal=pty.spawn('/bin/sh',['-c',"test -t 0 || exit 3; stty size; printf 'NODE_PTY_READY\\n'; read line; stty size; printf 'UTF8 α β %s\\n' \"$line\"; exit 7"],{name:'xterm',cols:80,rows:24,cwd:'/boot/home/opencode-acceptance',env:{...process.env,TERM:'xterm'}});
 terminal.onData(chunk=>{output+=chunk;if(!ready&&output.includes('NODE_PTY_READY')){ready=true;terminal.resize(100,42);terminal.write('HELLO\n');}});
 const timer=setTimeout(()=>terminal.kill('SIGKILL'),30000);
 const exit=await new Promise(resolve=>terminal.onExit(resolve));clearTimeout(timer);
 assert.equal(exit.exitCode,7);assert.ok(ready);assert.match(output,/24 80/);assert.match(output,/42 100/);assert.match(output,/UTF8 α β HELLO/);
 console.log(output);console.log('NODE_PTY_PASS: native spawn, read/write, UTF-8, resize, child exit');
})().catch(error=>{console.error(error);process.exitCode=1;});

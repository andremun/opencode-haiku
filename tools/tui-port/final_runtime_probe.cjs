'use strict';
const {spawn}=require('node:child_process'),fs=require('node:fs');
const work='/boot/home/opencode-acceptance',root=work+'/final-port';
const env={...process.env,OPENCODE_HAIKU_KOFFI:root+'/koffi',NODE_OPTIONS:'--require='+root+'/haiku-loader.cjs',LIBRARY_PATH:'/boot/system/lib'};
const child=spawn(process.execPath,[work+'/ffi-test.cjs',work+'/ffi-fixture.so'],{env,stdio:['ignore','pipe','pipe']});
let log='';const file=work+'/final-runtime.log';
for(const stream of [child.stdout,child.stderr])stream.on('data',d=>{log+=d;fs.writeFileSync(file,log);});
const timer=setTimeout(()=>{log+='TIMEOUT\n';child.kill('SIGKILL');},60000);
child.on('close',code=>{clearTimeout(timer);log+='exit: '+code+'\n';fs.writeFileSync(file,log);fs.writeFileSync(work+'/final-runtime.exit',String(code===0&&log.includes('FFI_PASS')?0:1)+'\n');});

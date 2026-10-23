// Copyright (c) 2026 Mario Andres Munoz
// Distributed under the terms of the MIT License. See LICENSE.
'use strict';
const fs=require('node:fs'),{execFileSync}=require('node:child_process');
const root='/boot/home/opencode-acceptance';
const pid=Number(fs.readFileSync(root+'/llama-server-small-batch.pid','utf8').trim());
if(!Number.isSafeInteger(pid)||pid<=1)throw new Error('Invalid owned PID');
const expected='/boot/home/haiku-app/build/bin/llama-server';
function owns(){return execFileSync('/bin/ps',{encoding:'utf8'}).split('\n').find(line=>line.startsWith(expected)&&new RegExp('\\s'+pid+'\\s').test(line));}
(async()=>{
 const before=owns();if(!before)throw new Error('Owned model PID/command did not match');
 process.kill(pid,'SIGTERM');
 await new Promise(resolve=>setTimeout(resolve,10000));
 let forced=false;if(owns()){process.kill(pid,'SIGKILL');forced=true;}
 await new Promise(resolve=>setTimeout(resolve,1000));
 const report={pid,before,forced,stopped:!owns()};
 fs.writeFileSync(root+'/model-stop.json',JSON.stringify(report,null,2)+'\n');
 await fetch('http://10.0.2.2:18080/model-stop.json',{method:'PUT',body:JSON.stringify(report,null,2),signal:AbortSignal.timeout(10000)});
})();

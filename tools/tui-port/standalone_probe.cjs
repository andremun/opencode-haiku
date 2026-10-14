'use strict';
const {spawn}=require('node:child_process'),fs=require('node:fs');
const work='/boot/home/opencode-acceptance';
const env={...process.env,OPENCODE_HAIKU_KOFFI:work+'/koffi',NODE_OPTIONS:'--require='+work+'/tui/haiku-loader.cjs',LIBRARY_PATH:'/boot/system/lib',OPENCODE_PRINT_LOGS:'1'};
for(const kind of ['DATA','CONFIG','CACHE','STATE'])env['XDG_'+kind+'_HOME']=work+'/private-probe/'+kind.toLowerCase();
env.OPENCODE_DISABLE_MODELS_FETCH='1';
for(const kind of ['data','config','cache','state'])fs.mkdirSync(work+'/private-probe/'+kind,{recursive:true});
const child=spawn(process.execPath,[work+'/tui/opencode.mjs','serve','--stdio','--port','0'],{env,cwd:work+'/fixture',stdio:['pipe','pipe','pipe']});
let log='';const file=work+'/standalone-probe.log';
function append(s){log+=s;fs.writeFileSync(file,log);}
child.stdout.on('data',d=>{append('stdout: '+d);try{JSON.parse(d.toString());child.stdin.end();}catch{}});
child.stderr.on('data',d=>append('stderr: '+d));
const timer=setTimeout(()=>{append('probe timeout\n');child.stdin.end();child.kill('SIGTERM');},120000);
child.on('close',code=>{clearTimeout(timer);append('exit: '+code+'\n');});

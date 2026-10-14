// Bounded native OpenCode test. The working directory contains synthetic data only.
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
const root = resolve(process.argv[2] ?? '.');
const fixture = resolve(root, 'local-fixture');
mkdirSync(fixture, {recursive:true});
writeFileSync(resolve(fixture,'README.md'), '# Synthetic OpenCode connectivity test\nNo private source files.\n');
writeFileSync(resolve(fixture,'opencode.json'), JSON.stringify({
 model:'local/qwen3-0.6b-test', update:'disable', share:'disabled', snapshots:false,
 permissions:[{action:'*',resource:'*',effect:'deny'}],
 providers:{local:{name:'Isolated local CPU model',package:'@opencode/ai/providers/openai-compatible',settings:{baseURL:process.platform==='haiku'?'http://10.0.2.2:18082/v1':'http://127.0.0.1:18082/v1',apiKey:'',provider:'local'},models:{'qwen3-0.6b-test':{name:'Qwen3 0.6B CPU test',capabilities:{tools:false,input:['text'],output:['text']},limit:{context:8192,output:32},body:{temperature:0,max_tokens:32,chat_template_kwargs:{enable_thinking:false}}}}}},
 agents:{probe:{mode:'primary',model:'local/qwen3-0.6b-test',system:'You are a concise assistant. Follow the user request. No tools are available.',steps:4},build:{model:'local/qwen3-0.6b-test',steps:4},title:{model:'local/qwen3-0.6b-test'},summary:{model:'local/qwen3-0.6b-test'}}
}));
const log = resolve(root,'local-model.log');
writeFileSync(log,'');
const env = Object.fromEntries(Object.entries(process.env).filter(([name]) => /^(PATH|XDG_(DATA|CONFIG|CACHE|STATE)_HOME|LANG|LC_[A-Z_]+|SSL_CERT_FILE|SSL_CERT_DIR)$/.test(name)));
env.OPENCODE_PRINT_LOGS = '1';
const child = spawn(process.execPath,[resolve(root,'opencode.mjs'),'run','--agent','probe','--standalone','--model','local/qwen3-0.6b-test','--title','Local CPU model connectivity test','--format','json','Reply with the single word OK. Do not use any tools.'],{
 cwd:fixture,env,stdio:['ignore','pipe','pipe']
});
let output='';
for (const stream of [child.stdout,child.stderr]) stream.on('data',chunk=>{output+=chunk;writeFileSync(log,output);});
let expired=false;
const timer=setTimeout(()=>{expired=true;child.kill('SIGTERM');setTimeout(()=>child.kill('SIGKILL'),5000).unref();},180000);
const code=await new Promise(resolve=>child.on('close',code=>resolve(code)));
clearTimeout(timer);
writeFileSync(resolve(root,'local-model.exit'),String(expired?124:(code===0&&!output.split('\n').some(line=>{try{const event=JSON.parse(line);return event.type==='text'&&/\bOK\b/.test(event.part?.text??'');}catch{return false;}})?2:code))+'\n');
console.log(output);
const valid = output.split('\n').some(line=>{try{const event=JSON.parse(line);return event.type==='text'&&/\bOK\b/.test(event.part?.text??'');}catch{return false;}});
process.exitCode=expired?124:(code===0&&!valid?2:(code??1));

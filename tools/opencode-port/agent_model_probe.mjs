// Bounded native OpenCode test. The working directory contains synthetic data only.
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
const root = resolve(process.argv[2] ?? '.');
const fixture = resolve(root, 'agent-fixture');
mkdirSync(fixture, {recursive:true});
writeFileSync(resolve(fixture,'README.md'), '# Synthetic OpenCode connectivity test\nNo private source files.\n');
writeFileSync(resolve(fixture,'opencode.json'), JSON.stringify({
 model:'local/qwen3-0.6b-test', update:'disable', share:'disabled', snapshots:false,formatter:false,lsp:false,
 permissions:[{action:'*',resource:'*',effect:'deny'},{action:'read',resource:'*.mjs',effect:'allow'},{action:'edit',resource:'add.mjs',effect:'allow'},{action:'shell',resource:'node test.mjs',effect:'allow'}],
 providers:{local:{name:'Isolated local CPU model',package:'@opencode/ai/providers/openai-compatible',settings:{baseURL:process.platform==='haiku'?'http://10.0.2.2:18082/v1':'http://127.0.0.1:18082/v1',apiKey:'',provider:'local'},models:{'qwen3-0.6b-test':{name:'Qwen3 0.6B CPU test',capabilities:{tools:true,input:['text'],output:['text']},limit:{context:8192,output:256},body:{temperature:0,max_tokens:256,chat_template_kwargs:{enable_thinking:false}}}}}},
 agents:{probe:{mode:'primary',model:'local/qwen3-0.6b-test',system:'You are a coding assistant. Use the read, write or edit, and shell tools to fix the requested file and run its test. Work only in the current fixture directory.',steps:8},build:{model:'local/qwen3-0.6b-test',steps:8},title:{model:'local/qwen3-0.6b-test'},summary:{model:'local/qwen3-0.6b-test'}}
}));
writeFileSync(resolve(fixture,'add.mjs'), 'export const add = (a, b) => a - b;\n');
writeFileSync(resolve(fixture,'test.mjs'), "import { add } from './add.mjs'; import assert from 'node:assert/strict'; assert.equal(add(2,3),5); assert.equal(add(-2,3),1); console.log('AGENT_TEST_PASS');\n");
const log = resolve(root,'agent-model.log');
writeFileSync(log,'');
const env = Object.fromEntries(Object.entries(process.env).filter(([name]) => /^(PATH|XDG_(DATA|CONFIG|CACHE|STATE)_HOME|LANG|LC_[A-Z_]+|SSL_CERT_FILE|SSL_CERT_DIR)$/.test(name)));
env.OPENCODE_PRINT_LOGS = '1';
const child = spawn(process.execPath,[resolve(root,'opencode.mjs'),'run','--agent','probe','--standalone','--model','local/qwen3-0.6b-test','--title','Local CPU model editing test','--format','json','Read add.mjs, fix add to return a + b using write or edit, then run node test.mjs using shell. Do not edit test.mjs. After the test passes, reply OK.'],{
 cwd:fixture,env,stdio:['ignore','pipe','pipe']
});
let output='';
const progress=setInterval(()=>{if(process.platform==='haiku')fetch('http://10.0.2.2:18080/opencode-guest-agent-model-progress.log',{method:'PUT',body:output,signal:AbortSignal.timeout(5000)}).catch(()=>{});},10000);
for (const stream of [child.stdout,child.stderr]) stream.on('data',chunk=>{output+=chunk;writeFileSync(log,output);});
let expired=false;
const timer=setTimeout(()=>{expired=true;child.kill('SIGTERM');setTimeout(()=>child.kill('SIGKILL'),5000).unref();},300000);
const code=await new Promise(resolve=>{child.on('error',error=>{output+=`spawn error: ${error.message}\n`;writeFileSync(log,output);resolve(127);});child.on('close',code=>resolve(code));});
clearTimeout(timer);clearInterval(progress);
const valid = /a\s*\+\s*b/.test(readFileSync(resolve(fixture,'add.mjs'),'utf8')) && output.split('\n').some(line=>{try{const event=JSON.parse(line);return event.type==='tool_use'&&event.part?.tool==='shell'&&JSON.stringify(event).includes('AGENT_TEST_PASS');}catch{return false;}});
const result=expired?124:(code===0&&!valid?2:(code??1));
writeFileSync(resolve(root,'agent-model.exit'),String(result)+'\n');
console.log(output);
process.exitCode=result;

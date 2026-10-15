// Bounded native OpenCode test. The working directory contains synthetic data only.
import { spawn, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
const root = resolve(process.argv[2] ?? '/boot/home/opencode-acceptance');
const steps=Number(process.env.OPENCODE_TEST_STEPS??8);
if(!Number.isInteger(steps)||steps<4||steps>16)throw new Error('OPENCODE_TEST_STEPS must be an integer from 4 to 16');
const runID='coding-'+Date.now();
const fixture=resolve(root,runID,'agent-fixture');
mkdirSync(fixture, {recursive:true});
writeFileSync(resolve(fixture,'README.md'), '# Synthetic OpenCode connectivity test\nNo private source files.\n');
writeFileSync(resolve(fixture,'opencode.json'), JSON.stringify({
 model:'local/haiku-qwen17', update:'disable', share:'disabled', snapshots:false,formatter:false,lsp:false,
 permissions:[{action:'*',resource:'*',effect:'deny'},{action:'read',resource:'*.mjs',effect:'allow'},{action:'edit',resource:'add.mjs',effect:'allow'},{action:'shell',resource:'node test.mjs',effect:'allow'}],
 providers:{local:{name:'Native Haiku CPU',package:'@opencode/ai/providers/openai-compatible',settings:{baseURL:'http://127.0.0.1:18081/v1',apiKey:'',provider:'local',headerTimeout:1800000,timeout:1800000,chunkTimeout:900000},models:{'haiku-qwen17':{name:'Qwen3 1.7B CPU test',capabilities:{tools:true,input:['text'],output:['text']},limit:{context:4096,output:256},body:{temperature:0,max_tokens:256,chat_template_kwargs:{enable_thinking:false}}}}}},
 agents:{probe:{mode:'primary',model:'local/haiku-qwen17',system:'You are a coding assistant. Use the read, write or edit, and shell tools to fix the requested file and run its test. Work only in the current fixture directory.',steps},build:{model:'local/haiku-qwen17',steps},title:{model:'local/haiku-qwen17'},summary:{model:'local/haiku-qwen17'}}
}));
writeFileSync(resolve(fixture,'add.mjs'), 'export const add = (a, b) => a - b;\n');
writeFileSync(resolve(fixture,'test.mjs'), "import { add } from './add.mjs'; import assert from 'node:assert/strict'; assert.equal(add(2,3),5); assert.equal(add(-2,3),1); console.log('AGENT_TEST_PASS');\n");
const testHash=createHash('sha256').update(readFileSync(resolve(fixture,'test.mjs'))).digest('hex');
const log=resolve(root,'agent-model.log');
writeFileSync(log,'');
writeFileSync(resolve(root,'coding-outcome.json'),JSON.stringify({status:'running',started:new Date().toISOString(),model:'haiku-qwen17',port_root:process.env.OPENCODE_TEST_PORT_ROOT||'http-port/opencode'},null,2)+'\n');
const env = Object.fromEntries(Object.entries(process.env).filter(([name]) => /^(PATH|XDG_(DATA|CONFIG|CACHE|STATE)_HOME|LANG|LC_[A-Z_]+|SSL_CERT_FILE|SSL_CERT_DIR)$/.test(name)));
env.OPENCODE_PRINT_LOGS = '1';
env.OPENCODE_DISABLE_MODELS_FETCH='1';
for(const name of ['DATA','CONFIG','CACHE','STATE'])env['XDG_'+name+'_HOME']=resolve(root,runID,'state',name.toLowerCase());
const child = spawn(resolve(root,process.env.OPENCODE_TEST_PORT_ROOT||'http-port/opencode'),['run','--agent','probe','--standalone','--model','local/haiku-qwen17','--title','Local CPU model editing test','--format','json','Read add.mjs, fix add to return a + b using write or edit, then run node test.mjs using shell. Do not edit test.mjs. After the test passes, reply OK.'],{
 cwd:fixture,env,stdio:['ignore','pipe','pipe']
});
let output='';
const progress=setInterval(()=>{if(process.platform==='haiku')fetch('http://10.0.2.2:18080/native-coding-progress.log',{method:'PUT',body:output,signal:AbortSignal.timeout(5000)}).catch(()=>{});},10000);
for (const stream of [child.stdout,child.stderr]) stream.on('data',chunk=>{output+=chunk;writeFileSync(log,output);});
let expired=false;
const timer=setTimeout(()=>{expired=true;child.kill('SIGTERM');setTimeout(()=>child.kill('SIGKILL'),5000).unref();},2700000);
let launchError;
const code=await new Promise(resolve=>{child.once('error',error=>{launchError=String(error);resolve(1);});child.once('close',code=>resolve(code));});
clearTimeout(timer);clearInterval(progress);
const valid = testHash===createHash('sha256').update(readFileSync(resolve(fixture,'test.mjs'))).digest('hex') && /a\s*\+\s*b/.test(readFileSync(resolve(fixture,'add.mjs'),'utf8')) && output.split('\n').some(line=>{try{const event=JSON.parse(line);return event.type==='tool_use'&&event.part?.tool==='shell'&&event.part.state?.status==='completed'&&event.part.state.input?.command?.trim()==='node test.mjs'&&String(event.part.state.output).includes('AGENT_TEST_PASS');}catch{return false;}});
const unchanged=testHash===createHash('sha256').update(readFileSync(resolve(fixture,'test.mjs'))).digest('hex');
const independent=unchanged?spawnSync(process.execPath,['test.mjs'],{cwd:fixture,encoding:'utf8',timeout:10000}):undefined;
const result=expired?124:(code??1);
writeFileSync(resolve(root,'coding-outcome.json'),JSON.stringify({exit:result,semantic_pass:valid&&independent?.status===0,expired,steps,fixture,launch_error:launchError,test_unchanged:unchanged,independent_test_pass:independent?.status===0,independent_test_output:independent?.stdout??'',edited_source:readFileSync(resolve(fixture,'add.mjs'),'utf8')},null,2)+'\n');
if(process.platform==='haiku')for(const name of ['agent-model.log','coding-outcome.json'])await fetch('http://10.0.2.2:18080/native-'+name,{method:'PUT',body:readFileSync(resolve(root,name)),signal:AbortSignal.timeout(10000)}).catch(()=>{});
writeFileSync(resolve(root,'agent-model.exit'),String(result)+'\n');
console.log(output);
process.exitCode=result;

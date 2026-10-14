// Bounded native OpenCode test. The working directory contains synthetic data only.
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
const root = resolve(process.argv[2] ?? '.');
const fixture = resolve(root, 'free-fixture');
mkdirSync(fixture, {recursive:true});
writeFileSync(resolve(fixture,'README.md'), '# Synthetic OpenCode connectivity test\nNo private source files.\n');
writeFileSync(resolve(fixture,'opencode.json'), JSON.stringify({
 model:'opencode/big-pickle', update:'disable', share:'disabled', snapshots:false,
 permissions:[{action:'*',resource:'*',effect:'deny'}],
 agents:{build:{model:'opencode/big-pickle',steps:1},title:{model:'opencode/big-pickle'},summary:{model:'opencode/big-pickle'}}
}));
const log = resolve(root,'free-model.log');
writeFileSync(log,'');
const env = Object.fromEntries(Object.entries(process.env).filter(([name]) => /^(PATH|XDG_(DATA|CONFIG|CACHE|STATE)_HOME|LANG|LC_[A-Z_]+|SSL_CERT_FILE|SSL_CERT_DIR)$/.test(name)));
env.OPENCODE_PRINT_LOGS = '1';
const child = spawn(process.execPath,[resolve(root,'opencode.mjs'),'run','--standalone','--model','opencode/big-pickle','--title','Free model connectivity test','--format','json','Reply with the single word OK. Do not use any tools.'],{
 cwd:fixture,env,stdio:['ignore','pipe','pipe']
});
let output='';
for (const stream of [child.stdout,child.stderr]) stream.on('data',chunk=>{output+=chunk;writeFileSync(log,output);});
let expired=false;
const timer=setTimeout(()=>{expired=true;child.kill('SIGTERM');setTimeout(()=>child.kill('SIGKILL'),5000).unref();},180000);
const code=await new Promise(resolve=>child.on('close',code=>resolve(code)));
clearTimeout(timer);
writeFileSync(resolve(root,'free-model.exit'),String(expired?124:code)+'\n');
console.log(output);
process.exitCode=expired?124:(code??1);

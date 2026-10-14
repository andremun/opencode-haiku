'use strict';
// Fresh, deterministic, sequential requests. No prior conversation is reused.
const fs=require('node:fs');
const endpoint=process.argv[2]||'http://127.0.0.1:18081';
const output=process.argv[3]||'/boot/home/opencode-acceptance/inference-compare.json';
const prompts=['Reply with the single word OK.','Write a Python function add(a, b) that returns their sum. Output only the code.','What is 7 plus 5? Reply with only the number.'];
(async()=>{
 const result={platform:process.platform,endpoint,requests:[]};
 for(const prompt of prompts){
  const body={model:'haiku-qwen17',messages:[{role:'user',content:prompt}],max_tokens:64,temperature:0,seed:1234,chat_template_kwargs:{enable_thinking:false}};
  const start=Date.now();
  try{
   const response=await fetch(endpoint+'/v1/chat/completions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(1800000)});
   const text=await response.text();
   result.requests.push({body,status:response.status,elapsed_ms:Date.now()-start,response:JSON.parse(text)});
  }catch(error){result.requests.push({body,elapsed_ms:Date.now()-start,error:String(error)});}
  fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
  if(process.platform==='haiku') await fetch('http://10.0.2.2:18080/inference-compare-haiku.json',{method:'PUT',body:JSON.stringify(result,null,2),signal:AbortSignal.timeout(10000)}).catch(()=>{});
 }
})();

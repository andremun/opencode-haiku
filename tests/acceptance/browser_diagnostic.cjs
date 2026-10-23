// Copyright (c) 2026 Mario Andres Munoz
// Distributed under the terms of the MIT License. See LICENSE.
'use strict';
// Temporary localhost diagnostic: compares WebPositive fetch/XHR on the same origin.
const http=require('node:http'),fs=require('node:fs');
const password=fs.readFileSync('/boot/home/opencode-acceptance/gui-server.log','utf8').split('\n').find(x=>x.startsWith('server password '))?.slice(16);
const html=`<!doctype html><meta charset="utf-8"><pre id="out">checking</pre><script>
(async function(){var result={};var auth='Basic '+btoa('opencode:'+${JSON.stringify(password)});
try{var r=await fetch('/api/info',{headers:{Authorization:auth}});result.fetch={status:r.status,body:await r.text()};}catch(e){result.fetch={error:e.message,stack:e.stack};}
try{var x=await new Promise(function(resolve,reject){var q=new XMLHttpRequest();q.open('GET','/api/info');q.setRequestHeader('Authorization',auth);q.onload=function(){resolve({status:q.status,body:q.responseText});};q.onerror=function(){reject(Error('XHR failed'));};q.send();});result.xhr=x;}catch(e){result.xhr={error:e.message};}
document.getElementById('out').textContent=JSON.stringify(result,null,2);var q=new XMLHttpRequest();q.open('PUT','/diagnostic-result');q.send(JSON.stringify(result,null,2));})();</script>`;
http.createServer((req,res)=>{
 if(req.url==='/diagnostic'){res.setHeader('Content-Type','text/html');res.end(html);return;}
 if(req.url==='/diagnostic-result'&&req.method==='PUT'){
  let body='';req.on('data',d=>{body+=d;if(body.length>65536)req.destroy();});req.on('end',()=>{fs.writeFileSync('/boot/home/opencode-acceptance/browser-diagnostic.json',body);res.end('saved');});return;
 }
 const proxy=http.request({hostname:'127.0.0.1',port:18083,path:req.url,method:req.method,headers:{...req.headers,host:'127.0.0.1:18083'}},incoming=>{res.writeHead(incoming.statusCode,incoming.headers);incoming.pipe(res);});proxy.on('error',e=>{res.writeHead(502);res.end(e.message);});req.pipe(proxy);
}).listen(18084,'127.0.0.1');

'use strict';
const {registerHooks}=require('node:module');
const {pathToFileURL}=require('node:url');
const path=require('node:path');
const target=pathToFileURL(path.join(__dirname,'haiku-ffi.cjs')).href;
registerHooks({resolve(specifier,context,nextResolve){return specifier==='node:ffi'?{url:target,shortCircuit:true}:nextResolve(specifier,context);}});

if(process.platform==='haiku')require('./haiku-watch.cjs').install();

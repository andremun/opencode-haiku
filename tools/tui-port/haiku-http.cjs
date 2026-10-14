'use strict';
// Preserve upstream Bun's explicit timeout:false for long-lived CLI waits.
exports.install=function(){
 const {getGlobalDispatcher}=require('./undici');
 const base=getGlobalDispatcher(),original=globalThis.fetch;
 const unlimited={dispatch(options,handler){return base.dispatch({...options,headersTimeout:0,bodyTimeout:0},handler);}};
 globalThis.fetch=function(input,options){
  return original(input,options?.timeout===false?{...options,dispatcher:options.dispatcher??unlimited}:options);
 };
 return ()=>{globalThis.fetch=original;};
};

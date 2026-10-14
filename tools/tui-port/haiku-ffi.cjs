// Node FFI compatibility facade backed by the maintained Koffi N-API module.
// Only OpenTUI's portable signature subset is supported; callbacks are synchronous.
'use strict';
// Servers/help import the facade but do not perform FFI. Load the native addon
// only for the first actual operation, keeping unused addon state out of children.
let native;
const koffi = new Proxy({}, {get(_target,key) {native ??= require(process.env.OPENCODE_HAIKU_KOFFI);return native[key];}});
const kinds = Object.freeze({char:'char',i8:'int8_t',u8:'uint8_t',i16:'int16_t',u16:'uint16_t',i32:'int32_t',u32:'uint32_t',i64:'int64_t',u64:'uint64_t',f32:'float',f64:'double',bool:'bool',pointer:'void *',buffer:'void *',string:'str',void:'void'});
function type(name) { if (!(name in kinds)) throw new TypeError('Unsupported FFI type: '+name); return kinds[name]; }
function normalize(value, kind) {
 if (kind==='pointer' || kind==='buffer') {
  if (kind==='buffer' && !ArrayBuffer.isView(value)) throw new TypeError('buffer requires an ArrayBufferView');
  if (value instanceof ArrayBuffer) return new Uint8Array(value);
  if (ArrayBuffer.isView(value)) return new Uint8Array(value.buffer,value.byteOffset,value.byteLength);
  if (value===null || value===0 || value===0n) return null;
  if (typeof value==='number') {if(!Number.isSafeInteger(value)||value<0)throw new RangeError('Invalid pointer');return BigInt(value);}
  if (typeof value==='bigint' && value>=0n) return value;
  throw new TypeError('Invalid pointer argument');
 }
 if (kind==='bool') return Boolean(value);
 return value;
}
function result(value, kind) {
 if(kind==='pointer') return value==null?0n:typeof value==='bigint'?value:koffi.address(value);
 if(kind==='i64'||kind==='u64') return BigInt(value);
 if(kind==='bool') return value?1:0;
 return value;
}
exports.suffix = 'so';
exports.getRawPointer = function(source) {
 if (!(source instanceof ArrayBuffer)) throw new TypeError('getRawPointer requires ArrayBuffer');
 return source.byteLength===0?0n:koffi.address(new Uint8Array(source));
};
exports.toArrayBuffer = function(pointer,length,copy=false) {
 if(!Number.isSafeInteger(length)||length<0||length>0x7fffffff)throw new RangeError('Invalid memory view length');
 if(length===0)return new ArrayBuffer(0);
 if(typeof pointer!=='bigint'||pointer<=0n)throw new RangeError('Invalid native address');
 const view=koffi.view(pointer,length);
 return copy?new Uint8Array(view).slice().buffer:view;
};
exports.dlopen = function(path,definitions) {
 const library=koffi.load(path);
 const callbacks=new Map();
 let closed=false;
 const alive=()=>{if(closed)throw new Error('FFI library is closed');};
 const functions={};
 try {
  for(const [name,signature] of Object.entries(definitions)) {
   const args=signature.arguments;
   const fn=library.func(name,type(signature.return),args.map(type));
   functions[name]=(...values)=>{alive();if(values.length!==args.length)throw new TypeError('Wrong FFI argument count');return result(fn(...values.map((value,index)=>normalize(value,args[index]))),signature.return);};
  }
 } catch(error) {library.unload();throw error;}
 return {functions,lib:{
  registerCallback(signature,callback) {
   alive();const proto=koffi.proto(type(signature.return),signature.arguments.map(type));
   const handle=koffi.register((...values)=>callback(...values.map((value,index)=>result(value,signature.arguments[index]))),koffi.pointer(proto));
   const address=koffi.address(handle);callbacks.set(address,handle);return address;
  },
  unregisterCallback(address) {alive();const handle=callbacks.get(address);if(!handle)throw new RangeError('Unknown callback');koffi.unregister(handle);callbacks.delete(address);},
  close() {if(closed)return;closed=true;try{library.unload();}finally{for(const handle of callbacks.values())koffi.unregister(handle);callbacks.clear();}}
 }};
};

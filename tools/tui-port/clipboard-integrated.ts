import {createHostClipboard} from '../../source/opentui-6f0efd3330978d696b42db3d7d95d2042008312b/packages/core/src/lib/clipboard.ts';
import assert from 'node:assert/strict';
const clipboard=createHostClipboard({timeoutMs:10000});
const previous=await clipboard.read({preferredTypes:['text/plain']});
try {
 assert.equal((await clipboard.writeText('Integrated Haiku clipboard\n')).status,'written');
 const result=await clipboard.read({preferredTypes:['text/plain']});assert.equal(result.status,'read');
 if(result.status==='read')assert.equal(Buffer.from(result.representation.bytes).toString(),'Integrated Haiku clipboard\n');
 console.log('INTEGRATED_CLIPBOARD_PASS: real OpenTUI factory write/read');
}finally{
 if(previous.status==='read')await clipboard.writeText(Buffer.from(previous.representation.bytes).toString());
 else if(previous.status==='empty')await clipboard.clear();
 await clipboard.dispose();
}

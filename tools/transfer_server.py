#!/usr/bin/env python3
"""Localhost transfer service. Serves only share/ and accepts bounded named results."""
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import re,json,time,os,tempfile
ROOT=Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**k):super().__init__(*a,directory=str(ROOT/'share'),**k)
    def do_PUT(self):
        name=self.path.lstrip('/')
        if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]*',name):self.send_error(400);return
        try:n=int(self.headers.get('Content-Length','-1'))
        except ValueError:self.send_error(400);return
        if not 0<=n<=64*1024*1024:self.send_error(413);return
        data=self.rfile.read(n)
        if len(data)!=n:self.send_error(400,'Incomplete upload');return
        out=ROOT/('logs' if name.startswith('job') else 'results');out.mkdir(exist_ok=True)
        # Readers wait on the final name: never expose a partially written result.
        temporary=None
        try:
            with tempfile.NamedTemporaryFile(dir=out,prefix='.upload-',delete=False) as target:
                temporary=Path(target.name);target.write(data)
            os.replace(temporary,out/name)
        finally:
            if temporary is not None:temporary.unlink(missing_ok=True)
        self.send_response(201);self.end_headers()
    def log_message(self,fmt,*args):print(time.strftime('%H:%M:%S'),fmt%args,flush=True)
if __name__=='__main__':
    ThreadingHTTPServer(('127.0.0.1',18080),Handler).serve_forever()

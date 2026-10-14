#!/usr/bin/env python3
"""Bounded loopback diagnostic relay for our own CPU test server only."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import http.client,json
ROOT=Path(__file__).resolve().parents[2]
class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        count=int(self.headers.get('Content-Length','0'))
        if not 0<count<=1024*1024:self.send_error(413);return
        payload=self.rfile.read(count)
        (ROOT/'results/opencode-local-wire-request.json').write_text(json.dumps(json.loads(payload),indent=2)+'\n')
        connection=http.client.HTTPConnection('127.0.0.1',18082,timeout=120)
        connection.request('POST',self.path,body=payload,headers={'Content-Type':'application/json'})
        response=connection.getresponse()
        self.send_response(response.status)
        self.send_header('Content-Type',response.getheader('Content-Type','application/json'))
        self.send_header('Connection','close');self.end_headers()
        data=b''
        while chunk:=response.read(1024):
            data+=chunk;self.wfile.write(chunk);self.wfile.flush()
        (ROOT/'results/opencode-local-wire-response.txt').write_bytes(data)
        connection.close()
    def log_message(self,*args):pass
ThreadingHTTPServer(('127.0.0.1',18083),Handler).serve_forever()

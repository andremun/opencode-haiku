#!/usr/bin/env python3
"""Host-only regression controls. No VM, model, Rust compiler or existing service used."""
from pathlib import Path
import http.client, importlib.util, json, os, shutil, subprocess, tempfile, threading, time, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which('node') or '/home/unimelb.edu.au/mariom1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'

class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='t7610-runner-test-')
        self.root = Path(self.tmp.name)
        self.bin = self.root/'bin'; self.bin.mkdir()
        self.env = {**os.environ, 'PATH':str(self.bin)+os.pathsep+os.environ['PATH']}
    def tearDown(self): self.tmp.cleanup()
    def stub(self,name,body):
        p=self.bin/name;p.write_text('#!/bin/sh\n'+body+'\n');p.chmod(0o755)
    def run_script(self,name):
        return subprocess.run(['sh',str(ROOT/name)],env=self.env,capture_output=True,text=True,timeout=10)
    def test_guest_failure_reaches_host_and_missing_status_rejected(self):
        tools=self.root/'tools';tools.mkdir();shutil.copy(ROOT/'tools/job.sh',tools/'job.sh')
        for number,trailer,expected in [(1,'exit=7',7),(2,'exit=0',0),(3,'incomplete',125)]:
            proc=subprocess.Popen(['sh',str(tools/'job.sh'),str(number),'exit 7','5'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            deadline=time.monotonic()+4
            request=self.root/'share'/f'job{number}.sh'
            while not request.exists() and time.monotonic()<deadline:time.sleep(.01)
            self.assertTrue(request.exists())
            # A complete result is published atomically, just as the transfer server now does.
            pending=self.root/'logs'/'pending';pending.write_text('guest output\n'+trailer+'\n')
            pending.replace(self.root/'logs'/f'job{number}.out')
            out,err=proc.communicate(timeout=7)
            self.assertEqual(proc.returncode,expected,(out,err));self.assertIn('guest output',out)
        reused=subprocess.run(['sh',str(tools/'job.sh'),'1','true'],capture_output=True,text=True)
        self.assertEqual(reused.returncode,2)
        timeout=subprocess.run(['sh',str(tools/'job.sh'),'4','sleep 100','1'],capture_output=True,text=True,timeout=5)
        self.assertEqual(timeout.returncode,124);self.assertIn('not been cancelled',timeout.stderr)
    def test_cargo_test_and_clippy_failures_are_not_hidden_by_tail(self):
        work=self.root/'native';(work/'pty').mkdir(parents=True)
        self.env['OPENCODE_NATIVE_WORK']=str(work)
        self.stub('cargo','''case "$1" in
 build) mkdir -p "$CARGO_TARGET_DIR/debug"; echo binary > "$CARGO_TARGET_DIR/debug/opencode-pty";;
 test) echo 'TEST_OUTPUT'; [ "${FAIL_CARGO:-}" != test ] || exit 9;;
 clippy) echo 'CLIPPY_OUTPUT'; [ "${FAIL_CARGO:-}" != clippy ] || exit 11;;
esac
exit 0''')
        self.stub('strip','exit 0');self.stub('rustc','echo rust-test-stub')
        for failed,expected in [('test',9),('clippy',11),('',0)]:
            self.env['FAIL_CARGO']=failed
            result=self.run_script('tools/kvm-run/pty.sh')
            self.assertEqual(result.returncode,expected,result.stdout+result.stderr)
            self.assertEqual('PTY-DONE' in result.stdout,expected==0)
            if failed:self.assertFalse((work/'opencode-pty-bin').exists())
    def test_api_failure_is_not_replaced_by_successful_upload(self):
        self.env['OPENCODE_ACCEPTANCE_WORK']=str(self.root/'acceptance')
        self.env['OPENCODE_PORT_ROOT']=str(self.root/'runtime')
        self.stub('curl','''while [ "$#" -gt 0 ]; do
 if [ "$1" = -o ]; then shift; [ "$1" = /dev/null ] || : > "$1"; fi
 shift
done
exit 0''')
        self.stub('node','echo API_PROBE; case "$1" in persistent-terminal-api.mjs) exit "${PROBE_EXIT:-0}";; esac')
        for code,expected in [('17',1),('0',0)]:
            self.env['PROBE_EXIT']=code;result=self.run_script('tools/kvm-run/api.sh')
            self.assertEqual(result.returncode,expected,result.stdout+result.stderr)
            self.assertIn('persistent-terminal-api exit='+code,result.stdout)
    def test_services_refuse_existing_listener_before_writing_configuration(self):
        self.stub('curl','exit 0')
        result=self.run_script('tools/kvm-run/services.sh')
        self.assertEqual(result.returncode,1)
        self.assertIn('refusing duplicate services',result.stderr)
    def test_transfer_publishes_only_complete_results(self):
        spec=importlib.util.spec_from_file_location('t7610_transfer',ROOT/'tools/transfer_server.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.ROOT=self.root
        (self.root/'share').mkdir();(self.root/'logs').mkdir()
        destination=self.root/'logs/job1.out';destination.write_bytes(b'old complete output')
        payload=b'x'*200000+b'\nexit=7\n';observations=[]
        original_replace=os.replace
        def replace(source,target):
            observations.append((Path(target).read_bytes(),Path(source).read_bytes()))
            original_replace(source,target)
        server=ThreadingHTTPServer(('127.0.0.1',0),module.Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with patch.object(module.os,'replace',side_effect=replace):
                conn=http.client.HTTPConnection(*server.server_address,timeout=3)
                conn.request('PUT','/job1.out',body=payload)
                response=conn.getresponse();response.read();self.assertEqual(response.status,201);conn.close()
            self.assertEqual(observations,[(b'old complete output',payload)])
            self.assertEqual(destination.read_bytes(),payload)
        finally:server.shutdown();server.server_close();thread.join()
    def test_http_error_and_invalid_completion_fail_the_inference_runner(self):
        status=200;body={'choices':[{'message':{'content':'OK'}}]}
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(status);self.end_headers();self.wfile.write(json.dumps(body).encode())
            def log_message(self,*args):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            endpoint='http://127.0.0.1:'+str(server.server_port)
            for status,body,expected in [(500,{'error':'injected'},1),(200,{},1),(200,{'choices':[{'message':{'content':'OK'}}]},0)]:
                output=self.root/'inference.json'
                result=subprocess.run([NODE,str(ROOT/'tools/tui-port/inference-compare.cjs'),endpoint,str(output)],capture_output=True,text=True,timeout=8)
                self.assertEqual(result.returncode,expected,result.stderr)
                self.assertEqual(len(json.loads(output.read_text())['requests']),3)
        finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__': unittest.main(verbosity=2)

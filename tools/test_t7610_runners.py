#!/usr/bin/env python3
"""Host-only regression controls. No VM, model, Rust compiler or existing service used."""
from pathlib import Path
import http.client, importlib.util, json, os, shutil, subprocess, tempfile, threading, time, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
NODE = os.environ.get('NODE') or shutil.which('node')
if NODE is None:raise SystemExit('Node.js is required: put node on PATH or set NODE')

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
        self.stub('uname','echo Haiku')
        self.stub('curl','exit 0')
        result=self.run_script('tools/kvm-run/services.sh')
        self.assertEqual(result.returncode,1)
        self.assertIn('refusing duplicate services',result.stderr)
    def test_coding_acceptance_requires_agent_test_and_an_unchanged_passing_fixture(self):
        for index,(reported,tampered,expected) in enumerate([(False,False,False),(True,False,True),(True,True,False)]):
            root=self.root/('coding-'+str(index));root.mkdir()
            launcher=self.root/('fake-opencode-'+str(index))
            launcher.write_text('#!'+NODE+'\n'+"const fs=require('node:fs');fs.writeFileSync('add.mjs','export const add=(a,b)=>a+b;');"+
                ("fs.writeFileSync('test.mjs','console.log(\"AGENT_TEST_PASS\")');" if tampered else '')+
                ("console.log(JSON.stringify({type:'tool_use',part:{tool:'shell',state:{status:'completed',input:{command:'node test.mjs'},output:'AGENT_TEST_PASS'}}}));" if reported else ''))
            launcher.chmod(0o755)
            result=subprocess.run([NODE,str(ROOT/'tools/tui-port/coding-workflow.mjs'),str(root)],env={**os.environ,'OPENCODE_TEST_PORT_ROOT':str(launcher)},capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            outcome=json.loads((root/'coding-outcome.json').read_text())
            self.assertEqual(outcome['semantic_pass'],expected)
            self.assertEqual(outcome['test_unchanged'],not tampered)
            self.assertEqual(outcome['steps'],8)
            if not tampered:self.assertTrue(outcome['independent_test_pass'])
    def test_cpu_experiments_refuse_the_host_platform(self):
        if os.uname().sysname=='Haiku':self.skipTest('This guard control is intended for the Linux host')
        for name in ['build-cpu-profile.sh','benchmark-cpu.sh','services.sh']:
            result=self.run_script('tools/kvm-run/'+name)
            self.assertEqual(result.returncode,2,result.stderr)
            self.assertIn('Haiku guest',result.stderr)
    def test_missing_coding_launcher_records_a_terminal_error(self):
        root=self.root/'missing-launcher';root.mkdir()
        result=subprocess.run([NODE,str(ROOT/'tools/tui-port/coding-workflow.mjs'),str(root)],env={**os.environ,'OPENCODE_TEST_PORT_ROOT':str(self.root/'does-not-exist')},capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,1,result.stderr)
        outcome=json.loads((root/'coding-outcome.json').read_text())
        self.assertIn('ENOENT',outcome['launch_error'])
        self.assertFalse(outcome['semantic_pass'])
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

    def test_transfer_rejects_dot_names(self):
        spec=importlib.util.spec_from_file_location('t7610_transfer_names',ROOT/'tools/transfer_server.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.ROOT=self.root;(self.root/'share').mkdir()
        server=ThreadingHTTPServer(('127.0.0.1',0),module.Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            for name,expected in [('..',400),('.',400),('.hidden',400),('ok-name.txt',201)]:
                conn=http.client.HTTPConnection(*server.server_address,timeout=3)
                conn.request('PUT','/'+name,body=b'x');response=conn.getresponse();response.read();conn.close()
                self.assertEqual(response.status,expected,name)
            self.assertFalse(any((self.root/'results').glob('.*')) if (self.root/'results').exists() else False)
        finally:server.shutdown();server.server_close();thread.join()
    def test_stage_reports_a_missing_runtime_archive(self):
        # Run the staging helper from a copy of the repo layout with a manifest but no archive.
        work=self.root/'stage';(work/'tools').mkdir(parents=True);(work/'results').mkdir()
        shutil.copy(ROOT/'tools/stage_t7610.py',work/'tools/stage_t7610.py')
        (work/'results/opencode-tui-package.json').write_text(json.dumps({'archive':'missing.tar.gz','sha256':'0'*64}))
        subprocess.run(['git','init','-q'],cwd=work,check=True)
        subprocess.run(['git','add','-A'],cwd=work,check=True)
        subprocess.run(['git','-c','user.name=t','-c','user.email=t@example.invalid','commit','-q','-m','fixture'],cwd=work,check=True)
        result=subprocess.run(['python3',str(work/'tools/stage_t7610.py')],cwd=work,capture_output=True,text=True,timeout=10)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Runtime archive missing',result.stderr)
        self.assertNotIn('Traceback',result.stderr)

    def test_cloud_task_fixture_and_acceptance_controls(self):
        ref=ROOT/'examples/cloud-task/reference/src'
        scenarios=[('solved',True,False,True),('no-test-run',False,False,False),('tampered-tests',True,True,False),('unsolved',None,False,False)]
        for name,ran,tamper,expected in scenarios:
            out=self.root/('cloud-'+name);out.mkdir()
            body=("const fs=require('node:fs');"+
                  ("fs.cpSync(process.env.LC_REF,'src',{recursive:true});" if ran is not None else '')+
                  ("fs.appendFileSync('test/csv.test.mjs','//x');" if tamper else '')+
                  ("console.log(JSON.stringify({type:'tool_use',part:{tool:'shell',state:{status:'completed',input:{command:'node --test'},output:'ok'}}}));" if ran else ''))
            if name=='no-test-run':body=body.replace("console.log","//")
            launcher=self.root/('cloud-launcher-'+name);launcher.write_text('#!'+NODE+'\n'+body);launcher.chmod(0o755)
            result=subprocess.run([NODE,str(ROOT/'tools/tui-port/cloud-coding-task.mjs'),str(out)],env={**os.environ,'LC_REF':str(ref),'OPENCODE_TEST_PORT_ROOT':str(launcher),'OPENCODE_CLOUD_MODEL':'opencode/test-model'},capture_output=True,text=True,timeout=60)
            outcome=json.loads(next((out/d/'outcome.json' for d in os.listdir(out))).read_text())
            self.assertEqual(outcome['semantic_pass'],expected,(name,result.stdout,result.stderr))
            if name=='solved':self.assertEqual(outcome['independent_tests'],{'tests':15,'pass':15,'fail':0})
            if name=='unsolved':self.assertEqual(outcome['independent_tests']['fail'],12)
    def test_cloud_task_requires_a_model_and_launcher(self):
        result=subprocess.run([NODE,str(ROOT/'tools/tui-port/cloud-coding-task.mjs'),str(self.root)],env={k:v for k,v in os.environ.items() if not k.startswith('OPENCODE_')},capture_output=True,text=True,timeout=20)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('OPENCODE_CLOUD_MODEL',result.stderr)

if __name__=='__main__': unittest.main(verbosity=2)

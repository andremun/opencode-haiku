#!/usr/bin/env python3
"""Offline controls only: fake model clients, fake service commands, /tmp files.

The Kepler card-runner controls moved to llm-server research/kepler-clang/tools/test_card_runners.py
on 2026-10-23, together with the runners.
"""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
NODE = os.environ.get('NODE') or shutil.which('node')


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='opencode-review-controls-')
        self.work = Path(self.tmp.name)
        self.bin = self.work / 'bin'
        self.bin.mkdir()
        self.env = {**os.environ, 'PATH': str(self.bin) + ':' + os.environ['PATH'], 'HOME': str(self.work)}

    def tearDown(self):
        self.tmp.cleanup()

    def stub(self, name, body):
        file = self.bin / name
        file.write_text('#!/bin/sh\n' + body + '\n')
        file.chmod(0o755)
        return file

    def test_cloud_rejects_failed_client_shell_unknown_exit_and_timeout(self):
        self.assertIsNotNone(NODE, 'Set NODE to a working Node executable')
        cases = [('pass', 0, 0, False, False, True), ('nested', 0, 0, False, True, True),
                 ('client-failed', 9, 0, False, False, False), ('shell-failed', 0, 1, False, False, False),
                 ('unknown-shell-exit', 0, None, False, False, False),
                 ('timed-out', 0, 0, True, False, False), ('pipe-hid-test-failure', 0, 0, False, False, False)]
        for name, client_exit, shell_exit, hangs, nested, expected in cases:
            with self.subTest(name=name):
                summary = 'ℹ tests 15\nℹ pass 15\nℹ fail 0\n'
                if name == 'pipe-hid-test-failure':
                    summary = 'ℹ tests 15\nℹ pass 14\nℹ fail 1\n'
                metadata = {} if shell_exit is None else {'exit': shell_exit}
                if nested:
                    metadata = {'metadata': metadata}
                event = {'type': 'tool_use', 'part': {'tool': 'shell', 'state': {'status': 'completed',
                         'input': {'command': 'node --test 2>&1 | tail -20'}, 'metadata': metadata, 'output': summary}}}
                launcher = self.work / ('client-' + name)
                launcher.write_text('#!' + NODE + '\nconst fs=require("node:fs");fs.cpSync(' +
                    json.dumps(str(ROOT / 'examples/cloud-task/reference/src')) + ',"src",{recursive:true});' +
                    'console.log(' + json.dumps(json.dumps(event)) + ');' +
                    ('setInterval(()=>{},1000);' if hangs else f'process.exitCode={client_exit};'))
                launcher.chmod(0o755)
                out = self.work / ('out-' + name)
                result = subprocess.run([NODE, str(ROOT / 'tools/tui-port/cloud-coding-task.mjs'), str(out)],
                    env={**self.env, 'OPENCODE_TEST_PORT_ROOT': str(launcher), 'OPENCODE_CLOUD_MODEL': 'opencode/test-free',
                         'OPENCODE_CLOUD_OFFLINE': '1', 'OPENCODE_TEST_TIMEOUT_MS': '500' if hangs else '10000'},
                    capture_output=True, text=True, timeout=20)
                outcome = json.loads(next(out.glob('*/outcome.json')).read_text())
                self.assertEqual(outcome['semantic_pass'], expected, result.stdout + result.stderr)
                self.assertEqual(result.returncode, 0 if expected else 1)
                self.assertTrue(outcome['independent_test_pass'])
                if hangs:
                    self.assertTrue(outcome['expired'])
                    self.assertEqual(outcome['exit'], 124)

    def test_cpu_runner_stops_after_refused_startup_and_leaves_pid_files_alone(self):
        self.stub('uname', 'echo Haiku')
        source = self.work / 'source/tools/kvm-run'
        source.mkdir(parents=True)
        shutil.copy(ROOT / 'tools/kvm-run/prodrun.sh', source / 'prodrun.sh')
        (source / 'services.sh').write_text('exit 17\n')
        self.stub('node', 'echo unexpected > "$HOME/ran-checks"; exit 0')
        pidfile = self.work / 'opencode-serve.pid'
        pidfile.write_text(str(os.getpid()))  # Must never be consumed by the runner.
        result = subprocess.run(['sh', str(source / 'prodrun.sh'), 'ivybridge'],
            env={**self.env, 'OPENCODE_SOURCE_ROOT': str(source.parents[1]), 'OPENCODE_GUEST_HOME': str(self.work)},
            capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 17, result.stderr)
        self.assertFalse((self.work / 'ran-checks').exists())
        self.assertEqual(pidfile.read_text(), str(os.getpid()))

    def test_scoped_services_cleanup_both_owned_children_after_check_failure(self):
        self.stub('uname', 'echo Haiku')
        self.stub('curl', '''case "$*" in
 *18081*) test -e "$HOME/model-ready";;
 *18083*) test -e "$HOME/backend-ready";;
 *) exit 1;; esac''')
        guest = self.work
        (guest / 'opencode-work').mkdir()
        (guest / 'opencode-work/opencode.json').write_text('{}')
        runtime = guest / 'runtime'
        runtime.mkdir()
        (guest / 'opencode-env.sh').write_text('OPENCODE_PASSWORD=fake-test-only\nOC=' + str(runtime) + '\n')
        llama = guest / 'haiku-llm/build-cpu-ivybridge/bin'
        llama.mkdir(parents=True)
        for program, name in [(llama / 'llama-server', 'model'), (runtime / 'opencode', 'backend')]:
            program.write_text('#!' + sys.executable + '\n' +
                'import os,signal,time\nfrom pathlib import Path\np=Path(os.environ["HOME"])\n' +
                f'(p/"{name}-ready").touch()\n' +
                f'def done(*a):\n (p/"{name}-stopped").touch()\n raise SystemExit(0)\n' +
                'signal.signal(signal.SIGTERM,done)\nwhile True: time.sleep(.02)\n')
            program.chmod(0o755)
        result = subprocess.run(['sh', str(ROOT / 'tools/kvm-run/services.sh'), 'sh', '-c', 'exit 11'],
            env={**self.env, 'OPENCODE_GUEST_HOME': str(guest)}, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 11, result.stdout + result.stderr)
        for name in ['model', 'backend']:
            deadline = time.monotonic() + 2
            while not (guest / (name + '-stopped')).exists() and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertTrue((guest / (name + '-stopped')).exists())



if __name__ == '__main__':
    unittest.main(verbosity=2)

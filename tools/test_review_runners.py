#!/usr/bin/env python3
"""Offline controls only: fake model clients, fake service/GPU commands, /tmp files."""
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

    def test_card_entry_requires_explicit_execution(self):
        # Even discovery commands are stubbed: this control cannot touch hardware.
        self.stub('nvidia-smi', 'echo forbidden >&2; exit 99')
        self.stub('systemctl', 'echo forbidden >&2; exit 99')
        result = subprocess.run(['bash', str(ROOT / 'tools/kepler-static/run_card_comparison.sh'), str(self.work / 'out')],
            env=self.env, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('forbidden', result.stderr)

    def supervisor(self, script, out, seconds='10'):
        return [sys.executable, str(ROOT / 'tools/kepler-static/card_supervisor.py'),
                '--timeout', seconds, '--restore-timeout', '2', str(script), str(out)]

    def test_supervisor_reaps_background_child_before_restore_on_timeout_and_signal(self):
        for mode in ['timeout', 'signal', 'normal-with-background']:
            with self.subTest(mode=mode):
                out = self.work / mode
                worker = self.work / ('worker-' + mode + '.sh')
                # Child starts its own session; subreaper must still find it.
                worker.write_text('''#!/bin/bash
if [ "$1" = --restore ]; then
 if kill -0 "$(cat "$2/child.pid")" 2>/dev/null; then echo live > "$2/restore-too-early"; exit 7; fi
 echo restored > "$2/restored"
 exit 0
fi
: > "$3"
''' + sys.executable + ''' -c 'import os,time;os.setsid();time.sleep(30)' &
echo $! > "$2/child.pid"
''' + ('exit 0\n' if mode == 'normal-with-background' else 'wait\n'))
                proc = subprocess.Popen(self.supervisor(worker, out, '.3' if mode == 'timeout' else '10'),
                                        env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if mode == 'signal':
                    deadline = time.monotonic() + 3
                    while not (out / 'child.pid').exists() and time.monotonic() < deadline:
                        time.sleep(.02)
                    self.assertTrue((out / 'child.pid').exists())
                    proc.send_signal(signal.SIGTERM)
                stdout, stderr = proc.communicate(timeout=12)
                self.assertEqual(proc.returncode, {'timeout':124, 'signal':143, 'normal-with-background':0}[mode], stdout + stderr)
                self.assertTrue((out / 'restored').exists(), stdout + stderr)
                self.assertFalse((out / 'restore-too-early').exists())

    def test_supervisor_propagates_worker_and_restore_failures_and_no_pause(self):
        for name, paused, restore_code, expected in [('no-pause',False,0,9), ('worker-fails',True,0,9), ('restore-fails',True,6,125)]:
            with self.subTest(name=name):
                out = self.work / name
                worker = self.work / (name + '.sh')
                worker.write_text('if [ "$1" = --restore ]; then echo restore > "$2/restored"; exit ' + str(restore_code) + '; fi\n' +
                                  (': > "$3"\n' if paused else '') + 'exit 9\n')
                result = subprocess.run(self.supervisor(worker, out), env=self.env, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                self.assertEqual((out / 'restored').exists(), paused)

    def test_card_worker_stops_on_correctness_failure_with_only_fake_commands(self):
        # Every hardware/service command resolves to our fake executable.
        for command in ['systemctl', 'curl', 'sleep']:
            self.stub(command, 'echo ' + command + ' "$*" >> "$HOME/commands"; exit 0')
        self.stub('timeout', 'shift 3; exec "$@"')  # strip -k 5 DEADLINE
        self.stub('nvidia-smi', 'echo nvidia-smi "$*" >> "$HOME/commands"; echo 0')
        unit = self.work / '.config/systemd/user'
        unit.mkdir(parents=True)
        (unit / 'llama-server-one.service').write_text('Environment=CUDA_VISIBLE_DEVICES=GPU-abc123\n')
        binaries = self.work / 'llm-server/llama.cpp/build/bin'
        binaries.mkdir(parents=True)
        for name in ['test-backend-ops', 'llama-bench']:
            file = binaries / name
            file.write_text('#!/bin/sh\necho ' + name + ' "$*" >> "$HOME/commands"\nexit 9\n')
            file.chmod(0o755)
        numa = self.work / '.local/bin'
        numa.mkdir(parents=True)
        (numa / 'numactl').write_text('#!/bin/sh\nshift 2; exec "$@"\n')
        (numa / 'numactl').chmod(0o755)
        for path in ['llm-server/models/Qwen3.5-9B-UD-Q4_K_XL.gguf', 'kepler-llvm-eval/lib-clang/libggml-cuda.so.0']:
            file = self.work / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.touch()
        # Reuse only fake programs for correctness failure, complete success,
        # and a restoration health failure (sleep is a no-op, not a 30-minute wait).
        for name, op_exit, curl_exit, expected in [('correctness-fails',9,0,9), ('all-pass',0,0,0), ('restore-unhealthy',9,1,125)]:
            with self.subTest(name=name):
                commands = self.work / 'commands'
                commands.unlink(missing_ok=True)
                self.stub('curl', 'exit ' + str(curl_exit))
                for filename in ['test-backend-ops', 'llama-bench']:
                    (binaries / filename).write_text('#!/bin/sh\necho ' + filename + ' "$*" >> "$HOME/commands"\nexit ' + str(op_exit) + '\n')
                result = subprocess.run(self.supervisor(ROOT / 'tools/kepler-static/run_card_comparison.sh', self.work / name),
                                        env=self.env, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                calls = commands.read_text()
                if op_exit:
                    self.assertEqual(calls.count('test-backend-ops'), 1)
                    self.assertNotIn('llama-bench', calls)
                    self.assertNotIn(' perf ', calls)
                else:
                    self.assertEqual(calls.count('test-backend-ops'), 43)  # 34 test + 9 perf
                    self.assertEqual(calls.count('llama-bench'), 3)
                self.assertIn('start llama-server-one.service', calls)



if __name__ == '__main__':
    unittest.main(verbosity=2)

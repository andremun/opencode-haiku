#!/usr/bin/env python3
"""Host-only regression controls. No VM, model, Rust compiler or existing service used."""
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.

from pathlib import Path
import functools, http.client, importlib.util, json, os, shutil, subprocess, tempfile, threading, time, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
# Shared VM tools (job runner, transfer server) belong to haiku-k40c (ADR 004).
HAIKU_K40C = Path(os.environ.get("HAIKU_K40C_ROOT", ROOT.parent / "haiku-k40c"))
NODE = os.environ.get("NODE") or shutil.which("node")
if NODE is None:
    raise SystemExit("Node.js is required: put node on PATH or set NODE")


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="t7610-runner-test-")
        self.root = Path(self.tmp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.env = {
            **os.environ,
            "PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
        }

    def tearDown(self):
        self.tmp.cleanup()

    def stub(self, name, body):
        p = self.bin / name
        p.write_text("#!/bin/sh\n" + body + "\n")
        p.chmod(0o755)

    def run_script(self, name):
        return subprocess.run(
            ["sh", str(ROOT / name)],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=10,
        )

    @unittest.skipUnless(
        (HAIKU_K40C / "tools/haiku/job.sh").is_file(),
        "haiku-k40c checkout not found (set HAIKU_K40C_ROOT)",
    )
    def test_guest_failure_reaches_host_and_missing_status_rejected(self):
        tools = self.root / "tools"
        tools.mkdir()
        shutil.copy(HAIKU_K40C / "tools/haiku/job.sh", tools / "job.sh")
        self.env["HAIKU_JOB_ROOT"] = str(self.root)
        for number, trailer, expected in [
            (1, "exit=7", 7),
            (2, "exit=0", 0),
            (3, "incomplete", 125),
        ]:
            proc = subprocess.Popen(
                ["sh", str(tools / "job.sh"), str(number), "exit 7", "5"],
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            deadline = time.monotonic() + 4
            request = self.root / "share" / f"job{number}.sh"
            while not request.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(request.exists())
            # A complete result is published atomically, just as the transfer server now does.
            pending = self.root / "logs" / "pending"
            pending.write_text("guest output\n" + trailer + "\n")
            pending.replace(self.root / "logs" / f"job{number}.out")
            out, err = proc.communicate(timeout=7)
            self.assertEqual(proc.returncode, expected, (out, err))
            self.assertIn("guest output", out)
        reused = subprocess.run(
            ["sh", str(tools / "job.sh"), "1", "true"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(reused.returncode, 2)
        timeout = subprocess.run(
            ["sh", str(tools / "job.sh"), "4", "sleep 100", "1"],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(timeout.returncode, 124)
        self.assertIn("not been cancelled", timeout.stderr)

    def test_cargo_test_and_clippy_failures_are_not_hidden_by_tail(self):
        work = self.root / "native"
        (work / "pty").mkdir(parents=True)
        self.env["OPENCODE_NATIVE_WORK"] = str(work)
        self.stub(
            "cargo",
            """case "$1" in
 build) mkdir -p "$CARGO_TARGET_DIR/debug"; echo binary > "$CARGO_TARGET_DIR/debug/opencode-pty";;
 test) echo 'TEST_OUTPUT'; [ "${FAIL_CARGO:-}" != test ] || exit 9;;
 clippy) echo 'CLIPPY_OUTPUT'; [ "${FAIL_CARGO:-}" != clippy ] || exit 11;;
esac
exit 0""",
        )
        self.stub("strip", "exit 0")
        self.stub("rustc", "echo rust-test-stub")
        for failed, expected in [("test", 9), ("clippy", 11), ("", 0)]:
            self.env["FAIL_CARGO"] = failed
            result = self.run_script("tests/acceptance/vm/pty.sh")
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            self.assertEqual("PTY-DONE" in result.stdout, expected == 0)
            if failed:
                self.assertFalse((work / "opencode-pty-bin").exists())

    def test_api_failure_is_not_replaced_by_successful_upload(self):
        self.env["OPENCODE_ACCEPTANCE_WORK"] = str(self.root / "acceptance")
        self.env["OPENCODE_PORT_ROOT"] = str(self.root / "runtime")
        self.stub(
            "curl",
            """while [ "$#" -gt 0 ]; do
 if [ "$1" = -o ]; then shift; [ "$1" = /dev/null ] || : > "$1"; fi
 shift
done
exit 0""",
        )
        self.stub(
            "node",
            'echo API_PROBE; case "$1" in persistent-terminal-api.mjs) exit "${PROBE_EXIT:-0}";; esac',
        )
        for code, expected in [("17", 1), ("0", 0)]:
            self.env["PROBE_EXIT"] = code
            result = self.run_script("tests/acceptance/vm/api.sh")
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            self.assertIn("persistent-terminal-api exit=" + code, result.stdout)

    def test_services_refuse_existing_listener_before_writing_configuration(self):
        self.stub("uname", "echo Haiku")
        self.stub("curl", "exit 0")
        result = self.run_script("tests/acceptance/vm/services.sh")
        self.assertEqual(result.returncode, 1)
        self.assertIn("refusing duplicate services", result.stderr)

    def test_coding_acceptance_requires_agent_test_and_an_unchanged_passing_fixture(
        self,
    ):
        for index, (reported, tampered, expected) in enumerate(
            [(False, False, False), (True, False, True), (True, True, False)]
        ):
            root = self.root / ("coding-" + str(index))
            root.mkdir()
            launcher = self.root / ("fake-opencode-" + str(index))
            launcher.write_text(
                "#!"
                + NODE
                + "\n"
                + "const fs=require('node:fs');fs.writeFileSync('add.mjs','export const add=(a,b)=>a+b;');"
                + (
                    "fs.writeFileSync('test.mjs','console.log(\"AGENT_TEST_PASS\")');"
                    if tampered
                    else ""
                )
                + (
                    "console.log(JSON.stringify({type:'tool_use',part:{tool:'shell',state:{status:'completed',input:{command:'node test.mjs'},output:'AGENT_TEST_PASS'}}}));"
                    if reported
                    else ""
                )
            )
            launcher.chmod(0o755)
            result = subprocess.run(
                [NODE, str(ROOT / "tests/acceptance/coding-workflow.mjs"), str(root)],
                env={**os.environ, "OPENCODE_TEST_PORT_ROOT": str(launcher)},
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            outcome = json.loads((root / "coding-outcome.json").read_text())
            self.assertEqual(outcome["semantic_pass"], expected)
            self.assertEqual(outcome["test_unchanged"], not tampered)
            self.assertEqual(outcome["steps"], 8)
            if not tampered:
                self.assertTrue(outcome["independent_test_pass"])

    def test_coding_uploads_use_per_run_names_outside_tracked_results(self):
        names = []

        class Capture(BaseHTTPRequestHandler):
            def do_PUT(self):
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                names.append(self.path.lstrip("/"))
                self.send_response(204)
                self.end_headers()

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Capture)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            root = self.root / "coding-upload"
            root.mkdir()
            launcher = self.root / "fake-opencode-upload"
            launcher.write_text(
                "#!"
                + NODE
                + "\n"
                + "require('node:fs').writeFileSync('add.mjs','export const add=(a,b)=>a+b;');"
            )
            launcher.chmod(0o755)
            base = "http://127.0.0.1:%d/" % server.server_address[1]
            result = subprocess.run(
                [NODE, str(ROOT / "tests/acceptance/coding-workflow.mjs"), str(root)],
                env={
                    **os.environ,
                    "OPENCODE_TEST_PORT_ROOT": str(launcher),
                    "OPENCODE_TEST_UPLOAD_BASE": base,
                },
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        finally:
            server.shutdown()
            server.server_close()
        run = json.loads((root / "coding-outcome.json").read_text())["fixture"].split(
            "/"
        )[-2]
        self.assertRegex(run, r"^coding-[0-9]+$")
        self.assertEqual(
            sorted(names),
            sorted(
                "native-" + run + "-" + n
                for n in ["agent-model.log", "coding-outcome.json"]
            ),
        )
        tracked = set(
            subprocess.run(
                ["git", "-C", str(ROOT), "ls-files", "results"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.split()
        )
        for name in names:
            self.assertNotIn("results/" + name, tracked)
            self.assertRegex(
                name, r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$"
            )  # accepted by transfer_server.py

    def test_cpu_experiments_refuse_the_host_platform(self):
        if os.uname().sysname == "Haiku":
            self.skipTest("This guard control is intended for the Linux host")
        for name in ["services.sh"]:
            result = self.run_script("tests/acceptance/vm/" + name)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("Haiku guest", result.stderr)

    def test_missing_coding_launcher_records_a_terminal_error(self):
        root = self.root / "missing-launcher"
        root.mkdir()
        result = subprocess.run(
            [NODE, str(ROOT / "tests/acceptance/coding-workflow.mjs"), str(root)],
            env={
                **os.environ,
                "OPENCODE_TEST_PORT_ROOT": str(self.root / "does-not-exist"),
            },
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        outcome = json.loads((root / "coding-outcome.json").read_text())
        self.assertIn("ENOENT", outcome["launch_error"])
        self.assertFalse(outcome["semantic_pass"])

    @unittest.skipUnless(
        (HAIKU_K40C / "tools/haiku/transfer_server.py").is_file(),
        "haiku-k40c checkout not found (set HAIKU_K40C_ROOT)",
    )
    def test_transfer_publishes_only_complete_results(self):
        spec = importlib.util.spec_from_file_location(
            "t7610_transfer", HAIKU_K40C / "tools/haiku/transfer_server.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        handler = functools.partial(
            module.Handler, root=self.root, results=self.root / "results"
        )
        (self.root / "share").mkdir()
        (self.root / "results").mkdir()
        # A result file is replaced atomically. Job logs in logs/ are written once
        # (haiku-k40c transfer_server.py), so they cannot show the replacement.
        destination = self.root / "results/guest-run.log"
        destination.write_bytes(b"old complete output")
        payload = b"x" * 200000 + b"\nexit=7\n"
        observations = []
        original_replace = os.replace

        def replace(source, target):
            observations.append((Path(target).read_bytes(), Path(source).read_bytes()))
            original_replace(source, target)

        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.object(module.os, "replace", side_effect=replace):
                conn = http.client.HTTPConnection(*server.server_address, timeout=3)
                conn.request("PUT", "/guest-run.log", body=payload)
                response = conn.getresponse()
                response.read()
                self.assertEqual(response.status, 201)
                conn.close()
            self.assertEqual(observations, [(b"old complete output", payload)])
            self.assertEqual(destination.read_bytes(), payload)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_http_error_and_invalid_completion_fail_the_inference_runner(self):
        status = 200
        body = {"choices": [{"message": {"content": "OK"}}]}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(status)
                self.end_headers()
                self.wfile.write(json.dumps(body).encode())

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            endpoint = "http://127.0.0.1:" + str(server.server_port)
            for status, body, expected in [
                (500, {"error": "injected"}, 1),
                (200, {}, 1),
                (200, {"choices": [{"message": {"content": "OK"}}]}, 0),
            ]:
                output = self.root / "inference.json"
                result = subprocess.run(
                    [
                        NODE,
                        str(ROOT / "tests/acceptance/inference-compare.cjs"),
                        endpoint,
                        str(output),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=8,
                )
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertEqual(len(json.loads(output.read_text())["requests"]), 3)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    @unittest.skipUnless(
        (HAIKU_K40C / "tools/haiku/transfer_server.py").is_file(),
        "haiku-k40c checkout not found (set HAIKU_K40C_ROOT)",
    )
    def test_transfer_rejects_dot_names(self):
        spec = importlib.util.spec_from_file_location(
            "t7610_transfer_names", HAIKU_K40C / "tools/haiku/transfer_server.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        handler = functools.partial(
            module.Handler, root=self.root, results=self.root / "results"
        )
        (self.root / "share").mkdir()
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for name, expected in [
                ("..", 400),
                (".", 400),
                (".hidden", 400),
                ("ok-name.txt", 201),
            ]:
                conn = http.client.HTTPConnection(*server.server_address, timeout=3)
                conn.request("PUT", "/" + name, body=b"x")
                response = conn.getresponse()
                response.read()
                conn.close()
                self.assertEqual(response.status, expected, name)
            self.assertFalse(
                any((self.root / "results").glob(".*"))
                if (self.root / "results").exists()
                else False
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_stage_reports_a_missing_runtime_archive(self):
        # Run the staging helper from a copy of the repo layout with a manifest but no archive.
        work = self.root / "stage"
        (work / "tests/acceptance/vm").mkdir(parents=True)
        (work / "results").mkdir()
        shutil.copy(
            ROOT / "tests/acceptance/vm/stage_t7610.py",
            work / "tests/acceptance/vm/stage_t7610.py",
        )
        (work / "results/opencode-tui-package.json").write_text(
            json.dumps({"archive": "missing.tar.gz", "sha256": "0" * 64})
        )
        subprocess.run(["git", "init", "-q"], cwd=work, check=True)
        subprocess.run(["git", "add", "-A"], cwd=work, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=t",
                "-c",
                "user.email=t@example.invalid",
                "commit",
                "-q",
                "-m",
                "fixture",
            ],
            cwd=work,
            check=True,
        )
        result = subprocess.run(
            ["python3", str(work / "tests/acceptance/vm/stage_t7610.py")],
            cwd=work,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Runtime archive missing", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_cloud_task_fixture_and_acceptance_controls(self):
        ref = ROOT / "examples/cloud-task/reference/src"
        scenarios = [
            ("solved", True, False, True),
            ("no-test-run", False, False, False),
            ("tampered-tests", True, True, False),
            ("unsolved", None, False, False),
        ]
        for name, ran, tamper, expected in scenarios:
            out = self.root / ("cloud-" + name)
            out.mkdir()
            body = (
                "const fs=require('node:fs');"
                + (
                    "fs.cpSync(process.env.LC_REF,'src',{recursive:true});"
                    if ran is not None
                    else ""
                )
                + ("fs.appendFileSync('test/csv.test.mjs','//x');" if tamper else "")
                + (
                    "console.log(JSON.stringify({type:'tool_use',part:{tool:'shell',state:{status:'completed',input:{command:'node --test'},metadata:{exit:0},output:'\u2139 tests 15\\n\u2139 pass 15\\n\u2139 fail 0\\n'}}}));"
                    if ran
                    else ""
                )
            )
            if name == "no-test-run":
                body = body.replace("console.log", "//")
            launcher = self.root / ("cloud-launcher-" + name)
            launcher.write_text("#!" + NODE + "\n" + body)
            launcher.chmod(0o755)
            result = subprocess.run(
                [NODE, str(ROOT / "tests/acceptance/cloud-coding-task.mjs"), str(out)],
                env={
                    **os.environ,
                    "LC_REF": str(ref),
                    "OPENCODE_TEST_PORT_ROOT": str(launcher),
                    "OPENCODE_CLOUD_MODEL": "opencode/test-model-free",
                },
                capture_output=True,
                text=True,
                timeout=60,
            )
            outcome = json.loads(
                next((out / d / "outcome.json" for d in os.listdir(out))).read_text()
            )
            self.assertEqual(
                outcome["semantic_pass"], expected, (name, result.stdout, result.stderr)
            )
            if name == "solved":
                self.assertEqual(
                    outcome["independent_tests"], {"tests": 15, "pass": 15, "fail": 0}
                )
            if name == "unsolved":
                self.assertEqual(outcome["independent_tests"]["fail"], 12)

    def test_cloud_task_requires_a_model_and_launcher(self):
        result = subprocess.run(
            [
                NODE,
                str(ROOT / "tests/acceptance/cloud-coding-task.mjs"),
                str(self.root),
            ],
            env={k: v for k, v in os.environ.items() if not k.startswith("OPENCODE_")},
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("OPENCODE_CLOUD_MODEL", result.stderr)

    # --- secrets handling (fake keys are assembled at run time so this file never contains key-shaped text)
    def fake_key(self):
        return "oc_sk_" + "a1b2c3d4e5f6" + "_" + "Zz9" * 8

    def key_file(self, mode=0o600, directory=None, name="cloud.env"):
        path = Path(directory or self.root) / name
        path.write_text("OPENCODE_API_KEY=" + self.fake_key() + "\n")
        path.chmod(mode)
        return path

    def test_key_wrapper_exports_the_key_without_printing_it(self):
        import hashlib

        wrapper = ROOT / "tools/secrets/with-cloud-key.sh"
        key = self.fake_key()
        child = [
            "sh",
            "-c",
            'printf %s "$OPENCODE_API_KEY" | sha256sum | cut -c1-16; echo pass=$OPENCODE_CLOUD_PASS_API_KEY',
        ]
        good = subprocess.run(
            ["sh", str(wrapper), *child],
            env={**os.environ, "OPENCODE_CLOUD_ENV_FILE": str(self.key_file())},
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertIn(hashlib.sha256(key.encode()).hexdigest()[:16], good.stdout)
        self.assertIn("pass=1", good.stdout)
        self.assertNotIn(key, good.stdout + good.stderr)

        def refused(file, expect):
            r = subprocess.run(
                ["sh", str(wrapper), "true"],
                env={**os.environ, "OPENCODE_CLOUD_ENV_FILE": str(file)},
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(r.returncode, 2, (expect, r.stderr))
            self.assertIn(expect, r.stderr)
            self.assertNotIn(key, r.stdout + r.stderr)

        refused(self.key_file(0o644, name="lax.env"), "mode 600")
        refused(self.root / "missing.env", "not found")
        inside = tempfile.NamedTemporaryFile(
            dir=ROOT, prefix=".keytest-", suffix=".env", delete=False
        )
        inside.close()
        try:
            Path(inside.name).write_text("OPENCODE_API_KEY=" + key + "\n")
            Path(inside.name).chmod(0o600)
            refused(inside.name, "outside the repository")
        finally:
            Path(inside.name).unlink(missing_ok=True)
        empty = self.root / "empty.env"
        empty.write_text("OTHER=1\n")
        empty.chmod(0o600)
        refused(empty, "No OPENCODE_API_KEY")

    def test_one_shot_key_server_serves_once_to_the_right_token(self):
        import urllib.request, urllib.error

        key = self.fake_key()
        server = subprocess.Popen(
            [
                "python3",
                str(ROOT / "tools/secrets/serve-key-once.py"),
                "--file",
                str(self.key_file()),
                "--guest-host",
                "127.0.0.1",
                "--timeout",
                "30",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            url = server.stdout.readline().strip().split("=", 1)[1]
            self.assertNotIn(key, url)
            base, token = url.rsplit("/", 1)
            with self.assertRaises(urllib.error.HTTPError) as bad:
                urllib.request.urlopen(base + "/wrong-token", timeout=5)
            self.assertEqual(bad.exception.code, 404)
            with urllib.request.urlopen(url, timeout=5) as ok:
                self.assertEqual(ok.read().decode(), key)
            self.assertEqual(server.wait(timeout=10), 0)
            with self.assertRaises(Exception):
                urllib.request.urlopen(url, timeout=2)
            self.assertNotIn(key, server.stdout.read() + server.stderr.read())
        finally:
            if server.poll() is None:
                server.kill()
            server.stdout.close()
            server.stderr.close()

    def test_secret_scanner_flags_keys_without_printing_them_and_ignores_placeholders(
        self,
    ):
        scan = ROOT / "tools/secrets/scan_secrets.py"
        key = self.fake_key()
        d = self.root / "scan"
        d.mkdir()
        (d / "clean.txt").write_text(
            'OPENCODE_API_KEY=%s\nexport OPENCODE_API_KEY="$K"\nprefix oc_sk_ only\n'
        )
        self.assertEqual(
            subprocess.run(
                ["python3", str(scan), str(d)], capture_output=True, text=True
            ).returncode,
            0,
        )
        (d / "leak.log").write_text("line\nrun with OPENCODE_API_KEY=" + key + " now\n")
        (d / "bearer.txt").write_text("Authorization: Bearer " + "x" * 30 + "\n")
        r = subprocess.run(
            ["python3", str(scan), str(d)], capture_output=True, text=True
        )
        self.assertEqual(r.returncode, 1)
        self.assertNotIn(key, r.stdout + r.stderr)
        self.assertIn("leak.log:2", r.stdout)
        self.assertIn("bearer.txt:1", r.stdout)

    def test_runner_refuses_paid_models_by_default(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("OPENCODE_")}
        r = subprocess.run(
            [
                NODE,
                str(ROOT / "tests/acceptance/cloud-coding-task.mjs"),
                str(self.root),
            ],
            env={
                **env,
                "OPENCODE_TEST_PORT_ROOT": "/bin/true",
                "OPENCODE_CLOUD_MODEL": "opencode/some-paid-model",
            },
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("non-free", r.stderr)

    def test_guest_wrapper_fetches_the_key_into_memory_once(self):
        import hashlib

        key = self.fake_key()
        server = subprocess.Popen(
            [
                "python3",
                str(ROOT / "tools/secrets/serve-key-once.py"),
                "--file",
                str(self.key_file()),
                "--guest-host",
                "127.0.0.1",
                "--timeout",
                "30",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            url = server.stdout.readline().strip().split("=", 1)[1]
            child = [
                "sh",
                "-c",
                'printf %s "$OPENCODE_API_KEY" | sha256sum | cut -c1-16; echo pass=$OPENCODE_CLOUD_PASS_API_KEY',
            ]
            first = subprocess.run(
                [
                    "sh",
                    str(ROOT / "tests/acceptance/vm/with-cloud-key-guest.sh"),
                    url,
                    *child,
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertIn(hashlib.sha256(key.encode()).hexdigest()[:16], first.stdout)
            self.assertNotIn(key, first.stdout + first.stderr)
            self.assertEqual(server.wait(timeout=10), 0)
            second = subprocess.run(
                [
                    "sh",
                    str(ROOT / "tests/acceptance/vm/with-cloud-key-guest.sh"),
                    url,
                    "true",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.assertEqual(second.returncode, 2)
            self.assertIn("Could not fetch", second.stderr)
        finally:
            if server.poll() is None:
                server.kill()
            server.stdout.close()
            server.stderr.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)

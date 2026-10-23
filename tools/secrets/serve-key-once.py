#!/usr/bin/env python3
"""Serve the cloud API key exactly once on localhost, so a VM can fetch it into memory.

Run on the host; give the printed URL to the guest job (the URL is a random single-use token and
never contains the key). The server exits after one successful fetch, five bad requests, or the
timeout. The key file is read with the same checks as with-cloud-key.sh and is never printed.
"""
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.

import argparse, os, secrets, stat, sys, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read_key(path):
    path = Path(path)
    if not path.is_file():
        raise SystemExit(f"Key file not found: {path} (see docs/SECRETS.md)")
    info = path.stat()
    if info.st_uid != os.getuid():
        raise SystemExit("Key file must be owned by you.")
    if stat.S_IMODE(info.st_mode) not in (0o600, 0o400):
        raise SystemExit(
            f"Key file must be mode 600 or 400 (it is {oct(stat.S_IMODE(info.st_mode))[2:]})."
        )
    real = path.resolve()
    if real == REPO or REPO in real.parents:
        raise SystemExit("Key file must be outside the repository.")
    for line in path.read_text().splitlines():
        if line.startswith("OPENCODE_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    raise SystemExit("No OPENCODE_API_KEY= line in the key file.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--file",
        default=os.environ.get(
            "OPENCODE_CLOUD_ENV_FILE",
            str(Path.home() / ".config/opencode-haiku-test/cloud.env"),
        ),
    )
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument(
        "--guest-host", default="10.0.2.2", help="address the guest uses for the host"
    )
    args = ap.parse_args()
    key = read_key(args.file)
    token = secrets.token_urlsafe(18)
    state = {"bad": 0, "served": False}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/" + token and not state["served"]:
                state["served"] = True
                body = key.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                threading.Thread(target=server.shutdown, daemon=True).start()
            else:
                state["bad"] += 1
                self.send_error(404)
                if state["bad"] >= 5:
                    threading.Thread(target=server.shutdown, daemon=True).start()

        def log_message(self, fmt, *a):
            pass  # never log request lines

    server = HTTPServer(("127.0.0.1", args.port), Handler)
    timer = threading.Timer(args.timeout, server.shutdown)
    timer.daemon = True
    timer.start()
    print(
        f"KEY_URL=http://{args.guest_host}:{server.server_address[1]}/{token}",
        flush=True,
    )
    print(f"LOCAL_PORT={server.server_address[1]}", flush=True)
    server.serve_forever()
    timer.cancel()
    server.server_close()
    sys.exit(0 if state["served"] else 3)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Download the pinned upstream inputs of the port into cache/ and check them.

Inputs: reference/INPUTS.json ("download" entries: URL, cache path, SHA-256).
Outputs: the archives in cache/. A file that exists and matches is kept. A file
that does not match is reported and left as is. Nothing is extracted.
Prerequisites: network access to the listed hosts. --check verifies only.
"""
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--check", action="store_true", help="verify present files, download nothing"
    )
    a = ap.parse_args()
    inputs = json.loads((ROOT / "reference/INPUTS.json").read_text())["download"]
    failures = 0
    for item in inputs:
        path = ROOT / item["cache"]
        if not path.exists() and not a.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            partial = path.with_name(path.name + ".partial")
            try:
                with (
                    urllib.request.urlopen(item["url"], timeout=120) as response,
                    partial.open("wb") as out,
                ):
                    while block := response.read(1 << 20):
                        out.write(block)
                partial.replace(path)
            except OSError as exc:
                partial.unlink(missing_ok=True)
                print(f"FAIL {item['name']}: download failed: {exc}")
                failures += 1
                continue
        if not path.exists():
            print(f"MISSING {item['name']}: {item['cache']}")
            failures += 1
        elif sha256(path) != item["sha256"]:
            print(f"FAIL {item['name']}: SHA-256 mismatch for {item['cache']}")
            failures += 1
        else:
            print(f"ok {item['name']}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

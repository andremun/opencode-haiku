#!/usr/bin/env python3
"""Find API-key-shaped strings. Prints file:line and the rule name, never the matched text.

Usage: scan_secrets.py [--staged] [PATH ...]
  --staged   scan the staged (index) version of changed files (used by the pre-commit hook)
  PATH       files or directories to scan (default: the repository, minus disks and caches)
Exit status: 0 clean, 1 findings, 2 usage error.
"""
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.

import re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKIP_DIRS = {".git", "cache", "source", "__pycache__", "node_modules"}
# Skipped only directly below the scan root: the old VM disk folder. A folder named
# "vm" deeper in the tree (tests/acceptance/vm) holds scripts and is scanned.
SKIP_TOP_DIRS = {"vm"}
SKIP_SUFFIXES = {
    ".qcow2",
    ".fd",
    ".iso",
    ".gz",
    ".tgz",
    ".zip",
    ".png",
    ".ppm",
    ".a",
    ".so",
    ".node",
}
MAX_BYTES = 20 * 1024 * 1024
PLACEHOLDER = re.compile(r"^(%s|\$|<|\[REDACTED\]|CHOOSE|your|xxx|\.\.\.|\{)", re.I)
RULES = [
    ("opencode-key", re.compile(r"\boc_sk_[A-Za-z0-9_-]{8,}")),
    ("generic-sk-key", re.compile(r"\bsk-[A-Za-z0-9_-]{24,}")),
    ("bearer-token", re.compile(r"Bearer\s+[A-Za-z0-9._-]{24,}")),
]
ASSIGN = re.compile(r"OPENCODE_API_KEY=([A-Za-z0-9_.-]{12,})")


def findings_in(text):
    for number, line in enumerate(text.splitlines(), 1):
        for name, rule in RULES:
            if rule.search(line):
                yield number, name
        for match in ASSIGN.finditer(line):
            if not PLACEHOLDER.match(match.group(1)):
                yield number, "api-key-assignment"


def iter_files(paths):
    for root in paths:
        root = Path(root)
        if root.is_file():
            yield root
            continue
        for path in sorted(root.rglob("*")):
            parts = path.relative_to(root).parts
            if parts[0] in SKIP_TOP_DIRS or any(part in SKIP_DIRS for part in parts):
                continue
            if path.is_file() and path.suffix not in SKIP_SUFFIXES:
                yield path


def main(argv):
    staged = "--staged" in argv
    paths = [a for a in argv if not a.startswith("--")]
    hits = 0
    if staged:
        names = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"],
            cwd=REPO,
        ).split(b"\0")
        for raw in filter(None, names):
            name = raw.decode()
            if Path(name).suffix in SKIP_SUFFIXES:
                continue
            blob = subprocess.run(
                ["git", "show", ":" + name], cwd=REPO, capture_output=True
            ).stdout
            if len(blob) > MAX_BYTES:
                continue
            for number, rule in findings_in(blob.decode("utf-8", "ignore")):
                print(f"{name}:{number}: {rule}")
                hits += 1
    else:
        for path in iter_files(paths or [REPO]):
            try:
                if path.stat().st_size > MAX_BYTES:
                    continue
                text = path.read_bytes().decode("utf-8", "ignore")
            except OSError:
                continue
            for number, rule in findings_in(text):
                print(f"{path}:{number}: {rule}")
                hits += 1
    if hits:
        print(
            f"{hits} possible secret(s) found; matched text is not shown.",
            file=sys.stderr,
        )
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

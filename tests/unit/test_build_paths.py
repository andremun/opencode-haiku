#!/usr/bin/env python3
"""Offline check: every repository file that a build or test script names exists.

Covers:
- "$root/<path>" in build/*.sh and build/guest/*.sh,
- root / "<path>" in build/*.py and tests/acceptance/vm/*.py,
- quoted "patches/..." and "reference/..." strings in build/ files,
- "$SRC/<path>" in tests/acceptance/ shell scripts (the guest copy of this repository),
- the patch paths of the input manifests in reference/,
- each patches/<upstream>/series file: it lists every patch of its folder once, and nothing else.
A moved file then fails here, not at the first patch step of a long build.
"""
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Tracked files only: cache/, source/, share/ and results/ hold ignored or generated build files.
TRACKED = ("patches/", "reference/", "src/", "build/", "packaging/", "tools/", "tests/", "examples/", "VERSION")
PATH = r"([A-Za-z0-9_./-]+)"
FORMS = [
    (("build/*.sh", "build/guest/*.sh"), re.compile(r"\$\{?root\}?/" + PATH)),
    (("build/*.py", "tests/acceptance/vm/*.py"), re.compile(r'root\s*/\s*"' + PATH + '"')),
    (("build/*.sh", "build/*.py", "build/guest/*.sh"), re.compile(r"""['"]((?:patches|reference)/[A-Za-z0-9_./-]+)['"]""")),
    (("tests/acceptance/*.sh", "tests/acceptance/vm/*.sh"), re.compile(r"\$\{?SRC\}?/" + PATH)),
]


def named_paths():
    """Yield (script, path) for each tracked repository path that a script names."""
    for patterns, form in FORMS:
        for pattern in patterns:
            for script in sorted(ROOT.glob(pattern)):
                for path in sorted(set(form.findall(script.read_text()))):
                    path = path.rstrip("/.")
                    if path.startswith(TRACKED):
                        yield script.relative_to(ROOT), path


class BuildPathTests(unittest.TestCase):
    def test_script_references_exist(self):
        found = sorted(set(named_paths()))
        self.assertGreater(len(found), 10, "the patterns no longer match the scripts")
        missing = [f"{script}: {path}" for script, path in found if not (ROOT / path).exists()]
        self.assertEqual(missing, [])

    def test_manifest_patch_paths_exist(self):
        missing = []
        for manifest in sorted((ROOT / "reference").glob("*.json")):
            text = manifest.read_text()
            for path in sorted(set(re.findall(r'"([A-Za-z0-9_./-]+\.patch)"', text))):
                if not (ROOT / path).is_file():
                    missing.append(f"{manifest.name}: {path}")
            json.loads(text)
        self.assertEqual(missing, [])

    def test_series_lists_each_patch_once(self):
        folders = sorted(p for p in (ROOT / "patches").iterdir() if p.is_dir())
        self.assertTrue(folders)
        for folder in folders:
            with self.subTest(folder=folder.name):
                lines = [line.strip() for line in (folder / "series").read_text().splitlines()]
                entries = [line for line in lines if line and not line.startswith("#")]
                patches = sorted(p.name for p in folder.glob("*.patch"))
                self.assertEqual(len(entries), len(set(entries)), "duplicate entry")
                self.assertEqual(sorted(entries), patches)


if __name__ == "__main__":
    unittest.main()

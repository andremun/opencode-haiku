#!/usr/bin/env python3
"""Offline check: every repository file that a build script names exists.

Covers the "$root/<path>" references in build/*.sh and the patch paths of the
input manifests in reference/. A moved file then fails here, not at the first
patch step of a long build.
"""
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Tracked folders only: cache/, source/ and share/ hold ignored build inputs.
TRACKED = ("patches/", "reference/", "src/", "build/", "packaging/", "tools/")
REFERENCE = re.compile(r'\$root/([A-Za-z0-9_./-]+)')


class BuildPathTests(unittest.TestCase):
    def test_build_script_references_exist(self):
        missing = []
        for script in sorted((ROOT / "build").glob("*.sh")):
            for path in sorted(set(REFERENCE.findall(script.read_text()))):
                if path.startswith(TRACKED) and not (ROOT / path).exists():
                    missing.append(f"{script.name}: {path}")
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


if __name__ == "__main__":
    unittest.main()

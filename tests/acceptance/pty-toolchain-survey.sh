#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
cd /boot/home/opencode-acceptance
(command -v rustc; command -v cargo; pkgman search -D rust_bin; pkgman search zig; pkgman search --help) > pty-toolchain-survey.log 2>&1
curl -T pty-toolchain-survey.log http://10.0.2.2:18080/pty-toolchain-survey.log

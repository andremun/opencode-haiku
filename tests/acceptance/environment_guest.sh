#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
set -u
work=/boot/home/opencode-acceptance
mkdir -p "$work"
cd "$work" || exit 1
(
 uname -a
 pkgman search nodejs26
 pkgman search zig
 pkgman search libffi
 pkgman search nodejs24_devel
 command -v gcc
 command -v g++
 ls /boot/system/develop/headers/node* 2>/dev/null
) > environment.log 2>&1
curl -fsS -T environment.log http://10.0.2.2:18080/opencode-tui-environment.log

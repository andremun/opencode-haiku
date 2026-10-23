#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
set -eu
work=/boot/home/opencode-acceptance
cd "$work"
(
 command -v clipboard || true
 clipboard --help || true
 echo 'PTY headers:'
 cat /boot/system/develop/headers/bsd/pty.h
 echo 'Existing owned services:'
 ps | grep -E 'llama-server|opencode|node' || true
 echo 'Memory:'
 vmstat || true
) > integration-survey.log 2>&1
curl -fsS -T integration-survey.log http://10.0.2.2:18080/native-integration-survey.log

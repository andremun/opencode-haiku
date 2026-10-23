#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
set -u
work=/boot/home/opencode-acceptance
export XDG_DATA_HOME="$work/state/data"
export XDG_CONFIG_HOME="$work/state/config"
export XDG_CACHE_HOME="$work/state/cache"
export XDG_STATE_HOME="$work/state/state"
export OPENCODE_PASSWORD=$(awk '/^server password / {print $3;exit}' "$work/gui-server.log")
cd "$work/fixture"
"${OPENCODE_PORT_ROOT:-$work/final-port}/opencode" --server http://127.0.0.1:18083 "$@" 2> "$work/tui-error.log"
rc=$?
echo "$rc" > "$work/tui.exit"
curl -T "$work/tui-error.log" http://10.0.2.2:18080/opencode-tui-error.log

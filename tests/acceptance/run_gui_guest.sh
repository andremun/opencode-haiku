#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
set -eu
work=/boot/home/opencode-acceptance
export XDG_DATA_HOME="$work/state/data"
export XDG_CONFIG_HOME="$work/state/config"
export XDG_CACHE_HOME="$work/state/cache"
export XDG_STATE_HOME="$work/state/state"
cd "$work/fixture"
"${OPENCODE_PORT_ROOT:-$work/final-port}/opencode" serve --hostname 127.0.0.1 --port 18083 > "$work/gui-server.log" 2>&1 &
echo "$!" > "$work/gui-server.pid"

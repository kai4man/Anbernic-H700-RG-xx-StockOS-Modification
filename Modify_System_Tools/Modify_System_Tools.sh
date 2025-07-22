#!/bin/bash

progdir="$(cd $(dirname "$0") || exit; pwd)"/mod_tools

random="$progdir/random.cfg"
[ -f "$random" ] && rm -f "$random"

program="python3 ${progdir}/main.py"
log_file="${progdir}/log.txt"

$program > "$log_file" 2>&1

if [ -f "$random" ]; then
    /mnt/mod/ctrl/random.sh "$(cat "$random")"
    rm -f "$random"
fi
exit 0

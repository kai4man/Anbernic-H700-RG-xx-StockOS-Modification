#!/bin/bash

progdir="$(cd $(dirname "$0") || exit; pwd)"/clock

export PYSDL2_DLL_PATH="/usr/lib"

program="python3 ${progdir}/main.py"
log_file="${progdir}/log.txt"

$program > "$log_file" 2>&1

#!/bin/bash

progdir="$(cd $(dirname "$0") || exit; pwd)"/clock

program="python3 ${progdir}/main.py"
log_file="${progdir}/log.txt"

$program > "$log_file" 2>&1

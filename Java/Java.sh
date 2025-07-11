#!/bin/bash

progdir=$(cd $(dirname "$0"); pwd)

program="python3 ${progdir}/java/main.py"
log_file="${progdir}/java/log.txt"

$program > "$log_file" 2>&1
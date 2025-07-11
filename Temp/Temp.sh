#!/bin/bash

progdir=$(cd $(dirname "$0"); pwd)

program="python3 ${progdir}/temp/main.py"
log_file="${progdir}/temp/log.txt"

$program > "$log_file" 2>&1
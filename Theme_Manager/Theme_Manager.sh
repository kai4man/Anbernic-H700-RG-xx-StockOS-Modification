#!/bin/bash

progdir="$(cd $(dirname "$0") || exit; pwd)"/themes_ins

[ ! -f /usr/bin/zip ] && cp -f "$progdir"/zip /usr/bin && chmod 777 /usr/bin/zip
[ ! -f /usr/bin/unzip ] && cp -f "$progdir"/unzip /usr/bin && chmod 777 /usr/bin/unzip

program="python3 ${progdir}/main.py"
log_file="${progdir}/log.txt"

$program > "$log_file" 2>&1

#!/bin/bash

progdir="$(cd $(dirname "$0") || exit; pwd)"/tiny_scraper

program="python3 ${progdir}/main.py ${progdir}/config.json"
log_file="${progdir}/log.txt"

$program > "$log_file" 2>&1

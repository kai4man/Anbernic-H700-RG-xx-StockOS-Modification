#!/bin/bash

progdir="$(cd $(dirname "$0") || exit; pwd)"
program="${progdir}/upgrade/upgrade.py"
log_file="${progdir}/upgrade/update.log"

while true
do
    if [ -f "/tmp/app.tar.gz" ]; then
        sleep 5
        tar -xf "/tmp/app.tar.gz" -C "$progdir/"
        [ -f "/tmp/app.tar.gz" ] && rm -rf "/tmp/app.tar.gz"
        [ -f "/tmp/app.tar.gz.md5" ] && rm -rf "/tmp/app.tar.gz.md5"
        [ -f "/tmp/info.txt" ] && rm -rf "/tmp/info.txt"
        sync
        sleep 1
    else
        $program > "$log_file" 2>&1
        if [ $? -ne 36 ]; then
            break
        fi
    fi
done

exit 0
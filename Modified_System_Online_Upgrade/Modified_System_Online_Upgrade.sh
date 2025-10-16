#!/bin/bash

progdir="$(cd $(dirname "$0") || exit; pwd)"
program="${progdir}/upgrade/upgrade.py"
log_file="${progdir}/upgrade/update.log"

SCRIPT_NAME="$0"
NEW_FILE="$progdir/upgrade/update.sh"
APP_FILE="/tmp/app.tar.gz"

export PYSDL2_DLL_PATH="/usr/lib"

while true
do
    if [ -f "$NEW_FILE" ]; then
        chmod +x "$NEW_FILE"
        if bash -n "$NEW_FILE" 2>/dev/null; then
            cat "$NEW_FILE" > "$SCRIPT_NAME"
            rm -f "$NEW_FILE"
            exec "$SCRIPT_NAME" "$@"
        else
            echo "The new version has syntax errors and the update has been aborted"
            rm -f "$NEW_FILE"
        fi
    elif [ -f "$APP_FILE" ]; then
        sleep 5
        tar -xf "$APP_FILE" -C "$progdir/"
        [ -f "$APP_FILE" ] && rm -rf "$APP_FILE"
    else
        $program > "$log_file" 2>&1
        if [ $? -ne 36 ]; then
            break
        fi
    fi
done

exit 0
